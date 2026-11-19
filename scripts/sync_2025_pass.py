import re
import sys
import warnings
from pathlib import Path
import pandas as pd
import pymysql

warnings.filterwarnings("ignore", category=UserWarning)

# standardize_majors.py 불러오기 위한 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "scripts"))
from standardize_majors import normalize_univ, match_major

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'database': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

# 2025 합격 명단 파일 경로 (.xlsx 또는 .csv)
PASS_FILE_PATH = r"C:\Users\esang\Documents\work\devel\peer-score-finder\data\raw\25\updated_2025_pass.csv"

def standardize_row(univ_raw, major_raw):
    univ_std = normalize_univ(univ_raw)
    major_std, status, _ = match_major(univ_std, major_raw)
    if status == "캠퍼스_다빈치교정":
        univ_std = "중앙대학교(다빈치)"
        major_std, _, _ = match_major(univ_std, major_raw)
    elif status == "캠퍼스_단국천안교정":
        univ_std = "단국대학교(천안)"
        major_std, _, _ = match_major(univ_std, major_raw)
    elif status == "캠퍼스_외대글로벌교정":
        univ_std = "한국외국어대학교(글로벌)"
        major_std, _, _ = match_major(univ_std, major_raw)
    return univ_std, major_std

def main():
    # 1. 2025 합격 파일 로드
    if PASS_FILE_PATH.endswith(".csv"):
        try:
            df_pass = pd.read_csv(PASS_FILE_PATH, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df_pass = pd.read_csv(PASS_FILE_PATH, encoding="cp949")
    else:
        df_pass = pd.read_excel(PASS_FILE_PATH)

    df_pass.columns = df_pass.columns.str.strip()

    # 컬럼명 자동 인식
    name_col = next(c for c in df_pass.columns if any(k in c for k in ['student_name', '이름', '성명']))
    univ_col = next(c for c in df_pass.columns if any(k in c for k in ['univ', '최종대', '대학', '학교']))
    major_col = next(c for c in df_pass.columns if any(k in c for k in ['major', '학과', '전공']))

    # 2. DB 내 2025년 등록 학생 이름 목록 조회
    conn = pymysql.connect(**DB_CONFIG)
    df_db = pd.read_sql("SELECT DISTINCT student_name FROM peer_data WHERE year = 2025", conn)
    db_names = set(df_db['student_name'].astype(str).str.strip())

    # 언더바 제거 매핑 사전 생성 (예: '김어진1' -> '김어진1', '김동현1' -> '김동현1')
    no_underscore_map = {n.replace("_", ""): n for n in db_names}

    updates = []
    unmatched = []
    matched_students = 0

    for _, row in df_pass.iterrows():
        raw_name = str(row.get(name_col, "")).strip()
        raw_univ = row.get(univ_col, "")
        raw_major = row.get(major_col, "")

        if not raw_name or raw_name == "nan" or pd.isna(raw_univ) or str(raw_univ).strip() in ["", "-", "미기재"]:
            continue

        # 이름 매칭: 1) 정확 일치 -> 2) 언더바(_) 제거 일치 (김어진_1 <-> 김어진1)
        target_db_name = None
        if raw_name in db_names:
            target_db_name = raw_name
        elif raw_name.replace("_", "") in no_underscore_map:
            target_db_name = no_underscore_map[raw_name.replace("_", "")]

        if not target_db_name:
            unmatched.append((raw_name, str(raw_univ).strip(), str(raw_major).strip()))
            continue

        univ_std, major_std = standardize_row(raw_univ, raw_major)
        updates.append((univ_std, major_std, target_db_name))
        matched_students += 1

    # 3. TiDB 일괄 UPDATE
    cursor = conn.cursor()
    sql = """
        UPDATE peer_data
        SET univ = %s, major = %s
        WHERE year = 2025 AND student_name = %s
    """
    if updates:
        cursor.executemany(sql, updates)
    conn.commit()
    updated_rows = cursor.rowcount
    cursor.close()
    conn.close()

    print(f"✅ 2025 합격자 매칭 성공: {matched_students}명 (DB 총 {updated_rows}개 월별 행 반영 완료)")
    if unmatched:
        print(f"\n⚠️ 합격 파일에는 있지만 DB(2025 성적)에서 이름을 못 찾은 학생 ({len(unmatched)}명):")
        for u_name, u_univ, u_major in unmatched:
            print(f"   - {u_name} ({u_univ} {u_major})")

if __name__ == "__main__":
    main()
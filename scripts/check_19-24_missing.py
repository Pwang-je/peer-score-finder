import re
import warnings
from pathlib import Path
import pandas as pd
import pymysql

warnings.filterwarnings("ignore", category=UserWarning)

BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "data" / "processed" / "전체_영어_성적_정제완료.xlsx"  #[cite: 2, 9]

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'database': 'peer_data',  #[cite: 9]
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

INVALID_VALS = {'', '-', '미기재', 'nan', 'NaN', 'None', 'null', 'NULL'}

def strip_suffix(name: str) -> str:
    s = re.sub(r'[_][A-Za-z0-9가-힣]+$', '', str(name).strip())
    s = re.sub(r'[A-Za-z0-9]+$', '', s)
    return s.strip()

def main():
    df_ex = pd.read_excel(EXCEL_PATH)  #[cite: 2]
    df_ex.columns = df_ex.columns.str.strip()
    df_ex = df_ex[df_ex['year'].between(2019, 2024)].copy()

    # 엑셀에서 합격 대학이 기록된 학생만 추출 (연도+이름 기준)
    df_ex_pass = df_ex[
        df_ex['univ'].notna() & (~df_ex['univ'].astype(str).str.strip().isin(INVALID_VALS))
    ].drop_duplicates(subset=['year', 'student_name'], keep='last')  #[cite: 9]

    conn = pymysql.connect(**DB_CONFIG)
    df_db = pd.read_sql(
        "SELECT year, student_name, univ, major FROM peer_data WHERE year BETWEEN 2019 AND 2024",
        conn
    )
    conn.close()

    # 연도별 DB 상태 정리
    db_by_year = {}
    for y, grp in df_db.groupby('year'):
        y_int = int(y)
        db_by_year[y_int] = {}
        for s_name, s_grp in grp.groupby('student_name'):
            valid_u = [u for u in s_grp['univ'].dropna().astype(str).str.strip() if u not in INVALID_VALS]
            db_by_year[y_int][str(s_name).strip()] = valid_u[0] if valid_u else ""

    empty_univ_in_db = []     # 1) DB에 같은 이름이 있는데 univ가 비어있는 경우
    name_mismatch = []        # 2) 이름 접미사 차이로 매칭 안 된 경우
    completely_missing = []   # 3) DB에 해당 연도·학생 행 자체가 없는 경우

    for _, row in df_ex_pass.iterrows():
        y = int(row['year'])
        name = str(row['student_name']).strip()
        ex_univ = str(row['univ']).strip()
        ex_major = str(row.get('major', '')).strip()

        year_map = db_by_year.get(y, {})

        if name in year_map:
            if not year_map[name]:
                empty_univ_in_db.append((y, name, ex_univ, ex_major))
        else:
            # 언더바 제거 또는 기본 이름 일치 후보 탐색
            no_us = name.replace("_", "")
            base = strip_suffix(name)
            cands = [
                db_n for db_n in year_map.keys()
                if db_n.replace("_", "") == no_us or strip_suffix(db_n) == base
            ]
            if cands:
                name_mismatch.append((y, name, ex_univ, ex_major, cands))
            else:
                completely_missing.append((y, name, ex_univ, ex_major))

    print(f"=== [유형 1] DB에 행은 있으나 합격대학이 비어 있는 학생 ({len(empty_univ_in_db)}명) ===")
    for item in empty_univ_in_db:
        print(f"  - {item[0]}년 | {item[1]} -> 엑셀: {item[2]} {item[3]}")

    print(f"\n=== [유형 2] 이름 표기 차이로 매칭되지 않은 학생 ({len(name_mismatch)}명) ===")
    for item in name_mismatch:
        print(f"  - {item[0]}년 | 엑셀 '{item[1]}' ({item[2]} {item[3]}) <--> DB 후보: {item[4]}")

    print(f"\n=== [유형 3] DB(peer_data)에 학생 데이터 자체가 없는 경우 ({len(completely_missing)}명) ===")
    for item in completely_missing:
        print(f"  - {item[0]}년 | {item[1]} ({item[2]} {item[3]})")

if __name__ == "__main__":
    main()
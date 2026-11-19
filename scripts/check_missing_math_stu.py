# 수학점수 누락 확인
import pandas as pd
import pymysql

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'db': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

# 실제 수학 점수 엑셀/CSV 파일 경로로 수정하세요[cite: 8]
MATH_FILE_PATH = r"C:\Users\esang\Documents\work\devel\peer-score-finder\data\raw\math\19-25_수학점수.xlsx"


def check_missing_math():
    df_math = pd.read_csv(MATH_FILE_PATH) if MATH_FILE_PATH.endswith(".csv") else pd.read_excel(MATH_FILE_PATH)
    df_math.columns = df_math.columns.str.strip()

    conn = pymysql.connect(**DB_CONFIG)
    df_db = pd.read_sql("""
                        SELECT year, month, student_name, department, math_total, univ, major
                        FROM peer_data
                        WHERE year < 2026
                        """, conn)
    conn.close()

    # 1) 엑셀에는 있는데 DB UPDATE에 실패한 건 찾기
    db_keys = set(zip(df_db['year'], df_db['month'], df_db['student_name'].astype(str).str.strip()))
    db_year_names = set(zip(df_db['year'], df_db['student_name'].astype(str).str.strip()))

    unmatched_excel = []
    for _, row in df_math.iterrows():
        raw_m = row.get('math_total')
        if pd.isna(raw_m) or str(raw_m).strip() in ['', '결시', 'None', 'nan']:
            continue
        try:
            m_score = float(raw_m)
        except ValueError:
            continue

        y, m, name = int(row['year']), int(row['month']), str(row['student_name']).strip()
        if (y, m, name) not in db_keys:
            reason = "해당 월 영어 행 없음(다른 월은 존재)" if (y, name) in db_year_names else "연도+이름 불일치(동명이인 _1 접미사/오타 의심)"
            unmatched_excel.append((y, m, name, m_score, reason))

    print(f"=== [1] 엑셀 -> DB 매칭 실패 건수: {len(unmatched_excel)}건 ===")
    for item in unmatched_excel:
        print(f"  - {item[0]}년 {item[1]}월 | {item[2]} (수학:{item[3]}) -> {item[4]}")

    # 2) DB 내 자연계열 학생 중 수학 점수가 전무한 학생 찾기
    df_nat = df_db[df_db['department'].astype(str).str.contains('자연', na=False)].copy()
    df_nat['math_num'] = pd.to_numeric(df_nat['math_total'], errors='coerce').fillna(0)

    nat_summary = df_nat.groupby(['year', 'student_name', 'univ', 'major'])['math_num'].max().reset_index()
    no_math_students = nat_summary[nat_summary['math_num'] <= 0]

    print(f"\n=== [2] DB 자연계열 학생 중 수학 점수가 0건인 학생: {len(no_math_students)}명 ===")
    for _, r in no_math_students.iterrows():
        print(f"  - {r['year']}년 | {r['student_name']} ({r['univ']} {r['major']})")


if __name__ == "__main__":
    check_missing_math()
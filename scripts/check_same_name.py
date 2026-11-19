import warnings
import pandas as pd
import pymysql

warnings.filterwarnings("ignore", category=UserWarning)

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'database': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

MATH_FILE_PATH = r"C:\Users\esang\Documents\work\devel\peer-score-finder\data\raw\math\19-25_수학점수.xlsx"

# 검증 완료된 1:1 확정 매핑 (김민규_2는 기존 김민규 8월 점수 덮어쓰기 방지를 위해 제외)
MANUAL_MAP = {
    (2023, "김수현"):   "김수현_I",
    (2023, "이수빈_I"): "이수빈",
    (2024, "김기범"):   "김기범_N",
    (2024, "김민서"):   "김민서_N",
    (2025, "김동현_1"): "김동현1",
    (2025, "김동현"):   "김동현2",
    (2025, "김서연_1"): "김서연1",
    (2025, "김서연_2"): "김서연2",
    (2025, "김어진_1"): "김어진1",
    (2025, "김어진_2"): "김어진2",
}

def main():
    df_math = pd.read_csv(MATH_FILE_PATH) if MATH_FILE_PATH.endswith(".csv") else pd.read_excel(MATH_FILE_PATH)
    df_math.columns = df_math.columns.str.strip()

    conn = pymysql.connect(**DB_CONFIG)
    df_db = pd.read_sql("SELECT year, month, student_name, math_total FROM peer_data WHERE year BETWEEN 2019 AND 2025", conn)
    db_exact = set(zip(df_db['year'], df_db['month'], df_db['student_name'].str.strip()))

    empty_df = df_db[df_db['math_total'].isna() | (pd.to_numeric(df_db['math_total'], errors='coerce').fillna(0) == 0)]
    latest_empty = (
        empty_df.sort_values('month', ascending=False)
        .drop_duplicates(subset=['year', 'student_name'])
        .set_index(['year', 'student_name'])['month']
        .to_dict()
    )

    updates = []
    used_fallback = set()

    for _, row in df_math.iterrows():
        raw_m = row.get('math_total')
        if pd.isna(raw_m) or str(raw_m).strip() in ['', '결시', 'None', 'nan']:
            continue
        try:
            m_score = float(raw_m)
        except ValueError:
            continue

        y = int(row['year'])
        m = int(row['month'])
        ex_name = str(row['student_name']).strip()

        db_name = MANUAL_MAP.get((y, ex_name))
        if not db_name:
            continue

        if (y, m, db_name) in db_exact:
            updates.append((m_score, y, m, db_name))
        elif (y, db_name) in latest_empty and (y, db_name) not in used_fallback:
            updates.append((m_score, y, int(latest_empty[(y, db_name)]), db_name))
            used_fallback.add((y, db_name))

    cursor = conn.cursor()
    sql = "UPDATE peer_data SET math_total = %s WHERE year = %s AND month = %s AND student_name = %s"
    if updates:
        cursor.executemany(sql, updates)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ 수동 매핑 업데이트 완료: 총 {len(updates)}건 반영")

if __name__ == "__main__":
    main()
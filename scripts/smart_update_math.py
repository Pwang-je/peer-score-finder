import re
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

def strip_suffix(name: str) -> str:
    s = re.sub(r'[_][A-Za-z0-9가-힣]+$', '', str(name).strip())
    s = re.sub(r'[A-Za-z0-9]+$', '', s)
    return s.strip()

def main():
    print("1/3. 엑셀 및 DB 데이터 로딩 중...")
    df_math = pd.read_csv(MATH_FILE_PATH) if MATH_FILE_PATH.endswith(".csv") else pd.read_excel(MATH_FILE_PATH)
    df_math.columns = df_math.columns.str.strip()
    df_math = df_math[df_math['year'].between(2019, 2025)].copy()

    conn = pymysql.connect(**DB_CONFIG)
    df_db = pd.read_sql("SELECT year, month, student_name, math_total FROM peer_data WHERE year BETWEEN 2019 AND 2025", conn)

    db_exact = set(zip(df_db['year'], df_db['month'], df_db['student_name'].str.strip()))
    db_names_by_year = df_db.groupby('year')['student_name'].unique().to_dict()

    # 학생별 math_total이 비어있는 최신 월 미리 매핑 (DB 왕복 최소화)
    empty_math_df = df_db[df_db['math_total'].isna() | (pd.to_numeric(df_db['math_total'], errors='coerce').fillna(0) == 0)]
    latest_empty_month = (
        empty_math_df.sort_values('month', ascending=False)
        .drop_duplicates(subset=['year', 'student_name'])
        .set_index(['year', 'student_name'])['month']
        .to_dict()
    )

    exact_updates = []
    fallback_updates = []
    used_fallback_keys = set()
    ambiguous = []

    print("2/3. 매칭 대상 분류 중...")
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
        raw_name = str(row['student_name']).strip()
        db_list = list(db_names_by_year.get(y, []))

        target_name = None
        if raw_name in db_list:
            target_name = raw_name
        else:
            base = strip_suffix(raw_name)
            cands = [n for n in db_list if strip_suffix(n) == base]
            if len(cands) == 1:
                target_name = cands[0]
            elif len(cands) > 1:
                ambiguous.append((y, m, raw_name, cands))
                continue
            else:
                continue

        if (y, m, target_name) in db_exact:
            exact_updates.append((m_score, y, m, target_name))
        else:
            fb_month = latest_empty_month.get((y, target_name))
            if fb_month and (y, fb_month, target_name) not in used_fallback_keys:
                fallback_updates.append((m_score, y, int(fb_month), target_name))
                used_fallback_keys.add((y, fb_month, target_name))

    print("3/3. TiDB 일괄 전송 중...")
    cursor = conn.cursor()
    sql = "UPDATE peer_data SET math_total = %s WHERE year = %s AND month = %s AND student_name = %s"
    if exact_updates:
        cursor.executemany(sql, exact_updates)
    if fallback_updates:
        cursor.executemany(sql, fallback_updates)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n✅ 정확 일치(연·월·이름) 업데이트: {len(exact_updates)}건")
    print(f"✅ 영어 결시 월 보충(인접 월 반영) 업데이트: {len(fallback_updates)}건")
    if ambiguous:
        print(f"⚠️ 동명이인 후보가 2명 이상이라 수동 확인이 필요한 건:")
        for item in sorted(set((x[0], x[2], tuple(x[3])) for x in ambiguous)):
            print(f"   - {item[0]}년 | 엑셀 '{item[1]}' -> DB 후보 {list(item[2])}")

if __name__ == "__main__":
    main()
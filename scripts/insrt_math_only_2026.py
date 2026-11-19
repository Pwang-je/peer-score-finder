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

FILE_PATH = r"C:\Users\esang\Documents\work\devel\peer-score-finder\data\raw\math\26_수학점수.xlsx"

def main():
    df = pd.read_csv(FILE_PATH) if FILE_PATH.endswith(".csv") else pd.read_excel(FILE_PATH)
    df.columns = df.columns.str.strip()
    df = df[df['year'] == 2026].copy()

    df['student_name'] = df['student_name'].astype(str).str.strip()
    df['month'] = pd.to_numeric(df['month'], errors='coerce')
    df['math_num'] = pd.to_numeric(df['math_total'], errors='coerce')
    df = df.dropna(subset=['month', 'math_num']).copy()
    df['month'] = df['month'].astype(int)

    conn = pymysql.connect(**DB_CONFIG)
    df_db = pd.read_sql("SELECT month, student_name, department FROM peer_data WHERE year = 2026", conn)

    db_students = set(df_db['student_name'].str.strip())
    db_exact_keys = set(zip(df_db['month'], df_db['student_name'].str.strip()))

    # 학생별 기존 계열(department) 매핑 (자연계열 유지)
    dept_map = {}
    for name, grp in df_db.groupby('student_name'):
        depts = [str(d).strip() for d in grp['department'].dropna() if str(d).strip() != '']
        nat_depts = [d for d in depts if '자연' in d]
        dept_map[name.strip()] = nat_depts[0] if nat_depts else (depts[0] if depts else '일반자연')

    # 듀이카 학생 중 해당 월 영어 행이 없어 빠졌던 건만 추출
    df_target = df[df['student_name'].isin(db_students)].copy()
    dup_mask = df_target.duplicated(subset=['month', 'student_name'], keep=False)
    df_safe = df_target[~dup_mask]

    inserts = []
    for _, row in df_safe.iterrows():
        m = int(row['month'])
        name = row['student_name']
        score = float(row['math_num'])
        if (m, name) not in db_exact_keys:
            dept = dept_map.get(name, '일반자연')
            inserts.append((2026, m, name, score, dept))

    cursor = conn.cursor()
    sql = """
        INSERT INTO peer_data (year, month, student_name, math_total, department)
        VALUES (%s, %s, %s, %s, %s)
    """
    if inserts:
        cursor.executemany(sql, inserts)
    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ 영어 미응시 월 수학 점수 {len(inserts)}건 신규 추가 완료!")

if __name__ == "__main__":
    main()
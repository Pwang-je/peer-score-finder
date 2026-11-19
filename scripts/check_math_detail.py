import re
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

MATH_FILE_PATH = r"C:\Users\esang\Documents\work\devel\peer-score-finder\data\raw\math\19-25_수학점수.xlsx"

def strip_suffix(name: str) -> str:
    s = re.sub(r'[_][A-Za-z0-9가-힣]+$', '', str(name).strip())
    s = re.sub(r'[A-Za-z0-9]+$', '', s)
    return s.strip()

df_math = pd.read_csv(MATH_FILE_PATH) if MATH_FILE_PATH.endswith(".csv") else pd.read_excel(MATH_FILE_PATH)
df_math.columns = df_math.columns.str.strip()
df_math = df_math[df_math['year'].between(2019, 2025)].copy()

conn = pymysql.connect(**DB_CONFIG)
df_db = pd.read_sql("SELECT DISTINCT year, student_name FROM peer_data WHERE year BETWEEN 2019 AND 2025", conn)
conn.close()

print(f"DB 내 2019년 등록 학생 수: {df_db[df_db['year'] == 2019]['student_name'].nunique()}명")

db_names_by_year = df_db.groupby('year')['student_name'].apply(list).to_dict()

suffix_candidates = {}
not_in_db = set()

for _, row in df_math.iterrows():
    if pd.isna(row.get('math_total')) or str(row.get('math_total')).strip() in ['', '결시', 'None', 'nan']:
        continue
    y = int(row['year'])
    raw_name = str(row['student_name']).strip()
    db_list = db_names_by_year.get(y, [])

    if raw_name in db_list:
        continue

    base = strip_suffix(raw_name)
    matches = [n for n in db_list if strip_suffix(n) == base]
    if matches:
        suffix_candidates[(y, raw_name)] = matches
    else:
        not_in_db.add((y, raw_name))

print(f"\n=== [1] 이름 접미사만 달라서 매칭 가능한 학생 ({len(suffix_candidates)}명) ===")
for (y, r_name), m_list in sorted(suffix_candidates.items()):
    print(f"  - {y}년 | 엑셀: '{r_name}'  <-->  DB 후보: {m_list}")

print(f"\n=== [2] DB(영어성적)에 아예 존재하지 않는 학생 ({len(not_in_db)}명) ===")
for y, r_name in sorted(not_in_db):
    print(f"  - {y}년 | '{r_name}'")
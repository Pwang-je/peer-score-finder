import pandas as pd
import pymysql

# 1. TiDB 연결 정보
DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'db': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

# 2. 정리하신 엑셀/CSV 파일 경로 (.xlsx 또는 .csv)
FILE_PATH = "C:\\Users\\esang\\Documents\\work\\devel\\peer-score-finder\\data\\raw\\26_수학점수.xlsx"  # 실제 저장하신 파일명으로 수정해 주세요.

print("파일 로딩 중...")
if FILE_PATH.endswith(".csv"):
    try:
        df = pd.read_csv(FILE_PATH, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(FILE_PATH, encoding="cp949")
else:
    df = pd.read_excel(FILE_PATH)

# 컬럼명 앞뒤 공백 제거
df.columns = df.columns.str.strip()

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("TiDB 데이터에 수학 점수 일괄 UPDATE 준비 중...")

# year + month + student_name 조건으로 math_total 갱신
update_query = """
               UPDATE peer_data
               SET math_total = %s
               WHERE year = %s \
                 AND month = %s \
                 AND student_name = %s \
               """

update_records = []
for _, row in df.iterrows():
    # 필수 식별자 유효성 검사
    if pd.isna(row.get('student_name')) or pd.isna(row.get('year')) or pd.isna(row.get('month')):
        continue

    name = str(row['student_name']).strip()
    year = int(row['year'])
    month = int(row['month'])

    # math_total 값 확인
    raw_math = row.get('math_total')
    if pd.isna(raw_math) or raw_math == '' or raw_math is None:
        continue

    try:
        math_score = float(raw_math)
    except ValueError:
        continue  # '결시' 등 문자인 경우 제외

    update_records.append((math_score, year, month, name))

print(f"매칭 대상 데이터 총 {len(update_records)}건 준비 완료. DB 전송을 시작합니다...")

# 1000건 단위 배치 업데이트
batch_size = 1000
total_updated = 0

for i in range(0, len(update_records), batch_size):
    batch = update_records[i:i + batch_size]
    cursor.executemany(update_query, batch)
    conn.commit()
    total_updated += len(batch)
    print(f"진행 상황: {total_updated} / {len(update_records)} 건 반영 완료...")

cursor.close()
conn.close()

print(f"\n🎉 모든 수학 점수가 성공적으로 반영되었습니다! (총 {total_updated}건)")
import pandas as pd
import pymysql

# 1. TiDB 연결 설정
DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'db': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

# 2. 수정된 25년도 파일 불러오기 (경로와 파일명에 맞게 수정)
csv_file = "C:\\Users\\esang\\Documents\\work\\devel\\peer-score-finder\\data\\raw\\updated_2025_pass.csv"  # 엑셀인 경우 pd.read_excel(...)
df = pd.read_csv(csv_file)

# 컬럼명 앞뒤 공백 제거 및 결측치 빈 문자열 처리
df.columns = df.columns.str.strip()
df = df.fillna("")

conn = pymysql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("TiDB 2025년도 데이터 업데이트 시작...")
update_count = 0

# 3. 2025년도 데이터의 대학/학과/계열 일괄 UPDATE
# (학생 이름과 year=2025 조건으로 기존 레코드 갱신)
update_query = """
               UPDATE peer_data
               SET univ       = %s, \
                   major      = %s, \
                   department = %s
               WHERE year = 2025 AND student_name = %s \
               """

for _, row in df.iterrows():
    name = str(row['student_name']).strip()
    univ = str(row.get('univ', '')).strip()
    major = str(row.get('major', '')).strip()
    dept = str(row.get('department', '')).strip()

    if not name or not univ:
        continue

    cursor.execute(update_query, (univ, major, dept, name))
    update_count += cursor.rowcount

conn.commit()
cursor.close()
conn.close()

print(f"업데이트 완료! 총 {update_count}건의 레코드가 갱신되었습니다.")
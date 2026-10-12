import pymysql

# TiDB Cloud 접속 설정
DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}  # TiDB SSL 필수 옵션
}

try:
    # 1. TiDB 서버 접속
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print(" TiDB Cloud 접속 성공!")

    # 2. peer_data 데이터베이스 생성
    cursor.execute("CREATE DATABASE IF NOT EXISTS peer_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    print(" peer_data 데이터베이스 생성 완료!")

    conn.commit()
    cursor.close()
    conn.close()

except Exception as e:
    print(" 접속 실패 에러:", e)
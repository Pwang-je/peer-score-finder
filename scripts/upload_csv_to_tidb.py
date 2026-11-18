import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
import urllib.parse

BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_FILE_PATH = BASE_DIR / "data" / "processed" / "전체_영어_성적_정제완료.xlsx"
TABLE_NAME = "peer_data"

USER = "3BAijZ6wxqbmp3n.root"
PASSWORD = "BDs2xnssZHYNtQS2"
HOST = "gateway01.ap-northeast-1.prod.aws.tidbcloud.com"
PORT = 4000
DB = "peer_data"

encoded_password = urllib.parse.quote_plus(PASSWORD)
connection_url = (
    f"mysql+pymysql://{USER}:{encoded_password}@{HOST}:{PORT}/{DB}"
    f"?ssl_check_hostname=false&ssl_verify_cert=false"
)

try:
    print("⏳ 정제완료된 엑셀 파일을 읽는 중...")
    df = pd.read_excel(EXCEL_FILE_PATH)
    print(f"📊 총 {len(df)}건의 정제된 데이터 로드 완료.")

    print("🚀 TiDB Cloud로 정제된 데이터 최종 덮어쓰기 시작...")
    engine = create_engine(connection_url)

    # 정제된 엑셀 데이터를 peer_data 테이블에 통째로 반영
    df.to_sql(name=TABLE_NAME, con=engine, if_exists='replace', index=False, chunksize=1000)

    print(f"🎉 성공! 이제 모든 대학 및 학과명이 정식 명칭으로 DB에 반영되었습니다.")

except Exception as e:
    print("❌ 업로드 중 에러 발생:", e)
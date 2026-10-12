import pandas as pd
from sqlalchemy import create_engine
import urllib.parse

# 1. 파일 및 테이블 설정
CSV_FILE_PATH = "data.csv"  # 여기에 본인의 CSV 파일 이름 또는 경로 입력
TABLE_NAME = "peer_data"  # DB에 생성할 테이블 이름 (원래 쓰던 테이블 이름으로 변경)

# 2. TiDB 접속 정보
USER = "3BAijZ6wxqbmp3n.root"
PASSWORD = "BDs2xnssZHYNtQS2"
HOST = "gateway01.ap-northeast-1.prod.aws.tidbcloud.com"
PORT = 4000
DB = "peer_data"

# 비밀번호에 특수문자가 있을 수 있으므로 인코딩 처리
encoded_password = urllib.parse.quote_plus(PASSWORD)

# SQLAlchemy 엔진 생성 (SSL 옵션 포함)
connection_url = (
    f"mysql+pymysql://{USER}:{encoded_password}@{HOST}:{PORT}/{DB}"
    f"?ssl_check_hostname=false&ssl_verify_cert=false"
)

try:
    print("⏳ CSV 파일 읽는 중...")
    # 인코딩 오류가 날 경우 encoding='utf-8' 또는 'cp949', 'euc-kr' 로 변경
    df = pd.read_csv('C:\\Users\\esang\\Documents\\work\\devel\\peer-score-finder\\전체_영어_성적.csv', encoding='utf-8')
    print(f"📊 총 {len(df)}건의 데이터 로드 완료. 컬럼 목록:", list(df.columns))

    print("🚀 TiDB Cloud로 업로드 시작...")
    engine = create_engine(connection_url)

    # to_sql을 통해 테이블 자동 생성 및 데이터 일괄 삽입
    # if_exists='replace': 기존 테이블이 있으면 덮어쓰기
    df.to_sql(name=TABLE_NAME, con=engine, if_exists='replace', index=False, chunksize=1000)

    print(f"🎉 성공! [{TABLE_NAME}] 테이블에 데이터가 정상적으로 저장되었습니다.")

except UnicodeDecodeError:
    print("⚠️ 인코딩 오류: pd.read_csv의 인코딩을 'cp949'로 변경하여 다시 시도해 보세요.")
except Exception as e:
    print("❌ 업로드 중 에러 발생:", e)
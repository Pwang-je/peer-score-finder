import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "data" / "processed" / "전체_영어_성적_정제완료.xlsx"
DB_URL = "mysql+pymysql://3BAijZ6wxqbmp3n.root:BDs2xnssZHYNtQS2@gateway01.ap-northeast-1.prod.aws.tidbcloud.com:4000/peer_data?charset=utf8mb4"

def main():
    # 1. 엑셀 샘플 확인
    df = pd.read_excel(EXCEL_PATH)
    df_valid = df[df["univ"].notna() & (df["univ"].astype(str).str.strip() != "")].copy()
    print("=== [엑셀 파일 데이터 샘플 (상위 3개)] ===")
    print(df_valid[["year", "student_name", "univ", "major"]].head(3))

    # 2. DB 샘플 확인
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        db_df = pd.read_sql(text("SELECT year, student_name, univ, major FROM peer_data LIMIT 3"), con=conn)
    print("\n=== [데이터베이스(peer_data) 테이블 샘플 (상위 3개)] ===")
    print(db_df)

if __name__ == "__main__":
    main()
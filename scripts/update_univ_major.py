import pandas as pd
import pymysql
from pathlib import Path

# ==========================================
# 1. 파일 경로 및 TiDB 연결 설정
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "data" / "processed" / "전체_영어_성적_정제완료.xlsx"

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'database': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

TABLE_NAME = "peer_data"  # 스크린샷 기준 실제 테이블명

def main():
    df = pd.read_excel(EXCEL_PATH)

    # 1) 대학명이 비어있는 행 제외 및 (year, student_name) 기준 최신 값 추출
    df_valid = df[df["univ"].notna() & (df["univ"].astype(str).str.strip() != "")].copy()
    df_valid = df_valid.drop_duplicates(subset=["year", "student_name"], keep="last")
    print(f"업데이트 대상 학생 수(연도+이름 기준): {len(df_valid)}명")

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            # [안전장치 1] TiDB 호환 백업 테이블 생성
            cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}_backup_major")
            cursor.execute(f"CREATE TABLE {TABLE_NAME}_backup_major LIKE {TABLE_NAME}")
            cursor.execute(f"INSERT INTO {TABLE_NAME}_backup_major SELECT * FROM {TABLE_NAME}")
            print(f"[1/2] 백업 테이블 생성 완료: {TABLE_NAME}_backup_major")

            # [안전장치 2] univ, major 컬럼만 업데이트 (기존 영어·math_total 점수 보존)
            # 같은 연도·같은 학생의 모든 월(영어/수학) 행에 정식 대학·학과명 일괄 반영
            sql = f"""
                UPDATE {TABLE_NAME}
                SET univ = %s, major = %s
                WHERE year = %s AND student_name = %s
            """

            params = []
            for _, row in df_valid.iterrows():
                univ_val = str(row["univ"]).strip()
                major_val = None if pd.isna(row["major"]) or str(row["major"]).strip() == "" else str(row["major"]).strip()
                params.append((
                    univ_val,
                    major_val,
                    int(row["year"]),
                    str(row["student_name"]).strip()
                ))

            affected_rows = cursor.executemany(sql, params)

        conn.commit()
        print(f"[2/2] TiDB 업데이트 완료! (수정된 행 수: {affected_rows}건)")

    except Exception as e:
        conn.rollback()
        print(f"오류 발생으로 롤백되었습니다: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
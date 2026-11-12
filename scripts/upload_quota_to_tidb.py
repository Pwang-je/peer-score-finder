import pymysql
import sys
from pathlib import Path

# 프로젝트 루트 경로(peer-score-finder)를 sys.path에 등록
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from backend.tidb_db import DB_CONFIG

# 가천대학교 2026학년도 모집요강 기준 데이터
GACHON_DATA = [
    # 자연계열
    {"dept": "자연", "major": "전자공학전공", "gen": 32, "bac": 6},
    {"dept": "자연", "major": "화공생명공학전공", "gen": 30, "bac": 3},
    {"dept": "자연", "major": "기계공학전공", "gen": 24, "bac": 3},
    {"dept": "자연", "major": "컴퓨터공학전공", "gen": 26, "bac": 6},
    {"dept": "자연", "major": "소프트웨어전공", "gen": 10, "bac": 0},
    {"dept": "자연", "major": "인공지능전공", "gen": 19, "bac": 0},
    {"dept": "자연", "major": "스마트보안전공", "gen": 3, "bac": 0},
    {"dept": "자연", "major": "전기공학과", "gen": 8, "bac": 2},
    {"dept": "자연", "major": "의공학과", "gen": 8, "bac": 0},
    {"dept": "자연", "major": "스마트시티학과", "gen": 6, "bac": 0},
    {"dept": "자연", "major": "신소재공학과", "gen": 6, "bac": 2},
    {"dept": "자연", "major": "바이오나노학과", "gen": 10, "bac": 2},
    {"dept": "자연", "major": "생명과학과", "gen": 5, "bac": 2},
    {"dept": "자연", "major": "식품생명공학과", "gen": 5, "bac": 2},
    {"dept": "자연", "major": "식품영양학과", "gen": 10, "bac": 2},
    {"dept": "자연", "major": "물리학과", "gen": 9, "bac": 2},
    {"dept": "자연", "major": "화학과", "gen": 3, "bac": 2},
    {"dept": "자연", "major": "토목환경공학과", "gen": 4, "bac": 2},
    {"dept": "자연", "major": "산업공학전공", "gen": 5, "bac": 2},
    {"dept": "자연", "major": "스마트팩토리전공", "gen": 4, "bac": 0},
    {"dept": "자연", "major": "도시계획학전공", "gen": 10, "bac": 0},
    {"dept": "자연", "major": "설비·소방공학과", "gen": 5, "bac": 0},
    {"dept": "자연", "major": "배터리공학전공", "gen": 2, "bac": 0},
    {"dept": "자연", "major": "금융수학전공", "gen": 12, "bac": 2},
    {"dept": "자연", "major": "빅데이터경영전공", "gen": 1, "bac": 0},
    {"dept": "자연", "major": "운동재활학과", "gen": 6, "bac": 0},
    {"dept": "자연", "major": "바이오로직스학과*", "gen": 12, "bac": 0},
    {"dept": "자연", "major": "간호학과*", "gen": 5, "bac": 2},
    {"dept": "자연", "major": "치위생학과*", "gen": 3, "bac": 0},
    {"dept": "자연", "major": "방사선학과*", "gen": 2, "bac": 1},
    {"dept": "자연", "major": "물리치료학과*", "gen": 1, "bac": 1},
    {"dept": "자연", "major": "응급구조학과*", "gen": 0, "bac": 0},

    # 인문계열
    {"dept": "인문", "major": "경영학전공", "gen": 40, "bac": 8},
    {"dept": "인문", "major": "미디어커뮤니케이션학과", "gen": 6, "bac": 2},
    {"dept": "인문", "major": "관광경영학과", "gen": 5, "bac": 2},
    {"dept": "인문", "major": "경제학과", "gen": 5, "bac": 2},
    {"dept": "인문", "major": "의료산업경영학과", "gen": 5, "bac": 2},
    {"dept": "인문", "major": "응용통계학과", "gen": 7, "bac": 2},
    {"dept": "인문", "major": "사회복지학과", "gen": 6, "bac": 2},
    {"dept": "인문", "major": "유아교육학과", "gen": 0, "bac": 0},
    {"dept": "인문", "major": "심리학과", "gen": 7, "bac": 2},
    {"dept": "인문", "major": "패션산업학과", "gen": 6, "bac": 0},
    {"dept": "인문", "major": "한국어문학과", "gen": 5, "bac": 2},
    {"dept": "인문", "major": "영미어문학과", "gen": 8, "bac": 2},
    {"dept": "인문", "major": "동양어문학과", "gen": 3, "bac": 2},
    {"dept": "인문", "major": "법학과", "gen": 20, "bac": 2},
    {"dept": "인문", "major": "경찰행정학과", "gen": 4, "bac": 2},
    {"dept": "인문", "major": "행정학과", "gen": 16, "bac": 2},
]

def upload_gachon_quota():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 1. 데이터베이스 선택 (에러 방지)
    cursor.execute("USE peer_data;")

    # 2. 테이블이 없을 경우 자동 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recruit_quota (
            id INT AUTO_INCREMENT PRIMARY KEY,
            year INT NOT NULL DEFAULT 2026,
            univ VARCHAR(50) NOT NULL,
            department VARCHAR(20) NOT NULL,
            major VARCHAR(50) NOT NULL,
            general_quota INT DEFAULT 0,
            bachelor_quota INT DEFAULT 0,
            UNIQUE KEY uq_univ_major (year, univ, major)
        );
    """)

    # 3. 데이터 삽입/업데이트
    query = """
        INSERT INTO recruit_quota (year, univ, department, major, general_quota, bachelor_quota)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            department = VALUES(department),
            general_quota = VALUES(general_quota),
            bachelor_quota = VALUES(bachelor_quota)
    """

    count = 0
    for item in GACHON_DATA:
        cursor.execute(query, (
            2026,
            "가천대학교",
            item["dept"],
            item["major"],
            item["gen"],
            item["bac"]
        ))
        count += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ 가천대학교 {count}개 모집단위 정원 적재 완료!")

if __name__ == "__main__":
    upload_gachon_quota()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pymysql
import numpy as np
from sklearn.neighbors import NearestNeighbors

app = FastAPI()

# 프론트엔드(Vue.js)와의 연동을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'wogns1224',  # 본인의 MySQL 비밀번호
    'db': 'peer_data',
    'charset': 'utf8mb4'
}


def get_db_data(month: int):
    conn = pymysql.connect(**DB_CONFIG)
    # year < 2026 조건을 주어 올해 데이터가 선배 매칭풀에 섞이지 않도록 격리합니다.
    query = f"""
        SELECT year, student_name, total_score, grammar, vocabulary, logic, reading, univ, major, department 
        FROM student_scores 
        WHERE month = {month} AND year < 2026 AND univ != '' AND univ IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")


def get_all_months_data():
    conn = pymysql.connect(**DB_CONFIG)
    query = "SELECT student_name, month, total_score FROM student_scores WHERE year < 2026 AND univ != '' AND univ IS NOT NULL"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")


def get_my_all_months_data(student_name: str):
    conn = pymysql.connect(**DB_CONFIG)
    query = f"""
        SELECT month, total_score 
        FROM student_scores 
        WHERE year = 2026 AND student_name = %s
    """
    df = pd.read_sql(query, conn, params=[student_name])
    conn.close()
    return df.fillna("")


# 1. 실시간 이름 검색 (자동완성) API
@app.get("/search-students")
def search_students(keyword: str = ""):
    if not keyword.strip():
        return []

    conn = pymysql.connect(**DB_CONFIG)
    query = """
        SELECT DISTINCT student_name 
        FROM student_scores 
        WHERE year = 2026 AND student_name LIKE %s
        LIMIT 10
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (f"%{keyword}%",))
        rows = cursor.fetchall()
        student_list = [row[0] for row in rows]
        return student_list
    except Exception as e:
        print("이름 검색 에러:", e)
        return []
    finally:
        conn.close()


# 2. 선택된 학생의 특정 달 성적 단건 조회 API
@app.get("/get-student-score")
def get_student_score(student_name: str, month: int):
    conn = pymysql.connect(**DB_CONFIG)
    query = """
        SELECT grammar, vocabulary, logic, reading, total_score 
        FROM student_scores 
        WHERE year = 2026 AND student_name = %s AND month = %s
    """
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query, (student_name, month))
        result = cursor.fetchone()
        if result:
            return {"status": "success", "data": result}
        else:
            return {"status": "empty", "message": "해당 월의 성적 데이터가 존재하지 않습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# 3. 유사 성적 합격자 예측 및 종합 분석 API
@app.get("/predict")
def predict_university(month: int, grammar: float, vocabulary: float, logic: float, reading: float, student_name: str):
    df_raw = get_db_data(month)
    if df_raw.empty:
        return {"status": "error", "message": "해당 월의 데이터가 없습니다."}

    # 영역별 선배 평균 데이터 가공
    month_averages = {
        "grammar": round(df_raw['grammar'].mean(), 1),
        "vocabulary": round(df_raw['vocabulary'].mean(), 1),
        "logic": round(df_raw['logic'].mean(), 1),
        "reading": round(df_raw['reading'].mean(), 1),
        "total": round(df_raw['total_score'].mean(), 1)
    }

    df_past = df_raw.copy()
    features = ['grammar', 'vocabulary', 'logic', 'reading']
    X_past = df_past[features]
    current_student = [[grammar, vocabulary, logic, reading]]

    # KNN 모델 빌드 및 이웃 선배 추출
    n_neighbors = min(100, len(df_past))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    knn.fit(X_past)

    distances, indices = knn.kneighbors(current_student)
    matched_seniors = df_past.iloc[indices[0]].copy()

    # 이름(student_name)과 총점(total_score)이 완전히 똑같은 복제 데이터 중복 제거
    matched_seniors = matched_seniors.drop_duplicates(subset=['student_name', 'total_score'])

    # 무작위 셔플
    matched_seniors = matched_seniors.sample(frac=1, random_state=None).reset_index(drop=True)

    matched_names = matched_seniors['student_name'].tolist()

    df_all_months = get_all_months_data()
    df_matched_timeline = df_all_months[df_all_months['student_name'].isin(matched_names)]

    # 선배들의 1월 ~ 11월 추이선 딕셔너리 빌드 (2월 공백 완벽 방어)
    timeline_stats = {}
    last_valid_senior_score = None

    for m in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
        m_df = df_matched_timeline[df_matched_timeline['month'] == m]
        avg_score = m_df['total_score'].mean() if not m_df.empty else None

        if avg_score is None or pd.isna(avg_score) or np.isnan(avg_score):
            if last_valid_senior_score is not None:
                avg_score = last_valid_senior_score
            else:
                global_m_df = df_all_months[df_all_months['month'] == m]
                avg_score = global_m_df['total_score'].mean() if not global_m_df.empty else 0.0

        final_score = round(float(avg_score), 1) if not pd.isna(avg_score) else 0.0
        timeline_stats[f"{m}월"] = final_score
        last_valid_senior_score = final_score

    # 나의 1월 ~ 11월 추이선 딕셔너리 빌드 (2월 공백 완벽 방어)
    df_my = get_my_all_months_data(student_name)
    my_timeline_stats = {}
    last_valid_my_score = None

    for m in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]:
        my_m_df = df_my[df_my['month'] == m]

        if not my_m_df.empty:
            avg_my_score = round(float(my_m_df['total_score'].iloc[0]), 1)
            my_timeline_stats[f"{m}월"] = avg_my_score
            last_valid_my_score = avg_my_score
        else:
            if last_valid_my_score is not None:
                my_timeline_stats[f"{m}월"] = last_valid_my_score
            else:
                my_timeline_stats[f"{m}월"] = None

    # === [들여쓰기 고정 완료] 매칭 확률 높은 TOP 10 대학 및 학과별 분포 추출 로직 ===
        # === [수정] 매칭 확률 높은 TOP 10 대학 및 학과별 분포 추출 로직 ===
        top_univ_names = matched_seniors['univ'].value_counts().head(10).index.tolist()
        univ_details = []

        for univ in top_univ_names:
            univ_df = matched_seniors[matched_seniors['univ'] == univ]
            major_groups = univ_df.groupby('major')
            major_list = []

            for major_name, group in major_groups:
                score_details = []
                for _, row in group.iterrows():
                    short_year = f"{str(row['year'])[2:]}'"

                    score_details.append({
                        "year": short_year,
                        "name": row['student_name'],
                        "grammar": float(row['grammar']),
                        "vocabulary": float(row['vocabulary']),
                        "logic": float(row['logic']),
                        "reading": float(row['reading']),
                        "total": float(row['total_score'])
                    })

                major_list.append({
                    "major": major_name,
                    "count": int(len(group)),
                    "scores": score_details
                })

            major_list = sorted(major_list, key=lambda x: x['count'], reverse=True)
            univ_details.append({
                "univ": univ,
                "total_count": int(len(univ_df)),
                "majors": major_list
            })

        # 🌟 [수정] 상세 목록용 리스트 생성 시 딱 상위 10명만 자르기 (.head(10) 추가)
        # === main.py 파일의 최하단 이 부분을 찾아서 수정해 주세요 ===
        senior_list = []
        for _, row in matched_seniors.head(10).iterrows():
            senior_list.append({
                "year": int(row['year']),
                "univ": row['univ'],
                "major": row['major'],
                "department": row['department'],
                "scores": {
                    "name": row['student_name'],  # 🌟 여기에 이름을 직접 꽂아서 프론트로 넘겨버립니다!
                    "grammar": float(row['grammar']),
                    "vocabulary": float(row['vocabulary']),
                    "logic": float(row['logic']),
                    "reading": float(row['reading']),
                    "total": float(row['total_score'])
                }
            })

        return {
            "status": "success",
            "month_averages": month_averages,
            "timeline_stats": timeline_stats,
            "my_timeline_stats": my_timeline_stats,
            "univ_details": univ_details,
            "all_seniors": senior_list
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
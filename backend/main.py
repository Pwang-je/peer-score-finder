from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pymysql
import numpy as np
from sklearn.neighbors import NearestNeighbors

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Local DB_Config
# DB_CONFIG = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'wogns1224',
#     'db': 'peer_data',
#     'charset': 'utf8mb4'
# }

# TiDB Config
# TiDB Config
DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'db': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}  # TiDB 연결 시 필수
}


def get_db_data(month: int):
    conn = pymysql.connect(**DB_CONFIG)
    # ⚠️ student_scores -> peer_data 로 변경
    query = f"""
        SELECT year, student_name, total_score, grammar, vocabulary, logic, reading, univ, major, department 
        FROM peer_data 
        WHERE month = {month} AND year < 2026 AND univ != '' AND univ IS NOT NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")


def get_all_months_data():
    conn = pymysql.connect(**DB_CONFIG)
    # ⚠️ student_scores -> peer_data 로 변경
    query = "SELECT student_name, month, total_score FROM peer_data WHERE year < 2026 AND univ != '' AND univ IS NOT NULL"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")


def get_my_all_months_data(student_name: str):
    conn = pymysql.connect(**DB_CONFIG)
    # ⚠️ student_scores -> peer_data 로 변경
    query = f"""
        SELECT month, total_score 
        FROM peer_data 
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
    # ⚠️ student_scores -> peer_data 로 변경
    query = """
        SELECT DISTINCT student_name 
        FROM peer_data 
        WHERE year = 2026 AND student_name LIKE %s
        LIMIT 10
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (f"%{keyword}%",))
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print("이름 검색 에러:", e)
        return []
    finally:
        conn.close()


# 2. 선택된 학생의 특정 달 성적 단건 조회 API
@app.get("/get-student-score")
def get_student_score(student_name: str, month: int):
    conn = pymysql.connect(**DB_CONFIG)
    # ⚠️ student_scores -> peer_data 로 변경
    query = """
        SELECT grammar, vocabulary, logic, reading, total_score 
        FROM peer_data 
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
# predict 로 불러오기
@app.get("/predict")
# 3. 유사 성적 합격자 예측 및 종합 분석 API (가중치 파라미터 추가)
@app.get("/predict")
def predict_university(
        month: int,
        grammar: float,
        vocabulary: float,
        logic: float,
        reading: float,
        student_name: str,
        w_grammar: float = 1.0,
        w_vocabulary: float = 1.0,
        w_logic: float = 1.0,
        w_reading: float = 1.0
):
    df_raw = get_db_data(month)
    if df_raw.empty:
        return {"status": "error", "message": "해당 월의 데이터가 없습니다."}

    month_averages = {
        "grammar": round(float(df_raw['grammar'].mean()), 1),
        "vocabulary": round(float(df_raw['vocabulary'].mean()), 1),
        "logic": round(float(df_raw['logic'].mean()), 1),
        "reading": round(float(df_raw['reading'].mean()), 1),
        "total": round(float(df_raw['total_score'].mean()), 1)
    }

    df_past = df_raw.copy()
    features = ['grammar', 'vocabulary', 'logic', 'reading']

    # 🌟 가중치 벡터 적용 (과목별 중요도에 비례하여 공간 확장)
    weights = np.array([w_grammar, w_vocabulary, w_logic, w_reading])
    X_past_weighted = df_past[features].values * weights
    current_student_weighted = np.array([[grammar, vocabulary, logic, reading]]) * weights

    # KNN 모델 빌드 (가중치가 적용된 피처 공간에서 이웃 탐색)
    n_neighbors = min(100, len(df_past))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    knn.fit(X_past_weighted)

    distances, indices = knn.kneighbors(current_student_weighted)
    matched_seniors = df_past.iloc[indices[0]].copy()

    # 중복 제거
    matched_seniors = matched_seniors.drop_duplicates(subset=['student_name', 'total_score'])
    matched_seniors = matched_seniors.sample(frac=1, random_state=None).reset_index(drop=True)

    matched_names = matched_seniors['student_name'].tolist()

    df_all_months = get_all_months_data()
    df_matched_timeline = df_all_months[df_all_months['student_name'].isin(matched_names)]

    # 1) 선배들의 1월 ~ 11월 추이선
    timeline_stats = {}
    last_valid_senior_score = None

    for m in range(1, 12):
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

    # 2) 나의 1월 ~ 11월 추이선
    df_my = get_my_all_months_data(student_name)
    my_timeline_stats = {}

    for m in range(1, 12):
        my_m_df = df_my[df_my['month'] == m]
        if not my_m_df.empty:
            avg_my_score = round(float(my_m_df['total_score'].iloc[0]), 1)
            my_timeline_stats[f"{m}월"] = avg_my_score
        else:
            my_timeline_stats[f"{m}월"] = None

    # 3) TOP 10 대학 및 학과별 분포 추출
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

    # 4) 상세 목록 상위 10명
    senior_list = []
    for _, row in matched_seniors.head(10).iterrows():
        senior_list.append({
            "year": int(row['year']),
            "univ": row['univ'],
            "major": row['major'],
            "department": row['department'],
            "scores": {
                "name": row['student_name'],
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
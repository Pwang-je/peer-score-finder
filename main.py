from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pymysql
import numpy as np  # 🌟 NaN 체크를 위해 추가
from sklearn.neighbors import NearestNeighbors

app = FastAPI()

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
    query = f"SELECT year, student_name, total_score, grammar, vocabulary, logic, reading, univ, major, department FROM student_scores WHERE month = {month}"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")


def get_all_months_data():
    conn = pymysql.connect(**DB_CONFIG)
    query = "SELECT student_name, month, total_score FROM student_scores WHERE univ != '' AND univ IS NOT NULL"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")


@app.get("/predict")
def predict_university(month: int, grammar: float, vocabulary: float, logic: float, reading: float):
    df_raw = get_db_data(month)
    if df_raw.empty:
        return {"status": "error", "message": "해당 월의 데이터가 없습니다."}

    month_averages = {
        "grammar": round(df_raw['grammar'].mean(), 1),
        "vocabulary": round(df_raw['vocabulary'].mean(), 1),
        "logic": round(df_raw['logic'].mean(), 1),
        "reading": round(df_raw['reading'].mean(), 1),
        "total": round(df_raw['total_score'].mean(), 1)
    }

    df_past = df_raw[df_raw['univ'] != ""].copy()
    if df_past.empty:
        return {"status": "error", "message": "해당 월의 과거 합격자 데이터가 부족합니다."}

    features = ['grammar', 'vocabulary', 'logic', 'reading']
    X_past = df_past[features]
    current_student = [[grammar, vocabulary, logic, reading]]

    n_neighbors = min(20, len(df_past))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    knn.fit(X_past)

    distances, indices = knn.kneighbors(current_student)
    matched_seniors = df_past.iloc[indices[0]].copy()

    matched_names = matched_seniors['student_name'].tolist()

    df_all_months = get_all_months_data()
    df_matched_timeline = df_all_months[df_all_months['student_name'].isin(matched_names)]

    # 🌟 [보안 및 수정] 3월부터 11월까지의 추이선 데이터 검증 로직 강화
    timeline_stats = {}
    last_valid_score = None  # 이전 달의 정상 점수를 백업할 변수

    for m in [3, 4, 5, 6, 7, 8, 9, 10, 11]:
        m_df = df_matched_timeline[df_matched_timeline['month'] == m]

        # 해당 월에 매칭된 선배들의 점수 평균 계산
        avg_score = m_df['total_score'].mean() if not m_df.empty else None

        # 만약 계산 결과가 NaN(결측치)이거나 데이터가 없다면 예외 처리
        if avg_score is None or pd.isna(avg_score) or np.isnan(avg_score):
            if last_valid_score is not None:
                # 1. 직전 달의 유효한 점수가 있다면 유동적으로 이어받음 (성적 유지)
                avg_score = last_valid_score
            else:
                # 2. 첫 달부터 없다면 전체 학생의 해당 월 평균 총점을 가져와 방어
                global_m_df = df_all_months[df_all_months['month'] == m]
                avg_score = global_m_df['total_score'].mean() if not global_m_df.empty else 0.0

        # 소수점 정돈 후 저장 및 백업
        final_score = round(float(avg_score), 1) if not pd.isna(avg_score) else 0.0
        timeline_stats[f"{m}월"] = final_score
        last_valid_score = final_score

    top_univ_names = matched_seniors['univ'].value_counts().head(6).index.tolist()
    univ_details = []
    for univ in top_univ_names:
        univ_df = matched_seniors[matched_seniors['univ'] == univ]
        major_groups = univ_df.groupby('major')
        major_list = []

        for major_name, group in major_groups:
            score_details = []
            for _, row in group.iterrows():
                score_details.append({
                    "grammar": float(row['grammar']),
                    "vocabulary": float(row['vocabulary']),
                    "logic": float(row['logic']),
                    "reading": float(row['reading']),
                    "total": float(row['total_score'])
                })
            major_list.append({"major": major_name, "count": len(group), "scores": score_details})

        major_list = sorted(major_list, key=lambda x: x['count'], reverse=True)
        univ_details.append({"univ": univ, "total_count": len(univ_df), "majors": major_list})

    senior_list = []
    for _, row in matched_seniors.iterrows():
        senior_list.append({
            "year": int(row['year']), "univ": row['univ'], "major": row['major'], "department": row['department'],
            "scores": {
                "grammar": float(row['grammar']), "vocabulary": float(row['vocabulary']),
                "logic": float(row['logic']), "reading": float(row['reading']), "total": float(row['total_score'])
            }
        })

    return {
        "status": "success",
        "month_averages": month_averages,
        "timeline_stats": timeline_stats,
        "univ_details": univ_details,
        "all_seniors": senior_list
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
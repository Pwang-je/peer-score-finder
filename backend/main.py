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

# TiDB Cloud DB 설정
DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'db': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}


def get_db_data(month: int):
    conn = pymysql.connect(**DB_CONFIG)
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
    query = "SELECT student_name, month, total_score FROM peer_data WHERE year < 2026 AND univ != '' AND univ IS NOT NULL"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")


def get_my_all_months_data(student_name: str):
    conn = pymysql.connect(**DB_CONFIG)
    query = f"""
        SELECT month, total_score 
        FROM peer_data 
        WHERE year = 2026 AND student_name = %s
    """
    df = pd.read_sql(query, conn, params=[student_name])
    conn.close()
    return df.fillna("")


# 🌟 [요구사항 2] 내 점수와 선배 점수를 비교해 구체적인 매칭 근거를 도출하는 헬퍼 함수
def generate_match_reason(my_scores: dict, senior_scores: dict) -> str:
    diffs = {
        '문법': abs(my_scores['grammar'] - senior_scores['grammar']),
        '어휘': abs(my_scores['vocabulary'] - senior_scores['vocabulary']),
        '논리': abs(my_scores['logic'] - senior_scores['logic']),
        '독해': abs(my_scores['reading'] - senior_scores['reading'])
    }

    # 점수 오차가 1.5점 이하인 완벽 매칭 과목
    identical_subs = [k for k, v in diffs.items() if v <= 1.5]
    total_diff = round(senior_scores['total'] - my_scores['total'], 1)

    reasons = []
    if len(identical_subs) >= 2:
        reasons.append(f"{', '.join(identical_subs[:2])} 득점 비중 일치")
    elif len(identical_subs) == 1:
        reasons.append(f"{identical_subs[0]} 점수 유사(오차 {diffs[identical_subs[0]]}점)")

    # 영역별 비중 최고점(주력 과목) 패턴 일치 여부
    my_max_sub = max(['grammar', 'vocabulary', 'logic', 'reading'], key=lambda k: my_scores[k])
    senior_max_sub = max(['grammar', 'vocabulary', 'logic', 'reading'], key=lambda k: senior_scores[k])

    sub_map = {'grammar': '문법', 'vocabulary': '어휘', 'logic': '논리', 'reading': '독해'}
    if my_max_sub == senior_max_sub:
        reasons.append(f"주력 득점 영역({sub_map.get(my_max_sub)}) 동일")

    # 총점 비교
    if abs(total_diff) == 0:
        reasons.append("총점 동일")
    elif total_diff > 0:
        reasons.append(f"총점 +{total_diff}점 차이")
    else:
        reasons.append(f"총점 {total_diff}점 차이")

    return " / ".join(reasons) if reasons else "4개 영역 밸런스 균등 유사"


# 🌟 [요구사항 1] 26년도 전체 학생 명단 가나다순 반환 API
@app.get("/all-students-2026")
def get_all_students_2026():
    conn = pymysql.connect(**DB_CONFIG)
    query = """
            SELECT DISTINCT student_name
            FROM peer_data
            WHERE year = 2026 AND student_name != '' AND student_name IS NOT NULL
            ORDER BY student_name ASC \
            """
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print("전체 학생 조회 에러:", e)
        return []
    finally:
        conn.close()


# 선택된 학생의 특정 달 성적 단건 조회 API
@app.get("/get-student-score")
def get_student_score(student_name: str, month: int):
    conn = pymysql.connect(**DB_CONFIG)
    query = """
            SELECT grammar, vocabulary, logic, reading, total_score
            FROM peer_data
            WHERE year = 2026 \
              AND student_name = %s \
              AND month = %s \
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


# 유사 성적 합격자 예측 및 종합 분석 API
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

    weights = np.array([w_grammar, w_vocabulary, w_logic, w_reading])
    X_past_weighted = df_past[features].values * weights
    current_student_weighted = np.array([[grammar, vocabulary, logic, reading]]) * weights

    n_neighbors = min(100, len(df_past))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    knn.fit(X_past_weighted)

    distances, indices = knn.kneighbors(current_student_weighted)
    matched_seniors = df_past.iloc[indices[0]].copy()

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

    # 내 점수 딕셔너리
    my_scores_dict = {
        'grammar': grammar,
        'vocabulary': vocabulary,
        'logic': logic,
        'reading': reading,
        'total': grammar + vocabulary + logic + reading
    }

    # 3) TOP 10 대학 및 학과별 분포 추출 (매칭 사유 주입)
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
                s_dict = {
                    "grammar": float(row['grammar']),
                    "vocabulary": float(row['vocabulary']),
                    "logic": float(row['logic']),
                    "reading": float(row['reading']),
                    "total": float(row['total_score'])
                }

                # 🌟 [요구사항 2] 각 매칭 선배별 구체적 매칭 근거 문구 생성
                reason = generate_match_reason(my_scores_dict, s_dict)

                score_details.append({
                    "year": short_year,
                    "name": row['student_name'],
                    "grammar": s_dict['grammar'],
                    "vocabulary": s_dict['vocabulary'],
                    "logic": s_dict['logic'],
                    "reading": s_dict['reading'],
                    "total": s_dict['total'],
                    "match_reason": reason
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

    # 4) 상세 목록 상위 10명 (매칭 사유 포함)
    senior_list = []
    for _, row in matched_seniors.head(10).iterrows():
        s_dict = {
            "grammar": float(row['grammar']),
            "vocabulary": float(row['vocabulary']),
            "logic": float(row['logic']),
            "reading": float(row['reading']),
            "total": float(row['total_score'])
        }
        senior_list.append({
            "year": int(row['year']),
            "univ": row['univ'],
            "major": row['major'],
            "department": row['department'],
            "scores": {
                "name": row['student_name'],
                "grammar": s_dict['grammar'],
                "vocabulary": s_dict['vocabulary'],
                "logic": s_dict['logic'],
                "reading": s_dict['reading'],
                "total": s_dict['total']
            },
            "match_reason": generate_match_reason(my_scores_dict, s_dict)
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
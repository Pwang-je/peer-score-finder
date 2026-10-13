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

# 예: ALLOWED_STUDENTS = ["하민정", "김철수", "이영희"]
# 빈 리스트 [] 로 두면 26년도 전체 학생이 출력됩니다.
ALLOWED_STUDENTS = [
    "강승현", "고시후", "고준형", "권도윤", "김가연_1", "김도현", "김민결", "김민재",
    "김병준", "김보승", "김서현", "김수겸", "김승은", "김승재", "김시윤", "김아진",
    "김예은", "김정섭", "김준호", "김지훈", "김진", "김진욱", "김태규", "김현빈",
    "류화윤", "문건호", "문빈", "박도현", "박선민", "박성호", "박우영", "박유경",
    "박진헌", "서하늘", "석유나", "성현서", "신재원", "심재인", "양은채", "유지원",
    "윤정한", "윤태경", "이규민", "이금담", "이민규", "이상호", "이솔", "이승찬",
    "이유림", "이은수", "이준기", "이하람", "이혁재", "임우진", "임재민", "임채영",
    "임태경", "임하준", "장율", "전승현", "전준형", "정시웅", "정연우", "정예림",
    "정의준", "조은서", "조인엽", "조하율", "조혜란", "채민석", "최상균", "최연준",
    "최윤지", "하민정", "하승민", "한지윤", "홍승훈", "홍시은", "홍채이", "황혜영"
]

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


# 🌟 특정 학생 명단만 반환하는 API
@app.get("/all-students-2026")
def get_all_students_2026():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        if ALLOWED_STUDENTS:
            # 지정된 특정 학생만 DB에 존재하는지 확인 후 가나다순 반환
            format_strings = ','.join(['%s'] * len(ALLOWED_STUDENTS))
            query = f"""
                SELECT DISTINCT student_name 
                FROM peer_data 
                WHERE year = 2026 AND student_name IN ({format_strings})
                ORDER BY student_name ASC
            """
            cursor.execute(query, tuple(ALLOWED_STUDENTS))
        else:
            query = """
                    SELECT DISTINCT student_name
                    FROM peer_data
                    WHERE year = 2026 AND student_name != '' AND student_name IS NOT NULL
                    ORDER BY student_name ASC \
                    """
            cursor.execute(query)

        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print("학생 목록 조회 에러:", e)
        return []
    finally:
        conn.close()


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

    # 선배들의 1월 ~ 11월 추이선
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

    # 나의 1월 ~ 11월 추이선
    df_my = get_my_all_months_data(student_name)
    my_timeline_stats = {}

    for m in range(1, 12):
        my_m_df = df_my[df_my['month'] == m]
        if not my_m_df.empty:
            avg_my_score = round(float(my_m_df['total_score'].iloc[0]), 1)
            my_timeline_stats[f"{m}월"] = avg_my_score
        else:
            my_timeline_stats[f"{m}월"] = None

    # TOP 10 대학 및 학과별 분포 추출 (산출 근거 텍스트 제거)
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

    # 상세 목록 상위 10명
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
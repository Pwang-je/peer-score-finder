from fastapi import FastAPI, UploadFile, File, Form
import io
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


# 엑셀로 업로드 가능하게 하는 코드
@app.post("/upload-scores")
async def upload_scores(file: UploadFile = File(...)):
    """
    엑셀(.xlsx) 또는 CSV 파일을 업로드 받아 TiDB peer_data 테이블에 일괄 적재/갱신
    필수 컬럼: year, month, student_name, total_score, grammar, vocabulary, logic, reading
    선택 컬럼: univ, major, department
    """
    try:
        contents = await file.read()
        filename = file.filename.lower()

        # 1. 파일 확장자에 따라 판다스 DataFrame으로 읽기
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(contents), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(contents), encoding="cp949")
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {"status": "error", "message": "지원하지 않는 파일 형식입니다. .xlsx 또는 .csv 파일을 업로드해 주세요."}

        # 2. 컬럼 공백 제거 및 소문자 정렬
        df.columns = df.columns.str.strip()

        # 필수 컬럼 체크
        required_cols = ['year', 'month', 'student_name', 'total_score', 'grammar', 'vocabulary', 'logic', 'reading']
        for col in required_cols:
            if col not in df.columns:
                return {"status": "error", "message": f"필수 컬럼 누락: '{col}' 열이 파일에 존재하지 않습니다."}

        # 선택 컬럼 기본값 처리
        for col in ['univ', 'major', 'department']:
            if col not in df.columns:
                df[col] = ""

        # 결측치 빈 문자열 및 기본값 처리
        df = df.fillna("")

        # 3. DB 연결 및 배치 INSERT / UPDATE
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """
              INSERT INTO peer_data (year, month, student_name, total_score, grammar, vocabulary, logic, reading, univ, \
                                     major, department)
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY \
              UPDATE \
                  total_score = \
              VALUES (total_score), grammar = \
              VALUES (grammar), vocabulary = \
              VALUES (vocabulary), logic = \
              VALUES (logic), reading = \
              VALUES (reading), univ = \
              VALUES (univ), major = \
              VALUES (major), department = \
              VALUES (department) \
              """

        rows_to_insert = []
        for _, row in df.iterrows():
            # 빈 행 스킵
            if not str(row['student_name']).strip() or not str(row['year']).strip():
                continue

            rows_to_insert.append((
                int(row['year']),
                int(row['month']),
                str(row['student_name']).strip(),
                float(row['total_score']) if row['total_score'] != "" else 0.0,
                float(row['grammar']) if row['grammar'] != "" else 0.0,
                float(row['vocabulary']) if row['vocabulary'] != "" else 0.0,
                float(row['logic']) if row['logic'] != "" else 0.0,
                float(row['reading']) if row['reading'] != "" else 0.0,
                str(row['univ']).strip(),
                str(row['major']).strip(),
                str(row['department']).strip()
            ))

        if not rows_to_insert:
            return {"status": "error", "message": "업로드할 유효한 데이터가 없습니다."}

        cursor.executemany(sql, rows_to_insert)
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "message": f"총 {len(rows_to_insert)}건의 성적 데이터가 성공적으로 반영되었습니다.",
            "count": len(rows_to_insert)
        }

    except Exception as e:
        print("엑셀 업로드 에러:", e)
        return {"status": "error", "message": f"업로드 처리 중 오류 발생: {str(e)}"}






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

    # 1. 넉넉하게 전체 풀에 대해 거리 계산 (최대 500명)
    n_neighbors = min(500, len(df_past))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    knn.fit(X_past_weighted)

    distances, indices = knn.kneighbors(current_student_weighted)
    all_matched = df_past.iloc[indices[0]].copy()
    all_matched['distance'] = distances[0]
    all_matched = all_matched.drop_duplicates(subset=['student_name', 'total_score'])

    # 🌟 2. [핵심] 연도별 강제 균등 쿼터 배분 (20, 21, 22년도 무조건 확보)
    # 데이터에 존재하는 연도별로 가장 가까운 순서대로 각 연도당 최대 15명씩 선발
    balanced_seniors_list = []
    available_years = sorted(all_matched['year'].unique())

    for y in available_years:
        year_df = all_matched[all_matched['year'] == y].sort_values(by='distance')
        # 각 연도별로 가장 점수가 가까운 12명씩 강제 추출
        balanced_seniors_list.append(year_df.head(12))

    # 연도별 대표 선배들 병합
    matched_seniors = pd.concat(balanced_seniors_list).reset_index(drop=True)

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

    # 3) TOP 10 대학 및 학과별 분포 추출 (과거 연도 선배 우선 포함 정렬)
    top_univ_names = matched_seniors['univ'].value_counts().head(10).index.tolist()
    univ_details = []
    top10_student_keys = set()

    for univ in top_univ_names:
        univ_df = matched_seniors[matched_seniors['univ'] == univ]
        major_groups = univ_df.groupby('major')
        major_list = []

        for major_name, group in major_groups:
            score_details = []
            # 🌟 학과 내에서도 연도가 골고루 보이도록 연도 오름차순(20년도부터)으로 정렬
            sorted_group = group.sort_values(by=['year', 'distance'], ascending=[True, True])

            for _, row in sorted_group.iterrows():
                short_year = f"{str(row['year'])[2:]}'"
                top10_student_keys.add(f"{row['year']}_{row['student_name']}")

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

    # 🌟 4) 하단 상세 목록: TOP 10 제외 + 과거 연도(20, 21, 22년) 선배들을 우선 배치
    senior_list = []
    # TOP 10에 없는 학생들만 추림
    remaining_seniors = all_matched[
        ~all_matched.apply(lambda r: f"{r['year']}_{r['student_name']}" in top10_student_keys, axis=1)]

    # 20~22년도 선배를 먼저 찾아서 넣고, 남은 자리를 23~25년도로 채움
    past_seniors = remaining_seniors[remaining_seniors['year'] <= 2022].sort_values(by='distance')
    recent_seniors = remaining_seniors[remaining_seniors['year'] > 2022].sort_values(by='distance')

    combined_remaining = pd.concat([past_seniors, recent_seniors]).reset_index(drop=True)

    for _, row in combined_remaining.head(10).iterrows():
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
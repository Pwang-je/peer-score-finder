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


def get_db_data(month: int, is_natural: bool = False):
    """과거 합격생 데이터 조회 (자연계열/인문계열 엄격 분기)"""
    conn = pymysql.connect(**DB_CONFIG)

    # 🌟 자연계열 학생: 과거 자연계열(일반자연, 학사자연, 자연) 합격생만 조회
    if is_natural:
        query = f"""
            SELECT year, student_name, total_score, grammar, vocabulary, logic, reading, math_total, univ, major, department 
            FROM peer_data 
            WHERE month = {month} AND year < 2026 
              AND department LIKE '%자연%'
              AND univ != '' AND univ IS NOT NULL
        """
    # 🌟 인문계열 학생: 과거 인문계열(일반인문, 학사인문, 인문) 합격생만 조회
    else:
        query = f"""
            SELECT year, student_name, total_score, grammar, vocabulary, logic, reading, math_total, univ, major, department 
            FROM peer_data 
            WHERE month = {month} AND year < 2026 
              AND (department LIKE '%인문%' OR (department NOT LIKE '%자연%' AND department != ''))
              AND univ != '' AND univ IS NOT NULL
        """
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")


def get_all_months_data(is_natural: bool = False):
    """추이선용 전체 월 과거 합격생 데이터 조회"""
    conn = pymysql.connect(**DB_CONFIG)
    if is_natural:
        query = """
                SELECT student_name, month, total_score, math_total
                FROM peer_data
                WHERE year \
                    < 2026
                  AND department LIKE '%자연%'
                  AND univ != '' \
                  AND univ IS NOT NULL \
                """
    else:
        query = """
                SELECT student_name, month, total_score, math_total
                FROM peer_data
                WHERE year \
                    < 2026
                  AND (department LIKE '%인문%' \
                   OR (department NOT LIKE '%자연%' \
                  AND department != ''))
                  AND univ != '' \
                  AND univ IS NOT NULL \
                """
    df = pd.read_sql(query, conn)
    conn.close()
    return df.fillna("")

def get_my_all_months_data(student_name: str):
    conn = pymysql.connect(**DB_CONFIG)
    query = """
        SELECT month, total_score, math_total 
        FROM peer_data 
        WHERE year = 2026 AND student_name = %s
    """
    df = pd.read_sql(query, conn, params=[student_name])
    conn.close()
    return df.fillna("")


# 엑셀/CSV 일괄 업로드
@app.post("/upload-scores")
async def upload_scores(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        filename = file.filename.lower()

        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(contents), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(contents), encoding="cp949")
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            return {"status": "error", "message": "지원하지 않는 파일 형식입니다. .xlsx 또는 .csv 파일을 업로드해 주세요."}

        df.columns = df.columns.str.strip()

        required_cols = ['year', 'month', 'student_name', 'total_score', 'grammar', 'vocabulary', 'logic', 'reading']
        for col in required_cols:
            if col not in df.columns:
                return {"status": "error", "message": f"필수 컬럼 누락: '{col}' 열이 파일에 존재하지 않습니다."}

        for col in ['univ', 'major', 'department']:
            if col not in df.columns:
                df[col] = ""
        if 'math_total' not in df.columns:
            df['math_total'] = None

        df = df.fillna("")

        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        sql = """
            INSERT INTO peer_data (year, month, student_name, total_score, grammar, vocabulary, logic, reading, math_total, univ, major, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                total_score = VALUES(total_score),
                grammar = VALUES(grammar),
                vocabulary = VALUES(vocabulary),
                logic = VALUES(logic),
                reading = VALUES(reading),
                math_total = VALUES(math_total),
                univ = VALUES(univ),
                major = VALUES(major),
                department = VALUES(department)
        """

        rows_to_insert = []
        for _, row in df.iterrows():
            if not str(row['student_name']).strip() or not str(row['year']).strip():
                continue

            math_val = None
            if row['math_total'] != "" and not pd.isna(row['math_total']):
                try:
                    math_val = float(row['math_total'])
                except ValueError:
                    math_val = None

            rows_to_insert.append((
                int(row['year']),
                int(row['month']),
                str(row['student_name']).strip(),
                float(row['total_score']) if row['total_score'] != "" else 0.0,
                float(row['grammar']) if row['grammar'] != "" else 0.0,
                float(row['vocabulary']) if row['vocabulary'] != "" else 0.0,
                float(row['logic']) if row['logic'] != "" else 0.0,
                float(row['reading']) if row['reading'] != "" else 0.0,
                math_val,
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


# 2026 학생 명단 반환 API
@app.get("/all-students-2026")
def get_all_students_2026():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        if ALLOWED_STUDENTS:
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
                ORDER BY student_name ASC
            """
            cursor.execute(query)

        rows = cursor.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print("학생 목록 조회 에러:", e)
        return []
    finally:
        conn.close()


# 🌟 선택된 학생의 성적 조회 및 자연계/인문계 자동 판정 API
@app.get("/get-student-score")
def get_student_score(student_name: str, month: int):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 1. 해당 학생의 2026년도 전체 시험 중 수학 점수가 0점 초과인 이력이 단 1번이라도 있는지 검사
        check_math_query = """
            SELECT COUNT(*) as math_count
            FROM peer_data
            WHERE year = 2026 AND student_name = %s AND math_total IS NOT NULL AND math_total > 0
        """
        cursor.execute(check_math_query, (student_name,))
        math_history = cursor.fetchone()
        has_math_history = (math_history['math_count'] > 0) if math_history else False

        # 2. 해당 월의 성적 조회
        query = """
            SELECT grammar, vocabulary, logic, reading, total_score, math_total, department
            FROM peer_data
            WHERE year = 2026 AND student_name = %s AND month = %s
        """
        cursor.execute(query, (student_name, month))
        result = cursor.fetchone()

        if result:
            # 🌟 자연계 자동 판정 규칙: 연중 수학 응시 이력이 있거나 department가 '자연'인 경우
            dept = result.get('department', '')
            is_natural = has_math_history or (dept == '자연')

            # math_total이 None일 경우 처리
            m_val = result.get('math_total')
            result['math_total'] = float(m_val) if (m_val is not None and m_val != '') else '-'

            return {
                "status": "success",
                "data": result,
                "is_natural": is_natural
            }
        else:
            return {
                "status": "empty",
                "message": "해당 월의 성적 데이터가 존재하지 않습니다.",
                "is_natural": has_math_history  # 성적이 없어도 이전 이력으로 계열은 전달
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# 🌟 계열별(인문/자연) 맞춤형 예측 및 KNN 종합 분석 API
@app.get("/predict")
def predict_university(
        month: int,
        grammar: float,
        vocabulary: float,
        logic: float,
        reading: float,
        student_name: str,
        math_total: float = 0.0,
        is_natural: bool = False,
        w_grammar: float = 1.0,
        w_vocabulary: float = 1.0,
        w_logic: float = 1.0,
        w_reading: float = 1.0,
        w_math: float = 2.0
):
    df_raw = get_db_data(month, is_natural=is_natural)
    if df_raw.empty:
        track_name = "자연계열" if is_natural else "인문계열"
        return {"status": "error", "message": f"{month}월의 {track_name} 합격생 데이터가 없습니다."}

    # 평균 점수 산출
    month_averages = {
        "grammar": round(float(pd.to_numeric(df_raw['grammar'], errors='coerce').mean()), 1),
        "vocabulary": round(float(pd.to_numeric(df_raw['vocabulary'], errors='coerce').mean()), 1),
        "logic": round(float(pd.to_numeric(df_raw['logic'], errors='coerce').mean()), 1),
        "reading": round(float(pd.to_numeric(df_raw['reading'], errors='coerce').mean()), 1),
        "total": round(float(pd.to_numeric(df_raw['total_score'], errors='coerce').mean()), 1)
    }
    if is_natural:
        math_series = pd.to_numeric(df_raw['math_total'], errors='coerce').dropna()
        month_averages["math"] = round(float(math_series.mean()), 1) if not math_series.empty else 0.0

    df_past = df_raw.copy()

    # 🌟 피처 및 가중치 설정 (자연: 5차원, 인문: 4차원)
    if is_natural:
        features = ['grammar', 'vocabulary', 'logic', 'reading', 'math_total']
        for col in features:
            df_past[col] = pd.to_numeric(df_past[col], errors='coerce').fillna(0.0)

        weights = np.array([w_grammar, w_vocabulary, w_logic, w_reading, w_math])
        X_past_weighted = df_past[features].values * weights
        current_student_weighted = np.array([[grammar, vocabulary, logic, reading, math_total]]) * weights
    else:
        features = ['grammar', 'vocabulary', 'logic', 'reading']
        for col in features:
            df_past[col] = pd.to_numeric(df_past[col], errors='coerce').fillna(0.0)

        weights = np.array([w_grammar, w_vocabulary, w_logic, w_reading])
        X_past_weighted = df_past[features].values * weights
        current_student_weighted = np.array([[grammar, vocabulary, logic, reading]]) * weights

    # 1. KNN 거리 계산 (최대 500명 풀)
    n_neighbors = min(500, len(df_past))
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
    knn.fit(X_past_weighted)

    distances, indices = knn.kneighbors(current_student_weighted)
    all_matched = df_past.iloc[indices[0]].copy()
    all_matched['distance'] = distances[0]
    all_matched = all_matched.drop_duplicates(subset=['student_name', 'total_score', 'year'])

    # 2. 연도별 균등 쿼터 배분
    balanced_seniors_list = []
    valid_years = [int(y) for y in all_matched['year'].dropna().unique() if str(y).isdigit()]

    for y in sorted(valid_years):
        year_df = all_matched[all_matched['year'] == y].sort_values(by='distance')
        if not year_df.empty:
            balanced_seniors_list.append(year_df.head(12))

    if balanced_seniors_list:
        matched_seniors = pd.concat(balanced_seniors_list).reset_index(drop=True)
    else:
        matched_seniors = all_matched.head(50).reset_index(drop=True)

    matched_names = matched_seniors['student_name'].tolist()
    df_all_months = get_all_months_data(is_natural=is_natural)
    df_matched_timeline = df_all_months[df_all_months['student_name'].isin(matched_names)]

    # 1) 선배들의 1월 ~ 11월 추이선 (영어 & 수학)
    timeline_stats = {}
    math_timeline_stats = {}
    last_valid_senior_score = None
    last_valid_senior_math = None

    for m in range(1, 12):
        m_df = df_matched_timeline[df_matched_timeline['month'] == m]

        # 영어 총점 평균
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

        # 🌟 수학 총점 평균
        if is_natural and 'math_total' in m_df.columns:
            m_valid = pd.to_numeric(m_df['math_total'], errors='coerce').dropna()
            m_valid = m_valid[m_valid > 0]
            avg_math = m_valid.mean() if not m_valid.empty else None
            if avg_math is None or pd.isna(avg_math) or np.isnan(avg_math):
                avg_math = last_valid_senior_math if last_valid_senior_math is not None else 0.0
            final_math = round(float(avg_math), 1)
            math_timeline_stats[f"{m}월"] = final_math
            last_valid_senior_math = final_math

    # 2) 나의 1월 ~ 11월 추이선 (영어 & 수학)
    my_timeline_stats = {}
    my_math_timeline_stats = {}
    total_input_score = grammar + vocabulary + logic + reading

    if student_name == "직접입력수험생":
        for m in range(1, 12):
            my_timeline_stats[f"{m}월"] = round(float(total_input_score), 1) if m == month else None
            my_math_timeline_stats[f"{m}월"] = round(float(math_total), 1) if (m == month and is_natural) else None
    else:
        df_my = get_my_all_months_data(student_name)
        for m in range(1, 12):
            my_m_df = df_my[df_my['month'] == m]
            if not my_m_df.empty:
                my_timeline_stats[f"{m}월"] = round(float(my_m_df['total_score'].iloc[0]), 1)

                # 수학
                if is_natural and 'math_total' in my_m_df.columns:
                    raw_m = my_m_df['math_total'].iloc[0]
                    my_math_timeline_stats[f"{m}월"] = round(float(raw_m), 1) if (
                                raw_m is not None and str(raw_m).strip() != '' and float(raw_m) > 0) else None
            else:
                my_timeline_stats[f"{m}월"] = None
                my_math_timeline_stats[f"{m}월"] = None

    # 3) TOP 10 대학 및 학과별 분포 추출
    top_univ_names = matched_seniors['univ'].value_counts().head(10).index.tolist()
    univ_details = []
    top10_student_keys = set()

    for univ in top_univ_names:
        univ_df = matched_seniors[matched_seniors['univ'] == univ]
        major_groups = univ_df.groupby('major')
        major_list = []

        for major_name, group in major_groups:
            score_details = []
            sorted_group = group.sort_values(by=['year', 'distance'], ascending=[True, True])

            for _, row in sorted_group.iterrows():
                short_year = f"{str(row['year'])[2:]}'"
                top10_student_keys.add(f"{row['year']}_{row['student_name']}")

                m_score = row.get('math_total', None)
                m_score_val = float(m_score) if (m_score is not None and m_score != '') else None

                score_details.append({
                    "year": short_year,
                    "name": row['student_name'],
                    "grammar": float(row['grammar']),
                    "vocabulary": float(row['vocabulary']),
                    "logic": float(row['logic']),
                    "reading": float(row['reading']),
                    "math": m_score_val,
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


    return {
        "status": "success",
        "is_natural": is_natural,
        "month_averages": month_averages,
        "timeline_stats": timeline_stats,
        "math_timeline_stats": math_timeline_stats,
        "my_timeline_stats": my_timeline_stats,
        "my_math_timeline_stats": my_math_timeline_stats,
        "univ_details": univ_details
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
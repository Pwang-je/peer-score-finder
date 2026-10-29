from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import io
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

INVALID_VALUES = ['미기재', '', ' ', '-', 'nan', 'NaN', 'None', 'null', 'NULL']


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    rename_dict = {}
    for c in df.columns:
        c_low = c.lower()
        if "student" in c_low or "이름" in c:
            rename_dict[c] = "student_name"
        elif c_low in ["year", "연도", "년도"]:
            rename_dict[c] = "year"
        elif c_low in ["month", "월"]:
            rename_dict[c] = "month"
        elif c_low in ["department", "계열"]:
            rename_dict[c] = "department"
        elif c_low in ["major", "학과"]:
            rename_dict[c] = "major"
        elif c_low in ["univ", "대학"]:
            rename_dict[c] = "univ"
        elif c_low in ["center", "분원"]:
            rename_dict[c] = "center"
    df = df.rename(columns=rename_dict)

    for col in ['department', 'major', 'univ', 'center']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace(INVALID_VALUES, np.nan)

    return df


def get_db_data(month: int, is_natural: bool = False):
    conn = pymysql.connect(**DB_CONFIG)
    if is_natural:
        query = f"""
            SELECT year, student_name, total_score, grammar, vocabulary, logic, reading, math_total, univ, major, department 
            FROM peer_data 
            WHERE month = {month} AND year < 2026 
              AND department LIKE '%자연%'
              AND univ != '' AND univ IS NOT NULL
        """
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

    # 문자열 컬럼만 공백 채우기
    str_cols = ['student_name', 'univ', 'major', 'department']
    for c in str_cols:
        if c in df.columns:
            df[c] = df[c].fillna("")

    # 숫자 컬럼은 float 변환 (수학 점수 유실 방지)
    num_cols = ['total_score', 'grammar', 'vocabulary', 'logic', 'reading', 'math_total']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    return df


def get_all_months_data(is_natural: bool = False):
    conn = pymysql.connect(**DB_CONFIG)
    if is_natural:
        query = """
            SELECT student_name, month, total_score, math_total
            FROM peer_data
            WHERE year < 2026
              AND department LIKE '%자연%'
              AND univ != '' AND univ IS NOT NULL
        """
    else:
        query = """
            SELECT student_name, month, total_score, math_total
            FROM peer_data
            WHERE year < 2026
              AND (department LIKE '%인문%' OR (department NOT LIKE '%자연%' AND department != ''))
              AND univ != '' AND univ IS NOT NULL
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


# =====================================================================
# 엑셀 사전 검증(Dry-run) 및 적재 API
# =====================================================================
@app.post("/api/upload/validate")
async def validate_excel(file: UploadFile = File(...)):
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
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다. .xlsx 또는 .csv 파일을 업로드해 주세요.")

    df = normalize_df(df)
    total_rows = len(df)
    issues = {
        "duplicates": [],
        "missing_department": 0,
        "missing_major": 0,
        "auto_fixable_department": 0
    }

    if 'year' in df.columns and 'month' in df.columns and 'student_name' in df.columns:
        dup_mask = df.duplicated(subset=['year', 'month', 'student_name'], keep=False)
        if dup_mask.any():
            dup_df = df[dup_mask]
            for (yr, mo, name), group in dup_df.groupby(['year', 'month', 'student_name']):
                centers = group['center'].dropna().unique().tolist() if 'center' in group.columns else []
                depts = group['department'].dropna().unique().tolist() if 'department' in group.columns else []
                issues["duplicates"].append({
                    "year": int(yr),
                    "month": int(mo),
                    "name": str(name),
                    "count": len(group),
                    "centers": centers,
                    "departments": depts
                })

    if 'student_name' in df.columns and 'department' in df.columns:
        dept_missing_mask = df['department'].isna()
        issues["missing_department"] = int(dept_missing_mask.sum())

        valid_depts = df.dropna(subset=['department'])
        student_dept_map = valid_depts.groupby('student_name')['department'].agg(
            lambda x: x.mode().iloc[0] if not x.empty else np.nan
        ).to_dict()

        can_fix_count = df[dept_missing_mask & df['student_name'].isin(student_dept_map)].shape[0]
        issues["auto_fixable_department"] = int(can_fix_count)

    if 'major' in df.columns:
        issues["missing_major"] = int(df['major'].isna().sum())

    return {
        "filename": file.filename,
        "total_rows": total_rows,
        "duplicate_count": len(issues["duplicates"]),
        "issues": issues
    }


@app.post("/api/upload/commit")
async def commit_excel(
        file: UploadFile = File(...),
        resolve_duplicates_with_center: bool = Form(True),
        auto_fill_missing: bool = Form(True)
):
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
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    df = normalize_df(df)

    if auto_fill_missing:
        for col in ['department', 'major', 'univ']:
            if col in df.columns and 'student_name' in df.columns:
                valid_records = df.dropna(subset=[col])
                if not valid_records.empty:
                    info_map = valid_records.groupby('student_name')[col].agg(
                        lambda x: x.mode().iloc[0] if not x.empty else np.nan
                    ).to_dict()
                    df[col] = df[col].fillna(df['student_name'].map(info_map))
        df = df.fillna("")

    if resolve_duplicates_with_center and 'center' in df.columns:
        dup_mask = df.duplicated(subset=['year', 'month', 'student_name'], keep=False)
        if dup_mask.any():
            def make_unique_name(row):
                if dup_mask[row.name] and row.get('center') and row['center'] != '미기재':
                    return f"{row['student_name']}_{row['center']}"
                return row['student_name']

            df['student_name'] = df.apply(make_unique_name, axis=1)

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    sql = """
          INSERT INTO peer_data (year, month, student_name, total_score, grammar, vocabulary, logic, reading,
                                 math_total, univ, major, department)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
          ON DUPLICATE KEY UPDATE
              total_score = CASE WHEN VALUES(total_score) > 0 THEN VALUES(total_score) ELSE total_score END,
              grammar = CASE WHEN VALUES(grammar) > 0 THEN VALUES(grammar) ELSE grammar END,
              vocabulary = CASE WHEN VALUES(vocabulary) > 0 THEN VALUES(vocabulary) ELSE vocabulary END,
              logic = CASE WHEN VALUES(logic) > 0 THEN VALUES(logic) ELSE logic END,
              reading = CASE WHEN VALUES(reading) > 0 THEN VALUES(reading) ELSE reading END,
              math_total = CASE WHEN VALUES(math_total) IS NOT NULL AND VALUES(math_total) > 0 THEN VALUES(math_total) ELSE math_total END,
              univ = CASE WHEN VALUES(univ) != '' THEN VALUES(univ) ELSE univ END,
              major = CASE WHEN VALUES(major) != '' THEN VALUES(major) ELSE major END,
              department = CASE WHEN VALUES(department) != '' THEN VALUES(department) ELSE department END
          """

    rows_to_insert = []
    for _, row in df.iterrows():
        s_name = str(row.get('student_name', '')).strip()
        s_year = str(row.get('year', '')).strip()
        if not s_name or not s_year:
            continue

        math_val = None
        raw_m = row.get('math_total', None)
        if raw_m is not None and str(raw_m).strip() != "" and not pd.isna(raw_m):
            try:
                math_val = float(raw_m)
            except ValueError:
                math_val = None

        rows_to_insert.append((
            int(row['year']),
            int(row['month']),
            s_name,
            float(row.get('total_score', 0)) if row.get('total_score', '') != "" else 0.0,
            float(row.get('grammar', 0)) if row.get('grammar', '') != "" else 0.0,
            float(row.get('vocabulary', 0)) if row.get('vocabulary', '') != "" else 0.0,
            float(row.get('logic', 0)) if row.get('logic', '') != "" else 0.0,
            float(row.get('reading', 0)) if row.get('reading', '') != "" else 0.0,
            math_val,
            str(row.get('univ', '')).strip(),
            str(row.get('major', '')).strip(),
            str(row.get('department', '')).strip()
        ))

    if not rows_to_insert:
        conn.close()
        return {"status": "error", "message": "업로드할 유효한 데이터가 없습니다."}

    cursor.executemany(sql, rows_to_insert)
    conn.commit()
    inserted_count = cursor.rowcount
    cursor.close()
    conn.close()

    return {
        "status": "success",
        "message": f"총 {len(rows_to_insert)}건의 데이터가 정제되어 안전하게 DB에 적재되었습니다.",
        "count": len(rows_to_insert)
    }


@app.post("/upload-scores")
async def upload_scores(file: UploadFile = File(...)):
    return await commit_excel(file=file, resolve_duplicates_with_center=True, auto_fill_missing=True)


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


# =====================================================================
# 🌟 [오류 해결] 2026 재원생 성적 조회 및 자연/인문 자동 판정 API
# =====================================================================
@app.get("/get-student-score")
def get_student_score(student_name: str, month: int):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 1. 자연계 이력 확인 (연중 수학 점수 존재 여부 또는 계열 확인)
        check_query = """
            SELECT math_total, department
            FROM peer_data
            WHERE year = 2026 AND student_name = %s
        """
        cursor.execute(check_query, (student_name,))
        all_records = cursor.fetchall()

        has_math_history = False
        is_dept_natural = False

        for r in all_records:
            m_val = r.get('math_total')
            if m_val is not None and str(m_val).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    if float(m_val) > 0:
                        has_math_history = True
                except ValueError:
                    pass
            dept = str(r.get('department') or '')
            if '자연' in dept:
                is_dept_natural = True

        # 2. 해당 월 성적 조회 (가장 최근 등록된 유효 행 조회)
        query = """
            SELECT grammar, vocabulary, logic, reading, total_score, math_total, department
            FROM peer_data
            WHERE year = 2026 AND student_name = %s AND month = %s
            ORDER BY (CASE WHEN total_score IS NOT NULL AND total_score > 0 THEN 1 ELSE 0 END) DESC
            LIMIT 1
        """
        cursor.execute(query, (student_name, month))
        result = cursor.fetchone()

        if result:
            curr_dept = str(result.get('department') or '')
            is_natural = has_math_history or is_dept_natural or ('자연' in curr_dept)

            # 수학 점수 정밀 파싱
            raw_math = result.get('math_total')
            if raw_math is not None and str(raw_math).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    result['math_total'] = float(raw_math)
                except ValueError:
                    result['math_total'] = '-'
            else:
                result['math_total'] = '-'

            # 영어 영역 점수 숫자화
            for k in ['grammar', 'vocabulary', 'logic', 'reading', 'total_score']:
                val = result.get(k)
                if val is not None and str(val).strip() not in ['', 'None', 'nan', 'null', '-']:
                    try:
                        result[k] = float(val)
                    except ValueError:
                        result[k] = '-'
                else:
                    result[k] = '-'

            return {
                "status": "success",
                "data": result,
                "is_natural": is_natural
            }
        else:
            return {
                "status": "empty",
                "message": f"{student_name} 학생은 {month}월 데이터가 없습니다.",
                "is_natural": has_math_history or is_dept_natural
            }
    except Exception as e:
        print("get-student-score 에러:", e)
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# =====================================================================
# 🌟 [들여쓰기 완전 교정] KNN 종합 분석 API
# =====================================================================
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

    # 가중치 벡터 곱셈 (원본 df_past의 math_total을 보존)
    if is_natural:
        features = ['grammar', 'vocabulary', 'logic', 'reading', 'math_total']
        # 계산용 임시 행렬 생성
        X_mat = df_past[features].fillna(0.0).values
        weights = np.array([w_grammar, w_vocabulary, w_logic, w_reading, w_math])
        X_past_weighted = X_mat * weights
        current_student_weighted = np.array([[grammar, vocabulary, logic, reading, math_total]]) * weights
    else:
        features = ['grammar', 'vocabulary', 'logic', 'reading']
        X_mat = df_past[features].fillna(0.0).values
        weights = np.array([w_grammar, w_vocabulary, w_logic, w_reading])
        X_past_weighted = X_mat * weights
        current_student_weighted = np.array([[grammar, vocabulary, logic, reading]]) * weights

    # 1. KNN 거리 계산
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

    # 1) 선배들의 1월 ~ 11월 추이선
    timeline_stats = {}
    math_timeline_stats = {}
    last_valid_senior_score = None
    last_valid_senior_math = None

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

        if is_natural and 'math_total' in m_df.columns:
            m_valid = pd.to_numeric(m_df['math_total'], errors='coerce').dropna()
            m_valid = m_valid[m_valid > 0]
            avg_math = m_valid.mean() if not m_valid.empty else None
            if avg_math is None or pd.isna(avg_math) or np.isnan(avg_math):
                avg_math = last_valid_senior_math if last_valid_senior_math is not None else 0.0
            final_math = round(float(avg_math), 1)
            math_timeline_stats[f"{m}월"] = final_math
            last_valid_senior_math = final_math

    # 2) 나의 1월 ~ 11월 추이선
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
                if is_natural and 'math_total' in my_m_df.columns:
                    raw_m = my_m_df['math_total'].iloc[0]
                    my_math_timeline_stats[f"{m}월"] = round(float(raw_m), 1) if (
                            raw_m is not None and str(raw_m).strip() != '' and float(raw_m) > 0) else None
            else:
                my_timeline_stats[f"{m}월"] = None
                my_math_timeline_stats[f"{m}월"] = None

    # 3) TOP 10 대학 및 학과별 분포 추출 (들여쓰기 교정 완료)
    top_univ_names = matched_seniors['univ'].value_counts().head(10).index.tolist()
    univ_details = []
    top10_student_keys = set()

    for univ in top_univ_names:
        univ_df = matched_seniors[matched_seniors['univ'] == univ]

        u_avg_total = float(pd.to_numeric(univ_df['total_score'], errors='coerce').mean())
        diff_total = round(total_input_score - u_avg_total, 1)

        diff_math = None
        if is_natural and 'math_total' in univ_df.columns:
            u_math_series = pd.to_numeric(univ_df['math_total'], errors='coerce').dropna()
            u_math_series = u_math_series[u_math_series > 0]
            if not u_math_series.empty:
                diff_math = round(math_total - float(u_math_series.mean()), 1)

        u_avg_g = float(pd.to_numeric(univ_df['grammar'], errors='coerce').mean())
        u_avg_v = float(pd.to_numeric(univ_df['vocabulary'], errors='coerce').mean())
        u_avg_l = float(pd.to_numeric(univ_df['logic'], errors='coerce').mean())
        u_avg_r = float(pd.to_numeric(univ_df['reading'], errors='coerce').mean())

        gaps = {
            "total": diff_total,
            "math": diff_math,
            "grammar": round(grammar - u_avg_g, 1),
            "vocabulary": round(vocabulary - u_avg_v, 1),
            "logic": round(logic - u_avg_l, 1),
            "reading": round(reading - u_avg_r, 1)
        }

        major_groups = univ_df.groupby('major')
        major_list = []

        for major_name, group in major_groups:
            score_details = []
            sorted_group = group.sort_values(by=['year', 'distance'], ascending=[True, True])

            for _, row in sorted_group.iterrows():
                short_year = f"{str(row['year'])[2:]}'"
                top10_student_keys.add(f"{row['year']}_{row['student_name']}")

                raw_m = row.get('math_total', None)
                if pd.isna(raw_m) or raw_m is None or str(raw_m).strip() in ['', 'None', 'nan', '-']:
                    m_score_val = None
                else:
                    try:
                        m_score_val = float(raw_m)
                    except ValueError:
                        m_score_val = None

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
            "gaps": gaps,
            "majors": major_list
        })

    # 4) 취약/강점 파트 자동 진단 로직
    senior_avg_grammar = round(float(matched_seniors['grammar'].mean()), 1)
    senior_avg_vocab = round(float(matched_seniors['vocabulary'].mean()), 1)
    senior_avg_logic = round(float(matched_seniors['logic'].mean()), 1)
    senior_avg_reading = round(float(matched_seniors['reading'].mean()), 1)

    diagnostic_tags = []

    diff_g = round(grammar - senior_avg_grammar, 1)
    diff_v = round(vocabulary - senior_avg_vocab, 1)
    diff_l = round(logic - senior_avg_logic, 1)
    diff_r = round(reading - senior_avg_reading, 1)

    if diff_g <= -3.0:
        diagnostic_tags.append(
            {"type": "weak", "part_class": "grammar", "diff": diff_g, "text": f"문법 보완 시급 ({diff_g}점)"})
    elif diff_g >= 3.0:
        diagnostic_tags.append(
            {"type": "strong", "part_class": "grammar", "diff": diff_g, "text": f"문법 우수 (+{diff_g}점)"})

    if diff_v <= -2.5:
        diagnostic_tags.append({"type": "weak", "part_class": "vocab", "diff": diff_v, "text": f"어휘 보완 필요 ({diff_v}점)"})
    elif diff_v >= 2.5:
        diagnostic_tags.append({"type": "strong", "part_class": "vocab", "diff": diff_v, "text": f"어휘 강점 (+{diff_v}점)"})

    if diff_l <= -2.5:
        diagnostic_tags.append({"type": "weak", "part_class": "logic", "diff": diff_l, "text": f"논리 보완 필요 ({diff_l}점)"})
    elif diff_l >= 2.5:
        diagnostic_tags.append({"type": "strong", "part_class": "logic", "diff": diff_l, "text": f"논리 우수 (+{diff_l}점)"})

    if diff_r <= -4.0:
        diagnostic_tags.append(
            {"type": "weak", "part_class": "reading", "diff": diff_r, "text": f"독해 집중 보완 ({diff_r}점)"})
    elif diff_r >= 4.0:
        diagnostic_tags.append(
            {"type": "strong", "part_class": "reading", "diff": diff_r, "text": f"독해 견인 (+{diff_r}점)"})

    if is_natural:
        valid_math = pd.to_numeric(matched_seniors['math_total'], errors='coerce').dropna()
        valid_math = valid_math[valid_math > 0]
        if not valid_math.empty:
            senior_avg_math = round(float(valid_math.mean()), 1)
            diff_m = round(math_total - senior_avg_math, 1)
            if diff_m <= -8.0:
                diagnostic_tags.append(
                    {"type": "weak", "part_class": "math", "diff": diff_m, "text": f"수학 고득점 필요 ({diff_m}점)"})
            elif diff_m >= 8.0:
                diagnostic_tags.append(
                    {"type": "strong", "part_class": "math", "diff": diff_m, "text": f"수학 강세 (+{diff_m}점)"})

    if not diagnostic_tags:
        diagnostic_tags.append(
            {"type": "balanced", "part_class": "balanced", "diff": 0, "text": "영역별 균형 양호 (선배 평균 수렴)"})

    return {
        "status": "success",
        "is_natural": is_natural,
        "month_averages": month_averages,
        "timeline_stats": timeline_stats,
        "math_timeline_stats": math_timeline_stats,
        "my_timeline_stats": my_timeline_stats,
        "my_math_timeline_stats": my_math_timeline_stats,
        "univ_details": univ_details,
        "diagnostic_tags": diagnostic_tags
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
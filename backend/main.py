from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import pandas as pd
import pymysql
import re
from tidb_db import DB_CONFIG
import numpy as np
from sklearn.neighbors import NearestNeighbors
from pydantic import BaseModel
from typing import Optional, List


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

# DB 연결 헬퍼 함수 정의ㄹ
def get_db_connection():
    conn = pymysql.connect(**DB_CONFIG)
    # 딕셔너리 형태로 컬럼명을 받기 위해 cursorclass 기본 설정
    with conn.cursor() as cursor:
        cursor.execute("USE peer_data")
    return conn

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
            return sorted(list(set(ALLOWED_STUDENTS)))

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



# 2026 재원생 성적 조회 및 자연/인문 자동 판정 API

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


# 2026 재원생 1월~10월 월별 성적 및 요약 조회 API
@app.get("/api/student-monthly-scores")
def get_student_monthly_scores(student_name: str):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT month, total_score, math_total, department
            FROM peer_data
            WHERE year = 2026 AND student_name = %s
            ORDER BY month ASC, (CASE WHEN total_score IS NOT NULL AND total_score > 0 THEN 1 ELSE 0 END) DESC
        """
        cursor.execute(query, (student_name,))
        rows = cursor.fetchall()

        month_map = {}
        has_math_history = False
        is_dept_natural = False

        for r in rows:
            m = r.get("month")
            if not m or m in month_map:
                continue

            dept = str(r.get("department") or "")
            if "자연" in dept:
                is_dept_natural = True

            raw_eng = r.get("total_score")
            eng_val = None
            if raw_eng is not None and str(raw_eng).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    num = float(raw_eng)
                    if num > 0:
                        eng_val = num
                except ValueError:
                    pass

            raw_math = r.get("math_total")
            math_val = None
            if raw_math is not None and str(raw_math).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    num = float(raw_math)
                    if num > 0:
                        math_val = num
                        has_math_history = True
                except ValueError:
                    pass

            month_map[int(m)] = {
                "eng": eng_val,
                "math": math_val
            }

        is_natural = has_math_history or is_dept_natural

        # 1월부터 10월까지 점수 리스트 구성
        monthly_scores = []
        eng_scores_list = []
        math_scores_list = []
        latest_month = None
        latest_eng = None
        latest_math = None

        for m in range(1, 11):
            data = month_map.get(m, {"eng": None, "math": None})
            eng = data["eng"]
            math = data["math"]

            if eng is not None:
                eng_scores_list.append(eng)
                latest_month = m
                latest_eng = eng
            if math is not None:
                math_scores_list.append(math)
                if eng is None:
                    latest_month = m
                latest_math = math

            monthly_scores.append({
                "month": m,
                "eng": eng,
                "math": math
            })

        avg_eng = round(sum(eng_scores_list) / len(eng_scores_list), 1) if eng_scores_list else None
        avg_math = round(sum(math_scores_list) / len(math_scores_list), 1) if math_scores_list else None
        max_eng = max(eng_scores_list) if eng_scores_list else None
        max_math = max(math_scores_list) if math_scores_list else None

        return {
            "status": "success",
            "student_name": student_name,
            "is_natural": is_natural,
            "monthly_scores": monthly_scores,
            "summary": {
                "avg_eng": avg_eng,
                "avg_math": avg_math,
                "max_eng": max_eng,
                "max_math": max_math,
                "latest_month": latest_month,
                "latest_eng": latest_eng,
                "latest_math": latest_math,
                "test_count": len(eng_scores_list)
            }
        }
    except Exception as e:
        print("get_student_monthly_scores 에러:", e)
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()



# 과거 전체 합격생 세부 성적 캐시 (월별 1:1 다차원 매칭용)
PAST_FULL_RECORDS_CACHE = None

def get_cached_past_full_records():
    global PAST_FULL_RECORDS_CACHE
    if PAST_FULL_RECORDS_CACHE is not None:
        return PAST_FULL_RECORDS_CACHE

    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT year, student_name, month, grammar, vocabulary, logic, reading, total_score, math_total, department, univ, major
            FROM peer_data
            WHERE year < 2026 
              AND univ != '' AND univ IS NOT NULL AND univ NOT IN ('학교모름', '미기재', '기타')
              AND major != '' AND major IS NOT NULL AND major NOT IN ('None', 'nan', '미기재')
            ORDER BY year DESC, student_name ASC, month ASC
        """)
        rows = cursor.fetchall()
        from collections import defaultdict
        students = defaultdict(lambda: {
            'year': None,
            'student_name': '',
            'univ': '',
            'major': '',
            'department': '',
            'is_natural': False,
            'months': {}
        })
        for r in rows:
            key = (r['year'], r['student_name'])
            s = students[key]
            s['year'] = r['year']
            s['student_name'] = r['student_name']
            s['univ'] = r['univ']
            s['major'] = r['major']
            s['department'] = r.get('department') or ''

            dept = str(r.get('department') or '')
            if '자연' in dept:
                s['is_natural'] = True
            m_val = r.get('math_total')
            if m_val is not None and str(m_val).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    if float(m_val) > 0:
                        s['is_natural'] = True
                except ValueError:
                    pass

            m = r.get('month')
            if m:
                month_data = {}
                for k in ['grammar', 'vocabulary', 'logic', 'reading', 'total_score', 'math_total']:
                    val = r.get(k)
                    if val is not None and str(val).strip() not in ['', 'None', 'nan', 'null', '-']:
                        try:
                            month_data[k] = float(val)
                        except ValueError:
                            month_data[k] = None
                    else:
                        month_data[k] = None
                s['months'][int(m)] = month_data

        PAST_FULL_RECORDS_CACHE = students
        return students
    finally:
        conn.close()


# KNN 및 실제 응시 월 기반 종합 합격 예측 API
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

    # 1. 2026 재원생인 경우, 실제 응시한 모든 월(month)의 세부 성적 조회
    is_existing_student = (student_name and student_name != "직접입력수험생")
    my_all_records = {}

    if is_existing_student:
        conn = pymysql.connect(**DB_CONFIG)
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("""
                SELECT month, grammar, vocabulary, logic, reading, total_score, math_total, department
                FROM peer_data
                WHERE year = 2026 AND student_name = %s
                ORDER BY month ASC
            """, (student_name,))
            s_rows = cursor.fetchall()
            for r in s_rows:
                m = r.get('month')
                m_dict = {}
                has_any = False
                for k in ['grammar', 'vocabulary', 'logic', 'reading', 'total_score', 'math_total']:
                    val = r.get(k)
                    if val is not None and str(val).strip() not in ['', 'None', 'nan', 'null', '-']:
                        try:
                            m_dict[k] = float(val)
                            has_any = True
                        except ValueError:
                            m_dict[k] = None
                    else:
                        m_dict[k] = None
                if m and has_any:
                    my_all_records[int(m)] = m_dict
        finally:
            conn.close()

    target_tested_months = sorted(list(my_all_records.keys()))
    match_mode = "multi_month" if (is_existing_student and len(target_tested_months) >= 2) else "single_month"

    # 2. 매칭 실행: 다중 응시 월 매칭 vs 단일 월 KNN 매칭
    if match_mode == "multi_month":
        # 🌟 실제 응시한 모든 월 성적 기반 다차원 매칭
        past_students = get_cached_past_full_records()
        target_months_set = set(target_tested_months)
        matched_candidates = []

        for (p_year, p_name), p_info in past_students.items():
            # 계열 필터링 (자연계열이면 자연계열만, 인문계열이면 인문계열만)
            if p_info['is_natural'] != is_natural:
                continue

            p_months_dict = p_info['months']
            p_months_set = set(p_months_dict.keys())
            overlap_months = target_months_set.intersection(p_months_set)
            if not overlap_months:
                continue

            sum_diff = 0.0
            for m in overlap_months:
                t_m = my_all_records[m]
                p_m = p_months_dict[m]

                # 세부 영역별 가중치 적용 오차
                # 문법
                if t_m['grammar'] is not None and p_m['grammar'] is not None:
                    sum_diff += abs(t_m['grammar'] - p_m['grammar']) * w_grammar
                # 어휘
                if t_m['vocabulary'] is not None and p_m['vocabulary'] is not None:
                    sum_diff += abs(t_m['vocabulary'] - p_m['vocabulary']) * w_vocabulary
                # 논리
                if t_m['logic'] is not None and p_m['logic'] is not None:
                    sum_diff += abs(t_m['logic'] - p_m['logic']) * w_logic
                # 독해
                if t_m['reading'] is not None and p_m['reading'] is not None:
                    sum_diff += abs(t_m['reading'] - p_m['reading']) * w_reading
                # 총점 보정
                if t_m['total_score'] is not None and p_m['total_score'] is not None:
                    sum_diff += abs(t_m['total_score'] - p_m['total_score']) * 0.3

                # 수학 (자연계열)
                if is_natural:
                    if t_m['math_total'] is not None and p_m['math_total'] is not None:
                        sum_diff += abs(t_m['math_total'] - p_m['math_total']) * w_math
                    elif t_m['math_total'] is not None or p_m['math_total'] is not None:
                        sum_diff += 20.0 * w_math

            missing_months = len(target_months_set - overlap_months)
            cnt_diff = abs(len(p_months_set) - len(target_months_set))
            avg_overlap_diff = sum_diff / len(overlap_months)
            total_dist = avg_overlap_diff + (missing_months * 8.0) + (cnt_diff * 1.2)

            # 대표 기준 월(month) 점수 (없으면 가장 가까운 월 점수)
            rep_score = p_months_dict.get(month)
            if not rep_score:
                closest_m = min(p_months_dict.keys(), key=lambda x: abs(x - month))
                rep_score = p_months_dict[closest_m]

            matched_candidates.append({
                'year': p_year,
                'student_name': p_name,
                'univ': p_info['univ'],
                'major': p_info['major'],
                'department': p_info['department'],
                'grammar': rep_score.get('grammar') or 0.0,
                'vocabulary': rep_score.get('vocabulary') or 0.0,
                'logic': rep_score.get('logic') or 0.0,
                'reading': rep_score.get('reading') or 0.0,
                'total_score': rep_score.get('total_score') or 0.0,
                'math_total': rep_score.get('math_total'),
                'distance': round(total_dist, 2),
                'overlap_count': len(overlap_months)
            })

        matched_candidates.sort(key=lambda x: x['distance'])

        # 연도별 균등 쿼터 배분
        df_candidates = pd.DataFrame(matched_candidates)
        balanced_seniors_list = []
        if not df_candidates.empty:
            valid_years = [int(y) for y in df_candidates['year'].dropna().unique() if str(y).isdigit()]
            for y in sorted(valid_years, reverse=True):
                y_df = df_candidates[df_candidates['year'] == y].sort_values(by='distance')
                if not y_df.empty:
                    balanced_seniors_list.append(y_df.head(15))

        if balanced_seniors_list:
            matched_seniors = pd.concat(balanced_seniors_list).reset_index(drop=True)
        elif not df_candidates.empty:
            matched_seniors = df_candidates.head(50).reset_index(drop=True)
        else:
            matched_seniors = pd.DataFrame()

    else:
        # 단일 월 KNN 매칭 (기존 방식 개선)
        df_past = df_raw.copy()
        if is_natural:
            features = ['grammar', 'vocabulary', 'logic', 'reading', 'math_total']
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

        n_neighbors = min(500, len(df_past))
        knn = NearestNeighbors(n_neighbors=n_neighbors, metric='euclidean')
        knn.fit(X_past_weighted)
        distances, indices = knn.kneighbors(current_student_weighted)
        all_matched = df_past.iloc[indices[0]].copy()
        all_matched['distance'] = distances[0]
        all_matched = all_matched.drop_duplicates(subset=['student_name', 'total_score', 'year'])

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

    if matched_seniors.empty:
        return {"status": "error", "message": "조건에 맞는 합격생 데이터를 찾을 수 없습니다."}

    matched_names = matched_seniors['student_name'].tolist()
    df_all_months = get_all_months_data(is_natural=is_natural)
    df_matched_timeline = df_all_months[df_all_months['student_name'].isin(matched_names)]

    # 3. 기준 월(month) 과목별 평균 (매칭된 학생들의 해당 월 실제 평균 우선 산출)
    month_match_df = df_matched_timeline[df_matched_timeline['month'] == month]
    base_df = df_raw  # 기본 백업

    month_averages = {
        "grammar": round(float(pd.to_numeric(base_df['grammar'], errors='coerce').mean()), 1),
        "vocabulary": round(float(pd.to_numeric(base_df['vocabulary'], errors='coerce').mean()), 1),
        "logic": round(float(pd.to_numeric(base_df['logic'], errors='coerce').mean()), 1),
        "reading": round(float(pd.to_numeric(base_df['reading'], errors='coerce').mean()), 1),
        "total": round(float(pd.to_numeric(base_df['total_score'], errors='coerce').mean()), 1)
    }
    if is_natural:
        math_series = pd.to_numeric(base_df['math_total'], errors='coerce').dropna()
        month_averages["math"] = round(float(math_series.mean()), 1) if not math_series.empty else 0.0

    # 4. 1월 ~ 11월 추이선 생성 (전체 평균 오염 버그 수정: 매칭된 그룹의 실제 응시 점수만 반영)
    timeline_stats = {}
    math_timeline_stats = {}
    last_valid_senior_score = None
    last_valid_senior_math = None

    for m in range(1, 12):
        m_df = df_matched_timeline[df_matched_timeline['month'] == m]

        # 영어 점수
        if not m_df.empty:
            m_valid_eng = pd.to_numeric(m_df['total_score'], errors='coerce').dropna()
            m_valid_eng = m_valid_eng[m_valid_eng > 0]
            if not m_valid_eng.empty:
                avg_score = round(float(m_valid_eng.mean()), 1)
                last_valid_senior_score = avg_score
            else:
                avg_score = last_valid_senior_score
        else:
            avg_score = last_valid_senior_score

        timeline_stats[f"{m}월"] = avg_score

        # 수학 점수 (자연계열)
        if is_natural:
            if not m_df.empty and 'math_total' in m_df.columns:
                m_valid_math = pd.to_numeric(m_df['math_total'], errors='coerce').dropna()
                m_valid_math = m_valid_math[m_valid_math > 0]
                if not m_valid_math.empty:
                    avg_math = round(float(m_valid_math.mean()), 1)
                    last_valid_senior_math = avg_math
                else:
                    avg_math = last_valid_senior_math
            else:
                avg_math = last_valid_senior_math

            math_timeline_stats[f"{m}월"] = avg_math

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
                raw_eng = my_m_df['total_score'].iloc[0]
                my_timeline_stats[f"{m}월"] = round(float(raw_eng), 1) if (
                        raw_eng is not None and str(raw_eng).strip() != '' and float(raw_eng) > 0) else None
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
        "match_mode": match_mode,
        "tested_months": target_tested_months,
        "month_averages": month_averages,
        "timeline_stats": timeline_stats,
        "math_timeline_stats": math_timeline_stats,
        "my_timeline_stats": my_timeline_stats,
        "my_math_timeline_stats": my_math_timeline_stats,
        "univ_details": univ_details,
        "diagnostic_tags": diagnostic_tags
    }


# 원서 지원 전략, 모집요강 관련 API 추가

class ApplicationCreate(BaseModel):
    student_name: str
    univ: str
    major: str
    memo: Optional[str] = "적정"


# 0. student_applications 테이블 자동 보장 함수
# 0. student_applications 및 univ_eligibility 테이블 자동 보장 함수
def ensure_application_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS student_applications
                   (
                       id INT AUTO_INCREMENT PRIMARY KEY,
                       year INT NOT NULL DEFAULT 2026,
                       student_name VARCHAR(50) NOT NULL,
                       univ VARCHAR(50) NOT NULL,
                       major VARCHAR(50) NOT NULL,
                       memo VARCHAR(50) DEFAULT '적정',
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                       UNIQUE KEY uq_student_univ (year, student_name, univ)
                   );
                   """)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS univ_eligibility
                   (
                       univ VARCHAR(50) PRIMARY KEY,
                       eligibility_text TEXT,
                       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                   );
                   """)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS student_notes
                   (
                       student_name VARCHAR(50) PRIMARY KEY,
                       memo TEXT,
                       pref_major_1 VARCHAR(100) DEFAULT '',
                       pref_major_2 VARCHAR(100) DEFAULT '',
                       dislike_major VARCHAR(100) DEFAULT '',
                       toeic_score VARCHAR(50) DEFAULT '',
                       gpa_score VARCHAR(50) DEFAULT '',
                       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                   );
                   """)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS student_past_exam_scores
                   (
                       id INT AUTO_INCREMENT PRIMARY KEY,
                       student_name VARCHAR(50) NOT NULL,
                       univ VARCHAR(50) NOT NULL,
                       exam_year INT NOT NULL,
                       subject_type VARCHAR(20) DEFAULT '영어',
                       my_score FLOAT NOT NULL,
                       avg_score FLOAT NULL,
                       score_gap FLOAT NULL,
                       eng_score FLOAT NULL,
                       math_score FLOAT NULL,
                       percentile VARCHAR(30) DEFAULT '',
                       is_unofficial BOOLEAN DEFAULT TRUE,
                       memo VARCHAR(100) DEFAULT '',
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                       UNIQUE KEY uq_student_univ_year_subj (student_name, univ, exam_year, subject_type)
                   );
                   """)
    # 기존 테이블이 이미 있을 경우 대비 컬럼 추가
    cols_to_add = [
        ("pref_major_1", "VARCHAR(100) DEFAULT ''"),
        ("pref_major_2", "VARCHAR(100) DEFAULT ''"),
        ("dislike_major", "VARCHAR(100) DEFAULT ''"),
        ("toeic_score", "VARCHAR(50) DEFAULT ''"),
        ("gpa_score", "VARCHAR(50) DEFAULT ''"),
    ]
    for col_name, col_type in cols_to_add:
        try:
            cursor.execute(f"ALTER TABLE student_notes ADD COLUMN {col_name} {col_type};")
            conn.commit()
        except Exception:
            pass

    past_cols = [
        ("subject_type", "VARCHAR(20) DEFAULT '영어'"),
        ("eng_score", "FLOAT NULL"),
        ("math_score", "FLOAT NULL"),
    ]
    for col_name, col_type in past_cols:
        try:
            cursor.execute(f"ALTER TABLE student_past_exam_scores ADD COLUMN {col_name} {col_type};")
            conn.commit()
        except Exception:
            pass
    conn.commit()
    cursor.close()
    conn.close()


# 서버 시작 시 테이블 점검
try:
    ensure_application_tables()
except Exception as e:
    print(f"테이블 점검 알림: {e}")

# 대학별 모집요강/합격자 조회 서버 메모리 캐시
DEPT_CACHE = {}


# 1. 모집요강 등록 대학 목록
@app.get("/api/quota/univ-list")
def get_quota_univ_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT univ FROM recruit_quota WHERE year = 2026 ORDER BY univ ASC;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [r[0] if isinstance(r, tuple) else r["univ"] for r in rows]


def extract_major_variants(s: str) -> set:
    """학과명에서 접두어 분리, 괄호 분리 등을 거친 가능한 전공명 후보군 집합 생성"""
    if not s:
        return set()
    s = str(s).strip()
    variants = {s}

    # 1. 앞쪽 학부명/대학명 접두어 분리:
    # 예: '첨단소재·전자융합공학부 신소재물리전공' -> '신소재물리전공', 'Fine Arts학부 서양화전공' -> '서양화전공'
    # 가운뎃점(·), 공백, 영문 등이 포함된 학부명도 처리할 수 있도록 non-greedy 패턴 사용 (단, 단독 형태인 '법학부' 등은 유지)
    prefix_match = re.match(r'^.+?(?:학부|대학)\s+(.+)$', s)
    if prefix_match:
        variants.add(prefix_match.group(1).strip())

    # 2. 괄호 분리:
    # 예: '전자정보공학부(IT융합전공)' -> '전자정보공학부', 'IT융합전공'
    if '(' in s and ')' in s:
        in_paren = re.search(r'\(([^)]+)\)', s)
        out_paren = re.sub(r'\([^)]*\)', '', s).strip()
        if in_paren:
            variants.add(in_paren.group(1).strip())
        if out_paren:
            variants.add(out_paren)

    return variants


def normalize_major_core(s: str) -> str:
    """특수기호, 공백, 접미어(학전공/공학전공/공학과/학과/학부/전공/과)를 일관 제거한 핵심 키워드 반환"""
    if not s:
        return ""
    # 1. 특수기호 및 공백 제거
    clean_s = re.sub(r'[*()\[\]·•ㆍ/,\-_~\s]', '', str(s))
    if not clean_s:
        return ""
    # 2. 끝부분 접미어(학전공|공학전공|공학과|학과|학부|전공|과) 제거
    core = re.sub(r'(학전공|공학전공|공학과|학과|학부|전공|과)$', '', clean_s)
    return core if core else clean_s


def clean_major_name(s: str) -> str:
    """호환성을 위한 정규화 함수"""
    if not s:
        return ""
    variants = extract_major_variants(s)
    for v in variants:
        core = normalize_major_core(v)
        if core:
            return core
    return normalize_major_core(s)


def is_major_matched(target_major: str, past_major: str) -> bool:
    """recruit_quota 학과와 peer_data 과거 학과 간의 동일 전공 매칭 판정"""
    if not target_major or not past_major:
        return False

    # 1. 원본 특수기호/공백만 제거한 단순 비교
    t_raw = re.sub(r'[*()\[\]·•ㆍ/,\-_~\s]', '', str(target_major).strip())
    p_raw = re.sub(r'[*()\[\]·•ㆍ/,\-_~\s]', '', str(past_major).strip())
    if t_raw and t_raw == p_raw:
        return True

    # 2. 접두어/괄호 변형 추출 후 핵심 코어 키워드 일치 비교
    t_variants = extract_major_variants(target_major)
    p_variants = extract_major_variants(past_major)

    t_cores = {normalize_major_core(v) for v in t_variants if normalize_major_core(v)}
    p_cores = {normalize_major_core(v) for v in p_variants if normalize_major_core(v)}

    if t_cores & p_cores:
        return True

    return False


def format_score_val(v):
    if v is None:
        return None
    try:
        f = float(v)
        if f > 0:
            return int(f) if f.is_integer() else f
        return None
    except (ValueError, TypeError):
        return None


def format_eng_val(v):
    if v is None:
        return "-"
    try:
        f = float(v)
        if f > 0:
            return int(f) if f.is_integer() else f
        return v
    except (ValueError, TypeError):
        return v


# 2. 대학별 모집요강 + 해당 학과 지원 원생 명단(최신 성적 매핑) + 과거 합격생 통합 조회
@app.get("/api/quota/departments")
def get_quota_departments(univ: str = "가천대학교"):
    # 캐시에 있으면 DB 조회 없이 즉시 반환
    if univ in DEPT_CACHE:
        return DEPT_CACHE[univ]

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1) 해당 대학 최신 모집요강 연도 조회 및 학과/정원 조회
    cursor.execute("SELECT COALESCE(MAX(year), 2026) FROM recruit_quota WHERE univ = %s;", (univ,))
    max_year_row = cursor.fetchone()
    target_year = max_year_row[0] if (max_year_row and max_year_row[0]) else 2026

    cursor.execute("""
                   SELECT id, univ, department, major, general_quota, bachelor_quota
                   FROM recruit_quota
                   WHERE year = %s AND univ = %s
                   ORDER BY department DESC, major ASC;
                   """, (target_year, univ))
    depts = cursor.fetchall()

    # 2) 해당 대학에 원서를 넣은 2026 원생들 + 최신 성적 조인 조회
    cursor.execute("""
                   SELECT a.id          AS app_id,
                          a.student_name,
                          a.univ,
                          a.major,
                          a.memo,
                          p.department  AS student_dept,
                          COALESCE(p_eng.latest_eng, p.total_score)    AS eng_score,
                          COALESCE(p_math.latest_math, p.math_total)   AS math_score
                   FROM student_applications a
                            LEFT JOIN (
                        SELECT p1.student_name, p1.department, p1.total_score, p1.math_total
                        FROM peer_data p1
                                 INNER JOIN (SELECT student_name, MAX(month) AS max_month
                                             FROM peer_data
                                             WHERE year = 2026
                                             GROUP BY student_name) p2
                                            ON p1.student_name = p2.student_name AND p1.month = p2.max_month
                        WHERE p1.year = 2026) p ON a.student_name = p.student_name
                            LEFT JOIN (
                        SELECT pe.student_name, pe.total_score AS latest_eng
                        FROM peer_data pe
                                 INNER JOIN (SELECT student_name, MAX(month) AS max_e_month
                                             FROM peer_data
                                             WHERE year = 2026 AND total_score IS NOT NULL AND total_score > 0
                                             GROUP BY student_name) pe2
                                            ON pe.student_name = pe2.student_name AND pe.month = pe2.max_e_month
                        WHERE pe.year = 2026) p_eng ON a.student_name = p_eng.student_name
                            LEFT JOIN (
                        SELECT pm.student_name, pm.math_total AS latest_math
                        FROM peer_data pm
                                 INNER JOIN (SELECT student_name, MAX(month) AS max_m_month
                                             FROM peer_data
                                             WHERE year = 2026 AND math_total IS NOT NULL AND math_total > 0
                                             GROUP BY student_name) pm2
                                            ON pm.student_name = pm2.student_name AND pm.month = pm2.max_m_month
                        WHERE pm.year = 2026) p_math ON a.student_name = p_math.student_name
                   WHERE a.year = 2026
                     AND a.univ = %s;
                   """, (univ,))
    apps = cursor.fetchall()

    # 3) 과거 합격생 조회 (target_year 이전)
    cursor.execute("""
                   SELECT p1.year,
                          p1.student_name,
                          p1.univ,
                          p1.major,
                          p1.department,
                          p1.total_score AS eng_score,
                          COALESCE(p1.math_total, p_math.latest_math)  AS math_score
                   FROM peer_data p1
                            INNER JOIN (SELECT year, student_name, MAX(month) AS max_month
                                        FROM peer_data
                                        WHERE year < %s
                                          AND univ = %s
                                          AND major IS NOT NULL AND major != '' AND major != '-' AND major != '미기재'
                                        GROUP BY year, student_name) p2
                                       ON p1.year = p2.year AND p1.student_name = p2.student_name AND p1.month = p2.max_month
                            LEFT JOIN (
                                 SELECT pm.year, pm.student_name, pm.math_total AS latest_math
                                 FROM peer_data pm
                                          INNER JOIN (SELECT year, student_name, MAX(month) AS max_m_month
                                                      FROM peer_data
                                                      WHERE year < %s AND math_total IS NOT NULL AND math_total > 0
                                                      GROUP BY year, student_name) pm2
                                                      ON pm.year = pm2.year AND pm.student_name = pm2.student_name AND pm.month = pm2.max_m_month
                                 WHERE pm.year < %s) p_math
                                 ON p1.year = p_math.year AND p1.student_name = p_math.student_name
                   WHERE p1.year < %s
                     AND p1.univ = %s
                     AND p1.major IS NOT NULL AND p1.major != '' AND p1.major != '-' AND p1.major != '미기재'
                   ORDER BY p1.year DESC, p1.total_score DESC;
                   """, (target_year, univ, target_year, target_year, target_year, univ))
    past_rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # 4) 학과별 지원자 리스트 및 과거 합격생 매칭 그룹핑
    result = []
    matched_past_indices = set()

    for d in depts:
        d_id = d[0] if isinstance(d, tuple) else d["id"]
        d_univ = d[1] if isinstance(d, tuple) else d["univ"]
        d_dept = d[2] if isinstance(d, tuple) else d["department"]
        d_major = d[3] if isinstance(d, tuple) else d["major"]
        d_gen = d[4] if isinstance(d, tuple) else d["general_quota"]
        d_bac = d[5] if isinstance(d, tuple) else d["bachelor_quota"]

        dept_apps = []
        for app in apps:
            app_major = app[3] if isinstance(app, tuple) else app["major"]
            if app_major == d_major:
                s_name = app[1] if isinstance(app, tuple) else app["student_name"]
                s_memo = app[4] if isinstance(app, tuple) else app["memo"]
                s_dept = (app[5] if isinstance(app, tuple) else app["student_dept"]) or ""
                eng = app[6] if isinstance(app, tuple) else app["eng_score"]
                math = app[7] if isinstance(app, tuple) else app["math_score"]

                apply_type = "학사" if "학사" in s_dept else "일반"

                dept_apps.append({
                    "app_id": app[0] if isinstance(app, tuple) else app["app_id"],
                    "student_name": s_name,
                    "type": apply_type,
                    "dept_full": s_dept,
                    "eng": format_eng_val(eng),
                    "math": format_score_val(math),
                    "memo": s_memo
                })

        target_clean = clean_major_name(d_major)
        dept_past = []
        seen_past = set()
        for idx_p, p in enumerate(past_rows):
            p_year = p[0] if isinstance(p, tuple) else p["year"]
            p_name = p[1] if isinstance(p, tuple) else p["student_name"]
            p_univ = p[2] if isinstance(p, tuple) else p["univ"]
            p_major = p[3] if isinstance(p, tuple) else p["major"]
            p_dept = (p[4] if isinstance(p, tuple) else p["department"]) or ""
            p_eng = p[5] if isinstance(p, tuple) else p["eng_score"]
            p_math = p[6] if isinstance(p, tuple) else p["math_score"]

            if is_major_matched(d_major, p_major):
                matched_past_indices.add(idx_p)
                key = (p_year, p_name)
                if key not in seen_past:
                    seen_past.add(key)
                    apply_type = "학사" if "학사" in p_dept else "일반"
                    dept_past.append({
                        "year": int(p_year),
                        "student_name": p_name,
                        "type": apply_type,
                        "dept_full": p_dept,
                        "eng": format_eng_val(p_eng),
                        "math": format_score_val(p_math),
                        "major": p_major
                    })

        result.append({
            "id": d_id,
            "univ": d_univ,
            "dept": d_dept,
            "major": d_major,
            "gen": d_gen,
            "bac": d_bac,
            "applicants": dept_apps,
            "past_admissions": dept_past,
            "is_closed": bool((d_gen is None or d_gen == 0) and (d_bac is None or d_bac == 0))
        })

    # 5) 현행 모집요강(recruit_quota)에 매칭되지 않은 과거 학과(미모집/개편 학과) 추출
    unmatched_by_major = {}
    for idx_p, p in enumerate(past_rows):
        if idx_p in matched_past_indices:
            continue
        p_year = p[0] if isinstance(p, tuple) else p["year"]
        p_name = p[1] if isinstance(p, tuple) else p["student_name"]
        p_univ = p[2] if isinstance(p, tuple) else p["univ"]
        p_major = p[3] if isinstance(p, tuple) else p["major"]
        p_dept = (p[4] if isinstance(p, tuple) else p["department"]) or ""
        p_eng = p[5] if isinstance(p, tuple) else p["eng_score"]
        p_math = p[6] if isinstance(p, tuple) else p["math_score"]

        if not p_major:
            continue

        if p_major not in unmatched_by_major:
            unmatched_by_major[p_major] = {
                "univ": p_univ or univ,
                "students": [],
                "seen": set()
            }

        key = (p_year, p_name)
        if key not in unmatched_by_major[p_major]["seen"]:
            unmatched_by_major[p_major]["seen"].add(key)
            apply_type = "학사" if "학사" in p_dept else "일반"
            unmatched_by_major[p_major]["students"].append({
                "year": int(p_year),
                "student_name": p_name,
                "type": apply_type,
                "dept_full": p_dept,
                "eng": format_eng_val(p_eng),
                "math": format_score_val(p_math),
                "major": p_major
            })

    for p_major, info in sorted(unmatched_by_major.items(), key=lambda x: x[0]):
        is_nat = any("자연" in s["dept_full"] for s in info["students"])
        is_hum = any("인문" in s["dept_full"] for s in info["students"])
        if is_nat and not is_hum:
            dept_cat = "자연"
        elif is_hum and not is_nat:
            dept_cat = "인문"
        else:
            dept_cat = "자연" if any(w in p_major for w in ["공학", "건축", "소프트", "컴퓨터", "생명", "수학", "물리", "화학", "의예", "간호", "전자", "정보", "기계"]) else "인문"

        def _sort_score(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return 0.0

        info["students"].sort(key=lambda s: (s["year"], _sort_score(s["eng"])), reverse=True)

        result.append({
            "id": f"closed-{univ}-{p_major}",
            "univ": univ,
            "dept": dept_cat,
            "major": p_major,
            "gen": 0,
            "bac": 0,
            "applicants": [],
            "past_admissions": info["students"],
            "is_closed": True
        })

    DEPT_CACHE[univ] = result
    return result


# 2-1. [신규] 디버깅용 과거 합격생 매칭 점검 진단 API
@app.get("/api/quota/unmatched-diagnosis")
def get_unmatched_diagnosis(univ: str = "이화여자대학교"):
    """특정 대학의 recruit_quota 학과와 매칭되지 않는 peer_data 과거 합격생 목록 진단"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1) 해당 대학 최신 recruit_quota 학과 목록
    cursor.execute("""
        SELECT major 
        FROM recruit_quota 
        WHERE univ = %s AND year = (SELECT COALESCE(MAX(year), 2026) FROM recruit_quota WHERE univ = %s);
    """, (univ, univ))
    quota_majors = [r[0] if isinstance(r, tuple) else r["major"] for r in cursor.fetchall()]

    # 2) 해당 대학 과거 합격생 (peer_data)
    cursor.execute("""
        SELECT year, student_name, department, major, total_score, math_total
        FROM peer_data
        WHERE univ = %s 
          AND year < 2026
          AND major IS NOT NULL AND major != '' AND major != '-' AND major != '미기재'
        ORDER BY year DESC, student_name ASC;
    """, (univ,))
    past_rows = cursor.fetchall()
    cursor.close()
    conn.close()

    unmatched_students = []
    matched_count = 0

    for p in past_rows:
        p_yr = p[0] if isinstance(p, tuple) else p["year"]
        p_name = p[1] if isinstance(p, tuple) else p["student_name"]
        p_dept = p[2] if isinstance(p, tuple) else p["department"]
        p_major = p[3] if isinstance(p, tuple) else p["major"]

        matched = any(is_major_matched(qm, p_major) for qm in quota_majors)
        if matched:
            matched_count += 1
        else:
            unmatched_students.append({
                "year": p_yr,
                "student_name": p_name,
                "department": p_dept,
                "major": p_major
            })

    return {
        "univ": univ,
        "quota_majors_count": len(quota_majors),
        "total_past_records": len(past_rows),
        "matched_count": matched_count,
        "unmatched_count": len(unmatched_students),
        "match_rate_percent": round(matched_count / len(past_rows) * 100, 1) if past_rows else 0.0,
        "unmatched_students": unmatched_students
    }


# 모집요강 엑셀 일괄 업로드 API
@app.post("/api/quota/upload")
async def upload_quota_excel(file: UploadFile = File(...)):
    filename = file.filename.lower()
    if not filename.endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="엑셀(.xlsx, .xls) 또는 CSV 파일만 업로드 가능합니다.")

    contents = await file.read()
    try:
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(contents), encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(contents), encoding="cp949")
        else:
            # 엑셀 파일인 경우 'DB업로드용' 시트 우선 로드
            excel_file = pd.ExcelFile(io.BytesIO(contents))
            target_sheet = 0
            for s in excel_file.sheet_names:
                if "DB업로드용" in s:
                    target_sheet = s
                    break
            df = pd.read_excel(excel_file, sheet_name=target_sheet)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 읽기 실패: {str(e)}")

    df.columns = [str(c).strip().replace("\ufeff", "") for c in df.columns]

    col_map = {
        "연도": "year", "학년도": "year", "입학년도": "year", "년도": "year",
        "대학": "univ", "학교": "univ", "대학명": "univ",
        "계열": "department",
        "학과": "major", "학과명": "major", "모집단위": "major",
        "일반": "general_quota", "일반정원": "general_quota", "일반편입": "general_quota",
        "학사": "bachelor_quota", "학사정원": "bachelor_quota", "학사편입": "bachelor_quota"
    }
    df.rename(columns=col_map, inplace=True)

    required_cols = {"univ", "department", "major"}
    if not required_cols.issubset(set(df.columns)):
        raise HTTPException(
            status_code=400,
            detail=f"필수 컬럼 누락 (현재 컬럼: {list(df.columns)} / 필수: 대학, 계열, 학과명)"
        )

    # 기본 연도 추출 (파일명에 2027 등이 있거나 컬럼에 있는 경우 대응, 기본 2026)
    default_year = 2026
    year_in_filename = re.search(r'202[0-9]|2[0-9]{3}', filename)
    if year_in_filename:
        try:
            default_year = int(year_in_filename.group())
        except (ValueError, TypeError):
            default_year = 2026

    df["general_quota"] = pd.to_numeric(df.get("general_quota", 0), errors="coerce").fillna(0).astype(int)
    df["bachelor_quota"] = pd.to_numeric(df.get("bachelor_quota", 0), errors="coerce").fillna(0).astype(int)
    df = df.dropna(subset=["univ", "department", "major"])

    rows_to_insert = []
    target_univs_by_year = {}

    for _, row in df.iterrows():
        univ_val = str(row["univ"]).strip()
        dept_val = str(row["department"]).strip()
        major_val = str(row["major"]).strip()
        if not univ_val or not major_val or univ_val == "nan" or major_val == "nan":
            continue

        row_year = default_year
        if "year" in row and pd.notna(row["year"]):
            try:
                y_val = int(float(str(row["year"]).replace("년", "").replace("학년도", "").strip()))
                if 2020 <= y_val <= 2040:
                    row_year = y_val
            except (ValueError, TypeError):
                row_year = default_year

        # 0명 / 0명인 학과도 필터링 없이 그대로 저장
        rows_to_insert.append((
            row_year,
            univ_val,
            dept_val,
            major_val,
            int(row["general_quota"]),
            int(row["bachelor_quota"])
        ))

        target_univs_by_year.setdefault(row_year, set()).add(univ_val)

    if not rows_to_insert:
        raise HTTPException(status_code=400, detail="유효한 데이터가 없습니다.")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE recruit_quota MODIFY COLUMN major VARCHAR(150) NOT NULL;")

        # 업로드 대상 대학의 기존 모집요강 데이터 깔끔하게 삭제 후 교체 (Clean Overwrite)
        for y, univs in target_univs_by_year.items():
            for u in univs:
                cursor.execute("DELETE FROM recruit_quota WHERE year = %s AND univ = %s;", (y, u))

        insert_query = """
            INSERT INTO recruit_quota (year, univ, department, major, general_quota, bachelor_quota)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.executemany(insert_query, rows_to_insert)
        conn.commit()
        cursor.close()

        # 메모리 캐시 즉각 완전 초기화
        DEPT_CACHE.clear()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB 적재 오류: {str(e)}")
    finally:
        conn.close()

    total_univs = sum(len(u_set) for u_set in target_univs_by_year.values())
    return {
        "status": "success",
        "message": f"총 {total_univs}개 대학 {len(rows_to_insert)}개 학과 모집요강 데이터가 성공적으로 교체 반영되었습니다. (0명 미선발 학과 포함)"
    }


# 3. 특정 학생의 지원 희망 리스트 조회
@app.get("/api/applications")
def get_student_applications(student_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT a.id,
                          a.univ,
                          a.major,
                          a.memo,
                          q.id                          AS quota_id,
                          COALESCE(q.general_quota, 0)  AS gen_quota,
                          COALESCE(q.bachelor_quota, 0) AS bac_quota,
                          (SELECT COUNT(*) FROM recruit_quota rq WHERE rq.year = 2026 AND rq.univ = a.univ) AS univ_quota_count
                   FROM student_applications a
                            LEFT JOIN recruit_quota q
                                      ON a.year = q.year AND a.univ = q.univ AND a.major = q.major
                   WHERE a.year = 2026
                     AND a.student_name = %s
                   ORDER BY a.created_at ASC;
                   """, (student_name,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    cards = []
    for r in rows:
        q_id = r[4] if isinstance(r, tuple) else r["quota_id"]
        g_quota = r[5] if isinstance(r, tuple) else r["gen_quota"]
        b_quota = r[6] if isinstance(r, tuple) else r["bac_quota"]
        u_count = r[7] if isinstance(r, tuple) else r["univ_quota_count"]

        is_released = bool(u_count and u_count > 0)
        has_quota = bool((g_quota and g_quota > 0) or (b_quota and b_quota > 0))
        # 대학의 2026 모집요강이 등록되어 있으나 해당 학과가 미선발(정원 0명 또는 미개설)인 경우
        is_closed = bool(is_released and (not q_id or not has_quota))

        cards.append({
            "id": r[0] if isinstance(r, tuple) else r["id"],
            "univ": r[1] if isinstance(r, tuple) else r["univ"],
            "major": r[2] if isinstance(r, tuple) else r["major"],
            "memo": r[3] if isinstance(r, tuple) else r["memo"],
            "gen_quota": g_quota,
            "bac_quota": b_quota,
            "is_quota_released": is_released,
            "has_quota": has_quota,
            "is_closed": is_closed
        })
    return cards


# 4. 지원 원서 카드 추가
@app.post("/api/applications")
def add_application(app_data: ApplicationCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
            INSERT INTO student_applications (year, student_name, univ, major, memo)
            VALUES (2026, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                major = VALUES(major),
                memo = VALUES(memo)
            """
    cursor.execute(query, (
        app_data.student_name,
        app_data.univ,
        app_data.major,
        app_data.memo
    ))
    conn.commit()
    cursor.close()
    conn.close()
    DEPT_CACHE.pop(app_data.univ, None)
    return {"status": "success", "message": f"{app_data.student_name}의 {app_data.univ} {app_data.major} 지원 등록 완료"}


# 5. 지원 원서 카드 삭제
@app.delete("/api/applications/{app_id}")
def delete_application(app_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM student_applications WHERE id = %s;", (app_id,))
    conn.commit()
    cursor.close()
    conn.close()
    DEPT_CACHE.clear()
    return {"status": "success", "message": "삭제 완료"}


# 6. 대학별 학점은행제 지원자격 조회 및 저장 API
class EligibilityUpdate(BaseModel):
    univ: str
    eligibility_text: str


@app.get("/api/quota/eligibility")
def get_univ_eligibility(univ: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT eligibility_text FROM univ_eligibility WHERE univ = %s;", (univ,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    text = ""
    if row:
        if isinstance(row, tuple):
            text = row[0] or ""
        elif isinstance(row, dict):
            text = row.get("eligibility_text") or ""
    return {"univ": univ, "eligibility_text": text}


@app.post("/api/quota/eligibility")
def save_univ_eligibility(data: EligibilityUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO univ_eligibility (univ, eligibility_text)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE eligibility_text = VALUES(eligibility_text);
        """, (data.univ, data.eligibility_text))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return {"status": "success", "univ": data.univ, "eligibility_text": data.eligibility_text}


# 7. 학생별 비고(상담 및 특이사항 메모) 및 희망학과/스펙 조회 및 저장 API
class StudentNoteUpdate(BaseModel):
    student_name: str
    memo: Optional[str] = ""
    pref_major_1: Optional[str] = ""
    pref_major_2: Optional[str] = ""
    dislike_major: Optional[str] = ""
    toeic_score: Optional[str] = ""
    gpa_score: Optional[str] = ""


@app.get("/api/student-notes")
def get_student_note(student_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT memo, updated_at, pref_major_1, pref_major_2, dislike_major, toeic_score, gpa_score 
        FROM student_notes 
        WHERE student_name = %s;
    """, (student_name,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    memo = ""
    updated_at = None
    pref_major_1 = ""
    pref_major_2 = ""
    dislike_major = ""
    toeic_score = ""
    gpa_score = ""

    if row:
        if isinstance(row, tuple):
            memo = row[0] or ""
            updated_at = row[1]
            pref_major_1 = row[2] or "" if len(row) > 2 else ""
            pref_major_2 = row[3] or "" if len(row) > 3 else ""
            dislike_major = row[4] or "" if len(row) > 4 else ""
            toeic_score = row[5] or "" if len(row) > 5 else ""
            gpa_score = row[6] or "" if len(row) > 6 else ""
        elif isinstance(row, dict):
            memo = row.get("memo") or ""
            updated_at = row.get("updated_at")
            pref_major_1 = row.get("pref_major_1") or ""
            pref_major_2 = row.get("pref_major_2") or ""
            dislike_major = row.get("dislike_major") or ""
            toeic_score = row.get("toeic_score") or ""
            gpa_score = row.get("gpa_score") or ""

    return {
        "student_name": student_name,
        "memo": memo or "",
        "updated_at": str(updated_at) if updated_at else None,
        "pref_major_1": pref_major_1 or "",
        "pref_major_2": pref_major_2 or "",
        "dislike_major": dislike_major or "",
        "toeic_score": toeic_score or "",
        "gpa_score": gpa_score or ""
    }


@app.post("/api/student-notes")
def save_student_note(data: StudentNoteUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO student_notes (student_name, memo, pref_major_1, pref_major_2, dislike_major, toeic_score, gpa_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            memo = VALUES(memo),
            pref_major_1 = VALUES(pref_major_1),
            pref_major_2 = VALUES(pref_major_2),
            dislike_major = VALUES(dislike_major),
            toeic_score = VALUES(toeic_score),
            gpa_score = VALUES(gpa_score)
    """, (
        data.student_name,
        data.memo or "",
        data.pref_major_1 or "",
        data.pref_major_2 or "",
        data.dislike_major or "",
        data.toeic_score or "",
        data.gpa_score or ""
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": f"{data.student_name} 학생 정보 및 비고 메모 저장 완료"}


class PastExamScoreCreate(BaseModel):
    student_name: str
    univ: str
    exam_year: int
    subject_type: Optional[str] = "영어"  # '영어' | '수학' | '영+수'
    my_score: float
    avg_score: Optional[float] = None
    eng_score: Optional[float] = None
    math_score: Optional[float] = None
    percentile: Optional[str] = ""
    memo: Optional[str] = ""


class PastExamScoreBatchItem(BaseModel):
    univ: str
    exam_year: int
    subject_type: str  # '영어' | '수학' | '영+수'
    my_score: Optional[float] = None
    avg_score: Optional[float] = None
    eng_score: Optional[float] = None
    math_score: Optional[float] = None
    percentile: Optional[str] = ""
    memo: Optional[str] = ""
    delete: Optional[bool] = False


class PastExamScoreBatchSave(BaseModel):
    student_name: str
    items: List[PastExamScoreBatchItem]


@app.get("/api/student-past-exams")
def get_student_past_exams(student_name: str, univ: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    if univ:
        univ_clean = univ.replace("대학교", "").replace("대학", "").split("(")[0].strip()
        cursor.execute("""
            SELECT id, student_name, univ, exam_year, subject_type, my_score, avg_score, score_gap, eng_score, math_score, percentile, memo, updated_at
            FROM student_past_exam_scores
            WHERE student_name = %s 
              AND (univ = %s OR univ LIKE %s OR %s LIKE CONCAT(univ, '%%'))
            ORDER BY exam_year DESC, subject_type ASC;
        """, (student_name, univ, f"%{univ_clean}%", univ))
    else:
        cursor.execute("""
            SELECT id, student_name, univ, exam_year, subject_type, my_score, avg_score, score_gap, eng_score, math_score, percentile, memo, updated_at
            FROM student_past_exam_scores
            WHERE student_name = %s
            ORDER BY univ ASC, exam_year DESC, subject_type ASC;
        """, (student_name,))
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "student_name": r["student_name"],
            "univ": r["univ"],
            "exam_year": r["exam_year"],
            "year_short": f"{str(r['exam_year'])[-2:]}'",
            "subject_type": r.get("subject_type") or "영어",
            "my_score": float(r["my_score"]) if r["my_score"] is not None else 0.0,
            "avg_score": float(r["avg_score"]) if r["avg_score"] is not None else None,
            "score_gap": float(r["score_gap"]) if r["score_gap"] is not None else None,
            "eng_score": float(r["eng_score"]) if r.get("eng_score") is not None else None,
            "math_score": float(r["math_score"]) if r.get("math_score") is not None else None,
            "percentile": r.get("percentile") or "",
            "memo": r.get("memo") or "",
            "updated_at": str(r["updated_at"]) if r.get("updated_at") else None
        })

    return {"scores": results}


@app.post("/api/student-past-exams")
def save_student_past_exam(data: PastExamScoreCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    subject_type = data.subject_type or "영어"
    my_score = float(data.my_score)
    # 영+수 선택 시 my_score가 0이고 eng_score 또는 math_score가 있으면 합산
    if subject_type == "영+수" and (my_score == 0 or my_score is None) and (data.eng_score or data.math_score):
        my_score = (data.eng_score or 0) + (data.math_score or 0)

    score_gap = None
    if data.avg_score is not None and data.avg_score > 0:
        score_gap = round(my_score - float(data.avg_score), 2)

    cursor.execute("""
        INSERT INTO student_past_exam_scores 
        (student_name, univ, exam_year, subject_type, my_score, avg_score, score_gap, eng_score, math_score, percentile, memo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            my_score = VALUES(my_score),
            avg_score = VALUES(avg_score),
            score_gap = VALUES(score_gap),
            eng_score = VALUES(eng_score),
            math_score = VALUES(math_score),
            percentile = VALUES(percentile),
            memo = VALUES(memo),
            updated_at = CURRENT_TIMESTAMP;
    """, (
        data.student_name,
        data.univ,
        data.exam_year,
        subject_type,
        my_score,
        data.avg_score,
        score_gap,
        data.eng_score,
        data.math_score,
        data.percentile or "",
        data.memo or ""
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": f"{data.student_name} 학생 {data.univ} {data.exam_year}년도 [{subject_type}] 기출 점수 저장 완료"}


@app.delete("/api/student-past-exams/{score_id}")
def delete_student_past_exam(score_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM student_past_exam_scores WHERE id = %s;", (score_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "success", "message": "기출 점수 삭제 완료"}


@app.post("/api/student-past-exams/batch")
def save_student_past_exams_batch(data: PastExamScoreBatchSave):
    conn = get_db_connection()
    cursor = conn.cursor()
    saved_count = 0
    deleted_count = 0

    for item in data.items:
        subj = item.subject_type or "영어"
        if item.delete or item.my_score is None:
            cursor.execute("""
                DELETE FROM student_past_exam_scores
                WHERE student_name = %s AND univ = %s AND exam_year = %s AND subject_type = %s;
            """, (data.student_name, item.univ, item.exam_year, subj))
            if cursor.rowcount > 0:
                deleted_count += 1
        else:
            my_score = float(item.my_score)
            if subj == "영+수" and (my_score == 0 or my_score is None) and (item.eng_score or item.math_score):
                my_score = (item.eng_score or 0) + (item.math_score or 0)
            score_gap = None
            if item.avg_score is not None and item.avg_score > 0:
                score_gap = round(my_score - float(item.avg_score), 2)

            cursor.execute("""
                INSERT INTO student_past_exam_scores 
                (student_name, univ, exam_year, subject_type, my_score, avg_score, score_gap, eng_score, math_score, percentile, memo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    my_score = VALUES(my_score),
                    avg_score = VALUES(avg_score),
                    score_gap = VALUES(score_gap),
                    eng_score = VALUES(eng_score),
                    math_score = VALUES(math_score),
                    percentile = VALUES(percentile),
                    memo = VALUES(memo),
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                data.student_name,
                item.univ,
                item.exam_year,
                subj,
                my_score,
                item.avg_score,
                score_gap,
                item.eng_score,
                item.math_score,
                item.percentile or "",
                item.memo or ""
            ))
            saved_count += 1

    conn.commit()
    cursor.close()
    conn.close()
    return {
        "status": "success",
        "message": f"{data.student_name} 학생 기출 성적 저장 완료 (반영: {saved_count}건, 삭제: {deleted_count}건)",
        "saved_count": saved_count,
        "deleted_count": deleted_count
    }


@app.post("/api/student-past-exams/upload-excel")
async def upload_past_exam_excel(
    file: UploadFile = File(...),
    default_student: Optional[str] = Form(None),
    default_univ: Optional[str] = Form(None)
):
    try:
        content = await file.read()
        filename = file.filename.lower()
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"엑셀 파일 읽기 실패: {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail="업로드한 파일에 데이터가 없습니다.")

    # 컬럼 헤더 정규화
    df.columns = [str(c).strip() for c in df.columns]

    def find_col(candidates):
        for c in df.columns:
            for cand in candidates:
                if cand.lower() == c.lower() or cand in c:
                    return c
        return None

    student_col = find_col(['학생 이름', '학생이름', '학생', '이름', 'student_name'])
    univ_col = find_col(['대학명', '대학', '학교명', '학교', '대학교', 'univ'])
    subj_col = find_col(['구분', '과목', '과목구분', '과목명', 'subject', 'subject_type'])
    memo_col = find_col(['메모', '비고', 'memo'])

    # 🌟 가로형 년도 컬럼 감지 (예: 2020, 2021 ... 2026, 2020년, 20' 등)
    year_cols = []
    for c in df.columns:
        m = re.search(r'(20[12]\d)|\b([12]\d)년|([12]\d)\'', str(c))
        if m:
            if m.group(1):
                yr = int(m.group(1))
            else:
                yr = 2000 + int(m.group(2) or m.group(3))
            if 2018 <= yr <= 2030:
                year_cols.append((c, yr))

    # 1. 가로형(와이드) 년도 컬럼 방식 (2개 이상의 년도 컬럼이 존재하는 경우)
    is_wide_year_format = len(year_cols) >= 2

    inserted_count = 0
    skipped_count = 0
    records = []

    if is_wide_year_format:
        # 가로형 년도 컬럼 처리
        for _, row in df.iterrows():
            s_name = str(row[student_col]).strip() if student_col and pd.notna(row[student_col]) else ""
            if not s_name or s_name in ['nan', 'None']:
                s_name = (default_student or "").strip()
            if not s_name:
                skipped_count += 1
                continue

            u_name = str(row[univ_col]).strip() if univ_col and pd.notna(row[univ_col]) else ""
            if not u_name or u_name in ['nan', 'None']:
                u_name = (default_univ or "").strip()
            if not u_name:
                skipped_count += 1
                continue

            # 과목 구분
            raw_subj = str(row[subj_col]).strip() if subj_col and pd.notna(row[subj_col]) else ""
            if ("영" in raw_subj and "수" in raw_subj) or "영수" in raw_subj:
                subj_type = "영+수"
            elif "수" in raw_subj or "자연" in raw_subj or "math" in raw_subj.lower():
                subj_type = "수학"
            else:
                subj_type = "영어"

            memo = str(row[memo_col]).strip() if memo_col and pd.notna(row[memo_col]) else ""
            if memo in ['nan', 'None']:
                memo = ""

            for col_name, yr_val in year_cols:
                val = row[col_name]
                if pd.isna(val) or val is None or str(val).strip() == "" or str(val).strip() in ['-', 'nan', 'None']:
                    continue
                try:
                    num_str = re.sub(r"[^\d.]", "", str(val))
                    if not num_str:
                        continue
                    score = float(num_str)
                except Exception:
                    continue

                curr_u_name = u_name
                # 명지대학교 년도별 세션 정규화: 2024년 이하는 '명지대학교', 2025년 이상은 '명지대학교(오전)'
                if "명지" in curr_u_name:
                    if yr_val <= 2024:
                        curr_u_name = "명지대학교"
                    elif yr_val >= 2025 and curr_u_name == "명지대학교":
                        curr_u_name = "명지대학교(오전)"

                eng_score = score if subj_type == "영어" else None
                math_score = score if subj_type == "수학" else None
                records.append((s_name, curr_u_name, yr_val, subj_type, score, None, None, eng_score, math_score, memo))

    else:
        # 2. 기존 단일 행(행별 년도) 방식
        year_col = find_col(['기출 년도', '기출년도', '년도', '연도', '기출연도', 'exam_year', 'year'])
        score_col = find_col(['내 총점', '내총점', '총점', '내점수', '내 점수', '점수', 'score', 'my_score'])
        avg_col = find_col(['평균', '평균점수', 'avg', 'avg_score'])
        eng_col = find_col(['영어점수', '영어 점수', '영어', 'eng_score'])
        math_col = find_col(['수학점수', '수학 점수', '수학', 'math_score'])

        for _, row in df.iterrows():
            s_name = str(row[student_col]).strip() if student_col and pd.notna(row[student_col]) else ""
            if not s_name or s_name in ['nan', 'None']:
                s_name = (default_student or "").strip()
            if not s_name:
                skipped_count += 1
                continue

            u_name = str(row[univ_col]).strip() if univ_col and pd.notna(row[univ_col]) else ""
            y_val = row[year_col] if year_col and pd.notna(row[year_col]) else None

            if u_name:
                m_year_univ = re.match(r"^(\d{2,4})\s*(.+)$", u_name)
                if m_year_univ:
                    if not y_val or pd.isna(y_val):
                        y_val = m_year_univ.group(1)
                    u_name = m_year_univ.group(2).strip()

            if not u_name or u_name in ['nan', 'None']:
                u_name = (default_univ or "").strip()
            if not u_name:
                skipped_count += 1
                continue

            exam_year = None
            if y_val is not None and not pd.isna(y_val):
                try:
                    y_num = int(float(re.sub(r"[^\d.]", "", str(y_val))))
                    if y_num < 100:
                        exam_year = 2000 + y_num
                    else:
                        exam_year = y_num
                except Exception:
                    pass
            if not exam_year:
                skipped_count += 1
                continue

            curr_u_name = u_name
            if "명지" in curr_u_name:
                if exam_year <= 2024:
                    curr_u_name = "명지대학교"
                elif exam_year >= 2025 and curr_u_name == "명지대학교":
                    curr_u_name = "명지대학교(오전)"

            raw_subj = str(row[subj_col]).strip() if subj_col and pd.notna(row[subj_col]) else ""
            if ("영" in raw_subj and "수" in raw_subj) or "영수" in raw_subj:
                subj_type = "영+수"
            elif "수" in raw_subj or "자연" in raw_subj or "math" in raw_subj.lower():
                subj_type = "수학"
            else:
                subj_type = "영어"

            eng_score = None
            math_score = None
            if eng_col and pd.notna(row[eng_col]):
                try: eng_score = float(re.sub(r"[^\d.]", "", str(row[eng_col])))
                except Exception: pass
            if math_col and pd.notna(row[math_col]):
                try: math_score = float(re.sub(r"[^\d.]", "", str(row[math_col])))
                except Exception: pass

            my_score = None
            if score_col and pd.notna(row[score_col]):
                try: my_score = float(re.sub(r"[^\d.]", "", str(row[score_col])))
                except Exception: pass
            
            if my_score is None:
                if eng_score is not None and math_score is not None:
                    my_score = eng_score + math_score
                elif eng_score is not None:
                    my_score = eng_score
                elif math_score is not None:
                    my_score = math_score
            
            if my_score is None:
                skipped_count += 1
                continue

            avg_score = None
            if avg_col and pd.notna(row[avg_col]):
                try: avg_score = float(re.sub(r"[^\d.]", "", str(row[avg_col])))
                except Exception: pass
            
            score_gap = None
            if avg_score is not None and avg_score > 0:
                score_gap = round(my_score - avg_score, 2)

            memo = str(row[memo_col]).strip() if memo_col and pd.notna(row[memo_col]) else ""
            if memo in ['nan', 'None']: memo = ""

            records.append((s_name, curr_u_name, exam_year, subj_type, my_score, avg_score, score_gap, eng_score, math_score, memo))

    if not records:
        raise HTTPException(status_code=400, detail="유효한 기출 성적 행을 찾을 수 없습니다. (학생이름, 기출년도/년도컬럼, 점수 확인 필요)")

    conn = get_db_connection()
    cursor = conn.cursor()
    for r in records:
        cursor.execute("""
            INSERT INTO student_past_exam_scores
            (student_name, univ, exam_year, subject_type, my_score, avg_score, score_gap, eng_score, math_score, memo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                my_score = VALUES(my_score),
                avg_score = VALUES(avg_score),
                score_gap = VALUES(score_gap),
                eng_score = VALUES(eng_score),
                math_score = VALUES(math_score),
                memo = VALUES(memo),
                updated_at = CURRENT_TIMESTAMP;
        """, r)
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "status": "success",
        "message": f"총 {len(records)}건의 기출 성적이 성공적으로 저장되었습니다." + (f" (제외/누락: {skipped_count}건)" if skipped_count > 0 else "")
    }


@app.get("/api/student-past-exams/sample-template")
def download_past_exam_template():
    # 전체 학교 및 세션 목록
    template_universities = [
        # 서성한
        "서강대학교", "성균관대학교", "한양대학교",
        # 중경외시
        "중앙대학교", "경희대학교", "한국외국어대학교(T1 A형)", "한국외국어대학교(T2 B형)", "서울시립대학교",
        # 건동홍
        "건국대학교", "동국대학교", "홍익대학교",
        # 국숭세단
        "국민대학교", "숭실대학교", "세종대학교", "단국대학교(오전)", "단국대학교(오후)",
        # 광명가
        "광운대학교", "명지대학교", "명지대학교(오전)", "명지대학교(오후)", "가톨릭대학교", "상명대학교",
        # 인가경
        "인하대학교", "인천대학교", "가천대학교(A형)", "가천대학교(B형)", "경기대학교", "아주대학교",
        # 여대라인
        "이화여자대학교", "숙명여자대학교(A형)", "숙명여자대학교(B형)", "동덕여자대학교",
        "덕성여자대학교(1교시)", "덕성여자대학교(2교시)", "덕성여자대학교(3교시)",
        "서울여자대학교(오전)", "서울여자대학교(오후)",
        # 한성/항공
        "한성대학교", "한국항공대학교"
    ]

    sample_rows = []
    # 예시 학생명 (홍길동 예시 1행 + 빈 입력용 행들)
    for idx, univ in enumerate(template_universities):
        sample_rows.append({
            "학생 이름": "홍길동" if idx == 0 else "",
            "대학명": univ,
            "과목 구분(영어/수학/영+수)": "영어",
            "2020년": 75.0 if idx == 0 else None,
            "2021년": 68.0 if idx == 0 else None,
            "2022년": 82.5 if idx == 0 else None,
            "2023년": None,
            "2024년": None,
            "2025년": None,
            "2026년": None,
            "비고": "인문 영어 기출" if idx == 0 else ""
        })

    df = pd.DataFrame(sample_rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='기출성적입력')
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=past_exam_all_years_template.xlsx"}
    )


# 8. 지원 현황: 실제 응시한 월들의 성적 기반 지난 합격생 진학 대학 매칭 API
PAST_ADMISSIONS_CACHE = None

def get_cached_past_admissions():
    global PAST_ADMISSIONS_CACHE
    if PAST_ADMISSIONS_CACHE is not None:
        return PAST_ADMISSIONS_CACHE

    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT year, student_name, month, total_score, math_total, department, univ, major
            FROM peer_data
            WHERE year < 2026 
              AND univ != '' AND univ IS NOT NULL AND univ NOT IN ('학교모름', '미기재', '기타')
              AND major != '' AND major IS NOT NULL AND major NOT IN ('None', 'nan', '미기재')
            ORDER BY year DESC, student_name ASC, month ASC
        """)
        rows = cursor.fetchall()

        # 학생별 구조화
        from collections import defaultdict
        students_map = defaultdict(lambda: {
            'univ': '',
            'major': '',
            'is_natural': False,
            'apply_type': '일반',
            'scores': {}
        })

        for r in rows:
            key = (r['year'], r['student_name'])
            stu = students_map[key]
            stu['univ'] = r['univ']
            stu['major'] = r['major']

            dept = str(r.get('department') or '')
            if '자연' in dept:
                stu['is_natural'] = True
            if '학사' in dept:
                stu['apply_type'] = '학사'
            elif '일반' in dept and stu['apply_type'] != '학사':
                stu['apply_type'] = '일반'

            m = r.get('month')
            if not m:
                continue

            raw_e = r.get('total_score')
            e_val = None
            if raw_e is not None and str(raw_e).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    num = float(raw_e)
                    if num > 0:
                        e_val = num
                except ValueError:
                    pass

            raw_m = r.get('math_total')
            m_val = None
            if raw_m is not None and str(raw_m).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    num = float(raw_m)
                    if num > 0:
                        m_val = num
                        stu['is_natural'] = True
                except ValueError:
                    pass

            if e_val is not None or m_val is not None:
                stu['scores'][int(m)] = {'eng': e_val, 'math': m_val}

        PAST_ADMISSIONS_CACHE = students_map
        return students_map
    finally:
        conn.close()


@app.get("/api/similar-senior-destinations")
def get_similar_senior_destinations(student_name: str):
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 1. 대상 2026 학생의 월별 성적 및 계열 판정
        cursor.execute("""
            SELECT month, total_score, math_total, department
            FROM peer_data
            WHERE year = 2026 AND student_name = %s
            ORDER BY month ASC
        """, (student_name,))
        rows = cursor.fetchall()

        target_month_scores = {}
        has_math = False
        is_dept_natural = False

        for r in rows:
            m = r.get("month")
            dept = str(r.get("department") or "")
            if "자연" in dept:
                is_dept_natural = True

            raw_e = r.get("total_score")
            e_val = None
            if raw_e is not None and str(raw_e).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    num = float(raw_e)
                    if num > 0:
                        e_val = num
                except ValueError:
                    pass

            raw_m = r.get("math_total")
            m_val = None
            if raw_m is not None and str(raw_m).strip() not in ['', 'None', 'nan', 'null', '-']:
                try:
                    num = float(raw_m)
                    if num > 0:
                        m_val = num
                        has_math = True
                except ValueError:
                    pass

            if m and (e_val is not None or m_val is not None):
                target_month_scores[int(m)] = {"eng": e_val, "math": m_val}

        is_natural = is_dept_natural or has_math
        target_months = set(target_month_scores.keys())

        if not target_months:
            return {
                "status": "empty",
                "message": f"{student_name} 학생의 모의고사 성적 데이터가 없습니다.",
                "similar_seniors": []
            }

        # 대상 학생 평균 점수 집계
        t_eng_list = [v["eng"] for v in target_month_scores.values() if v["eng"] is not None]
        t_math_list = [v["math"] for v in target_month_scores.values() if v["math"] is not None]
        avg_target_eng = round(sum(t_eng_list) / len(t_eng_list), 1) if t_eng_list else None
        avg_target_math = round(sum(t_math_list) / len(t_math_list), 1) if t_math_list else None

        # 2. 과거 합격생 캐시 로드 & 계열 100% 일치 필터링
        past_students = get_cached_past_admissions()
        matched = []

        for (year, name), info in past_students.items():
            # 학생이 자연계열이면 자연계열 지난 합격생만, 인문계열이면 인문계열 지난 합격생만!
            if info["is_natural"] != is_natural:
                continue

            p_scores = info["scores"]
            p_months = set(p_scores.keys())
            if not p_months:
                continue

            overlap_months = target_months.intersection(p_months)
            if not overlap_months:
                continue

            # 응시한 월별 1:1 점수 차이 계산
            sum_diff = 0.0
            for m in overlap_months:
                t_score = target_month_scores[m]
                p_score = p_scores[m]

                # 영어 점수 차이
                if t_score["eng"] is not None and p_score["eng"] is not None:
                    sum_diff += abs(t_score["eng"] - p_score["eng"]) * 1.0
                elif t_score["eng"] is not None or p_score["eng"] is not None:
                    sum_diff += 15.0

                # 수학 점수 차이 (자연계열인 경우)
                if is_natural:
                    if t_score["math"] is not None and p_score["math"] is not None:
                        sum_diff += abs(t_score["math"] - p_score["math"]) * 1.0
                    elif t_score["math"] is not None or p_score["math"] is not None:
                        sum_diff += 20.0

            # 결시 월 페널티 완화 (2020~2023년도는 연간 모의고사 시행 횟수가 적어 과도한 페널티로 배제되던 현상 방지)
            missing_months = len(target_months - overlap_months)
            cnt_diff = abs(len(p_months) - len(target_months))

            avg_overlap_diff = sum_diff / len(overlap_months)
            total_dist = avg_overlap_diff + (missing_months * 1.5) + (cnt_diff * 0.4)

            # 해당 과거 합격생의 전체 평균 점수
            p_eng_list = [v["eng"] for v in p_scores.values() if v["eng"] is not None]
            p_math_list = [v["math"] for v in p_scores.values() if v["math"] is not None]
            avg_p_eng = round(sum(p_eng_list) / len(p_eng_list), 1) if p_eng_list else None
            avg_p_math = round(sum(p_math_list) / len(p_math_list), 1) if p_math_list else None

            matched.append({
                "student_name": name,
                "senior_name": name,  # 호환성 유지
                "year": year,
                "apply_type": info.get("apply_type", "일반"),
                "univ": info["univ"],
                "major": info["major"],
                "test_count": len(p_months),
                "overlap_count": len(overlap_months),
                "avg_eng": avg_p_eng,
                "avg_math": avg_p_math,
                "distance": round(total_dist, 2)
            })

        matched.sort(key=lambda x: x["distance"])

        # 🌟 특정 연도(24~25년도) 쏠림 방지: 연도별 라운드로빈 균등 배분 (2020~2025 전 연도 골고루 반영)
        from collections import defaultdict
        by_year = defaultdict(list)
        for item in matched:
            by_year[item["year"]].append(item)

        unique_destinations = []
        seen = set()

        # 라운드로빈 방식으로 2025부터 2020까지 연도별 최유사 합격생 순차 선발
        available_years = sorted(by_year.keys(), reverse=True)
        for _ in range(3):
            for y in available_years:
                for cand in by_year[y]:
                    key = f"{cand['univ']}_{cand['major']}"
                    if key not in seen:
                        seen.add(key)
                        unique_destinations.append(cand)
                        break
                if len(unique_destinations) >= 10:
                    break
            if len(unique_destinations) >= 10:
                break

        # 혹시 10개가 안 채워졌을 경우 전체 거리 순으로 보충
        if len(unique_destinations) < 10:
            for item in matched:
                key = f"{item['univ']}_{item['major']}"
                if key not in seen:
                    seen.add(key)
                    unique_destinations.append(item)
                if len(unique_destinations) >= 10:
                    break

        # 최종 가독성을 위해 유사도(distance) 순으로 정렬
        unique_destinations.sort(key=lambda x: x["distance"])

        return {
            "status": "success",
            "student_name": student_name,
            "target": {
                "test_count": len(target_months),
                "tested_months": sorted(list(target_months)),
                "avg_eng": avg_target_eng,
                "avg_math": avg_target_math,
                "is_natural": is_natural
            },
            "similar_seniors": unique_destinations
        }
    except Exception as e:
        print("similar_senior_destinations 에러:", e)
        return {"status": "error", "message": str(e), "similar_seniors": []}
    finally:
        conn.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
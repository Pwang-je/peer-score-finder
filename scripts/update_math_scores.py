import warnings
import pandas as pd
import pymysql

warnings.filterwarnings("ignore", category=UserWarning)

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'database': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

FILE_PATH = r"C:\Users\esang\Documents\work\devel\peer-score-finder\data\raw\math\26_수학점수.xlsx"

def main():
    df = pd.read_csv(FILE_PATH) if FILE_PATH.endswith(".csv") else pd.read_excel(FILE_PATH)
    df.columns = df.columns.str.strip()

    # 1) 2026년 데이터만 필터링
    df = df[df['year'] == 2026].copy()

    # 2) '분원' 또는 'center' 컬럼이 있으면 '듀이카'만 1차 필터링
    center_cols = [c for c in df.columns if c.lower() in ['분원', 'center']]
    if center_cols:
        c_col = center_cols[0]
        df = df[df[c_col].astype(str).str.strip() == '듀이카'].copy()
        print(f"✅ '{c_col}' 컬럼에서 듀이카 학생만 1차 필터링 완료 ({len(df)}건)")
    else:
        print("ℹ️ 엑셀에 '분원' 컬럼이 없어 DB의 2026년 듀이카 명단과 대조합니다.")

    # 유효한 수학 점수만 남기기
    df['student_name'] = df['student_name'].astype(str).str.strip()
    df['month'] = pd.to_numeric(df['month'], errors='coerce')
    df['math_num'] = pd.to_numeric(df['math_total'], errors='coerce')
    df = df.dropna(subset=['month', 'math_num']).copy()
    df['month'] = df['month'].astype(int)

    # 3) DB에 올라가 있는 2026년 듀이카 학생 목록 조회
    conn = pymysql.connect(**DB_CONFIG)
    df_db = pd.read_sql("SELECT DISTINCT month, student_name FROM peer_data WHERE year = 2026", conn)
    db_students = set(df_db['student_name'].str.strip())
    db_exact_keys = set(zip(df_db['month'], df_db['student_name'].str.strip()))

    # DB에 등록된 듀이카 학생 이름과 일치하는 행만 추출
    df_target = df[df['student_name'].isin(db_students)].copy()

    # 4) 같은 월에 동명이인이 2명 이상 겹치는 경우 분리 (타 분원 동명이인 섞임 방지)
    dup_mask = df_target.duplicated(subset=['month', 'student_name'], keep=False)
    df_safe = df_target[~dup_mask]
    df_collision = df_target[dup_mask]

    updates = []
    no_eng_month = []

    for _, row in df_safe.iterrows():
        m = int(row['month'])
        name = row['student_name']
        score = float(row['math_num'])
        if (m, name) in db_exact_keys:
            updates.append((score, 2026, m, name))
        else:
            no_eng_month.append((m, name, score))

    # 5) 안전한 1:1 매칭 건만 DB 일괄 업데이트
    cursor = conn.cursor()
    sql = "UPDATE peer_data SET math_total = %s WHERE year = %s AND month = %s AND student_name = %s"
    if updates:
        cursor.executemany(sql, updates)
    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n🎉 안전한 수학 점수 반영 완료: 총 {len(updates)}건")

    if not df_collision.empty:
        print(f"\n⚠️ 같은 월에 동명이인이 2명 이상 있어 보류된 건 ({len(df_collision)}건) -> 점수 확인 후 수동 선택 필요:")
        print(df_collision[['month', 'student_name', 'math_num']].sort_values(['month', 'student_name']).to_string(index=False))

    if no_eng_month:
        print(f"\nℹ️ 해당 월 영어 성적 행이 없어 미반영된 건 ({len(no_eng_month)}건):")
        for m, name, sc in no_eng_month:
            print(f"   - 2026년 {m}월 | {name} (수학: {sc})")

if __name__ == "__main__":
    main()
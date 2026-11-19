# 원서지원현황의 조회대학에 안나오는 학생 확인

import re
import pandas as pd
import pymysql

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'db': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

def clean_major_name(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r'[*()\[\]·•ㆍ/,\s]', '', str(s))
    return s.strip()

def is_major_matched(target_clean: str, past_clean: str) -> bool:
    if not target_clean or not past_clean:
        return False
    if target_clean == past_clean:
        return True
    t_core = re.sub(r'(학과|학부|전공|과)$', '', target_clean)
    p_core = re.sub(r'(학과|학부|전공|과)$', '', past_clean)
    return bool(t_core and t_core == p_core)

def check_hidden_past_admissions():
    conn = pymysql.connect(**DB_CONFIG)
    df_quota = pd.read_sql("SELECT DISTINCT univ, major FROM recruit_quota WHERE year = 2026", conn)
    df_past = pd.read_sql("""
        SELECT DISTINCT year, student_name, univ, major, department
        FROM peer_data
        WHERE year < 2026
          AND univ IS NOT NULL AND univ != ''
          AND major IS NOT NULL AND major NOT IN ('', '-', '미기재')
    """, conn)
    conn.close()

    quota_univs = set(df_quota['univ'].str.strip())
    quota_majors_by_univ = {}
    for univ, grp in df_quota.groupby('univ'):
        quota_majors_by_univ[univ.strip()] = [clean_major_name(m) for m in grp['major']]

    hidden_list = []
    for _, row in df_past.iterrows():
        u = str(row['univ']).strip()
        m = str(row['major']).strip()
        m_clean = clean_major_name(m)

        if u not in quota_univs:
            hidden_list.append((row['year'], row['student_name'], u, m, "대학명 불일치 (recruit_quota에 해당 대학명 없음)"))
            continue

        target_majors = quota_majors_by_univ.get(u, [])
        matched = any(is_major_matched(tm, m_clean) for tm in target_majors)
        if not matched:
            hidden_list.append((row['year'], row['student_name'], u, m, "학과명 불일치 (해당 대학 모집요강 학과명과 다름)"))

    print(f"=== 웹 화면에 표시되지 않는 지난 합격생 총 {len(hidden_list)}명 ===")
    for y, name, u, m, reason in sorted(hidden_list, key=lambda x: (x[2], x[0])):
        print(f"  - [{u}] {y}년 {name} | DB학과: '{m}' -> 원인: {reason}")

if __name__ == "__main__":
    check_hidden_past_admissions()
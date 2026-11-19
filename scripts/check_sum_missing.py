import warnings
from pathlib import Path
import pandas as pd
import pymysql

warnings.filterwarnings("ignore", category=UserWarning)

BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "data" / "processed" / "전체_영어_성적_정제완료.xlsx"  #[cite: 2, 9]

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'database': 'peer_data',  #[cite: 9]
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

INVALID_VALS = {'', '-', '미기재', 'nan', 'NaN', 'None', 'null', 'NULL'}

def clean_str(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s in INVALID_VALS else s

def main():
    df_ex = pd.read_excel(EXCEL_PATH)  #[cite: 2]
    df_ex.columns = df_ex.columns.str.strip()
    df_ex = df_ex[df_ex['year'].between(2019, 2024)].copy()

    df_ex['univ_clean'] = df_ex['univ'].apply(clean_str)
    df_ex['major_clean'] = df_ex['major'].apply(clean_str)
    df_ex_pass = df_ex[df_ex['univ_clean'] != ""].drop_duplicates(subset=['year', 'student_name'], keep='last')  #[cite: 9]

    conn = pymysql.connect(**DB_CONFIG)
    df_db = pd.read_sql(
        "SELECT year, student_name, univ, major FROM peer_data WHERE year BETWEEN 2019 AND 2024",
        conn
    )
    conn.close()

    df_db['univ_clean'] = df_db['univ'].apply(clean_str)
    df_db['major_clean'] = df_db['major'].apply(clean_str)

    # DB 학생별 대표 (univ, major) 추출
    db_map = {}
    for (y, name), grp in df_db.groupby(['year', 'student_name']):
        valid_rows = grp[grp['univ_clean'] != ""]
        if not valid_rows.empty:
            db_map[(int(y), str(name).strip())] = (
                valid_rows['univ_clean'].iloc[-1],
                valid_rows['major_clean'].iloc[-1]
            )
        else:
            db_map[(int(y), str(name).strip())] = ("", "")

    exact_ok = 0
    diff_list = []
    missing_list = []

    for _, row in df_ex_pass.iterrows():
        y = int(row['year'])
        name = str(row['student_name']).strip()
        ex_u, ex_m = row['univ_clean'], row['major_clean']

        if (y, name) not in db_map:
            missing_list.append((y, name, ex_u, ex_m, "DB에 학생 행 없음"))
            continue

        db_u, db_m = db_map[(y, name)]
        if db_u == "":
            missing_list.append((y, name, ex_u, ex_m, "DB에 대학명 비어있음"))
        elif (ex_u, ex_m) != (db_u, db_m):
            diff_list.append((y, name, f"{ex_u} {ex_m}", f"{db_u} {db_m}"))
        else:
            exact_ok += 1

    print(f"✅ 엑셀과 DB가 100% 일치하는 합격생: {exact_ok}명")
    print(f"❌ 누락된 합격생: {len(missing_list)}명")
    for item in missing_list[:20]:
        print(f"   - {item[0]}년 | {item[1]} ({item[2]} {item[3]}) -> {item[4]}")

    print(f"⚠️ 대학 또는 학과명이 엑셀과 다르게 들어간 학생: {len(diff_list)}명")
    for item in diff_list[:20]:
        print(f"   - {item[0]}년 | {item[1]} | 엑셀: [{item[2]}] vs DB: [{item[3]}]")

if __name__ == "__main__":
    main()
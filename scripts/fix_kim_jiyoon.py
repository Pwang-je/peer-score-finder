import pymysql
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_CONFIG = {
    'host': 'gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3BAijZ6wxqbmp3n.root',
    'password': 'BDs2xnssZHYNtQS2',
    'database': 'peer_data',
    'charset': 'utf8mb4',
    'ssl': {'ca': None}
}

def update_tidb():
    print("--- [1] TiDB peer_data 업데이트 시작 ---")
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 1. 듀이카 학생 11건 업데이트: 학사인문
    cursor.execute("""
        UPDATE peer_data
        SET student_name = '김지윤',
            univ = '한국외국어대학교(서울)',
            major = '경제학전공',
            center = '듀이카',
            department = '학사인문',
            math_total = NULL
        WHERE year = 2025 AND student_name = '김지윤' AND department = '학사인문'
    """)
    duica_affected = cursor.rowcount
    print(f"듀이카 김지윤 (한국외대 경제학전공) 업데이트 완료: {duica_affected}행")
    
    # 2. 강남 학생 5건 업데이트: department != '학사인문'
    cursor.execute("""
        UPDATE peer_data
        SET student_name = '김지윤_강남',
            univ = '서울시립대학교',
            major = '융합응용화학과',
            center = '강남',
            department = '일반자연'
        WHERE year = 2025 AND student_name = '김지윤' AND department != '학사인문'
    """)
    gangnam_affected = cursor.rowcount
    print(f"강남 김지윤 (서울시립대 융합응용화학과) 업데이트 완료: {gangnam_affected}행")
    
    conn.commit()
    
    # 확인 쿼리
    cursor.execute("""
        SELECT student_name, month, department, center, univ, major, math_total
        FROM peer_data
        WHERE year = 2025 AND student_name LIKE '김지윤%'
        ORDER BY student_name, month
    """)
    results = cursor.fetchall()
    print("DB 업데이트 후 결과:")
    for r in results:
        print(f"  {r['student_name']} | {r['month']}월 | {r['department']} | {r['center']} | {r['univ']} | {r['major']} | 수:{r['math_total']}")
    
    conn.close()

def update_csv_files():
    print("\n--- [2] 로컬 데이터 파일 업데이트 시작 ---")
    
    # 1) data/raw/25/2025_최종.csv
    p1 = BASE_DIR / "data" / "raw" / "25" / "2025_최종.csv"
    if p1.exists():
        df1 = pd.read_csv(p1)
        # 듀이카: year==2025, student_name=='김지윤', department=='학사인문'
        mask_duica = (df1['year'] == 2025) & (df1['student_name'] == '김지윤') & (df1['department'] == '학사인문')
        df1.loc[mask_duica, 'univ'] = '한국외대'
        df1.loc[mask_duica, 'major'] = '경제학'
        if 'center' in df1.columns:
            df1.loc[mask_duica, 'center'] = '듀이카'
        if 'math_total' in df1.columns:
            df1.loc[mask_duica, 'math_total'] = None
            
        # 강남: year==2025, student_name=='김지윤', department!='학사인문'
        mask_gangnam = (df1['year'] == 2025) & (df1['student_name'] == '김지윤') & (df1['department'] != '학사인문')
        df1.loc[mask_gangnam, 'student_name'] = '김지윤_강남'
        df1.loc[mask_gangnam, 'univ'] = '서울시립대'
        df1.loc[mask_gangnam, 'major'] = '융합응용화학'
        df1.loc[mask_gangnam, 'department'] = '일반자연'
        if 'center' in df1.columns:
            df1.loc[mask_gangnam, 'center'] = '강남'
            
        df1.to_csv(p1, index=False)
        print(f"{p1} 업데이트 완료 (듀이카: {mask_duica.sum()}건, 강남: {mask_gangnam.sum()}건)")

    # 2) data/raw/25/updated_2025_pass.csv
    p2 = BASE_DIR / "data" / "raw" / "25" / "updated_2025_pass.csv"
    if p2.exists():
        df2 = pd.read_csv(p2)
        mask_duica = (df2['year'] == 2025) & (df2['student_name'] == '김지윤') & (df2['department'] == '학사인문')
        df2.loc[mask_duica, 'univ'] = '한국외대'
        df2.loc[mask_duica, 'major'] = '경제학'
        if 'center' in df2.columns:
            df2.loc[mask_duica, 'center'] = '듀이카'
        if 'math_total' in df2.columns:
            df2.loc[mask_duica, 'math_total'] = None
            
        mask_gangnam = (df2['year'] == 2025) & (df2['student_name'] == '김지윤') & (df2['department'] != '학사인문')
        df2.loc[mask_gangnam, 'student_name'] = '김지윤_강남'
        df2.loc[mask_gangnam, 'univ'] = '서울시립대'
        df2.loc[mask_gangnam, 'major'] = '융합응용화학'
        df2.loc[mask_gangnam, 'department'] = '일반자연'
        if 'center' in df2.columns:
            df2.loc[mask_gangnam, 'center'] = '강남'
            
        df2.to_csv(p2, index=False)
        print(f"{p2} 업데이트 완료 (듀이카: {mask_duica.sum()}건, 강남: {mask_gangnam.sum()}건)")

    # 3) data/raw/전체_영어_성적.csv
    p3 = BASE_DIR / "data" / "raw" / "전체_영어_성적.csv"
    if p3.exists():
        df3 = pd.read_csv(p3, low_memory=False)
        if 'center' in df3.columns:
            df3['center'] = df3['center'].astype(object)
        mask_duica = (df3['year'] == 2025) & (df3['student_name'] == '김지윤') & (df3['department'] == '학사인문')
        df3.loc[mask_duica, 'univ'] = '한국외대'
        df3.loc[mask_duica, 'major'] = '경제학'
        if 'center' in df3.columns:
            df3.loc[mask_duica, 'center'] = '듀이카'
        if 'math_total' in df3.columns:
            df3.loc[mask_duica, 'math_total'] = None
            
        mask_gangnam = (df3['year'] == 2025) & (df3['student_name'] == '김지윤') & (df3['department'] != '학사인문')
        df3.loc[mask_gangnam, 'student_name'] = '김지윤_강남'
        df3.loc[mask_gangnam, 'univ'] = '서울시립대'
        df3.loc[mask_gangnam, 'major'] = '융합응용화학'
        df3.loc[mask_gangnam, 'department'] = '일반자연'
        if 'center' in df3.columns:
            df3.loc[mask_gangnam, 'center'] = '강남'
            
        df3.to_csv(p3, index=False)
        print(f"{p3} 업데이트 완료 (듀이카: {mask_duica.sum()}건, 강남: {mask_gangnam.sum()}건)")

    # 4) data/processed/전체_영어_성적_정제완료.xlsx
    p4 = BASE_DIR / "data" / "processed" / "전체_영어_성적_정제완료.xlsx"
    if p4.exists():
        df4 = pd.read_excel(p4)
        if 'center' in df4.columns:
            df4['center'] = df4['center'].astype(object)
        mask_duica = (df4['year'] == 2025) & (df4['student_name'] == '김지윤') & (df4['department'] == '학사인문')
        df4.loc[mask_duica, 'univ'] = '한국외국어대학교(서울)'
        df4.loc[mask_duica, 'major'] = '경제학전공'
        if 'center' in df4.columns:
            df4.loc[mask_duica, 'center'] = '듀이카'
        if 'math_total' in df4.columns:
            df4.loc[mask_duica, 'math_total'] = None
            
        mask_gangnam = (df4['year'] == 2025) & (df4['student_name'] == '김지윤') & (df4['department'] != '학사인문')
        df4.loc[mask_gangnam, 'student_name'] = '김지윤_강남'
        df4.loc[mask_gangnam, 'univ'] = '서울시립대학교'
        df4.loc[mask_gangnam, 'major'] = '융합응용화학과'
        df4.loc[mask_gangnam, 'department'] = '일반자연'
        if 'center' in df4.columns:
            df4.loc[mask_gangnam, 'center'] = '강남'
            
        df4.to_excel(p4, index=False)
        print(f"{p4} 업데이트 완료 (듀이카: {mask_duica.sum()}건, 강남: {mask_gangnam.sum()}건)")

if __name__ == "__main__":
    update_tidb()
    update_csv_files()
    print("\n모든 작업이 성공적으로 완료되었습니다.")

import pandas as pd
import os

# 1. 경로 설정
# data_dir = r"C:\Users\esang\PycharmProjects\convhwp\년도별합격정보"
data_dir = r"/Users/pwang/PycharmProjects/peer-score-finder/"
all_years_data = []

for year in range(2019, 2027):
    score_file = os.path.join(data_dir, f"{year}_영어_성적.xlsx")
    pass_file = os.path.join(data_dir, f"{year}_합격.xlsx")

    if not os.path.exists(score_file):
        continue

    print(f"📦 {year}년도 데이터 매칭 및 통합 중...")

    # [수정] 시트 순회 없이 이미 잘 만들어진 Sheet1 통째로 불러오기
    df_scores = pd.read_excel(score_file, sheet_name='Sheet1')

    # 만약 기존 파일에 영문 변환이 안 되어 있을 경우를 대비한 안전장치
    df_scores = df_scores.rename(columns={
        '이름': 'student_name', '계열': 'department',
        '문법': 'grammar', '어휘': 'vocabulary', '논리': 'logic', '독해': 'reading', '월': 'month', '년도': 'year'
    })

    # 텍스트 공백 제거 및 데이터 타입 정형화
    df_scores['student_name'] = df_scores['student_name'].astype(str).str.strip()
    for col in ['grammar', 'vocabulary', 'logic', 'reading']:
        if col in df_scores.columns:
            df_scores[col] = pd.to_numeric(df_scores[col], errors='coerce').fillna(0)

    # 총점 다시 깔끔하게 계산
    df_scores['total_score'] = df_scores['grammar'] + df_scores['vocabulary'] + df_scores['logic'] + df_scores[
        'reading']

    # 대학/학과 컬럼 초기화 (기존 값 지우고 깨끗하게 매칭하기 위함)
    df_scores['univ'] = ""
    df_scores['major'] = ""

    # 2. 합격 파일 매칭 진행
    if os.path.exists(pass_file):
        try:
            df_pass = pd.read_excel(pass_file)

            # 유연한 컬럼명 찾기 로직
            name_col = [c for c in df_pass.columns if any(k in str(c) for k in ['이름', '성명', '학생'])]
            univ_col = [c for c in df_pass.columns if any(k in str(c) for k in ['최종대', '학교', '대학'])]
            major_col = [c for c in df_pass.columns if any(k in str(c) for k in ['학과', '전공', '과'])]

            if name_col and univ_col and major_col:
                df_pass = df_pass.rename(columns={
                    name_col[0]: 'student_name',
                    univ_col[0]: 'pass_univ',
                    major_col[0]: 'pass_major'
                })

                df_pass['student_name'] = df_pass['student_name'].astype(str).str.strip()

                # 이름 기준 중복 제거 (첫 번째 합격 기록 유지)
                df_pass_unique = df_pass.drop_duplicates(subset=['student_name'], keep='first')

                # 이름 기준으로 조건 없이 결합 (VLOOKUP 효과)
                df_merged = pd.merge(
                    df_scores,
                    df_pass_unique[['student_name', 'pass_univ', 'pass_major']],
                    on='student_name',
                    how='left'
                )

                # 병합된 최종 값 채우기
                df_scores['univ'] = df_merged['pass_univ'].fillna("")
                df_scores['major'] = df_merged['pass_major'].fillna("")
            else:
                print(f"⚠️ {year}년도 합격 파일에서 기준 컬럼을 찾지 못해 성적만 통합합니다. (감지된 컬럼: {list(df_pass.columns)})")
        except Exception as e:
            print(f"❌ {year}년도 합격 파일 처리 중 예상치 못한 에러 발생: {e}")

    all_years_data.append(df_scores)

# 3. 최종 통합 및 저장
final_all_df = pd.concat(all_years_data, ignore_index=True)

# 요구사항 컬럼 순서 고정
column_order = ['year', 'student_name', 'month', 'grammar', 'vocabulary', 'logic', 'reading', 'total_score', 'univ',
                'major', 'department']
final_all_df = final_all_df[column_order]

output_file = os.path.join(data_dir, "최종_통합_성적_합격_데이터.xlsx")
final_all_df.to_excel(output_file, index=False)
print(f"\n🎉 [진짜 완벽 통합 완료] '{output_file}' 파일이 성공적으로 생성되었습니다!")
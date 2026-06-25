import pandas as pd

# 1. 원본 엑셀 파일 경로 지정
file_name = r"C:\Users\esang\PycharmProjects\convhwp\19_11월_성적표_영어.xlsm"

# 2. 모든 시트 불러오기
all_sheets = pd.read_excel(file_name, sheet_name=None)

all_data = []

# 3. 각 시트 순회 및 가공
for sheet_name, df in all_sheets.items():
    try:
        month_val = int(''.join(filter(str.isdigit, sheet_name)))
    except ValueError:
        continue

    df['month'] = month_val
    df['year'] = 2023  # 수험 연도 지정

    all_data.append(df)

# 4. 데이터 통합
final_df = pd.concat(all_data, ignore_index=True)

# [수정 포인트 1] 한글 컬럼명 변경 (이미지에 있던 이름만 정확히 매칭)
final_df = final_df.rename(columns={
    '이름': 'student_name',
    '계열': 'department',
    '문법': 'grammar',
    '어휘': 'vocabulary',
    '논리': 'logic',
    '독해': 'reading'
})

# [수정 포인트 2] 총점(total_score)을 파이썬이 네 과목 점수를 더해서 자동으로 계산하게 함
final_df['total_score'] = final_df['grammar'] + final_df['vocabulary'] + final_df['logic'] + final_df['reading']

# [수정 포인트 3] 빈 값으로 둘 대학, 학과 컬럼 생성
final_df['univ'] = ""
final_df['major'] = ""

# [수정 포인트 4] 실제 존재하는 컬럼들로만 순서 재배치 (admission_type 제외)
column_order = [
    'year', 'student_name', 'month',
    'grammar', 'vocabulary', 'logic', 'reading', 'total_score',
    'univ', 'major', 'department'
]
final_df = final_df[column_order]

# 5. 저장
output_name = "통합_성적데이터_정제완료.xlsx"
final_df.to_excel(output_name, index=False)

print(f"🎉 성공! 총점 계산까지 완료되어 '{output_name}' 파일이 생성되었습니다.")
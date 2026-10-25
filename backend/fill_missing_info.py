import pandas as pd
import numpy as np

# 1. 원본 엑셀 파일 불러오기 (.xlsx 또는 .xls)
input_file = "C:\\Users\\Owner\\Documents\\pwang\\dd\\peer-score-finder\\data\\raw\\2020_최종.xlsx"
output_file = "C:\\Users\\Owner\\Documents\\pwang\\dd\\peer-score-finder\\data\\raw\\2020_최종_보정완료.xlsx"

print(f"[{input_file}] 파일을 읽어오는 중...")
df = pd.read_excel(input_file)

# 컬럼명 공백 제거
df.columns = df.columns.str.strip()

# student_name 컬럼명 보정 (student_nam 등으로 잘려 있을 경우 대응)
name_col = None
for col in df.columns:
    if "student" in col.lower() or "이름" in col:
        name_col = col
        break

if not name_col:
    name_col = "student_name"

print(f"학생 이름 기준 컬럼: '{name_col}'")

# 채워 넣을 대상 컬럼 목록 (major, department, univ, center)
target_cols = [c for c in ['department', 'major', 'univ'] if c in df.columns]

# '미기재', 공백, '-', 'None' 등 무효한 값들을 NaN으로 일괄 치환
invalid_values = ['미기재', '', ' ', '-', 'nan', 'NaN', 'None', 'null', 'NULL']

for col in target_cols:
    df[col] = df[col].astype(str).str.strip()
    df[col] = df[col].replace(invalid_values, np.nan)

# 2. 학생별로 가장 유효한(최빈값 또는 첫 번째 유효값) 정보를 매핑 딕셔너리로 추출
print("학생별 유효 정보 추출 및 빈칸 매핑 중...")

for col in target_cols:
    # 유효한 값이 존재하는 행만 필터링하여 학생별 대표값 추출
    valid_records = df.dropna(subset=[col])

    if not valid_records.empty:
        # 학생별로 가장 많이 등장한 유효값(mode) 또는 첫 번째 값 선택
        student_info_map = (
            valid_records.groupby(name_col)[col]
            .agg(lambda x: x.mode().iloc[0] if not x.empty else np.nan)
            .to_dict()
        )

        # 기존 결측치(NaN) 자리에 매핑된 학생의 유효값 채우기
        df[col] = df[col].fillna(df[name_col].map(student_info_map))

# 3. 여전히 비어있는 행은 기본값('미기재' 또는 빈칸) 처리
for col in target_cols:
    df[col] = df[col].fillna("")

# 4. 정제 완료된 파일 저장
df.to_excel(output_file, index=False)
print(f"✅ 보정 완료! 결과 파일이 저장되었습니다 -> [{output_file}]")
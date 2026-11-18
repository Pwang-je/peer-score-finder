import pandas as pd

df = pd.read_excel(r"C:\Users\esang\Documents\work\devel\peer-score-finder\data\processed\전체_영어_성적_정제완료.xlsx")

print("=== 1. 기준표외_대학 목록 (상위 30개) ===")
print(df[df["매칭_상태"] == "기준표외_대학"]["univ"].value_counts().head(30))

print("\n=== 2. 검토필요(대학 + 원본학과 -> 추천후보) 목록 ===")
review_df = df[df["매칭_상태"].str.startswith("검토필요")]
print(review_df.groupby(["univ", "major", "매칭_상태"]).size().sort_values(ascending=False).to_string())

# 새 모집요강 업로드 전 기존 대학 데이터 비우기
DELETE FROM recruit_quota
WHERE year = 2026 AND univ = '학교이름';

# 학과명이 개편된 경우 과거 합격생이랑 매칭
-- 예시 1: 경영학전공 -> 경영학과
UPDATE peer_data
SET major = '경영학과'
WHERE year < 2026 AND univ = '가천대학교' AND major = '경영학전공';

-- 예시 2: 물리학과 -> 반도체물리학과
UPDATE peer_data
SET major = '반도체물리학과'
WHERE year < 2026 AND univ = '가천대학교' AND major = '물리학과';


# 특정 대학과 학과의 과거 합격생 정상 등록 여부 확인
SELECT year, month, student_name, univ, major, total_score, math_total
FROM peer_data
WHERE univ = '가천대학교' AND major = '경영학과' AND year < 2026;

# (확인용) 보이지 않는 공백값 제거 및 누락된 month 보정
# 엑셀 복사·붙여넣기 과정에서 대학명/학과명 앞뒤에 공백이 들어갔거나, 과거 합격생의 month 값이 비어(NULL) 화면 목록에서 누락될 때 한 번에 정리하는 쿼리
-- 1) 대학명·학과명 앞뒤 공백 일괄 제거
UPDATE peer_data
SET univ = TRIM(univ), major = TRIM(major)
WHERE univ LIKE '%가천%';

-- 2) 과거 합격생 데이터 중 month가 비어있는 행 보정
UPDATE peer_data
SET month = 11
WHERE year < 2026 AND month IS NULL;

# 꼭! 아무학생 아무학교에 원서 하나 담고 바로 빼야 render 에서 리프레시 됨.

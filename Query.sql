# 새 모집요강 업로드 전 기존 대학 데이터 비우기
DELETE FROM recruit_quota
WHERE year = 2026 AND univ = '한국항공대학교';

# 학과명이 개편된 경우 과거 합격생이랑 매칭
-- 예시 1: 경영학전공 -> 경영학과
UPDATE peer_data
SET major = '경영학과'
WHERE year < 2026 AND univ = '가천대학교' AND major = '경영학전공';

-- 예시 2: 물리학과 -> 반도체물리학과
UPDATE peer_data
SET major = '반도체물리학과'
WHERE year < 2026 AND univ = '가천대학교' AND major = '물리학과';


# 전공변경
# UPDATE peer_data
# SET major = '바꿀전공'
# WHERE univ = '대학'
#   AND major = '이전전공';


UPDATE peer_data
SET major = '컴퓨터공학전공'
WHERE univ = '가천대학교'
  AND major = '컴퓨터공학과';


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



# 항공대
-- 1) 현재 DB에 적재된 한국항공대학교 과거 합격생 학과명 분포 확인
SELECT department, COUNT(*) AS cnt
FROM peer_data
WHERE univ = '한국항공대학교'
GROUP BY department
ORDER BY cnt DESC;

-- 1) 공과대학
UPDATE peer_data
SET major = '공과대학'
WHERE univ = '한국항공대학교'
  AND major IN (
    '기계항공공학과', '항공우주및기계공학부', '항공우주공학과', '기계공학과',
    '신소재공학과', '항공재료공학과'
  );

-- 2) AI융합대학
UPDATE peer_data
SET major = 'AI융합대학'
WHERE univ = '한국항공대학교'
  AND major IN (
    '전기전자공학과', '항공전자정보공학부', '전자및항공전자공학부',
    '소프트웨어학과', '컴퓨터공학과', 'AI융합학부'
  );

-- 3) 항공·경영대학
UPDATE peer_data
SET major = '항공·경영대학'
WHERE univ = '한국항공대학교'
  AND major IN (
    '항공교통물류학부', '항공교통전공', '물류전공',
    '경영학부', '경영학과', '항공경영전공'
  );

DELETE FROM recruit_quota
WHERE year = 2026
  AND univ = '숙명여자대학교';


-- 1) 현재 DB에 저장된 숙명여자대학교 과거 합격생 major 분포 확인
SELECT department, major, COUNT(*) AS cnt
FROM peer_data
WHERE univ = '숙명여자대학교'
GROUP BY department, major
ORDER BY cnt DESC;

-- 2) 구(舊) 학과명·학부명 -> 현행 모집단위명 연결 예시 (조회 결과 확인 후 필요한 항목만 실행)
-- 예: 프랑스언어·문화학과(구 불어불문학과), 독일언어·문화학과(구 독어독문학과), 인공지능공학부(구 IT공학전공 등)
UPDATE peer_data
SET major = '프랑스언어·문화학과'
WHERE univ = '숙명여자대학교'
  AND major IN ('불어불문학과', '프랑스언어문화학과');

UPDATE peer_data
SET major = '독일언어·문화학과'
WHERE univ = '숙명여자대학교'
  AND major IN ('독어독문학과', '독일언어문화학과');

UPDATE peer_data
SET major = '인공지능공학부'
WHERE univ = '숙명여자대학교'
  AND major IN ('IT공학전공', 'IT공학과', '인공지능전공');

UPDATE peer_data
SET major = '지능형전자시스템전공'
WHERE univ = '숙명여자대학교'
  AND major IN ('전자공학전공', '전자공학과');

UPDATE peer_data
SET major = '신소재물리전공'
WHERE univ = '숙명여자대학교'
  AND major IN ('응용물리전공', '물리학과');

-- 2. 전형구분(department) 및 학과명(major)별 분포 확인
SELECT
    univ,
    department,
    major,
    COUNT(*) AS 행수,
    COUNT(DISTINCT student_name, year) AS 합격생수
FROM peer_data
WHERE univ LIKE '숙명%'
GROUP BY univ, department, major
ORDER BY department, 행수 DESC;

SELECT
    univ,
    COUNT(*) AS 총_데이터_행수,
    COUNT(DISTINCT student_name, year) AS 실제_합격생수
FROM peer_data
WHERE univ LIKE '숙명%'
GROUP BY univ;

-- 16명 전체 명단 및 매칭 기준 컬럼(univ, department, major) 조회
SELECT
    student_name,
    univ,
    department,
    major,
    year,
    COUNT(*) AS 데이터_행수
FROM peer_data
WHERE univ LIKE '숙명%'
GROUP BY student_name, univ, department, major, year
ORDER BY department, major, year;

INSERT INTO recruit_quota (year, univ, department, major, general_quota, bachelor_quota)
VALUES
  (2026, '숙명여자대학교', '인문', '문헌정보학과', 0, 0),
  (2026, '숙명여자대학교', '인문', '르꼬르동블루외식경영전공', 0, 0),
  (2026, '숙명여자대학교', '인문', '행정학과', 0, 0),
  (2026, '숙명여자대학교', '인문', '사회심리학과', 0, 0),
  (2026, '숙명여자대학교', '인문', '글로벌협력전공', 0, 0),
  (2026, '숙명여자대학교', '인문', '앙트러프러너십전공', 0, 0);

SELECT
    p.student_name,
    p.univ,
    p.department,
    p.major,
    p.year,
    CASE WHEN rq.id IS NULL THEN '❌ 매칭실패' ELSE '✅ 연결됨' END AS 상태
FROM (
    SELECT DISTINCT student_name, univ, department, major, year
    FROM peer_data
    WHERE univ LIKE '숙명%'
) p
LEFT JOIN recruit_quota rq
  ON rq.year = 2026
 AND rq.univ = p.univ
 AND CONCAT(
       CASE WHEN p.department LIKE '일반%' THEN '일반' ELSE '학사' END,
       rq.department
     ) = p.department
 AND REGEXP_REPLACE(REPLACE(REPLACE(REPLACE(p.major, '*', ''), '·', ''), ' ', ''), '(학전공|학과|학부|전공|과)$', '')
   = REGEXP_REPLACE(REPLACE(REPLACE(REPLACE(rq.major, '*', ''), '·', ''), ' ', ''), '(학전공|학과|학부|전공|과)$', '')
ORDER BY 상태 ASC, p.department, p.major;

-- 1) 앞쪽 학부명 접두어 제거 (임서영, 김지원)
UPDATE peer_data
SET major = '신소재물리전공'
WHERE univ = '숙명여자대학교'
  AND major LIKE '%신소재물리전공%';

UPDATE peer_data
SET major = '컴퓨터과학전공'
WHERE univ = '숙명여자대학교'
  AND major LIKE '%컴퓨터과학전공%';

-- 2) 식품영양학과·의류학과 계열 보정 (노서진, 조영은, 이지원, 박채은)
UPDATE peer_data
SET department = '일반자연'
WHERE univ = '숙명여자대학교'
  AND department = '일반인문'
  AND major IN ('식품영양학과', '의류학과');

UPDATE peer_data
SET department = '학사자연'
WHERE univ = '숙명여자대학교'
  AND department = '학사인문'
  AND major IN ('식품영양학과', '의류학과');

-- 3) 역사문화학과 계열 오타 수정 (김다희)
UPDATE peer_data
SET department = '일반인문'
WHERE univ = '숙명여자대학교'
  AND major = '역사문화학과'
  AND department = '일반자연';

DELETE FROM recruit_quota
WHERE year = 2026
  AND univ = '건국대학교';

DELETE FROM recruit_quota
WHERE year = 2026
  AND univ = '건국대학교(서울)';

-- 1) 현재 peer_data에 저장된 건국대 대학명(univ) 및 학과명(major) 분포 확인
SELECT univ, department, major, COUNT(*) AS cnt
FROM peer_data
WHERE univ LIKE '건국%'
GROUP BY univ, department, major
ORDER BY univ, department, cnt DESC;

-- 2) peer_data의 대학명이 '건국대학교'로 되어 있다면 '건국대학교(서울)'로 통일 (글로컬캠퍼스 제외)
UPDATE peer_data
SET univ = '건국대학교(서울)'
WHERE univ = '건국대학교';

-- 3) 구(舊) 학과명 / 학부 병기 명칭 -> 2027 현행 모집단위 매핑
UPDATE peer_data
SET major = '기계·로봇·자동차공학부'
WHERE univ = '건국대학교(서울)'
  AND major IN ('기계공학부', '기계공학과', '기계항공공학부', '스마트운행체공학과');

UPDATE peer_data
SET major = '화공·생명·에너지공학부'
WHERE univ = '건국대학교(서울)'
  AND major IN ('화학공학부', '화학공학과');

UPDATE peer_data
SET major = '항공우주·모빌리티공학과'
WHERE univ = '건국대학교(서울)'
  AND major IN ('항공우주정보시스템공학과', '항공우주공학과');

UPDATE peer_data
SET major = '컴퓨터공학과'
WHERE univ = '건국대학교(서울)'
  AND major IN ('컴퓨터공학부', '인공지능컴퓨터공학부 컴퓨터공학과', '소프트웨어학과');

UPDATE peer_data
SET major = TRIM(REPLACE(REPLACE(REPLACE(major, '생명공학부 ', ''), '식품융합학부 ', ''), '환경생태과학부 ', ''))
WHERE univ = '건국대학교(서울)'
  AND (major LIKE '생명공학부 %' OR major LIKE '식품융합학부 %' OR major LIKE '환경생태과학부 %');

UPDATE peer_data
SET major = TRIM(REPLACE(major, '건축학부 ', ''))
WHERE univ = '건국대학교(서울)'
  AND major LIKE '건축학부 %';

UPDATE peer_data
SET major = '의상디자인학과-인문계'
WHERE univ = '건국대학교(서울)'
  AND major IN ('의상디자인학과', '의상디자인학과(인문계)');

-- 1) peer_data에 저장된 건국대 표기 확인
SELECT univ, COUNT(*) AS cnt
FROM peer_data
WHERE univ LIKE '건국%'
GROUP BY univ;

SELECT
    p.student_name,
    p.univ,
    p.department,
    p.major,
    p.year,
    CASE WHEN rq.id IS NULL THEN '❌ 매칭실패' ELSE '✅ 연결됨' END AS 상태
FROM (
    SELECT DISTINCT student_name, univ, department, major, year
    FROM peer_data
    WHERE univ LIKE '건국%'
) p
LEFT JOIN recruit_quota rq
  ON rq.year = 2026
 AND rq.univ = p.univ
 AND CONCAT(
       CASE WHEN p.department LIKE '일반%' THEN '일반' ELSE '학사' END,
       rq.department
     ) = p.department
 AND REGEXP_REPLACE(REPLACE(REPLACE(REPLACE(p.major, '*', ''), '·', ''), ' ', ''), '(학전공|학과|학부|전공|과)$', '')
   = REGEXP_REPLACE(REPLACE(REPLACE(REPLACE(rq.major, '*', ''), '·', ''), ' ', ''), '(학전공|학과|학부|전공|과)$', '')
ORDER BY 상태 ASC, p.department, p.major;



-- 1) 계열(department) 오타 수정 (조성연, 김윤지, 유성재, 김승현, 이규리)
UPDATE peer_data
SET department = '일반자연'
WHERE univ = '건국대학교(서울)'
  AND department = '일반인문'
  AND major IN ('산업공학과', '재료공학과');

UPDATE peer_data
SET department = '일반인문'
WHERE univ = '건국대학교(서울)'
  AND department = '일반자연'
  AND major = '철학과';

UPDATE peer_data
SET department = '학사인문'
WHERE univ = '건국대학교(서울)'
  AND department = '학사자연'
  AND major = '행정학과';

-- 2) 구(舊) 학과명 -> 2027 현행 모집단위 매핑 (김진웅, 김민우, 이현규)
UPDATE peer_data
SET major = '생명과학과'
WHERE univ = '건국대학교(서울)'
  AND major = '생명과학특성학과';

UPDATE peer_data
SET major = '동물자원과학과'
WHERE univ = '건국대학교(서울)'
  AND major = '동물자원·식품과학·유통학부';

-- 3) 한민지 학생 전형구분 보완 (일반편입 기준 예시, 학사편입이면 '학사자연'으로 변경)
UPDATE peer_data
SET department = '일반자연'
WHERE univ = '건국대학교(서울)'
  AND student_name = '한민지'
  AND major = '융합생명공학과'
  AND department IN ('일반자연', '자연');


-- 1) 이현규(50번): 가운뎃점 문자 차이를 피하기 위해 LIKE로 매핑
UPDATE peer_data
SET major = '동물자원과학과'
WHERE univ = '건국대학교(서울)'
  AND major LIKE '동물자원%유통학부%';

-- 2) 한민지(46번): 전형구분 보정 (학사편입이면 '학사자연'으로 변경)
UPDATE peer_data
SET department = '일반자연'
WHERE univ = '건국대학교(서울)'
  AND student_name = '한민지'
  AND department LIKE '미기재';

-- 3) 올해 미모집 학과 3개(유현정, 김은서, 강은진)도 사이트에 노출하려면 0명 행 추가
INSERT INTO recruit_quota (year, univ, department, major, general_quota, bachelor_quota)
VALUES
  (2026, '건국대학교(서울)', '인문', '리빙디자인학과', 0, 0),
  (2026, '건국대학교(서울)', '인문', '매체연기학과', 0, 0),
  (2026, '건국대학교(서울)', '인문', '일어교육과', 0, 0);

select peer_data.student_name, peer_data.major, peer_data.year from peer_data where major = '건축학부';

-- 1) 과거 합격생 학과명을 2027 현행 모집단위명('전공')으로 변경
UPDATE peer_data
SET major = '시스템생명공학전공'
WHERE univ = '건국대학교(서울)'
  AND major = '시스템생명공학과';

UPDATE peer_data
SET major = '융합생명공학전공'
WHERE univ = '건국대학교(서울)'
  AND major = '융합생명공학과';

-- 2) 혹시 recruit_quota에 구 학과명(0/0)으로 들어간 행이 있다면 정리
DELETE FROM recruit_quota
WHERE year = 2026
  AND univ = '건국대학교(서울)'
  AND major IN ('시스템생명공학과', '융합생명공학과');

-- 1) 과거 합격생 학과명을 2027 현행 모집단위명('컴퓨터공학과')으로 변경
UPDATE peer_data
SET major = '컴퓨터공학과'
WHERE univ = '가천대학교'
  AND major = '컴퓨터공학전공';

-- 2) recruit_quota에 구 학과명(0/0)으로 등록된 행이 있다면 정리
DELETE FROM recruit_quota
WHERE year = 2026
  AND univ = '가천대학교'
  AND major = '컴퓨터공학전공';


-- (선택) 설비·소방학과 -> 설비·소방공학전공 통합
UPDATE peer_data
SET major = '설비·소방공학전공'
WHERE univ = '가천대학교'
  AND major = '설비·소방공학과';

DELETE FROM recruit_quota
WHERE year = 2026
  AND univ = '가천대학교'
  AND major = '설비·소방공학과';

-- 1) 의류학과: 일반 0명, 학사 1명으로 수정
UPDATE recruit_quota
SET general_quota = 0,
    bachelor_quota = 1
WHERE year = 2026
  AND univ = '숙명여자대학교'
  AND major = '의류학과';

-- 2) 식품영양학과: 일반 2명, 학사 1명으로 수정
UPDATE recruit_quota
SET general_quota = 2,
    bachelor_quota = 1
WHERE year = 2026
  AND univ = '숙명여자대학교'
  AND major = '식품영양학과';

select peer_data.student_name from peer_data where univ = '숙명여자대학교' and major = '화공생명공학부';

DELETE FROM recruit_quota
WHERE year = 2026
  AND univ = '경기대학교';

-- 1) 현재 DB에 적재된 경기대학교 과거 합격생 univ / department / major 분포 확인
SELECT univ, department, major, COUNT(*) AS cnt
FROM peer_data
WHERE univ LIKE '경기%'
GROUP BY univ, department, major
ORDER BY department, cnt DESC;

-- 2) 구(舊) 학과명 및 학부 병기 명칭 -> 2027 현행 모집단위 매핑 (조회 결과 확인 후 실행)
UPDATE peer_data
SET major = '산업경영공학과'
WHERE univ = '경기대학교'
  AND major = '산업경영정보공학과';

UPDATE peer_data
SET major = '컴퓨터공학전공'
WHERE univ = '경기대학교'
  AND major IN ('AI컴퓨터공학부 컴퓨터공학전공', '컴퓨터공학과');

-- 학부명 접두어가 붙어 저장된 과거 데이터 정리 (단, 요강에 학부명이 포함된 인공지능·SW안전보안 제외)
UPDATE peer_data
SET major = TRIM(
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
    major,
    '글로벌어문학부 ', ''),
    '디자인비즈학부 ', ''),
    'Fine Arts학부 ', ''),
    '스포츠과학부 ', ''),
    '공공안전학부 ', ''),
    '휴먼서비스학부 ', ''),
    '공공인재학부 ', ''),
    '경제학부 ', ''),
    '경영학부 ', ''),
    '바이오융합학부 ', ''),
    '신소재화학공학부 ', '')
)
WHERE univ = '경기대학교'
  AND major LIKE '%학부 %';

UPDATE peer_data
SET major = TRIM(REPLACE(REPLACE(major, '스마트시티공학부 ', ''), '호텔외식경영학부 ', ''))
WHERE univ = '경기대학교'
  AND (major LIKE '스마트시티공학부 %' OR major LIKE '호텔외식경영학부 %');

-- 3) 매칭 누락 여부 최종 검증 SQL
SELECT
    p.student_name,
    p.univ,
    p.department,
    p.major,
    p.year,
    CASE WHEN rq.id IS NULL THEN '❌ 매칭실패' ELSE '✅ 연결됨' END AS 상태
FROM (
    SELECT DISTINCT student_name, univ, department, major, year
    FROM peer_data
    WHERE univ LIKE '경기%'
) p
LEFT JOIN recruit_quota rq
  ON rq.year = 2026
 AND rq.univ = p.univ
 AND CONCAT(
       CASE WHEN p.department LIKE '일반%' THEN '일반' ELSE '학사' END,
       rq.department
     ) = p.department
 AND REGEXP_REPLACE(REPLACE(REPLACE(REPLACE(p.major, '*', ''), '·', ''), ' ', ''), '(학전공|학과|학부|전공|과)$', '')
   = REGEXP_REPLACE(REPLACE(REPLACE(REPLACE(rq.major, '*', ''), '·', ''), ' ', ''), '(학전공|학과|학부|전공|과)$', '')
ORDER BY 상태 ASC, p.department, p.major;

SELECT year, univ, COUNT(*) AS 학과수, SUM(general_quota) AS 일반합계, SUM(bachelor_quota) AS 학사합계
FROM recruit_quota
WHERE univ LIKE '%경기%'
GROUP BY year, univ;

UPDATE recruit_quota
SET year = 2026
WHERE univ = '국민대학교'
  AND year = 2027;

-- 1) 앞의 '전자공학부 ' 제거하여 현행 모집단위명과 일치시키기
UPDATE peer_data
SET major = '나노·반도체전공'
WHERE univ = '경기대학교'
  AND major LIKE '%나노·반도체전공%';

-- 2) 인문으로 잘못 들어간 행을 자연계열로 보정
UPDATE peer_data
SET department = '일반자연'
WHERE univ = '경기대학교'
  AND major = '나노·반도체전공'
  AND department = '일반인문';

UPDATE peer_data
SET major = '호텔경영전공'
WHERE univ = '경기대학교'
  AND major = '호텔외식호텔경영전공';

DELETE FROM recruit_quota
WHERE year = 2026
  AND univ = '국민대학교';

-- 1) 현재 DB에 적재된 국민대학교 과거 합격생 분포 확인
SELECT univ, department, major, COUNT(*) AS cnt
FROM peer_data
WHERE univ LIKE '국민%'
GROUP BY univ, department, major
ORDER BY department, cnt DESC;

-- 2) 학부명 접두어 제거 및 개편 학과명 매핑 예시
UPDATE peer_data
SET major = TRIM(
  REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
    major,
    '한국어문학부 ', ''),
    '영어영문학부 ', ''),
    '미디어·광고학부 ', ''),
    '동아시아국제학부 ', ''),
    '법학부 ', ''),
    '경영학부 ', ''),
    '경영정보학부 ', ''),
    '신소재공학부 ', ''),
    '기계공학부 ', ''),
    '전자공학부 ', '')
)
WHERE univ = '국민대학교'
  AND major LIKE '%학부 %';

UPDATE peer_data
SET major = TRIM(REPLACE(REPLACE(REPLACE(major, '건설시스템공학부 ', ''), '소프트웨어학부 ', ''), '인공지능학부 ', ''))
WHERE univ = '국민대학교'
  AND (major LIKE '건설시스템공학부 %' OR major LIKE '소프트웨어학부 %' OR major LIKE '인공지능학부 %');

-- 건축학부 세부전공 명칭 통일
UPDATE peer_data
SET major = '건축설계전공(5년제)'
WHERE univ = '국민대학교'
  AND major IN ('건축설계전공', '건축학부 건축설계전공');

UPDATE peer_data
SET major = '건축학전공(4년제)'
WHERE univ = '국민대학교'
  AND major IN ('건축학전공', '건축학부 건축학전공');

-- 3) 매칭 누락 여부 최종 검증 SQL
SELECT
    p.student_name,
    p.univ,
    p.department,
    p.major,
    p.year,
    CASE WHEN rq.id IS NULL THEN '❌ 매칭실패' ELSE '✅ 연결됨' END AS 상태
FROM (
    SELECT DISTINCT student_name, univ, department, major, year
    FROM peer_data
    WHERE univ LIKE '국민%'
) p
LEFT JOIN recruit_quota rq
  ON rq.year = 2026
 AND rq.univ = p.univ
 AND CONCAT(
       CASE WHEN p.department LIKE '일반%' THEN '일반' ELSE '학사' END,
       rq.department
     ) = p.department
 AND REGEXP_REPLACE(REPLACE(REPLACE(REPLACE(p.major, '*', ''), '·', ''), ' ', ''), '(학전공|학과|학부|전공|과)$', '')
   = REGEXP_REPLACE(REPLACE(REPLACE(REPLACE(rq.major, '*', ''), '·', ''), ' ', ''), '(학전공|학과|학부|전공|과)$', '')
ORDER BY 상태 ASC, p.department, p.major;
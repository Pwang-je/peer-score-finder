-- 대학별 모집요강 테이블 생성
CREATE TABLE IF NOT EXISTS recruit_quota (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL DEFAULT 2026,
    univ VARCHAR(50) NOT NULL,
    department VARCHAR(20) NOT NULL,
    major VARCHAR(50) NOT NULL,
    general_quota INT DEFAULT 0,
    bachelor_quota INT DEFAULT 0,
    UNIQUE KEY uq_univ_major (year, univ, major)
);

-- 원서 지원 기록 테이블 생성
CREATE TABLE IF NOT EXISTS student_applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year INT NOT NULL DEFAULT 2026,
    student_name VARCHAR(50) NOT NULL,
    univ VARCHAR(50) NOT NULL,
    major VARCHAR(50) NOT NULL,
    memo VARCHAR(50) DEFAULT '적정',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_univ (year, student_name, univ)
);


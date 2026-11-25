# 🎓 ScoreFinder (편입학 합격 예측 & 원서 지원 전략 통합 플랫폼)

> **수험생 모의고사 성적 기반 피어 매칭 합격 예측, 목표 대학 라인별 지원선 분석, 2026 모집요강 실시간 연동 원서 지원 전략, 대학별 기출문제 성적 관리를 지원하는 올인원 입시 솔루션**

---

## 📌 프로젝트 소개 (Overview)

**ScoreFinder**는 편입 수험생의 모의고사 성적 추이(영어·수학)와 대학별 기출문제 점수, 그리고 수년간 축적된 합격생 빅데이터를 정밀 분석하여 최적의 목표 대학과 학과 지원 전략을 제시하는 풀스택 웹 애플리케이션입니다.

- **성적 유사 피어 매칭:** 수험생의 1~10월 모의고사 응시 패턴과 성적 유사도가 가장 높은 지난 합격생 데이터를 실시간 매칭하여 실제 진학 및 합불 결과 비교
- **2026 모집요강 실시간 연동 원서 전략:** 대학별 일반편입·학사편입 정원 확인, 학점은행제 지원자격 메모, 학생별 원서 담기, 요강 발표 후 미선발 학과 실시간 감지 및 원클릭 학과 변경 지원
- **기출 성적 누적 관리 & 매트릭스:** 2018~2026학년도 대학별/시험 세션별(오전·오후·캠퍼스) 기출 점수 입력, 평균 대비 편차 분석, 엑셀 일괄 업로드 지원
- **상담표 원클릭 출력 & 이미지 저장:** 표준 대학 순서로 정렬된 지원 대학·학과 리포트를 HTML 인쇄 및 고해상도 PNG 이미지로 즉시 생성
- **완전 분리형 클라우드 아키텍처:** Vue 3 SPA 프론트엔드, FastAPI 고성능 백엔드, TiDB Cloud 서버리스 데이터베이스 디커플링 구성

---

## 🏛 시스템 아키텍처 (Architecture)

```text
[ 사용자 브라우저 (User Client) ]
               │
               ▼
┌─────────────────────────────────────────┐
│        Vue 3 SPA (Vite + CSS Modules)   │  <-- Vercel 글로벌 CDN 호스팅
│  - 대시보드 / 성적 분석                    │
│  - 원서 지원 전략 & 실시간 모집단위 관리   │
│  - 기출문제 성적 입력 & 엑셀 업로드       │
└─────────────────────────────────────────┘
               │
               │ REST API (/api/predict, /api/quota, /api/applications, /api/past-exams)
               ▼
┌─────────────────────────────────────────┐
│        FastAPI Backend (Python)         │  <-- Render Web Service
│  - k-NN / 점수 편차 기반 피어 매칭 엔진 │
│  - 2026 모집요강 미선발 학과 자동 감지  │
│  - 대용량 엑셀 파싱 및 정규화 파이프라인 │
└─────────────────────────────────────────┘
               │
               │ PyMySQL / SSL (Port 4000)
               ▼
┌─────────────────────────────────────────┐
│       TiDB Cloud (Serverless MySQL)     │  <-- AWS ap-northeast-1 리전
│  - peer_data (성적 및 합격생 이력)       │
│  - recruit_quota (2026 모집단위/정원)   │
│  - student_applications (지원 현황)     │
│  - student_past_exam_scores (기출 성적) │
│  - student_notes (상담 메모 및 스펙)    │
└─────────────────────────────────────────┘
```

---

## ✨ 핵심 기능 (Key Features)

### 1. 📊 모의고사 성적 분석 & 합격 예측 (Score Analysis & Prediction)
- **1월~10월 누적 성적 추이 분석:** 인문계열(영어), 자연계열(수학 / 영+수) 월별 원점수 및 백분위 실시간 연산
- **피어 매칭 (Peer Matching) 알고리즘:** 응시 패턴과 성적 곡선이 가장 유사한 선배 합격생을 탐색하여 실제 1차 합격, 최종 합격, 등록 대학 이력 대조
- **대학 라인별 합격 예측선 판정:** 서성한, 중경외시, 건동홍, 국숭세단, 광명상가, 인가경, 주요 여대 등 목표 라인별 적정/소신/안정 진단

### 2. 🎯 2026 원서 지원 전략 대시보드 (Application Strategy)
- **대학별 모집단위 및 정원 현황 (Tab 1):**
  - 2026학년도 대학별 일반편입·학사편입 선발 인원 및 실시간 학원 수험생 지원자 명단 확인
  - 대학별 학점은행제 지원자격 메모(일반 지원 최소 학점, 기회균등/농어촌 등) 인라인 편집 및 공유
  - 현행 미선발/개편 과거 학과 별도 접이식 아카이브 제공 (과거 합격생 성적 참고용)
- **학생별 지원 현황 및 빠른 담기 (Tab 2):**
  - 대학/학과 빠른 탐색 및 원클릭 원서 담기/취소
  - 학생 프로필 관리: 1·2순위 희망학과, 기피학과, 공인영어(토익) 점수, 전적대 학점, 상담 특이사항 비고 및 메모 영구 저장
  - 응시 모의고사 성적 기반 유사 성적 선배 진학 대학 추천 카드 제공
- **🚨 2026 모집요강 실시간 감지 & 원클릭 학과 변경 워크플로우:**
  - 요강 발표 전 사전 담아둔 학과가 당해 연도 요강에서 미선발(선발정원 0명 또는 폐지)될 경우 `🚨 26년 미선발` 배지와 경고 배너 자동 표시
  - 원서 카드의 `[학과 변경 ➔]` 버튼 클릭 시 해당 대학으로 자동 전환되며, 선발 중인 새 학과를 클릭하면 기존 원서 자동 삭제 후 즉시 대체 등록
- **🖨️ 지원 대학·학과 상담표 인쇄 및 PNG 이미지 저장:**
  - 서강대 ~ 서울여대 표준 순서로 정렬된 지원 대학 목록을 HTML 인쇄 및 Canvas 기반 고해상도 PNG 이미지로 저장 (미선발 학과는 붉은색 경고 표시)

### 3. 📝 대학별 기출문제 성적 관리 (Past Exam Score Management)
- **18~26년도 기출 점수 세부 등록:** 영어, 수학, 영+수(통합) 과목별 내 점수, 평균, 편차, 풀이 메모 입력
- **대학별 세부 세션 분리 관리:** 단국대(죽전 vs 천안 분리, 오전/오후), 명지대(오전/오후), 아주대, 서울여대, 숙명여대 등 캠퍼스/전형별 기출 분리
- **엑셀 일괄 업로드 & 템플릿 제공:** 표준 기출 성적 엑셀 서식을 다운로드하여 수십 명의 기출 점수를 일괄 DB 저장
- **한눈에 보는 기출 성적 칩 & 매트릭스:** 대학별 평균 점수, 최근 응시 점수 요약 배지 표시

---

## 📂 프로젝트 구조 (Directory Structure)

```text
peer-score-finder/
├── backend/                      # FastAPI 기반 고성능 RESTful API 서버
│   ├── main.py                   # 메인 애플리케이션 진입점 및 전체 API 엔드포인트
│   ├── tidb_db.py                # TiDB Cloud(MySQL) 커넥션 설정
│   ├── fill_missing_info.py      # 결측 성적 및 인적사항 보정 스크립트
│   └── requirements.txt          # 백엔드 의존성 패키지 목록
│
├── frontend/                     # Vue.js 3 기반 모던 반응형 웹 애플리케이션
│   ├── public/                   # 파비콘 및 SVG 벡터 에셋
│   ├── src/
│   │   ├── assets/               # 정적 이미지 및 로고
│   │   ├── components/           # 핵심 비즈니스 뷰 컴포넌트
│   │   │   ├── ApplicationStrategy.vue # 2026 원서 지원 전략 & 모집요강 대시보드
│   │   │   └── PastExamScoreInput.vue  # 기출문제 성적 입력 & 엑셀 일괄 관리
│   │   ├── styles/               # 컴포넌트별 분리된 Scoped CSS 모듈
│   │   │   ├── App.css                 # 메인 대시보드 레이아웃 스타일
│   │   │   ├── App.global.css          # 전역 폰트(SUIT), 공통 유틸리티 스타일
│   │   │   ├── ApplicationStrategy.css # 원서 지원 전략 컴포넌트 전용 스타일
│   │   │   └── PastExamScoreInput.css  # 기출 성적 등록 컴포넌트 전용 스타일
│   │   ├── App.vue               # 메인 레이아웃 및 탭 네비게이션
│   │   ├── main.js               # 프론트엔드 진입점
│   │   └── style.css             # 베이스 리셋 CSS
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── data/                         # 입시 분석용 원본 및 정제 데이터셋
│   ├── raw/                      # 연도별 합격생 원본 엑셀/CSV 데이터 (.gitignore 적용)
│   └── processed/                # 정규화 완료된 전체 성적 통합 파일
│
├── scripts/                      # 데이터 정제, 점수 매핑 및 DB 마이그레이션 도구
│   ├── merge_all.py              # 연도별 성적 데이터 병합 및 학과명 표준화
│   ├── stu.py                    # 학생별 성적 지표 전처리 스크립트
│   ├── upload_csv_to_tidb.py     # 로컬 CSV 데이터를 TiDB Cloud로 일괄 업로드
│   └── upload_quota_to_tidb.py   # 2026학년도 대학별 모집정원 엑셀 DB 적재
│
├── .gitignore                    # 민감 정보 및 대용량 데이터 제외 설정
└── README.md                     # 프로젝트 문서
```

---

## 🛠 기술 스택 (Tech Stack)

### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Server:** Uvicorn
- **Data & ML:** Pandas, NumPy, Scikit-Learn (NearestNeighbors), OpenPyXL
- **Database Driver:** PyMySQL, Cryptography

### Frontend
- **Framework:** Vue.js 3 (Composition API / `<script setup>`)
- **Build Tool:** Vite 8+
- **Icons:** Lucide Vue Next
- **Graphics & Export:** HTML5 Canvas API (상담표 PNG 생성)
- **Styling:** 모듈형 Scoped CSS (`src/styles/`), SUIT 웹폰트

### Database & Cloud DevOps
- **Database:** TiDB Cloud (Serverless MySQL Compatible, TLS/SSL 암호화 적용)
- **Backend Hosting:** Render (Web Service)
- **Frontend Hosting:** Vercel (Global Edge Network)

---

## 💻 로컬 개발 환경 실행 방법 (Getting Started)

### 1. 백엔드 (FastAPI) 실행
```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate       # macOS / Linux
# Windows (PowerShell): .\venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt

# 로컬 개발 서버 가동
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- **API Swagger 대시보드:** `http://localhost:8000/docs`

### 2. 프론트엔드 (Vue 3 + Vite) 실행
```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 종속성 패키지 설치
npm install

# 개발 서버 시작
npm run dev
```
- **로컬 서비스 URL:** `http://localhost:5173`

### 3. 프로덕션 빌드 검증
```bash
cd frontend
npm run build
```

---

## ☁️ 배포 가이드 (Cloud Deployment)

### Render (백엔드 배포 설정)
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** `Free` (cron-job.org 등을 활용한 헬스체크 핑 유지 권장)

### Vercel (프론트엔드 배포 설정)
- **Root Directory:** `frontend`
- **Framework Preset:** `Vite`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
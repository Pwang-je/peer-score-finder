# 🎓 대학 합격 예측 서비스 (College Admission Predictor)

> **수험생 성적 데이터를 기반으로 지원 가능한 대학 및 학과 합격 가능성을 정밀하게 예측하고 추천해 주는 웹 서비스**

---

## 📌 프로젝트 소개 (Overview)

수험생의 표준점수, 백분위, 등급 등 다양한 성적 지표를 종합 분석하여 목표 대학 및 적정/안정 지원 가능 대학을 한눈에 파악할 수 있도록 돕는 솔루션입니다.

- **실시간 예측 연산:** 백엔드 API와 클라우드 데이터베이스 간 최적화된 쿼리를 통한 빠른 결과 산출
- **직관적인 UI/UX:** 수험생과 학부모 모두 직관적으로 이해할 수 있는 결과 리포트 시각화
- **완전 분리형 클라우드 아키텍처:** 프론트엔드, 백엔드, 데이터베이스의 완전한 디커플링(Decoupling) 배포

---

## 🏛 시스템 아키텍처 (Architecture)

```
[ 사용자 브라우저 (User Client) ]
               │
               ▼
┌───────────────────────────────┐
│     Vue.js Frontend (SPA)     │  <-- Vercel 글로벌 CDN 호스팅
└───────────────────────────────┘
               │
               │ REST API (/api/predict)
               ▼
┌───────────────────────────────┐
│     FastAPI Backend (API)     │  <-- Render Web Service
└───────────────────────────────┘
               │
               │ PyMySQL / SSL (Port 4000)
               ▼
┌───────────────────────────────┐
│    TiDB Cloud (MySQL DB)      │  <-- 입시 데이터 및 컷라인 저장
└───────────────────────────────┘
```

---

## 📂 프로젝트 구조 (Directory Structure)

프로젝트는 프론트엔드, 백엔드, 데이터 파이프라인 및 원본 데이터셋이 명확히 분리된 모노레포(Monorepo) 구조로 관리됩니다.

```
peer-score-finder/
├── backend/                      # FastAPI 기반 RESTful API 서버
│   ├── main.py                   # 애플리케이션 진입점 및 API 라우터
│   ├── database.py               # TiDB Cloud(MySQL) 커넥션 풀 및 SSL 설정
│   └── requirements.txt          # 백엔드 의존성 패키지 목록
│
├── frontend/                     # Vue.js 기반 반응형 웹 애플리케이션
│   ├── public/                   # 파비콘 및 정적 에셋
│   ├── src/
│   │   ├── assets/               # CSS 스타일 및 이미지
│   │   ├── App.vue               # 메인 레이아웃 컴포넌트
│   │   ├── main.js               # 프론트엔드 진입점
│   │   └── style.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── data/                         # 입시 분석용 데이터셋
│   └── raw/                      # 연도별 합격생 원본 엑셀 및 CSV 파일 (.gitignore 적용)
│
├── scripts/                      # 데이터 수집, 정제 및 DB 마이그레이션 도구
│   ├── merge_all.py              # 연도별 데이터 병합 및 정규화
│   ├── stu.py                    # 학생 성적 지표 전처리 스크립트
│   └── upload_csv_to_tidb.py     # 로컬 CSV 데이터를 TiDB Cloud로 일괄 업로드
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
- **Data & DB:** Pandas, PyMySQL, SQLAlchemy, Cryptography

### Frontend
- **Framework:** Vue.js 3 (Vite)
- **Styling:** CSS3, Flexbox/Grid
- **HTTP Client:** Axios / Fetch API

### Database & DevOps
- **Database:** TiDB Cloud (Serverless MySQL Compatible, TLS 암호화 적용)
- **Backend Hosting:** Render (Web Service Free Tier)
- **Frontend Hosting:** Vercel

---

## 💻 로컬 개발 환경 실행 방법 (Getting Started)

### 1. 백엔드(FastAPI) 실행
```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate       # macOS / Linux
# Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 로컬 개발 서버 가동
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- Swagger API 문서: `http://localhost:8000/docs`

### 2. 프론트엔드(Vue) 실행
```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 종속성 패키지 설치
npm install

# 개발 서버 시작
npm run dev
```
- 로컬 웹 서비스: `http://localhost:5173`

### 3. 데이터 마이그레이션 (옵션)
새로운 연도별 합격생 데이터를 클라우드 DB로 밀어 넣을 때 실행합니다:
```bash
python scripts/upload_csv_to_tidb.py
```

---

## 🔒 환경 변수 설정 (Environment Variables)

보안을 위해 데이터베이스 접속 정보는 소스코드에 하드코딩하지 않고 환경 변수(`.env`)로 분리 관리합니다.

| 변수명 | 설명 | 예시 |
| :--- | :--- | :--- |
| `DB_HOST` | TiDB Cloud 호스트 엔드포인트 | `gateway01.ap-northeast-1.prod.aws.tidbcloud.com` |
| `DB_PORT` | 데이터베이스 접속 포트 | `4000` |
| `DB_USER` | DB 사용자 계정 | `3BAijZ6wxqbmp3n.root` |
| `DB_PASSWORD` | DB 보안 비밀번호 | `******` |
| `DB_NAME` | 서비스 데이터베이스 명 | `peer_data` |

---

## ☁️ 배포 가이드 (Cloud Deployment)

### Render (백엔드 배포 설정)
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** `Free`

### Vercel (프론트엔드 배포 설정)
- **Root Directory:** `frontend`
- **Framework Preset:** `Vite`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
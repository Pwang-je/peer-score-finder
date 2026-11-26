<template>
  <div class="dashboard-root">
    <!-- 🌟 최상단 메인 페이지 전환 탭 바 -->
    <div class="main-mode-nav">
      <button
        @click="currentMainView = 'analysis'"
        :class="['mode-nav-btn', { active: currentMainView === 'analysis' }]"
      >
        성적 합격 예측 (Peer Analyzer)
      </button>
      <button
        @click="currentMainView = 'strategy'"
        :class="['mode-nav-btn', { active: currentMainView === 'strategy' }]"
      >
        원서 지원 현황
      </button>
      <button
        @click="currentMainView = 'past_exam'"
        :class="['mode-nav-btn', { active: currentMainView === 'past_exam' }]"
      >
        기출 성적 직접 입력
      </button>
    </div>

    <!-- 화면 A: 신규 원서 지원 현황 및 전략 관리 컴포넌트 -->
    <ApplicationStrategy v-if="currentMainView === 'strategy'" />

    <!-- 화면 C: 학생 기출 성적 직접 입력 컴포넌트 -->
    <PastExamScoreInput v-else-if="currentMainView === 'past_exam'" />

    <!-- 화면 B: 기존 Peer Analyzer 성적 및 지원 가능 대학 분석 대시보드 -->
    <template v-else>
      <!-- 헤더 섹션 -->
      <header class="app-header">
        <!-- 헤더 우측 상단 관리자 업로드 버튼 -->
        <div class="admin-action-row">
          <button @click="openUploadModal" class="admin-upload-btn">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            <span>성적 엑셀/CSV 일괄 업로드</span>
          </button>
        </div>

        <!-- 🌟 단계별(사전검증 ➔ 확인 ➔ 반영) 업로드 모달 창 -->
        <div v-if="showUploadModal" class="modal-backdrop" @click.self="closeUploadModal">
          <div class="modal-card">
            <div class="modal-header">
              <h3 style="display: flex; align-items: center; gap: 8px;">
                <FileSpreadsheet :size="18" :stroke-width="2" />
                <span>성적 엑셀/CSV 사전 검증 및 적재</span>
              </h3>
              <button @click="closeUploadModal" class="modal-close-btn">&times;</button>
            </div>

            <!-- 1단계: 파일 선택 및 기본 가이드 -->
            <div v-if="uploadStep === 'select'" class="modal-body">
              <p class="modal-guide">
                엑셀(.xlsx) 또는 .csv 파일을 선택하면 <strong>DB에 넣기 전 동명이인 및 결측치를 먼저 진단</strong>합니다.<br>
                <strong>필수 컬럼:</strong> <code>year</code>, <code>month</code>, <code>student_name</code>, <code>total_score</code>,
                <code>grammar</code>, <code>vocabulary</code>, <code>logic</code>, <code>reading</code><br>
                <strong>선택 컬럼:</strong> <code>math_total</code>, <code>univ</code>, <code>major</code>,
                <code>department</code>, <code>center(분원)</code>
              </p>

              <div class="file-drop-zone">
                <input type="file" ref="excelFileInput" @change="handleFileChange" accept=".xlsx, .xls, .csv"
                       class="file-input-hidden" id="excelFile">
                <label for="excelFile" class="file-drop-label">
                  <span class="file-icon"><FileText :size="32" :stroke-width="1.6" /></span>
                  <span v-if="!selectedFile" class="file-txt">여기를 클릭하여 파일을 선택하세요 (.xlsx, .csv)</span>
                  <span v-else class="file-txt selected">{{ selectedFile.name }} ({{
                      (selectedFile.size / 1024).toFixed(1)
                    }} KB)</span>
                </label>
              </div>

              <div v-if="uploadStatusMsg" :class="['upload-msg-box', uploadStatusType]">
                {{ uploadStatusMsg }}
              </div>
            </div>

            <!-- 2단계: 사전 검증(Dry-run) 결과 리포트 및 보정 옵션 확인 -->
            <div v-else-if="uploadStep === 'review'" class="modal-body">
              <div class="report-header">
                <span class="report-filename">{{ validationReport.filename }}</span>
                <span class="report-total">총 <strong>{{ validationReport.total_rows }}</strong>행 분석 완료</span>
              </div>

              <!-- 동명이인 충돌 알림 -->
              <div v-if="validationReport.duplicate_count > 0" class="alert-block warning">
                <div class="alert-title" style="display: flex; align-items: center; gap: 6px;">
                  <AlertTriangle :size="15" :stroke-width="2" />
                  <span>동명이인 충돌 {{ validationReport.duplicate_count }}건 감지</span>
                </div>
                <p class="alert-desc">동일 연도/월에 이름이 같아 덮어쓰기 위험이 있습니다.</p>
                <div class="dup-scroll-list">
                  <div v-for="(d, i) in validationReport.issues.duplicates" :key="i" class="dup-item">
                    <strong>{{ d.year }}년 {{ d.month }}월 {{ d.name }}</strong> ({{ d.count }}명):
                    <span>분원 [{{ d.centers.length ? d.centers.join(', ') : '미기재' }}]</span> /
                    <span>계열 [{{ d.departments.length ? d.departments.join(', ') : '미기재' }}]</span>
                  </div>
                </div>
                <label class="custom-checkbox">
                  <input type="checkbox" v-model="uploadOptions.resolveDuplicates"/>
                  <span>타 분원 학생 이름 뒤에 분원명 자동 부착 (예: <code>이름_노원</code>)</span>
                </label>
              </div>

              <!-- 계열 및 정보 누락 알림 -->
              <div v-if="validationReport.issues.missing_department > 0" class="alert-block info">
                <div class="alert-title" style="display: flex; align-items: center; gap: 6px;">
                  <Info :size="15" :stroke-width="2" />
                  <span>계열(department) 미기재 {{ validationReport.issues.missing_department }}건 발견</span>
                </div>
                <p class="alert-desc">
                  해당 학생의 다른 월 합격/응시 기록을 바탕으로 <strong>{{ validationReport.issues.auto_fixable_department }}건</strong> 자동 복구
                  가능합니다.
                </p>
                <label class="custom-checkbox">
                  <input type="checkbox" v-model="uploadOptions.autoFillMissing"/>
                  <span>다른 월 유효 기록을 탐색하여 빈칸(계열/학과/대학) 자동 보정</span>
                </label>
              </div>

              <!-- 완전 무결할 때 -->
              <div v-if="validationReport.duplicate_count === 0 && validationReport.issues.missing_department === 0"
                   class="alert-block success" style="display: flex; align-items: center; gap: 6px;">
                <CheckCircle2 :size="16" :stroke-width="2" />
                <span>데이터 충돌이나 누락 없이 완벽합니다. 즉시 적재 가능합니다.</span>
              </div>

              <div v-if="uploadStatusMsg" :class="['upload-msg-box', uploadStatusType]" style="margin-top: 12px;">
                {{ uploadStatusMsg }}
              </div>
            </div>

            <!-- 모달 하단 버튼 -->
            <div class="modal-footer">
              <template v-if="uploadStep === 'select'">
                <button @click="closeUploadModal" class="cancel-btn" :disabled="isUploading">닫기</button>
                <button @click="runValidation" class="confirm-btn" :disabled="!selectedFile || isUploading">
                  <span v-if="isUploading">파일 분석 중...</span>
                  <span v-else>검증 및 리포트 확인</span>
                </button>
              </template>
              <template v-else-if="uploadStep === 'review'">
                <button @click="resetUploadStep" class="cancel-btn" :disabled="isUploading">파일 다시 선택</button>
                <button @click="commitValidatedUpload" class="confirm-btn" :disabled="isUploading">
                  <span v-if="isUploading">DB 반영 적재 중...</span>
                  <span v-else>최종 DB 반영 실행</span>
                </button>
              </template>
            </div>
          </div>
        </div>

        <div class="header-content">
          <div class="brand-badge">데이터분석 연습용 사이트</div>
          <h1 class="main-title">Peer Analyzer</h1>
          <p class="main-desc">
            2019~2025 합격자 성적 패턴 데이터를 기반으로 나와 가장 비슷한 점수 그룹을 탐색합니다.
          </p>
        </div>
      </header>

      <main class="dashboard-body">
        <!-- 1. 알고리즘 작동 프로세스 카드 -->
        <section class="methodology-card">
          <div class="methodology-header">
            <span class="icon-chip">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                   stroke-linejoin="round">
                <path
                    d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </span>
            <h3>Peer Analyzer의 작동 방식에 대하여?</h3>
          </div>
          <div class="methodology-grid">
            <div class="method-step">
              <div class="step-num">01</div>
              <div class="step-body">
                <strong>총점만 보지 않고 '과목별 균형'을 봅니다</strong>
                <p>총점이 70점으로 같아도 문법 강자형인지, 독해 올인형인지는 전혀 다릅니다. 문법·어휘·논리·독해(자연계열은 수학 포함) 영역의 점수 비율을 분석해 고유한 성적 특징을 만듭니다.</p>
              </div>
            </div>
            <div class="method-step">
              <div class="step-num">02</div>
              <div class="step-body">
                <strong>나와 강점·약점이 똑같았던 학생을 찾습니다</strong>
                <p>수만 명의 합격자 데이터 중에서 "내가 잘하는 과목을 똑같이 잘했고, 내가 어려워하는 과목을 똑같이 겪었던" 유사한 합격 학생들을 골라냅니다.</p>
              </div>
            </div>
            <div class="method-step">
              <div class="step-num">03</div>
              <div class="step-body">
                <strong>그 학생들이 실제로 어디에 붙었는지 보여줍니다</strong>
                <p>나와 비슷한 성적 패턴을 가졌던 학생들이 최종적으로 어느 대학·학과에 합격했는지 모아서 보여주고, 11월까지 성적이 어떻게 올랐는지 알려줍니다.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- 2. 컨트롤 패널 (2열 레이아웃) -->
        <section class="control-grid">
          <!-- 왼쪽: 2026 재원생 선택 패널 -->
          <div class="glass-panel">
            <div class="panel-tag-row">
              <span class="panel-tag">MODE 01</span>
              <!-- 계열 자동 감지 뱃지 -->
              <span v-if="form.student_name && isNatural" class="track-badge natural">자연</span>
              <span v-else-if="form.student_name && !isNatural" class="track-badge human">인문</span>
            </div>

            <h2 class="panel-heading">26년도 성적 불러오기</h2>
            <div class="form-row">
              <div class="input-wrap">
                <label>학생 선택</label>
                <select v-model="form.student_name" @change="onStudentSelectChange" class="modern-select">
                  <option value="" disabled selected>학생을 선택해 주세요</option>
                  <option v-for="(name, idx) in allStudents" :key="idx" :value="name">
                    {{ name }}
                  </option>
                </select>
              </div>
              <div class="input-wrap">
                <label>모의고사 월</label>
                <select v-model="form.month" @change="loadStudentScore" class="modern-select">
                  <option value="" disabled selected>월 선택</option>
                  <option v-for="m in [1,2,3,4,5,6,7,8,9,10,11]" :key="m" :value="m">{{ m }}월 모의고사</option>
                </select>
              </div>
            </div>

            <!-- 로드된 학생 스탯 모니터 -->
            <div class="stat-summary-box">
              <div class="stat-summary-title">
                {{
                  form.student_name ? `${form.student_name} 학생 (${form.month ? form.month + '월' : '월 미선택'} 데이터)` : '선택된 학생이 없습니다'
                }}
              </div>
              <div class="stat-mini-grid">
                <div class="stat-pill"><span class="k">문법</span><span class="v">{{ studentDBData.grammar }}</span></div>
                <div class="stat-pill"><span class="k">어휘</span><span class="v">{{ studentDBData.vocabulary }}</span>
                </div>
                <div class="stat-pill"><span class="k">논리</span><span class="v">{{ studentDBData.logic }}</span></div>
                <div class="stat-pill"><span class="k">독해</span><span class="v">{{ studentDBData.reading }}</span></div>
                <div class="stat-pill total"><span class="k">영어</span><span class="v">{{
                    studentDBData.total_score
                  }}</span></div>
                <div v-if="isNatural" class="stat-pill math"><span class="k">수학</span><span
                    class="v">{{ studentDBData.math_total }}</span></div>
              </div>
            </div>
          </div>

          <!-- 오른쪽: 점수 직접 입력 패널 -->
          <div class="glass-panel">
            <div class="panel-tag-row">
              <span class="panel-tag">MODE 02</span>
              <!-- 수동 계열 선택 토글 버튼 -->
              <div class="track-toggle-group">
                <button :class="['toggle-btn', { active: !manualIsNatural }]" @click="manualIsNatural = false">인문계
                </button>
                <button :class="['toggle-btn', { active: manualIsNatural }]" @click="manualIsNatural = true">자연계</button>
              </div>
            </div>

            <h2 class="panel-heading">점수 임의 직접 입력</h2>
            <div class="form-row">
              <div class="input-wrap full">
                <label>비교 기준 월 선택</label>
                <select v-model="manualMonth" class="modern-select">
                  <option value="" disabled selected>비교할 기준 월을 선택해 주세요</option>
                  <option v-for="m in [1,2,3,4,5,6,7,8,9,10,11]" :key="m" :value="m">{{ m }}월 기준 합격생과 비교</option>
                </select>
              </div>
            </div>

            <!-- 점수 입력 그리드 -->
            <div :class="['manual-score-grid', { 'grid-natural': manualIsNatural }]">
              <div class="input-wrap">
                <label>문법</label>
                <input type="number" v-model.number="form.grammar" step="0.1" placeholder="0.0" class="modern-input">
              </div>
              <div class="input-wrap">
                <label>어휘</label>
                <input type="number" v-model.number="form.vocabulary" step="0.1" placeholder="0.0" class="modern-input">
              </div>
              <div class="input-wrap">
                <label>논리</label>
                <input type="number" v-model.number="form.logic" step="0.1" placeholder="0.0" class="modern-input">
              </div>
              <div class="input-wrap">
                <label>독해</label>
                <input type="number" v-model.number="form.reading" step="0.1" placeholder="0.0" class="modern-input">
              </div>
              <!-- 수동 자연계열 선택 시 수학 점수 입력 칸 -->
              <div v-if="manualIsNatural" class="input-wrap math-wrap">
                <label>수학 총점</label>
                <input type="number" v-model.number="form.math_total" step="0.1" placeholder="0.0"
                       class="modern-input math-input">
              </div>
            </div>

            <div class="manual-total-line">
              <span>직접 입력 점수 합계</span>
              <span class="total-number">{{ inputTotalSummary }}</span>
            </div>
          </div>
        </section>

        <!-- 🌟 [신규] 선택한 학생의 원서 지원 목록 패널 -->
        <section class="student-apps-summary-panel">
          <div class="apps-summary-header">
            <div class="header-title-group">
              <span class="panel-icon apps-icon">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
              </span>
              <div class="title-text-wrap">
                <div class="main-title-row">
                  <h3 class="panel-title">
                    {{ form.student_name ? `${form.student_name} 학생 원서 지원 목록` : '선택한 학생의 원서 지원 목록' }}
                  </h3>
                  <span v-if="form.student_name && studentApplications.length > 0" class="apps-count-badge">
                    총 {{ studentApplications.length }}개교 지원
                  </span>
                </div>
                <p class="panel-subtitle">
                  학생이 원서 전략 탭에서 담아둔 2026/2027 지원 대학 및 학과 목록입니다.
                </p>
              </div>
            </div>

            <div class="header-action-group" v-if="form.student_name">
              <button
                type="button"
                class="btn-go-strategy"
                @click="currentMainView = 'app_strategy'"
                title="원서 지원 전략 탭으로 이동"
              >
                <span>원서 전략 관리 이동 ➔</span>
              </button>
            </div>
          </div>

          <!-- 학생 미선택 안내 -->
          <div v-if="!form.student_name" class="apps-empty-guide">
            <p>위 <strong>MODE 01 [26년도 성적 불러오기]</strong>에서 학생을 선택하면, 해당 학생이 지원한 원서 목록이 이곳에 표시됩니다.</p>
          </div>

          <!-- 로딩 상태 -->
          <div v-else-if="isLoadingApplications" class="apps-summary-loading">
            원서 목록을 불러오는 중입니다...
          </div>

          <!-- 지원 원서가 없을 때 -->
          <div v-else-if="studentApplications.length === 0" class="apps-empty-guide">
            <p>
              <strong>{{ form.student_name }}</strong> 학생의 등록된 지원 원서가 없습니다.
              <button @click="currentMainView = 'app_strategy'" class="link-inline-btn">
                [원서 전략 관리] 탭에서 원서를 담아보세요 →
              </button>
            </p>
          </div>

          <!-- 지원 원서 카드 그리드 -->
          <div v-else class="apps-cards-grid">
            <div
              v-for="(app, idx) in sortedStudentApplications"
              :key="app.id || idx"
              class="app-mini-card"
              :class="{ 'is-closed': app.is_closed }"
            >
              <div class="card-top">
                <span class="card-seq">{{ idx + 1 }}</span>
                <strong class="app-univ-name">{{ app.univ }}</strong>
                <span v-if="app.is_closed" class="app-status-tag closed">미선발</span>
                <span v-else-if="!app.is_quota_released" class="app-status-tag pending">요강미정</span>
                <span v-else class="app-status-tag ok">모집</span>
              </div>
              <div class="app-major-name" :title="app.major">
                {{ app.major }}
              </div>
              <div class="card-bottom">
                <span v-if="app.is_closed" class="quota-info closed">정원 0명 (미선발)</span>
                <span v-else-if="!app.is_quota_released" class="quota-info pending">정원 미정</span>
                <span v-else class="quota-info">
                  일반 {{ app.gen_quota ?? 0 }} / 학사 {{ app.bac_quota ?? 0 }}
                </span>
                <span v-if="app.memo" class="app-memo-dot" :title="`메모: ${app.memo}`">💬</span>
              </div>
            </div>
          </div>
        </section>

        <!-- 🌟 [신규] 선택한 학생의 모든 기출고사 성적 매트릭스 표 (사진의 엑셀 스타일) -->
        <section class="student-past-exams-panel">
          <div class="past-exams-header">
            <div class="header-title-group">
              <span class="panel-icon">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2"
                     stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="3" y1="9" x2="21" y2="9"></line>
                  <line x1="3" y1="15" x2="21" y2="15"></line>
                  <line x1="9" y1="3" x2="9" y2="21"></line>
                  <line x1="15" y1="3" x2="15" y2="21"></line>
                </svg>
              </span>
              <div class="title-text-wrap">
                <div class="main-title-row">
                  <h3 class="panel-title">
                    {{ form.student_name ? `${form.student_name} 학생 기출고사 성적표` : '선택한 학생의 기출고사 성적표' }}
                  </h3>
                  <span v-if="studentPastExams.length > 0" class="score-total-chip">
                    총 {{ studentPastExams.length }}건 등록됨
                  </span>
                </div>
                <p class="panel-subtitle">
                  대학별(열) × 년도별(행) 기출고사 점수를 엑셀 표 형태로 한눈에 확인합니다.
                </p>
              </div>
            </div>

            <!-- 우측 액션 버튼 및 모드 전환 -->
            <div class="header-action-group" v-if="form.student_name">
              <div class="matrix-view-toggle">
                <button
                  type="button"
                  :class="['toggle-chip', { active: matrixViewMode === 'taken' }]"
                  @click="matrixViewMode = 'taken'"
                  title="현재 학생이 기출을 푼 대학만 모아보기"
                >
                  응시 대학만 보기 ({{ matrixTakenUnivCount }}개교)
                </button>
                <button
                  type="button"
                  :class="['toggle-chip', { active: matrixViewMode === 'all' }]"
                  @click="matrixViewMode = 'all'"
                  title="전체 주요 대학 컬럼 모두 보기"
                >
                  전체 대학 보기
                </button>
              </div>

              <button
                type="button"
                @click="currentMainView = 'past_exam'"
                class="btn-go-input-tab"
                title="기출 성적 직접 입력 탭으로 이동"
              >
                <Edit3 :size="13" :stroke-width="2" />
                <span>기출 점수 입력·수정</span>
              </button>

              <button
                type="button"
                @click="isPastExamFolded = !isPastExamFolded"
                class="btn-fold-toggle"
              >
                {{ isPastExamFolded ? '펼치기 ▼' : '접기 ▲' }}
              </button>
            </div>
          </div>

          <!-- 로딩 상태 -->
          <div v-if="isLoadingPastExams" class="past-exams-loading">
            기출 성적을 불러오는 중입니다...
          </div>

          <!-- 학생 미선택 안내 -->
          <div v-else-if="!form.student_name" class="past-exams-empty-guide">
            <span class="guide-icon"><User :size="24" :stroke-width="1.8" /></span>
            <p>위 <strong>MODE 01 [26년도 성적 불러오기]</strong>에서 학생을 선택하면, 해당 학생의 2020~2026년도 기출 점수 표가 이곳에 표시됩니다.</p>
          </div>

          <!-- 등록된 기출 성적이 없을 때 -->
          <div v-else-if="studentPastExams.length === 0" class="past-exams-empty-guide">
            <span class="guide-icon"><Info :size="24" :stroke-width="1.8" /></span>
            <p>
              <strong>{{ form.student_name }}</strong> 학생의 등록된 기출 점수가 없습니다.
              <button @click="currentMainView = 'past_exam'" class="link-inline-btn">
                [기출 성적 직접 입력] 탭에서 점수를 등록하세요 →
              </button>
            </p>
          </div>

          <!-- 🌟 [신규] 대학 라인(그룹) 탭 바 (서성한, 중경외시, 건동홍, 국숭세단 등) -->
          <div v-if="studentPastExams.length > 0 && !isPastExamFolded" class="matrix-tier-tabs">
            <button
              type="button"
              @click="matrixTierFilter = 'ALL'"
              :class="['matrix-tier-btn', { active: matrixTierFilter === 'ALL' }]"
            >
              <span class="m-tier-name">전체 대학</span>
              <span class="m-tier-count">({{ matrixTakenUnivCount }}개교)</span>
            </button>
            <button
              v-for="grp in UNIVERSITY_TIERS"
              :key="grp.tier"
              type="button"
              @click="matrixTierFilter = grp.tier"
              :class="['matrix-tier-btn', { active: matrixTierFilter === grp.tier }]"
            >
              <span class="m-tier-name">{{ grp.tier }}</span>
              <span class="m-tier-sub">{{ grp.name }}</span>
              <span v-if="getTierScoreCount(grp) > 0" class="m-tier-count-chip">
                {{ getTierScoreCount(grp) }}
              </span>
            </button>
          </div>

          <!-- 🌟 [핵심] 사진의 엑셀 스타일 매트릭스 표 (가로: 학교이름, 세로: 년도) -->
          <div v-if="studentPastExams.length > 0 && !isPastExamFolded" class="excel-matrix-wrapper">
            <div v-if="matrixUnivColumns.length === 0" class="matrix-tier-empty">
              <span>해당 라인({{ matrixTierFilter }})에 등록된 대학 기출 성적이 없습니다. 상단의 [전체 대학 보기]를 누르면 모든 대학 컬럼이 표시됩니다.</span>
            </div>
            <table v-else class="excel-matrix-table">
              <thead>
                <tr>
                  <!-- 좌상단 고정 코너 셀 -->
                  <th class="matrix-corner-th">년도 \ 대학</th>
                  <!-- 상단 가로 헤더: 학교 이름들 -->
                  <th
                    v-for="univ in matrixUnivColumns"
                    :key="univ"
                    class="matrix-univ-th"
                  >
                    <div class="th-univ-title">{{ formatMatrixUnivTitle(univ).name }}</div>
                    <div v-if="formatMatrixUnivTitle(univ).session" class="th-univ-session">
                      {{ formatMatrixUnivTitle(univ).session }}
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <!-- 년도 행 (2026 -> 2020) -->
                <tr
                  v-for="year in matrixYears"
                  :key="year"
                  class="matrix-row"
                >
                  <!-- 좌측 년도 헤더 열 -->
                  <th class="matrix-year-th">
                    <span class="year-num">{{ year }}년도</span>
                    <span class="year-sub">({{ String(year).slice(-2) }}' 기출)</span>
                  </th>

                  <!-- 각 학교별 점수 셀 -->
                  <td
                    v-for="univ in matrixUnivColumns"
                    :key="univ"
                    class="matrix-cell"
                    :class="{ 'has-score': getCellScores(year, univ).length > 0 }"
                  >
                    <div v-if="getCellScores(year, univ).length > 0" class="cell-scores-box">
                      <div
                        v-for="sc in getCellScores(year, univ)"
                        :key="sc.id || sc.subject_type"
                        class="cell-score-pill"
                        :title="getCellTooltip(sc)"
                      >
                        <span :class="['pill-subj-tag', getSubjBadgeClass(sc.subject_type)]">
                          {{ getMiniSubjText(sc.subject_type) }}
                        </span>
                        <strong class="pill-score-val">{{ sc.my_score }}</strong>
                        <span
                          v-if="sc.score_gap !== null && sc.score_gap !== undefined"
                          :class="['pill-gap', sc.score_gap >= 0 ? 'plus' : 'minus']"
                        >
                          {{ sc.score_gap >= 0 ? '+' + sc.score_gap : sc.score_gap }}
                        </span>
                      </div>
                    </div>
                    <span v-else class="cell-dash">-</span>
                  </td>
                </tr>

                <!-- 🌟 하단 통계 행: 대학별 평균 점수 -->
                <tr class="matrix-summary-row">
                  <th class="matrix-year-th summary-th">
                    평균 (응시)
                  </th>
                  <td
                    v-for="univ in matrixUnivColumns"
                    :key="univ"
                    class="matrix-cell summary-cell"
                  >
                    <div v-if="getColumnSummary(univ)" class="col-summary-content">
                      <strong class="summary-avg">{{ getColumnSummary(univ).avg }}점</strong>
                      <span class="summary-cnt">({{ getColumnSummary(univ).count }}회)</span>
                    </div>
                    <span v-else class="cell-dash">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- 과목별 가중치 패널 -->
        <section class="weight-control-panel">
          <div class="weight-header">
            <div class="weight-title-group">
              <span class="weight-icon">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#2563eb" stroke-width="2"
                     stroke-linecap="round" stroke-linejoin="round">
                  <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
                  <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
                  <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
                  <line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23"
                                                                                                 y2="16"/>
                </svg>
              </span>
              <div>
                <div class="weight-title-row">
                  <h3 class="weight-title">과목별 매칭 가중치 실시간 튜닝</h3>
                  <span v-if="isUpdating" class="live-update-badge">실시간 분석 중...</span>
                </div>
                <p class="weight-desc">슬라이더를 조작하면 0.4초 후 실시간으로 매칭 결과가 갱신됩니다.</p>
              </div>
            </div>
            <button @click="resetWeights" class="reset-weight-btn">가중치 리셋</button>
          </div>

          <div :class="['weight-sliders-grid', { 'grid-five': activeIsNatural }]">
            <div class="slider-card b-grammar-border">
              <div class="slider-meta">
                <span class="slider-name">문법 가중치</span>
                <span class="slider-badge b-grammar-badge">{{ weights.grammar.toFixed(1) }}x</span>
              </div>
              <input type="range" v-model.number="weights.grammar" min="0.2" max="2.5" step="0.1" class="weight-range">
              <div class="slider-scale"><span>0.2x</span><span>1.0x</span><span>2.5x</span></div>
            </div>

            <div class="slider-card b-vocab-border">
              <div class="slider-meta">
                <span class="slider-name">어휘 가중치</span>
                <span class="slider-badge b-vocab-badge">{{ weights.vocabulary.toFixed(1) }}x</span>
              </div>
              <input type="range" v-model.number="weights.vocabulary" min="0.2" max="2.5" step="0.1" class="weight-range">
              <div class="slider-scale"><span>0.2x</span><span>1.0x</span><span>2.5x</span></div>
            </div>

            <div class="slider-card b-logic-border">
              <div class="slider-meta">
                <span class="slider-name">논리 가중치</span>
                <span class="slider-badge b-logic-badge">{{ weights.logic.toFixed(1) }}x</span>
              </div>
              <input type="range" v-model.number="weights.logic" min="0.2" max="2.5" step="0.1" class="weight-range">
              <div class="slider-scale"><span>0.2x</span><span>1.0x</span><span>2.5x</span></div>
            </div>

            <div class="slider-card b-reading-border">
              <div class="slider-meta">
                <span class="slider-name">독해 가중치</span>
                <span class="slider-badge b-reading-badge">{{ weights.reading.toFixed(1) }}x</span>
              </div>
              <input type="range" v-model.number="weights.reading" min="0.2" max="2.5" step="0.1" class="weight-range">
              <div class="slider-scale"><span>0.2x</span><span>1.0x</span><span>2.5x</span></div>
            </div>

            <!-- 자연계열일 경우 수학 가중치 슬라이더 활성화 -->
            <div v-if="activeIsNatural" class="slider-card b-math-border">
              <div class="slider-meta">
                <span class="slider-name">수학 가중치</span>
                <span class="slider-badge b-math-badge">{{ weights.math.toFixed(1) }}x</span>
              </div>
              <input type="range" v-model.number="weights.math" min="0.5" max="3.0" step="0.1"
                     class="weight-range range-math">
              <div class="slider-scale"><span>0.5x</span><span>2.0x</span><span>3.0x</span></div>
            </div>
          </div>
        </section>

        <!-- 수동 실행 버튼 -->
        <div class="action-bar">
          <button @click="fetchPrediction" class="primary-btn">
            <span>비슷한 점수 분석 실행</span>
            <span class="btn-arrow">→</span>
          </button>
        </div>

        <!-- 3. 결과 시각화 섹션 -->
        <section v-if="result" class="results-container">

          <!-- 🌟 실제 응시 월 다차원 매칭 안내 배너 -->
          <div v-if="result.match_mode === 'multi_month'" class="matching-mode-banner">
            <div class="mode-badge-wrap">
              <span class="mode-icon"><BarChart2 :size="15" :stroke-width="2" /></span>
              <span class="mode-title">실제 응시 월 종합 매칭 분석</span>
              <span class="mode-desc">
                단일 월 평균이 아닌 <strong>실제 응시한 {{ result.tested_months.join(', ') }}월</strong> 전체 성적 추이(문법/어휘/논리/독해<template v-if="result.is_natural">/수학</template>)를 1:1로 종합 매칭한 결과입니다.
              </span>
            </div>
          </div>
          <div v-else-if="result.match_mode === 'single_month'" class="matching-mode-banner single">
            <div class="mode-badge-wrap">
              <span class="mode-icon"><Bookmark :size="15" :stroke-width="2" /></span>
              <span class="mode-title">{{ currentMonth }}월 단일 시험 매칭</span>
              <span class="mode-desc">선택된 {{ currentMonth }}월 시험 성적을 기준으로 매칭된 결과입니다.</span>
            </div>
          </div>

          <!-- 🌟 [신규] 취약/강점 파트 자동 진단 배지 바 -->
          <div v-if="result.diagnostic_tags && result.diagnostic_tags.length" class="diagnostic-banner">
            <div class="diag-label">
              <span class="diag-icon"><Target :size="15" :stroke-width="2" /></span>
              <strong>지난 합격생 대비:</strong>
            </div>
            <div class="diag-tags-wrap">
            <span
                v-for="(tag, tIdx) in result.diagnostic_tags"
                :key="tIdx"
                :class="['diag-tag', tag.part_class]"
            >
              {{ tag.text }}
            </span>
            </div>
          </div>

          <div class="section-divider">
            <span>ANALYSIS RESULTS</span>
          </div>

          <!-- 차트 대시보드 레이아웃 -->
          <div class="charts-section">
            <!-- 자연계열일 때 5개 타일 레이아웃 적용 -->
            <div :class="['mini-charts-row', { 'row-five': result.is_natural }]">
              <div class="chart-tile">
                <div class="tile-header">문법 ({{ weights.grammar.toFixed(1) }}x)</div>
                <div class="chart-canvas-box">
                  <canvas id="grammarChart"></canvas>
                </div>
              </div>
              <div class="chart-tile">
                <div class="tile-header">어휘 ({{ weights.vocabulary.toFixed(1) }}x)</div>
                <div class="chart-canvas-box">
                  <canvas id="vocabularyChart"></canvas>
                </div>
              </div>
              <div class="chart-tile">
                <div class="tile-header">논리 ({{ weights.logic.toFixed(1) }}x)</div>
                <div class="chart-canvas-box">
                  <canvas id="logicChart"></canvas>
                </div>
              </div>
              <div class="chart-tile">
                <div class="tile-header">독해 ({{ weights.reading.toFixed(1) }}x)</div>
                <div class="chart-canvas-box">
                  <canvas id="readingChart"></canvas>
                </div>
              </div>
              <!-- 수학 타일: 2칸 차지하여 깔끔하게 정렬 -->
              <div v-if="result.is_natural" class="chart-tile math-tile">
                <div class="tile-header">수학 ({{ weights.math.toFixed(1) }}x)</div>
                <div class="chart-canvas-box">
                  <canvas id="mathChart"></canvas>
                </div>
              </div>
            </div>

            <!-- 타임라인 꺾은선 차트 -->
            <div class="main-timeline-tile">
              <div class="timeline-header-wrap">
                <div class="tile-header">{{ timelineMode === 'eng' ? '영어 총점 추이 비교' : '수학 총점 추이 비교' }} (1월 ~ 11월)</div>
                <div v-if="result.is_natural" class="timeline-tab-group">
                  <button :class="['tab-btn', { active: timelineMode === 'eng' }]" @click="switchTimelineMode('eng')">영어
                    비교
                  </button>
                  <button :class="['tab-btn', { active: timelineMode === 'math' }]" @click="switchTimelineMode('math')">수학
                    비교
                  </button>
                </div>
              </div>
              <div class="timeline-canvas-box">
                <canvas id="timelineChart"></canvas>
              </div>
            </div>
          </div>

          <!-- 매칭 확률 높은 TOP 10 대학 및 학과별 분포 -->
          <div class="univ-summary-wrap">
            <h2 class="sub-heading">
              매칭 확률 높은 TOP 10 대학 및 학과별 분포
              <span class="sub-heading-pill">{{ result.is_natural ? '자연계열 기준' : '인문계열 기준' }}</span>
            </h2>
            <div class="univ-card-flow">
              <div v-for="(u, idx) in result.univ_details" :key="idx" class="univ-modern-card">
                <div class="u-card-head">
                  <div class="u-title-group">
                    <span class="u-name">{{ u.univ }}</span>
                    <span class="u-badge">총 {{ u.total_count }}명</span>
                  </div>

                  <!-- 🌟 대학별 합격 선배 평균 대비 갭 배지 -->
                  <div v-if="u.gaps" class="u-gap-group">
                    <!-- 영어 총점 갭 -->
                    <span :class="['gap-badge', u.gaps.total >= 0 ? 'plus' : 'minus']">
                      영어 {{ u.gaps.total >= 0 ? '+' + u.gaps.total : u.gaps.total }}점
                    </span>

                    <!-- 자연계열일 때 수학 총점 갭 -->
                    <span v-if="result.is_natural && u.gaps.math !== null"
                          :class="['gap-badge math', u.gaps.math >= 0 ? 'plus' : 'minus']">
                      수학 {{ u.gaps.math >= 0 ? '+' + u.gaps.math : u.gaps.math }}점
                    </span>
                  </div>
                </div>
                <div class="u-card-body">
                  <div v-for="(m, mIdx) in u.majors" :key="mIdx" class="major-pill-group">
                    <div class="m-title-bar">
                      <span class="m-title">{{ m.major }}</span>
                      <span class="m-count">{{ m.count }}명</span>
                    </div>

                    <!-- 선배 2줄 블록 구조 -->
                    <div v-for="(scoreObj, sIdx) in m.scores" :key="sIdx" class="senior-block">
                      <div class="senior-line-top">
                        <span class="badge-meta">[{{ scoreObj.year }} {{ scoreObj.name }}]</span>
                        <span class="badge-score b-total">영어 {{ scoreObj.total }}</span>
                        <span v-if="scoreObj.math !== null && scoreObj.math !== undefined" class="badge-score b-math">수학 {{
                            scoreObj.math
                          }}</span>
                      </div>

                      <div class="senior-line-sub">
                        <span class="badge-score b-grammar">{{ scoreObj.grammar }}</span>
                        <span class="badge-score b-vocab">{{ scoreObj.vocabulary }}</span>
                        <span class="badge-score b-logic">{{ scoreObj.logic }}</span>
                        <span class="badge-score b-reading">{{ scoreObj.reading }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </template>
  </div>
</template>

<script>
import axios from 'axios';
import {Chart, registerables} from 'chart.js';
import ApplicationStrategy from "./components/ApplicationStrategy.vue";
import PastExamScoreInput from "./components/PastExamScoreInput.vue";
import { ref } from 'vue'
import {
  FileSpreadsheet,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Edit3,
  User,
  Info,
  BarChart2,
  Bookmark,
  Target
} from 'lucide-vue-next';

Chart.register(...registerables);

// 백엔드 URL 기본 상수로 선언 (로컬 테스트 시 http://127.0.0.1:8000 으로 변경 가능)
const API_BASE_URL = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? 'http://127.0.0.1:8000'
  : 'https://peer-score-finder.onrender.com';

// 대학 라인(그룹) 정의 상수 (서성한, 중경외시, 건동홍, 국숭세단 등)
const UNIVERSITY_TIERS = [
  {
    tier: '서성한',
    name: '서강 · 성균관 · 한양',
    univs: ['서강대학교', '성균관대학교', '한양대학교']
  },
  {
    tier: '중경외시',
    name: '중앙 · 경희 · 한국외대 · 시립대',
    univs: ['중앙대학교', '경희대학교', '한국외국어대학교(T1 A형)', '한국외국어대학교(T2 B형)', '서울시립대학교']
  },
  {
    tier: '건동홍',
    name: '건국 · 동국 · 홍익',
    univs: ['건국대학교', '동국대학교', '홍익대학교']
  },
  {
    tier: '국숭세단',
    name: '국민 · 숭실 · 세종 · 단국',
    univs: ['국민대학교', '숭실대학교', '세종대학교', '단국대학교', '단국대학교(오전)', '단국대학교(오후)']
  },
  {
    tier: '광명가',
    name: '광운 · 명지 · 가톨릭 · 상명',
    univs: ['광운대학교', '명지대학교', '명지대학교(오전)', '명지대학교(오후)', '가톨릭대학교', '상명대학교']
  },
  {
    tier: '인가경',
    name: '인하 · 인천 · 가천 · 경기 · 아주',
    univs: ['인하대학교', '인천대학교', '가천대학교', '가천대학교(A형)', '가천대학교(B형)', '경기대학교', '아주대학교']
  },
  {
    tier: '여대라인',
    name: '이화 · 숙명 · 동덕 · 덕성 · 서울여대',
    univs: ['이화여자대학교', '숙명여자대학교', '숙명여자대학교(A형)', '숙명여자대학교(B형)', '동덕여자대학교', '덕성여자대학교', '덕성여자대학교(1교시)', '덕성여자대학교(2교시)', '덕성여자대학교(3교시)', '서울여자대학교', '서울여자대학교(오전)', '서울여자대학교(오후)']
  },
  {
    tier: '한성·항공',
    name: '한성 · 항공',
    univs: ['한성대학교', '한국항공대학교']
  }
];

export default {
  components: {
    ApplicationStrategy,
    PastExamScoreInput,
    FileSpreadsheet,
    FileText,
    AlertTriangle,
    CheckCircle2,
    Edit3,
    User,
    Info,
    BarChart2,
    Bookmark,
    Target
  },
  data() {
    return {
      currentMainView: 'analysis',
      // 모달 상태
      showUploadModal: false,
      uploadStep: 'select', // 'select' | 'review'
      selectedFile: null,
      isUploading: false,
      uploadStatusMsg: '',
      uploadStatusType: '',
      validationReport: null,
      uploadOptions: {
        resolveDuplicates: true,
        autoFillMissing: true
      },

      allStudents: [],
      isNatural: false,          // 26년도 학생 선택 시 자동 감지된 계열
      manualIsNatural: false,    // MODE 02 직접 입력 시 선택한 계열
      timelineMode: 'eng',       // 추이선 표시 모드 ('eng' 또는 'math')
      form: {
        month: '',
        grammar: '',
        vocabulary: '',
        logic: '',
        reading: '',
        math_total: '',
        student_name: ''
      },
      manualMonth: '',
      weights: {
        grammar: 1.0,
        vocabulary: 1.0,
        logic: 1.0,
        reading: 1.0,
        math: 2.0
      },
      debounceTimer: null,
      isUpdating: false,
      studentDBData: {grammar: '-', vocabulary: '-', logic: '-', reading: '-', math_total: '-', total_score: '-'},
      currentAnalysisScores: {grammar: 0, vocabulary: 0, logic: 0, reading: 0, math: 0},
      result: null,
      chartInstances: {},

      // 🌟 선택한 학생의 기출고사 성적 데이터 상태
      studentPastExams: [],
      isLoadingPastExams: false,
      isPastExamFolded: false,
      matrixViewMode: 'taken', // 'taken' (응시 대학만 보기) | 'all' (전체 대학 보기)
      matrixTierFilter: 'ALL', // 'ALL' or '서성한', '중경외시', '건동홍', '국숭세단' 등
      matrixYears: [2026, 2025, 2024, 2023, 2022, 2021, 2020],
      UNIVERSITY_TIERS,

      // 🌟 [신규] 선택한 학생의 원서 지원 현황 데이터 상태
      studentApplications: [],
      isLoadingApplications: false
    };
  },
  computed: {
    sortedStudentApplications() {
      if (!this.studentApplications || !this.studentApplications.length) return [];
      const getRank = (univ) => {
        if (!univ) return 999;
        for (let i = 0; i < this.UNIVERSITY_TIERS.length; i++) {
          const tier = this.UNIVERSITY_TIERS[i];
          if (tier.univs.some(u => univ.includes(u.split('(')[0].trim()))) {
            return i;
          }
        }
        return 999;
      };
      return [...this.studentApplications].sort((a, b) => {
        const rankA = getRank(a.univ);
        const rankB = getRank(b.univ);
        if (rankA !== rankB) return rankA - rankB;
        return (a.univ || '').localeCompare(b.univ || '', 'ko');
      });
    },
    activeIsNatural() {
      const hasManual = [this.form.grammar, this.form.vocabulary, this.form.logic, this.form.reading, this.form.math_total].some(v => v !== '');
      return hasManual ? this.manualIsNatural : this.isNatural;
    },
    inputTotalSummary() {
      const g = Number(this.form.grammar) || 0;
      const v = Number(this.form.vocabulary) || 0;
      const l = Number(this.form.logic) || 0;
      const r = Number(this.form.reading) || 0;
      const engTotal = g + v + l + r;

      if (!this.manualIsNatural) {
        return engTotal > 0 ? `${(Math.round(engTotal * 10) / 10).toFixed(1)} 점` : '- 점';
      } else {
        const m = Number(this.form.math_total) || 0;
        return (engTotal > 0 || m > 0) ? `영어 ${(Math.round(engTotal * 10) / 10).toFixed(1)}점 + 수학 ${m.toFixed(1)}점` : '- 점';
      }
    },
    matrixTakenUnivList() {
      if (!this.studentPastExams || !this.studentPastExams.length) return [];
      const standardOrder = [
        '서강대학교', '성균관대학교', '한양대학교',
        '중앙대학교', '경희대학교', '한국외국어대학교(T1 A형)', '한국외국어대학교(T2 B형)', '서울시립대학교',
        '건국대학교', '동국대학교', '홍익대학교',
        '국민대학교', '숭실대학교', '세종대학교', '단국대학교(오전)', '단국대학교(오후)', '단국대학교',
        '광운대학교', '명지대학교', '명지대학교(오전)', '명지대학교(오후)', '가톨릭대학교', '상명대학교',
        '인하대학교', '인천대학교', '가천대학교(A형)', '가천대학교(B형)', '가천대학교', '경기대학교', '아주대학교',
        '이화여자대학교', '숙명여자대학교(A형)', '숙명여자대학교(B형)', '숙명여자대학교', '동덕여자대학교',
        '덕성여자대학교(1교시)', '덕성여자대학교(2교시)', '덕성여자대학교(3교시)', '덕성여자대학교',
        '서울여자대학교(오전)', '서울여자대학교(오후)', '서울여자대학교',
        '한성대학교', '한국항공대학교'
      ];
      const set = new Set();
      for (const sc of this.studentPastExams) {
        if (sc.univ) set.add(sc.univ);
      }
      const list = Array.from(set);
      list.sort((a, b) => {
        const idxA = standardOrder.findIndex(u => a === u || a.startsWith(u) || u.startsWith(a));
        const idxB = standardOrder.findIndex(u => b === u || b.startsWith(u) || u.startsWith(b));
        if (idxA !== -1 && idxB !== -1) return idxA - idxB;
        if (idxA !== -1) return -1;
        if (idxB !== -1) return 1;
        return a.localeCompare(b);
      });
      return list;
    },
    matrixTakenUnivCount() {
      return this.matrixTakenUnivList.length;
    },
    matrixUnivColumns() {
      const standardOrder = [
        '서강대학교', '성균관대학교', '한양대학교',
        '중앙대학교', '경희대학교', '한국외국어대학교(T1 A형)', '한국외국어대학교(T2 B형)', '서울시립대학교',
        '건국대학교', '동국대학교', '홍익대학교',
        '국민대학교', '숭실대학교', '세종대학교', '단국대학교(오전)', '단국대학교(오후)',
        '광운대학교', '명지대학교', '명지대학교(오전)', '명지대학교(오후)', '가톨릭대학교', '상명대학교',
        '인하대학교', '인천대학교', '가천대학교(A형)', '가천대학교(B형)', '경기대학교', '아주대학교',
        '이화여자대학교', '숙명여자대학교(A형)', '숙명여자대학교(B형)', '동덕여자대학교',
        '덕성여자대학교(1교시)', '덕성여자대학교(2교시)', '덕성여자대학교(3교시)',
        '서울여자대학교(오전)', '서울여자대학교(오후)',
        '한성대학교', '한국항공대학교'
      ];

      let baseList = [];
      if (this.matrixViewMode === 'taken') {
        baseList = this.matrixTakenUnivList;
      } else {
        const all = [...standardOrder];
        for (const u of this.matrixTakenUnivList) {
          if (!all.includes(u)) all.push(u);
        }
        baseList = all;
      }

      // 라인(티어) 필터 적용
      if (this.matrixTierFilter === 'ALL') {
        return baseList;
      }

      const grp = UNIVERSITY_TIERS.find(g => g.tier === this.matrixTierFilter);
      if (!grp) return baseList;

      return baseList.filter(u => {
        return grp.univs.some(target => {
          if (u === target) return true;
          // 세션 포함 호환 ("단국대학교(오전)" vs "단국대학교")
          const uBase = u.replace(/\(.*?\)/, '').trim();
          const targetBase = target.replace(/\(.*?\)/, '').trim();
          return uBase === targetBase || u.startsWith(targetBase) || target.startsWith(uBase);
        });
      });
    }
  },
  watch: {
    weights: {
      deep: true,
      handler() {
        const hasScores = (this.form.student_name && this.studentDBData.grammar !== '-') ||
            (this.form.grammar !== '' || this.form.vocabulary !== '' || this.form.logic !== '' || this.form.reading !== '');

        if (!hasScores && !this.result) return;

        this.isUpdating = true;
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
          this.fetchPrediction(true);
        }, 400);
      }
    },
    'form.student_name'(newVal) {
      if (newVal) {
        this.fetchStudentPastExams(newVal);
        this.fetchStudentApplications(newVal);
      } else {
        this.studentPastExams = [];
        this.studentApplications = [];
      }
    }
  },
  mounted() {
    this.fetchAllStudents();
  },
  methods: {
    openUploadModal() {
      this.resetUploadStep();
      this.showUploadModal = true;
    },
    closeUploadModal() {
      if (this.isUploading) return;
      this.showUploadModal = false;
      this.resetUploadStep();
    },
    resetUploadStep() {
      this.uploadStep = 'select';
      this.selectedFile = null;
      this.uploadStatusMsg = '';
      this.validationReport = null;
      if (this.$refs.excelFileInput) this.$refs.excelFileInput.value = '';
    },
    handleFileChange(e) {
      const file = e.target.files[0];
      if (file) {
        this.selectedFile = file;
        this.uploadStatusMsg = '';
      }
    },
    // 🌟 1단계: 사전 검증(Dry-run) 요청
    async runValidation() {
      if (!this.selectedFile) return;

      this.isUploading = true;
      this.uploadStatusMsg = '파일의 동명이인 및 결측치를 사전 진단 중입니다...';
      this.uploadStatusType = 'info';

      const formData = new FormData();
      formData.append('file', this.selectedFile);

      try {
        const res = await axios.post(`${API_BASE_URL}/api/upload/validate`, formData, {
          headers: {'Content-Type': 'multipart/form-data'}
        });

        this.validationReport = res.data;
        this.uploadStep = 'review';
        this.uploadStatusMsg = '';
      } catch (err) {
        console.error('검증 실패:', err);
        this.uploadStatusMsg = err.response?.data?.detail || '파일 검증 중 오류가 발생했습니다. 파일 형식을 확인해 주세요.';
        this.uploadStatusType = 'error';
      } finally {
        this.isUploading = false;
      }
    },
    // 🌟 2단계: 옵션 적용 후 최종 DB 반영
    async commitValidatedUpload() {
      if (!this.selectedFile) return;

      this.isUploading = true;
      this.uploadStatusMsg = '정제 규칙을 적용하여 TiDB에 안전하게 적재 중입니다...';
      this.uploadStatusType = 'info';

      const formData = new FormData();
      formData.append('file', this.selectedFile);
      formData.append('resolve_duplicates_with_center', this.uploadOptions.resolveDuplicates);
      formData.append('auto_fill_missing', this.uploadOptions.autoFillMissing);

      try {
        const res = await axios.post(`${API_BASE_URL}/api/upload/commit`, formData, {
          headers: {'Content-Type': 'multipart/form-data'}
        });

        if (res.data.status === 'success') {
          this.uploadStatusMsg = res.data.message;
          this.uploadStatusType = 'success';
          setTimeout(() => {
            this.closeUploadModal();
            this.fetchAllStudents();
          }, 1500);
        } else {
          this.uploadStatusMsg = res.data.message;
          this.uploadStatusType = 'error';
        }
      } catch (err) {
        console.error('DB 적재 실패:', err);
        this.uploadStatusMsg = '서버 통신 중 에러가 발생했습니다.';
        this.uploadStatusType = 'error';
      } finally {
        this.isUploading = false;
      }
    },
    resetWeights() {
      this.weights = {
        grammar: 1.0,
        vocabulary: 1.0,
        logic: 1.0,
        reading: 1.0,
        math: 2.0
      };
    },
    async fetchAllStudents() {
      try {
        const res = await axios.get(`${API_BASE_URL}/all-students-2026`);
        this.allStudents = res.data;
      } catch (e) {
        console.error("전체 학생 명단 로드 실패:", e);
      }
    },
    onStudentSelectChange() {
      this.loadStudentScore();
      if (this.form.student_name) {
        this.fetchStudentPastExams(this.form.student_name);
        this.fetchStudentApplications(this.form.student_name);
      }
    },
    async fetchStudentPastExams(studentName) {
      if (!studentName) {
        this.studentPastExams = [];
        return;
      }
      this.isLoadingPastExams = true;
      try {
        const res = await axios.get(`${API_BASE_URL}/api/student-past-exams`, {
          params: { student_name: studentName }
        });
        this.studentPastExams = res.data?.scores || [];
      } catch (err) {
        console.error("기출 성적 조회 실패:", err);
        this.studentPastExams = [];
      } finally {
        this.isLoadingPastExams = false;
      }
    },
    async fetchStudentApplications(studentName) {
      if (!studentName) {
        this.studentApplications = [];
        return;
      }
      this.isLoadingApplications = true;
      try {
        const res = await axios.get(`${API_BASE_URL}/api/applications`, {
          params: { student_name: studentName }
        });
        this.studentApplications = res.data || [];
      } catch (err) {
        console.error("원서 지원 목록 조회 실패:", err);
        this.studentApplications = [];
      } finally {
        this.isLoadingApplications = false;
      }
    },
    getTierScoreCount(grp) {
      if (!this.studentPastExams || !this.studentPastExams.length) return 0;
      return this.studentPastExams.filter(s => {
        if (!s.univ) return false;
        return grp.univs.some(target => {
          if (s.univ === target) return true;
          const sBase = s.univ.replace(/\(.*?\)/, '').trim();
          const targetBase = target.replace(/\(.*?\)/, '').trim();
          return sBase === targetBase || s.univ.startsWith(targetBase) || target.startsWith(sBase);
        });
      }).length;
    },
    extractSession(univ) {
      if (!univ) return '';
      const match = univ.match(/\(([^)]+)\)/);
      return match ? match[1] : '';
    },
    getSubjBadgeClass(subj) {
      if (subj === '수학') return 'subj-math';
      if (subj === '영+수') return 'subj-both';
      return 'subj-eng';
    },
    getCellScores(year, univName) {
      if (!this.studentPastExams || !this.studentPastExams.length) return [];
      const yr = Number(year);
      return this.studentPastExams.filter(s => {
        if (Number(s.exam_year) !== yr) return false;
        if (s.univ === univName) return true;
        const sNorm = (s.univ || '').replace(/\s+/g, '');
        const uNorm = (univName || '').replace(/\s+/g, '');
        if (sNorm === uNorm) return true;

        // 명지대학교 호환 처리: 2024년 이하는 단일 공통, 2025년 이상은 오전/오후
        if (sNorm.includes('명지') && uNorm.includes('명지')) {
          if (yr <= 2024 && (univName === '명지대학교' || s.univ === '명지대학교')) {
            return true;
          }
          if (yr >= 2025 && univName === '명지대학교(오전)' && s.univ === '명지대학교') {
            return true;
          }
        }
        return false;
      });
    },
    getColumnSummary(univName) {
      if (!this.studentPastExams || !this.studentPastExams.length) return null;
      const matches = [];
      for (const yr of this.matrixYears) {
        matches.push(...this.getCellScores(yr, univName));
      }
      if (!matches.length) return null;
      const total = matches.reduce((acc, cur) => acc + (Number(cur.my_score) || 0), 0);
      return {
        avg: (total / matches.length).toFixed(1),
        count: matches.length
      };
    },
    formatMatrixUnivTitle(univ) {
      if (!univ) return { name: '', session: '' };
      if (univ === '명지대학교') {
        return { name: '명지대학교', session: '20~24년 공통' };
      }
      const match = univ.match(/^(.*?)\((.*?)\)$/);
      if (match) {
        return { name: match[1], session: match[2] };
      }
      return { name: univ, session: '' };
    },
    getMiniSubjText(subj) {
      if (subj === '수학') return '수';
      if (subj === '영+수') return '영수';
      return '영';
    },
    getCellTooltip(sc) {
      let tip = `${sc.univ} ${sc.exam_year}년도 [${sc.subject_type || '영어'}]\n내 점수: ${sc.my_score}점`;
      if (sc.avg_score) tip += `\n기출 평균: ${sc.avg_score}점 (격차: ${sc.score_gap >= 0 ? '+' : ''}${sc.score_gap}점)`;
      if (sc.memo) tip += `\n메모: ${sc.memo}`;
      return tip;
    },
    async loadStudentScore() {
      if (!this.form.student_name || !this.form.month) return;
      try {
        const res = await axios.get(`${API_BASE_URL}/get-student-score`, {
          params: { student_name: this.form.student_name, month: this.form.month }
        });

        if (res.data.is_natural !== undefined) {
          this.isNatural = res.data.is_natural;
        }

        if (res.data.status === 'success') {
          const s = res.data.data;
          this.studentDBData = {
            grammar: s.grammar !== null ? s.grammar : '-',
            vocabulary: s.vocabulary !== null ? s.vocabulary : '-',
            logic: s.logic !== null ? s.logic : '-',
            reading: s.reading !== null ? s.reading : '-',
            total_score: s.total_score !== null ? s.total_score : '-',
            math_total: (s.math_total !== null && s.math_total !== undefined && s.math_total !== '') ? s.math_total : '-'
          };

          // 직접 입력 폼 초기화
          this.form.grammar = '';
          this.form.vocabulary = '';
          this.form.logic = '';
          this.form.reading = '';
          this.form.math_total = '';
        } else {
          this.studentDBData = { grammar: '-', vocabulary: '-', logic: '-', reading: '-', math_total: '-', total_score: '-' };
          alert(`${this.form.student_name} 학생은 ${this.form.month}월 데이터가 없습니다.`);
        }
      } catch (e) {
        console.error("성적 로드 실패:", e);
      }
    },
    switchTimelineMode(mode) {
      this.timelineMode = mode;
      this.$nextTick(() => {
        this.renderTimelineChart();
      });
    },
    async fetchPrediction(isDebounce = false) {
      const hasManual = [this.form.grammar, this.form.vocabulary, this.form.logic, this.form.reading, this.form.math_total].some(v => v !== '');
      let m, name, g, v, l, r, mathScore, isNat;

      if (hasManual) {
        if (!this.manualMonth) {
          if (!isDebounce) alert("비교 기준 월을 선택해 주세요!");
          return;
        }
        m = this.manualMonth;
        name = "직접입력수험생";
        g = Number(this.form.grammar) || 0;
        v = Number(this.form.vocabulary) || 0;
        l = Number(this.form.logic) || 0;
        r = Number(this.form.reading) || 0;

        // 🌟 수정 적용된 부분
        const rawMath = this.studentDBData.math_total;
        mathScore = (rawMath !== '-' && rawMath !== '' && rawMath !== null && !isNaN(rawMath)) ? Number(rawMath) : 0;
        isNat = this.manualIsNatural;
      } else {
        if (!this.form.student_name || this.studentDBData.grammar === '-') {
          if (!isDebounce) alert("학생을 선택하거나 점수를 직접 입력해 주세요!");
          this.isUpdating = false;
          return;
        }
        if (!this.form.month) {
          if (!isDebounce) alert("모의고사 월을 선택해 주세요!");
          return;
        }
        m = this.form.month;
        name = this.form.student_name;
        g = Number(this.studentDBData.grammar);
        v = Number(this.studentDBData.vocabulary);
        l = Number(this.studentDBData.logic);
        r = Number(this.studentDBData.reading);
        mathScore = (this.studentDBData.math_total !== '-' && this.studentDBData.math_total !== '') ? Number(this.studentDBData.math_total) : 0;
        isNat = this.isNatural;
      }

      this.currentAnalysisScores = {grammar: g, vocabulary: v, logic: l, reading: r, math: mathScore};

      try {
        const res = await axios.get(`${API_BASE_URL}/predict`, {
          params: {
            month: m,
            student_name: name,
            grammar: g,
            vocabulary: v,
            logic: l,
            reading: r,
            math_total: mathScore,
            is_natural: isNat,
            w_grammar: this.weights.grammar,
            w_vocabulary: this.weights.vocabulary,
            w_logic: this.weights.logic,
            w_reading: this.weights.reading,
            w_math: this.weights.math
          }
        });

        if (res.data.status === 'success' || res.data.univ_details || res.data.month_averages) {
          this.result = res.data;
          this.$nextTick(() => {
            requestAnimationFrame(() => {
              this.renderCharts(this.result.month_averages, this.result.is_natural);
            });
          });
        } else if (!isDebounce) {
          alert(res.data.message || "결과를 불러올 수 없습니다.");
        }
      } catch (e) {
        console.error("예측 요청 실패:", e);
        if (!isDebounce) alert("백엔드 분석 에러가 발생했습니다.");
      } finally {
        this.isUpdating = false;
      }
    },
    renderCharts(averages, isNat = false) {
      if (!averages) return;

      const subConfigs = [
        {
          id: 'grammar',
          my: this.currentAnalysisScores.grammar,
          avg: averages.grammar,
          color: 'rgba(132, 204, 22, 0.85)',
          max: 25
        },
        {
          id: 'vocabulary',
          my: this.currentAnalysisScores.vocabulary,
          avg: averages.vocabulary,
          color: 'rgba(59, 130, 246, 0.85)',
          max: 12.5
        },
        {
          id: 'logic',
          my: this.currentAnalysisScores.logic,
          avg: averages.logic,
          color: 'rgba(249, 115, 22, 0.85)',
          max: 20
        },
        {
          id: 'reading',
          my: this.currentAnalysisScores.reading,
          avg: averages.reading,
          color: 'rgba(234, 179, 8, 0.85)',
          max: 50
        }
      ];

      if (isNat && averages.math !== undefined) {
        subConfigs.push({
          id: 'math',
          my: this.currentAnalysisScores.math,
          avg: averages.math,
          color: 'rgba(147, 51, 234, 0.85)',
          max: 100
        });
      }

      subConfigs.forEach(cfg => {
        const el = document.getElementById(`${cfg.id}Chart`);
        if (!el) return;
        const ctx = el.getContext('2d');
        if (!ctx) return;

        if (this.chartInstances[cfg.id]) {
          this.chartInstances[cfg.id].destroy();
          this.chartInstances[cfg.id] = null;
        }

        this.chartInstances[cfg.id] = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: ['내 성적', '전체 평균'],
            datasets: [{
              data: [cfg.my, cfg.avg],
              backgroundColor: [cfg.color, '#e2e8f0'],
              borderRadius: 6,
              barThickness: 18
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {duration: 350},
            plugins: {legend: {display: false}},
            scales: {
              x: {grid: {display: false}, ticks: {font: {size: 11, weight: '600'}, color: '#64748b'}},
              y: {max: cfg.max, grid: {display: false}, ticks: {display: false}}
            }
          }
        });
      });

      this.renderTimelineChart();
    },
    renderTimelineChart() {
      if (!this.result) return;
      const tlEl = document.getElementById('timelineChart');
      if (!tlEl) return;
      const tlCtx = tlEl.getContext('2d');
      if (!tlCtx) return;

      if (this.chartInstances['timeline']) {
        this.chartInstances['timeline'].destroy();
        this.chartInstances['timeline'] = null;
      }

      const isMath = (this.timelineMode === 'math');
      const timelineData = isMath ? (this.result.math_timeline_stats || {}) : (this.result.timeline_stats || {});
      const myTimelineData = isMath ? (this.result.my_math_timeline_stats || {}) : (this.result.my_timeline_stats || {});

      const labels = Object.keys(timelineData);
      const cleanNum = s => String(s).replace(/[^0-9]/g, '');
      const normMy = {};
      Object.keys(myTimelineData).forEach(k => {
        normMy[cleanNum(k)] = myTimelineData[k];
      });
      const myLineData = labels.map(l => normMy[cleanNum(l)] ?? null);

      const lineColor = isMath ? '#9333ea' : '#2563eb';
      const lineBg = isMath ? 'rgba(147, 51, 234, 0.06)' : 'rgba(37, 99, 235, 0.05)';
      const seniorLabel = isMath ? '매칭된 학생들 평균 수학' : '매칭된 학생들 평균 영어';
      const myLabel = isMath ? '나의 수학 추이' : '나의 영어 추이';

      this.chartInstances['timeline'] = new Chart(tlCtx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            {
              label: seniorLabel,
              data: Object.values(timelineData),
              borderColor: '#ec4899',
              borderWidth: 3,
              pointBackgroundColor: '#ffffff',
              pointBorderColor: '#ec4899',
              pointBorderWidth: 2,
              pointRadius: 4,
              fill: false,
              tension: 0.35
            },
            {
              label: myLabel,
              data: myLineData,
              spanGaps: true,
              borderColor: lineColor,
              backgroundColor: lineBg,
              fill: true,
              borderWidth: 3.5,
              pointBackgroundColor: '#ffffff',
              pointBorderColor: lineColor,
              pointBorderWidth: 2.5,
              pointRadius: 5,
              tension: 0.35
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {duration: 350},
          plugins: {
            legend: {position: 'top', labels: {boxWidth: 12, font: {size: 12, weight: '600'}}}
          },
          scales: {
            x: {grid: {display: false}, ticks: {font: {size: 11, weight: '600'}, color: '#64748b'}},
            y: {grid: {color: 'rgba(226, 232, 240, 0.6)'}, ticks: {color: '#64748b'}}
          }
        }
      });
    }
  }
};
</script>

<style scoped src="./styles/App.css"></style>
<style src="./styles/App.global.css"></style>

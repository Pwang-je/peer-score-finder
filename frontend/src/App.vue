<template>
  <div class="dashboard-root">
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
            <h3>📂 성적 엑셀/CSV 사전 검증 및 적재</h3>
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
                <span class="file-icon">📄</span>
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
              <div class="alert-title">
                <span>⚠️ 동명이인 충돌 {{ validationReport.duplicate_count }}건 감지</span>
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
              <div class="alert-title">
                <span>ℹ️ 계열(department) 미기재 {{ validationReport.issues.missing_department }}건 발견</span>
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
                 class="alert-block success">
              ✅ 데이터 충돌이나 누락 없이 완벽합니다. 즉시 적재 가능합니다.
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
              <select v-model="form.student_name" @change="loadStudentScore" class="modern-select">
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

        <!-- 🌟 [신규] 취약/강점 파트 자동 진단 배지 바 -->
        <div v-if="result.diagnostic_tags && result.diagnostic_tags.length" class="diagnostic-banner">
          <div class="diag-label">
            <span class="diag-icon">🎯</span>
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
  </div>
</template>

<script>
import axios from 'axios';
import {Chart, registerables} from 'chart.js';

Chart.register(...registerables);

// 백엔드 URL 기본 상수로 선언 (로컬 테스트 시 http://127.0.0.1:8000 으로 변경 가능)
const API_BASE_URL = 'https://peer-score-finder.onrender.com';

export default {
  data() {
    return {
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
      chartInstances: {}
    };
  },
  computed: {
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

<style scoped>
/* ========================================================
   🌐 전역 기본 레이아웃 & 폰트
   ======================================================== */
.dashboard-root {
  min-height: 100vh;
  background-color: #f8fafc;
  color: #0f172a;
  font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Inter", sans-serif;
  padding: 40px 24px;
}

.dashboard-body {
  max-width: 1140px;
  margin: 0 auto;
}

.app-header {
  text-align: center;
  margin-bottom: 36px;
}

.brand-badge {
  display: inline-block;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  background: #e0e7ff;
  color: #4338ca;
  border-radius: 9999px;
  margin-bottom: 10px;
}

.main-title {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #0f172a;
  margin: 0 0 8px;
}

.main-desc {
  font-size: 14.5px;
  color: #64748b;
  margin: 0;
}

/* 관리자 업로드 버튼 상단 바 */
.admin-action-row {
  display: flex;
  justify-content: flex-end;
  max-width: 1140px;
  margin: 0 auto 16px;
}

.admin-upload-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  color: #334155;
  font-size: 12.5px;
  font-weight: 600;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.admin-upload-btn:hover {
  background: #f8fafc;
  border-color: #2563eb;
  color: #2563eb;
}

/* 계열 태그 및 수동 토글 버튼 */
.panel-tag-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.panel-tag {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.05em;
}

.track-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
}

.track-badge.natural {
  background: #f3e8ff;
  color: #7e22ce;
  border: 1px solid #e9d5ff;
}

.track-badge.human {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #dbeafe;
}

.track-toggle-group {
  display: flex;
  background: #f1f5f9;
  border-radius: 6px;
  padding: 2px;
}

.toggle-btn {
  background: none;
  border: none;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.toggle-btn.active {
  background: #ffffff;
  color: #0f172a;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

/* ========================================================
   1. 상시 노출 알고리즘 가이드 카드
   ======================================================== */
.methodology-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.methodology-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
}

.icon-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #eff6ff;
  border-radius: 8px;
  border: 1px solid #dbeafe;
}

.icon-chip svg {
  width: 16px;
  height: 16px;
  stroke: #2563eb;
}

.methodology-header h3 {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  color: #1e293b;
}

.methodology-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.method-step {
  display: flex;
  gap: 12px;
  padding: 14px;
  background: #f8fafc;
  border-radius: 12px;
}

.step-num {
  font-size: 13px;
  font-weight: 800;
  font-family: monospace;
  color: #2563eb;
}

.step-body strong {
  display: block;
  font-size: 13px;
  color: #1e293b;
  margin-bottom: 4px;
}

.step-body p {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin: 0;
}

/* ========================================================
   2. 컨트롤 패널 (MODE 01 / MODE 02)
   ======================================================== */
.control-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-bottom: 20px;
  max-width: 1140px;
  width: 100%;
  box-sizing: border-box;
}

.glass-panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  position: relative;
  min-width: 0;
  box-sizing: border-box;
}

.panel-heading {
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 18px;
  color: #0f172a;
}

.form-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.input-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
  min-width: 0;
}

.input-wrap label {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.modern-input, .modern-select {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  height: 42px;
  padding: 0 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13.5px;
  background: #ffffff;
  color: #0f172a;
  outline: none;
  transition: border-color 0.15s ease;
}

.modern-input:focus, .modern-select:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.stat-summary-box {
  background: #f8fafc;
  border-radius: 10px;
  padding: 12px;
  border: 1px solid #e2e8f0;
}

.stat-summary-title {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
}

.stat-mini-grid {
  display: flex;
  gap: 6px;
}

.stat-pill {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 6px 2px;
}

.stat-pill.math {
  background: #fdf4ff;
  border-color: #f0abfc;
}

.stat-pill.math .v {
  color: #9333ea;
}

.stat-pill.total {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.stat-pill .k {
  font-size: 10px;
  color: #64748b;
}

.stat-pill .v {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}

.stat-pill.total .v {
  color: #2563eb;
}

/* 점수 직접 입력 그리드 */
.manual-score-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 14px;
  width: 100%;
  box-sizing: border-box;
}

.manual-score-grid.grid-natural {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.math-input {
  border-color: #d8b4fe !important;
}

.math-input:focus {
  border-color: #9333ea !important;
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1) !important;
}

.manual-total-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f1f5f9;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.total-number {
  font-size: 15px;
  font-weight: 800;
  color: #2563eb;
}

/* ========================================================
   가중치 튜닝 슬라이더 패널
   ======================================================== */
.weight-control-panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.weight-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.weight-title-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weight-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #eff6ff;
  border-radius: 8px;
}

.weight-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.weight-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.live-update-badge {
  font-size: 10.5px;
  background: #dbeafe;
  color: #1e40af;
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 700;
  animation: pulse 1s infinite alternate;
}

@keyframes pulse {
  from {
    opacity: 0.6;
  }
  to {
    opacity: 1;
  }
}

.weight-desc {
  font-size: 12px;
  color: #64748b;
  margin: 2px 0 0;
}

.reset-weight-btn {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.reset-weight-btn:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.weight-sliders-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.weight-sliders-grid.grid-five {
  grid-template-columns: repeat(5, 1fr);
}

.slider-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
}

.b-grammar-border:hover {
  border-color: #84cc16;
}

.b-vocab-border:hover {
  border-color: #3b82f6;
}

.b-logic-border:hover {
  border-color: #f97316;
}

.b-reading-border:hover {
  border-color: #eab308;
}

.b-math-border:hover {
  border-color: #9333ea;
}

.slider-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.slider-name {
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}

.slider-badge {
  font-size: 11px;
  font-family: monospace;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.b-grammar-badge {
  background: #ecfccb;
  color: #4d7c0f;
}

.b-vocab-badge {
  background: #eff6ff;
  color: #1d4ed8;
}

.b-logic-badge {
  background: #fff7ed;
  color: #c2410c;
}

.b-reading-badge {
  background: #fefce8;
  color: #a16207;
}

.b-math-badge {
  background: #f3e8ff;
  color: #7e22ce;
}

.weight-range {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
  appearance: none;
}

.weight-range::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  transition: transform 0.1s;
}

.weight-range.range-math::-webkit-slider-thumb {
  background: #9333ea;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  font-size: 9.5px;
  color: #94a3b8;
  margin-top: 4px;
}

.action-bar {
  text-align: center;
  margin: 24px 0 36px;
}

.primary-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 14px 28px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
  transition: transform 0.15s, background-color 0.15s;
}

.primary-btn:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
}

/* ========================================================
   3. 결과 리포트 섹션 & 차트 레이아웃
   ======================================================== */
.section-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
  color: #94a3b8;
  letter-spacing: 0.12em;
  margin-bottom: 24px;
}

.charts-section {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 20px;
  margin-bottom: 32px;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.mini-charts-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
  min-width: 0;
}

.mini-charts-row.row-five {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.chart-tile, .main-timeline-tile {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  min-width: 0;
  box-sizing: border-box;
  overflow: hidden;
}

.mini-charts-row.row-five .math-tile {
  grid-column: span 2;
  border-color: #f0abfc;
}

.tile-header {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  margin-bottom: 12px;
}

.timeline-header-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.timeline-header-wrap .tile-header {
  margin-bottom: 0;
}

.timeline-tab-group {
  display: flex;
  background: #f1f5f9;
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.tab-btn {
  background: none;
  border: none;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-btn.active {
  background: #ffffff;
  color: #0f172a;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.chart-canvas-box {
  position: relative;
  width: 100%;
  height: 110px;
  min-width: 0;
}

.timeline-canvas-box {
  position: relative;
  width: 100%;
  height: 260px;
  min-width: 0;
}

.chart-canvas-box canvas,
.timeline-canvas-box canvas {
  width: 100% !important;
  max-width: 100% !important;
}

.sub-heading {
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 14px;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sub-heading-pill {
  font-size: 11.5px;
  font-weight: 600;
  color: #475569;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 9999px;
}

/* ========================================================
   TOP 10 대학 카드 & 선배 2줄 프로필 스타일
   ======================================================== */
.univ-card-flow {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}

.univ-modern-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.u-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.u-name {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.u-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  background: #eff6ff;
  color: #2563eb;
  border-radius: 6px;
}

.major-pill-group {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f1f5f9;
}

.m-title-bar {
  display: flex;
  justify-content: space-between;
  font-size: 12.5px;
  color: #334155;
  margin-bottom: 8px;
}

.m-title {
  font-weight: 700;
}

.m-count {
  color: #64748b;
  font-size: 11.5px;
}

.senior-block {
  padding: 8px 0;
  border-bottom: 1px dashed #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.senior-block:last-child {
  border-bottom: none;
}

.senior-line-top {
  display: flex;
  align-items: center;
  gap: 6px;
}

.senior-line-sub {
  display: flex;
  align-items: center;
  gap: 5px;
  padding-left: 2px;
}

.badge-meta {
  font-size: 11.5px;
  color: #475569;
  font-family: monospace;
  font-weight: 700;
}

.badge-score {
  font-size: 11px;
  font-family: monospace;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}

.b-grammar {
  background: #ecfccb;
  color: #4d7c0f;
}

.b-vocab {
  background: #eff6ff;
  color: #1d4ed8;
}

.b-logic {
  background: #fff7ed;
  color: #c2410c;
}

.b-reading {
  background: #fefce8;
  color: #a16207;
}

.b-total {
  background: #e0e7ff;
  color: #3730a3;
  font-weight: 800;
}

.b-math {
  background: #f3e8ff;
  color: #7e22ce;
  font-weight: 800;
}

/* ========================================================
   모달 팝업 및 사전 검증(Dry-run) 리포트 스타일
   ======================================================== */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 16px;
}

.modal-card {
  background: #ffffff;
  border-radius: 16px;
  max-width: 520px;
  width: 100%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 700;
  margin: 0;
  color: #0f172a;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #94a3b8;
  cursor: pointer;
}

.modal-body {
  padding: 20px 24px;
}

.modal-guide {
  font-size: 12.5px;
  color: #475569;
  line-height: 1.6;
  background: #f8fafc;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  margin: 0 0 16px;
}

.modal-guide code {
  background: #e2e8f0;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 11px;
}

.file-drop-zone {
  position: relative;
  margin-bottom: 16px;
}

.file-input-hidden {
  display: none;
}

.file-drop-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 24px 16px;
  cursor: pointer;
  background: #ffffff;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.file-drop-label:hover {
  border-color: #2563eb;
  background: #eff6ff;
}

.file-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.file-txt {
  font-size: 13px;
  color: #64748b;
  text-align: center;
}

.file-txt.selected {
  color: #2563eb;
  font-weight: 700;
}

/* 검증 리포트 전용 스타일 */
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  margin-bottom: 14px;
  border-bottom: 1px solid #f1f5f9;
}

.report-filename {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.report-total {
  font-size: 12.5px;
  color: #64748b;
}

.alert-block {
  padding: 12px 14px;
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 12.5px;
}

.alert-block.warning {
  background: #fffbeb;
  border: 1px solid #fde68a;
  color: #92400e;
}

.alert-block.info {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
}

.alert-block.success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  font-weight: 600;
}

.alert-title {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 4px;
}

.alert-desc {
  margin: 0 0 8px;
  line-height: 1.4;
}

.dup-scroll-list {
  max-height: 110px;
  overflow-y: auto;
  background: #ffffff;
  border: 1px solid #fef3c7;
  border-radius: 6px;
  padding: 6px 10px;
  margin-bottom: 10px;
}

.dup-item {
  font-size: 11.5px;
  padding: 3px 0;
  border-bottom: 1px dashed #fef3c7;
  color: #78350f;
}

.dup-item:last-child {
  border-bottom: none;
}

.custom-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  cursor: pointer;
  font-weight: 600;
}

.custom-checkbox input[type="checkbox"] {
  width: 15px;
  height: 15px;
  cursor: pointer;
}

.custom-checkbox code {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 4px;
  border-radius: 4px;
  font-family: monospace;
}

.upload-msg-box {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 12.5px;
  line-height: 1.4;
}

.upload-msg-box.info {
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

.upload-msg-box.success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.upload-msg-box.error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.cancel-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
}

.confirm-btn {
  background: #2563eb;
  border: none;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
  cursor: pointer;
}

.confirm-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* ========================================================
   📱 모바일 & 태블릿 완벽 대응 통합 미디어 쿼리 (768px 이하)
   ======================================================== */
@media (max-width: 768px) {
  .dashboard-root {
    padding: 20px 12px;
    width: 100%;
    max-width: 100vw;
    box-sizing: border-box;
    overflow-x: hidden;
  }

  .dashboard-body {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .main-title {
    font-size: 24px;
  }

  .main-desc {
    font-size: 13px;
    line-height: 1.5;
  }

  .methodology-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .method-step {
    padding: 12px;
  }

  .control-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    width: 100%;
  }

  .glass-panel {
    padding: 18px 14px;
    min-width: 0;
  }

  .manual-score-grid,
  .manual-score-grid.grid-natural {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    gap: 10px;
    width: 100%;
  }

  .weight-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .reset-weight-btn {
    width: 100%;
    padding: 8px 0;
    text-align: center;
  }

  .weight-sliders-grid,
  .weight-sliders-grid.grid-five {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    width: 100%;
  }

  .slider-card {
    padding: 10px 12px;
    min-width: 0;
  }

  .action-bar {
    margin: 20px 0 28px;
  }

  .primary-btn {
    width: 100%;
    justify-content: center;
    padding: 15px 0;
    font-size: 16px;
  }

  .results-container {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .charts-section {
    grid-template-columns: 1fr;
    gap: 16px;
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }

  .mini-charts-row,
  .mini-charts-row.row-five {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    width: 100%;
    min-width: 0;
  }

  .mini-charts-row.row-five .math-tile {
    grid-column: span 2;
  }

  .chart-tile {
    padding: 12px 10px;
    min-width: 0;
    overflow: hidden;
  }

  .tile-header {
    font-size: 12px;
    margin-bottom: 8px;
    word-break: keep-all;
  }

  .chart-canvas-box {
    position: relative;
    width: 100% !important;
    height: 95px !important;
    min-width: 0;
  }

  .main-timeline-tile {
    padding: 14px 10px;
    width: 100%;
    min-width: 0;
    overflow: hidden;
  }

  .timeline-canvas-box {
    position: relative;
    width: 100% !important;
    height: 210px !important;
    min-width: 0;
  }

  .chart-canvas-box canvas,
  .timeline-canvas-box canvas {
    width: 100% !important;
    max-width: 100% !important;
  }

  .univ-card-flow {
    grid-template-columns: 1fr;
    gap: 12px;
    width: 100%;
  }
}

/* ========================================================
   1. 합격 선배 대비 영역 진단 배너 (하단 카드 고유색 적용)
   ======================================================== */
.diagnostic-banner {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 18px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.diag-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  color: #1e293b;
  font-weight: 700;
}

.diag-tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.diag-tag {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 9999px;
  letter-spacing: -0.01em;
}

/* 문법 고유색: 연두 */
.diag-tag.grammar {
  background: #ecfccb !important;
  color: #4d7c0f !important;
  border: 1px solid #d9f99d !important;
}

/* 어휘 고유색: 파랑 */
.diag-tag.vocab {
  background: #eff6ff !important;
  color: #1d4ed8 !important;
  border: 1px solid #bfdbfe !important;
}

/* 논리 고유색: 주황 */
.diag-tag.logic {
  background: #fff7ed !important;
  color: #c2410c !important;
  border: 1px solid #fed7aa !important;
}

/* 독해 고유색: 노랑/골드 */
.diag-tag.reading {
  background: #fefce8 !important;
  color: #a16207 !important;
  border: 1px solid #fef08a !important;
}

/* 수학 고유색: 보라 */
.diag-tag.math {
  background: #f3e8ff !important;
  color: #7e22ce !important;
  border: 1px solid #e9d5ff !important;
}

/* 균형형: 그레이 */
.diag-tag.balanced {
  background: #f8fafc !important;
  color: #475569 !important;
  border: 1px solid #cbd5e1 !important;
}


/* ========================================================
   2. TOP 10 대학 카드 점수 갭 배지 (차분한 소프트 톤)
   ======================================================== */
.u-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.u-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.u-gap-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 갭 배지: 눈이 편안한 미니멀/소프트 스타일 */
.gap-badge {
  font-size: 11px;
  font-family: -apple-system, BlinkMacSystemFont, monospace;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  letter-spacing: -0.01em;
}

/* 기준점 초과(+): 자극적인 초록/원색 대신 은은한 민트-슬레이트 톤 */
.gap-badge.plus {
  background: #f1f5f9;
  color: #0f766e;
  border: 1px solid #cbd5e1;
}

/* 기준점 미달(-): 눈 아픈 빨강 대신 은은한 로즈-슬레이트 톤 */
.gap-badge.minus {
  background: #f8fafc;
  color: #b91c1c;
  border: 1px solid #e2e8f0;
}

/* 수학 점수 갭: 파랑/보라 대비를 줄이고 서체 두께와 톤다운된 보더로 구분 */
.gap-badge.math.plus {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
  font-weight: 700;
}

.gap-badge.math.minus {
  background: #f8fafc;
  color: #c2410c;
  border: 1px solid #fed7aa;
  font-weight: 700;
}
</style>
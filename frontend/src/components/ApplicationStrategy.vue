<template>
  <div class="strategy-container">
    <!-- 서버 깨어남(Cold Start) 대기 안내 배너 -->
    <div v-if="isInitialLoading" class="wakeup-banner">
      <span class="spinner"></span>
      <span>서버와 데이터베이스를 연결하고 있습니다. 첫 접속 시 최대 30~40초 정도 소요될 수 있으니 새로고침하지 말고 잠시만 기다려 주세요...</span>
    </div>

    <!-- 상단 헤더 & 모드 전환 탭 -->
    <div class="header-card">
      <div class="header-left">
        <h2>2026학년도 편입학 원서 지원 관리</h2>
        <p class="sub-desc">학교별 모집요강·학점은행제 지원자격 및 학생별 빠른 원서 담기</p>
      </div>

      <div class="header-right-actions">
        <button @click="showQuotaModal = true" class="btn-upload-quota">
          <FileSpreadsheet :size="14" :stroke-width="2" />
          <span>모집요강 엑셀 등록</span>
        </button>

        <div class="tab-controls">
          <button
            :class="['tab-btn', currentTab === 'univ' ? 'active' : '']"
            @click="currentTab = 'univ'"
          >
            <School :size="15" :stroke-width="2" />
            <span>학교별 모집요강</span>
          </button>
          <button
            :class="['tab-btn', currentTab === 'student' ? 'active' : '']"
            @click="currentTab = 'student'"
          >
            <User :size="15" :stroke-width="2" />
            <span>학생별 지원 현황</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 모집요강 엑셀 업로드 모달 -->
    <div v-if="showQuotaModal" class="modal-backdrop" @click.self="showQuotaModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3 style="display: flex; align-items: center; gap: 8px;">
            <FileSpreadsheet :size="18" :stroke-width="2" />
            <span>대학별 모집요강 엑셀 일괄 업로드</span>
          </h3>
          <button @click="showQuotaModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <p class="guide-text">
            엑셀(.xlsx) 또는 CSV 파일의 첫 번째 행에 아래 컬럼명을 맞춰서 올려주세요.<br>
            <strong>필수 컬럼:</strong> <code>대학</code>, <code>계열</code>, <code>학과명</code>, <code>일반정원</code>, <code>학사정원</code>
          </p>
          <div class="sample-table-wrap">
            <table class="sample-table">
              <thead>
                <tr><th>대학</th><th>계열</th><th>학과명</th><th>일반정원</th><th>학사정원</th></tr>
              </thead>
              <tbody>
                <tr><td>국민대학교</td><td>자연</td><td>기계공학부</td><td>20</td><td>4</td></tr>
                <tr><td>건국대학교</td><td>인문</td><td>경영학과</td><td>18</td><td>3</td></tr>
              </tbody>
            </table>
          </div>
          <input type="file" ref="quotaFileInput" accept=".xlsx, .xls, .csv" class="file-input" />
        </div>
        <div class="modal-footer">
          <button @click="showQuotaModal = false" class="btn-cancel">닫기</button>
          <button @click="uploadQuotaFile" :disabled="isUploadingQuota" class="btn-submit">
            {{ isUploadingQuota ? '업로드 중...' : 'DB에 일괄 등록' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 기출문제 성적 엑셀 일괄 업로드 모달 -->
    <div v-if="showPastExamExcelModal" class="modal-backdrop" @click.self="showPastExamExcelModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3 style="display: flex; align-items: center; gap: 8px;">
            <FileSpreadsheet :size="18" :stroke-width="2" />
            <span>기출문제 성적 엑셀 일괄 업로드</span>
          </h3>
          <button @click="showPastExamExcelModal = false" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <p class="guide-text">
            엑셀(.xlsx) 파일의 첫 행에 아래 4개 컬럼을 필수로 입력해 주세요.<br>
            <strong>필수 컬럼:</strong> <code>학생 이름</code>, <code>기출 년도</code>, <code>내 총점</code>, <code>평균</code><br>
            <strong>선택 컬럼:</strong> <code>구분</code>(영어 / 수학 / 영+수), <code>대학명</code> (미입력 시 현재 선택된 <strong>{{ formUniv || '대학' }}</strong> 자동 적용), <code>메모</code>
          </p>
          <div class="sample-table-wrap">
            <table class="sample-table">
              <thead>
                <tr>
                  <th>학생 이름</th>
                  <th>대학명</th>
                  <th>기출 년도</th>
                  <th>구분</th>
                  <th>내 총점</th>
                  <th>평균</th>
                  <th>메모</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ selectedStudent || '김도현' }}</td>
                  <td>{{ formUniv || '건국대학교' }}</td>
                  <td>2024</td>
                  <td>영어</td>
                  <td>72.5</td>
                  <td>58.0</td>
                  <td>인문 영어 기출</td>
                </tr>
                <tr>
                  <td>{{ selectedStudent || '김도현' }}</td>
                  <td>{{ formUniv || '건국대학교' }}</td>
                  <td>2024</td>
                  <td>수학</td>
                  <td>68.0</td>
                  <td>55.0</td>
                  <td>자연 수학 기출</td>
                </tr>
                <tr>
                  <td>{{ selectedStudent || '김도현' }}</td>
                  <td>{{ formUniv || '아주대학교' }}</td>
                  <td>2023</td>
                  <td>영+수</td>
                  <td>145.0</td>
                  <td>130.0</td>
                  <td>영수 통합 기출</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="template-download-row">
            <button @click="downloadPastExamTemplate" type="button" class="btn-template-dl">
              <Download :size="14" :stroke-width="2" />
              <span>양식 엑셀 파일 다운로드 (.xlsx)</span>
            </button>
          </div>
          <div class="file-upload-row">
            <label class="file-input-label">업로드할 엑셀 파일 선택</label>
            <input type="file" ref="pastExamFileInput" accept=".xlsx, .xls, .csv" class="file-input" />
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showPastExamExcelModal = false" class="btn-cancel">닫기</button>
          <button @click="uploadPastExamExcelFile" :disabled="isUploadingPastExam" class="btn-submit">
            {{ isUploadingPastExam ? '업로드 및 DB 저장 중...' : '기출점수 일괄 등록' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 🖨️ 지원 대학:학과 리스트 출력 및 PNG 저장 모달 -->
    <div
      v-if="showPrintSlipModal"
      class="modal-backdrop slip-modal-backdrop"
      @click.self="closePrintModal"
    >
      <div class="modal-box slip-modal-box">
        <div class="modal-header slip-modal-header">
          <div class="slip-modal-title-wrap">
            <span class="slip-header-icon"><Printer :size="20" :stroke-width="1.8" /></span>
            <div>
              <h3>지원 대학 · 학과 리스트 출력 및 PNG 저장</h3>
              <p class="slip-header-sub">
                서강대 ~ 서울여대 순서대로 정렬된 <strong>{{ selectedStudent }}</strong> 학생의 원서 지원표입니다.
              </p>
            </div>
          </div>
          <button @click="closePrintModal" class="close-btn">&times;</button>
        </div>

        <!-- 옵션 컨트롤 툴바 -->
        <div class="slip-modal-toolbar">
          <div class="toolbar-group">
            <label class="toolbar-label">출력 범위:</label>
            <div class="toolbar-toggle-btns">
              <button
                type="button"
                :class="['toggle-btn', { active: printViewMode === 'applied' }]"
                @click="printViewMode = 'applied'"
              >
                지원 대학만 ({{ studentApplications.length }}개교)
              </button>
              <button
                type="button"
                :class="['toggle-btn', { active: printViewMode === 'all25' }]"
                @click="printViewMode = 'all25'"
              >
                주요 대학 전체 양식 ({{ TARGET_UNIV_ORDER_LIST.length }}개교)
              </button>
            </div>
          </div>
        </div>

        <div class="modal-body slip-modal-body">
          <!-- 복사 완료 피드백 알림 -->
          <div v-if="copySlipSuccess" class="copy-success-alert">
            {{ copySlipSuccess }}
          </div>

          <!-- 실제 인쇄 및 화면에 표시되는 상담표 시트 (Canvas 및 window.print 타겟) -->
          <div class="slip-print-container">
            <div class="print-slip-sheet" id="printSlipSheet">
              <!-- 슬립 상단 헤더 -->
              <div class="slip-header">
                <div class="slip-top-line">
                  <span class="slip-category-pill">2026학년도 편입학 원서접수 상담표</span>
                  <span class="slip-today-date">출력일자: {{ todayFormattedStr }}</span>
                </div>
                <h2 class="slip-sheet-title">지원 대학 · 학과 리스트</h2>
                <div class="slip-meta-cards">
                  <div class="slip-meta-item">
                    <span class="lbl">학생 이름</span>
                    <strong class="val student">{{ selectedStudent }}</strong>
                  </div>
                  <div class="slip-meta-item">
                    <span class="lbl">지원 대학 수</span>
                    <strong class="val count">{{ studentApplications.length }}개교</strong>
                  </div>
                  <div class="slip-meta-item" v-if="studentProfile && studentProfile.pref_major_1">
                    <span class="lbl">1순위 희망</span>
                    <span class="val">{{ studentProfile.pref_major_1 }}</span>
                  </div>
                  <div class="slip-meta-item" v-if="studentProfile && studentProfile.pref_major_2">
                    <span class="lbl">2순위 희망</span>
                    <span class="val">{{ studentProfile.pref_major_2 }}</span>
                  </div>
                </div>
              </div>

              <!-- 지원 대학 : 지원 학과 리스트 테이블 -->
              <div class="slip-table-wrap">
                <table class="slip-table">
                  <thead>
                    <tr>
                      <th class="th-num">No.</th>
                      <th class="th-univ">지원 학교</th>
                      <th class="th-sep"></th>
                      <th class="th-major">지원 학과</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(row, idx) in printDisplayList"
                      :key="row.id"
                      :class="['slip-row', { 'row-empty': !row.isApplied }]"
                    >
                      <td class="td-num">{{ String(idx + 1).padStart(2, '0') }}</td>
                      <td class="td-univ">
                        <strong>{{ row.displayUniv }}</strong>
                      </td>
                      <td class="td-sep">:</td>
                      <td class="td-major">
                        <span :class="['major-name', { 'applied-txt': row.isApplied, 'unapplied-txt': !row.isApplied, 'closed-app-txt': row.is_closed }]">
                          {{ row.displayMajor }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <!-- 슬립 하단 안내 문구 -->
              <div class="slip-footer">
                <div class="slip-footer-left">
                  <span>※ 본 문서는 편입학 상담 및 원서 지원용 참고 자료입니다.</span>
                  <span>※ 접수 전 각 대학별 세부 전형일정 및 공식 모집요강을 반드시 확인하시기 바랍니다.</span>
                </div>
                <div class="slip-footer-brand">
                  ScoreFinder 원서 전략
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer slip-modal-footer">
          <div class="footer-left-info">
            <span class="info-tip" style="display: flex; align-items: center; gap: 6px;">
              <Info :size="14" :stroke-width="2" />
              <span>PNG 이미지를 저장하거나 출력하여 학생 상담 및 원서 접수 시 활용하세요.</span>
            </span>
          </div>
          <div class="footer-right-actions">
            <button @click="copyTextList" class="btn-slip-action text" title="카카오톡 전송용 텍스트 복사">
              <MessageSquare :size="13" :stroke-width="2" />
              <span>텍스트 복사</span>
            </button>
            <button @click="copySlipToClipboard" class="btn-slip-action copy" title="클립보드에 이미지 복사 (Ctrl+V)">
              <Copy :size="13" :stroke-width="2" />
              <span>이미지 복사</span>
            </button>
            <button @click="printSlip" class="btn-slip-action print" title="브라우저 인쇄">
              <Printer :size="13" :stroke-width="2" />
              <span>프린트 (인쇄)</span>
            </button>
            <button @click="downloadSlipAsPNG" class="btn-slip-action primary" title="고화질 PNG 이미지 파일로 다운로드">
              <Download :size="13" :stroke-width="2" />
              <span>PNG 이미지 저장</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- 탭 1: 학교별 모집요강 현황판 (빠른 대학 칩 + 학점은행제 지원자격) -->
    <!-- ================================================================= -->
    <div v-if="currentTab === 'univ'" class="content-section">
      <!-- 1) 빠른 대학 선택 카드 -->
      <div class="univ-picker-card">
        <div class="univ-picker-top">
          <div class="univ-search-wrap">
            <input
              v-model="univSearchKeyword"
              type="text"
              placeholder="대학명 빠른 검색 (예: 국민, 건국, 한양...)"
              class="quick-input"
            />
            <button v-if="univSearchKeyword" @click="univSearchKeyword = ''" class="input-clear-btn">✕</button>
          </div>

          <div class="dept-filters">
            <button
              :class="['filter-btn', deptFilter === 'ALL' ? 'active' : '']"
              @click="deptFilter = 'ALL'"
            >전체</button>
            <button
              :class="['filter-btn', deptFilter === '자연' ? 'active' : '']"
              @click="deptFilter = '자연'"
            >자연계열</button>
            <button
              :class="['filter-btn', deptFilter === '인문' ? 'active' : '']"
              @click="deptFilter = '인문'"
            >인문계열</button>
          </div>

          <div class="legend-box">
            <span class="legend-item"><span class="badge bac">학사</span> 학사지원</span>
            <span class="legend-item"><span class="badge gen">일반</span> 일반지원</span>
          </div>
        </div>

        <!-- 대학 칩 그리드 -->
        <div class="univ-chip-box">
          <button
            v-for="u in filteredUnivListTab1"
            :key="u"
            :class="['univ-chip', { active: selectedUniv === u }]"
            @click="selectTab1Univ(u)"
          >
            {{ u }}
          </button>
        </div>
      </div>

      <!-- 2) 학점은행제 학생 지원자격 안내/편집 박스 -->
      <div class="eligibility-card">
        <div class="eligibility-header">
          <div class="eligibility-title">
            <span class="elig-badge">학점은행제 지원자격</span>
            <strong>{{ selectedUniv }}</strong>
          </div>
          <div class="eligibility-actions">
            <button v-if="!isEditingEligibility" @click="startEditEligibility" class="btn-edit-elig">
              <Edit3 :size="13" :stroke-width="2" />
              <span>자격 수정</span>
            </button>
            <template v-else>
              <button @click="cancelEditEligibility" class="btn-cancel-sm">취소</button>
              <button @click="saveEligibility" :disabled="isSavingElig" class="btn-save-sm">
                {{ isSavingElig ? '저장 중...' : '저장' }}
              </button>
            </template>
          </div>
        </div>

        <div v-if="!isEditingEligibility" class="eligibility-body">
          <p v-if="eligibilityText" class="elig-text">{{ eligibilityText }}</p>
          <p v-else class="elig-placeholder">
            등록된 학점은행제 지원자격이 없습니다. 우측 <strong>[자격 수정]</strong> 버튼을 눌러 입력해 주세요. (예: 일반지원 학점 80 이상, 기회균등 가능, 농어촌 12년 이상)
          </p>
        </div>
        <div v-else class="eligibility-edit-box">
          <textarea
            v-model="eligibilityDraft"
            rows="2"
            placeholder="예) 일반편입: 80학점 이상 / 학사편입: 140학점 / 기회균등 지원 가능 / 농어촌 12년 이상 이수자 가능"
            class="elig-textarea"
          ></textarea>
        </div>
      </div>

      <!-- 3) 2027 모집학과 테이블 -->
      <div class="quota-section-header">
        <div class="quota-header-left">
          <strong class="quota-header-title">📋 {{ selectedUniv }} 2027 모집학과 (정원 선발 단위)</strong>
          <span class="quota-count-badge">{{ filteredDepartments.length }}개 학과</span>
        </div>
        <span class="quota-header-sub">일반 또는 학사 정원이 배정된 학과 목록입니다. (원서 지원 가능)</span>
      </div>

      <div class="table-wrapper">
        <div class="mobile-scroll-hint">← 좌우로 스크롤하여 전체 모집인원 및 지원현황을 확인하세요 →</div>
        <div v-if="isLoadingDepts" class="table-loading-overlay">
          데이터 불러오는 중...
        </div>
        <table class="quota-table">
          <thead>
            <tr>
              <th style="width: 65px;" class="text-center">계열</th>
              <th style="width: 180px;">모집단위 (학과명)</th>
              <th style="width: 75px;" class="text-center">일반 정원</th>
              <th style="width: 75px;" class="text-center">학사 정원</th>
              <th style="min-width: 220px;">지원 명단 (모의고사 성적)</th>
              <th style="width: 140px;" class="text-center">지원 인원</th>
              <th style="min-width: 260px;">지난 합격생 이력 (합격년도 / 성적)</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="dept in filteredDepartments"
              :key="dept.id"
              :class="{ 'row-highlight': dept.applicants && dept.applicants.length > 0 }"
            >
              <td class="text-center font-medium">{{ dept.dept }}</td>
              <td class="font-bold text-dark">{{ dept.major }}</td>
              <td class="text-center">{{ dept.gen > 0 ? dept.gen + '명' : '-' }}</td>
              <td class="text-center" :class="{ 'highlight-bac': dept.bac > 0 && dept.bac <= 2 }">
                {{ dept.bac > 0 ? dept.bac + '명' : '-' }}
              </td>
              <td>
                <div v-if="!dept.applicants || dept.applicants.length === 0" class="empty-applicant">
                  -
                </div>
                <div v-else class="applicant-tag-list">
                  <div
                    v-for="app in dept.applicants"
                    :key="app.app_id"
                    class="student-tag"
                  >
                    <span :class="['tag-type', app.type === '학사' ? 'tag-bac' : 'tag-gen']">
                      {{ app.type }}
                    </span>
                    <span class="tag-name">{{ app.student_name }}</span>
                    <span class="tag-score">
                      <template v-if="app.eng && app.eng !== '-'">영{{ app.eng }}</template>
                      <template v-if="app.eng && app.eng !== '-' && app.math && app.math !== '-' && Number(app.math) > 0"> / </template>
                      <template v-if="app.math && app.math !== '-' && Number(app.math) > 0">수{{ app.math }}</template>
                      <template v-if="(!app.eng || app.eng === '-') && (!app.math || app.math === '-' || Number(app.math) <= 0)">-</template>
                    </span>
                  </div>
                </div>
              </td>
              <td class="text-center">
                <div v-if="dept.applicants && dept.applicants.length > 0" class="count-summary-cell">
                  <span class="total-app-badge">총 {{ dept.applicants.length }}명</span>
                  <span class="sub-app-detail">
                    (일반 {{ getGenCount(dept) }} / 학사 {{ getBacCount(dept) }})
                  </span>
                </div>
                <span v-else class="zero-app-text">0명</span>
              </td>
              <td>
                <div v-if="!dept.past_admissions || dept.past_admissions.length === 0" class="empty-applicant">
                  -
                </div>
                <div v-else class="past-tag-list">
                  <div
                    v-for="(past, pIdx) in dept.past_admissions"
                    :key="pIdx"
                    class="past-student-tag"
                  >
                    <span class="tag-year">{{ String(past.year).slice(-2) }}'</span>
                    <span :class="['tag-type', past.type === '학사' ? 'tag-bac' : 'tag-gen']">
                      {{ past.type }}
                    </span>
                    <span class="tag-name">{{ past.student_name }}</span>
                    <span class="tag-score">
                      <template v-if="past.eng && past.eng !== '-'">영{{ past.eng }}</template>
                      <template v-if="past.eng && past.eng !== '-' && past.math && past.math !== '-' && Number(past.math) > 0"> / </template>
                      <template v-if="past.math && past.math !== '-' && Number(past.math) > 0">수{{ past.math }}</template>
                      <template v-if="(!past.eng || past.eng === '-') && (!past.math || past.math === '-' || Number(past.math) <= 0)">-</template>
                    </span>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 🏛️ [신규] 현행 미모집 / 개편 과거 학과 (과거 합격생 이력 별도 접이식 테이블) -->
      <div v-if="closedDepartments.length > 0" class="closed-depts-accordion">
        <button
          type="button"
          class="closed-depts-toggle-header"
          @click="isClosedTab1Open = !isClosedTab1Open"
        >
          <div class="toggle-left">
            <span class="icon"><Archive :size="16" :stroke-width="2" /></span>
            <span class="title">현행 미선발 / 개편 과거 학과 (과거 합격생 이력)</span>
            <span class="badge">{{ closedDepartments.length }}개 학과</span>
          </div>
          <div class="toggle-right">
            <span class="hint">{{ isClosedTab1Open ? '접기' : '과거 합격생 이력 펼치기' }}</span>
            <span class="arrow">{{ isClosedTab1Open ? '▲' : '▼' }}</span>
          </div>
        </button>

        <div v-if="isClosedTab1Open" class="closed-depts-body">
          <div class="closed-banner">
            <span class="info-icon"><Info :size="15" :stroke-width="2" /></span>
            <span>
              현행 모집요강에서 분리·통합되거나 미선발된 과거 학과들입니다.
              현행 모집단위와 분리되어 관리되며, 과거 합격생 성적 참고용으로 제공됩니다. (정원 없음 / 원서 접수 불가)
            </span>
          </div>

          <div class="table-wrapper closed-table-wrapper">
            <table class="quota-table closed-quota-table">
              <thead>
                <tr>
                  <th style="width: 65px;" class="text-center">계열</th>
                  <th style="width: 220px;">과거 모집단위 (학과명)</th>
                  <th style="width: 90px;" class="text-center">모집 상태</th>
                  <th style="min-width: 280px;">지난 합격생 이력 (합격년도 / 전형 / 성적)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="dept in closedDepartments" :key="dept.id" class="closed-row">
                  <td class="text-center font-medium">{{ dept.dept }}</td>
                  <td>
                    <strong class="closed-major-title">{{ dept.major }}</strong>
                    <span class="closed-status-pill">현행 미선발</span>
                  </td>
                  <td class="text-center text-muted">선발 없음</td>
                  <td>
                    <div v-if="!dept.past_admissions || dept.past_admissions.length === 0" class="empty-applicant">-</div>
                    <div v-else class="past-tag-list">
                      <div
                        v-for="(past, pIdx) in dept.past_admissions"
                        :key="pIdx"
                        class="past-student-tag"
                      >
                        <span class="tag-year">{{ String(past.year).slice(-2) }}'</span>
                        <span :class="['tag-type', past.type === '학사' ? 'tag-bac' : 'tag-gen']">
                          {{ past.type }}
                        </span>
                        <span class="tag-name">{{ past.student_name }}</span>
                        <span class="tag-score">
                          <template v-if="past.eng && past.eng !== '-'">영{{ past.eng }}</template>
                          <template v-if="past.eng && past.eng !== '-' && past.math && past.math !== '-' && Number(past.math) > 0"> / </template>
                          <template v-if="past.math && past.math !== '-' && Number(past.math) > 0">수{{ past.math }}</template>
                          <template v-if="(!past.eng || past.eng === '-') && (!past.math || past.math === '-' || Number(past.math) <= 0)">-</template>
                        </span>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- 탭 2: 학생별 지원 현황 및 빠른 담기 -->
    <!-- ================================================================= -->
    <div v-if="currentTab === 'student'" class="content-section">
      <div class="student-quick-bar">
        <div class="student-bar-top">
          <div class="student-nav-group">
            <select v-model="selectedStudent" @change="onSelectStudentChange" class="select-box student-select">
              <option v-for="s in (filteredStudentList.length ? filteredStudentList : studentList)" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>

          <div class="student-search-wrap">
            <input
              v-model="studentSearch"
              type="text"
              placeholder="학생 이름 빠른 검색..."
              class="quick-input"
              @keydown.enter="selectFirstMatchingStudent"
            />
            <button v-if="studentSearch" @click="studentSearch = ''" class="input-clear-btn">✕</button>
          </div>

          <span class="stat-badge count">담긴 원서: {{ studentApplications.length }}개교</span>
        </div>

        <!-- 🌟 선택된 학생 1월~10월 컴팩트 인라인 스코어보드 -->
        <div v-if="studentScoreData" class="student-score-strip">
          <div class="score-summary-col">
            <div class="summary-top">
              <span :class="['dept-badge-pill', studentScoreData.is_natural ? 'natural' : 'humanities']">
                {{ studentScoreData.is_natural ? '자연계열 (영+수)' : '인문계열 (영어)' }}
              </span>
              <span class="test-cnt-badge">응시 {{ studentScoreData.summary.test_count }}회</span>
            </div>
            <div class="summary-values">
              <div class="val-item">
                <span class="val-label">평균</span>
                <span class="val-score eng">영 {{ studentScoreData.summary.avg_eng !== null ? studentScoreData.summary.avg_eng : '-' }}</span>
                <span v-if="studentScoreData.is_natural" class="val-score math">수 {{ studentScoreData.summary.avg_math !== null ? studentScoreData.summary.avg_math : '-' }}</span>
              </div>
              <div class="val-item">
                <span class="val-label">최고</span>
                <span class="val-score max-eng">영 {{ studentScoreData.summary.max_eng !== null ? studentScoreData.summary.max_eng : '-' }}</span>
                <span v-if="studentScoreData.is_natural" class="val-score max-math">수 {{ studentScoreData.summary.max_math !== null ? studentScoreData.summary.max_math : '-' }}</span>
              </div>
            </div>
          </div>

          <div class="monthly-grid-wrapper">
            <div
              class="monthly-grid"
              :style="{ gridTemplateColumns: `repeat(${studentScoreData.monthly_scores?.length || 11}, minmax(44px, 1fr))` }"
            >
              <div
                v-for="item in studentScoreData.monthly_scores"
                :key="item.month"
                :class="['month-col', {
                  'has-score': item.eng !== null || item.math !== null,
                  'is-latest': item.month === studentScoreData.summary.latest_month
                }]"
              >
                <div class="month-header">
                  <span>{{ item.month }}월</span>
                  <span v-if="item.month === studentScoreData.summary.latest_month" class="latest-dot" title="최근 응시">●</span>
                </div>
                <div class="score-cell eng-cell" :title="`영어 ${item.eng !== null ? item.eng : '미응시'}`">
                  <span class="subj-sub">영</span>
                  <span class="score-num">{{ item.eng !== null ? item.eng : '-' }}</span>
                </div>
                <div
                  v-if="studentScoreData.is_natural"
                  class="score-cell math-cell"
                  :title="`수학 ${item.math !== null ? item.math : '미응시'}`"
                >
                  <span class="subj-sub">수</span>
                  <span class="score-num">{{ item.math !== null ? item.math : '-' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 🔍 [신규] 전체 대학 학과 통합 검색 카드 (월말평가 점수 스트립 바로 밑에 독립 배치) -->
      <div class="global-major-search-card">
        <div class="global-search-bar-row">
          <div class="global-search-input-box">
            <span class="search-input-icon"><Search :size="15" :stroke-width="2" /></span>
            <input
              v-model="globalKeyword"
              type="text"
              placeholder="전체 대학 학과 검색 (예: 기계, 컴퓨터, 경영, 전자, 간호...)"
              class="global-search-input"
              @input="onGlobalKeywordInput"
              @keydown.enter="triggerGlobalSearch"
            />
            <button
              v-if="globalKeyword"
              @click="globalKeyword = ''; globalSearchResults = [];"
              class="input-clear-btn"
            >✕</button>
          </div>

          <div class="global-dept-filters">
            <button
              type="button"
              :class="['dept-filter-btn', { active: globalDeptFilter === 'ALL' }]"
              @click="globalDeptFilter = 'ALL'; if (globalKeyword.trim()) triggerGlobalSearch();"
            >전체</button>
            <button
              type="button"
              :class="['dept-filter-btn', { active: globalDeptFilter === '자연' }]"
              @click="globalDeptFilter = '자연'; if (globalKeyword.trim()) triggerGlobalSearch();"
            >자연계열</button>
            <button
              type="button"
              :class="['dept-filter-btn', { active: globalDeptFilter === '인문' }]"
              @click="globalDeptFilter = '인문'; if (globalKeyword.trim()) triggerGlobalSearch();"
            >인문계열</button>
          </div>

          <span v-if="globalKeyword.trim() && !isSearchingGlobal" class="global-results-counter">
            검색 결과 <strong>{{ filteredGlobalMajors.length }}</strong>개
          </span>
        </div>

        <!-- 검색 결과 패널 (검색어가 입력되었을 때만 펼쳐짐) -->
        <div v-if="globalKeyword.trim()" class="global-search-results-panel">
          <div v-if="isSearchingGlobal" class="global-search-loading">
            <span class="spinner"></span>
            <span>전체 대학에서 '{{ globalKeyword }}' 학과를 검색하고 있습니다...</span>
          </div>

          <div v-else-if="filteredGlobalMajors.length === 0" class="global-search-empty">
            '{{ globalKeyword }}' 단어가 포함된 2026학년도 대학 및 학과가 없습니다.
          </div>

          <div v-else class="global-search-results-list">
            <div
              v-for="d in filteredGlobalMajors"
              :key="`global-${d.univ}-${d.id}`"
              :class="['global-result-row', { selected: isMajorApplied(d.univ, d.major) }]"
              @click="toggleApplication(d)"
            >
              <div class="result-left">
                <span class="result-univ-tag">{{ d.univ }}</span>
                <span :class="['dept-pill', d.dept === '자연' ? 'nat' : 'hum']">{{ d.dept }}</span>
                <strong class="result-major-title">{{ d.major }}</strong>
              </div>

              <div class="result-right">
                <div class="quota-tag-group">
                  <span
                    :class="['quota-pill', 'gen', { zero: !d.gen || d.gen == 0 }]"
                    :title="`일반편입 정원: ${d.gen || 0}명`"
                  >
                    일반 <strong class="num">{{ d.gen || 0 }}</strong>명
                  </span>
                  <span
                    :class="['quota-pill', 'bac', { zero: !d.bac || d.bac == 0 }]"
                    :title="`학사편입 정원: ${d.bac || 0}명`"
                  >
                    학사 <strong class="num">{{ d.bac || 0 }}</strong>명
                  </span>
                </div>

                <span
                  v-if="d.past_count && d.past_count > 0"
                  class="past-mini"
                  :title="`${d.univ} ${d.major} 과거 합격생 ${d.past_count}명`"
                >
                  합격 {{ d.past_count }}
                </span>
                <span
                  v-else
                  class="past-empty-slot"
                  aria-hidden="true"
                ></span>

                <span
                  :class="['pick-status-btn', { active: isMajorApplied(d.univ, d.major) }]"
                  :title="isMajorApplied(d.univ, d.major) ? '담김 (클릭 시 취소)' : '원서 담기'"
                >
                  {{ isMajorApplied(d.univ, d.major) ? '✓' : '+' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="fast-basket-layout">
        <!-- 좌측 패널: 대학 및 학과 탐색 및 담기 -->
        <div class="panel picker-panel">
          <div class="panel-header">
            <div class="panel-header-left">
              <h3 class="panel-title">지원 대학 · 학과 탐색 및 담기</h3>
              <span class="guide-hint">학과를 클릭하면 즉시 담기/취소됩니다 (지원한 대학 <span class="dot-legend">●</span> 표시)</span>
            </div>
          </div>

          <!-- 3. 대학 선택 UI (깔끔한 드롭다운 및 지원 대학 퀵 뱃지) -->
          <div class="univ-selector-section">
            <div class="univ-selector-row">
              <div class="univ-dropdown-wrap full-width">
                <label class="univ-select-label">탐색 대학 선택</label>
                <select
                  v-model="formUniv"
                  @change="selectFormUniv(formUniv)"
                  class="univ-modern-select"
                >
                  <option v-for="u in sortedUnivList" :key="u" :value="u">
                    {{ u }} {{ appliedUnivSet.has(u) ? '★ (지원 담김)' : '' }}
                  </option>
                </select>
              </div>
            </div>

            <!-- 지원 중인 대학 바로가기 뱃지 (있을 때만 표시) -->
            <div v-if="appliedUnivList.length > 0" class="applied-quick-bar">
              <span class="applied-bar-label">지원 담긴 대학:</span>
              <div class="applied-chips-wrap">
                <button
                  v-for="u in appliedUnivList"
                  :key="u"
                  :class="['applied-quick-chip', { active: formUniv === u }]"
                  @click="selectFormUniv(u)"
                  :title="`${u} 바로 이동`"
                >
                  <span class="dot">●</span>
                  {{ u }}
                </button>
              </div>
            </div>
          </div>

          <!-- 2 & 4. 선택된 대학의 기출문제 성적 카드 및 18~26년도 직접 입력 / 엑셀 일괄 등록 -->
          <div class="past-exam-box">
            <div class="past-exam-box-header">
              <div class="past-exam-title-group">
                <span class="past-exam-badge">기출 성적</span>
                <strong class="past-exam-univ-name">{{ formUniv }}</strong>
                <span class="past-exam-count" v-if="currentUnivPastExams.length > 0">
                  ({{ currentUnivPastExams.length }}건)
                </span>
                <!-- 한눈에 보는 기출 성적 요약 배지 -->
                <div v-if="currentUnivPastExamStats" class="past-exam-summary-chips">
                  <span class="exam-summary-chip avg" title="기출 내점수 평균">
                    평균 <strong>{{ currentUnivPastExamStats.avgMyScore }}</strong>점
                  </span>
                  <span class="exam-summary-chip latest" title="가장 최근 응시 기출 점수">
                    최근({{ String(currentUnivPastExamStats.latestYear).slice(-2) }}') <strong>{{ currentUnivPastExamStats.latestScore }}</strong>점
                  </span>
                </div>
              </div>
              <div class="past-exam-header-btns">
                <button
                  @click="showPastExamExcelModal = true"
                  class="btn-excel-upload-exam"
                  title="엑셀로 기출 성적 일괄 등록"
                >
                  <Upload :size="13" :stroke-width="2" />
                </button>
                <button
                  @click="showAddPastExamModal = !showAddPastExamModal"
                  class="btn-toggle-add-exam"
                  :title="showAddPastExamModal ? '등록 폼 닫기' : '기출 점수 직접 추가'"
                >
                  {{ showAddPastExamModal ? '입력 닫기 ✕' : '+' }}
                </button>
                <button
                  v-if="currentUnivPastExams.length > 0"
                  @click="isPastExamFolded = !isPastExamFolded"
                  class="btn-fold-exam"
                  :title="isPastExamFolded ? '기출 성적 카드 펼치기' : '기출 성적 카드 접기'"
                >
                  {{ isPastExamFolded ? '펼치기 ▼' : '접기 ▲' }}
                </button>
              </div>
            </div>

            <!-- 18~26년도 점수 직접 입력 폼 (영어 / 수학 / 영+수 구분) -->
            <div v-if="showAddPastExamModal" class="past-exam-form-card">
              <div class="exam-form-header-line">
                <span class="exam-form-title">{{ formUniv }} 기출 점수 등록 (18~26년도)</span>
                <!-- 과목 구분 토글 (영어 / 수학 / 영+수) -->
                <div class="subject-toggle-group">
                  <button
                    type="button"
                    :class="['subject-btn', { active: newPastExam.subject_type === '영어' }]"
                    @click="newPastExam.subject_type = '영어'"
                  >
                    영어만
                  </button>
                  <button
                    type="button"
                    :class="['subject-btn', { active: newPastExam.subject_type === '수학' }]"
                    @click="newPastExam.subject_type = '수학'"
                  >
                    수학만
                  </button>
                  <button
                    type="button"
                    :class="['subject-btn', { active: newPastExam.subject_type === '영+수' }]"
                    @click="newPastExam.subject_type = '영+수'"
                  >
                    영+수 (통합)
                  </button>
                </div>
              </div>

              <div class="exam-form-inputs">
                <!-- 연도 선택 -->
                <div class="exam-input-group year-group">
                  <label>기출 연도</label>
                  <select v-model.number="newPastExam.exam_year" class="exam-form-select">
                    <option v-for="y in [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018]" :key="y" :value="y">
                      {{ y }}년도 ({{ String(y).slice(-2) }}')
                    </option>
                  </select>
                </div>

                <!-- 영+수 선택 시: 영어점수, 수학점수, 총점, 평균 -->
                <template v-if="newPastExam.subject_type === '영+수'">
                  <div class="exam-input-group">
                    <label>내 영어 점수 (선택)</label>
                    <input
                      v-model.number="newPastExam.eng_score"
                      @input="onSubScoreChange"
                      type="number"
                      step="0.1"
                      placeholder="예: 70.0"
                      class="exam-form-input"
                    />
                  </div>
                  <div class="exam-input-group">
                    <label>내 수학 점수 (선택)</label>
                    <input
                      v-model.number="newPastExam.math_score"
                      @input="onSubScoreChange"
                      type="number"
                      step="0.1"
                      placeholder="예: 75.0"
                      class="exam-form-input"
                    />
                  </div>
                  <div class="exam-input-group">
                    <label>영+수 총점 (필수)</label>
                    <input
                      v-model.number="newPastExam.my_score"
                      type="number"
                      step="0.1"
                      placeholder="예: 145.0"
                      class="exam-form-input highlight"
                    />
                  </div>
                  <div class="exam-input-group">
                    <label>영+수 총점 평균 (선택)</label>
                    <input
                      v-model.number="newPastExam.avg_score"
                      type="number"
                      step="0.1"
                      placeholder="예: 125.0"
                      class="exam-form-input"
                    />
                  </div>
                </template>

                <!-- 영어만 선택 시 -->
                <template v-else-if="newPastExam.subject_type === '영어'">
                  <div class="exam-input-group">
                    <label>내 영어 총점 (필수)</label>
                    <input
                      v-model.number="newPastExam.my_score"
                      type="number"
                      step="0.1"
                      placeholder="예: 68.5"
                      class="exam-form-input"
                    />
                  </div>
                  <div class="exam-input-group">
                    <label>영어 평균 (선택)</label>
                    <input
                      v-model.number="newPastExam.avg_score"
                      type="number"
                      step="0.1"
                      placeholder="예: 55.0"
                      class="exam-form-input"
                    />
                  </div>
                </template>

                <!-- 수학만 선택 시 -->
                <template v-else-if="newPastExam.subject_type === '수학'">
                  <div class="exam-input-group">
                    <label>내 수학 총점 (필수)</label>
                    <input
                      v-model.number="newPastExam.my_score"
                      type="number"
                      step="0.1"
                      placeholder="예: 72.0"
                      class="exam-form-input"
                    />
                  </div>
                  <div class="exam-input-group">
                    <label>수학 평균 (선택)</label>
                    <input
                      v-model.number="newPastExam.avg_score"
                      type="number"
                      step="0.1"
                      placeholder="예: 60.0"
                      class="exam-form-input"
                    />
                  </div>
                </template>
              </div>

              <div class="exam-form-footer-row">
                <input
                  v-model="newPastExam.memo"
                  type="text"
                  placeholder="메모 (예: 60분 시간 재고 풀이 등 - 선택)"
                  class="exam-form-memo"
                />
                <button
                  @click="savePastExamScore"
                  :disabled="isSavingExam"
                  class="btn-submit-exam"
                >
                  {{ isSavingExam ? '저장 중...' : '기출 점수 저장' }}
                </button>
              </div>
            </div>

            <!-- 등록된 기출 점수 타일 목록 (가로형 컴팩트 카드) -->
            <div v-if="currentUnivPastExams.length > 0 && !isPastExamFolded" class="past-exam-tiles-wrapper">
              <div class="past-exam-tiles" @wheel="handleTilesWheel">
                <div
                  v-for="sc in currentUnivPastExams"
                  :key="sc.id"
                  class="past-exam-tile"
                >
                  <div class="tile-top-row">
                    <span class="exam-year-tag">{{ String(sc.exam_year).slice(-2) }}' 기출</span>
                    <span v-if="sc.univ && sc.univ.includes('(')" class="exam-session-badge">
                      {{ sc.univ.match(/\(([^)]+)\)/)?.[1] }}
                    </span>
                    <span :class="['exam-subj-badge', getSubjClass(sc.subject_type)]">
                      {{ sc.subject_type || '영어' }}
                    </span>
                    <button
                      @click="deletePastExamScore(sc.id)"
                      class="btn-del-exam-score"
                      title="기출 점수 삭제"
                    >
                      ✕
                    </button>
                  </div>

                  <div class="tile-score-row">
                    <div class="exam-score-display">
                      <strong class="val">{{ sc.my_score }}</strong>
                      <span class="unit">점</span>
                    </div>
                    <div
                      v-if="sc.score_gap !== null && sc.score_gap !== undefined"
                      :class="['exam-gap-pill', sc.score_gap >= 0 ? 'plus' : 'minus']"
                      :title="`평균 대비 ${sc.score_gap >= 0 ? '+' : ''}${sc.score_gap}점`"
                    >
                      {{ sc.score_gap >= 0 ? '+' + sc.score_gap : sc.score_gap }}점
                    </div>
                  </div>

                  <!-- 영+수 세부 점수 표시 -->
                  <div v-if="sc.subject_type === '영+수' && (sc.eng_score !== null || sc.math_score !== null)" class="subscore-breakdown">
                    영 {{ sc.eng_score ?? '-' }} · 수 {{ sc.math_score ?? '-' }}
                  </div>

                  <div class="tile-foot-row">
                    <span v-if="sc.avg_score" class="exam-avg-display" :title="`기출 평균 ${sc.avg_score}점`">
                      평균 {{ sc.avg_score }}점
                    </span>
                    <span v-else class="exam-avg-display empty">평균 미등록</span>
                    <span v-if="sc.memo" class="exam-memo-chip" :title="`메모: ${sc.memo}`" style="display: inline-flex; align-items: center; justify-content: center;">
                      <MessageSquare :size="11" :stroke-width="2" />
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else-if="!isLoadingPastExams && !isPastExamFolded" class="no-past-exam">
              <span v-if="formUniv.includes('단국') && formUniv.includes('천안')">
                단국대학교(천안)은 별도의 기출 시험이 없습니다. (기출 점수는 죽전 캠퍼스에만 해당합니다)
              </span>
              <span v-else>{{ selectedStudent ? `${selectedStudent} 학생의 ${formUniv} 기출 점수 기록이 없습니다.` : '학생을 선택하면 기출 점수가 표시됩니다.' }}</span>
            </div>
          </div>

          <!-- 🔄 학과 변경 진행 중 안내 바 -->
          <div v-if="changingAppTarget" class="change-major-guide-bar">
            <div class="guide-bar-left">
              <span class="guide-badge">🔄 학과 변경 모드</span>
              <span class="guide-text">
                <strong>[{{ changingAppTarget.univ }}]</strong> 기존 <strong>'{{ changingAppTarget.major }}'</strong>을(를) 대체할 학과를 선택하세요.
              </span>
            </div>
            <button @click="cancelChangeMajor" class="btn-cancel-change">변경 취소 ✕</button>
          </div>

          <div class="major-filter-row">
            <div class="major-search-wrap">
              <span class="search-input-icon"><Search :size="14" :stroke-width="2" /></span>
              <input
                ref="majorSearchInput"
                v-model="majorKeyword"
                type="text"
                :placeholder="`${formUniv} 학과 검색 (예: 기계, 컴, 경영...)`"
                class="major-search-input with-icon"
              />
              <button v-if="majorKeyword" @click="majorKeyword = ''" class="input-clear-btn">✕</button>
            </div>

            <div class="mini-dept-tabs">
              <button :class="['mini-tab', { active: formDeptFilter === 'ALL' }]" @click="formDeptFilter = 'ALL'">전체</button>
              <button :class="['mini-tab', { active: formDeptFilter === '자연' }]" @click="formDeptFilter = '자연'">자연</button>
              <button :class="['mini-tab', { active: formDeptFilter === '인문' }]" @click="formDeptFilter = '인문'">인문</button>
            </div>
          </div>

          <div class="form-major-section-label">
            <div class="label-left">
              <span class="label-text">📋 2026 선발 학과 (클릭 시 원서 담기)</span>
              <span class="label-badge">{{ filteredFormMajors.length }}개</span>
            </div>
            <div class="label-right-cols">
              <span class="col-head gen">일반정원</span>
              <span class="col-head bac">학사정원</span>
              <span class="col-head past">과거합격</span>
              <span class="col-head btn">담기</span>
            </div>
          </div>

          <div class="quick-major-list">
            <div
              v-for="d in filteredFormMajors"
              :key="d.id"
              :class="['major-pick-row', { selected: isMajorApplied(d.univ, d.major) }]"
              @click="toggleApplication(d)"
            >
              <div class="major-left">
                <span :class="['dept-pill', d.dept === '자연' ? 'nat' : 'hum']">{{ d.dept }}</span>
                <span class="major-title" :title="d.major">{{ d.major }}</span>
              </div>

              <div class="major-right">
                <div class="quota-tag-group">
                  <span
                    :class="['quota-pill', 'gen', { zero: !d.gen || d.gen == 0 }]"
                    :title="`일반편입 정원: ${d.gen || 0}명`"
                  >
                    일반 <strong class="num">{{ d.gen || 0 }}</strong>명
                  </span>
                  <span
                    :class="['quota-pill', 'bac', { zero: !d.bac || d.bac == 0 }]"
                    :title="`학사편입 정원: ${d.bac || 0}명`"
                  >
                    학사 <strong class="num">{{ d.bac || 0 }}</strong>명
                  </span>
                </div>
                <span
                  v-if="d.past_admissions && d.past_admissions.length > 0"
                  class="past-mini"
                  :title="getPastTooltip(d.past_admissions)"
                >
                  합격 {{ d.past_admissions.length }}
                </span>
                <span
                  v-else
                  class="past-empty-slot"
                  aria-hidden="true"
                ></span>
                <span
                  :class="['pick-status-btn', { active: isMajorApplied(d.univ, d.major) }]"
                  :title="isMajorApplied(d.univ, d.major) ? '담김 (클릭 시 취소)' : '원서 담기'"
                >
                  {{ isMajorApplied(d.univ, d.major) ? '✓' : '+' }}
                </span>
              </div>
            </div>

            <div v-if="filteredFormMajors.length === 0" class="empty-list-box">
              조건에 맞는 학과가 없습니다.
            </div>
          </div>

          <!-- 🏛️ [신규] 현행 미선발 / 개편 과거 학과 (과거 합격생 조회용 접이식 영역) -->
          <div v-if="closedFormMajors.length > 0" class="closed-form-accordion">
            <button
              type="button"
              class="closed-form-toggle-btn"
              @click="isClosedTab2Open = !isClosedTab2Open"
            >
              <div class="btn-left">
                <span class="icon"><Archive :size="16" :stroke-width="2" /></span>
                <span class="title">현행 미선발 / 개편 학과 (과거 합격생 조회)</span>
                <span class="closed-count-badge">{{ closedFormMajors.length }}개</span>
              </div>
              <div class="btn-right">
                <span class="hint">{{ isClosedTab2Open ? '접기' : '펼치기' }}</span>
                <span class="arrow">{{ isClosedTab2Open ? '▲' : '▼' }}</span>
              </div>
            </button>

            <div v-if="isClosedTab2Open" class="closed-form-content">
              <div class="closed-form-notice">
                <span style="display: inline-flex; align-items: center; gap: 6px;">
                  <Info :size="14" :stroke-width="2" />
                  <span>현행 모집요강 미선발 학과 (원서 담기 불가 · 과거 합격생 성적 참고용)</span>
                </span>
              </div>

              <div class="closed-form-list">
                <div
                  v-for="d in closedFormMajors"
                  :key="d.id"
                  class="closed-major-item"
                >
                  <div class="closed-item-main">
                    <div class="major-left">
                      <span :class="['dept-pill', d.dept === '자연' ? 'nat' : 'hum']">{{ d.dept }}</span>
                      <strong class="major-title">{{ d.major }}</strong>
                      <span class="closed-tag">미모집</span>
                    </div>

                    <!-- 🌟 과거 합격자 접고 펼 필요 없이 바로 옆에 표시 -->
                    <div class="major-mid-past">
                      <div v-if="d.past_admissions && d.past_admissions.length > 0" class="past-tag-list inline-past">
                        <div
                          v-for="(past, pIdx) in d.past_admissions"
                          :key="pIdx"
                          class="past-student-tag mini"
                        >
                          <span class="tag-year">{{ String(past.year).slice(-2) }}'</span>
                          <span :class="['tag-type', past.type === '학사' ? 'tag-bac' : 'tag-gen']">
                            {{ past.type }}
                          </span>
                          <span class="tag-name">{{ past.student_name }}</span>
                          <span class="tag-score">
                            <template v-if="past.eng && past.eng !== '-'">영{{ past.eng }}</template>
                            <template v-if="past.eng && past.eng !== '-' && past.math && past.math !== '-' && Number(past.math) > 0"> / </template>
                            <template v-if="past.math && past.math !== '-' && Number(past.math) > 0">수{{ past.math }}</template>
                            <template v-if="(!past.eng || past.eng === '-') && (!past.math || past.math === '-' || Number(past.math) <= 0)">-</template>
                          </span>
                        </div>
                      </div>
                      <span v-else class="empty-past-hint">과거 합격 이력 없음</span>
                    </div>

                    <div class="major-right">
                      <span
                        class="pick-status-btn disabled"
                        title="현행 미선발 학과이므로 원서에 담을 수 없습니다"
                        @click.stop="alertClosedDepartment"
                      >
                        담기 불가
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 우측 패널: 학생 지원 현황 & 특이사항 비고 & 성적 유사 선배 합격 진학 대학 -->
        <div class="panel list-panel">
          <div class="panel-header">
            <div class="panel-header-left">
              <h3 class="panel-title" style="display: flex; align-items: center; gap: 6px;">
                <ClipboardList :size="16" :stroke-width="2" />
                <span>{{ selectedStudent }} 학생 지원 정보</span>
              </h3>
              <span class="count-tag">총 {{ studentApplications.length }}개교</span>
            </div>
            <button
              @click="openPrintModal"
              :disabled="!selectedStudent || studentApplications.length === 0"
              class="btn-open-print-modal"
              title="지원 대학:학과 리스트를 PNG 이미지로 저장하거나 인쇄합니다"
            >
              <Printer :size="13" :stroke-width="2" />
              <span>지원표 출력 / PNG</span>
            </button>
          </div>

          <!-- 🎯 [요청 2] 가고싶은 학과 1/2순위, 기피 학과, 토익 점수, 학점(4.5) 입력 카드 -->
          <div class="student-pref-card">
            <div class="pref-card-body">
              <div class="pref-grid-row">
                <div class="pref-field-group">
                  <div class="pref-label-row">
                    <label class="pref-label">
                      <span class="rank-badge r1">1순위 학과</span>
                    </label>
                  </div>
                  <input
                    v-model="studentProfile.pref_major_1"
                    @blur="autoSaveStudentProfile"
                    placeholder=""
                    class="pref-input"
                  />
                </div>
                <div class="pref-field-group">
                  <div class="pref-label-row with-action">
                    <label class="pref-label">
                      <span class="rank-badge r2">2순위 학과</span>
                    </label>
                    <div class="pref-actions">
                      <span v-if="profileSaveMsg" class="pref-save-status">{{ profileSaveMsg }}</span>
                      <button
                        @click="saveStudentProfile"
                        :disabled="isSavingProfile"
                        class="btn-save-pref"
                      >
                        {{ isSavingProfile ? '저장 중...' : '저장' }}
                      </button>
                    </div>
                  </div>
                  <input
                    v-model="studentProfile.pref_major_2"
                    @blur="autoSaveStudentProfile"
                    placeholder=""
                    class="pref-input"
                  />
                </div>
              </div>

              <div class="pref-grid-row three-cols">
                <div class="pref-field-group">
                  <label class="pref-label">
                    <span class="rank-badge dislike">기피 학과</span>

                  </label>
                  <input
                    v-model="studentProfile.dislike_major"
                    @blur="autoSaveStudentProfile"
                    placeholder=""
                    class="pref-input dislike-input"
                  />
                </div>
                <div class="pref-field-group">
                  <label class="pref-label">
                    <span class="rank-badge spec">토익 점수</span>

                  </label>
                  <input
                    v-model="studentProfile.toeic_score"
                    @blur="autoSaveStudentProfile"
                    placeholder=""
                    class="pref-input"
                  />
                </div>
                <div class="pref-field-group">
                  <label class="pref-label">
                    <span class="rank-badge spec">학점 ( /4.5)</span>

                  </label>
                  <input
                    v-model="studentProfile.gpa_score"
                    @blur="autoSaveStudentProfile"
                    placeholder=""
                    class="pref-input"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- 📝 학생별 특이사항 및 상담 비고 카드 -->
          <div class="student-note-card">
            <div class="note-card-header">
              <div class="note-title-wrap">
                <span class="note-icon"><FileEdit :size="15" :stroke-width="2" /></span>
                <span class="note-title">{{ selectedStudent }} 특이사항 & 비고</span>
              </div>
              <div class="note-actions">
                <span v-if="noteSaveMsg" class="note-save-status">{{ noteSaveMsg }}</span>
                <button
                  @click="saveStudentNote"
                  :disabled="isSavingNote"
                  class="btn-save-note"
                >
                  {{ isSavingNote ? '저장 중...' : (savedStudentNote ? '메모 수정 저장' : '메모 저장') }}
                </button>
              </div>
            </div>
            <div class="note-card-body">
              <textarea
                v-model="studentNoteText"
                placeholder="학생 상담 메모를 입력하세요 (저장된 메모를 직접 수정하여 다시 저장할 수 있습니다)"
                rows="2"
                class="student-note-textarea"
              ></textarea>
            </div>
          </div>

          <!-- 📌 [요청 1 & 3] 저장된 메모를 비고 밑에 따로 띄움 + 메모 삭제 기능 -->
          <div class="saved-memo-card">
            <div class="saved-memo-header">
              <div class="saved-memo-title-wrap">
                <span class="saved-icon"><Pin :size="15" :stroke-width="2" /></span>
                <span class="saved-title">저장된 메모</span>
                <span v-if="savedNoteUpdatedAt" class="saved-date">({{ savedNoteUpdatedAt }} 기준)</span>
              </div>
              <div style="display: flex; gap: 6px;">
                <button
                  v-if="savedStudentNote && savedStudentNote.trim() && studentNoteText !== savedStudentNote"
                  @click="studentNoteText = savedStudentNote"
                  class="btn-reload-memo"
                  title="입력창을 기존 저장된 메모 내용으로 되돌립니다"
                >
                  원래대로
                </button>
                <button
                  v-if="savedStudentNote && savedStudentNote.trim()"
                  @click="deleteSavedNote"
                  :disabled="isDeletingNote"
                  class="btn-delete-memo"
                  title="저장된 메모 삭제"
                >
                  {{ isDeletingNote ? '삭제 중...' : '메모 삭제' }}
                </button>
              </div>
            </div>
            <div class="saved-memo-body">
              <div v-if="savedStudentNote && savedStudentNote.trim()" class="saved-memo-text">
                {{ savedStudentNote }}
              </div>
              <div v-else class="saved-memo-empty">
                저장된 메모가 없습니다. 위의 비고란에 메모를 작성하고 저장해보세요.
              </div>
            </div>
          </div>

          <!-- 🚨 2026 모집요강 미선발 학과 감지 경고 배너 -->
          <div v-if="closedApplicationsCount > 0" class="closed-apps-alert-box">
            <div class="alert-icon-col">🚨</div>
            <div class="alert-content-col">
              <div class="alert-title">
                2026 모집요강 기준 <strong>미선발 학과 {{ closedApplicationsCount }}건 감지</strong>
              </div>
              <div class="alert-desc">
                요강 발표 전 사전 담아둔 학과 중 올해 선발인원이 없습니다. <strong>[학과 변경 ➔]</strong>을 눌러 다른 학과로 변경해주세요.
              </div>
            </div>
          </div>

          <!-- 담긴 원서 목록 -->
          <div v-if="studentApplications.length > 0" class="app-cards-top-bar">
            <span class="app-cards-subtitle">담긴 원서 목록 ({{ studentApplications.length }}개교)</span>
            <button
              @click="openPrintModal"
              class="btn-print-mini-action"
              title="지원 대학:학과 리스트 PNG 저장 및 인쇄"
            >
              <Printer :size="12" :stroke-width="2" />
              <span>PNG 저장 · 인쇄</span>
            </button>
          </div>

          <!-- 담긴 원서 목록 (상향/하향 분할 및 통합형 한칸 매트릭스) -->
          <div v-if="studentApplications.length > 0" class="app-cards-top-bar">
            <span class="app-cards-subtitle">
              담긴 원서 목록 (총 {{ studentApplications.length }}개교 · 상향 {{ upwardApplications.length }}개 · 하향 {{ downwardApplications.length }}개)
            </span>
            <button
              @click="openPrintModal"
              class="btn-print-mini-action"
              title="지원 대학:학과 리스트 PNG 저장 및 인쇄"
            >
              <Printer :size="12" :stroke-width="2" />
              <span>PNG 저장 · 인쇄</span>
            </button>
          </div>

          <div v-if="studentApplications.length === 0" class="empty-list-box">
            아직 추가된 지원 대학이 없습니다.<br>좌측에서 대학과 학과를 클릭해 바로 담아보세요.
          </div>

          <div v-else class="app-matrix-container">
            <!-- 상단 열 헤더: 상향 | 하향 -->
            <div class="matrix-column-headers">
              <div
                :class="['matrix-header-col', 'upward', { 'is-drag-over': dragOverTarget === 'upward' }]"
                @dragover="onDragOver($event, 'upward')"
                @dragleave="onDragLeave($event, 'upward')"
                @drop="onDrop($event, 'upward')"
              >
                <div class="header-col-title">
                  <span class="column-mark up">▲</span>
                  <span class="header-text">상향</span>
                  <span class="column-count-chip">{{ upwardApplications.length }}</span>
                </div>
              </div>

              <div
                :class="['matrix-header-col', 'downward', { 'is-drag-over': dragOverTarget === 'downward' }]"
                @dragover="onDragOver($event, 'downward')"
                @dragleave="onDragLeave($event, 'downward')"
                @drop="onDrop($event, 'downward')"
              >
                <div class="header-col-title">
                  <span class="column-mark down">▼</span>
                  <span class="header-text">하향</span>
                  <span class="column-count-chip">{{ downwardApplications.length }}</span>
                </div>
              </div>
            </div>

            <!-- 대학 순서대로 배치되는 원서 목록 행 -->
            <div class="matrix-rows-list">
              <div
                v-for="(app, idx) in sortedStudentApplications"
                :key="app.id"
                :class="['matrix-row-item', isUnifiedUniv(app.univ) ? 'unified-row' : 'split-row']"
              >
                <!-- 1. 상향/하향 구분 없이 한 칸 전체 너비로 나오는 학교들 -->
                <!-- (서강, 성균, 한양, 중앙, 경희, 외대, 시립대, 이화여대, 홍익, 항공대, 공학대, 한성대) -->
                <template v-if="isUnifiedUniv(app.univ)">
                  <div
                    :class="['app-card', 'unified-card', {
                      'is-closed-alert': app.is_closed,
                      'is-target-changing': changingAppTarget && changingAppTarget.id === app.id
                    }]"
                  >
                    <span class="card-idx">{{ idx + 1 }}</span>

                    <div class="card-main-content" @click="jumpToFormUniv(app.univ)" title="클릭 시 좌측에서 해당 대학 열기">
                      <div class="card-top-row">
                        <span class="card-univ-title">{{ app.univ }}</span>

                        <!-- 전형 결과 뱃지 -->
                        <span v-if="app.is_enrolled" class="status-tag enrolled">최종등록</span>
                        <span v-else-if="app.final_result === '최초합'" class="status-tag pass-first">최초합</span>
                        <span v-else-if="app.final_result === '추가합'" class="status-tag pass-add">추가합</span>
                        <span v-else-if="app.final_result === '예비'" class="status-tag waitlist">예비 {{ app.waitlist_no ? app.waitlist_no + '번' : '대기' }}</span>
                        <span v-else-if="app.stage1_result === '합격'" class="status-tag pass-stage1">1차합격</span>
                        <span v-else-if="app.stage1_result === '불합격' || app.final_result === '불합격'" class="status-tag fail">불합격</span>
                        <span v-else-if="app.is_closed" class="status-tag closed">26년 미선발</span>
                        <span v-else-if="!app.is_quota_released" class="status-tag pending">요강 대기</span>
                      </div>

                      <div class="card-major-row">
                        <span class="card-major-name" :class="{ 'is-closed': app.is_closed }">{{ formatMajorDisplay(app.major) }}</span>
                        <button
                          v-if="app.is_closed"
                          @click.stop="startChangeMajor(app)"
                          class="btn-change-major-pill"
                          title="선발 중인 다른 학과로 즉시 변경"
                        >
                          학과 변경 ➔
                        </button>
                      </div>

                      <div v-if="app.is_closed || !app.is_quota_released" class="card-meta-row">
                        <span v-if="app.is_closed" class="meta-warn">2026 선발인원 없음 (0명)</span>
                        <span v-else-if="!app.is_quota_released" class="meta-pending">2026 요강 발표 대기중</span>
                      </div>
                    </div>

                    <div class="card-side-actions">
                      <button
                        type="button"
                        @click.stop="handleRemoveApplication(app.id)"
                        class="btn-card-delete"
                        title="원서 삭제"
                      >
                        <X :size="13" :stroke-width="2.2" />
                      </button>
                    </div>
                  </div>
                </template>

                <!-- 2. 상향과 하향이 구분되어야 하는 학교들 -->
                <!-- (건국, 동국, 국민, 숭실, 세종, 단국, 광운, 명지, 가천, 인하, 아주, 경기 등) -->
                <template v-else>
                  <!-- 좌측: 상향 슬롯 -->
                  <div
                    :class="['split-slot', 'up-slot', { 'has-card': app.memo !== '하향' }]"
                    @dragover="onDragOver($event, 'upward')"
                    @dragleave="onDragLeave($event, 'upward')"
                    @drop="onDrop($event, 'upward')"
                  >
                    <div
                      v-if="app.memo !== '하향'"
                      :class="['app-card', 'split-card', {
                        'is-closed-alert': app.is_closed,
                        'is-target-changing': changingAppTarget && changingAppTarget.id === app.id,
                        'is-dragging': draggedAppId === app.id
                      }]"
                      draggable="true"
                      @dragstart="onDragStart($event, app)"
                      @dragend="onDragEnd"
                    >
                      <div class="card-drag-handle" title="드래그하여 하향(우측)으로 이동">
                        <GripVertical :size="13" :stroke-width="2" />
                      </div>
                      <span class="card-idx">{{ idx + 1 }}</span>

                      <div class="card-main-content" @click="jumpToFormUniv(app.univ)" title="클릭 시 좌측에서 해당 대학 열기">
                        <div class="card-top-row">
                          <span class="card-univ-title">{{ app.univ }}</span>

                          <!-- 전형 결과 뱃지 -->
                          <span v-if="app.is_enrolled" class="status-tag enrolled">최종등록</span>
                          <span v-else-if="app.final_result === '최초합'" class="status-tag pass-first">최초합</span>
                          <span v-else-if="app.final_result === '추가합'" class="status-tag pass-add">추가합</span>
                          <span v-else-if="app.final_result === '예비'" class="status-tag waitlist">예비 {{ app.waitlist_no ? app.waitlist_no + '번' : '대기' }}</span>
                          <span v-else-if="app.stage1_result === '합격'" class="status-tag pass-stage1">1차합격</span>
                          <span v-else-if="app.stage1_result === '불합격' || app.final_result === '불합격'" class="status-tag fail">불합격</span>
                          <span v-else-if="app.is_closed" class="status-tag closed">26년 미선발</span>
                          <span v-else-if="!app.is_quota_released" class="status-tag pending">요강 대기</span>
                        </div>

                        <div class="card-major-row">
                          <span class="card-major-name" :class="{ 'is-closed': app.is_closed }">{{ formatMajorDisplay(app.major) }}</span>
                          <button
                            v-if="app.is_closed"
                            @click.stop="startChangeMajor(app)"
                            class="btn-change-major-pill"
                            title="선발 중인 다른 학과로 즉시 변경"
                          >
                            학과 변경 ➔
                          </button>
                        </div>

                        <div v-if="app.is_closed || !app.is_quota_released" class="card-meta-row">
                          <span v-if="app.is_closed" class="meta-warn">2026 선발인원 없음 (0명)</span>
                          <span v-else-if="!app.is_quota_released" class="meta-pending">2026 요강 발표 대기중</span>
                        </div>
                      </div>

                      <div class="card-side-actions">
                        <button
                          type="button"
                          @click.stop="toggleAppTier(app)"
                          class="btn-card-shift"
                          title="하향(우측)으로 이동"
                        >
                          <ArrowRight :size="13" :stroke-width="2.2" />
                        </button>
                        <button
                          type="button"
                          @click.stop="handleRemoveApplication(app.id)"
                          class="btn-card-delete"
                          title="원서 삭제"
                        >
                          <X :size="13" :stroke-width="2.2" />
                        </button>
                      </div>
                    </div>

                    <!-- 하향으로 지정되어 좌측이 빈 경우: 클릭 시 상향으로 이동 가능한 빈 슬롯 -->
                    <div
                      v-else
                      class="empty-tier-slot"
                      @click="moveAppToTier(app, 'upward')"
                      title="클릭 시 상향(좌측)으로 이동"
                    ></div>
                  </div>

                  <!-- 우측: 하향 슬롯 -->
                  <div
                    :class="['split-slot', 'down-slot', { 'has-card': app.memo === '하향' }]"
                    @dragover="onDragOver($event, 'downward')"
                    @dragleave="onDragLeave($event, 'downward')"
                    @drop="onDrop($event, 'downward')"
                  >
                    <div
                      v-if="app.memo === '하향'"
                      :class="['app-card', 'split-card', {
                        'is-closed-alert': app.is_closed,
                        'is-target-changing': changingAppTarget && changingAppTarget.id === app.id,
                        'is-dragging': draggedAppId === app.id
                      }]"
                      draggable="true"
                      @dragstart="onDragStart($event, app)"
                      @dragend="onDragEnd"
                    >
                      <div class="card-drag-handle" title="드래그하여 상향(좌측)으로 이동">
                        <GripVertical :size="13" :stroke-width="2" />
                      </div>
                      <span class="card-idx">{{ idx + 1 }}</span>

                      <div class="card-main-content" @click="jumpToFormUniv(app.univ)" title="클릭 시 좌측에서 해당 대학 열기">
                        <div class="card-top-row">
                          <span class="card-univ-title">{{ app.univ }}</span>

                          <!-- 전형 결과 뱃지 -->
                          <span v-if="app.is_enrolled" class="status-tag enrolled">최종등록</span>
                          <span v-else-if="app.final_result === '최초합'" class="status-tag pass-first">최초합</span>
                          <span v-else-if="app.final_result === '추가합'" class="status-tag pass-add">추가합</span>
                          <span v-else-if="app.final_result === '예비'" class="status-tag waitlist">예비 {{ app.waitlist_no ? app.waitlist_no + '번' : '대기' }}</span>
                          <span v-else-if="app.stage1_result === '합격'" class="status-tag pass-stage1">1차합격</span>
                          <span v-else-if="app.stage1_result === '불합격' || app.final_result === '불합격'" class="status-tag fail">불합격</span>
                          <span v-else-if="app.is_closed" class="status-tag closed">26년 미선발</span>
                          <span v-else-if="!app.is_quota_released" class="status-tag pending">요강 대기</span>
                        </div>

                        <div class="card-major-row">
                          <span class="card-major-name" :class="{ 'is-closed': app.is_closed }">{{ formatMajorDisplay(app.major) }}</span>
                          <button
                            v-if="app.is_closed"
                            @click.stop="startChangeMajor(app)"
                            class="btn-change-major-pill"
                            title="선발 중인 다른 학과로 즉시 변경"
                          >
                            학과 변경 ➔
                          </button>
                        </div>

                        <div v-if="app.is_closed || !app.is_quota_released" class="card-meta-row">
                          <span v-if="app.is_closed" class="meta-warn">2026 선발인원 없음 (0명)</span>
                          <span v-else-if="!app.is_quota_released" class="meta-pending">2026 요강 발표 대기중</span>
                        </div>
                      </div>

                      <div class="card-side-actions">
                        <button
                          type="button"
                          @click.stop="toggleAppTier(app)"
                          class="btn-card-shift"
                          title="상향(좌측)으로 이동"
                        >
                          <ArrowLeft :size="13" :stroke-width="2.2" />
                        </button>
                        <button
                          type="button"
                          @click.stop="handleRemoveApplication(app.id)"
                          class="btn-card-delete"
                          title="원서 삭제"
                        >
                          <X :size="13" :stroke-width="2.2" />
                        </button>
                      </div>
                    </div>

                    <!-- 상향으로 지정되어 우측이 빈 경우: 클릭 시 하향으로 이동 가능한 빈 슬롯 -->
                    <div
                      v-else
                      class="empty-tier-slot"
                      @click="moveAppToTier(app, 'downward')"
                      title="클릭 시 하향(우측)으로 이동"
                    ></div>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- 💡 응시한 월별 성적 기반 지난 합격생 진학 대학 추천 섹션 -->
          <div class="similar-seniors-section">
            <div class="similar-header">
              <div class="similar-title-wrap">
                <span class="similar-icon"><Sparkles :size="16" :stroke-width="2" /></span>
                <h4 class="similar-title">성적 유사 지난 합격생 진학 대학</h4>
                <span class="similar-badge">
                  {{ similarSeniorsTarget?.is_natural ? '자연계열 지난 합격생' : '인문계열 지난 합격생' }} 매칭
                </span>
              </div>
            </div>

            <div v-if="similarSeniorsTarget" class="similar-target-bar">
              <span>
                기준: <strong>{{ similarSeniorsTarget.test_count }}회</strong> 응시
                <template v-if="similarSeniorsTarget.tested_months && similarSeniorsTarget.tested_months.length">
                  ({{ similarSeniorsTarget.tested_months.join(', ') }}월 시험 기준)
                </template>
                · 평균 영 <strong>{{ similarSeniorsTarget.avg_eng }}점</strong>
                <span v-if="similarSeniorsTarget.is_natural && similarSeniorsTarget.avg_math"> / 수 <strong>{{ similarSeniorsTarget.avg_math }}점</strong></span>
              </span>
            </div>

            <div v-if="isLoadingSimilar" class="similar-loading">
              유사 성적 지난 합격생 진학 데이터를 분석 중입니다...
            </div>
            <div v-else-if="similarSeniorsList.length === 0" class="similar-empty">
              비교할 수 있는 모의고사 성적 데이터가 아직 없습니다.
            </div>
            <div v-else class="similar-cards-grid">
              <div
                v-for="(s, idx) in similarSeniorsList"
                :key="idx"
                class="similar-card"
              >
                <div class="similar-card-top">
                  <div class="senior-info-pill">
                    <span class="senior-yr">{{ s.year }}'</span>
                    <span class="senior-nm">{{ s.student_name || s.senior_name }}</span>
                    <span :class="['senior-apply-badge', s.apply_type === '학사' ? 'bac' : 'gen']">
                      {{ s.apply_type || '일반' }}
                    </span>
                  </div>
                  <span class="senior-spec">
                    {{ s.test_count }}회 응시 · 영 {{ s.avg_eng }}<span v-if="s.avg_math"> / 수 {{ s.avg_math }}</span>
                  </span>
                </div>

                <div class="similar-card-dest" @click="jumpToFormUniv(s.univ)" :title="`${s.univ} 학과 탐색하기`">
                  <span class="dest-univ">{{ s.univ }}</span>
                  <span class="dest-major">{{ s.major }}</span>
                </div>

                <div class="similar-card-action">
                  <button
                    :class="['btn-add-similar', { added: isMajorApplied(s.univ, s.major) }]"
                    @click.stop="quickApplySimilar(s.univ, s.major)"
                  >
                    {{ isMajorApplied(s.univ, s.major) ? '담김 ✓' : '+ 내 원서에 담기' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  FileSpreadsheet,
  School,
  User,
  Upload,
  Download,
  Printer,
  Info,
  MessageSquare,
  Copy,
  Edit3,
  Archive,
  Award,
  ClipboardList,
  FileEdit,
  Pin,
  Sparkles,
  GripVertical,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  X,
  Search
} from 'lucide-vue-next'

const currentTab = ref('univ')

const API_BASE = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? 'http://127.0.0.1:8000'
  : 'https://peer-score-finder.onrender.com'

// 메모리 캐시 (대학 전환 즉시 로딩용)
const deptCache = {}
const eligCache = {}

const isInitialLoading = ref(true)
const isLoadingDepts = ref(false)

// 1. 대학 목록 및 학과 현황 상태
const univList = ref([])
const univSearchKeyword = ref('')
const selectedUniv = ref('가천대학교')
const deptFilter = ref('ALL')
const departmentRows = ref([])

// 학점은행제 지원자격 상태
const eligibilityText = ref('')
const eligibilityDraft = ref('')
const isEditingEligibility = ref(false)
const isSavingElig = ref(false)

// 2. 학생 목록 및 빠른 검색 상태
const studentList = ref([])
const studentSearch = ref('')
const selectedStudent = ref('')
const studentApplications = ref([])
const studentScoreData = ref(null)
const isLoadingScore = ref(false)

// 3. 빠른 담기 패널 상태
const formUniv = ref('가천대학교')
const formMajorList = ref([])
const majorKeyword = ref('')
const formDeptFilter = ref('ALL')
const majorSearchInput = ref(null)
const isSavingApp = ref(false)

// 3-0. [신규] 전체 대학 학과 통합 검색 상태 (월말평가 점수 아래 독립 배치)
const globalKeyword = ref('')
const globalDeptFilter = ref('ALL')
const globalSearchResults = ref([])
const isSearchingGlobal = ref(false)
let globalSearchTimer = null

// 3-1. 기출문제 성적 상태
const studentPastExams = ref([])
const isLoadingPastExams = ref(false)
const showAddPastExamModal = ref(false)
const isSavingExam = ref(false)
const isPastExamFolded = ref(false)

const showPastExamExcelModal = ref(false)
const pastExamFileInput = ref(null)
const isUploadingPastExam = ref(false)

const newPastExam = ref({
  exam_year: 2024,
  subject_type: '영어', // '영어' | '수학' | '영+수'
  my_score: '',
  avg_score: '',
  eng_score: '',
  math_score: '',
  memo: ''
})

// 4. 모집요강 엑셀 업로드 모달 상태
const showQuotaModal = ref(false)
const quotaFileInput = ref(null)
const isUploadingQuota = ref(false)

// 5. 학생별 특이사항 비고 및 희망/스펙 상태
const studentNoteText = ref('')
const savedStudentNote = ref('')
const savedNoteUpdatedAt = ref('')
const isSavingNote = ref(false)
const isDeletingNote = ref(false)
const noteSaveMsg = ref('')
let noteSaveTimer = null

const studentProfile = ref({
  pref_major_1: '',
  pref_major_2: '',
  dislike_major: '',
  toeic_score: '',
  gpa_score: ''
})
const isSavingProfile = ref(false)
const profileSaveMsg = ref('')
let profileSaveTimer = null

// 6. 유사 성적 선배 합격 대학 상태
const similarSeniorsList = ref([])
const similarSeniorsTarget = ref(null)
const isLoadingSimilar = ref(false)

// 7. 지원 대학:학과 리스트 인쇄 / PNG 저장 상태
const showPrintSlipModal = ref(false)
const printViewMode = ref('applied') // 'applied' (지원한 대학만) | 'all25' (25개 전체 양식)
const copySlipSuccess = ref('')
let copySlipTimer = null

const todayFormattedStr = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, '0')}.${String(now.getDate()).padStart(2, '0')}`
})

// 목표 대학 순서 정의 (서성한 중경외시 건동홍 국숭세단 광명상가 인가경 여대 한성 항공 순)
const TARGET_UNIV_ORDER_LIST = [
  // 1. 서성한
  { name: '서강대학교', match: u => u.includes('서강') },
  { name: '성균관대학교', match: u => u.includes('성균관') },
  { name: '한양대학교', match: u => u.includes('한양') },
  // 2. 중경외시
  { name: '중앙대학교', match: u => u.includes('중앙') },
  { name: '경희대학교', match: u => u.includes('경희') },
  { name: '한국외국어대학교', match: u => u.includes('한국외') || u.includes('외국어') },
  { name: '서울시립대학교', match: u => u.includes('시립') },
  // 3. 건동홍
  { name: '건국대학교', match: u => u.includes('건국') },
  { name: '동국대학교', match: u => u.includes('동국') },
  { name: '홍익대학교', match: u => u.includes('홍익') },
  // 4. 국숭세단
  { name: '국민대학교', match: u => u.includes('국민') },
  { name: '숭실대학교', match: u => u.includes('숭실') },
  { name: '세종대학교', match: u => u.includes('세종') },
  { name: '단국대학교', match: u => u.includes('단국') },
  // 5. 광명상가
  { name: '광운대학교', match: u => u.includes('광운') },
  { name: '명지대학교', match: u => u.includes('명지') },
  { name: '상명대학교', match: u => u.includes('상명') },
  { name: '가톨릭대학교', match: u => u.includes('가톨릭') },
  // 6. 인가경 · 아주
  { name: '인하대학교', match: u => u.includes('인하') },
  { name: '인천대학교', match: u => u.includes('인천') },
  { name: '가천대학교', match: u => u.includes('가천') },
  { name: '경기대학교', match: u => u.includes('경기') },
  { name: '아주대학교', match: u => u.includes('아주') },
  // 7. 여대 라인 (이대, 숙대, 동덕여대, 덕성여대, 서울여대)
  { name: '이화여자대학교', match: u => u.includes('이화') },
  { name: '숙명여자대학교', match: u => u.includes('숙명') },
  { name: '동덕여자대학교', match: u => u.includes('동덕') },
  { name: '덕성여자대학교', match: u => u.includes('덕성') },
  { name: '서울여자대학교', match: u => u.includes('서울여') || (u.includes('서울') && u.includes('여자')) },
  // 8. 한성, 항공, 공학대
  { name: '한성대학교', match: u => u.includes('한성') },
  { name: '한국항공대학교', match: u => u.includes('항공') },
  { name: '한국공학대학교', match: u => u.includes('한국공학') || u.includes('공학대') }
]

function getUnivMeta(univName) {
  if (!univName) return { name: '', rank: 999 }
  const clean = univName.replace(/\s+/g, '')
  for (let i = 0; i < TARGET_UNIV_ORDER_LIST.length; i++) {
    const item = TARGET_UNIV_ORDER_LIST[i]
    if (item.match(clean)) {
      return { name: item.name, rank: i }
    }
  }
  return { name: univName, rank: 900 }
}

// 🌟 상향, 하향 구분 없이 한 칸(전체 너비)으로 표시하는 대학 판별
// 서강, 성균, 한양, 중앙, 경희, 외대, 시립대, 이화여대, 홍익, 항공대, 공학대, 한성대
const UNIFIED_UNIV_KEYWORDS = [
  '서강', '성균', '한양', '중앙', '경희', '외대', '외국어', '시립', '이화', '홍익', '항공', '공학', '한성'
]

function isUnifiedUniv(univName) {
  if (!univName) return false
  const clean = univName.replace(/\s+/g, '')
  return UNIFIED_UNIV_KEYWORDS.some(k => clean.includes(k))
}

// 담긴 원서 목록 정렬 (서성한 중경외시 건동홍 국숭세단 광명상가 인가경 여대 한성 항공 순)
const sortedStudentApplications = computed(() => {
  return [...studentApplications.value].sort((a, b) => {
    const metaA = getUnivMeta(a.univ)
    const metaB = getUnivMeta(b.univ)
    if (metaA.rank !== metaB.rank) return metaA.rank - metaB.rank
    return (a.univ || '').localeCompare(b.univ || '', 'ko')
  })
})

// 🌟 구분형 대학 중 상향(▲) 지원 원서
const upwardApplications = computed(() => {
  return sortedStudentApplications.value.filter(a => !isUnifiedUniv(a.univ) && a.memo !== '하향')
})

// 🌟 구분형 대학 중 하향(▼) 지원 원서
const downwardApplications = computed(() => {
  return sortedStudentApplications.value.filter(a => !isUnifiedUniv(a.univ) && a.memo === '하향')
})

// 🌟 상/하향 구분 없는 통합(전체 너비) 원서
const unifiedApplications = computed(() => {
  return sortedStudentApplications.value.filter(a => isUnifiedUniv(a.univ))
})

// 🌟 학과 이름 중 띄어쓰기가 있는 경우 첫 띄어쓰기 기준으로 줄바꿈
function formatMajorDisplay(major) {
  if (!major) return ''
  const firstSpaceIdx = major.indexOf(' ')
  if (firstSpaceIdx !== -1) {
    return major.slice(0, firstSpaceIdx) + '\n' + major.slice(firstSpaceIdx + 1).trim()
  }
  return major
}

const draggedAppId = ref(null)
const dragOverTarget = ref(null) // 'upward' | 'downward' | null

function onDragStart(event, app) {
  if (isUnifiedUniv(app.univ)) return
  draggedAppId.value = app.id
  if (event.dataTransfer) {
    event.dataTransfer.setData('text/plain', String(app.id))
    event.dataTransfer.effectAllowed = 'move'
  }
}

function onDragEnd() {
  draggedAppId.value = null
  dragOverTarget.value = null
}

function onDragOver(event, targetTier) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
  dragOverTarget.value = targetTier
}

function onDragLeave(event, targetTier) {
  if (dragOverTarget.value === targetTier) {
    dragOverTarget.value = null
  }
}

async function moveAppToTier(app, targetTier) {
  if (!app || isUnifiedUniv(app.univ)) return
  const newMemo = targetTier === 'downward' ? '하향' : '상향'
  if (app.memo === newMemo) return
  app.memo = newMemo
  try {
    await fetch(`${API_BASE}/api/applications/${app.id}/result`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ memo: newMemo })
    })
  } catch (err) {
    console.error('지원 구분(상향/하향) 저장 실패:', err)
  }
}

async function onDrop(event, targetTier) {
  event.preventDefault()
  dragOverTarget.value = null
  const appIdStr = event.dataTransfer ? event.dataTransfer.getData('text/plain') : null
  const appId = appIdStr ? Number(appIdStr) : draggedAppId.value
  draggedAppId.value = null

  if (!appId) return
  const app = studentApplications.value.find(a => a.id === appId)
  if (!app || isUnifiedUniv(app.univ)) return
  await moveAppToTier(app, targetTier)
}

async function toggleAppTier(app) {
  if (isUnifiedUniv(app.univ)) return
  const newMemo = (app.memo === '하향') ? '상향' : '하향'
  // 로컬 즉시 반영
  app.memo = newMemo
  try {
    await fetch(`${API_BASE}/api/applications/${app.id}/result`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ memo: newMemo })
    })
  } catch (err) {
    console.error('지원 구분(▲/▼) 저장 실패:', err)
  }
}

const closedApplicationsCount = computed(() => {
  return studentApplications.value.filter(a => a.is_closed).length
})

const changingAppTarget = ref(null)

function startChangeMajor(app) {
  changingAppTarget.value = app
  selectFormUniv(app.univ)
  nextTick(() => {
    if (majorSearchInput.value) {
      majorSearchInput.value.focus()
    }
  })
}

function cancelChangeMajor() {
  changingAppTarget.value = null
}

const printDisplayList = computed(() => {
  if (printViewMode.value === 'applied') {
    return sortedStudentApplications.value.map((app, idx) => {
      const meta = getUnivMeta(app.univ)
      return {
        id: app.id || idx,
        displayUniv: app.univ,
        displayMajor: app.is_closed ? `${app.major} (올해 미선발)` : app.major,
        isApplied: true,
        is_closed: app.is_closed,
        rank: meta.rank
      }
    })
  } else {
    const result = []
    const appliedList = [...studentApplications.value]
    const matchedAppIds = new Set()

    TARGET_UNIV_ORDER_LIST.forEach((spec, sIdx) => {
      const apps = appliedList.filter(a => spec.match((a.univ || '').replace(/\s+/g, '')))
      if (apps.length > 0) {
        apps.forEach(app => {
          matchedAppIds.add(app.id)
          result.push({
            id: app.id,
            displayUniv: app.univ,
            displayMajor: app.is_closed ? `${app.major} (올해 미선발)` : app.major,
            isApplied: true,
            is_closed: app.is_closed,
            rank: sIdx
          })
        })
      } else {
        result.push({
          id: `empty-${spec.name}`,
          displayUniv: spec.name,
          displayMajor: '-',
          isApplied: false,
          is_closed: false,
          rank: sIdx
        })
      }
    })

    appliedList.filter(a => !matchedAppIds.has(a.id)).forEach((app, idx) => {
      const meta = getUnivMeta(app.univ)
      result.push({
        id: app.id || `extra-${idx}`,
        displayUniv: app.univ,
        displayMajor: app.is_closed ? `${app.major} (올해 미선발)` : app.major,
        isApplied: true,
        is_closed: app.is_closed,
        rank: 900 + idx
      })
    })

    return result
  }
})

const filteredUnivListTab1 = computed(() => {
  const kw = univSearchKeyword.value.trim().toLowerCase()
  if (!kw) return univList.value
  return univList.value.filter(u => u.toLowerCase().includes(kw))
})

// 미모집/개편 과거 학과 관련 상태
const isClosedTab1Open = ref(false)
const isClosedTab2Open = ref(true)
const selectedClosedDeptId = ref(null)

function toggleClosedDetail(id) {
  selectedClosedDeptId.value = selectedClosedDeptId.value === id ? null : id
}

function alertClosedDepartment() {
  alert('해당 학과는 이번 모집요강에서 선발하지 않는 과거 학과이므로 원서에 담을 수 없습니다.')
}

// Tab 1: 현행 모집 학과만 상단 테이블에 표시
const activeDepartments = computed(() => {
  return departmentRows.value.filter(d => !d.is_closed && (deptFilter.value === 'ALL' || d.dept === deptFilter.value))
})

// Tab 1: 미모집/개편 과거 학과 (하단 접이식 테이블)
const closedDepartments = computed(() => {
  return departmentRows.value.filter(d => d.is_closed && (deptFilter.value === 'ALL' || d.dept === deptFilter.value))
})

const filteredDepartments = computed(() => {
  return activeDepartments.value
})

const filteredStudentList = computed(() => {
  const kw = studentSearch.value.trim()
  if (!kw) return studentList.value
  return studentList.value.filter(s => s.includes(kw))
})

// Tab 2: 현행 모집 학과만 탐색 및 담기 목록에 표시
const filteredFormMajors = computed(() => {
  const kw = majorKeyword.value.trim().toLowerCase()
  return formMajorList.value.filter(d => {
    if (d.is_closed) return false
    const matchDept = formDeptFilter.value === 'ALL' || d.dept === formDeptFilter.value
    const matchKw = !kw || d.major.toLowerCase().includes(kw)
    return matchDept && matchKw
  })
})

// Tab 2: 전체 대학 대상 검색 결과
const filteredGlobalMajors = computed(() => {
  return globalSearchResults.value.filter(d => {
    if (globalDeptFilter.value === 'ALL') return true
    return d.dept === globalDeptFilter.value
  })
})

function onGlobalKeywordInput() {
  if (globalSearchTimer) clearTimeout(globalSearchTimer)
  globalSearchTimer = setTimeout(() => {
    triggerGlobalSearch()
  }, 250)
}

async function triggerGlobalSearch() {
  const kw = globalKeyword.value.trim()
  if (!kw) {
    globalSearchResults.value = []
    return
  }
  isSearchingGlobal.value = true
  try {
    const res = await fetch(`${API_BASE}/api/quota/search-majors?keyword=${encodeURIComponent(kw)}&dept=${globalDeptFilter.value}`)
    if (res.ok) {
      globalSearchResults.value = await res.json()
    }
  } catch (err) {
    console.error('전체 대학 학과 검색 실패:', err)
  } finally {
    isSearchingGlobal.value = false
  }
}

// Tab 2: 미모집/개편 과거 학과 (과거 합격생 조회용 하단 접이식 목록)
const closedFormMajors = computed(() => {
  const kw = majorKeyword.value.trim().toLowerCase()
  return formMajorList.value.filter(d => {
    if (!d.is_closed) return false
    const matchDept = formDeptFilter.value === 'ALL' || d.dept === formDeptFilter.value
    const matchKw = !kw || d.major.toLowerCase().includes(kw)
    return matchDept && matchKw
  })
})

const getPastTooltip = (pastList) => {
  if (!pastList || pastList.length === 0) return '과거 합격생 데이터 없음'
  return pastList
    .map(p => {
      const yearStr = p.year ? `${String(p.year).slice(-2)}'` : ''
      const typeStr = p.type ? `[${p.type}]` : ''
      const nameStr = p.student_name || '합격생'
      const engStr = p.eng && p.eng !== '-' ? `영 ${p.eng}` : ''
      const mathStr = p.math && p.math !== '-' && Number(p.math) > 0 ? `수 ${p.math}` : ''
      const scoreStr = [engStr, mathStr].filter(Boolean).join(' / ') || '-'
      return `${yearStr} ${typeStr} ${nameStr}: ${scoreStr}`.trim()
    })
    .join('\n')
}

const appliedUnivSet = computed(() => new Set(studentApplications.value.map(a => a.univ)))

const sortedUnivList = computed(() => {
  return [...univList.value].sort((a, b) => a.localeCompare(b, 'ko'))
})

const appliedUnivList = computed(() => {
  return Array.from(appliedUnivSet.value)
})

const currentUnivPastExams = computed(() => {
  if (!formUniv.value) return []
  // 단국대학교(천안)은 기출문제가 없으므로 기출 점수를 노출하지 않음 (죽전만 노출)
  if (formUniv.value.includes('단국') && formUniv.value.includes('천안')) {
    return []
  }
  const uClean = formUniv.value.replace(/대학교|대학/g, '').split('(')[0].trim()
  return studentPastExams.value.filter(s => {
    if (s.univ && s.univ.includes('천안')) return false
    const sUniv = (s.univ || '').replace(/대학교|대학/g, '').split('(')[0].trim()
    return s.univ === formUniv.value || sUniv === uClean || formUniv.value.includes(sUniv) || s.univ.includes(uClean)
  }).sort((a, b) => b.exam_year - a.exam_year)
})

const currentUnivPastExamStats = computed(() => {
  const list = currentUnivPastExams.value
  if (!list.length) return null
  const total = list.reduce((acc, cur) => acc + (Number(cur.my_score) || 0), 0)
  const avg = (total / list.length).toFixed(1)
  const latest = list[0]
  return {
    count: list.length,
    avgMyScore: avg.endsWith('.0') ? parseInt(avg) : avg,
    latestYear: latest.exam_year,
    latestScore: latest.my_score
  }
})

function isMajorApplied(univ, major) {
  return studentApplications.value.some(a => a.univ === univ && a.major === major)
}

function getGenCount(dept) {
  if (!dept.applicants) return 0
  return dept.applicants.filter(a => a.type === '일반').length
}

function getBacCount(dept) {
  if (!dept.applicants) return 0
  return dept.applicants.filter(a => a.type === '학사').length
}

// 공통 대학 데이터 로더 (캐시 우선 사용 -> 0ms 전환)
async function getDepartmentsCached(univ, forceRefresh = false) {
  if (!forceRefresh && deptCache[univ]) {
    return deptCache[univ]
  }
  const res = await fetch(`${API_BASE}/api/quota/departments?univ=${encodeURIComponent(univ)}`)
  const data = await res.json()
  deptCache[univ] = data
  return data
}

// 학점은행제 지원자격 조회
async function loadEligibility(univ) {
  isEditingEligibility.value = false
  if (eligCache[univ] !== undefined) {
    eligibilityText.value = eligCache[univ]
    return
  }
  try {
    const res = await fetch(`${API_BASE}/api/quota/eligibility?univ=${encodeURIComponent(univ)}`)
    if (res.ok) {
      const data = await res.json()
      eligCache[univ] = data.eligibility_text || ''
      eligibilityText.value = eligCache[univ]
    }
  } catch (err) {
    eligibilityText.value = ''
  }
}

function startEditEligibility() {
  eligibilityDraft.value = eligibilityText.value
  isEditingEligibility.value = true
}

function cancelEditEligibility() {
  isEditingEligibility.value = false
}

async function saveEligibility() {
  isSavingElig.value = true
  try {
    const res = await fetch(`${API_BASE}/api/quota/eligibility`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        univ: selectedUniv.value,
        eligibility_text: eligibilityDraft.value.trim()
      })
    })
    if (res.ok) {
      eligibilityText.value = eligibilityDraft.value.trim()
      eligCache[selectedUniv.value] = eligibilityText.value
      isEditingEligibility.value = false
    }
  } catch (err) {
    alert('지원자격 저장 중 오류가 발생했습니다.')
  } finally {
    isSavingElig.value = false
  }
}

async function selectTab1Univ(univ) {
  selectedUniv.value = univ
  await Promise.all([
    fetchUnivDepartments(),
    loadEligibility(univ)
  ])
}

async function fetchStudentMonthlyScores() {
  if (!selectedStudent.value) {
    studentScoreData.value = null
    return
  }
  isLoadingScore.value = true
  try {
    const res = await fetch(`${API_BASE}/api/student-monthly-scores?student_name=${encodeURIComponent(selectedStudent.value)}`)
    const data = await res.json()
    if (data && data.status === 'success') {
      studentScoreData.value = data
    } else {
      studentScoreData.value = null
    }
  } catch (err) {
    console.error('학생 월별 성적 조회 실패:', err)
    studentScoreData.value = null
  } finally {
    isLoadingScore.value = false
  }
}

async function fetchStudentNote() {
  if (!selectedStudent.value) {
    studentNoteText.value = ''
    savedStudentNote.value = ''
    savedNoteUpdatedAt.value = ''
    studentProfile.value = {
      pref_major_1: '',
      pref_major_2: '',
      dislike_major: '',
      toeic_score: '',
      gpa_score: ''
    }
    return
  }
  try {
    const res = await fetch(`${API_BASE}/api/student-notes?student_name=${encodeURIComponent(selectedStudent.value)}`)
    const data = await res.json()
    // 💡 기존 저장된 메모를 입력창에 기본으로 불러와 바로 수정 가능하도록 설정
    studentNoteText.value = data.memo || ''
    savedStudentNote.value = data.memo || ''
    savedNoteUpdatedAt.value = data.updated_at || ''
    studentProfile.value = {
      pref_major_1: data.pref_major_1 || '',
      pref_major_2: data.pref_major_2 || '',
      dislike_major: data.dislike_major || '',
      toeic_score: data.toeic_score || '',
      gpa_score: data.gpa_score || ''
    }
  } catch (err) {
    console.error('학생 비고 및 정보 조회 실패:', err)
  }
}

async function saveStudentNote() {
  if (!selectedStudent.value || isSavingNote.value) return
  const textToSave = studentNoteText.value.trim()
  
  if (!textToSave && !savedStudentNote.value) return // 내용도 없고 저장된 것도 없으면 저장 건너뜀
  if (!textToSave && savedStudentNote.value) {
    if (!confirm('메모 내용이 비어있습니다. 기존 저장된 메모를 삭제하시겠습니까?')) return
  }

  isSavingNote.value = true
  noteSaveMsg.value = ''
  try {
    const res = await fetch(`${API_BASE}/api/student-notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        memo: textToSave,
        pref_major_1: studentProfile.value.pref_major_1,
        pref_major_2: studentProfile.value.pref_major_2,
        dislike_major: studentProfile.value.dislike_major,
        toeic_score: studentProfile.value.toeic_score,
        gpa_score: studentProfile.value.gpa_score
      })
    })
    if (res.ok) {
      savedStudentNote.value = textToSave
      // 💡 저장 후 입력창 내용을 비우지 않고 유지하여 지속적인 수정이 가능하도록 함
      studentNoteText.value = textToSave
      const now = new Date()
      savedNoteUpdatedAt.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
      noteSaveMsg.value = '저장됨 ✓'
      if (noteSaveTimer) clearTimeout(noteSaveTimer)
      noteSaveTimer = setTimeout(() => {
        noteSaveMsg.value = ''
      }, 2500)
    }
  } catch (err) {
    console.error('학생 비고 저장 실패:', err)
  } finally {
    isSavingNote.value = false
  }
}

function autoSaveStudentNote() {
  // blur 시에는 저장하지 않고 사용자가 명시적으로 '메모 저장' 버튼을 누를 때 저장
}

async function deleteSavedNote() {
  if (!selectedStudent.value || isDeletingNote.value) return
  if (!confirm(`'${selectedStudent.value}' 학생의 저장된 메모를 삭제하시겠습니까?`)) return

  isDeletingNote.value = true
  try {
    const res = await fetch(`${API_BASE}/api/student-notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        memo: '', // 빈 문자열로 메모 삭제
        pref_major_1: studentProfile.value.pref_major_1,
        pref_major_2: studentProfile.value.pref_major_2,
        dislike_major: studentProfile.value.dislike_major,
        toeic_score: studentProfile.value.toeic_score,
        gpa_score: studentProfile.value.gpa_score
      })
    })
    if (res.ok) {
      savedStudentNote.value = ''
      savedNoteUpdatedAt.value = ''
      studentNoteText.value = ''
    }
  } catch (err) {
    console.error('메모 삭제 실패:', err)
    alert('메모 삭제 중 오류가 발생했습니다.')
  } finally {
    isDeletingNote.value = false
  }
}

async function saveStudentProfile() {
  if (!selectedStudent.value || isSavingProfile.value) return
  isSavingProfile.value = true
  profileSaveMsg.value = ''
  try {
    const res = await fetch(`${API_BASE}/api/student-notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        memo: savedStudentNote.value || '', // 💡 저장된 기존 메모 유지
        pref_major_1: studentProfile.value.pref_major_1,
        pref_major_2: studentProfile.value.pref_major_2,
        dislike_major: studentProfile.value.dislike_major,
        toeic_score: studentProfile.value.toeic_score,
        gpa_score: studentProfile.value.gpa_score
      })
    })
    if (res.ok) {
      profileSaveMsg.value = '저장됨 ✓'
      if (profileSaveTimer) clearTimeout(profileSaveTimer)
      profileSaveTimer = setTimeout(() => {
        profileSaveMsg.value = ''
      }, 2500)
    }
  } catch (err) {
    console.error('학생 희망/스펙 정보 저장 실패:', err)
  } finally {
    isSavingProfile.value = false
  }
}

function autoSaveStudentProfile() {
  saveStudentProfile()
}

async function fetchSimilarSeniors() {
  if (!selectedStudent.value) {
    similarSeniorsList.value = []
    similarSeniorsTarget.value = null
    return
  }
  isLoadingSimilar.value = true
  try {
    const res = await fetch(`${API_BASE}/api/similar-senior-destinations?student_name=${encodeURIComponent(selectedStudent.value)}`)
    const data = await res.json()
    if (data && data.status === 'success') {
      similarSeniorsList.value = data.similar_seniors || []
      similarSeniorsTarget.value = data.target || null
    } else {
      similarSeniorsList.value = []
      similarSeniorsTarget.value = null
    }
  } catch (err) {
    console.error('유사 지난 합격생 조회 실패:', err)
    similarSeniorsList.value = []
    similarSeniorsTarget.value = null
  } finally {
    isLoadingSimilar.value = false
  }
}

async function quickApplySimilar(univ, major) {
  if (isSavingApp.value || !selectedStudent.value) return

  const existing = studentApplications.value.find(
    a => a.univ === univ && a.major === major
  )

  if (existing) {
    await handleRemoveApplication(existing.id)
    return
  }

  isSavingApp.value = true
  try {
    const res = await fetch(`${API_BASE}/api/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        univ: univ,
        major: major
      })
    })

    if (res.ok) {
      delete deptCache[univ]
      await fetchStudentApplications()
      if (selectedUniv.value === univ) {
        await fetchUnivDepartments(true)
      }
      if (formUniv.value === univ) {
        await fetchFormMajors(true)
      }
    }
  } catch (err) {
    console.error('원서 담기 실패:', err)
  } finally {
    isSavingApp.value = false
  }
}

async function fetchAllowedStudents() {
  try {
    const res = await fetch(`${API_BASE}/all-students-2026`)
    const data = await res.json()
    if (Array.isArray(data) && data.length > 0) {
      studentList.value = data
      selectedStudent.value = data[0]
      await Promise.all([
        fetchStudentApplications(),
        fetchStudentMonthlyScores(),
        fetchStudentNote(),
        fetchSimilarSeniors(),
        fetchStudentPastExams()
      ])
    }
  } catch (err) {
    console.error('학생 명단 로드 실패:', err)
  }
}

async function selectStudent(name) {
  if (!name) return
  changingAppTarget.value = null
  selectedStudent.value = name
  await Promise.all([
    fetchStudentApplications(),
    fetchStudentMonthlyScores(),
    fetchStudentNote(),
    fetchSimilarSeniors(),
    fetchStudentPastExams()
  ])
}

function onSelectStudentChange() {
  selectStudent(selectedStudent.value)
}

function selectFirstMatchingStudent() {
  if (filteredStudentList.value.length > 0) {
    selectStudent(filteredStudentList.value[0])
    studentSearch.value = ''
  }
}

function moveStudent(step) {
  if (!studentList.value.length) return
  const currentList = filteredStudentList.value.length > 0 ? filteredStudentList.value : studentList.value
  const idx = currentList.indexOf(selectedStudent.value)
  const nextIdx = (idx + step + currentList.length) % currentList.length
  selectStudent(currentList[nextIdx])
}

async function fetchUnivList() {
  try {
    const res = await fetch(`${API_BASE}/api/quota/univ-list`)
    const data = await res.json()
    if (data && data.length > 0) {
      univList.value = data
      if (!data.includes(selectedUniv.value)) {
        selectedUniv.value = data[0]
      }
      if (!data.includes(formUniv.value)) {
        formUniv.value = data[0]
      }
      await Promise.all([
        fetchUnivDepartments(),
        loadEligibility(selectedUniv.value),
        fetchFormMajors()
      ])
    }
  } catch (err) {
    console.error('대학 목록 조회 실패:', err)
  }
}

async function fetchUnivDepartments(force = false) {
  if (!deptCache[selectedUniv.value] || force) {
    isLoadingDepts.value = true
  }
  try {
    departmentRows.value = await getDepartmentsCached(selectedUniv.value, force)
  } catch (err) {
    console.error('학과 정원 조회 실패:', err)
  } finally {
    isLoadingDepts.value = false
  }
}

async function selectFormUniv(univ) {
  formUniv.value = univ
  majorKeyword.value = ''
  selectedClosedDeptId.value = null
  await fetchFormMajors()
  nextTick(() => {
    if (majorSearchInput.value) majorSearchInput.value.focus()
  })
}

async function jumpToFormUniv(univ) {
  if (formUniv.value !== univ) {
    await selectFormUniv(univ)
  }
}

async function fetchFormMajors(force = false) {
  try {
    formMajorList.value = await getDepartmentsCached(formUniv.value, force)
  } catch (err) {
    console.error('폼 학과 조회 실패:', err)
  }
}

async function fetchStudentApplications() {
  if (!selectedStudent.value) return
  try {
    const res = await fetch(`${API_BASE}/api/applications?student_name=${encodeURIComponent(selectedStudent.value)}`)
    studentApplications.value = await res.json()
  } catch (err) {
    console.error('학생 원서 목록 조회 실패:', err)
  }
}

async function toggleApplication(deptItem) {
  if (deptItem.is_closed) {
    alert('해당 학과는 이번 모집요강에서 선발하지 않는 과거 학과이므로 원서에 담을 수 없습니다.')
    return
  }
  if (isSavingApp.value || !selectedStudent.value) return

  // 🔄 학과 변경 모드 진행 중인 경우: 기존 원서 제거 후 새 학과로 자동 교체
  if (changingAppTarget.value) {
    const oldApp = changingAppTarget.value
    if (oldApp.univ !== deptItem.univ) {
      if (!confirm(`현재 [${oldApp.univ} - ${oldApp.major}] 학과 변경 중입니다.\n[${deptItem.univ} - ${deptItem.major}] 학과로 대체 변경하시겠습니까?`)) {
        return
      }
    }
    isSavingApp.value = true
    try {
      await fetch(`${API_BASE}/api/applications/${oldApp.id}`, { method: 'DELETE' })
      const res = await fetch(`${API_BASE}/api/applications`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_name: selectedStudent.value,
          univ: deptItem.univ,
          major: deptItem.major
        })
      })
      if (res.ok) {
        delete deptCache[oldApp.univ]
        delete deptCache[deptItem.univ]
        changingAppTarget.value = null
        await fetchStudentApplications()
        if (selectedUniv.value === deptItem.univ) await fetchUnivDepartments(true)
        if (formUniv.value === deptItem.univ) await fetchFormMajors(true)
        alert(`[${deptItem.univ}] 지원 학과가 '${oldApp.major}'에서 '${deptItem.major}'(으)로 성공적으로 변경되었습니다.`)
      }
    } catch (err) {
      console.error('학과 변경 실패:', err)
      alert('학과 변경 중 오류가 발생했습니다.')
    } finally {
      isSavingApp.value = false
    }
    return
  }

  const existing = studentApplications.value.find(
    a => a.univ === deptItem.univ && a.major === deptItem.major
  )

  if (existing) {
    await handleRemoveApplication(existing.id)
    return
  }

  isSavingApp.value = true
  try {
    const res = await fetch(`${API_BASE}/api/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        univ: deptItem.univ,
        major: deptItem.major
      })
    })

    if (res.ok) {
      delete deptCache[deptItem.univ]
      await fetchStudentApplications()
      if (selectedUniv.value === deptItem.univ) {
        await fetchUnivDepartments(true)
      }
    }
  } catch (err) {
    console.error('원서 추가 실패:', err)
  } finally {
    isSavingApp.value = false
  }
}

async function handleRemoveApplication(appId) {
  if (isSavingApp.value) return
  const targetApp = studentApplications.value.find(a => a.id === appId)
  isSavingApp.value = true
  try {
    const res = await fetch(`${API_BASE}/api/applications/${appId}`, { method: 'DELETE' })
    if (res.ok) {
      if (targetApp) delete deptCache[targetApp.univ]
      await fetchStudentApplications()
      if (targetApp && selectedUniv.value === targetApp.univ) {
        await fetchUnivDepartments(true)
      }
    }
  } catch (err) {
    console.error('원서 삭제 실패:', err)
  } finally {
    isSavingApp.value = false
  }
}

async function uploadQuotaFile() {
  const fileEl = quotaFileInput.value
  if (!fileEl || !fileEl.files || fileEl.files.length === 0) {
    alert('업로드할 엑셀 파일을 선택해 주세요.')
    return
  }

  const formData = new FormData()
  formData.append('file', fileEl.files[0])
  isUploadingQuota.value = true

  try {
    const res = await fetch(`${API_BASE}/api/quota/upload`, {
      method: 'POST',
      body: formData
    })
    const result = await res.json()
    if (res.ok) {
      alert(result.message)
      showQuotaModal.value = false
      fileEl.value = ''
      Object.keys(deptCache).forEach(k => delete deptCache[k])
      await fetchUnivList()
    } else {
      alert(result.detail || '업로드 중 오류가 발생했습니다.')
    }
  } catch (err) {
    console.error('모집요강 업로드 에러:', err)
    alert('서버 통신 중 오류가 발생했습니다.')
  } finally {
    isUploadingQuota.value = false
  }
}

// 3-2. 기출문제 성적 API 연동 함수
async function fetchStudentPastExams() {
  if (!selectedStudent.value) {
    studentPastExams.value = []
    return
  }
  isLoadingPastExams.value = true
  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams?student_name=${encodeURIComponent(selectedStudent.value)}`)
    if (res.ok) {
      const data = await res.json()
      studentPastExams.value = data.scores || []
    }
  } catch (err) {
    console.error('기출 성적 조회 실패:', err)
  } finally {
    isLoadingPastExams.value = false
  }
}

function onSubScoreChange() {
  if (newPastExam.value.subject_type === '영+수') {
    const e = parseFloat(newPastExam.value.eng_score) || 0
    const m = parseFloat(newPastExam.value.math_score) || 0
    if (newPastExam.value.eng_score !== '' || newPastExam.value.math_score !== '') {
      newPastExam.value.my_score = Math.round((e + m) * 10) / 10
    }
  }
}

function handleTilesWheel(e) {
  const el = e.currentTarget
  if (!el) return
  if (el.scrollWidth > el.clientWidth && Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
    el.scrollLeft += e.deltaY
    e.preventDefault()
  }
}

async function savePastExamScore() {
  if (!selectedStudent.value) {
    alert('학생을 먼저 선택해 주세요.')
    return
  }
  if (!formUniv.value) {
    alert('대학을 선택해 주세요.')
    return
  }

  // 영+수일 때 총점 미입력 시 영어+수학 자동 합산
  if (newPastExam.value.subject_type === '영+수') {
    if (newPastExam.value.my_score === '' && (newPastExam.value.eng_score !== '' || newPastExam.value.math_score !== '')) {
      const e = parseFloat(newPastExam.value.eng_score) || 0
      const m = parseFloat(newPastExam.value.math_score) || 0
      newPastExam.value.my_score = e + m
    }
  }

  if (newPastExam.value.my_score === '' || newPastExam.value.my_score === null || isNaN(Number(newPastExam.value.my_score))) {
    alert('내 총점을 올바르게 입력해 주세요.')
    return
  }
  isSavingExam.value = true
  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        univ: formUniv.value,
        exam_year: Number(newPastExam.value.exam_year),
        subject_type: newPastExam.value.subject_type || '영어',
        my_score: Number(newPastExam.value.my_score),
        avg_score: newPastExam.value.avg_score !== '' && newPastExam.value.avg_score !== null ? Number(newPastExam.value.avg_score) : null,
        eng_score: newPastExam.value.eng_score !== '' && newPastExam.value.eng_score !== null ? Number(newPastExam.value.eng_score) : null,
        math_score: newPastExam.value.math_score !== '' && newPastExam.value.math_score !== null ? Number(newPastExam.value.math_score) : null,
        memo: newPastExam.value.memo || ''
      })
    })
    if (res.ok) {
      await fetchStudentPastExams()
      newPastExam.value.my_score = ''
      newPastExam.value.avg_score = ''
      newPastExam.value.eng_score = ''
      newPastExam.value.math_score = ''
      newPastExam.value.memo = ''
      showAddPastExamModal.value = false
    } else {
      const errData = await res.json()
      alert('저장 실패: ' + (errData.detail || '오류가 발생했습니다.'))
    }
  } catch (err) {
    console.error('기출 점수 저장 실패:', err)
    alert('기출 점수 저장 중 오류가 발생했습니다.')
  } finally {
    isSavingExam.value = false
  }
}

async function deletePastExamScore(id) {
  if (!confirm('이 기출 점수를 삭제하시겠습니까?')) return
  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams/${id}`, { method: 'DELETE' })
    if (res.ok) {
      await fetchStudentPastExams()
    }
  } catch (err) {
    console.error('기출 점수 삭제 실패:', err)
  }
}

function downloadPastExamTemplate() {
  window.open(`${API_BASE}/api/student-past-exams/sample-template`, '_blank')
}

async function uploadPastExamExcelFile() {
  const fileEl = pastExamFileInput.value
  if (!fileEl || !fileEl.files || fileEl.files.length === 0) {
    alert('업로드할 엑셀 파일을 선택해 주세요.')
    return
  }
  const formData = new FormData()
  formData.append('file', fileEl.files[0])
  if (selectedStudent.value) {
    formData.append('default_student', selectedStudent.value)
  }
  if (formUniv.value) {
    formData.append('default_univ', formUniv.value)
  }

  isUploadingPastExam.value = true
  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams/upload-excel`, {
      method: 'POST',
      body: formData
    })
    const result = await res.json()
    if (res.ok) {
      alert(result.message)
      showPastExamExcelModal.value = false
      fileEl.value = ''
      await fetchStudentPastExams()
    } else {
      alert(result.detail || '기출 엑셀 업로드 중 오류가 발생했습니다.')
    }
  } catch (err) {
    console.error('기출 엑셀 업로드 에러:', err)
    alert('서버 통신 중 오류가 발생했습니다.')
  } finally {
    isUploadingPastExam.value = false
  }
}

function getSubjClass(subj) {
  if (subj === '수학') return 'subj-math'
  if (subj === '영+수') return 'subj-both'
  return 'subj-eng'
}

function getUnivExamSummary(univ) {
  if (!univ) return ''
  // 단국대학교(천안)은 기출점수가 없음 (죽전만 노출)
  if (univ.includes('단국') && univ.includes('천안')) {
    return ''
  }
  const uClean = univ.replace(/대학교|대학/g, '').split('(')[0].trim()
  const matches = studentPastExams.value.filter(s => {
    if (s.univ && s.univ.includes('천안')) return false
    const sUniv = (s.univ || '').replace(/대학교|대학/g, '').split('(')[0].trim()
    return s.univ === univ || sUniv === uClean || univ.includes(sUniv) || s.univ.includes(uClean)
  }).sort((a, b) => b.exam_year - a.exam_year)

  if (matches.length === 0) return ''
  return matches.map(m => {
    const yr = String(m.exam_year).slice(-2) + "'"
    const subj = m.subject_type ? `[${m.subject_type}] ` : ''
    let str = `${yr} ${subj}${m.my_score}점`
    if (m.score_gap !== null && m.score_gap !== undefined) {
      str += `(${m.score_gap >= 0 ? '+' : ''}${m.score_gap})`
    }
    return str
  }).slice(0, 2).join(' / ')
}

/* =====================================================================
   🖨️ 지원 대학:학과 상담표 인쇄 및 PNG 이미지 생성 로직
   ===================================================================== */
function openPrintModal() {
  if (!selectedStudent.value) {
    alert('학생을 먼저 선택해 주세요.')
    return
  }
  if (studentApplications.value.length === 0) {
    alert('지원 담긴 대학이 없습니다. 먼저 대학과 학과를 담아주세요.')
    return
  }
  copySlipSuccess.value = ''
  showPrintSlipModal.value = true
}

function closePrintModal() {
  showPrintSlipModal.value = false
}

function drawSlipToCanvas() {
  const items = printDisplayList.value
  if (!items || items.length === 0) return null

  const scale = 2
  const width = 640
  const rowH = 38
  const headerH = 135
  const footerH = 50
  const height = headerH + items.length * rowH + footerH

  const canvas = document.createElement('canvas')
  canvas.width = width * scale
  canvas.height = height * scale
  const ctx = canvas.getContext('2d')
  ctx.scale(scale, scale)

  // 1. 전체 배경
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)

  // 상단 로열 블루 악센트 바
  const grad = ctx.createLinearGradient(0, 0, width, 0)
  grad.addColorStop(0, '#1d4ed8')
  grad.addColorStop(1, '#3b82f6')
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, width, 6)

  // 2. 카테고리 태그 및 출력일
  ctx.fillStyle = '#eff6ff'
  if (ctx.roundRect) {
    ctx.beginPath()
    ctx.roundRect(40, 22, 130, 22, 4)
    ctx.fill()
  } else {
    ctx.fillRect(40, 22, 130, 22)
  }
  ctx.fillStyle = '#1d4ed8'
  ctx.font = 'bold 11px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText('2026 편입 지원 상담표', 48, 37)

  ctx.fillStyle = '#94a3b8'
  ctx.font = '12px Pretendard, "Malgun Gothic", sans-serif'
  ctx.textAlign = 'right'
  ctx.fillText(`출력일자: ${todayFormattedStr.value}`, width - 40, 37)
  ctx.textAlign = 'left'

  // 3. 타이틀
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 22px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText('지원 대학 · 학과 리스트', 40, 72)

  // 4. 학생 정보 메타 요약 줄
  ctx.fillStyle = '#475569'
  ctx.font = '13.5px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText('학생명: ', 40, 98)
  ctx.fillStyle = '#0f172a'
  ctx.font = 'bold 14px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText(`${selectedStudent.value} 학생`, 85, 98)

  ctx.fillStyle = '#cbd5e1'
  ctx.font = '13px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText('|', 165, 98)

  ctx.fillStyle = '#475569'
  ctx.font = '13.5px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText('지원 대학: ', 180, 98)
  ctx.fillStyle = '#2563eb'
  ctx.font = 'bold 14px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText(`총 ${studentApplications.value.length}개교`, 245, 98)

  if (studentProfile.value && studentProfile.value.pref_major_1) {
    ctx.fillStyle = '#cbd5e1'
    ctx.font = '13px Pretendard, "Malgun Gothic", sans-serif'
    ctx.fillText('|', 320, 98)
    ctx.fillStyle = '#475569'
    ctx.font = '13.5px Pretendard, "Malgun Gothic", sans-serif'
    ctx.fillText('1순위 희망: ', 335, 98)
    ctx.fillStyle = '#1e293b'
    ctx.font = 'bold 13.5px Pretendard, "Malgun Gothic", sans-serif'
    ctx.fillText(`${studentProfile.value.pref_major_1}`, 405, 98)
  }

  // 구분선
  ctx.strokeStyle = '#e2e8f0'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(40, 112)
  ctx.lineTo(width - 40, 112)
  ctx.stroke()

  // 5. 테이블 헤더
  const tableX = 40
  const tableW = width - 80
  const headY = 120
  const headH = 28
  ctx.fillStyle = '#f1f5f9'
  ctx.fillRect(tableX, headY, tableW, headH)
  ctx.strokeStyle = '#cbd5e1'
  ctx.strokeRect(tableX, headY, tableW, headH)

  ctx.fillStyle = '#475569'
  ctx.font = 'bold 12px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText('No.', tableX + 14, headY + 19)
  ctx.fillText('지원 학교', tableX + 54, headY + 19)
  ctx.fillText(':', tableX + 215, headY + 19)
  ctx.fillText('지원 학과', tableX + 235, headY + 19)

  // 6. 테이블 행 (Rows)
  const startRowY = headY + headH
  items.forEach((item, idx) => {
    const rY = startRowY + idx * rowH
    // 교차 배경
    if (idx % 2 === 1) {
      ctx.fillStyle = '#f8fafc'
      ctx.fillRect(tableX, rY, tableW, rowH)
    }

    // 하단 구분선
    ctx.strokeStyle = '#f1f5f9'
    ctx.beginPath()
    ctx.moveTo(tableX, rY + rowH)
    ctx.lineTo(tableX + tableW, rY + rowH)
    ctx.stroke()

    // No.
    ctx.fillStyle = item.isApplied ? '#64748b' : '#cbd5e1'
    ctx.font = '600 12px Pretendard, "Malgun Gothic", sans-serif'
    ctx.fillText(String(idx + 1).padStart(2, '0'), tableX + 14, rY + 24)

    // 학교
    ctx.fillStyle = item.isApplied ? '#0f172a' : '#94a3b8'
    ctx.font = item.isApplied ? 'bold 13.5px Pretendard, "Malgun Gothic", sans-serif' : '13px Pretendard, "Malgun Gothic", sans-serif'
    ctx.fillText(item.displayUniv, tableX + 54, rY + 24)

    // 콜론 :
    ctx.fillStyle = '#cbd5e1'
    ctx.font = 'bold 13px Pretendard, "Malgun Gothic", sans-serif'
    ctx.fillText(':', tableX + 215, rY + 24)

    // 학과
    if (item.is_closed) {
      ctx.fillStyle = '#dc2626'
    } else {
      ctx.fillStyle = item.isApplied ? '#1d4ed8' : '#cbd5e1'
    }
    ctx.font = item.isApplied ? 'bold 13.5px Pretendard, "Malgun Gothic", sans-serif' : '13px Pretendard, "Malgun Gothic", sans-serif'
    ctx.fillText(item.displayMajor, tableX + 235, rY + 24)
  })

  // 테이블 외곽 테두리
  ctx.strokeStyle = '#cbd5e1'
  ctx.lineWidth = 1
  ctx.strokeRect(tableX, headY, tableW, headH + items.length * rowH)

  // 7. 하단 안내 문구
  const footY = height - 20
  ctx.fillStyle = '#94a3b8'
  ctx.font = '11px Pretendard, "Malgun Gothic", sans-serif'
  ctx.fillText('※ 원서 접수 시 대학별 공식 모집요강 및 전형 일정을 반드시 재확인하시기 바랍니다.', 40, footY)

  return canvas
}

function downloadSlipAsPNG() {
  const canvas = drawSlipToCanvas()
  if (!canvas) return
  const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const link = document.createElement('a')
  link.download = `${selectedStudent.value}_2026편입지원_${dateStr}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

async function copySlipToClipboard() {
  const canvas = drawSlipToCanvas()
  if (!canvas) return
  try {
    canvas.toBlob(async blob => {
      if (!blob) return
      try {
        await navigator.clipboard.write([
          new ClipboardItem({ 'image/png': blob })
        ])
        copySlipSuccess.value = '이미지가 클립보드에 복사되었습니다! (Ctrl+V로 카톡/문서에 붙여넣기)'
      } catch (clipErr) {
        downloadSlipAsPNG()
        copySlipSuccess.value = '클립보드 보안 제한으로 인해 PNG 파일로 자동 다운로드되었습니다.'
      }
      if (copySlipTimer) clearTimeout(copySlipTimer)
      copySlipTimer = setTimeout(() => {
        copySlipSuccess.value = ''
      }, 3500)
    }, 'image/png')
  } catch (err) {
    downloadSlipAsPNG()
  }
}

async function copyTextList() {
  const items = printDisplayList.value
  if (!items || items.length === 0) return
  const todayStr = new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' })
  const lines = [
    `[2026학년도 편입 지원 대학 · 학과 리스트]`,
    `학생명: ${selectedStudent.value} (총 ${studentApplications.value.length}개교 지원)`,
    `출력일자: ${todayStr}`,
    '----------------------------------------'
  ]
  items.forEach((item, idx) => {
    const num = String(idx + 1).padStart(2, '0')
    lines.push(`${num}. ${item.displayUniv} : ${item.displayMajor}`)
  })
  lines.push('----------------------------------------')
  try {
    await navigator.clipboard.writeText(lines.join('\n'))
    copySlipSuccess.value = '텍스트가 복사되었습니다! (카카오톡에 바로 붙여넣기 가능)'
    if (copySlipTimer) clearTimeout(copySlipTimer)
    copySlipTimer = setTimeout(() => {
      copySlipSuccess.value = ''
    }, 3500)
  } catch (err) {
    console.error('클립보드 텍스트 복사 실패:', err)
  }
}

function printSlip() {
  window.print()
}

onMounted(async () => {
  isInitialLoading.value = true
  try {
    await Promise.all([
      fetchAllowedStudents(),
      fetchUnivList()
    ])
  } finally {
    isInitialLoading.value = false
  }
})
</script>

<style scoped src="../styles/ApplicationStrategy.css"></style>

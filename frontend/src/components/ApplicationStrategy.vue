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
                        <span :class="['major-name', { 'applied-txt': row.isApplied, 'unapplied-txt': !row.isApplied }]">
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

      <!-- 3) 모집단위 테이블 -->
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
            <div class="monthly-grid">
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
              <span>{{ selectedStudent ? `${selectedStudent} 학생의 ${formUniv} 기출 점수 기록이 없습니다.` : '학생을 선택하면 기출 점수가 표시됩니다.' }}</span>
            </div>
          </div>

          <div class="major-filter-row">
            <div class="major-search-wrap">
              <input
                ref="majorSearchInput"
                v-model="majorKeyword"
                type="text"
                :placeholder="`${formUniv} 학과 검색 (예: 컴, 전자, 경영...)`"
                class="major-search-input"
              />
              <button v-if="majorKeyword" @click="majorKeyword = ''" class="input-clear-btn">✕</button>
            </div>

            <div class="mini-dept-tabs">
              <button :class="['mini-tab', { active: formDeptFilter === 'ALL' }]" @click="formDeptFilter = 'ALL'">전체</button>
              <button :class="['mini-tab', { active: formDeptFilter === '자연' }]" @click="formDeptFilter = '자연'">자연</button>
              <button :class="['mini-tab', { active: formDeptFilter === '인문' }]" @click="formDeptFilter = '인문'">인문</button>
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
                <span class="major-title">{{ d.major }}</span>
              </div>

              <div class="major-right">
                <div class="quota-tag-group">
                  <span :class="['quota-pill', 'gen', { zero: !d.gen || d.gen == 0 }]">
                    일반 <strong class="num">{{ d.gen || 0 }}</strong>명
                  </span>
                  <span :class="['quota-pill', 'bac', { zero: !d.bac || d.bac == 0 }]">
                    학사 <strong class="num">{{ d.bac || 0 }}</strong>명
                  </span>
                </div>
                <span v-if="d.past_admissions && d.past_admissions.length > 0" class="past-mini">
                  합격 {{ d.past_admissions.length }}
                </span>
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
                  <div class="closed-item-main" @click="toggleClosedDetail(d.id)">
                    <div class="major-left">
                      <span :class="['dept-pill', d.dept === '자연' ? 'nat' : 'hum']">{{ d.dept }}</span>
                      <strong class="major-title">{{ d.major }}</strong>
                      <span class="closed-tag">미모집</span>
                    </div>

                    <div class="major-right">
                      <span class="past-mini highlight">
                        과거 합격 {{ d.past_admissions.length }}명
                      </span>
                      <span
                        class="pick-status-btn disabled"
                        title="현행 미선발 학과이므로 원서에 담을 수 없습니다"
                        @click.stop="alertClosedDepartment"
                      >
                        담기 불가
                      </span>
                      <span class="detail-chevron">
                        {{ selectedClosedDeptId === d.id ? '▲' : '▼' }}
                      </span>
                    </div>
                  </div>

                  <!-- 클릭 시 합격생 리스트 상세 펼치기 -->
                  <div v-if="selectedClosedDeptId === d.id" class="closed-past-detail-box">
                    <div class="past-detail-header">
                      <span style="display: inline-flex; align-items: center; gap: 6px;">
                        <Award :size="15" :stroke-width="2" />
                        <span>{{ d.major }} 과거 합격생 성적 이력 (총 {{ d.past_admissions.length }}명)</span>
                      </span>
                    </div>
                    <div class="past-tag-list in-detail">
                      <div
                        v-for="(past, pIdx) in d.past_admissions"
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
                  {{ isSavingNote ? '저장 중...' : '메모 저장' }}
                </button>
              </div>
            </div>
            <div class="note-card-body">
              <textarea
                v-model="studentNoteText"
                placeholder=""
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
            <div class="saved-memo-body">
              <div v-if="savedStudentNote && savedStudentNote.trim()" class="saved-memo-text">
                {{ savedStudentNote }}
              </div>
              <div v-else class="saved-memo-empty">
                저장된 메모가 없습니다. 위의 비고란에 메모를 작성하고 저장해보세요.
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

          <div v-if="studentApplications.length === 0" class="empty-list-box">
            아직 추가된 지원 대학이 없습니다.<br>좌측에서 대학과 학과를 클릭해 바로 담아보세요.
          </div>

          <div v-else class="application-cards">
            <div
              v-for="(app, idx) in sortedStudentApplications"
              :key="app.id"
              class="app-card"
            >
              <div class="card-num">{{ idx + 1 }}</div>
              <div class="card-content" @click="jumpToFormUniv(app.univ)" title="클릭하면 좌측에서 해당 대학 열기">
                <div class="card-univ">{{ app.univ }}</div>
                <div class="card-major">{{ app.major }}</div>
                <div class="card-meta">
                  <span>선발정원: 일반 {{ app.gen_quota }}명 / 학사 {{ app.bac_quota }}명</span>
                  <div v-if="getUnivExamSummary(app.univ)" class="card-exam-tag">
                    <span class="exam-tag-label">기출:</span> {{ getUnivExamSummary(app.univ) }}
                  </div>
                </div>
              </div>
              <button @click="handleRemoveApplication(app.id)" class="btn-remove" title="삭제">
                ✕
              </button>
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
  Sparkles
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
  { name: '중앙대학교(다빈치)', match: u => u.includes('중앙') && (u.includes('다빈치') || u.includes('안성')) },
  { name: '중앙대학교', match: u => u.includes('중앙') },
  { name: '경희대학교', match: u => u.includes('경희') },
  { name: '한국외국어대학교(글로벌)', match: u => (u.includes('한국외') || u.includes('외국어') || u.includes('외대')) && u.includes('글로벌') },
  { name: '한국외국어대학교', match: u => u.includes('한국외') || u.includes('외국어') || u.includes('외대') },
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
  { name: '서울과학기술대학교', match: u => u.includes('과기') || u.includes('과학기술') },
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
  // 8. 한성, 항공
  { name: '한성대학교', match: u => u.includes('한성') },
  { name: '한국항공대학교', match: u => u.includes('항공') },
  // 9. 산기, 수원
  { name: '한국공학대학교', match: u => u.includes('공학대') || u.includes('한국공학') || u.includes('산기대') || u.includes('산업기술') },
  { name: '수원대학교', match: u => u.includes('수원') }
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

// 담긴 원서 목록 정렬 (서성한 중경외시 건동홍 국숭세단 광명상가 인가경 여대 한성 항공 순)
const sortedStudentApplications = computed(() => {
  return [...studentApplications.value].sort((a, b) => {
    const metaA = getUnivMeta(a.univ)
    const metaB = getUnivMeta(b.univ)
    if (metaA.rank !== metaB.rank) return metaA.rank - metaB.rank
    return (a.univ || '').localeCompare(b.univ || '', 'ko')
  })
})

const printDisplayList = computed(() => {
  if (printViewMode.value === 'applied') {
    return sortedStudentApplications.value.map((app, idx) => {
      const meta = getUnivMeta(app.univ)
      return {
        id: app.id || idx,
        displayUniv: app.univ,
        displayMajor: app.major,
        isApplied: true,
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
            displayMajor: app.major,
            isApplied: true,
            rank: sIdx
          })
        })
      } else {
        result.push({
          id: `empty-${spec.name}`,
          displayUniv: spec.name,
          displayMajor: '-',
          isApplied: false,
          rank: sIdx
        })
      }
    })

    appliedList.filter(a => !matchedAppIds.has(a.id)).forEach((app, idx) => {
      const meta = getUnivMeta(app.univ)
      result.push({
        id: app.id || `extra-${idx}`,
        displayUniv: app.univ,
        displayMajor: app.major,
        isApplied: true,
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
const isClosedTab2Open = ref(false)
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

const appliedUnivSet = computed(() => new Set(studentApplications.value.map(a => a.univ)))

const sortedUnivList = computed(() => {
  return [...univList.value].sort((a, b) => a.localeCompare(b, 'ko'))
})

const appliedUnivList = computed(() => {
  return Array.from(appliedUnivSet.value)
})

const currentUnivPastExams = computed(() => {
  if (!formUniv.value) return []
  const uClean = formUniv.value.replace(/대학교|대학/g, '').split('(')[0].trim()
  return studentPastExams.value.filter(s => {
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
    // 💡 [사용자 요청 2] 새로고침/학생 변경 시 입력창은 언제나 빈칸으로 대기
    studentNoteText.value = ''
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
  if (!textToSave) return // 내용이 없으면 저장하지 않음

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
      // 💡 [사용자 요청 2] 저장 완료 후 입력창은 다시 빈칸으로 리셋
      studentNoteText.value = ''
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
  const uClean = univ.replace(/대학교|대학/g, '').split('(')[0].trim()
  const matches = studentPastExams.value.filter(s => {
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
    ctx.fillStyle = item.isApplied ? '#1d4ed8' : '#cbd5e1'
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

<style scoped>
.strategy-container {
  max-width: 1280px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", Roboto, sans-serif;
  color: #1e293b;
}

.wakeup-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
  padding: 12px 18px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 14px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2.5px solid #93c5fd;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.header-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 18px 24px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left h2 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.sub-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.header-right-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-upload-quota {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  background: #f8fafc;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  cursor: pointer;
}
.btn-upload-quota:hover {
  background: #eff6ff;
  border-color: #2563eb;
  color: #2563eb;
}

.tab-controls {
  display: flex;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 8px;
  gap: 4px;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 6px;
  cursor: pointer;
}
.tab-btn.active {
  background: #ffffff;
  color: #2563eb;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

/* 탭 1: 빠른 대학 선택 카드 */
.univ-picker-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 14px;
}

.univ-picker-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.univ-search-wrap {
  position: relative;
  width: 240px;
}

.dept-filters { display: flex; gap: 6px; }
.filter-btn {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  color: #475569;
  border-radius: 6px;
  cursor: pointer;
}
.filter-btn.active { background: #2563eb; color: #ffffff; border-color: #2563eb; }

.legend-box { display: flex; align-items: center; gap: 12px; font-size: 12px; color: #64748b; }
.badge { font-size: 10px; padding: 2px 5px; border-radius: 4px; color: #fff; font-weight: bold; }
.badge.bac { background: #4f46e5; }
.badge.gen { background: #64748b; }

/* 학점은행제 지원자격 카드 */
.eligibility-card {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 10px;
  padding: 12px 18px;
  margin-bottom: 16px;
}

.eligibility-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.eligibility-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #92400e;
}

.elig-badge {
  background: #f59e0b;
  color: #ffffff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.eligibility-actions {
  display: flex;
  gap: 6px;
}

.btn-edit-elig {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  background: #ffffff;
  border: 1px solid #fcd34d;
  color: #92400e;
  border-radius: 6px;
  cursor: pointer;
}
.btn-edit-elig:hover { background: #fef3c7; }

.btn-cancel-sm {
  padding: 4px 10px;
  font-size: 12px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
}

.btn-save-sm {
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 700;
  background: #d97706;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.elig-text {
  margin: 0;
  font-size: 13.5px;
  font-weight: 600;
  color: #78350f;
  white-space: pre-line;
  line-height: 1.5;
}

.elig-placeholder {
  margin: 0;
  font-size: 12.5px;
  color: #b45309;
}

.elig-textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #f59e0b;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  box-sizing: border-box;
  outline: none;
}

/* 테이블 및 공통 스타일 */
.table-wrapper {
  position: relative;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  width: 100%;
}

.mobile-scroll-hint {
  display: none;
}

.table-loading-overlay {
  padding: 10px;
  text-align: center;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 12.5px;
  font-weight: 600;
}

.quota-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.quota-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  padding: 12px 14px;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
}
.quota-table td { padding: 11px 14px; border-bottom: 1px solid #f1f5f9; }
.row-highlight { background-color: #f8fafc; }

.text-center { text-align: center; }
.font-bold { font-weight: 700; }
.text-dark { color: #0f172a; }
.highlight-bac { color: #b45309; font-weight: 700; }
.empty-applicant { color: #cbd5e1; font-size: 12px; }

.applicant-tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.student-tag {
  display: inline-flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 3px 7px;
  gap: 5px;
}

.tag-type { font-size: 10px; padding: 1px 4px; border-radius: 3px; font-weight: bold; }
.tag-bac { background: #e0e7ff; color: #4338ca; }
.tag-gen { background: #f1f5f9; color: #475569; }
.tag-name { font-weight: 700; color: #1e293b; }
.tag-score { font-size: 11px; color: #0284c7; font-family: monospace; font-weight: 600; }

.past-tag-list { display: flex; flex-wrap: wrap; gap: 6px; }
.past-student-tag {
  display: inline-flex;
  align-items: center;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 3px 7px;
  gap: 5px;
}
.tag-year {
  font-size: 11px;
  font-weight: 700;
  color: #0284c7;
  background: #e0f2fe;
  padding: 1px 5px;
  border-radius: 4px;
}

.count-summary-cell { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.total-app-badge {
  font-size: 12px;
  font-weight: 700;
  color: #1d4ed8;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 999px;
}
.sub-app-detail { font-size: 11px; color: #64748b; }
.zero-app-text { font-size: 12px; color: #94a3b8; }

/* 대학 칩 공통 */
.univ-chip-box {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  max-height: 130px;
  overflow-y: auto;
}

.univ-chip {
  padding: 5px 10px;
  font-size: 12.5px;
  font-weight: 600;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  transition: all 0.12s;
}
.univ-chip:hover { border-color: #2563eb; color: #2563eb; }
.univ-chip.applied { border-color: #3b82f6; background: #eff6ff; color: #1d4ed8; }
.univ-chip.active { background: #0f172a; color: #ffffff; border-color: #0f172a; }
.univ-chip.active.applied { background: #1d4ed8; border-color: #1d4ed8; color: #ffffff; }
.applied-dot { font-size: 8px; }

/* 탭 2 및 모달 스타일 */
.student-quick-bar {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.student-bar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.student-nav-group { display: flex; align-items: center; gap: 6px; }
.nav-arrow-btn {
  width: 30px;
  height: 32px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
}
.select-box {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1d4ed8;
  background: #f8fafc;
}
.student-select { min-width: 125px; height: 32px; }
.student-search-wrap { position: relative; flex: 1; max-width: 240px; }

.quick-input {
  width: 100%;
  height: 32px;
  padding: 0 28px 0 10px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 13px;
  box-sizing: border-box;
  outline: none;
}
.quick-input:focus { border-color: #2563eb; }

.input-clear-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
}

.stat-badge {
  font-size: 12.5px;
  padding: 5px 12px;
  border-radius: 999px;
  font-weight: 700;
  background: #eff6ff;
  color: #1d4ed8;
}

/* =====================================================================
   선택 학생 1월~10월 컴팩트 인라인 스코어보드
   ===================================================================== */
.student-score-strip {
  display: flex;
  align-items: stretch;
  gap: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 8px 12px;
  margin-top: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
}

.score-summary-col {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  padding-right: 12px;
  border-right: 1px solid #e2e8f0;
  min-width: 145px;
  flex-shrink: 0;
}

.summary-top {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dept-badge-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  letter-spacing: -0.3px;
}
.dept-badge-pill.natural {
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #bae6fd;
}
.dept-badge-pill.humanities {
  background: #ffedd5;
  color: #c2410c;
  border: 1px solid #fed7aa;
}

.test-cnt-badge {
  font-size: 11px;
  color: #64748b;
  background: #edf2f7;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.summary-values {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.val-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.val-label {
  color: #64748b;
  font-size: 11px;
  font-weight: 600;
  width: 26px;
}

.val-score {
  font-weight: 700;
  font-size: 12px;
}
.val-score.eng, .val-score.max-eng {
  color: #2563eb;
}
.val-score.math, .val-score.max-math {
  color: #0d9488;
}

.monthly-grid-wrapper {
  flex: 1;
  overflow-x: auto;
  display: flex;
  align-items: center;
}

.monthly-grid {
  display: grid;
  grid-template-columns: repeat(10, minmax(54px, 1fr));
  gap: 6px;
  width: 100%;
}

.month-col {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 7px;
  padding: 5px 3px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  transition: all 0.15s ease;
}

.month-col.is-latest {
  border-color: #3b82f6;
  background: #f0f7ff;
  box-shadow: 0 0 0 1px #3b82f6;
}

.month-header {
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 3px;
  margin-bottom: 3px;
}

.latest-dot {
  font-size: 8px;
  color: #2563eb;
}

.score-cell {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 3px;
  font-size: 11.5px;
  padding: 1px 0;
  border-radius: 3px;
}

.score-cell.eng-cell {
  color: #1e293b;
  font-weight: 700;
}

.score-cell.math-cell {
  color: #0f766e;
  font-weight: 700;
  border-top: 1px dashed #e2e8f0;
  margin-top: 2px;
  padding-top: 2px;
}

.subj-sub {
  font-size: 9.5px;
  font-weight: 600;
  color: #94a3b8;
}

.month-col:not(.has-score) .score-num {
  color: #cbd5e1;
  font-weight: 500;
}

.fast-basket-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
  width: 100%;
  min-width: 0;
}

.panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 18px;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.picker-panel,
.list-panel {
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 10px;
  margin-bottom: 14px;
}
.panel-title { font-size: 15px; font-weight: 700; color: #0f172a; margin: 0; }
.guide-hint { font-size: 11.5px; color: #64748b; }
/* =====================================================================
   🏫 신규 대학 선택 UI & 기출 성적 섹션 스타일
   ===================================================================== */
.univ-selector-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
}

.univ-selector-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 12px;
}

.univ-select-label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 4px;
  letter-spacing: -0.2px;
}

.univ-modern-select {
  width: 100%;
  height: 38px;
  padding: 0 10px;
  border: 1.5px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
  background-color: #ffffff;
  outline: none;
  cursor: pointer;
  transition: all 0.15s ease;
}
.univ-modern-select:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.quick-filter-input-box {
  position: relative;
  width: 100%;
}

.univ-quick-filter-input {
  width: 100%;
  height: 38px;
  padding: 0 30px 0 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13px;
  background-color: #ffffff;
  box-sizing: border-box;
  outline: none;
}
.univ-quick-filter-input:focus {
  border-color: #2563eb;
}

.univ-filter-results {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
  padding: 8px;
  background: #ffffff;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
}

.univ-result-chip {
  padding: 4px 9px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #f8fafc;
  color: #334155;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.univ-result-chip:hover {
  background: #eff6ff;
  border-color: #2563eb;
  color: #2563eb;
}
.univ-result-chip.active {
  background: #0f172a;
  color: #ffffff;
  border-color: #0f172a;
}
.applied-star {
  color: #f59e0b;
  font-size: 11px;
}
.no-univ-match {
  font-size: 12px;
  color: #94a3b8;
  padding: 4px;
}

.applied-quick-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px dashed #e2e8f0;
  flex-wrap: wrap;
}

.applied-bar-label {
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
  white-space: nowrap;
}

.applied-chips-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.applied-quick-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  font-size: 11.5px;
  font-weight: 600;
  background: #ffffff;
  border: 1px solid #bfdbfe;
  color: #1d4ed8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.12s ease;
}
.applied-quick-chip .dot {
  font-size: 8px;
  color: #2563eb;
}
.applied-quick-chip:hover {
  background: #eff6ff;
  border-color: #2563eb;
}
.applied-quick-chip.active {
  background: #1d4ed8;
  color: #ffffff;
  border-color: #1d4ed8;
}
.applied-quick-chip.active .dot {
  color: #ffffff;
}

/* =====================================================================
   🎯 기출 성적 섹션 & 점수 등록 양식 스타일
   ===================================================================== */
.past-exam-box {
  background: #ffffff;
  border: 1.5px solid #dbeafe;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.04);
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.past-exam-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
  max-width: 100%;
}

.past-exam-title-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.past-exam-badge {
  font-size: 10.5px;
  font-weight: 800;
  padding: 2px 6px;
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  border-radius: 4px;
}

.past-exam-univ-name {
  font-size: 13.5px;
  font-weight: 800;
  color: #0f172a;
}

.past-exam-count {
  font-size: 11.5px;
  color: #64748b;
  font-weight: 600;
}

.past-exam-summary-chips {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: 2px;
}

.exam-summary-chip {
  font-size: 11px;
  padding: 1.5px 7px;
  border-radius: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.exam-summary-chip.avg {
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #e2e8f0;
}
.exam-summary-chip.avg strong {
  color: #0f172a;
  font-weight: 800;
}

.exam-summary-chip.latest {
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #dbeafe;
}
.exam-summary-chip.latest strong {
  color: #1d4ed8;
  font-weight: 800;
}

.past-exam-header-btns {
  display: flex;
  gap: 6px;
  align-items: center;
}

.btn-toggle-add-exam {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 9px;
  background: #ffffff;
  border: 1px solid #93c5fd;
  color: #2563eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  height: 26px;
  display: inline-flex;
  align-items: center;
}
.btn-toggle-add-exam:hover {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

.btn-excel-upload-exam {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 9px;
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.12s ease;
  height: 26px;
  display: inline-flex;
  align-items: center;
}
.btn-excel-upload-exam:hover {
  background: #dcfce7;
}

.btn-fold-exam {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 8px;
  background: #f8fafc;
  color: #475569;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.12s ease;
  height: 26px;
  display: inline-flex;
  align-items: center;
}
.btn-fold-exam:hover {
  background: #e2e8f0;
  color: #1e293b;
}

/* 직접 입력 폼 */
.past-exam-form-card {
  margin-top: 10px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
}

.exam-form-header-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 6px;
}

.exam-form-title {
  font-size: 12.5px;
  font-weight: 700;
  color: #1e293b;
}

.subject-toggle-group {
  display: inline-flex;
  background: #e2e8f0;
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.subject-btn {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.12s ease;
}
.subject-btn.active {
  background: #ffffff;
  color: #1e293b;
  font-weight: 700;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.exam-form-inputs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

.exam-input-group {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.exam-input-group label {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}

.exam-form-select,
.exam-form-input {
  width: 100%;
  height: 32px;
  padding: 0 8px;
  font-size: 12.5px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  box-sizing: border-box;
  outline: none;
}
.exam-form-select:focus,
.exam-form-input:focus {
  border-color: #2563eb;
}
.exam-form-input.highlight {
  border-color: #2563eb;
  background: #eff6ff;
  font-weight: 700;
}

.exam-form-footer-row {
  display: flex;
  gap: 8px;
}

.exam-form-memo {
  flex: 1;
  height: 32px;
  padding: 0 10px;
  font-size: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #ffffff;
  box-sizing: border-box;
  outline: none;
}

.btn-submit-exam {
  padding: 0 14px;
  height: 32px;
  font-size: 12px;
  font-weight: 700;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  white-space: nowrap;
}
.btn-submit-exam:hover:not(:disabled) {
  background: #1d4ed8;
}

/* 기출 점수 가로 스크롤 카드 래퍼 및 리스트 */
.past-exam-tiles-wrapper {
  margin-top: 8px;
  position: relative;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
}

.past-exam-tiles {
  display: flex;
  flex-direction: row;
  gap: 8px;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 2px 2px 8px 2px;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f8fafc;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.past-exam-tiles::-webkit-scrollbar {
  height: 5px;
}
.past-exam-tiles::-webkit-scrollbar-track {
  background: #f8fafc;
  border-radius: 4px;
}
.past-exam-tiles::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.past-exam-tiles::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.past-exam-tile {
  flex: 0 0 138px;
  min-width: 130px;
  max-width: 155px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 4px;
  padding: 7px 9px;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  box-sizing: border-box;
  transition: transform 160ms var(--ease-out, ease-out), border-color 150ms ease, box-shadow 150ms ease, background-color 150ms ease;
}

@media (hover: hover) and (pointer: fine) {
  .past-exam-tile:hover {
    background: #ffffff;
    border-color: #93c5fd;
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.08);
  }
}

.past-exam-tile:active {
  transform: scale(0.98);
}

.tile-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  width: 100%;
}

.exam-year-tag {
  font-size: 11.5px;
  font-weight: 800;
  color: #1e293b;
  background: #e2e8f0;
  padding: 1px 5px;
  border-radius: 4px;
  white-space: nowrap;
}

.exam-session-badge {
  font-size: 9.5px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 4px;
  white-space: nowrap;
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
}

.exam-subj-badge {
  font-size: 9.5px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 4px;
  white-space: nowrap;
}
.exam-subj-badge.subj-eng {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}
.exam-subj-badge.subj-math {
  background: #faf5ff;
  color: #7e22ce;
  border: 1px solid #e9d5ff;
}
.exam-subj-badge.subj-both {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.btn-del-exam-score {
  width: 17px;
  height: 17px;
  font-size: 9px;
  border: none;
  background: transparent;
  color: #94a3b8;
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.12s ease;
  margin-left: auto;
}
.btn-del-exam-score:hover {
  background: #fee2e2;
  color: #dc2626;
}

.tile-score-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px;
  margin-top: 1px;
}

.exam-score-display {
  display: inline-flex;
  align-items: baseline;
}
.exam-score-display .val {
  font-size: 17px;
  font-weight: 900;
  color: #0f172a;
  letter-spacing: -0.3px;
}
.exam-score-display .unit {
  font-size: 10.5px;
  font-weight: 600;
  color: #64748b;
  margin-left: 1px;
}

.exam-gap-pill {
  font-size: 10.5px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 4px;
  white-space: nowrap;
}
.exam-gap-pill.plus {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}
.exam-gap-pill.minus {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.subscore-breakdown {
  font-size: 10px;
  color: #475569;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tile-foot-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  font-size: 10.5px;
  border-top: 1px dashed #e2e8f0;
  padding-top: 4px;
  margin-top: 2px;
}

.exam-avg-display {
  font-size: 10.5px;
  color: #64748b;
  white-space: nowrap;
}
.exam-avg-display.empty {
  color: #94a3b8;
  font-size: 10px;
}

.exam-memo-chip {
  font-size: 11px;
  cursor: help;
  display: inline-flex;
  align-items: center;
}

.no-past-exam {
  margin-top: 8px;
  padding: 10px 14px;
  font-size: 12px;
  color: #94a3b8;
  text-align: center;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px dashed #e2e8f0;
}

.template-download-row {
  margin: 10px 0 6px 0;
}
.btn-template-dl {
  font-size: 12px;
  font-weight: 600;
  padding: 6px 12px;
  background: #f1f5f9;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.12s ease;
}
.btn-template-dl:hover {
  background: #e2e8f0;
}
.file-upload-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}
.file-input-label {
  font-size: 11.5px;
  font-weight: 600;
  color: #475569;
}
.univ-dropdown-wrap.full-width {
  flex: 1;
  width: 100%;
}
.btn-del-exam-score:hover {
  background: #dc2626;
  color: #ffffff;
}

.past-exam-empty-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #64748b;
  margin-top: 6px;
  padding: 8px 10px;
  background: #f8fafc;
  border-radius: 6px;
  flex-wrap: wrap;
}

.btn-open-exam-input {
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  text-decoration: underline;
}

.card-exam-tag {
  margin-top: 3px;
  font-size: 11px;
  font-weight: 600;
  color: #0369a1;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 4px;
  padding: 2px 6px;
  display: inline-block;
  line-height: 1.35;
}
.exam-tag-label {
  font-weight: 800;
  color: #0284c7;
}

.count-tag { font-size: 12.5px; font-weight: 700; color: #2563eb; }

.major-filter-row { display: flex; gap: 8px; margin: 12px 0 10px; }
.major-search-wrap { position: relative; flex: 1; }
.major-search-input {
  width: 100%;
  height: 36px;
  padding: 0 30px 0 12px;
  border: 1.5px solid #94a3b8;
  border-radius: 8px;
  font-size: 13.5px;
  box-sizing: border-box;
  outline: none;
}
.major-search-input:focus { border-color: #2563eb; }

.mini-dept-tabs { display: flex; background: #f1f5f9; padding: 3px; border-radius: 8px; gap: 2px; }
.mini-tab {
  padding: 0 10px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 6px;
  cursor: pointer;
}
.mini-tab.active { background: #ffffff; color: #0f172a; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }

.quick-major-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 850px;
  overflow-y: auto;
}
.major-pick-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  cursor: pointer;
}
.major-pick-row:hover { background: #f8fafc; border-color: #94a3b8; }
.major-pick-row.selected { background: #eff6ff; border-color: #3b82f6; }

.major-left { display: flex; align-items: center; gap: 8px; }
.dept-pill { font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }
.dept-pill.nat { background: #f3e8ff; color: #7e22ce; }
.dept-pill.hum { background: #fef3c7; color: #92400e; }
.major-title { font-size: 13.5px; font-weight: 700; color: #0f172a; }

.major-right { display: flex; align-items: center; gap: 8px; }

/* 선발 정원 뱃지 디자인 (일반 / 학사) */
.quota-tag-group {
  display: flex;
  align-items: center;
  gap: 5px;
}
.quota-pill {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
}
.quota-pill .num {
  font-weight: 800;
}
.quota-pill.gen {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}
.quota-pill.bac {
  background: #faf5ff;
  color: #7e22ce;
  border: 1px solid #e9d5ff;
}
.quota-pill.zero {
  background: #f8fafc;
  color: #94a3b8;
  border: 1px solid #e2e8f0;
}
.quota-pill.zero .num {
  font-weight: 600;
}

.past-mini { font-size: 11px; font-weight: 600; color: #0284c7; background: #e0f2fe; padding: 2px 6px; border-radius: 4px; }
.pick-status-btn {
  font-size: 13px;
  font-weight: 800;
  min-width: 26px;
  height: 24px;
  padding: 0 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  cursor: pointer;
  white-space: nowrap;
}
.pick-status-btn.active { background: #2563eb; border-color: #2563eb; color: #ffffff; }

.dot-legend {
  color: #2563eb;
  font-size: 10px;
}

/* =====================================================================
   🎯 학생 희망 학과 및 스펙 입력 카드
   ===================================================================== */
.student-pref-card {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.pref-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 22px;
}
.pref-label-row.with-action {
  gap: 6px;
}

.pref-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}
.pref-save-status {
  font-size: 10.5px;
  font-weight: 700;
  color: #16a34a;
  background: #dcfce7;
  padding: 1px 5px;
  border-radius: 4px;
}
.btn-save-pref {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  line-height: 1;
}
.btn-save-pref:hover:not(:disabled) {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}
.pref-card-body {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.pref-grid-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.pref-grid-row.three-cols {
  grid-template-columns: 1.2fr 0.9fr 0.9fr;
}
.pref-field-group {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.pref-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  min-height: 22px;
}
.rank-badge {
  font-size: 9.5px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  line-height: 1.2;
}
.rank-badge.r1 {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}
.rank-badge.r2 {
  background: #f5f3ff;
  color: #6d28d9;
  border: 1px solid #ddd6fe;
}
.rank-badge.dislike {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}
.rank-badge.spec {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}
.pref-input {
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 5px 8px;
  font-size: 12px;
  box-sizing: border-box;
  background: #f8fafc;
  color: #1e293b;
  outline: none;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.pref-input:focus {
  background: #ffffff;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.12);
}
.pref-input.dislike-input {
  color: #991b1b;
}

/* =====================================================================
   학생별 특이사항 및 상담 비고 카드
   ===================================================================== */
.student-note-card {
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 10px;
}
.note-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.note-title-wrap {
  display: flex;
  align-items: center;
  gap: 5px;
}
.note-icon {
  font-size: 13px;
}
.note-title {
  font-size: 12.5px;
  font-weight: 700;
  color: #1e293b;
}
.note-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.note-save-status {
  font-size: 11px;
  font-weight: 700;
  color: #16a34a;
  background: #dcfce7;
  padding: 1px 6px;
  border-radius: 4px;
}
.btn-save-note {
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 9px;
  border-radius: 5px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  cursor: pointer;
}
.btn-save-note:hover:not(:disabled) {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}
.student-note-textarea {
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 12.5px;
  line-height: 1.45;
  box-sizing: border-box;
  resize: vertical;
  outline: none;
  background: #ffffff;
  color: #1e293b;
  font-family: inherit;
}
.student-note-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

/* =====================================================================
   📌 저장된 메모 카드 (비고 밑에 따로 띄움)
   ===================================================================== */
.saved-memo-card {
  background: #fffdf5;
  border: 1px solid #fef08a;
  border-radius: 8px;
  padding: 9px 12px;
  margin-bottom: 14px;
  box-shadow: 0 1px 2px rgba(234, 179, 8, 0.05);
}
.saved-memo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}
.saved-memo-title-wrap {
  display: flex;
  align-items: center;
  gap: 5px;
}
.saved-icon {
  font-size: 12px;
}
.saved-title {
  font-size: 11.5px;
  font-weight: 700;
  color: #854d0e;
}
.saved-date {
  font-size: 10.5px;
  color: #a16207;
}
.btn-delete-memo {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid #fecaca;
  background: #ffffff;
  color: #dc2626;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-delete-memo:hover:not(:disabled) {
  background: #dc2626;
  color: #ffffff;
  border-color: #dc2626;
}
.saved-memo-body {
  font-size: 12px;
  line-height: 1.45;
  color: #334155;
  word-break: break-word;
}
.saved-memo-text {
  white-space: pre-wrap;
  color: #1e293b;
  background: rgba(254, 240, 138, 0.3);
  padding: 6px 9px;
  border-radius: 6px;
  border-left: 3px solid #eab308;
}
.saved-memo-empty {
  font-size: 11px;
  color: #94a3b8;
  font-style: italic;
  padding: 2px 0;
}

.empty-list-box { padding: 40px 20px; text-align: center; font-size: 13px; color: #94a3b8; line-height: 1.6; }
.application-cards { display: flex; flex-direction: column; gap: 8px; max-height: 480px; overflow-y: auto; }
.app-card {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  gap: 12px;
}
.card-num { font-size: 13px; font-weight: 800; color: #2563eb; width: 20px; text-align: center; }
.card-content { flex: 1; cursor: pointer; }
.card-univ { font-size: 12px; font-weight: 700; color: #2563eb; }
.card-major { font-size: 13.5px; font-weight: 700; color: #0f172a; margin: 2px 0; }
.card-meta { font-size: 11px; color: #64748b; }
.btn-remove {
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 6px;
  background: #fee2e2;
  color: #dc2626;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

/* =====================================================================
   💡 성적 유사 선배 합격 대학 추천 섹션
   ===================================================================== */
.similar-seniors-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1.5px dashed #cbd5e1;
}
.similar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.similar-title-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}
.similar-icon {
  font-size: 14px;
}
.similar-title {
  margin: 0;
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
}
.similar-badge {
  font-size: 10.5px;
  font-weight: 600;
  color: #0369a1;
  background: #e0f2fe;
  border: 1px solid #bae6fd;
  padding: 1px 6px;
  border-radius: 4px;
}
.similar-target-bar {
  font-size: 11.5px;
  color: #475569;
  background: #f1f5f9;
  padding: 5px 10px;
  border-radius: 6px;
  margin-bottom: 10px;
}
.similar-loading, .similar-empty {
  font-size: 12px;
  color: #94a3b8;
  padding: 18px 10px;
  text-align: center;
  background: #f8fafc;
  border-radius: 8px;
}
.similar-cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 7px;
  max-height: 520px;
  overflow-y: auto;
}
.similar-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 12px;
  transition: all 0.15s ease;
}
.similar-card:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}
.similar-card-top {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 135px;
}
.senior-info-pill {
  display: flex;
  align-items: center;
  gap: 5px;
}
.senior-yr {
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
}
.senior-nm {
  font-size: 12px;
  font-weight: 700;
  color: #1e293b;
}
.senior-apply-badge {
  font-size: 9.5px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  line-height: 1.2;
}
.senior-apply-badge.gen {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}
.senior-apply-badge.bac {
  background: #faf5ff;
  color: #7e22ce;
  border: 1px solid #e9d5ff;
}
.senior-spec {
  font-size: 10.5px;
  color: #64748b;
}
.similar-card-dest {
  flex: 1;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.dest-univ {
  font-size: 11px;
  font-weight: 700;
  color: #475569;
}
.dest-major {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
}
.similar-card-action {
  flex-shrink: 0;
}
.btn-add-similar {
  font-size: 11.5px;
  font-weight: 700;
  padding: 5px 10px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #1e293b;
  cursor: pointer;
  white-space: nowrap;
}
.btn-add-similar:hover {
  background: #eff6ff;
  border-color: #2563eb;
  color: #2563eb;
}
.btn-add-similar.added {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

/* 모달 */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  padding: 16px;
}
.modal-box { background: #ffffff; border-radius: 12px; width: 100%; max-width: 500px; overflow: hidden; }
.modal-header { padding: 16px 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
.modal-header h3 { margin: 0; font-size: 16px; font-weight: 700; }
.close-btn { background: none; border: none; font-size: 22px; color: #94a3b8; cursor: pointer; }
.modal-body { padding: 20px; }
.guide-text { font-size: 13px; color: #475569; line-height: 1.5; margin-top: 0; }
.sample-table-wrap { margin: 12px 0 16px 0; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; }
.sample-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; }
.sample-table th { background: #f8fafc; padding: 6px; border-bottom: 1px solid #e2e8f0; }
.sample-table td { padding: 6px; border-bottom: 1px solid #f1f5f9; }
.file-input { width: 100%; padding: 8px; border: 1px dashed #cbd5e1; border-radius: 6px; font-size: 13px; }
.modal-footer { padding: 14px 20px; background: #f8fafc; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end; gap: 8px; }
.btn-cancel { padding: 7px 14px; border: 1px solid #cbd5e1; background: #fff; border-radius: 6px; font-size: 13px; cursor: pointer; }
.btn-submit { padding: 7px 16px; border: none; background: #2563eb; color: #fff; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; }

/* =====================================================================
   🖨️ 지원 대학 · 학과 리스트 출력 및 PNG 모달 스타일
   ===================================================================== */
.panel-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-open-print-modal {
  font-size: 11.5px;
  font-weight: 700;
  padding: 4px 10px;
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.15s ease;
}
.btn-open-print-modal:hover:not(:disabled) {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.2);
}
.btn-open-print-modal:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f1f5f9;
  color: #94a3b8;
  border-color: #cbd5e1;
}

.app-cards-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed #e2e8f0;
}
.app-cards-subtitle {
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}
.btn-print-mini-action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  background: #f8fafc;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-print-mini-action:hover {
  background: #2563eb;
  color: #ffffff;
}

/* 출력 모달 크기 & 구조 */
.slip-modal-box {
  max-width: 840px !important;
  width: 95% !important;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  border-radius: 14px !important;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.slip-modal-header {
  padding: 14px 20px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.slip-modal-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.slip-header-icon {
  font-size: 24px;
}
.slip-modal-title-wrap h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}
.slip-header-sub {
  margin: 2px 0 0 0;
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

/* 툴바 */
.slip-modal-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  flex-wrap: wrap;
}
.toolbar-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.toolbar-label {
  font-size: 11.5px;
  font-weight: 700;
  color: #475569;
}
.toolbar-toggle-btns {
  display: inline-flex;
  background: #e2e8f0;
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}
.toolbar-toggle-btns .toggle-btn {
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 9px;
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.12s ease;
}
.toolbar-toggle-btns .toggle-btn.active {
  background: #ffffff;
  color: #1e293b;
  font-weight: 700;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
.toolbar-checkbox {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  user-select: none;
}

.slip-modal-body {
  padding: 18px 20px;
  overflow-y: auto;
  flex: 1;
  background: #f1f5f9;
}

.copy-success-alert {
  background: #dcfce7;
  border: 1px solid #86efac;
  color: #15803d;
  font-size: 12px;
  font-weight: 700;
  padding: 8px 14px;
  border-radius: 6px;
  margin-bottom: 12px;
  text-align: center;
}

/* 실제 인쇄용 상담표 시트 (Canvas 및 브라우저 인쇄 대상) */
.slip-print-container {
  width: 100%;
  display: flex;
  justify-content: center;
}

.print-slip-sheet {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 24px 26px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
  width: 100%;
  max-width: 720px;
  box-sizing: border-box;
}

.slip-header {
  margin-bottom: 10px;
}
.slip-top-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.slip-category-pill {
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #bfdbfe;
}
.slip-today-date {
  font-size: 11.5px;
  color: #94a3b8;
  font-weight: 500;
}
.slip-sheet-title {
  font-size: 21px;
  font-weight: 900;
  color: #0f172a;
  margin: 0 0 10px 0;
  letter-spacing: -0.4px;
}

.slip-meta-cards {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px 14px;
  flex-wrap: wrap;
}
.slip-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
}
.slip-meta-item .lbl {
  color: #64748b;
  font-weight: 600;
}
.slip-meta-item .val {
  color: #0f172a;
  font-weight: 800;
}
.slip-meta-item .val.count {
  color: #2563eb;
}

/* 표 스타일 */
.slip-table-wrap {
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 12px;
}
.slip-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.slip-table th {
  background: #f1f5f9;
  color: #334155;
  font-weight: 800;
  padding: 8px 10px;
  border-bottom: 1px solid #cbd5e1;
  text-align: left;
}
.slip-table td {
  padding: 7px 10px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}
.th-num, .td-num {
  width: 44px;
  text-align: center;
  color: #94a3b8;
  font-weight: 700;
  font-size: 12px;
}
.th-univ, .td-univ {
  width: 170px;
  white-space: nowrap;
}
.td-univ strong {
  font-size: 13.5px;
  color: #0f172a;
  font-weight: 800;
}
.th-sep, .td-sep {
  width: 16px;
  text-align: center;
  color: #cbd5e1;
  font-weight: 700;
}
.th-major, .td-major {
  font-size: 13.5px;
}
.major-name.applied-txt {
  font-weight: 800;
  color: #1d4ed8;
}
.major-name.unapplied-txt {
  color: #cbd5e1;
  font-style: italic;
}

.slip-row:nth-child(even) {
  background: #fafbfc;
}
.slip-row:hover {
  background: #eff6ff;
}
.slip-row.row-empty .td-univ strong {
  color: #94a3b8;
  font-weight: 600;
}

.slip-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-top: 1px dashed #e2e8f0;
  padding-top: 8px;
  font-size: 11px;
  color: #94a3b8;
}
.slip-footer-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.slip-footer-brand {
  font-weight: 700;
  color: #cbd5e1;
}

/* 모달 하단 버튼 액션 */
.slip-modal-footer {
  padding: 12px 20px;
  background: #ffffff;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.footer-left-info .info-tip {
  font-size: 11.5px;
  color: #64748b;
}
.footer-right-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}
.btn-slip-action {
  font-size: 12px;
  font-weight: 700;
  padding: 7px 13px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.btn-slip-action:hover:not(.primary) {
  background: #f1f5f9;
  color: #0f172a;
}
.btn-slip-action.primary {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}
.btn-slip-action.primary:hover {
  background: #1d4ed8;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.25);
}

/* 브라우저 인쇄 모드 (@media print) */
@media print {
  body {
    background: #ffffff !important;
  }
  .strategy-container,
  .modal-header,
  .slip-modal-toolbar,
  .slip-modal-footer,
  .close-btn {
    display: none !important;
  }
  .slip-modal-backdrop {
    position: static !important;
    background: transparent !important;
    padding: 0 !important;
    display: block !important;
  }
  .slip-modal-box {
    box-shadow: none !important;
    border: none !important;
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
  }
  .slip-modal-body {
    padding: 0 !important;
    background: #ffffff !important;
  }
  .slip-print-container {
    width: 100% !important;
    padding: 0 !important;
  }
  .print-slip-sheet {
    box-shadow: none !important;
    border: 1px solid #94a3b8 !important;
    max-width: 100% !important;
    padding: 10mm 15mm !important;
  }
}

/* ========================================================
   📱 원서 지원 관리 모바일 완벽 대응 (768px 이하)
   ======================================================== */
@media (max-width: 768px) {
  .strategy-container {
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
    overflow-x: hidden;
  }

  .wakeup-banner {
    padding: 10px 12px;
    font-size: 12px;
    line-height: 1.45;
  }

  .header-card {
    padding: 14px 12px;
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    margin-bottom: 12px;
  }

  .header-left h2 {
    font-size: 16px;
    line-height: 1.35;
    margin-bottom: 4px;
  }

  .sub-desc {
    font-size: 12px;
    line-height: 1.4;
  }

  .header-right-actions {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .btn-upload-quota {
    width: 100%;
    text-align: center;
    padding: 9px 12px;
    font-size: 13px;
    box-sizing: border-box;
  }

  .tab-controls {
    width: 100%;
    display: flex;
    box-sizing: border-box;
  }

  .tab-btn {
    flex: 1;
    text-align: center;
    padding: 9px 8px;
    font-size: 13px;
  }

  /* 탭 1: 빠른 대학 선택 */
  .univ-picker-card {
    padding: 12px 10px;
    margin-bottom: 12px;
  }

  .univ-picker-top {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
    margin-bottom: 8px;
  }

  .univ-search-wrap {
    width: 100%;
  }

  .dept-filters {
    width: 100%;
    display: flex;
    gap: 4px;
  }

  .filter-btn {
    flex: 1;
    text-align: center;
    padding: 7px 0;
    font-size: 12px;
  }

  .legend-box {
    justify-content: flex-end;
    font-size: 11.5px;
  }

  .univ-chip-box {
    padding: 8px;
    gap: 5px;
    max-height: 125px;
  }

  .univ-chip {
    padding: 5px 8px;
    font-size: 12px;
  }

  /* 탭 1: 학점은행제 지원자격 */
  .eligibility-card {
    padding: 10px 12px;
    margin-bottom: 12px;
  }

  .eligibility-header {
    flex-wrap: wrap;
    gap: 6px;
  }

  .eligibility-title {
    font-size: 13px;
  }

  .elig-badge {
    font-size: 10.5px;
    padding: 2px 6px;
  }

  .elig-text {
    font-size: 12.5px;
    line-height: 1.45;
  }

  /* 탭 1: 모집단위 테이블 */
  .table-wrapper {
    border-radius: 8px;
    width: 100%;
    max-width: 100%;
    box-sizing: border-box;
  }

  .mobile-scroll-hint {
    display: block;
    text-align: center;
    font-size: 11.5px;
    font-weight: 700;
    color: #2563eb;
    background: #eff6ff;
    border-bottom: 1px solid #dbeafe;
    padding: 7px 10px;
    letter-spacing: -0.2px;
  }

  .quota-table {
    min-width: 780px;
  }

  .quota-table th, .quota-table td {
    padding: 8px 10px;
    font-size: 12px;
  }

  .student-tag, .past-student-tag {
    padding: 2px 5px;
    gap: 4px;
    font-size: 11px;
  }

  /* 탭 2: 학생 선택 바 */
  .student-quick-bar {
    padding: 12px 10px;
    gap: 8px;
    margin-bottom: 12px;
  }

  .student-bar-top {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .student-nav-group {
    width: 100%;
    display: flex;
  }

  .student-select {
    flex: 1;
    width: 100%;
  }

  .student-search-wrap {
    width: 100%;
    max-width: 100%;
  }

  .stat-badge.count {
    width: 100%;
    text-align: center;
    box-sizing: border-box;
    font-size: 12px;
    padding: 5px 0;
  }

  /* 탭 2: 월별 스코어보드 */
  .student-score-strip {
    flex-direction: column;
    gap: 8px;
    padding: 10px;
  }

  .score-summary-col {
    min-width: 0;
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e2e8f0;
    padding-right: 0;
    padding-bottom: 8px;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
  }

  .summary-top {
    gap: 6px;
  }

  .summary-values {
    flex-direction: row;
    gap: 10px;
  }

  .monthly-grid-wrapper {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
  }

  .monthly-grid {
    grid-template-columns: repeat(10, 48px);
    gap: 4px;
  }

  .month-col {
    padding: 4px 2px;
  }

  .month-header {
    font-size: 10px;
  }

  .score-cell {
    font-size: 10.5px;
  }

  /* 탭 2: 패널 레이아웃 */
  .fast-basket-layout {
    grid-template-columns: 1fr;
    gap: 14px;
    width: 100%;
  }

  .panel {
    padding: 14px 10px;
    min-width: 0;
    box-sizing: border-box;
  }

  .panel-header {
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 10px;
    padding-bottom: 8px;
  }

  .guide-hint {
    font-size: 11px;
    line-height: 1.35;
  }

  /* 탭 2: 대학 선택 및 기출점수 영역 */
  .univ-selector-row {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .univ-quick-search,
  .univ-main-select {
    width: 100%;
    min-width: 0;
  }

  .applied-quick-bar {
    gap: 4px;
  }

  .past-exam-box-header {
    flex-wrap: wrap;
    gap: 8px;
  }

  .past-exam-header-btns {
    width: 100%;
    justify-content: flex-end;
  }

  .past-exam-tiles {
    gap: 6px;
  }

  .exam-form-inputs {
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }

  /* 탭 2: 학과 탐색 및 담기 행 */
  .major-filter-row {
    flex-direction: column;
    gap: 8px;
  }

  .major-search-wrap {
    width: 100%;
  }

  .mini-dept-tabs {
    width: 100%;
    display: flex;
  }

  .mini-tab {
    flex: 1;
    text-align: center;
    padding: 6px 0;
  }

  .major-pick-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 10px 10px;
  }

  .major-left {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .major-title {
    flex: 1;
    word-break: keep-all;
    font-size: 13px;
    line-height: 1.35;
  }

  .major-right {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 6px;
    flex-wrap: wrap;
    border-top: 1px dashed #f1f5f9;
    padding-top: 6px;
  }

  .quota-tag-group {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .pick-status-btn {
    padding: 5px 12px;
    font-size: 12px;
  }

  /* 탭 2: 희망 학과 및 스펙 */
  .student-pref-card {
    padding: 10px;
  }

  .pref-actions {
    justify-content: flex-end;
  }

  .pref-grid-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .pref-grid-row.three-cols {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .pref-grid-row.three-cols .pref-field-group:first-child {
    grid-column: span 2;
  }

  /* 탭 2: 특이사항 & 메모 */
  .note-card-header,
  .saved-memo-header {
    flex-wrap: wrap;
    gap: 6px;
  }

  .note-actions {
    width: 100%;
    justify-content: flex-end;
  }

  /* 탭 2: 지원 카드 */
  .app-card {
    padding: 8px 10px;
    gap: 8px;
  }

  .card-num {
    width: 16px;
    font-size: 12px;
  }

  .card-major {
    font-size: 13px;
    word-break: keep-all;
  }

  .card-meta {
    font-size: 10.5px;
  }

  /* 탭 2: 성적 유사 지난 합격생 추천 */
  .similar-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 10px;
  }

  .similar-card-top {
    width: 100%;
    min-width: 0;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
  }

  .similar-card-dest {
    width: 100%;
  }

  .dest-major {
    font-size: 13px;
    word-break: keep-all;
  }

  .similar-card-action {
    width: 100%;
  }

  .btn-add-similar {
    width: 100%;
    text-align: center;
    padding: 6px 0;
  }

  /* 엑셀 업로드 모달 */
  .modal-backdrop {
    padding: 10px;
  }

  .modal-box {
    width: 100%;
    max-width: 100%;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal-header {
    padding: 12px 14px;
  }

  .modal-body {
    padding: 14px;
  }

  .sample-table-wrap {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .sample-table {
    min-width: 360px;
  }

  .modal-footer {
    padding: 10px 14px;
  }
}

/* =====================================================================
   🏛️ 현행 미모집 / 개편 과거 학과 (Tab 1 모집요강 하단 접이식 영역)
   ===================================================================== */
.closed-depts-accordion {
  margin-top: 16px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.closed-depts-toggle-header {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: #f8fafc;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease;
  text-align: left;
}
.closed-depts-toggle-header:hover {
  background: #f1f5f9;
}

.closed-depts-toggle-header .toggle-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.closed-depts-toggle-header .icon {
  font-size: 16px;
}
.closed-depts-toggle-header .title {
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}
.closed-depts-toggle-header .badge {
  font-size: 11px;
  font-weight: 700;
  background: #e2e8f0;
  color: #475569;
  padding: 2px 8px;
  border-radius: 12px;
}

.closed-depts-toggle-header .toggle-right {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}
.closed-depts-toggle-header .arrow {
  font-size: 11px;
  color: #94a3b8;
}

.closed-depts-body {
  border-top: 1px solid #e2e8f0;
  padding: 14px 18px;
  background: #ffffff;
}

.closed-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  font-size: 12px;
  color: #475569;
  line-height: 1.5;
  margin-bottom: 14px;
}
.closed-banner .info-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.closed-table-wrapper {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.closed-quota-table .closed-row {
  background: #fafbfc;
}
.closed-quota-table .closed-row:hover {
  background: #f1f5f9;
}
.closed-major-title {
  font-size: 13.5px;
  color: #475569;
}
.closed-status-pill {
  display: inline-block;
  font-size: 10.5px;
  font-weight: 700;
  background: #fee2e2;
  color: #b91c1c;
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 6px;
  vertical-align: middle;
}

/* =====================================================================
   🏛️ 현행 미모집 / 개편 과거 학과 (Tab 2 탐색/담기 패널 하단 접이식 영역)
   ===================================================================== */
.closed-form-accordion {
  margin-top: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: #ffffff;
  overflow: hidden;
}

.closed-form-toggle-btn {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f8fafc;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease;
  text-align: left;
}
.closed-form-toggle-btn:hover {
  background: #f1f5f9;
}

.closed-form-toggle-btn .btn-left {
  display: flex;
  align-items: center;
  gap: 7px;
}
.closed-form-toggle-btn .icon {
  font-size: 14px;
}
.closed-form-toggle-btn .title {
  font-size: 12.5px;
  font-weight: 700;
  color: #334155;
}
.closed-form-toggle-btn .closed-count-badge {
  font-size: 11px;
  font-weight: 700;
  background: #e2e8f0;
  color: #475569;
  padding: 1.5px 6px;
  border-radius: 10px;
}

.closed-form-toggle-btn .btn-right {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 11.5px;
  font-weight: 600;
}
.closed-form-toggle-btn .arrow {
  font-size: 10px;
  color: #94a3b8;
}

.closed-form-content {
  border-top: 1px solid #e2e8f0;
  padding: 10px;
  background: #fcfdfe;
}

.closed-form-notice {
  font-size: 11px;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fef3c7;
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  line-height: 1.4;
}

.closed-form-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.closed-major-item {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #ffffff;
  overflow: hidden;
}

.closed-item-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 12px;
  cursor: pointer;
  transition: background 0.12s ease;
}
.closed-item-main:hover {
  background: #f8fafc;
}

.closed-tag {
  font-size: 10.5px;
  font-weight: 700;
  color: #b91c1c;
  background: #fee2e2;
  padding: 1px 5px;
  border-radius: 3px;
  margin-left: 6px;
}

.past-mini.highlight {
  font-weight: 700;
  color: #0369a1;
  background: #e0f2fe;
}

.pick-status-btn.disabled {
  background: #f1f5f9 !important;
  color: #94a3b8 !important;
  border: 1px solid #e2e8f0 !important;
  cursor: not-allowed !important;
}

.detail-chevron {
  font-size: 10px;
  color: #94a3b8;
  margin-left: 4px;
}

.closed-past-detail-box {
  background: #f8fafc;
  border-top: 1px dashed #e2e8f0;
  padding: 10px 12px;
}

.past-detail-header {
  font-size: 11.5px;
  font-weight: 700;
  color: #475569;
  margin-bottom: 6px;
}

.past-tag-list.in-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
</style>
<template>
  <div class="past-exam-input-container">
    <!-- 1. 상단 안내 및 학생 선택 섹션 -->
    <header class="section-header">
      <div class="header-left">
        <h2 class="section-title">
          <span class="icon"><Edit3 :size="18" :stroke-width="2" /></span>
          <span>학생 기출 성적 직접 입력</span>
        </h2>
        <p class="section-subtitle">
          종이 성적표를 보며 2020~2026년도 기출 점수를 대학별/세션별로 직접 입력하고 저장합니다.
        </p>
      </div>

      <!-- 학생 빠른 검색 및 선택 바 -->
      <div class="student-select-card">
        <div class="student-picker">
          <label class="picker-label">학생 선택</label>
          <div class="picker-control">
            <select v-model="selectedStudent" @change="onStudentChange" class="student-dropdown">
              <option v-for="stu in studentList" :key="stu" :value="stu">{{ stu }}</option>
            </select>
            <div class="search-input-wrapper">
              <input
                type="text"
                v-model="studentSearchQuery"
                @input="onStudentSearchInput"
                placeholder="학생 이름 빠른 검색..."
                class="student-search-input"
              />
              <ul v-if="filteredStudents.length > 0 && studentSearchQuery.trim()" class="search-autocomplete-list">
                <li
                  v-for="s in filteredStudents"
                  :key="s"
                  @click="selectStudent(s)"
                  class="autocomplete-item"
                >
                  <strong>{{ s }}</strong>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- 선택된 학생 요약 통계 배지 -->
        <div class="student-summary-pill" v-if="selectedStudent">
          <span class="stu-badge">{{ selectedStudent }} 학생</span>
          <span class="score-count-badge">등록된 기출 점수: <strong>{{ studentScoreCount }}</strong>건</span>
        </div>

        <!-- 🌟 2020~2026 한 시트 엑셀 일괄 다운로드/업로드 버튼 -->
        <div class="excel-header-actions">
          <button @click="downloadTemplate" class="btn-excel-template" title="2020~2026 전체 대학 기출 점수 엑셀 템플릿 다운로드">
            📥 엑셀 양식 다운로드
          </button>
          <button @click="openExcelModal" class="btn-excel-upload" title="기출 점수 엑셀 일괄 업로드">
            📂 엑셀 일괄 업로드
          </button>
        </div>
      </div>
    </header>

    <!-- 🌟 엑셀 일괄 업로드 모달 -->
    <div v-if="showExcelUploadModal" class="modal-backdrop" @click.self="showExcelUploadModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>📊 2020~2026 기출고사 성적 엑셀 일괄 업로드</h3>
          <button @click="showExcelUploadModal = false" class="modal-close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="excel-guide-banner">
            <p class="banner-title">💡 <strong>한 시트에서 전체 학교 · 전체 년도(2020~2026) 일괄 등록</strong></p>
            <p class="banner-desc">
              1. <strong>[엑셀 양식 다운로드]</strong>로 전체 주요 대학(서성한~항공대)이 포함된 템플릿을 받으세요.<br>
              2. <strong>과목 구분(영어 / 수학 / 영+수)</strong>을 확인하고, 2020년~2026년 열에 점수를 입력하세요.<br>
              3. 완성된 엑셀 파일을 아래에 업로드하면 수십 개의 점수가 한 번에 등록됩니다!
            </p>
          </div>

          <div class="upload-field-row">
            <label class="field-label">기본 적용 학생 (파일 내에 이름이 없을 때 적용)</label>
            <select v-model="uploadTargetStudent" class="modal-student-select">
              <option value="">(파일의 '학생 이름' 컬럼 우선 사용)</option>
              <option v-for="stu in studentList" :key="stu" :value="stu">{{ stu }} 학생</option>
            </select>
          </div>

          <div class="file-picker-box">
            <input
              type="file"
              ref="excelFileInput"
              accept=".xlsx, .xls, .csv"
              id="pastExamExcelFile"
              class="file-hidden-input"
            />
            <label for="pastExamExcelFile" class="file-picker-label">
              <span class="upload-icon">📄</span>
              <span class="upload-prompt">엑셀 파일(.xlsx, .xls, .csv)을 선택하세요</span>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="downloadTemplate" class="btn-modal-sub">📥 양식 다시 받기</button>
          <div class="modal-right-btns">
            <button @click="showExcelUploadModal = false" class="btn-modal-cancel">취소</button>
            <button @click="handleExcelUpload" :disabled="isUploadingExcel" class="btn-modal-submit">
              <span v-if="isUploadingExcel">⏳ 업로드 처리 중...</span>
              <span v-else>🚀 기출 성적 일괄 반영</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. 대학 라인(그룹) 탭 바 -->
    <nav class="tier-nav-bar">
      <button
        v-for="grp in UNIVERSITY_GROUPS"
        :key="grp.tier"
        @click="activeTier = grp.tier"
        :class="['tier-tab-btn', { active: activeTier === grp.tier }]"
      >
        <span class="tier-label">{{ grp.tier }}</span>
        <span class="tier-sub">{{ grp.name }}</span>
        <span v-if="getTierScoreCount(grp) > 0" class="tier-count-chip">
          {{ getTierScoreCount(grp) }}
        </span>
      </button>
    </nav>

    <!-- 3. 선택된 라인의 대학 선택 칩 목록 -->
    <div class="univ-selector-row">
      <button
        v-for="u in currentTierUniversities"
        :key="u.name"
        @click="selectUniversity(u)"
        :class="['univ-chip-btn', { active: currentUniv.name === u.name }]"
      >
        <span class="univ-chip-name">{{ u.name }}</span>
        <span v-if="u.sessions.length > 1" class="split-indicator-pill">
          {{ u.sessions.length }}개 세션
        </span>
        <span v-if="getUnivScoreCount(u.name) > 0" class="univ-score-count">
          {{ getUnivScoreCount(u.name) }}건
        </span>
      </button>
    </div>

    <!-- 4. 기출 성적 입력 메인 카드 -->
    <main class="score-table-card" v-if="selectedStudent && currentUniv">
      <!-- 테이블 헤더 영역: 대학 정보, 세션 필터, 전체 저장 버튼 -->
      <div class="card-toolbar">
        <div class="univ-info-block">
          <h3 class="current-univ-title">
            {{ currentUniv.name }}
            <span class="title-sub">기출 점수 입력표 (2020 ~ 2026년도)</span>
          </h3>
          <!-- 다중 세션 대학인 경우 세션 필터 탭 제공 -->
          <div v-if="currentUniv.sessions.length > 1" class="session-filter-group">
            <span class="filter-caption">시험 세션:</span>
            <button
              @click="activeSessionFilter = 'ALL'"
              :class="['session-btn', { active: activeSessionFilter === 'ALL' }]"
            >
              전체 보기
            </button>
            <button
              v-for="sess in currentUniv.sessions"
              :key="sess"
              @click="activeSessionFilter = sess"
              :class="['session-btn', { active: activeSessionFilter === sess }]"
            >
              {{ sess }}
            </button>
          </div>
        </div>

        <!-- 우측 액션: 이전/다음 대학 전환 및 일괄 저장 -->
        <div class="toolbar-actions">
          <div class="nav-btn-group">
            <button @click="navigateUniv(-1)" class="btn-step-univ" title="이전 대학">◀ 이전</button>
            <button @click="navigateUniv(1)" class="btn-step-univ" title="다음 대학">다음 ▶</button>
          </div>
          <button
            @click="saveAllForCurrentUniv"
            :disabled="isSavingBatch || !hasModifiedRows"
            :class="['btn-save-all', { modified: hasModifiedRows }]"
          >
            <span v-if="isSavingBatch" class="btn-spinner-wrap" style="display: inline-flex; align-items: center; gap: 6px;">
              <Loader2 class="spin" :size="13" />
              <span>저장 중...</span>
            </span>
            <span v-else style="display: inline-flex; align-items: center; gap: 6px;">
              <Save :size="13" :stroke-width="2" />
              <span>{{ currentUniv.name }} 전체 저장</span>
              <kbd class="kbd-hint">Ctrl+S</kbd>
            </span>
          </button>
        </div>
      </div>

      <!-- 저장 알림 토스트 / 상태 바 -->
      <div v-if="statusMessage" :class="['status-toast', statusType]">
        {{ statusMessage }}
      </div>

      <!-- 기출 성적 입력 테이블 -->
      <div class="table-responsive">
        <table class="score-input-table">
          <thead>
            <tr>
              <th class="th-year">기출 년도</th>
              <th v-if="currentUniv.sessions.length > 1" class="th-session">세션 구분</th>
              <th class="th-score eng">영어</th>
              <th class="th-score math">수학</th>
              <th class="th-score both">영+수 (합산/총점)</th>
              <th class="th-memo">비고 / 메모</th>
              <th class="th-status">상태</th>
              <th class="th-action">액션</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(group, gIdx) in yearGroups" :key="group.year">
              <!-- 년도별 구분 간격 (다중 세션 대학에서 년도 간 시각적 여백 및 분리선) -->
              <tr
                v-if="gIdx > 0 && group.rows.length > 1"
                class="year-group-gap-row"
                aria-hidden="true"
              >
                <td :colspan="currentUniv.sessions.length > 1 ? 8 : 7" class="td-year-gap"></td>
              </tr>

              <tr
                v-for="(row, rIdx) in group.rows"
                :key="row.key"
                :class="[
                  'score-row',
                  {
                    modified: row.isModified,
                    saved: row.justSaved,
                    'first-in-group': rIdx === 0,
                    'last-in-group': rIdx === group.rows.length - 1,
                    'is-grouped': group.rows.length > 1
                  }
                ]"
              >
                <!-- 1. 기출 년도 (한 해에 세션이 2개 이상이면 첫 행에서 rowspan 병합) -->
                <td
                  v-if="rIdx === 0"
                  :rowspan="group.rows.length"
                  class="td-year"
                  :class="{ 'td-year-merged': group.rows.length > 1 }"
                >
                  <div class="year-block-content">
                    <span class="year-badge">{{ String(row.year).slice(-2) }}' 기출</span>
                    <span class="full-year">{{ row.year }}년도</span>
                    <span v-if="group.rows.length > 1" class="group-session-tag">
                      {{ group.rows.length }}개 세션
                    </span>
                  </div>
                </td>

                <!-- 2. 세션 구분 (해당 대학만) -->
                <td v-if="currentUniv.sessions.length > 1" class="td-session">
                  <span :class="['session-badge', getSessionColorClass(row.session)]">
                    {{ row.session }}
                  </span>
                </td>

                <!-- 3. 영어 점수 입력 -->
                <td class="td-score eng">
                  <div class="input-with-clear">
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="200"
                      v-model.number="row.eng_score"
                      @input="onRowInput(row)"
                      placeholder=""
                      class="score-input eng-input"
                    />
                    <span class="unit-text">점</span>
                  </div>
                </td>

                <!-- 4. 수학 점수 입력 -->
                <td class="td-score math">
                  <div class="input-with-clear">
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="200"
                      v-model.number="row.math_score"
                      @input="onRowInput(row)"
                      placeholder=""
                      class="score-input math-input"
                    />
                    <span class="unit-text">점</span>
                  </div>
                </td>

                <!-- 5. 영+수 점수 입력 (합산 편의 버튼 제공) -->
                <td class="td-score both">
                  <div class="both-input-wrapper">
                    <div class="input-with-clear">
                      <input
                        type="number"
                        step="0.1"
                        min="0"
                        max="300"
                        v-model.number="row.both_score"
                        @input="onRowInput(row)"
                        placeholder=""
                        class="score-input both-input"
                      />
                      <span class="unit-text">점</span>
                    </div>
                    <!-- 영어, 수학 둘 다 입력되어 있고 영+수가 비어있을 때 간편 합산 버튼 -->
                    <button
                      v-if="canAutoSum(row)"
                      @click="applyAutoSum(row)"
                      class="btn-autosum"
                      type="button"
                      title="영어+수학 점수 자동 합산"
                    >
                      +합산 {{ getSumValue(row) }}
                    </button>
                  </div>
                </td>

                <!-- 6. 비고 메모 -->
                <td class="td-memo">
                  <input
                    type="text"
                    v-model="row.memo"
                    @input="onRowInput(row)"
                    placeholder="특이사항 메모 (선택)"
                    class="memo-input"
                  />
                </td>

                <!-- 7. 저장 상태 인디케이터 -->
                <td class="td-status">
                  <span v-if="row.justSaved" class="status-pill saved" style="display: inline-flex; align-items: center; gap: 3px;">
                    <Check :size="12" :stroke-width="2.5" />
                    <span>저장완료</span>
                  </span>
                  <span v-else-if="row.isModified" class="status-pill unsaved">수정됨</span>
                  <span v-else-if="hasAnyScore(row)" class="status-pill registered">등록됨</span>
                  <span v-else class="status-pill empty">미입력</span>
                </td>

                <!-- 8. 개별 저장 / 초기화 버튼 -->
                <td class="td-action">
                  <button
                    @click="saveSingleRow(row)"
                    :disabled="row.isSaving"
                    :class="['btn-row-save', { active: row.isModified }]"
                    title="해당 년도 점수 저장"
                  >
                    <span v-if="row.isSaving" style="display: inline-flex; align-items: center; justify-content: center;">
                      <Loader2 class="spin" :size="12" />
                    </span>
                    <span v-else>저장</span>
                  </button>
                  <button
                    v-if="hasAnyScore(row)"
                    @click="clearRow(row)"
                    class="btn-row-clear"
                    title="이 행 점수 삭제"
                  >
                    삭제
                  </button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- 하단 플로팅 저장 바 (스크롤 긴 경우 대비) -->
      <div class="card-footer-toolbar">
        <div class="footer-left-info">
          <span>{{ currentUniv.name }} 기출 성적: </span>
          <strong>{{ currentUnivRegisteredCount }}개 등록됨</strong>
          <span v-if="hasModifiedRows" class="unsaved-warning"> (미저장 변경사항 있음)</span>
        </div>
        <button
          @click="saveAllForCurrentUniv"
          :disabled="isSavingBatch || !hasModifiedRows"
          :class="['btn-save-all', { modified: hasModifiedRows }]"
        >
          <span v-if="isSavingBatch" class="btn-spinner-wrap" style="display: inline-flex; align-items: center; gap: 6px;">
            <Loader2 class="spin" :size="13" />
            <span>저장 중...</span>
          </span>
          <span v-else style="display: inline-flex; align-items: center; gap: 6px;">
            <Save :size="14" :stroke-width="2" />
            <span>전체 일괄 저장 (Ctrl+S)</span>
          </span>
        </button>
      </div>
    </main>

    <!-- 학생 미선택 시 안내 카드 -->
    <div v-else-if="!selectedStudent" class="empty-guide-card">
      <div class="guide-content">
        <span class="guide-icon"><User :size="28" :stroke-width="1.8" /></span>
        <h3>학생을 먼저 선택해 주세요</h3>
        <p>상단의 학생 선택 드롭다운 또는 빠른 검색창에서 기출 성적을 입력할 학생을 선택하세요.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Edit3, Save, Check, User, Loader2 } from 'lucide-vue-next'

const API_BASE = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? 'http://127.0.0.1:8000'
  : 'https://peer-score-finder.onrender.com'

// =========================================================================
// 1. 지원 대학 목록 및 공식 정식 명칭, 세션 구분 정의
// =========================================================================
const UNIVERSITY_GROUPS = [
  {
    tier: '서성한',
    name: '서강 · 성균관 · 한양',
    universities: [
      { name: '서강대학교', sessions: ['공통'] },
      { name: '성균관대학교', sessions: ['공통'] },
      { name: '한양대학교', sessions: ['공통'] }
    ]
  },
  {
    tier: '중경외시',
    name: '중앙 · 경희 · 한국외대 · 시립대',
    universities: [
      { name: '중앙대학교', sessions: ['공통'] },
      { name: '경희대학교', sessions: ['공통'] },
      { name: '한국외국어대학교', sessions: ['T1 A형', 'T2 B형'] },
      { name: '서울시립대학교', sessions: ['공통'] }
    ]
  },
  {
    tier: '건동홍',
    name: '건국 · 동국 · 홍익',
    universities: [
      { name: '건국대학교', sessions: ['공통'] },
      { name: '동국대학교', sessions: ['공통'] },
      { name: '홍익대학교', sessions: ['공통'] }
    ]
  },
  {
    tier: '국숭세단',
    name: '국민 · 숭실 · 세종 · 단국',
    universities: [
      { name: '국민대학교', sessions: ['공통'] },
      { name: '숭실대학교', sessions: ['공통'] },
      { name: '세종대학교', sessions: ['공통'] },
      { name: '단국대학교', sessions: ['오전', '오후'] }
    ]
  },
  {
    tier: '광명가',
    name: '광운 · 명지 · 가톨릭 · 상명',
    universities: [
      { name: '광운대학교', sessions: ['공통'] },
      { name: '명지대학교', sessions: ['오전', '오후'] },
      { name: '가톨릭대학교', sessions: ['공통'] },
      { name: '상명대학교', sessions: ['공통'] }
    ]
  },
  {
    tier: '인가경',
    name: '인하 · 인천 · 가천 · 경기 · 아주',
    universities: [
      { name: '인하대학교', sessions: ['공통'] },
      { name: '인천대학교', sessions: ['공통'] },
      { name: '가천대학교', sessions: ['A형', 'B형'] },
      { name: '경기대학교', sessions: ['공통'] },
      { name: '아주대학교', sessions: ['공통'] }
    ]
  },
  {
    tier: '여대라인',
    name: '이화 · 숙명 · 동덕 · 덕성 · 서울여대',
    universities: [
      { name: '이화여자대학교', sessions: ['공통'] },
      { name: '숙명여자대학교', sessions: ['A형', 'B형'] },
      { name: '동덕여자대학교', sessions: ['공통'] },
      { name: '덕성여자대학교', sessions: ['1교시', '2교시', '3교시'] },
      { name: '서울여자대학교', sessions: ['오전', '오후'] }
    ]
  },
  {
    tier: '한성 · 항공',
    name: '한성 · 항공',
    universities: [
      { name: '한성대학교', sessions: ['공통'] },
      { name: '한국항공대학교', sessions: ['공통'] }
    ]
  }
]

// 2020년도부터 2026년도까지 (내림차순 정렬)
const EXAM_YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020]

// =========================================================================
// 2. 상태(State) 반응형 변수
// =========================================================================
const studentList = ref([])
const selectedStudent = ref('')
const studentSearchQuery = ref('')

const activeTier = ref('서성한')
const currentUniv = ref(UNIVERSITY_GROUPS[0].universities[0])
const activeSessionFilter = ref('ALL') // 'ALL' or specific session name

// 전체 학생 기출 성적 DB 레코드 보관 리스트
const rawStudentPastExams = ref([])

// 현재 선택된 대학의 행별 데이터 모델 리스트
const rows = ref([])

const isSavingBatch = ref(false)
const statusMessage = ref('')
const statusType = ref('success')

// 🌟 엑셀 다운로드 / 일괄 업로드 관련 상태
const showExcelUploadModal = ref(false)
const excelFileInput = ref(null)
const isUploadingExcel = ref(false)
const uploadTargetStudent = ref('')

function downloadTemplate() {
  window.open(`${API_BASE}/api/student-past-exams/sample-template`, '_blank')
}

function openExcelModal() {
  uploadTargetStudent.value = selectedStudent.value || ''
  showExcelUploadModal.value = true
}

async function handleExcelUpload() {
  const fileEl = excelFileInput.value
  if (!fileEl || !fileEl.files || fileEl.files.length === 0) {
    alert('업로드할 엑셀 파일을 선택해 주세요.')
    return
  }
  const formData = new FormData()
  formData.append('file', fileEl.files[0])
  if (uploadTargetStudent.value) {
    formData.append('default_student', uploadTargetStudent.value)
  }

  isUploadingExcel.value = true
  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams/upload-excel`, {
      method: 'POST',
      body: formData
    })
    const result = await res.json()
    if (res.ok) {
      alert(result.message)
      showExcelUploadModal.value = false
      fileEl.value = ''
      await loadStudentPastExams()
    } else {
      alert(result.detail || '기출 엑셀 업로드 중 오류가 발생했습니다.')
    }
  } catch (err) {
    console.error('기출 엑셀 업로드 에러:', err)
    alert('서버 통신 중 오류가 발생했습니다.')
  } finally {
    isUploadingExcel.value = false
  }
}

// =========================================================================
// 3. Computed 계산식
// =========================================================================
const filteredStudents = computed(() => {
  const q = studentSearchQuery.value.trim().toLowerCase()
  if (!q) return studentList.value
  return studentList.value.filter(s => s.toLowerCase().includes(q))
})

const currentTierUniversities = computed(() => {
  const grp = UNIVERSITY_GROUPS.find(g => g.tier === activeTier.value)
  return grp ? grp.universities : []
})

const allUniversitiesFlat = computed(() => {
  const list = []
  for (const grp of UNIVERSITY_GROUPS) {
    for (const u of grp.universities) {
      list.push({ ...u, tier: grp.tier })
    }
  }
  return list
})

const studentScoreCount = computed(() => {
  return rawStudentPastExams.value.length
})

const visibleRows = computed(() => {
  if (activeSessionFilter.value === 'ALL') {
    return rows.value
  }
  return rows.value.filter(r => r.session === activeSessionFilter.value)
})

// 년도별로 행들을 묶어 다중 세션 대학을 깔끔하게 그룹핑
const yearGroups = computed(() => {
  const vRows = visibleRows.value
  const groups = []
  const map = new Map()

  for (const row of vRows) {
    if (!map.has(row.year)) {
      const g = { year: row.year, rows: [] }
      map.set(row.year, g)
      groups.push(g)
    }
    map.get(row.year).rows.push(row)
  }
  return groups
})

const hasModifiedRows = computed(() => {
  return rows.value.some(r => r.isModified)
})

const currentUnivRegisteredCount = computed(() => {
  return rows.value.filter(r => hasAnyScore(r)).length
})

// =========================================================================
// 4. 초기화 및 학생 성적 데이터 로드
// =========================================================================
onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  await fetchStudentList()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})

function handleKeydown(e) {
  // Ctrl + S (or Cmd + S) 단축키로 전체 저장
  if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
    e.preventDefault()
    if (hasModifiedRows.value && !isSavingBatch.value) {
      saveAllForCurrentUniv()
    }
  }
}

async function fetchStudentList() {
  try {
    const res = await fetch(`${API_BASE}/all-students-2026`)
    if (res.ok) {
      const data = await res.json()
      if (Array.isArray(data) && data.length > 0) {
        studentList.value = data
        if (!selectedStudent.value) {
          selectedStudent.value = data[0]
          await loadStudentPastExams()
        }
      }
    }
  } catch (err) {
    console.error('학생 명단 로드 오류:', err)
  }
}

async function loadStudentPastExams() {
  if (!selectedStudent.value) {
    rawStudentPastExams.value = []
    rebuildRows()
    return
  }

  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams?student_name=${encodeURIComponent(selectedStudent.value)}`)
    if (res.ok) {
      const data = await res.json()
      rawStudentPastExams.value = data.scores || []
    }
  } catch (err) {
    console.error('기출 성적 조회 오류:', err)
  } finally {
    rebuildRows()
  }
}

function onStudentChange() {
  loadStudentPastExams()
}

function selectStudent(name) {
  selectedStudent.value = name
  studentSearchQuery.value = ''
  loadStudentPastExams()
}

function onStudentSearchInput() {
  // 검색어 입력 시 자동완성 표시
}

// =========================================================================
// 5. 현재 대학 및 세션에 따른 테이블 행 구성
// =========================================================================
function selectUniversity(univ) {
  currentUniv.value = univ
  activeSessionFilter.value = 'ALL'
  rebuildRows()
}

function getUnivKeyForSession(univName, session) {
  if (!session || session === '공통') {
    return univName
  }
  return `${univName}(${session})`
}

function rebuildRows() {
  if (!currentUniv.value) {
    rows.value = []
    return
  }

  const newRows = []
  const univName = currentUniv.value.name
  const sessions = currentUniv.value.sessions

  for (const year of EXAM_YEARS) {
    for (const session of sessions) {
      const univKey = getUnivKeyForSession(univName, session)

      // DB 레코드 매칭: 정확히 일치하거나, 단일 세션 대학인 경우 이름 호환
      const matchingScores = rawStudentPastExams.value.filter(s => {
        if (s.exam_year !== year) return false
        if (s.univ === univKey) return true
        // 공통 세션인 경우 괄호 없는 이름 매칭
        if (session === '공통' && (s.univ === univName || s.univ.startsWith(univName + '(') === false && s.univ.includes(univName.replace('대학교', '')))) {
          return true
        }
        return false
      })

      // 영어, 수학, 영+수 점수 추출
      const engRecord = matchingScores.find(s => s.subject_type === '영어')
      const mathRecord = matchingScores.find(s => s.subject_type === '수학')
      const bothRecord = matchingScores.find(s => s.subject_type === '영+수')

      const engVal = engRecord ? engRecord.my_score : null
      const mathVal = mathRecord ? mathRecord.my_score : null
      const bothVal = bothRecord ? bothRecord.my_score : null

      // 메모 (우선순위: 영+수 > 영어 > 수학)
      const memoVal = (bothRecord?.memo || engRecord?.memo || mathRecord?.memo || '')

      newRows.push({
        key: `${univKey}_${year}`,
        univName: univName,
        session: session,
        univKey: univKey,
        year: year,
        eng_score: engVal,
        math_score: mathVal,
        both_score: bothVal,
        memo: memoVal,
        // 원본 비교용 스냅샷
        original: {
          eng_score: engVal,
          math_score: mathVal,
          both_score: bothVal,
          memo: memoVal
        },
        isModified: false,
        isSaving: false,
        justSaved: false
      })
    }
  }

  rows.value = newRows
}

function onRowInput(row) {
  const orig = row.original
  const isChanged =
    Number(row.eng_score ?? '') !== Number(orig.eng_score ?? '') ||
    Number(row.math_score ?? '') !== Number(orig.math_score ?? '') ||
    Number(row.both_score ?? '') !== Number(orig.both_score ?? '') ||
    (row.memo || '').trim() !== (orig.memo || '').trim()

  row.isModified = isChanged
  row.justSaved = false
}

function hasAnyScore(row) {
  return (
    (row.eng_score !== null && row.eng_score !== '' && !isNaN(row.eng_score)) ||
    (row.math_score !== null && row.math_score !== '' && !isNaN(row.math_score)) ||
    (row.both_score !== null && row.both_score !== '' && !isNaN(row.both_score))
  )
}

function canAutoSum(row) {
  const e = Number(row.eng_score)
  const m = Number(row.math_score)
  const b = row.both_score
  return !isNaN(e) && e > 0 && !isNaN(m) && m > 0 && (b === null || b === '' || isNaN(b))
}

function getSumValue(row) {
  const e = Number(row.eng_score) || 0
  const m = Number(row.math_score) || 0
  return Math.round((e + m) * 10) / 10
}

function applyAutoSum(row) {
  row.both_score = getSumValue(row)
  onRowInput(row)
}

// =========================================================================
// 6. 점수 저장 및 삭제 처리
// =========================================================================
function showToast(msg, type = 'success') {
  statusMessage.value = msg
  statusType.value = type
  setTimeout(() => {
    if (statusMessage.value === msg) {
      statusMessage.value = ''
    }
  }, 4000)
}

// 단일 행 저장
async function saveSingleRow(row) {
  if (!selectedStudent.value) {
    alert('학생을 먼저 선택해 주세요.')
    return
  }

  row.isSaving = true
  const itemsToSave = []

  // 1. 영어
  if (row.eng_score !== null && row.eng_score !== '' && !isNaN(Number(row.eng_score))) {
    itemsToSave.push({
      univ: row.univKey,
      exam_year: row.year,
      subject_type: '영어',
      my_score: Number(row.eng_score),
      memo: row.memo || ''
    })
  } else if (row.original.eng_score !== null && row.original.eng_score !== '') {
    // 삭제
    itemsToSave.push({
      univ: row.univKey,
      exam_year: row.year,
      subject_type: '영어',
      delete: true
    })
  }

  // 2. 수학
  if (row.math_score !== null && row.math_score !== '' && !isNaN(Number(row.math_score))) {
    itemsToSave.push({
      univ: row.univKey,
      exam_year: row.year,
      subject_type: '수학',
      my_score: Number(row.math_score),
      memo: row.memo || ''
    })
  } else if (row.original.math_score !== null && row.original.math_score !== '') {
    // 삭제
    itemsToSave.push({
      univ: row.univKey,
      exam_year: row.year,
      subject_type: '수학',
      delete: true
    })
  }

  // 3. 영+수
  if (row.both_score !== null && row.both_score !== '' && !isNaN(Number(row.both_score))) {
    itemsToSave.push({
      univ: row.univKey,
      exam_year: row.year,
      subject_type: '영+수',
      my_score: Number(row.both_score),
      eng_score: row.eng_score !== null && row.eng_score !== '' ? Number(row.eng_score) : null,
      math_score: row.math_score !== null && row.math_score !== '' ? Number(row.math_score) : null,
      memo: row.memo || ''
    })
  } else if (row.original.both_score !== null && row.original.both_score !== '') {
    // 삭제
    itemsToSave.push({
      univ: row.univKey,
      exam_year: row.year,
      subject_type: '영+수',
      delete: true
    })
  }

  if (itemsToSave.length === 0) {
    row.isSaving = false
    showToast('입력된 점수가 없어 변경사항이 없습니다.', 'info')
    return
  }

  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        items: itemsToSave
      })
    })

    if (res.ok) {
      row.original = {
        eng_score: row.eng_score,
        math_score: row.math_score,
        both_score: row.both_score,
        memo: row.memo
      }
      row.isModified = false
      row.justSaved = true
      setTimeout(() => { row.justSaved = false }, 2500)
      showToast(`✓ ${row.univKey} ${row.year}년도 점수가 성공적으로 저장되었습니다.`)
      // 백그라운드 갱신
      fetchStudentPastExamsQuietly()
    } else {
      const err = await res.json()
      alert('저장 실패: ' + (err.detail || '오류가 발생했습니다.'))
    }
  } catch (err) {
    console.error('단일 행 저장 실패:', err)
    alert('저장 도중 통신 오류가 발생했습니다.')
  } finally {
    row.isSaving = false
  }
}

// 전체 일괄 저장
async function saveAllForCurrentUniv() {
  if (!selectedStudent.value) {
    alert('학생을 먼저 선택해 주세요.')
    return
  }

  const modifiedRows = rows.value.filter(r => r.isModified)
  if (modifiedRows.length === 0) {
    showToast('저장할 변경사항이 없습니다.', 'info')
    return
  }

  isSavingBatch.value = true
  const allBatchItems = []

  for (const row of modifiedRows) {
    // 1. 영어
    if (row.eng_score !== null && row.eng_score !== '' && !isNaN(Number(row.eng_score))) {
      allBatchItems.push({
        univ: row.univKey,
        exam_year: row.year,
        subject_type: '영어',
        my_score: Number(row.eng_score),
        memo: row.memo || ''
      })
    } else if (row.original.eng_score !== null && row.original.eng_score !== '') {
      allBatchItems.push({
        univ: row.univKey,
        exam_year: row.year,
        subject_type: '영어',
        delete: true
      })
    }

    // 2. 수학
    if (row.math_score !== null && row.math_score !== '' && !isNaN(Number(row.math_score))) {
      allBatchItems.push({
        univ: row.univKey,
        exam_year: row.year,
        subject_type: '수학',
        my_score: Number(row.math_score),
        memo: row.memo || ''
      })
    } else if (row.original.math_score !== null && row.original.math_score !== '') {
      allBatchItems.push({
        univ: row.univKey,
        exam_year: row.year,
        subject_type: '수학',
        delete: true
      })
    }

    // 3. 영+수
    if (row.both_score !== null && row.both_score !== '' && !isNaN(Number(row.both_score))) {
      allBatchItems.push({
        univ: row.univKey,
        exam_year: row.year,
        subject_type: '영+수',
        my_score: Number(row.both_score),
        eng_score: row.eng_score !== null && row.eng_score !== '' ? Number(row.eng_score) : null,
        math_score: row.math_score !== null && row.math_score !== '' ? Number(row.math_score) : null,
        memo: row.memo || ''
      })
    } else if (row.original.both_score !== null && row.original.both_score !== '') {
      allBatchItems.push({
        univ: row.univKey,
        exam_year: row.year,
        subject_type: '영+수',
        delete: true
      })
    }
  }

  if (allBatchItems.length === 0) {
    isSavingBatch.value = false
    showToast('적용할 변경사항이 없습니다.', 'info')
    return
  }

  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        items: allBatchItems
      })
    })

    if (res.ok) {
      for (const row of modifiedRows) {
        row.original = {
          eng_score: row.eng_score,
          math_score: row.math_score,
          both_score: row.both_score,
          memo: row.memo
        }
        row.isModified = false
        row.justSaved = true
        setTimeout(() => { row.justSaved = false }, 2500)
      }
      showToast(`✓ ${currentUniv.value.name} 기출 성적 ${allBatchItems.length}건이 성공적으로 저장되었습니다.`)
      fetchStudentPastExamsQuietly()
    } else {
      const err = await res.json()
      alert('일괄 저장 실패: ' + (err.detail || '오류가 발생했습니다.'))
    }
  } catch (err) {
    console.error('일괄 저장 실패:', err)
    alert('일괄 저장 중 네트워크 오류가 발생했습니다.')
  } finally {
    isSavingBatch.value = false
  }
}

// 행 삭제 / 비우기
async function clearRow(row) {
  if (!confirm(`${row.univKey} ${row.year}년도 등록된 점수를 모두 삭제하시겠습니까?`)) {
    return
  }

  row.eng_score = null
  row.math_score = null
  row.both_score = null
  row.memo = ''

  await saveSingleRow(row)
}

async function fetchStudentPastExamsQuietly() {
  if (!selectedStudent.value) return
  try {
    const res = await fetch(`${API_BASE}/api/student-past-exams?student_name=${encodeURIComponent(selectedStudent.value)}`)
    if (res.ok) {
      const data = await res.json()
      rawStudentPastExams.value = data.scores || []
    }
  } catch (err) {
    // 조용히 무시
  }
}

// =========================================================================
// 7. 이전 / 다음 대학 탐색 네비게이션
// =========================================================================
function navigateUniv(delta) {
  const all = allUniversitiesFlat.value
  const idx = all.findIndex(u => u.name === currentUniv.value.name)
  if (idx === -1) return

  let nextIdx = idx + delta
  if (nextIdx < 0) nextIdx = all.length - 1
  if (nextIdx >= all.length) nextIdx = 0

  const target = all[nextIdx]
  activeTier.value = target.tier
  selectUniversity(target)
}

// =========================================================================
// 8. 배지 및 통계 헬퍼
// =========================================================================
function getUnivScoreCount(univName) {
  return rawStudentPastExams.value.filter(s => {
    return s.univ === univName || s.univ.startsWith(univName + '(')
  }).length
}

function getTierScoreCount(tierGroup) {
  let count = 0
  for (const u of tierGroup.universities) {
    count += getUnivScoreCount(u.name)
  }
  return count
}

function getSessionColorClass(session) {
  if (session === '오전' || session === '1교시' || session === 'A형' || session === 'T1 A형') {
    return 'sess-primary'
  }
  if (session === '오후' || session === '2교시' || session === 'B형' || session === 'T2 B형') {
    return 'sess-secondary'
  }
  if (session === '3교시') {
    return 'sess-tertiary'
  }
  return 'sess-default'
}
</script>

<style scoped>
.past-exam-input-container {
  max-width: 1280px;
  margin: 0 auto 40px auto;
  padding: 0 16px;
  color: #1e293b;
}

/* 1. 상단 섹션 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  padding: 20px;
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
}

.header-left .section-title {
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left .section-subtitle {
  font-size: 13.5px;
  color: #64748b;
  margin: 0;
}

.student-select-card {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.student-picker {
  display: flex;
  align-items: center;
  gap: 10px;
}

.picker-label {
  font-size: 13px;
  font-weight: 700;
  color: #475569;
  white-space: nowrap;
}

.picker-control {
  display: flex;
  gap: 8px;
  position: relative;
}

.student-dropdown {
  padding: 8px 12px;
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  background: #f8fafc;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  outline: none;
  cursor: pointer;
}

.student-dropdown:focus {
  border-color: #2563eb;
  background: #ffffff;
}

.search-input-wrapper {
  position: relative;
}

.student-search-input {
  padding: 8px 12px;
  font-size: 13.5px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  width: 170px;
  outline: none;
  background: #ffffff;
}

.student-search-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
}

.search-autocomplete-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  padding: 4px 0;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  list-style: none;
  z-index: 50;
  max-height: 180px;
  overflow-y: auto;
}

.autocomplete-item {
  padding: 8px 12px;
  font-size: 13.5px;
  cursor: pointer;
  color: #334155;
}

.autocomplete-item:hover {
  background: #eff6ff;
  color: #1d4ed8;
}

.student-summary-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f1f5f9;
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
}

.stu-badge {
  font-size: 13px;
  font-weight: 800;
  color: #0f172a;
}

.score-count-badge {
  font-size: 12.5px;
  color: #475569;
}

.score-count-badge strong {
  color: #2563eb;
}

/* 2. 라인 탭 바 */
.tier-nav-bar {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.tier-tab-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  cursor: pointer;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.23, 1, 0.32, 1)), background-color 150ms ease, border-color 150ms ease, color 150ms ease;
  white-space: nowrap;
  position: relative;
  min-width: 120px;
}

.tier-tab-btn:hover {
  background: #f8fafc;
  border-color: #94a3b8;
}

.tier-tab-btn:active {
  transform: scale(0.97);
}

.tier-tab-btn.active {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.25);
}

.tier-label {
  font-size: 14px;
  font-weight: 800;
}

.tier-tab-btn.active .tier-label {
  color: #ffffff;
}

.tier-sub {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}

.tier-tab-btn.active .tier-sub {
  color: #dbeafe;
}

.tier-count-chip {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 10.5px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
  background: #eff6ff;
  color: #1d4ed8;
}

.tier-tab-btn.active .tier-count-chip {
  background: #ffffff;
  color: #2563eb;
}

/* 3. 대학 칩 바 */
.univ-selector-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  background: #f8fafc;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.univ-chip-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 700;
  color: #334155;
  cursor: pointer;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.23, 1, 0.32, 1)), background-color 150ms ease, border-color 150ms ease, color 150ms ease;
}

.univ-chip-btn:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}

.univ-chip-btn:active {
  transform: scale(0.97);
}

.univ-chip-btn.active {
  background: #0f172a;
  color: #ffffff;
  border-color: #0f172a;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.split-indicator-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  background: #fef3c7;
  color: #b45309;
  border-radius: 4px;
}

.univ-chip-btn.active .split-indicator-pill {
  background: #334155;
  color: #fde68a;
}

.univ-score-count {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 6px;
  background: #eff6ff;
  color: #2563eb;
  border-radius: 10px;
}

.univ-chip-btn.active .univ-score-count {
  background: #38bdf8;
  color: #0f172a;
}

/* 4. 점수 입력 메인 카드 */
.score-table-card {
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.card-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  padding: 18px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.current-univ-title {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.current-univ-title .title-sub {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
}

.session-filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
}

.filter-caption {
  font-size: 12.5px;
  font-weight: 700;
  color: #64748b;
}

.session-btn {
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  color: #475569;
  cursor: pointer;
}

.session-btn.active {
  background: #7c3aed;
  color: #ffffff;
  border-color: #7c3aed;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.nav-btn-group {
  display: flex;
  gap: 4px;
}

.btn-step-univ {
  padding: 8px 12px;
  font-size: 12.5px;
  font-weight: 700;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  color: #475569;
  cursor: pointer;
}

.btn-step-univ:hover {
  background: #f1f5f9;
}

.btn-save-all {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 800;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 160ms var(--ease-out, cubic-bezier(0.23, 1, 0.32, 1)), background-color 150ms ease, box-shadow 150ms ease;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
}

.btn-save-all:hover:not(:disabled) {
  background: #1d4ed8;
  transform: translateY(-1px);
}

.btn-save-all:active:not(:disabled) {
  transform: scale(0.97);
}

.btn-save-all:disabled {
  background: #cbd5e1;
  color: #94a3b8;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-save-all.modified {
  background: #ea580c;
  animation: pulse-orange 1.8s infinite;
}

@keyframes pulse-orange {
  0% { box-shadow: 0 0 0 0 rgba(234, 88, 12, 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(234, 88, 12, 0); }
  100% { box-shadow: 0 0 0 0 rgba(234, 88, 12, 0); }
}

.kbd-hint {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 5px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 4px;
  margin-left: 4px;
}

/* 상태 알림 토스트 */
.status-toast {
  padding: 10px 20px;
  font-size: 13.5px;
  font-weight: 700;
  text-align: center;
}

.status-toast.success {
  background: #ecfdf5;
  color: #047857;
  border-bottom: 1px solid #a7f3d0;
}

.status-toast.info {
  background: #eff6ff;
  color: #1d4ed8;
  border-bottom: 1px solid #bfdbfe;
}

/* 테이블 스타일 */
.table-responsive {
  overflow-x: auto;
}

.score-input-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
}

.score-input-table th {
  padding: 12px 14px;
  background: #f1f5f9;
  color: #475569;
  font-weight: 800;
  text-align: left;
  border-bottom: 1px solid #cbd5e1;
  white-space: nowrap;
}

.score-input-table th.th-score.eng {
  color: #1d4ed8;
}

.score-input-table th.th-score.math {
  color: #7e22ce;
}

.score-input-table th.th-score.both {
  color: #047857;
}

.score-input-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.score-row:hover {
  background: #f8fafc;
}

.score-row.modified {
  background: #fffbeb;
}

.score-row.saved {
  background: #f0fdf4;
  transition: background 1.5s ease;
}

/* ========================================================
   다중 세션 대학 년도별 그룹핑 & 구분 여백 스타일
   ======================================================== */
.year-group-gap-row {
  height: 14px;
}

.td-year-gap {
  padding: 0 !important;
  height: 14px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0 !important;
  border-bottom: 1px solid #cbd5e1 !important;
  border-left: none !important;
  border-right: none !important;
}

/* 다중 세션 대학: 년도 그룹 시작 행 (상단 실선 구분) */
.score-row.is-grouped.first-in-group td {
  border-top: 1.5px solid #cbd5e1;
}

/* 다중 세션 대학: 같은 년도 내 세션 간 행 (부드러운 점선 구분) */
.score-row.is-grouped:not(.first-in-group) td {
  border-top: 1px dashed #e2e8f0;
}

/* 다중 세션 대학: 년도 그룹 마지막 행 (하단 실선 구분) */
.score-row.is-grouped.last-in-group td {
  border-bottom: 1.5px solid #cbd5e1;
}

/* 병합된 년도 헤더 셀 */
.td-year.td-year-merged {
  background: #f8fafc;
  border-right: 1.5px solid #e2e8f0 !important;
  border-left: 3.5px solid #2563eb !important; /* 좌측에 눈에 띄는 블루 포인트 악센트 */
  border-top: 1.5px solid #cbd5e1 !important;
  border-bottom: 1.5px solid #cbd5e1 !important;
  vertical-align: middle !important;
  text-align: center;
  padding: 14px 10px;
}

.year-block-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.group-session-tag {
  display: inline-block;
  font-size: 10.5px;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 4px;
  padding: 1px 5px;
  letter-spacing: -0.2px;
  margin-top: 2px;
}

.td-year {
  white-space: nowrap;
}

.year-badge {
  font-size: 12px;
  font-weight: 800;
  color: #0f172a;
  background: #e2e8f0;
  padding: 3px 7px;
  border-radius: 6px;
  margin-right: 6px;
}

.full-year {
  font-size: 13px;
  color: #64748b;
}

.td-session {
  white-space: nowrap;
}

.session-badge {
  font-size: 12px;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
}

.session-badge.sess-primary {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.session-badge.sess-secondary {
  background: #faf5ff;
  color: #7e22ce;
  border: 1px solid #e9d5ff;
}

.session-badge.sess-tertiary {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
}

.session-badge.sess-default {
  background: #f1f5f9;
  color: #475569;
}

.input-with-clear {
  display: inline-flex;
  align-items: center;
  position: relative;
}

.score-input {
  width: 75px;
  padding: 7px 8px;
  font-size: 14px;
  font-weight: 700;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  outline: none;
  text-align: right;
  padding-right: 22px;
  -moz-appearance: textfield;
}

.score-input::-webkit-outer-spin-button,
.score-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.score-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
  background: #ffffff;
}

.score-input.eng-input:focus {
  border-color: #2563eb;
}

.score-input.math-input:focus {
  border-color: #7e22ce;
  box-shadow: 0 0 0 2px rgba(126, 34, 206, 0.1);
}

.score-input.both-input:focus {
  border-color: #059669;
  box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.1);
}

.unit-text {
  position: absolute;
  right: 6px;
  font-size: 11px;
  color: #94a3b8;
  pointer-events: none;
}

.both-input-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-autosum {
  padding: 3px 6px;
  font-size: 11px;
  font-weight: 700;
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
}

.btn-autosum:hover {
  background: #d1fae5;
}

.memo-input {
  width: 100%;
  min-width: 150px;
  max-width: 260px;
  padding: 6px 10px;
  font-size: 13px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  outline: none;
}

.memo-input:focus {
  border-color: #2563eb;
  background: #ffffff;
}

.status-pill {
  display: inline-block;
  font-size: 11.5px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
}

.status-pill.saved {
  background: #dcfce7;
  color: #15803d;
}

.status-pill.unsaved {
  background: #ffedd5;
  color: #c2410c;
}

.status-pill.registered {
  background: #f1f5f9;
  color: #475569;
}

.status-pill.empty {
  background: #f8fafc;
  color: #94a3b8;
}

.td-action {
  white-space: nowrap;
}

.btn-row-save {
  padding: 6px 12px;
  font-size: 12.5px;
  font-weight: 700;
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-right: 4px;
}

.btn-row-save:hover {
  background: #e2e8f0;
}

.btn-row-save.active {
  background: #ea580c;
  color: #ffffff;
  border-color: #ea580c;
}

.btn-row-clear {
  padding: 6px 8px;
  font-size: 12px;
  color: #ef4444;
  background: transparent;
  border: 1px solid #fecaca;
  border-radius: 6px;
  cursor: pointer;
}

.btn-row-clear:hover {
  background: #fee2e2;
}

/* 하단 툴바 */
.card-footer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 20px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.footer-left-info {
  font-size: 13.5px;
  color: #475569;
}

.footer-left-info strong {
  color: #0f172a;
}

.unsaved-warning {
  color: #ea580c;
  font-weight: 700;
}

/* 5. 빈 상태 가이드 */
.empty-guide-card {
  padding: 60px 20px;
  background: #ffffff;
  border-radius: 14px;
  border: 1px dashed #cbd5e1;
  text-align: center;
}

.guide-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  margin-bottom: 12px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.spin {
  animation: spin 1s linear infinite;
  display: inline-block;
}

.empty-guide-card h3 {
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.empty-guide-card p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .student-select-card {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
  }
}

/* ========================================================
   엑셀 일괄 다운로드/업로드 버튼 & 모달 스타일
   ======================================================== */
.excel-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.btn-excel-template {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-excel-template:hover {
  background: #dcfce7;
  border-color: #86efac;
}

.btn-excel-upload {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 700;
  background: #2563eb;
  color: #ffffff;
  border: 1px solid #2563eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.2);
}

.btn-excel-upload:hover {
  background: #1d4ed8;
}

/* 모달 */
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-card {
  background: #ffffff;
  border-radius: 16px;
  max-width: 580px;
  width: 100%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #94a3b8;
  cursor: pointer;
  line-height: 1;
}

.modal-close-btn:hover {
  color: #0f172a;
}

.modal-body {
  padding: 24px;
}

.excel-guide-banner {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 18px;
}

.banner-title {
  margin: 0 0 6px 0;
  font-size: 13.5px;
  color: #1e40af;
}

.banner-desc {
  margin: 0;
  font-size: 12.5px;
  color: #3b82f6;
  line-height: 1.6;
}

.upload-field-row {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  margin-bottom: 6px;
}

.modal-student-select {
  width: 100%;
  padding: 8px 12px;
  font-size: 13.5px;
  font-weight: 600;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  outline: none;
}

.file-picker-box {
  margin-top: 10px;
}

.file-hidden-input {
  display: none;
}

.file-picker-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28px 16px;
  background: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-picker-label:hover {
  background: #f1f5f9;
  border-color: #2563eb;
}

.upload-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.upload-prompt {
  font-size: 13.5px;
  font-weight: 700;
  color: #475569;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
}

.btn-modal-sub {
  padding: 8px 12px;
  font-size: 12.5px;
  font-weight: 700;
  color: #16a34a;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  cursor: pointer;
}

.modal-right-btns {
  display: flex;
  gap: 8px;
}

.btn-modal-cancel {
  padding: 8px 16px;
  font-size: 13.5px;
  font-weight: 700;
  color: #64748b;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  cursor: pointer;
}

.btn-modal-submit {
  padding: 8px 18px;
  font-size: 13.5px;
  font-weight: 800;
  color: #ffffff;
  background: #2563eb;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.btn-modal-submit:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-modal-submit:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>

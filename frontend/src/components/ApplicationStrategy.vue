<template>
  <div class="strategy-container">
    <!-- 상단 헤더 & 모드 전환 탭 -->
    <div class="header-card">
      <div class="header-left">
        <h2>2026학년도 편입학 원서 지원 관리</h2>
        <p class="sub-desc">학교별 모집요강 전체 현황 및 학생별 빠른 원서 담기</p>
      </div>

      <div class="header-right-actions">
        <!-- 모집요강 엑셀 업로드 버튼 -->
        <button @click="showQuotaModal = true" class="btn-upload-quota">
          📂 모집요강 엑셀 등록
        </button>

        <div class="tab-controls">
          <button
            :class="['tab-btn', currentTab === 'univ' ? 'active' : '']"
            @click="currentTab = 'univ'"
          >
            🏫 학교별 모집요강
          </button>
          <button
            :class="['tab-btn', currentTab === 'student' ? 'active' : '']"
            @click="currentTab = 'student'"
          >
            👤 학생별 지원 현황
          </button>
        </div>
      </div>
    </div>

    <!-- 모집요강 엑셀 업로드 모달 -->
    <div v-if="showQuotaModal" class="modal-backdrop" @click.self="showQuotaModal = false">
      <div class="modal-box">
        <div class="modal-header">
          <h3>📊 대학별 모집요강 엑셀 일괄 업로드</h3>
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

    <!-- ================================================================= -->
    <!-- 탭 1: 학교별 모집요강 현황판 (종합 상황판) -->
    <!-- ================================================================= -->
    <div v-if="currentTab === 'univ'" class="content-section">
      <div class="filter-toolbar">
        <div class="univ-selector">
          <label>조회 대학:</label>
          <select v-model="selectedUniv" @change="fetchUnivDepartments" class="select-box">
            <option v-for="u in univList" :key="u" :value="u">{{ u }}</option>
          </select>
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

      <div class="table-wrapper">
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
    </div>

    <!-- ================================================================= -->
    <!-- 탭 2: 학생별 지원 현황 및 빠른 담기 (개선된 1클릭 UI) -->
    <!-- ================================================================= -->
    <div v-if="currentTab === 'student'" class="content-section">
      <!-- 상단 학생 빠른 탐색 & 선택 바 -->
      <div class="student-quick-bar">
        <div class="student-bar-top">
          <div class="student-nav-group">
            <button @click="moveStudent(-1)" class="nav-arrow-btn" title="이전 학생">◀</button>
            <select v-model="selectedStudent" @change="fetchStudentApplications" class="select-box student-select">
              <option v-for="s in studentList" :key="s" :value="s">{{ s }}</option>
            </select>
            <button @click="moveStudent(1)" class="nav-arrow-btn" title="다음 학생">▶</button>
          </div>

          <div class="student-search-wrap">
            <input
              v-model="studentSearch"
              type="text"
              placeholder="학생 이름 빠른 검색..."
              class="quick-input"
            />
            <button v-if="studentSearch" @click="studentSearch = ''" class="input-clear-btn">✕</button>
          </div>

          <span class="stat-badge count">담긴 원서: {{ studentApplications.length }}개교</span>
        </div>

        <!-- 가로 스크롤 학생 칩 목록 -->
        <div class="student-chip-strip">
          <button
            v-for="s in filteredStudentList"
            :key="s"
            :class="['stu-chip', { active: selectedStudent === s }]"
            @click="selectStudent(s)"
          >
            {{ s }}
          </button>
        </div>
      </div>

      <!-- 좌우 2단 빠른 담기 작업대 -->
      <div class="fast-basket-layout">
        <!-- 좌측: 대학 칩 + 학과 실시간 필터 + 1클릭 토글 -->
        <div class="panel picker-panel">
          <div class="panel-header">
            <h3 class="panel-title">⚡ 빠른 대학 · 학과 선택</h3>
            <span class="guide-hint">학과를 클릭하면 즉시 담기/취소됩니다</span>
          </div>

          <!-- 1. 대학 빠른 선택 칩 그리드 -->
          <div class="univ-chip-box">
            <button
              v-for="u in univList"
              :key="u"
              :class="[
                'univ-chip',
                { active: formUniv === u, applied: appliedUnivSet.has(u) }
              ]"
              @click="selectFormUniv(u)"
            >
              <span>{{ u }}</span>
              <span v-if="appliedUnivSet.has(u)" class="applied-dot">●</span>
            </button>
          </div>

          <!-- 2. 학과 검색창 & 계열 필터 -->
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

          <!-- 3. 학과 1클릭 선택 리스트 -->
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
                <span class="quota-mini">일반 {{ d.gen }} / 학사 {{ d.bac }}</span>
                <span v-if="d.past_admissions && d.past_admissions.length > 0" class="past-mini">
                  합격 {{ d.past_admissions.length }}
                </span>
                <span :class="['pick-status-btn', { active: isMajorApplied(d.univ, d.major) }]">
                  {{ isMajorApplied(d.univ, d.major) ? '담김 ✓' : '+ 담기' }}
                </span>
              </div>
            </div>

            <div v-if="filteredFormMajors.length === 0" class="empty-list-box">
              조건에 맞는 학과가 없습니다.
            </div>
          </div>
        </div>

        <!-- 우측: 담긴 지원 대학 리스트 -->
        <div class="panel list-panel">
          <div class="panel-header">
            <h3 class="panel-title">📋 {{ selectedStudent }} 학생 지원 희망 리스트</h3>
            <span class="count-tag">총 {{ studentApplications.length }}개교</span>
          </div>

          <div v-if="studentApplications.length === 0" class="empty-list-box">
            아직 추가된 지원 대학이 없습니다.<br>좌측에서 대학과 학과를 클릭해 바로 담아보세요.
          </div>

          <div v-else class="application-cards">
            <div
              v-for="(app, idx) in studentApplications"
              :key="app.id"
              class="app-card"
            >
              <div class="card-num">{{ idx + 1 }}</div>
              <div class="card-content" @click="jumpToFormUniv(app.univ)" title="클릭하면 좌측에서 해당 대학 열기">
                <div class="card-univ">{{ app.univ }}</div>
                <div class="card-major">{{ app.major }}</div>
                <div class="card-meta">
                  <span>선발정원: 일반 {{ app.gen_quota }}명 / 학사 {{ app.bac_quota }}명</span>
                </div>
              </div>
              <button @click="handleRemoveApplication(app.id)" class="btn-remove" title="삭제">
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'

const currentTab = ref('univ')

const API_BASE = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? 'http://127.0.0.1:8000'
  : 'https://peer-score-finder.onrender.com'

// 1. 대학 목록 및 학과 현황 상태
const univList = ref([])
const selectedUniv = ref('가천대학교')
const deptFilter = ref('ALL')
const departmentRows = ref([])

// 2. 학생 목록 및 빠른 검색 상태
const studentList = ref([])
const studentSearch = ref('')
const selectedStudent = ref('')
const studentApplications = ref([])

// 3. 빠른 담기 패널 상태
const formUniv = ref('가천대학교')
const formMajorList = ref([])
const majorKeyword = ref('')
const formDeptFilter = ref('ALL')
const majorSearchInput = ref(null)
const isSavingApp = ref(false)

// 4. 모집요강 엑셀 업로드 모달 상태
const showQuotaModal = ref(false)
const quotaFileInput = ref(null)
const isUploadingQuota = ref(false)

// 탭 1 필터링된 학과 목록
const filteredDepartments = computed(() => {
  return departmentRows.value.filter(d => {
    return deptFilter.value === 'ALL' || d.dept === deptFilter.value
  })
})

// 탭 2 학생 검색 필터링
const filteredStudentList = computed(() => {
  const kw = studentSearch.value.trim()
  if (!kw) return studentList.value
  return studentList.value.filter(s => s.includes(kw))
})

// 탭 2 학과 검색 및 계열 필터링
const filteredFormMajors = computed(() => {
  const kw = majorKeyword.value.trim().toLowerCase()
  return formMajorList.value.filter(d => {
    const matchDept = formDeptFilter.value === 'ALL' || d.dept === formDeptFilter.value
    const matchKw = !kw || d.major.toLowerCase().includes(kw)
    return matchDept && matchKw
  })
})

// 이미 지원한 대학 Set (대학 칩 강조용)
const appliedUnivSet = computed(() => new Set(studentApplications.value.map(a => a.univ)))

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

// 0. 재원생 명단 불러오기
async function fetchAllowedStudents() {
  try {
    const res = await fetch(`${API_BASE}/all-students-2026`)
    const data = await res.json()
    if (Array.isArray(data) && data.length > 0) {
      studentList.value = data
      selectedStudent.value = data[0]
      await fetchStudentApplications()
    }
  } catch (err) {
    console.error('학생 명단 로드 실패:', err)
  }
}

async function selectStudent(name) {
  selectedStudent.value = name
  await fetchStudentApplications()
}

function moveStudent(step) {
  if (!studentList.value.length) return
  const idx = studentList.value.indexOf(selectedStudent.value)
  const nextIdx = (idx + step + studentList.value.length) % studentList.value.length
  selectStudent(studentList.value[nextIdx])
}

// 1. 등록된 대학 목록 조회
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
      await fetchUnivDepartments()
      await fetchFormMajors()
    }
  } catch (err) {
    console.error('대학 목록 조회 실패:', err)
  }
}

// 2. 탭 1 선택 대학의 학과 및 지원자 현황 조회
async function fetchUnivDepartments() {
  try {
    const res = await fetch(`${API_BASE}/api/quota/departments?univ=${encodeURIComponent(selectedUniv.value)}`)
    departmentRows.value = await res.json()
  } catch (err) {
    console.error('학과 정원 조회 실패:', err)
  }
}

// 3. 탭 2 대학 선택 및 학과 리스트 조회
async function selectFormUniv(univ) {
  formUniv.value = univ
  majorKeyword.value = ''
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

async function fetchFormMajors() {
  try {
    const res = await fetch(`${API_BASE}/api/quota/departments?univ=${encodeURIComponent(formUniv.value)}`)
    formMajorList.value = await res.json()
  } catch (err) {
    console.error('폼 학과 조회 실패:', err)
  }
}

// 4. 특정 학생의 원서 리스트 조회
async function fetchStudentApplications() {
  if (!selectedStudent.value) return
  try {
    const res = await fetch(`${API_BASE}/api/applications?student_name=${encodeURIComponent(selectedStudent.value)}`)
    studentApplications.value = await res.json()
  } catch (err) {
    console.error('학생 원서 목록 조회 실패:', err)
  }
}

// 5. 1클릭 즉시 담기 / 이미 담긴 학과면 삭제 토글
async function toggleApplication(deptItem) {
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
      await fetchStudentApplications()
      await fetchUnivDepartments()
    }
  } catch (err) {
    console.error('원서 추가 실패:', err)
  } finally {
    isSavingApp.value = false
  }
}

// 6. 원서 삭제
async function handleRemoveApplication(appId) {
  if (isSavingApp.value) return
  isSavingApp.value = true
  try {
    const res = await fetch(`${API_BASE}/api/applications/${appId}`, { method: 'DELETE' })
    if (res.ok) {
      await fetchStudentApplications()
      await fetchUnivDepartments()
    }
  } catch (err) {
    console.error('원서 삭제 실패:', err)
  } finally {
    isSavingApp.value = false
  }
}

// 7. 모집요강 엑셀 업로드 처리
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

onMounted(async () => {
  await fetchAllowedStudents()
  await fetchUnivList()
})
</script>

<style scoped>
.strategy-container {
  max-width: 1280px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", Roboto, sans-serif;
  color: #1e293b;
}

.header-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  padding: 18px 24px;
  margin-bottom: 18px;
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
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  background: #f8fafc;
  color: #334155;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
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

/* 모달 스타일 */
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

.modal-box {
  background: #ffffff;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0,0,0,0.15);
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 { margin: 0; font-size: 16px; font-weight: 700; }
.close-btn { background: none; border: none; font-size: 22px; color: #94a3b8; cursor: pointer; }
.modal-body { padding: 20px; }
.guide-text { font-size: 13px; color: #475569; line-height: 1.5; margin-top: 0; }
.guide-text code { background: #f1f5f9; padding: 2px 5px; border-radius: 4px; color: #0f172a; }

.sample-table-wrap { margin: 12px 0 16px 0; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; }
.sample-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; }
.sample-table th { background: #f8fafc; padding: 6px; border-bottom: 1px solid #e2e8f0; color: #475569; }
.sample-table td { padding: 6px; border-bottom: 1px solid #f1f5f9; color: #334155; }

.file-input { width: 100%; padding: 8px; border: 1px dashed #cbd5e1; border-radius: 6px; font-size: 13px; }
.modal-footer { padding: 14px 20px; background: #f8fafc; border-top: 1px solid #e2e8f0; display: flex; justify-content: flex-end; gap: 8px; }
.btn-cancel { padding: 7px 14px; border: 1px solid #cbd5e1; background: #fff; border-radius: 6px; font-size: 13px; cursor: pointer; }
.btn-submit { padding: 7px 16px; border: none; background: #2563eb; color: #fff; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-submit:disabled { background: #94a3b8; }

.filter-toolbar {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 18px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.univ-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
}

.select-box {
  padding: 6px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1d4ed8;
  outline: none;
  background: #f8fafc;
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

.table-wrapper {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
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

.count-summary-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
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

/* ================================================================= */
/* 탭 2: 개선된 빠른 학생별 원서 담기 스타일 */
/* ================================================================= */
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

.student-nav-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

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
.nav-arrow-btn:hover { background: #e2e8f0; }

.student-select {
  min-width: 125px;
  height: 32px;
}

.student-search-wrap {
  position: relative;
  flex: 1;
  max-width: 240px;
}

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

.student-chip-strip {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.stu-chip {
  padding: 5px 11px;
  font-size: 12.5px;
  font-weight: 600;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #475569;
  border-radius: 999px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.12s;
}
.stu-chip:hover { border-color: #94a3b8; color: #0f172a; }
.stu-chip.active {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

/* 좌우 2단 작업 레이아웃 */
.fast-basket-layout {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 18px;
  align-items: start;
}

.panel {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 18px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 10px;
  margin-bottom: 14px;
}

.panel-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.guide-hint {
  font-size: 11.5px;
  color: #64748b;
}

.count-tag {
  font-size: 12.5px;
  font-weight: 700;
  color: #2563eb;
}

/* 대학 칩 그리드 */
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
  margin-bottom: 12px;
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
.univ-chip.applied {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #1d4ed8;
}
.univ-chip.active {
  background: #0f172a;
  color: #ffffff;
  border-color: #0f172a;
}
.univ-chip.active.applied {
  background: #1d4ed8;
  border-color: #1d4ed8;
  color: #ffffff;
}
.applied-dot { font-size: 8px; }

/* 학과 검색 및 계열 미니 탭 */
.major-filter-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.major-search-wrap {
  position: relative;
  flex: 1;
}

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

.mini-dept-tabs {
  display: flex;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 8px;
  gap: 2px;
}

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
.mini-tab.active {
  background: #ffffff;
  color: #0f172a;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}

/* 학과 1클릭 선택 리스트 */
.quick-major-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 2px;
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
  transition: all 0.12s;
  gap: 10px;
}
.major-pick-row:hover {
  background: #f8fafc;
  border-color: #94a3b8;
}
.major-pick-row.selected {
  background: #eff6ff;
  border-color: #3b82f6;
}

.major-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.dept-pill {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}
.dept-pill.nat { background: #f3e8ff; color: #7e22ce; }
.dept-pill.hum { background: #fef3c7; color: #92400e; }

.major-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #0f172a;
}

.major-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.quota-mini {
  font-size: 11.5px;
  color: #64748b;
}

.past-mini {
  font-size: 11px;
  font-weight: 600;
  color: #0284c7;
  background: #e0f2fe;
  padding: 2px 6px;
  border-radius: 4px;
}

.pick-status-btn {
  font-size: 11.5px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
}
.pick-status-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

/* 우측 바구니 카드 */
.empty-list-box {
  padding: 40px 20px;
  text-align: center;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.6;
}

.application-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 640px;
  overflow-y: auto;
}

.app-card {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  gap: 12px;
  transition: border-color 0.12s;
}
.app-card:hover { border-color: #2563eb; }

.card-num {
  font-size: 14px;
  font-weight: 800;
  color: #2563eb;
  width: 20px;
  text-align: center;
}

.card-content {
  flex: 1;
  cursor: pointer;
}

.card-univ {
  font-size: 12px;
  font-weight: 700;
  color: #2563eb;
}

.card-major {
  font-size: 14.5px;
  font-weight: 700;
  color: #0f172a;
  margin: 2px 0;
}

.card-meta {
  font-size: 11.5px;
  color: #64748b;
}

.btn-remove {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: #fee2e2;
  color: #dc2626;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}
.btn-remove:hover { background: #fecaca; }

@media (max-width: 900px) {
  .fast-basket-layout {
    grid-template-columns: 1fr;
  }
}
</style>
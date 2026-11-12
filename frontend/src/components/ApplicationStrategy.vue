<template>
  <div class="strategy-container">
    <!-- 상단 헤더 & 모드 전환 탭 -->
    <div class="header-card">
      <div class="header-left">
        <h2>2026학년도 편입학 원서 지원 관리</h2>
        <p class="sub-desc">학교별 모집요강 전체 현황</p>
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
            🏫 학교별 모집요강 현황판
          </button>
          <button
            :class="['tab-btn', currentTab === 'student' ? 'active' : '']"
            @click="currentTab = 'student'"
          >
            👤 학생별 지원 현황 및 담기
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
              <th style="width: 75px;" class="text-center">계열</th>
              <th style="width: 220px;">모집단위 (학과명)</th>
              <th style="width: 85px;" class="text-center">일반 정원</th>
              <th style="width: 85px;" class="text-center">학사 정원</th>
              <th>원내 지원 희망자 명단 (모의고사 성적)</th>
              <th style="width: 155px;" class="text-center">지원 인원</th>
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
                      영{{ app.eng }} <template v-if="app.math">/ 수{{ app.math }}</template>
                    </span>
                  </div>
                </div>
              </td>
              <!-- 변경된 지원 인원수 표시 컬럼 -->
              <td class="text-center">
                <div v-if="dept.applicants && dept.applicants.length > 0" class="count-summary-cell">
                  <span class="total-app-badge">총 {{ dept.applicants.length }}명</span>
                  <span class="sub-app-detail">
                    (일반 {{ getGenCount(dept) }} / 학사 {{ getBacCount(dept) }})
                  </span>
                </div>
                <span v-else class="zero-app-text">0명</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- 탭 2: 학생별 지원 현황 및 담기 (1:1 상담용) -->
    <!-- ================================================================= -->
    <div v-if="currentTab === 'student'" class="content-section">
      <div class="student-select-card">
        <div class="input-inline">
          <label>상담 학생 선택 (2026 재원생):</label>
          <select v-model="selectedStudent" @change="fetchStudentApplications" class="select-box student-select">
            <option v-for="s in studentList" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>

        <div class="student-stat-badges">
          <span class="stat-badge count">담긴 원서: {{ studentApplications.length }}개교</span>
        </div>
      </div>

      <div class="basket-layout">
        <!-- 좌측: 원서 추가 폼 -->
        <div class="panel add-form-panel">
          <h3 class="panel-title">➕ 새 지원 카드 추가</h3>

          <div class="form-group">
            <label>1. 목표 대학</label>
            <select v-model="formUniv" @change="onFormUnivChange" class="form-control">
              <option v-for="u in univList" :key="u" :value="u">{{ u }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>2. 지원 희망 학과</label>
            <select v-model="formMajor" class="form-control">
              <option disabled value="">학과를 선택하세요</option>
              <option
                v-for="d in formMajorList"
                :key="d.id"
                :value="d.major"
              >
                {{ d.major }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>3. 지원 성향 메모</label>
            <div class="radio-chips">
              <label :class="['chip', formStrategy === '안정' ? 'selected' : '']">
                <input type="radio" value="안정" v-model="formStrategy" /> 안정
              </label>
              <label :class="['chip', formStrategy === '적정' ? 'selected' : '']">
                <input type="radio" value="적정" v-model="formStrategy" /> 적정
              </label>
              <label :class="['chip', formStrategy === '상향' ? 'selected' : '']">
                <input type="radio" value="상향" v-model="formStrategy" /> 상향
              </label>
            </div>
          </div>

          <button @click="handleAddApplication" class="btn-primary-add">
            원서 목록에 추가
          </button>
        </div>

        <!-- 우측: 담긴 지원 대학 리스트 -->
        <div class="panel list-panel">
          <div class="panel-header">
            <h3 class="panel-title">📋 {{ selectedStudent }} 학생 지원 희망 리스트</h3>
            <span class="count-tag">총 {{ studentApplications.length }}장</span>
          </div>

          <div v-if="studentApplications.length === 0" class="empty-list-box">
            아직 추가된 지원 대학이 없습니다. 좌측에서 대학과 학과를 선택해 담아주세요.
          </div>

          <div v-else class="application-cards">
            <div
              v-for="(app, idx) in studentApplications"
              :key="app.id"
              class="app-card"
            >
              <div class="card-num">{{ idx + 1 }}</div>
              <div class="card-content">
                <div class="card-univ">{{ app.univ }}</div>
                <div class="card-major">{{ app.major }}</div>
                <div class="card-meta">
                  <span>선발정원: 일반 {{ app.gen_quota }}명 / 학사 {{ app.bac_quota }}명</span>
                  <span :class="['strategy-badge', getStrategyClass(app.memo)]">{{ app.memo }}</span>
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
import { ref, computed, onMounted } from 'vue'

const currentTab = ref('univ')

// 로컬 테스트 및 배포 주소 자동 대응 (App.vue와 동일하게 맞추어 사용)
// const API_BASE = 'http://127.0.0.1:8000'
const API_BASE = 'https://peer-score-finder.onrender.com'

// 1. 대학 목록 및 학과 현황 상태
const univList = ref([])
const selectedUniv = ref('가천대학교')
const deptFilter = ref('ALL')
const departmentRows = ref([])

// 2. 학생 목록 (백엔드 ALLOWED_STUDENTS에서 자동 로드)
const studentList = ref([])
const selectedStudent = ref('')
const studentApplications = ref([])

// 3. 입력 폼 상태
const formUniv = ref('가천대학교')
const formMajorList = ref([])
const formMajor = ref('')
const formStrategy = ref('적정')

// 4. 모집요강 엑셀 업로드 모달 상태
const showQuotaModal = ref(false)
const quotaFileInput = ref(null)
const isUploadingQuota = ref(false)

// 필터링된 학과 목록
const filteredDepartments = computed(() => {
  return departmentRows.value.filter(d => {
    return deptFilter.value === 'ALL' || d.dept === deptFilter.value
  })
})

// 일반 / 학사 지원 인원 카운트 헬퍼
function getGenCount(dept) {
  if (!dept.applicants) return 0
  return dept.applicants.filter(a => a.type === '일반').length
}

function getBacCount(dept) {
  if (!dept.applicants) return 0
  return dept.applicants.filter(a => a.type === '학사').length
}

// 0. ALLOWED_STUDENTS 기반 학생 명단 불러오기
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

// 2. 선택 대학의 학과 및 지원자 현황 조회
async function fetchUnivDepartments() {
  try {
    const res = await fetch(`${API_BASE}/api/quota/departments?univ=${encodeURIComponent(selectedUniv.value)}`)
    departmentRows.value = await res.json()
  } catch (err) {
    console.error('학과 정원 조회 실패:', err)
  }
}

// 3. 폼용 특정 대학 학과 리스트 조회
async function fetchFormMajors() {
  try {
    const res = await fetch(`${API_BASE}/api/quota/departments?univ=${encodeURIComponent(formUniv.value)}`)
    formMajorList.value = await res.json()
    formMajor.value = ''
  } catch (err) {
    console.error('폼 학과 조회 실패:', err)
  }
}

function onFormUnivChange() {
  fetchFormMajors()
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

// 5. 원서 추가
async function handleAddApplication() {
  if (!formMajor.value) {
    alert('지원 학과를 선택해 주세요.')
    return
  }

  try {
    const res = await fetch(`${API_BASE}/api/applications`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_name: selectedStudent.value,
        univ: formUniv.value,
        major: formMajor.value,
        memo: formStrategy.value
      })
    })

    if (res.ok) {
      formMajor.value = ''
      await fetchStudentApplications()
      await fetchUnivDepartments()
    }
  } catch (err) {
    console.error('원서 추가 실패:', err)
  }
}

// 6. 원서 삭제
async function handleRemoveApplication(appId) {
  try {
    const res = await fetch(`${API_BASE}/api/applications/${appId}`, { method: 'DELETE' })
    if (res.ok) {
      await fetchStudentApplications()
      await fetchUnivDepartments()
    }
  } catch (err) {
    console.error('원서 삭제 실패:', err)
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

function getStrategyClass(memo) {
  if (memo === '안정') return 'strategy-safe'
  if (memo === '적정') return 'strategy-fit'
  return 'strategy-high'
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

/* 지원 인원수 셀 스타일 */
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
.sub-app-detail {
  font-size: 11px;
  color: #64748b;
}
.zero-app-text {
  font-size: 12px;
  color: #94a3b8;
}

/* 탭 2 스타일 */
.student-select-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stat-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 600;
  background: #f1f5f9;
  color: #334155;
}

.basket-layout { display: grid; grid-template-columns: 340px 1fr; gap: 20px; }
.panel { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; }
.panel-title { font-size: 15px; font-weight: 700; color: #0f172a; margin: 0 0 16px 0; }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 12px;
  margin-bottom: 16px;
}
.count-tag { font-size: 12px; font-weight: bold; color: #2563eb; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 6px; }
.form-control {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: #f8fafc;
  box-sizing: border-box;
}
.radio-chips { display: flex; gap: 8px; }
.chip {
  flex: 1;
  text-align: center;
  padding: 7px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
}
.chip input { display: none; }
.chip.selected { background: #eff6ff; border-color: #3b82f6; color: #1d4ed8; }
.btn-primary-add {
  width: 100%;
  padding: 9px;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  margin-top: 6px;
}
.btn-primary-add:hover { background: #1d4ed8; }
.empty-list-box { padding: 40px; text-align: center; font-size: 13px; color: #94a3b8; }
.application-cards { display: flex; flex-direction: column; gap: 10px; }
.app-card {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  gap: 12px;
}
.card-num { font-size: 14px; font-weight: 700; color: #2563eb; width: 20px; }
.card-content { flex: 1; }
.card-univ { font-size: 12px; font-weight: 600; color: #64748b; }
.card-major { font-size: 14px; font-weight: 700; color: #0f172a; }
.card-meta { font-size: 11px; color: #64748b; display: flex; align-items: center; gap: 8px; margin-top: 2px; }
.strategy-badge { font-size: 10px; font-weight: bold; padding: 1px 6px; border-radius: 4px; }
.strategy-safe { background: #dcfce7; color: #166534; }
.strategy-fit { background: #e0f2fe; color: #075985; }
.strategy-high { background: #f3e8ff; color: #6b21a8; }
.btn-remove { border: none; background: transparent; color: #94a3b8; font-size: 14px; cursor: pointer; }
.btn-remove:hover { color: #ef4444; }
</style>
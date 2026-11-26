<template>
  <div class="results-board-container">
    <!-- 1. 상단 타이틀 & 뷰 전환 헤더 -->
    <div class="board-header-card">
      <div class="board-title-group">
        <h2 class="board-title">
          <span>2026학년도 편입 전형 결과 및 합격 현황판</span>
          <span class="board-title-badge">실시간 동기화</span>
        </h2>
        <p class="board-subtitle">
          지원 학생들의 1차 합격 여부, 예비번호 변동, 최초/추가 합격 및 최종 진학 등록을 한 화면에서 일괄 관리합니다.
        </p>
      </div>

      <div class="board-actions">
        <!-- 보기 모드 전환 탭 (플랫 테이블 vs 학생별 묶어보기) -->
        <div class="view-mode-toggle">
          <button
            :class="['view-toggle-btn', viewMode === 'table' ? 'active' : '']"
            @click="viewMode = 'table'"
            title="스프레드시트형 전체 표로 보기"
          >
            <Table :size="15" :stroke-width="2" />
            <span>전체 표 (테이블)</span>
          </button>
          <button
            :class="['view-toggle-btn', viewMode === 'grouped' ? 'active' : '']"
            @click="viewMode = 'grouped'"
            title="학생별 지원 대학 묶어서 보기"
          >
            <Users :size="15" :stroke-width="2" />
            <span>학생별 묶어보기</span>
          </button>
        </div>

        <button @click="loadData" class="btn-refresh" :disabled="loading" title="최신 상태 새로고침">
          <RotateCw :size="14" :class="{ 'spin': loading }" :stroke-width="2" />
          <span>새로고침</span>
        </button>
      </div>
    </div>

    <!-- 2. 핵심 통계 대시보드 카드 그리드 -->
    <div class="stats-grid">
      <div class="stat-card total">
        <div class="stat-icon">
          <Bookmark :size="20" :stroke-width="2" />
        </div>
        <div class="stat-info">
          <span class="stat-label">총 지원 건수</span>
          <span class="stat-val">{{ stats.total_applications }}건</span>
          <span class="stat-sub">{{ stats.unique_students }}명 지원 중</span>
        </div>
      </div>

      <div class="stat-card stage1">
        <div class="stat-icon">
          <CheckCircle2 :size="20" :stroke-width="2" />
        </div>
        <div class="stat-info">
          <span class="stat-label">1차 합격</span>
          <span class="stat-val">{{ stats.stage1_pass }}건</span>
          <span class="stat-sub">서류/면접 대상</span>
        </div>
      </div>

      <div class="stat-card initial">
        <div class="stat-icon">
          <Award :size="20" :stroke-width="2" />
        </div>
        <div class="stat-info">
          <span class="stat-label">최초 합격</span>
          <span class="stat-val">{{ stats.final_initial }}건</span>
          <span class="stat-sub">정규 합격</span>
        </div>
      </div>

      <div class="stat-card reserve">
        <div class="stat-icon">
          <Clock :size="20" :stroke-width="2" />
        </div>
        <div class="stat-info">
          <span class="stat-label">예비 대기</span>
          <span class="stat-val">{{ stats.final_reserve }}건</span>
          <span class="stat-sub">충원 대기중</span>
        </div>
      </div>

      <div class="stat-card added">
        <div class="stat-icon">
          <Sparkles :size="20" :stroke-width="2" />
        </div>
        <div class="stat-info">
          <span class="stat-label">추가 합격</span>
          <span class="stat-val">{{ stats.final_added }}건</span>
          <span class="stat-sub">전화/차수 추합</span>
        </div>
      </div>

      <div class="stat-card enrolled">
        <div class="stat-icon">
          <GraduationCap :size="20" :stroke-width="2" />
        </div>
        <div class="stat-info">
          <span class="stat-label">최종 진학 등록</span>
          <span class="stat-val">{{ stats.enrolled }}명</span>
          <span class="stat-sub">진학 확정</span>
        </div>
      </div>
    </div>

    <!-- 3. 검색 및 필터 툴바 -->
    <div class="filter-toolbar">
      <div class="search-box">
        <Search :size="16" :stroke-width="2" color="#64748b" />
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="학생 이름, 지원 대학, 학과명 검색..."
        />
      </div>

      <div class="filter-group">
        <!-- 계열 필터 -->
        <select v-model="filterDept" class="filter-select">
          <option value="ALL">전체 계열</option>
          <option value="자연">자연계열</option>
          <option value="인문">인문계열</option>
        </select>

        <!-- 1차 결과 필터 -->
        <select v-model="filterStage1" class="filter-select">
          <option value="ALL">1차 결과: 전체</option>
          <option value="대기">1차 대기</option>
          <option value="합격">1차 합격</option>
          <option value="불합격">1차 불합격</option>
          <option value="해당없음">1차 해당없음</option>
        </select>

        <!-- 최종 결과 필터 -->
        <select v-model="filterFinal" class="filter-select">
          <option value="ALL">최종 결과: 전체</option>
          <option value="대기">최종 대기</option>
          <option value="최초합">최초합</option>
          <option value="예비">예비대기</option>
          <option value="추가합">추가합</option>
          <option value="불합격">불합격</option>
          <option value="ENROLLED">최종 등록생만</option>
        </select>
      </div>
    </div>

    <!-- 4. [모드 A] 스프레드시트형 전체 플랫 테이블 뷰 -->
    <div v-if="viewMode === 'table'" class="table-card">
      <div class="results-table-wrap">
        <table class="results-table">
          <thead>
            <tr>
              <th style="width: 140px;">학생명 (계열)</th>
              <th style="width: 150px;">지원 대학</th>
              <th>지원 학과</th>
              <th style="width: 80px; text-align: center;">전략</th>
              <th style="width: 110px; text-align: center;">1차 전형</th>
              <th style="width: 130px; text-align: center;">최종 전형</th>
              <th style="width: 100px; text-align: center;">예비 번호</th>
              <th style="width: 100px; text-align: center;">최종 등록</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredApplications.length === 0">
              <td colspan="8" class="empty-state">
                <Inbox :size="32" :stroke-width="1.5" />
                <p>일치하는 지원 및 결과 내역이 없습니다.</p>
              </td>
            </tr>

            <tr
              v-for="app in filteredApplications"
              :key="app.id"
              :class="{ 'row-enrolled': app.is_enrolled }"
            >
              <!-- 학생명 & 계열 -->
              <td>
                <div class="student-cell">
                  <span class="student-name-text">{{ app.student_name }}</span>
                  <span
                    :class="['dept-badge', app.department && app.department.includes('자연') ? 'natural' : 'human']"
                  >
                    {{ app.department && app.department.includes('자연') ? '자연' : (app.department && app.department.includes('인문') ? '인문' : '미기재') }}
                  </span>
                </div>
              </td>

              <!-- 대학 -->
              <td>
                <span class="univ-text">{{ app.univ }}</span>
              </td>

              <!-- 학과 -->
              <td>
                <span class="major-text">{{ app.major }}</span>
              </td>

              <!-- 전략 메모 -->
              <td style="text-align: center;">
                <span class="memo-tag">{{ app.memo || '적정' }}</span>
              </td>

              <!-- 1차 결과 (원클릭 순환 토글 버튼) -->
              <td style="text-align: center;">
                <button
                  :class="['stage1-toggle-btn', app.stage1_result || '대기']"
                  @click="toggleStage1(app)"
                  :title="'클릭하여 1차 결과 변경 (현재: ' + (app.stage1_result || '대기') + ')'"
                >
                  {{ formatStage1(app.stage1_result) }}
                </button>
              </td>

              <!-- 최종 결과 (드롭다운 빠른 선택) -->
              <td style="text-align: center;">
                <select
                  v-model="app.final_result"
                  :class="['final-result-select', app.final_result || '대기']"
                  @change="onFinalResultChange(app)"
                >
                  <option value="대기">대기</option>
                  <option value="최초합">최초합 🎉</option>
                  <option value="예비">예비 ⏳</option>
                  <option value="추가합">추가합 🎊</option>
                  <option value="불합격">불합격 ⚪</option>
                </select>
              </td>

              <!-- 예비 번호 인라인 입력 -->
              <td style="text-align: center;">
                <div class="waitlist-wrap" v-if="app.final_result === '예비' || app.final_result === '추가합' || app.waitlist_no">
                  <input
                    type="number"
                    min="1"
                    max="999"
                    v-model.number="app.waitlist_no"
                    @change="updateResult(app)"
                    @keyup.enter="$event.target.blur()"
                    placeholder="번호"
                    class="waitlist-input"
                  />
                  <span class="waitlist-unit">번</span>
                </div>
                <span v-else style="color: #cbd5e1;">-</span>
              </td>

              <!-- 최종 등록 토글 버튼 -->
              <td style="text-align: center;">
                <button
                  :class="['enrolled-btn', { 'is-enrolled': app.is_enrolled }]"
                  @click="toggleEnrolled(app)"
                  :disabled="app.final_result === '불합격'"
                  :title="app.is_enrolled ? '최종 등록 취소' : '이 학교를 최종 진학으로 등록'"
                >
                  {{ app.is_enrolled ? '등록완료 🏆' : '등록선택' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 5. [모드 B] 학생별 지원 대학 묶어보기 뷰 -->
    <div v-else class="grouped-container">
      <div v-if="groupedStudents.length === 0" class="empty-state">
        <Inbox :size="36" :stroke-width="1.5" />
        <p>표시할 지원 학생이 없습니다.</p>
      </div>

      <div
        v-for="group in groupedStudents"
        :key="group.student_name"
        class="student-card"
      >
        <div class="student-card-header" @click="group.expanded = !group.expanded">
          <div class="student-profile">
            <div class="student-avatar">
              <User :size="18" :stroke-width="2" />
            </div>
            <div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="student-name-big">{{ group.student_name }}</span>
                <span
                  :class="['dept-badge', group.department && group.department.includes('자연') ? 'natural' : 'human']"
                >
                  {{ group.department && group.department.includes('자연') ? '자연' : (group.department && group.department.includes('인문') ? '인문' : '미기재') }}
                </span>
                <span v-if="group.enrolledUniv" class="mini-badge enrolled">
                  🏆 {{ group.enrolledUniv }} {{ group.enrolledMajor }} 최종진학
                </span>
              </div>
            </div>
          </div>

          <div class="student-status-summary">
            <span class="mini-badge total">총 {{ group.items.length }}곳 지원</span>
            <span v-if="group.stage1PassCount > 0" class="mini-badge pass">
              1차합 {{ group.stage1PassCount }}곳
            </span>
            <span v-if="group.finalPassCount > 0" class="mini-badge pass">
              합격 {{ group.finalPassCount }}곳
            </span>
            <ChevronDown
              :size="18"
              :style="{ transform: group.expanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease' }"
              color="#64748b"
            />
          </div>
        </div>

        <!-- 펼쳐진 카드 내부 학생별 지원 학교 리스트 -->
        <div v-if="group.expanded" class="student-card-body">
          <table class="results-table">
            <thead>
              <tr>
                <th style="width: 150px;">지원 대학</th>
                <th>지원 학과</th>
                <th style="width: 80px; text-align: center;">전략</th>
                <th style="width: 110px; text-align: center;">1차 전형</th>
                <th style="width: 130px; text-align: center;">최종 전형</th>
                <th style="width: 100px; text-align: center;">예비 번호</th>
                <th style="width: 100px; text-align: center;">최종 등록</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="app in group.items"
                :key="app.id"
                :class="{ 'row-enrolled': app.is_enrolled }"
              >
                <td><span class="univ-text">{{ app.univ }}</span></td>
                <td><span class="major-text">{{ app.major }}</span></td>
                <td style="text-align: center;"><span class="memo-tag">{{ app.memo || '적정' }}</span></td>

                <!-- 1차 결과 토글 -->
                <td style="text-align: center;">
                  <button
                    :class="['stage1-toggle-btn', app.stage1_result || '대기']"
                    @click="toggleStage1(app)"
                  >
                    {{ formatStage1(app.stage1_result) }}
                  </button>
                </td>

                <!-- 최종 결과 셀렉트 -->
                <td style="text-align: center;">
                  <select
                    v-model="app.final_result"
                    :class="['final-result-select', app.final_result || '대기']"
                    @change="onFinalResultChange(app)"
                  >
                    <option value="대기">대기</option>
                    <option value="최초합">최초합 🎉</option>
                    <option value="예비">예비 ⏳</option>
                    <option value="추가합">추가합 🎊</option>
                    <option value="불합격">불합격 ⚪</option>
                  </select>
                </td>

                <!-- 예비번호 -->
                <td style="text-align: center;">
                  <div class="waitlist-wrap" v-if="app.final_result === '예비' || app.final_result === '추가합' || app.waitlist_no">
                    <input
                      type="number"
                      min="1"
                      max="999"
                      v-model.number="app.waitlist_no"
                      @change="updateResult(app)"
                      @keyup.enter="$event.target.blur()"
                      placeholder="번호"
                      class="waitlist-input"
                    />
                    <span class="waitlist-unit">번</span>
                  </div>
                  <span v-else style="color: #cbd5e1;">-</span>
                </td>

                <!-- 최종 등록 토글 -->
                <td style="text-align: center;">
                  <button
                    :class="['enrolled-btn', { 'is-enrolled': app.is_enrolled }]"
                    @click="toggleEnrolled(app)"
                    :disabled="app.final_result === '불합격'"
                  >
                    {{ app.is_enrolled ? '등록완료 🏆' : '등록선택' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import {
  Table,
  Users,
  RotateCw,
  Bookmark,
  CheckCircle2,
  Award,
  Clock,
  Sparkles,
  GraduationCap,
  Search,
  Inbox,
  User,
  ChevronDown
} from 'lucide-vue-next';
import '../styles/AdmissionResultsBoard.css';

const API_BASE_URL = (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
  ? 'http://127.0.0.1:8000'
  : 'https://peer-score-finder.onrender.com';

export default {
  name: 'AdmissionResultsBoard',
  components: {
    Table,
    Users,
    RotateCw,
    Bookmark,
    CheckCircle2,
    Award,
    Clock,
    Sparkles,
    GraduationCap,
    Search,
    Inbox,
    User,
    ChevronDown
  },
  data() {
    return {
      loading: false,
      viewMode: 'table', // 'table' | 'grouped'
      searchKeyword: '',
      filterDept: 'ALL',
      filterStage1: 'ALL',
      filterFinal: 'ALL',
      stats: {
        total_applications: 0,
        unique_students: 0,
        stage1_pass: 0,
        final_initial: 0,
        final_reserve: 0,
        final_added: 0,
        final_fail: 0,
        enrolled: 0
      },
      applications: [],
      expandedStudents: {}
    };
  },
  computed: {
    filteredApplications() {
      let list = this.applications;

      // 1) 검색어 필터 (학생명, 대학, 학과)
      if (this.searchKeyword.trim()) {
        const kw = this.searchKeyword.trim().toLowerCase();
        list = list.filter(a =>
          (a.student_name && a.student_name.toLowerCase().includes(kw)) ||
          (a.univ && a.univ.toLowerCase().includes(kw)) ||
          (a.major && a.major.toLowerCase().includes(kw))
        );
      }

      // 2) 계열 필터
      if (this.filterDept !== 'ALL') {
        list = list.filter(a => {
          if (!a.department) return false;
          return a.department.includes(this.filterDept);
        });
      }

      // 3) 1차 결과 필터
      if (this.filterStage1 !== 'ALL') {
        list = list.filter(a => (a.stage1_result || '대기') === this.filterStage1);
      }

      // 4) 최종 결과 필터
      if (this.filterFinal !== 'ALL') {
        if (this.filterFinal === 'ENROLLED') {
          list = list.filter(a => a.is_enrolled);
        } else {
          list = list.filter(a => (a.final_result || '대기') === this.filterFinal);
        }
      }

      return list;
    },
    groupedStudents() {
      const map = {};
      this.filteredApplications.forEach(app => {
        if (!map[app.student_name]) {
          map[app.student_name] = {
            student_name: app.student_name,
            department: app.department,
            expanded: this.expandedStudents[app.student_name] !== false, // 기본 펼침
            items: [],
            enrolledUniv: '',
            enrolledMajor: '',
            stage1PassCount: 0,
            finalPassCount: 0
          };
        }
        map[app.student_name].items.push(app);
        if (app.is_enrolled) {
          map[app.student_name].enrolledUniv = app.univ;
          map[app.student_name].enrolledMajor = app.major;
        }
        if (app.stage1_result === '합격') {
          map[app.student_name].stage1PassCount++;
        }
        if (app.final_result === '최초합' || app.final_result === '추가합') {
          map[app.student_name].finalPassCount++;
        }
      });

      return Object.values(map);
    }
  },
  mounted() {
    this.loadData();
  },
  methods: {
    async loadData() {
      this.loading = true;
      try {
        const res = await axios.get(`${API_BASE_URL}/api/applications/results-board`);
        if (res.data) {
          this.stats = res.data.stats || this.stats;
          this.applications = res.data.applications || [];
        }
      } catch (err) {
        console.error('결과 현황판 로드 오류:', err);
      } finally {
        this.loading = false;
      }
    },

    formatStage1(val) {
      if (!val || val === '대기') return '대기';
      if (val === '합격') return '1차합격 🟢';
      if (val === '불합격') return '1차불합 ⚪';
      if (val === '해당없음') return '해당없음';
      return val;
    },

    // 1차 결과 순환 토글 (대기 -> 합격 -> 불합격 -> 해당없음 -> 대기)
    async toggleStage1(app) {
      const cycle = ['대기', '합격', '불합격', '해당없음'];
      const currentIdx = cycle.indexOf(app.stage1_result || '대기');
      const nextVal = cycle[(currentIdx + 1) % cycle.length];
      app.stage1_result = nextVal;
      await this.updateResult(app);
    },

    // 최종 결과 드롭다운 변경 시
    async onFinalResultChange(app) {
      if (app.final_result === '불합격') {
        app.is_enrolled = false;
      }
      await this.updateResult(app);
    },

    // 최종 등록 토글 (학생당 1개만 허용)
    async toggleEnrolled(app) {
      const nextState = !app.is_enrolled;
      if (nextState) {
        // 동일 학생의 다른 모든 원서 등록 해제
        this.applications.forEach(a => {
          if (a.student_name === app.student_name) {
            a.is_enrolled = false;
          }
        });
      }
      app.is_enrolled = nextState;
      await this.updateResult(app);
    },

    // 서버로 단건 업데이트 전송
    async updateResult(app) {
      try {
        const payload = {
          stage1_result: app.stage1_result,
          final_result: app.final_result,
          waitlist_no: app.waitlist_no !== '' && app.waitlist_no !== null ? Number(app.waitlist_no) : null,
          is_enrolled: app.is_enrolled
        };

        await axios.patch(`${API_BASE_URL}/api/applications/${app.id}/result`, payload);
        
        // 로컬 통계 재계산
        this.recalculateStats();
      } catch (err) {
        console.error('결과 저장 실패:', err);
        alert('저장에 실패했습니다. 다시 시도해 주세요.');
      }
    },

    recalculateStats() {
      const apps = this.applications;
      this.stats.total_applications = apps.length;
      this.stats.unique_students = new Set(apps.map(a => a.student_name)).size;
      this.stats.stage1_pass = apps.filter(a => a.stage1_result === '합격').length;
      this.stats.final_initial = apps.filter(a => a.final_result === '최초합').length;
      this.stats.final_reserve = apps.filter(a => a.final_result === '예비').length;
      this.stats.final_added = apps.filter(a => a.final_result === '추가합').length;
      this.stats.final_fail = apps.filter(a => a.final_result === '불합격').length;
      this.stats.enrolled = apps.filter(a => a.is_enrolled).length;
    }
  }
};
</script>

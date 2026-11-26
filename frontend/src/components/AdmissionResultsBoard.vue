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
        <!-- 보기 모드 전환 탭 (학생별 묶어보기 우선) -->
        <div class="view-mode-toggle">
          <button
            :class="['view-toggle-btn', viewMode === 'grouped' ? 'active' : '']"
            @click="viewMode = 'grouped'"
            title="학생별 지원 대학 묶어서 보기"
          >
            <Users :size="15" :stroke-width="2" />
            <span>학생별 묶어보기</span>
          </button>
          <button
            :class="['view-toggle-btn', viewMode === 'table' ? 'active' : '']"
            @click="viewMode = 'table'"
            title="스프레드시트형 전체 빠른 표로 보기"
          >
            <Table :size="15" :stroke-width="2" />
            <span>전체 빠른 표</span>
          </button>
        </div>

        <!-- 학생별 보기일 때 전체 펼침/접힘 토글 -->
        <div v-if="viewMode === 'grouped'" class="batch-expand-btns">
          <button @click="toggleAllStudents(true)" class="btn-batch-toggle" title="전체 학생 펼치기">모두 펼치기</button>
          <button @click="toggleAllStudents(false)" class="btn-batch-toggle" title="전체 학생 접기">모두 접기</button>
        </div>

        <button @click="loadData" class="btn-refresh" :disabled="loading" title="최신 상태 새로고침">
          <RotateCw :size="14" :class="{ 'spin': loading }" :stroke-width="2" />
          <span>새로고침</span>
        </button>
      </div>
    </div>

    <!-- 2. 핵심 통계 대시보드 (군더더기 없는 모던 미니멀 스타일) -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-info">
          <span class="stat-label">총 지원 건수</span>
          <span class="stat-val">{{ stats.total_applications }}<span class="stat-val-unit">건</span></span>
          <span class="stat-sub">{{ stats.unique_students }}명 지원 중</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-info">
          <span class="stat-label">1차 합격</span>
          <span class="stat-val stat-stage1">{{ stats.stage1_pass }}<span class="stat-val-unit">건</span></span>
          <span class="stat-sub">서류/면접 대상</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-info">
          <span class="stat-label">최초 합격</span>
          <span class="stat-val stat-initial">{{ stats.final_initial }}<span class="stat-val-unit">건</span></span>
          <span class="stat-sub">정규 최초 합격</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-info">
          <span class="stat-label">예비 대기</span>
          <span class="stat-val stat-reserve">{{ stats.final_reserve }}<span class="stat-val-unit">건</span></span>
          <span class="stat-sub">충원 대기중</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-info">
          <span class="stat-label">추가 합격</span>
          <span class="stat-val stat-added">{{ stats.final_added }}<span class="stat-val-unit">건</span></span>
          <span class="stat-sub">차수/전화 추합</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-info">
          <span class="stat-label">최종 진학 등록</span>
          <span class="stat-val stat-enrolled">{{ stats.enrolled }}<span class="stat-val-unit">명</span></span>
          <span class="stat-sub">진학 확정생</span>
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

    <!-- 4. [모드 A] 스프레드시트형 매트릭스 빠른 표 (행: 학생, 열: 지원 대학) -->
    <div v-if="viewMode === 'table'" class="table-card matrix-table-card">
      <div class="results-table-wrap">
        <table class="results-table matrix-table">
          <thead>
            <tr>
              <th class="matrix-sticky-col matrix-col-header" style="width: 85px; min-width: 85px; max-width: 85px;">
                학생명
              </th>
              <th class="matrix-sticky-dept matrix-col-header" style="width: 55px; min-width: 55px; max-width: 55px; text-align: center;">
                계열
              </th>
              <th
                v-for="univ in matrixUnivHeaders"
                :key="univ"
                class="matrix-col-header matrix-univ-th"
              >
                <div class="matrix-univ-name" :title="univ">{{ univ }}</div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="matrixStudentRows.length === 0">
              <td :colspan="2 + matrixUnivHeaders.length" class="empty-state">
                <Inbox :size="32" :stroke-width="1.5" />
                <p>일치하는 지원 학생 및 결과가 없습니다.</p>
              </td>
            </tr>

            <tr
              v-for="row in matrixStudentRows"
              :key="row.student_name"
              :class="['matrix-row', { 'row-has-enrolled': row.hasEnrolled }]"
            >
              <!-- 1) 고정 열: 학생명 (딱 맞는 너비) -->
              <td class="matrix-sticky-col cell-student-name">
                <div class="matrix-student-info">
                  <span class="student-name-text">{{ row.student_name }}</span>
                  <span v-if="row.enrolledUniv" class="enrolled-indicator" :title="`${row.enrolledUniv} 등록`">🏆</span>
                </div>
              </td>

              <!-- 2) 고정 열: 계열 (딱 맞는 너비) -->
              <td class="matrix-sticky-dept" style="text-align: center;">
                <span
                  :class="['dept-badge', row.department && row.department.includes('자연') ? 'natural' : 'human']"
                >
                  {{ row.department && row.department.includes('자연') ? '자연' : (row.department && row.department.includes('인문') ? '인문' : '-') }}
                </span>
              </td>

              <!-- 3) 가로 대학 열 셀 -->
              <td
                v-for="univ in matrixUnivHeaders"
                :key="univ"
                :class="['matrix-cell', {
                  'cell-applied': !!row.appsByUniv[univ],
                  'cell-enrolled': row.appsByUniv[univ] && row.appsByUniv[univ].is_enrolled,
                  'cell-stage1-pass': row.appsByUniv[univ] && getUnifiedStatus(row.appsByUniv[univ]) === '1차합',
                  'cell-final-pass': row.appsByUniv[univ] && getUnifiedStatus(row.appsByUniv[univ]) === '최초합',
                  'cell-reserve': row.appsByUniv[univ] && getUnifiedStatus(row.appsByUniv[univ]) === '예비'
                }]"
              >
                <!-- 지원한 학교인 경우: 단일 원클릭 토글 (대기->최초합->1차합->예비->불합) + 바로 옆 예비번호 -->
                <div v-if="row.appsByUniv[univ]" class="matrix-cell-content">
                  <div class="matrix-cell-row">
                    <!-- 원클릭 순환 토글 버튼 -->
                    <button
                      class="matrix-status-btn"
                      :data-status="getUnifiedStatus(row.appsByUniv[univ])"
                      @click="cycleUnifiedStatus(row.appsByUniv[univ])"
                      title="클릭하여 결과 변경: 대기 ➔ 최초합 ➔ 1차합 ➔ 예비 ➔ 불합"
                    >
                      {{ getUnifiedStatus(row.appsByUniv[univ]) }}
                    </button>

                    <!-- 옆에 붙은 예비번호 입력창 (화살표 제거) -->
                    <div class="matrix-waitlist-box">
                      <input
                        type="number"
                        min="1"
                        max="999"
                        v-model.number="row.appsByUniv[univ].waitlist_no"
                        @change="updateResult(row.appsByUniv[univ])"
                        @keyup.enter="$event.target.blur()"
                        placeholder="예비"
                        class="matrix-waitlist-input no-spinner"
                      />
                      <span class="matrix-waitlist-unit">번</span>
                    </div>
                  </div>

                  <!-- 학과 툴팁/안내 -->
                  <div class="matrix-major-preview" :title="row.appsByUniv[univ].major">
                    {{ row.appsByUniv[univ].major }}
                  </div>
                </div>

                <!-- 미지원 학교 -->
                <span v-else class="matrix-empty-dash">-</span>
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
        <div class="student-card-header" @click="toggleStudent(group.student_name)">
          <div class="student-profile">
            <div class="student-avatar">
              <User :size="16" :stroke-width="2" />
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

        <!-- 펼쳐진 카드 내부 학생별 지원 학교 리스트 (전략 열 제거) -->
        <div v-if="group.expanded" class="student-card-body">
          <table class="results-table compact-table">
            <thead>
              <tr>
                <th style="width: 160px;">지원 대학</th>
                <th>지원 학과</th>
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
                <td><strong class="univ-text">{{ app.univ }}</strong></td>
                <td><span class="major-text">{{ app.major }}</span></td>

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
                    <option value="최초합">최초합</option>
                    <option value="예비">예비</option>
                    <option value="추가합">추가합</option>
                    <option value="불합격">불합격</option>
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
    Search,
    Inbox,
    User,
    ChevronDown
  },
  data() {
    return {
      loading: false,
      viewMode: 'grouped', // 'grouped' (기본값) | 'table'
      searchKeyword: '',
      filterDept: 'ALL',
      filterStage1: 'ALL',
      filterFinal: 'ALL',
      tableGroupByStudent: true, // 빠른 표에서 학생별 구분선 및 음영 그룹핑
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
            expanded: this.expandedStudents[app.student_name] === true, // 🌟 기본값: 모두 접혀있게 설정
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
    },

    // 🌟 [매트릭스 빠른 표] 가로 열: 학생들이 실제 지원한 대학 목록 (선호 순위 순 정렬)
    matrixUnivHeaders() {
      const set = new Set();
      this.filteredApplications.forEach(a => {
        if (a.univ) set.add(a.univ);
      });
      const univs = Array.from(set);

      // 주요 대학 서열 목록 (서성한 중경외시 건동홍 국숭세단 광명상가 인가경 여대 한성항공)
      const ORDER_PATTERNS = [
        '서강', '성균관', '한양',
        '중앙', '경희', '한국외', '외국어', '시립',
        '건국', '동국', '홍익',
        '국민', '숭실', '세종', '단국',
        '광운', '명지', '상명', '가톨릭',
        '인하', '인천', '가천', '경기', '아주',
        '이화', '숙명', '동덕', '덕성', '서울여',
        '한성', '항공'
      ];

      function getUnivRank(name) {
        for (let i = 0; i < ORDER_PATTERNS.length; i++) {
          if (name.includes(ORDER_PATTERNS[i])) return i;
        }
        return 999;
      }

      return univs.sort((a, b) => {
        const rA = getUnivRank(a);
        const rB = getUnivRank(b);
        if (rA !== rB) return rA - rB;
        return a.localeCompare(b, 'ko');
      });
    },

    // 🌟 [매트릭스 빠른 표] 세로 행: 학생별 행 데이터 (학생명, 계열, 대학별 지원 내역 매핑)
    matrixStudentRows() {
      const map = {};
      this.filteredApplications.forEach(app => {
        if (!map[app.student_name]) {
          map[app.student_name] = {
            student_name: app.student_name,
            department: app.department,
            appsByUniv: {},
            hasEnrolled: false,
            enrolledUniv: ''
          };
        }
        map[app.student_name].appsByUniv[app.univ] = app;
        if (app.is_enrolled) {
          map[app.student_name].hasEnrolled = true;
          map[app.student_name].enrolledUniv = app.univ;
        }
      });

      return Object.values(map).sort((a, b) => a.student_name.localeCompare(b.student_name, 'ko'));
    }
  },
  mounted() {
    this.loadData();
  },
  methods: {
    toggleStudent(name) {
      this.expandedStudents[name] = !this.expandedStudents[name];
    },

    toggleAllStudents(expand) {
      const newMap = {};
      this.groupedStudents.forEach(g => {
        newMap[g.student_name] = expand;
      });
      this.expandedStudents = newMap;
    },

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
      if (val === '합격') return '1차합격';
      if (val === '불합격') return '1차불합';
      return val;
    },

    // 🌟 원클릭 통합 상태 계산 (대기 / 최초합 / 1차합 / 예비 / 불합)
    getUnifiedStatus(app) {
      if (!app) return '대기';
      if (app.final_result === '최초합') return '최초합';
      if (app.final_result === '추가합') return '최초합'; // 또는 합격
      if (app.final_result === '예비') return '예비';
      if (app.stage1_result === '합격') return '1차합';
      if (app.final_result === '불합격' || app.stage1_result === '불합격') return '불합';
      return '대기';
    },

    // 🌟 한 번 누를 때마다 순환: 대기 ➔ 최초합 ➔ 1차합 ➔ 예비 ➔ 불합 ➔ 대기
    async cycleUnifiedStatus(app) {
      const current = this.getUnifiedStatus(app);
      if (current === '대기') {
        app.stage1_result = '합격';
        app.final_result = '최초합';
      } else if (current === '최초합') {
        app.stage1_result = '합격';
        app.final_result = '대기'; // 1차만 합격한 상태
      } else if (current === '1차합') {
        app.stage1_result = '합격';
        app.final_result = '예비'; // 예비 상태
      } else if (current === '예비') {
        app.stage1_result = '불합격';
        app.final_result = '불합격';
        app.is_enrolled = false;
      } else { // '불합' -> '대기'
        app.stage1_result = '대기';
        app.final_result = '대기';
      }
      await this.updateResult(app);
    },

    // 1차 결과 순환 토글 (대기 -> 1차합 -> 1차불합 -> 대기, 불필요한 '-' 삭제)
    async toggleStage1(app) {
      const cycle = ['대기', '합격', '불합격'];
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

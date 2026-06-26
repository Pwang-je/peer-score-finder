<template>
  <div class="container">
    <h2>Welcome back, Peer Analyzer</h2>
    <p class="subtitle">과거 성적 데이터를 기반으로 나와 가장 정밀하게 일치하는 선배들의 정보를 시각화 만드는중..</p>
    
    <div class="input-section filter-panel">
      <div class="top-form-row">
        <div class="form-group autocomplete-container">
          <label>학생 이름 선택 (2026년)</label>
          <input 
            type="text" 
            v-model="searchKeyword" 
            @input="onSearchInput"
            placeholder="이름을 입력하세요 (예: 임하준)"
            autocomplete="off"
            class="search-input"
          >
          <ul v-if="suggestedStudents.length > 0" class="suggestion-list">
            <li 
              v-for="(name, idx) in suggestedStudents" 
              :key="idx" 
              @click="selectStudent(name)"
            >
              {{ name }}
            </li>
          </ul>
        </div>

        <div class="form-group">
          <label>모의고사 월 선택</label>
          <select v-model="form.month" @change="loadStudentScore">
            <option v-for="m in [1,2,3,4,5,6,7,8,9,10,11]" :key="m" :value="m">{{ m }}월</option>
          </select>
        </div>
      </div>
    </div>

    <div class="stats-monitor-section">
      <div class="section-title-badge">
        <span>{{ form.student_name ? form.student_name + ' 학생의 기록' : '선택된 학생 없음' }}</span>
      </div>
      <div class="monitor-grid">
        <div class="monitor-card m-grammar">
          <span class="m-label">선택한 학생의 문법</span>
          <span class="m-value">{{ studentDBData.grammar }}</span>
        </div>
        <div class="monitor-card m-vocabulary">
          <span class="m-label">선택한 학생의 어휘</span>
          <span class="m-value">{{ studentDBData.vocabulary }}</span>
        </div>
        <div class="monitor-card m-logic">
          <span class="m-label">선택한 학생의 논리</span>
          <span class="m-value">{{ studentDBData.logic }}</span>
        </div>
        <div class="monitor-card m-reading">
          <span class="m-label">선택한 학생의 독해</span>
          <span class="m-value">{{ studentDBData.reading }}</span>
        </div>
        <div class="monitor-card m-total">
          <span class="m-label">선택한 학생의 총점</span>
          <span class="m-value-total">{{ studentDBData.total_score }}</span>
        </div>
      </div>
    </div>

    <div class="accordion-container" :class="{ 'is-open': isAccordionOpen }">
      <div class="accordion-header" @click="isAccordionOpen = !isAccordionOpen">
        <span class="accordion-title">❓ Peer Analyzer는 어떻게 작동하나요? (클릭하여 열기/접기)</span>
        <span class="accordion-icon">{{ isAccordionOpen ? '🔼' : '🔽' }}</span>
      </div>
      <div v-show="isAccordionOpen" class="accordion-content">
        <p>🎯 <strong>1. 나만의 AI 점수 지도 생성</strong><br>
        여러분이 하단에 입력한 문법, 어휘, 논리, 독해 점수는 가상의 4차원 성적 공간 위에 하나의 위치(좌표)로 기록됩니다.</p>
        
        <p>🔍 <strong>2. 가장 정밀한 합격 선배 탐색 (KNN 알고리즘)</strong><br>
        수만 명의 과거 합격 선배들 중에서, 내가 입력한 점수와 <u>가장 가까운 거리에 밀집해 있는 진짜 이웃 선배들</u>을 데이터 기반으로 빠르게 추려냅니다.</p>
        
        <p>📊 <strong>3. 합격 대학 분포 가시화</strong><br>
        추출된 유사 성적 선배들이 실제로 어느 대학, 어느 학과에 많이 매칭되었는지 통계를 내어 실시간 대시보드로 시각화해 줍니다.</p>
      </div>
    </div>

    <div class="input-section manual-input-panel">
      <div class="manual-header">
        <h4>📝 점수 직접 입력</h4>
        <p>선배 매칭 예측에 사용할 점수를 입력창에 직접 채워주세요.</p>
      </div>
      
      <div class="manual-inputs-grid">
        <div class="form-group input-box">
          <label>문법 점수 입력 칸</label>
          <input type="number" v-model.number="form.grammar" step="0.1" placeholder="0.0">
        </div>
        <div class="form-group input-box">
          <label>어휘 점수 입력 칸</label>
          <input type="number" v-model.number="form.vocabulary" step="0.1" placeholder="0.0">
        </div>
        <div class="form-group input-box">
          <label>논리 점수 입력 칸</label>
          <input type="number" v-model.number="form.logic" step="0.1" placeholder="0.0">
        </div>
        <div class="form-group input-box">
          <label>독해 점수 입력 칸</label>
          <input type="number" v-model.number="form.reading" step="0.1" placeholder="0.0">
        </div>
        <div class="form-group input-box total-preview-box">
          <label>입력된 점수 총점</label>
          <div class="live-total">{{ inputTotalScore }} <small>점</small></div>
        </div>
      </div>
      
      <button @click="fetchPrediction" class="btn-submit">유사 성적 선배 분석하기</button>
    </div>

    <div v-if="result" class="result-section">
      <div class="dashboard-layout-container">
        <div class="subjects-horizontal-row">
          <div class="chart-card-item card-grammar">
            <span class="card-label">문법</span>
            <div class="mini-chart-space"><canvas id="grammarChart"></canvas></div>
          </div>
          <div class="chart-card-item card-vocabulary">
            <span class="card-label">어휘</span>
            <div class="mini-chart-space"><canvas id="vocabularyChart"></canvas></div>
          </div>
          <div class="chart-card-item card-logic">
            <span class="card-label">논리</span>
            <div class="mini-chart-space"><canvas id="logicChart"></canvas></div>
          </div>
          <div class="chart-card-item card-reading">
            <span class="card-label">독해</span>
            <div class="mini-chart-space"><canvas id="readingChart"></canvas></div>
          </div>
        </div>
        
        <div class="chart-card-item card-total total-wide-card">
          <span class="card-label">유사 성적 합격 선배들과 나의 시즌 총점 추이 비교 그래프 (1월 ~ 11월 흐름)</span>
          <div class="mini-chart-space"><canvas id="timelineChart"></canvas></div>
        </div>
      </div>
      
      <h3>매칭 확률 높은 TOP 10 대학 및 학과별 분포</h3>
      <div class="univ-card-container">
        <div v-for="(u, idx) in result.univ_details" :key="idx" class="univ-card">
          <div class="univ-card-header">
            <span class="univ-title">{{ u.univ }}</span>
            <span class="univ-badge">총 {{ u.total_count }}명</span>
          </div>
          <div class="univ-card-body">
            <div v-for="(m, mIdx) in u.majors" :key="mIdx" class="major-box">
              <div class="major-title-line">
                <span class="m-name">{{ m.major }}</span>
                <span class="m-count">{{ m.count }}명</span>
              </div>
              
              <div v-for="(scoreObj, sIdx) in m.scores" :key="sIdx" class="senior-scores-tags senior-profile-line">
                <span class="badge-senior-meta">[{{ scoreObj.year }} {{ scoreObj.name }}]</span>
                <span class="badge-score badge-grammar">{{ scoreObj.grammar }}</span>
                <span class="badge-score badge-vocabulary">{{ scoreObj.vocabulary }}</span>
                <span class="badge-score badge-logic">{{ scoreObj.logic }}</span>
                <span class="badge-score badge-reading">{{ scoreObj.reading }}</span>
                <span class="badge-score badge-total">{{ scoreObj.total }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <h3>가장 가까운 성적의 선배 10인 상세 리스트</h3>
      <div class="table-wrapper">
        <table class="senior-table">
          <thead>
            <tr>
              <th>연도</th>
              <th>합격 대학</th>
              <th>합격 학과</th>
              <th>전형 계열</th>
              <th>영역별 상세 취득 점수</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(s, sIdx) in result.all_seniors" :key="sIdx">
              <td>{{ s.year }}년</td>
              <td class="bold-text">
                <div class="table-univ-cell">
                  <span class="badge-senior-meta">[{{ String(s.year).slice(2) }}' {{ s.scores.name || '선배' }}]</span>
                  <span>{{ s.univ }}</span>
                </div>
              </td>
              <td>{{ s.major }}</td>
              <td class="gray-text">{{ s.department }}</td>
              <td>
                <div class="table-badge-group">
                  <span class="badge-score badge-grammar">{{ s.scores.grammar }}</span>
                  <span class="badge-score badge-vocabulary">{{ s.scores.vocabulary }}</span>
                  <span class="badge-score badge-logic">{{ s.scores.logic }}</span>
                  <span class="badge-score badge-reading">{{ s.scores.reading }}</span>
                  <span class="badge-score badge-total">{{ s.scores.total }}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { Chart, registerables } from 'chart.js';
import './style.css';

Chart.register(...registerables);

export default {
  data() {
    return {
      searchKeyword: '', 
      isAccordionOpen: false, // 🌟 아코디언 접이식 제어 상태값 기본 닫힘 세팅
      form: { 
        month: 5, 
        grammar: '', 
        vocabulary: '', 
        logic: '', 
        reading: '', 
        student_name: '' 
      },
      studentDBData: { grammar: '-', vocabulary: '-', logic: '-', reading: '-', total_score: '-' },
      suggestedStudents: [], 
      result: null,
      chartInstances: {}
    };
  },
  computed: {
    inputTotalScore() {
      const g = Number(this.form.grammar) || 0;
      const v = Number(this.form.vocabulary) || 0;
      const l = Number(this.form.logic) || 0;
      const r = Number(this.form.reading) || 0;
      return g + v + l + r > 0 ? roundToOneDecimal(g + v + l + r) : '-';
    }
  },
  methods: {
    async onSearchInput() {
      const keyword = this.searchKeyword;
      if (!keyword || keyword.trim() === '') {
        this.suggestedStudents = [];
        return;
      }
      try {
        const response = await axios.get(`http://127.0.0.1:8000/search-students`, {
          params: { keyword: keyword }
        });
        this.suggestedStudents = response.data;
      } catch (error) {
        console.error("이름 검색 실패:", error);
      }
    },

    selectStudent(name) {
      this.searchKeyword = name;
      this.form.student_name = name;
      this.suggestedStudents = [];
      this.loadStudentScore();
    },

    async loadStudentScore() {
      if (!this.form.student_name || this.form.student_name.trim() === '') return;
      
      try {
        const response = await axios.get('http://127.0.0.1:8000/get-student-score', {
          params: {
            student_name: this.form.student_name,
            month: this.form.month
          }
        });
        
        if (response.data.status === 'success') {
          const score = response.data.data;
          this.studentDBData.grammar = score.grammar;
          this.studentDBData.vocabulary = score.vocabulary;
          this.studentDBData.logic = score.logic;
          this.studentDBData.reading = score.reading;
          this.studentDBData.total_score = score.total_score;

          this.form.grammar = score.grammar;
          this.form.vocabulary = score.vocabulary;
          this.form.logic = score.logic;
          this.form.reading = score.reading;
        } else {
          this.studentDBData = { grammar: '-', vocabulary: '-', logic: '-', reading: '-', total_score: '-' };
          alert(`${this.form.student_name} 학생은 ${this.form.month}월 모의고사 성적 데이터가 없습니다.`);
        }
      } catch (error) {
        console.error("학생 성적 로드 실패:", error);
      }
    },

    async fetchPrediction() {
      if (!this.form.grammar && !this.form.vocabulary && !this.form.logic && !this.form.reading) {
        alert("분석할 점수를 하단 입력창에 작성해 주세요!");
        return;
      }
      try {
        const sendForm = { ...this.form, student_name: this.form.student_name || "직접입력수험생" };
        const response = await axios.get('http://127.0.0.1:8000/predict', { params: sendForm });
        
        if (response.data.status === 'success') {
          this.result = response.data;
          this.$nextTick(() => {
            // 🌟 백엔드에서 온 리스트업의 개별 이름들을 프론트엔드 상세 리스트 가공단에 바인딩
            this.result.all_seniors.forEach(senior => {
               const matchInTop = this.result.univ_details.find(u => u.univ === senior.univ);
               if(matchInTop) {
                  const majorMatch = matchInTop.majors.find(m => m.major === senior.major);
                  if(majorMatch) {
                     const scoreMatch = majorMatch.scores.find(s => s.total === senior.scores.total);
                     if(scoreMatch) senior.scores.name = scoreMatch.name;
                  }
               }
            });
            this.renderAllCharts(this.result.month_averages, this.result.timeline_stats, this.result.my_timeline_stats);
          });
        } else {
          alert(response.data.message);
        }
      } catch (error) {
        alert("백엔드 분석 에러가 발생했습니다.");
      }
    },

    renderAllCharts(averages, timeline, myTimeline) {
      const miniConfigs = [
        { id: 'grammar', my: this.form.grammar || 0, avg: averages.grammar, bg: 'rgba(132, 204, 22, 0.75)', max: 25 },
        { id: 'vocabulary', my: this.form.vocabulary || 0, avg: averages.vocabulary, bg: 'rgba(59, 130, 246, 0.75)', max: 12.5 },
        { id: 'logic', my: this.form.logic || 0, avg: averages.logic, bg: 'rgba(249, 115, 22, 0.75)', max: 20 },
        { id: 'reading', my: this.form.reading || 0, avg: averages.reading, bg: 'rgba(234, 179, 8, 0.75)', max: 50 }
      ];

      miniConfigs.forEach(cfg => {
        const ctx = document.getElementById(`${cfg.id}Chart`).getContext('2d');
        if (this.chartInstances[cfg.id]) this.chartInstances[cfg.id].destroy();
        this.chartInstances[cfg.id] = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: ['내 점수', '평균'],
            datasets: [{
              data: [cfg.my, cfg.avg],
              backgroundColor: [cfg.bg, 'rgba(148, 163, 184, 0.15)'],
              borderRadius: 6,
              barThickness: 16
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { grid: { display: false }, ticks: { font: { family: 'Noto Sans KR', size: 11 } } },
              y: { beginAtZero: true, max: cfg.max, grid: { display: false }, border: { display: false }, ticks: { display: false } }
            }
          }
        });
      });

      const ctxTotal = document.getElementById('timelineChart').getContext('2d');
      if (this.chartInstances['timeline']) this.chartInstances['timeline'].destroy();

      this.chartInstances['timeline'] = new Chart(ctxTotal, {
        type: 'line',
        data: {
          labels: Object.keys(timeline),
          datasets: [
            {
              label: '합격 선배 평균 총점',
              data: Object.values(timeline),
              borderColor: '#ec4899', 
              borderWidth: 3.5,
              pointBackgroundColor: '#ffffff',
              pointBorderColor: '#ec4899',
              pointBorderWidth: 2.5,
              pointRadius: 4,
              fill: false,
              tension: 0.4 
            },
            {
              label: '나의 총점 추이',
              data: Object.values(myTimeline),
              borderColor: '#2563eb', 
              borderWidth: 3.5,
              pointBackgroundColor: '#ffffff',
              pointBorderColor: '#2563eb',
              pointBorderWidth: 2.5,
              pointRadius: 5,
              fill: false, 
              tension: 0.4 
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: true, position: 'top' } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { family: 'Noto Sans KR', size: 11, weight: '600' } } },
            y: { grid: { color: 'rgba(226, 232, 240, 0.5)' }, border: { display: false } }
          }
        }
      });
    }
  }
};

function roundToOneDecimal(num) {
  return Math.round(num * 10) / 10;
}
</script>

<style scoped>
/* 🌟 접이식 아코디언 및 테이블 이름 정렬 보정 전용 로컬 스타일 스킨 브릿지 */

</style>
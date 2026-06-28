<template>
  <div class="container">
    <h2>Welcome back, Peer Analyzer</h2>
    <p class="subtitle">과거 성적 데이터를 기반으로 나와 가장 정밀하게 일치하는 학생의 정보를 시각화 만드는중</p>
    <p class="subtitle">데이터는 2020년~2025년까지의 합격생 입니다.</p>
    
    <div class="input-section filter-panel">
      <div class="top-form-row">
        <div class="form-group autocomplete-container">
          <label>학생 이름 선택 (2026년)</label>
          <input 
            type="text" 
            v-model="searchKeyword" 
            @input="onSearchInput"
            placeholder="이름을 입력하세요"
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
        <span class="accordion-title">
          <i class="icon-info"></i> Peer Analyzer는 어떻게 작동하나요?
        </span>
        <span class="accordion-arrow-icon"></span>
      </div>
      <div v-show="isAccordionOpen" class="accordion-content">
        <p><strong class="step-badge">01</strong> <strong>4차원 성적 공간(Multi-Dimensional Space) 매핑</strong><br>
        여러분이 입력한 문법, 어휘, 논리, 독해 점수는 단순한 총점 계산에 그치지 않고, 시스템 내부에서 가상의 <strong>'4차원 성적 좌표'</strong>로 치환됩니다. 이는 과목별 강점과 약점을 고유한 위치 데이터로 기록하는 과정입니다.</p>
        
        <p><strong class="step-badge">02</strong> <strong>유클리드 거리 기반 패턴 분석 (KNN 알고리즘)</strong><br>
        Peer Analyzer는 수만 명의 합격 선배 데이터 중 단순히 총점이 일치하는 사람이 아니라, <u>나와 과목별 점수 밸런스(비율)가 가장 대칼코마니처럼 닮은 이웃 선배들</u>을 찾아냅니다.<br>
        <span class="highlight-text">* 총점이 나보다 높더라도 문법 만점 비율, 독해 약세 패턴 등 '영역별 성적 추이'가 소수점 단위로 일치하면 가장 가까운 핵심 이웃으로 매칭됩니다.</span></p>
        
        <p><strong class="step-badge">03</strong> <strong>중복 제거 및 데이터 다양성 확보</strong><br>
        추출된 유사 선배들 중 동일 인물의 중복 데이터를 칼같이 정제하고, 특정 대학이 리스트를 독점하지 않도록 정밀 필터링(Sampling)을 거쳐 가장 신뢰도 높은 최상위 합격 선배 10인의 최종 명단을 완성합니다.</p>

        <p class="guide-box"><strong class="guide-title">ANALYSIS GUIDE</strong><br>
        리스트에 총점이 높은 상위권 대학(예: 중앙대 등) 선배가 매칭되었다면, 이는 <strong>"현재 나의 과목별 약점을 보완해 총점을 끌어올렸을 때, 내가 도달할 수 있는 가장 유력한 합격 패턴"</strong>을 AI가 추천한 것입니다. 선배들의 영역별 점수를 나의 최종 목표 지표로 삼아보세요!</p>
      </div>
    </div>

    <div class="input-section manual-input-panel">
      <div class="manual-header">
        <h4>📝 점수 직접 입력</h4>
        <p>예측에 사용할 점수를 입력창에 직접 채워주세요.</p>
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

      <h3>점수와 가까운 지난 학생 리스트</h3>
      <div class="table-wrapper">
        <table class="senior-table">
          <thead>
            <tr>
              <th>연도</th>
              <th>[이름] 합격 대학</th>
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
      isAccordionOpen: false, 
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
            this.renderAllCharts(this.result.month_averages, this.result.timeline_stats, this.result.my_timeline_stats);
          });
        } else {
          alert(response.data.message);
        }
      } catch (error) {
        alert("백엔드 분석 에러가 발생했습니다.");
      }
    },

    // 🌟 원본에 존재하던 역추적 함수 본래 상태 그대로 유지
    findRealSeniorName(senior) {
      if (!this.result || !this.result.univ_details) return '선배';
      
      const targetUniv = this.result.univ_details.find(u => u.univ === senior.univ);
      if (targetUniv) {
        const targetMajor = targetUniv.majors.find(m => m.major === senior.major);
        if (targetMajor) {
          const matchedScore = targetMajor.scores.find(s => 
            s.total === senior.scores.total && 
            s.reading === senior.scores.reading
          );
          if (matchedScore && matchedScore.name) {
            return matchedScore.name;
          }
          if (targetMajor.scores.length > 0) {
            return targetMajor.scores[0].name;
          }
        }
      }
      return '선배';
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
.accordion-container {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  margin-bottom: 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.accordion-header {
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: #f8fafc;
  user-select: none;
  transition: background 0.2s;
}

.accordion-header:hover {
  background: #f1f5f9;
}

.accordion-title {
  font-size: 14.5px;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ℹ️ 세련된 원형 인포메이션 아이콘 */
.icon-info {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 1.5px solid #64748b;
  border-radius: 50%;
  position: relative;
}
.icon-info::before {
  content: '';
  position: absolute;
  width: 1.5px;
  height: 5px;
  background: #64748b;
  left: 50%;
  top: 6px;
  transform: translateX(-50%);
}
.icon-info::after {
  content: '';
  position: absolute;
  width: 1.5px;
  height: 1.5px;
  background: #64748b;
  left: 50%;
  top: 3px;
  transform: translateX(-50%);
}

/* 모던한 꺾쇠 화살표 */
.accordion-arrow-icon {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-right: 2px solid #64748b;
  border-bottom: 2px solid #64748b;
  transform: rotate(45deg);
  transition: transform 0.3s ease;
  margin-right: 4px;
}

.accordion-container.is-open .accordion-arrow-icon {
  transform: rotate(-135deg);
}

.accordion-content {
  padding: 24px;
  background: white;
  border-top: 1px solid #e2e8f0;
  font-size: 14px;
  line-height: 1.7;
  color: #475569;
}

/* 테크니컬 숫자 배지 */
.step-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: monospace;
  font-size: 11px;
  background: #f1f5f9;
  color: #64748b;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 6px;
  font-weight: 700;
  vertical-align: middle;
}

.highlight-text {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: #2563eb;
  font-weight: 500;
  background: #eff6ff;
  padding: 8px 14px;
  border-radius: 8px;
  border-left: 4px solid #3b82f6;
}

.guide-box {
  margin-top: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px dashed #cbd5e1;
}

.guide-title {
  font-size: 11px;
  font-family: monospace;
  color: #475569;
  letter-spacing: 1px;
}

.table-univ-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

strong {
  color: #1e293b;
}
</style>
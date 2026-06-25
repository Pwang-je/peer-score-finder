<template>
  <div class="container">
    <h2>Welcome back, Peer Analyzer</h2>
    <p class="subtitle">과거 성적 데이터를 기반으로 나와 가장 정밀하게 일치하는 선배들의 정보를 시각화합니다.</p>
    
    <div class="input-section">
      <div class="form-group">
        <label>모의고사 월 선택</label>
        <select v-model="form.month">
          <option v-for="m in [3,4,5,6,7,8,9,10]" :key="m" :value="m">{{ m }}월</option>
        </select>
      </div>
      
      <div class="score-inputs">
        <div class="form-group"><label>문법 점수</label><input type="number" v-model.number="form.grammar" step="0.1"></div>
        <div class="form-group"><label>어휘 점수</label><input type="number" v-model.number="form.vocabulary" step="0.1"></div>
        <div class="form-group"><label>논리 점수</label><input type="number" v-model.number="form.logic" step="0.1"></div>
        <div class="form-group"><label>독해 점수</label><input type="number" v-model.number="form.reading" step="0.1"></div>
      </div>
      <button @click="fetchPrediction" class="btn-submit">유사 성적 선배 분석하기</button>
    </div>

    <div v-if="result" class="result-section">
      
      <div class="dashboard-layout-container">
        
        <div class="subjects-horizontal-row">
          <div class="chart-card-item card-grammar">
            <span class="card-label">문법 분석 (20점 만점)</span>
            <div class="mini-chart-space"><canvas id="grammarChart"></canvas></div>
          </div>
          <div class="chart-card-item card-vocabulary">
            <span class="card-label">어휘 분석 (20점 만점)</span>
            <div class="mini-chart-space"><canvas id="vocabularyChart"></canvas></div>
          </div>
          <div class="chart-card-item card-logic">
            <span class="card-label">논리 분석 (20점 만점)</span>
            <div class="mini-chart-space"><canvas id="logicChart"></canvas></div>
          </div>
          <div class="chart-card-item card-reading">
            <span class="card-label">독해 분석 (50점 만점)</span>
            <div class="mini-chart-space"><canvas id="readingChart"></canvas></div>
          </div>
        </div>
        
        <div class="chart-card-item card-total total-wide-card">
          <span class="card-label">유사 성적 합격 선배들의 시즌 총점 추이 그래프 (3월 ~ 10월 흐름)</span>
          <div class="mini-chart-space"><canvas id="timelineChart"></canvas></div>
        </div>

      </div>
      
      <h3>매칭 확률 높은 TOP 6 대학 및 학과별 분포</h3>
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
              
              <div v-for="(scoreObj, sIdx) in m.scores" :key="sIdx" class="senior-scores-tags">
                <span class="badge-score badge-grammar">문법 {{ scoreObj.grammar }}</span>
                <span class="badge-score badge-vocabulary">어휘 {{ scoreObj.vocabulary }}</span>
                <span class="badge-score badge-logic">논리 {{ scoreObj.logic }}</span>
                <span class="badge-score badge-reading">독해 {{ scoreObj.reading }}</span>
                <span class="badge-score badge-total">총점 {{ scoreObj.total }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <h3>가장 가까운 성적의 선배 20인 상세 리스트</h3>
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
              <td class="bold-text">{{ s.univ }}</td>
              <td>{{ s.major }}</td>
              <td class="gray-text">{{ s.department }}</td>
              <td>
                <div class="table-badge-group">
                  <span class="badge-score badge-grammar">문법 {{ s.scores.grammar }}</span>
                  <span class="badge-score badge-vocabulary">어휘 {{ s.scores.vocabulary }}</span>
                  <span class="badge-score badge-logic">논리 {{ s.scores.logic }}</span>
                  <span class="badge-score badge-reading">독해 {{ s.scores.reading }}</span>
                  <span class="badge-score badge-total">총점 {{ s.scores.total }}</span>
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
      form: { month: 4, grammar: '', vocabulary: '', logic: '', reading: '' },
      result: null,
      chartInstances: {}
    };
  },
  computed: {
    myTotalScore() {
      const g = this.form.grammar || 0;
      const v = this.form.vocabulary || 0;
      const l = this.form.logic || 0;
      const r = this.form.reading || 0;
      return roundToOneDecimal(g + v + l + r);
    }
  },
  methods: {
    async fetchPrediction() {
      if (!this.form.grammar && !this.form.vocabulary && !this.form.logic && !this.form.reading) {
        alert("점수를 입력해 주세요!");
        return;
      }
      try {
        const response = await axios.get('http://127.0.0.1:8000/predict', { params: this.form });
        if (response.data.status === 'success') {
          this.result = response.data;
          this.$nextTick(() => {
            this.renderAllCharts(this.result.month_averages, this.result.timeline_stats);
          });
        } else {
          alert(response.data.message);
        }
      } catch (error) {
        alert("백엔드 서버와 연결할 수 없습니다. 파이참을 확인해 주세요.");
      }
    },
    renderAllCharts(averages, timeline) {
      // 🌟 [수정 완료] 영역별 문항 배점 정량 한계 고유 설정 부여 (20점 vs 50점 만점 분리)
      const miniConfigs = [
        { id: 'grammar', my: this.form.grammar || 0, avg: averages.grammar, bg: 'rgba(132, 204, 22, 0.75)', max: 17.5 },
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
              borderSkipped: false,
              barThickness: 16,
              maxBarThickness: 20
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { 
                grid: { display: false }, 
                ticks: { font: { family: 'Noto Sans KR', size: 11, weight: '500' }, color: '#64748b' } 
              },
              y: { 
                beginAtZero: true, 
                max: cfg.max, // 🌟 과목별로 20 또는 50 스케일이 유동적으로 바인딩되어 압착 버그 파괴
                grid: { display: false }, 
                border: { display: false }, 
                ticks: { display: false } 
              }
            }
          }
        });
      });

      // 2. 하단 와이드: 라벤더 핑크 멀티 그라데이션 선 추이 차트 빌드
      const ctxTotal = document.getElementById('timelineChart').getContext('2d');
      if (this.chartInstances['timeline']) this.chartInstances['timeline'].destroy();

      const lineGradient = ctxTotal.createLinearGradient(0, 0, ctxTotal.canvas.width, 0);
      lineGradient.addColorStop(0, '#8b5cf6');   
      lineGradient.addColorStop(0.5, '#a78bfa'); 
      lineGradient.addColorStop(1, '#ec4899');   

      const fillGradient = ctxTotal.createLinearGradient(0, 0, 0, 240);
      fillGradient.addColorStop(0, 'rgba(139, 92, 246, 0.35)');
      fillGradient.addColorStop(0.6, 'rgba(167, 139, 250, 0.15)');
      fillGradient.addColorStop(1, 'rgba(236, 72, 153, 0.0)');

      const monthsLabels = Object.keys(timeline);
      const scoresData = Object.values(timeline);

      this.chartInstances['timeline'] = new Chart(ctxTotal, {
        type: 'line',
        data: {
          labels: monthsLabels,
          datasets: [{
            label: '선배들의 월별 평균 총점',
            data: scoresData,
            borderColor: lineGradient, 
            borderWidth: 3.5,
            pointBackgroundColor: '#ffffff',
            pointBorderColor: '#8b5cf6',
            pointBorderWidth: 2.5,
            pointRadius: 4,
            pointHoverRadius: 7,
            pointHoverBackgroundColor: '#ffffff',
            pointHoverBorderColor: '#ec4899',
            pointHoverBorderWidth: 3,
            fill: true,
            backgroundColor: fillGradient, 
            tension: 0.4 
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          layout: { padding: { left: 10, right: 15, top: 10, bottom: 5 } },
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { font: { family: 'Noto Sans KR', size: 11, weight: '600' }, color: '#64748b' } },
            y: { 
              beginAtZero: false, 
              grid: { color: 'rgba(226, 232, 240, 0.5)', drawTicks: false },
              border: { dash: [4, 4], display: false }, 
              ticks: { font: { family: 'Noto Sans KR', size: 11, weight: '500' }, color: '#94a3b8', padding: 8 } 
            }
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
/* 독립 컴포넌트 관리를 위해 핵심 스타일은 style.css로 완전 유지 */
</style>
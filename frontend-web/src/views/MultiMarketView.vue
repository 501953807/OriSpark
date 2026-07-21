<template>
  <div class="multimarket-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>多市场扩张规划器</h2>
      <p class="subtitle">地理套利 · 出海规划 · 跨境税务</p>

      <!-- Tab 切换 -->
      <div class="tabs">
        <button :class="['tab', { active: tab === 'markets' }]" @click="tab = 'markets'">市场对比</button>
        <button :class="['tab', { active: tab === 'arbitrage' }]" @click="tab = 'arbitrage'">地理套利</button>
        <button :class="['tab', { active: tab === 'phases' }]" @click="tab = 'phases'">出海规划</button>
      </div>

      <!-- 市场对比 -->
      <div v-if="tab === 'markets'" class="section">
        <div class="market-table">
          <table>
            <thead>
              <tr>
                <th>市场</th>
                <th>创作者数(万)</th>
                <th>年收入中位数</th>
                <th>RPM(元)</th>
                <th>增速</th>
                <th>开放度</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in store.markets" :key="m.market_code" :class="{ current: m.market_code === 'cn' }">
                <td><strong>{{ m.name_zh }}</strong></td>
                <td>{{ m.total_creators?.toLocaleString() }}</td>
                <td>¥{{ m.revenue_median_yuan?.toLocaleString() }}</td>
                <td>¥{{ m.avg_rpm_yuan }}</td>
                <td>{{ m.growth_rate_yoy }}%</td>
                <td>{{ m.is_open_to_foreign_creators ? '✅' : '❌' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 地理套利计算器 -->
      <div v-if="tab === 'arbitrage'" class="section">
        <div class="arbitrage-form">
          <div class="form-group">
            <label>当前市场</label>
            <select v-model="arbitrageForm.current_markets">
              <option value="cn">中国大陆</option>
            </select>
          </div>
          <div class="form-group">
            <label>月均收入 (元)</label>
            <input type="number" v-model.number="arbitrageForm.monthly_revenue_yuan" />
          </div>
          <div class="form-group">
            <label>创作者类型</label>
            <select v-model="arbitrageForm.creator_type">
              <option value="illustrator">插画师</option>
              <option value="photographer">摄影师</option>
              <option value="musician">音乐人</option>
              <option value="writer">文字作者</option>
            </select>
          </div>
          <button class="btn-primary" @click="doCalc">计算收益提升</button>
        </div>

        <div v-if="store.geoArbitrage" class="arbitrage-result">
          <div class="result-summary">
            <div class="current-revenue">
              <span>当前月收入</span>
              <span class="value">¥{{ store.geoArbitrage.current_total_monthly.toLocaleString() }}</span>
            </div>
            <div class="arrow">→</div>
            <div class="projected-revenue">
              <span>预期月收入</span>
              <span class="value green">¥{{ store.geoArbitrage.total_projected_monthly.toLocaleString() }}</span>
            </div>
          </div>
          <div class="increase-badge">+{{ store.geoArbitrage.increase_percent }}%</div>

          <div class="breakdown">
            <div v-for="(rev, code) in store.geoArbitrage.projected_with_targets" :key="code" class="market-breakdown">
              <span>{{ marketName(code) }}</span>
              <span>¥{{ rev.toLocaleString() }}/月</span>
            </div>
          </div>

          <div v-if="store.geoArbitrage.recommended_markets.length > 0" class="recommendation">
            <strong>推荐优先扩展：</strong>
            {{ store.geoArbitrage.recommended_markets.map(marketName).join('、') }}
          </div>
        </div>
      </div>

      <!-- 出海三阶段 -->
      <div v-if="tab === 'phases'" class="section">
        <div v-for="phase in store.phases" :key="phase.phase_key" class="phase-card">
          <div class="phase-header">
            <h3>{{ phase.phase_name_zh }}</h3>
            <span class="phase-duration">{{ phase.duration_months }}个月</span>
          </div>
          <ul class="phase-actions">
            <li v-for="a in phase.key_actions" :key="a">{{ a }}</li>
          </ul>
          <div class="milestones">
            <strong>里程碑：</strong>
            <ul>
              <li v-for="m in phase.milestones" :key="m">{{ m }}</li>
            </ul>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useMultiMarketStore } from '@/stores/useMultiMarketStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useMultiMarketStore()
const tab = ref('markets')

const arbitrageForm = ref({
  current_markets: ['cn'],
  creator_type: 'illustrator',
  monthly_revenue_yuan: 5000,
})

async function doCalc() {
  await store.runGeoArbitrage(arbitrageForm.value)
}

function marketName(code: string): string {
  const map: Record<string, string> = {
    cn: '中国大陆', us: '美国', eu: '欧盟', jp: '日本',
  }
  return map[code] || code
}

// Init
store.loadMarkets()
store.loadPhases()
</script>

<style scoped>
.multimarket-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.9rem;
}
.tab.active { background: var(--accent); color: white; border-color: var(--accent); }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }

.market-table { overflow-x: auto; }
.market-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.market-table th, .market-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  text-align: left;
}
.market-table th { font-weight: 600; color: var(--muted); }
.market-table tr.current { background: #f0f9ff; }

.arbitrage-form { max-width: 400px; margin-bottom: 20px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 0.85rem; margin-bottom: 4px; font-weight: 600; }
.form-group input, .form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  width: 100%;
}

.arbitrage-result {
  border-top: 1px solid var(--border);
  padding-top: 20px;
}
.result-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 12px;
}
.current-revenue, .projected-revenue { text-align: center; }
.current-revenue span:first-child, .projected-revenue span:first-child {
  display: block; font-size: 0.8rem; color: var(--muted);
}
.value { font-size: 1.5rem; font-weight: 800; }
.value.green { color: #22c55e; }
.arrow { font-size: 2rem; color: var(--muted); }

.increase-badge {
  text-align: center;
  font-size: 1.8rem;
  font-weight: 800;
  color: #22c55e;
  margin-bottom: 16px;
}

.breakdown { display: grid; gap: 8px; margin-bottom: 16px; }
.market-breakdown {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.recommendation {
  padding: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: var(--radius);
  font-size: 0.85rem;
}

.phase-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 12px;
}
.phase-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.phase-header h3 { margin: 0; font-size: 1rem; }
.phase-duration {
  font-size: 0.8rem;
  color: var(--muted);
  background: var(--bg);
  padding: 2px 8px;
  border-radius: 4px;
}
.phase-actions { margin: 0 0 12px; padding-left: 20px; }
.phase-actions li { margin-bottom: 4px; font-size: 0.85rem; }
.milestones { font-size: 0.85rem; }
.milestones ul { margin: 4px 0 0; padding-left: 20px; }
</style>

<template>
  <div class="enforcement-roi-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>维权 ROI 计算器</h2>
      <p class="subtitle">决策树 · ROI预测 · 四层防御 · 案例库</p>

      <div class="tabs">
        <button :class="['tab', { active: tab === 'decision' }]" @click="tab = 'decision'">维权决策树</button>
        <button :class="['tab', { active: tab === 'roi' }]" @click="tab = 'roi'">ROI预测</button>
        <button :class="['tab', { active: tab === 'defense' }]" @click="tab = 'defense'">防御预算</button>
        <button :class="['tab', { active: tab === 'cases' }]" @click="tab = 'cases'">案例库</button>
      </div>

      <!-- 维权决策树 -->
      <div v-if="tab === 'decision'" class="section">
        <div class="form-inline">
          <div class="form-group">
            <label>侵权类型</label>
            <select v-model="decisionForm.infringement_type">
              <option value="platform_copy">平台内容复制</option>
              <option value="commercial_use">商业滥用</option>
              <option value="ai_training">AI训练使用</option>
              <option value="social_share">社交分享</option>
              <option value="reverse_image">图片反向搜索发现</option>
            </select>
          </div>
          <div class="form-group">
            <label>预估损失 (元)</label>
            <input type="number" v-model.number="decisionForm.loss_amount" />
          </div>
          <button class="btn-primary" @click="runDecision">分析维权路径</button>
        </div>

        <div v-if="store.decisionTree" class="decision-result">
          <p class="reasoning">{{ store.decisionTree.reasoning }}</p>
          <div v-for="(action, i) in store.decisionTree.recommended_actions" :key="i" class="action-card">
            <div class="action-header">
              <strong>{{ i + 1 }}. {{ action.name_zh }}</strong>
              <span class="win-rate">胜率 {{ (action.win_rate * 100).toFixed(0) }}%</span>
            </div>
            <div class="action-details">
              <span>费用: ¥{{ action.estimated_cost[0] }}-¥{{ action.estimated_cost[1] }}</span>
              <span>耗时: {{ action.expected_duration_days[0] }}-{{ action.expected_duration_days[1] }}天</span>
            </div>
            <span v-if="action.note_zh" class="note">{{ action.note_zh }}</span>
          </div>
        </div>
      </div>

      <!-- ROI预测 -->
      <div v-if="tab === 'roi'" class="section">
        <div class="form-grid">
          <div class="form-group">
            <label>作品价值 (元)</label>
            <input type="number" v-model.number="roiForm.work_value_yuan" />
          </div>
          <div class="form-group">
            <label>侵权类型</label>
            <select v-model="roiForm.infringement_type">
              <option value="platform_copy">平台内容复制</option>
              <option value="commercial_use">商业滥用</option>
              <option value="ai_training">AI训练使用</option>
              <option value="social_share">社交分享</option>
              <option value="reverse_image">图片反向搜索发现</option>
            </select>
          </div>
          <div class="form-group">
            <label>目标平台</label>
            <select v-model="roiForm.target_platform">
              <option value="xiaohongshu">小红书</option>
              <option value="weibo">微博</option>
              <option value="douyin">抖音</option>
              <option value="taobao">淘宝</option>
              <option value="amazon">Amazon</option>
              <option value="etsy">Etsy</option>
              <option value="youtube">YouTube</option>
              <option value="generic">通用平台</option>
            </select>
          </div>
          <div class="form-group">
            <label>维权方式</label>
            <select v-model="roiForm.action_type">
              <option value="platform_complaint">平台投诉</option>
              <option value="cease_desist">律师函</option>
              <option value="civil_lawsuit">民事诉讼</option>
              <option value="criminal_report">刑事报案</option>
            </select>
          </div>
          <button class="btn-primary" @click="runRoi">预测ROI</button>
        </div>

        <div v-if="store.roiPrediction" class="roi-result">
          <div class="roi-main">
            <div class="roi-value" :class="store.roiPrediction.roi_percent > 100 ? 'positive' : store.roiPrediction.roi_percent > 0 ? 'neutral' : 'negative'">
              ROI {{ store.roiPrediction.roi_percent > 0 ? '+' : '' }}{{ store.roiPrediction.roi_percent }}%
            </div>
            <div class="risk-badge" :class="store.roiPrediction.risk_level">
              风险: {{ store.roiPrediction.risk_level === 'low' ? '低' : store.roiPrediction.risk_level === 'medium' ? '中' : '高' }}
            </div>
          </div>
          <div class="roi-breakdown">
            <div class="stat"><span>预期成本</span><strong>¥{{ store.roiPrediction.expected_cost.toLocaleString() }}</strong></div>
            <div class="stat"><span>预期周期</span><strong>{{ store.roiPrediction.expected_duration_days }}天</strong></div>
            <div class="stat"><span>胜率</span><strong>{{ store.roiPrediction.win_probability }}%</strong></div>
            <div class="stat"><span>预期赔偿</span><strong>¥{{ store.roiPrediction.expected_compensation.toLocaleString() }}</strong></div>
            <div class="stat"><span>净收益</span><strong :class="store.roiPrediction.net_return >= 0 ? 'green' : 'red'">¥{{ store.roiPrediction.net_return.toLocaleString() }}</strong></div>
          </div>
        </div>
      </div>

      <!-- 四层防御预算 -->
      <div v-if="tab === 'defense'" class="section">
        <div class="defense-grid">
          <div v-for="tier in store.defenseTiers" :key="tier.tier_key" class="defense-card">
            <div class="tier-badge" :class="tier.tier_key">{{ tier.tier_name_zh }}</div>
            <div class="tier-cost">
              <span v-if="tier.monthly_cost_high && tier.monthly_cost_high > 0">
                ¥{{ tier.monthly_cost_low }}-¥{{ tier.monthly_cost_high }}/月
              </span>
              <span v-else>免费</span>
            </div>
            <p class="tier-desc">{{ tier.description_zh }}</p>
            <ul class="tier-features">
              <li v-for="f in tier.features" :key="f">{{ f }}</li>
            </ul>
            <div class="tier-recommended">{{ tier.recommended_for }}</div>
          </div>
        </div>
      </div>

      <!-- 案例库 -->
      <div v-if="tab === 'cases'" class="section">
        <div class="case-list">
          <div v-for="c in store.caseReferences" :key="c.id" class="case-item">
            <div class="case-type">{{ infringementLabel(c.infringement_type) }}</div>
            <div class="case-platform">{{ platformLabel(c.target_platform) }}</div>
            <div class="case-stats">
              <span>胜率 {{ c.win_rate_percent }}%</span>
              <span>平均赔偿 ¥{{ (c.avg_compensation_yuan || 0).toLocaleString() }}</span>
            </div>
            <div class="case-roi" :class="c.roi_tier">
              {{ roiTierLabel(c.roi_tier) }}
            </div>
            <p class="case-desc">{{ c.description_zh }}</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useEnforcementRoiStore } from '@/stores/useEnforcementRoiStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useEnforcementRoiStore()
const tab = ref('decision')

const decisionForm = ref({
  infringement_type: 'platform_copy',
  loss_amount: 10000,
})

const roiForm = ref({
  work_value_yuan: 50000,
  infringement_type: 'commercial_use',
  target_platform: 'taobao',
  action_type: 'cease_desist',
})

async function runDecision() {
  await store.runDecisionTree(decisionForm.value.infringement_type, decisionForm.value.loss_amount)
}

async function runRoi() {
  await store.runRoiPrediction(roiForm.value)
}

function infringementLabel(key: string): string {
  const map: Record<string, string> = {
    platform_copy: '平台复制', commercial_use: '商业滥用', ai_training: 'AI训练',
    social_share: '社交分享', reverse_image: '反向图片搜索',
  }
  return map[key] || key
}

function platformLabel(code: string): string {
  const map: Record<string, string> = {
    xiaohongshu: '小红书', weibo: '微博', douyin: '抖音', taobao: '淘宝',
    amazon: 'Amazon', etsy: 'Etsy', youtube: 'YouTube', generic: '通用平台',
  }
  return map[code] || code
}

function roiTierLabel(tier?: string): string {
  const map: Record<string, string> = {
    high: '高ROI (+500%)', medium: '中ROI (100-500%)', low_negative: '低/负ROI (<100%)',
  }
  return map[tier || ''] || tier || ''
}

// Init
store.loadDefenseTiers()
store.loadCaseReferences()
</script>

<style scoped>
.enforcement-roi-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.tab {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.85rem;
}
.tab.active { background: var(--accent); color: white; border-color: var(--accent); }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }

.form-inline { display: flex; gap: 12px; align-items: flex-end; margin-bottom: 20px; flex-wrap: wrap; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px; }
.form-group { display: flex; flex-direction: column; }
.form-group label { font-size: 0.8rem; margin-bottom: 4px; font-weight: 600; color: var(--muted); }
.form-group input, .form-group select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
}
.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
  height: fit-content;
}

/* Decision tree */
.reasoning {
  padding: 12px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius);
  font-size: 0.85rem;
  margin-bottom: 16px;
}
.action-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
  margin-bottom: 8px;
}
.action-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}
.win-rate {
  font-size: 0.8rem;
  color: #22c55e;
  font-weight: 600;
}
.action-details {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
  color: var(--muted);
}
.note {
  display: block;
  margin-top: 6px;
  font-size: 0.8rem;
  color: #f59e0b;
  font-style: italic;
}

/* ROI result */
.roi-main {
  text-align: center;
  margin-bottom: 20px;
}
.roi-value {
  font-size: 2.2rem;
  font-weight: 800;
}
.roi-value.positive { color: #22c55e; }
.roi-value.neutral { color: #3b82f6; }
.roi-value.negative { color: #ef4444; }
.risk-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  margin-top: 8px;
}
.risk-badge.low { background: #dcfce7; color: #16a34a; }
.risk-badge.medium { background: #dbeafe; color: #2563eb; }
.risk-badge.high { background: #fee2e2; color: #dc2626; }

.roi-breakdown {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}
.stat {
  text-align: center;
  padding: 12px;
  background: var(--bg);
  border-radius: var(--radius-sm);
}
.stat span { display: block; font-size: 0.75rem; color: var(--muted); margin-bottom: 4px; }
.stat strong { font-size: 1rem; }
.stat .green { color: #22c55e; }
.stat .red { color: #ef4444; }

/* Defense tiers */
.defense-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.defense-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
.tier-badge {
  font-weight: 700;
  font-size: 0.9rem;
  margin-bottom: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}
.tier-badge.zero { background: #f3f4f6; color: #6b7280; }
.tier-badge.low { background: #dbeafe; color: #2563eb; }
.tier-badge.mid { background: #fef3c7; color: #d97706; }
.tier-badge.high { background: #dcfce7; color: #16a34a; }
.tier-cost { font-size: 0.85rem; color: var(--muted); margin-bottom: 8px; }
.tier-desc { font-size: 0.8rem; color: var(--muted); margin-bottom: 8px; }
.tier-features { margin: 0; padding-left: 16px; font-size: 0.8rem; }
.tier-features li { margin-bottom: 2px; }
.tier-recommended {
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--muted);
  font-style: italic;
}

/* Case list */
.case-list { display: grid; gap: 12px; }
.case-item {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
}
.case-type { font-weight: 700; font-size: 0.85rem; }
.case-platform { font-size: 0.8rem; color: var(--muted); }
.case-stats {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
  margin: 6px 0;
}
.case-roi {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}
.case-roi.high { background: #dcfce7; color: #16a34a; }
.case-roi.medium { background: #fef3c7; color: #d97706; }
.case-roi.low_negative { background: #fee2e2; color: #dc2626; }
.case-desc { font-size: 0.8rem; color: var(--muted); margin-top: 6px; }
</style>

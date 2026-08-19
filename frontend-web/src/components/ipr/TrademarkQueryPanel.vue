<template>
  <div class="tm-query-panel">
    <div class="panel-title">🔍 商标查询</div>
    <div class="panel-desc">查询前先检索是否有高度相似的已有注册商标</div>

    <div class="query-form">
      <div class="form-row">
        <label class="form-label">查询关键词</label>
        <input
          v-model="queryText"
          class="form-input"
          placeholder="输入商标名称（如：麒麟、应龙）"
          @keyup.enter="doQuery"
        />
      </div>
      <div class="form-row">
        <label class="form-label">查询辖区</label>
        <select v-model="jurisdiction" class="form-input">
          <option value="cn">🇨🇳 中国 (CNIPA)</option>
          <option value="us">🇺🇸 美国 (USPTO)</option>
          <option value="eu">🇪🇺 欧盟 (EUIPO)</option>
          <option value="wipo">🌐 WIPO</option>
        </select>
        <label class="form-label">尼斯分类</label>
        <select v-model="classNo" class="form-input">
          <option value="">不限</option>
          <option value="9">第9类 — 数字产品</option>
          <option value="16">第16类 — 印刷品、文具</option>
          <option value="21">第21类 — 家居用品</option>
          <option value="25">第25类 — 服装、鞋帽</option>
          <option value="28">第28类 — 玩具、运动</option>
          <option value="35">第35类 — 广告、商业管理</option>
          <option value="41">第41类 — 教育、娱乐</option>
        </select>
      </div>
      <button class="btn btn-primary btn-sm" :disabled="!queryText || searching" @click="doQuery">
        {{ searching ? '查询中...' : '查询' }}
      </button>
    </div>

    <div v-if="results.length > 0" class="query-results">
      <div class="results-header">
        找到 <strong>{{ results.length }}</strong> 条相似商标
      </div>
      <div v-for="r in results" :key="r.name" class="result-item" :class="{ high: r.similarity >= 70, medium: r.similarity >= 40 }">
        <span class="result-name">{{ r.name }}</span>
        <span class="result-sim">相似度 {{ r.similarity }}%</span>
        <span class="result-status">{{ r.status }}</span>
        <span v-if="r.classes" class="result-classes">{{ r.classes.join('、') }}类</span>
        <span v-if="r.owner" class="result-owner">{{ r.owner }}</span>
        <div v-if="r.similarity >= 70" class="result-alert">
          ⚠️ 高度相似，建议考虑替代名称
        </div>
      </div>
      <div v-if="highSimilarityResults.length > 0" class="suggestion-banner">
        💡 建议：第{{ highSimilarityResults[0]?.classes?.[0] || '' }}类已有高度相似注册商标，建议考虑替代名称或咨询律师
      </div>
    </div>

    <div v-else-if="queried" class="no-results">
      未找到相似商标，可以安全推进申请
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { iprApi } from '@/api/ipr'

const props = defineProps<{
  jurisdiction?: string
  workTitle?: string
  queryText?: string
}>()

const emit = defineEmits<{
  query: [jurisdiction: string, text: string, classes: string[]]
  viewDetail: [name: string]
  ignore: [name: string]
}>()

const localJurisdiction = ref(props.jurisdiction || 'cn')
const localQueryText = ref(props.queryText || '')
const classNo = ref<string>('')
const results = ref<any[]>([])
const searching = ref(false)
const queried = ref(false)

const highSimilarityResults = ref<any[]>([])

async function doQuery() {
  if (!localQueryText.value.trim()) return
  searching.value = true
  queried.value = true
  try {
    const res = await iprApi.trademarkQuery({
      text: localQueryText.value,
      jurisdiction: localJurisdiction.value,
      class_no: classNo.value || undefined,
    })
    results.value = res.data?.data?.results || []
    highSimilarityResults.value = results.value.filter((r: any) => r.similarity >= 70)
    emit('query', localJurisdiction.value, localQueryText.value, [classNo.value].filter(Boolean))
  } catch {
    results.value = []
  } finally {
    searching.value = false
  }
}
</script>

<style scoped>
.tm-query-panel { padding: 16px; }
.panel-title { font-size: 1rem; font-weight: 700; margin-bottom: 4px; }
.panel-desc { font-size: 0.82rem; color: var(--muted); margin-bottom: 12px; }
.query-form { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.form-row { display: flex; gap: 8px; align-items: center; }
.form-label { font-size: 0.82rem; color: var(--muted); white-space: nowrap; }
.form-input {
  padding: 6px 10px; border: 1px solid var(--border); border-radius: var(--m-radius-sm);
  font-size: 0.85rem; background: var(--surface); color: var(--fg); outline: none;
}
.form-input:focus { border-color: var(--accent); }
.query-results { margin-top: 12px; }
.results-header { font-size: 0.85rem; color: var(--fg); margin-bottom: 8px; }
.result-item {
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  padding: 8px 10px; border: 1px solid var(--border); border-radius: var(--m-radius-sm);
  margin-bottom: 6px; font-size: 0.82rem;
}
.result-item.high { border-color: #ef4444; background: rgba(239,68,68,0.05); }
.result-item.medium { border-color: #f59e0b; background: rgba(245,158,11,0.05); }
.result-name { font-weight: 600; }
.result-sim { color: var(--orange); font-weight: 600; }
.result-status { color: var(--muted); }
.result-classes { color: var(--muted); }
.result-owner { color: var(--muted); font-style: italic; }
.result-alert { width: 100%; color: #ef4444; font-size: 0.8rem; font-weight: 600; }
.suggestion-banner {
  margin-top: 8px; padding: 10px; background: #fffbeb; border: 1px solid #fde68a;
  border-radius: var(--m-radius-sm); font-size: 0.82rem; color: #92400e;
}
.no-results { color: var(--green); font-size: 0.85rem; padding: 12px 0; }
</style>

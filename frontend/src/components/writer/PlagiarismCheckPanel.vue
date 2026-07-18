<script setup lang="ts">
import { ref } from 'vue'

interface MatchSource { url: string; similarity: number; excerpt: string }
interface PlagiarismResult { match_rate: number; sources: MatchSource[] }

const checking = ref(false)
const result = ref<PlagiarismResult | null>(null)

async function runCheck() {
  checking.value = true
  await new Promise(r => setTimeout(r, 1500))
  result.value = { match_rate: 12.5, sources: [
    { url: 'https://example.com/article', similarity: 8.3, excerpt: '部分段落存在相似内容...' },
    { url: 'https://example.net/essay', similarity: 4.2, excerpt: '引言部分有引用...' },
  ]}
  checking.value = false
}

function exportReport() {
  if (!result.value) return
  const json = JSON.stringify(result.value, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = 'plagiarism_report.json'; a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="plagiarism-check-panel">
    <div class="panel-header">
      <h3>文本查重</h3>
      <button @click="runCheck" :disabled="checking" class="btn btn-primary btn-sm">{{ checking ? '查重中...' : '开始查重' }}</button>
    </div>
    <div v-if="!result" class="empty-state">点击"开始查重"检测文本相似度</div>
    <div v-else class="results">
      <div class="match-rate">匹配率: <strong>{{ result.match_rate }}%</strong></div>
      <div v-if="result.sources.length" class="sources">
        <h4>匹配来源</h4>
        <div v-for="source in result.sources" :key="source.url" class="source-item">
          <a :href="source.url" target="_blank">{{ source.url }}</a>
          <span class="similarity">{{ source.similarity }}% 相似</span>
          <pre class="excerpt">{{ source.excerpt }}</pre>
        </div>
      </div>
      <div class="actions"><button class="btn btn-outline btn-sm" @click="exportReport">导出报告 (JSON)</button></div>
    </div>
  </div>
</template>

<style scoped>
.plagiarism-check-panel { padding: 16px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.empty-state { padding: 24px; text-align: center; color: #9ca3af; font-size: 14px; }
.match-rate { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 14px; }
.sources { margin-bottom: 12px; }
.sources h4 { font-size: 14px; margin: 0 0 8px; }
.source-item { padding: 10px; border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: 8px; }
.source-item a { color: #3b82f6; text-decoration: none; font-size: 13px; }
.similarity { float: right; font-size: 12px; color: #f59e0b; font-weight: 600; }
.excerpt { background: #f9fafb; padding: 8px; border-radius: 4px; font-size: 12px; margin: 8px 0 0; white-space: pre-wrap; max-height: 60px; overflow: auto; }
.actions { display: flex; gap: 8px; }
.btn-sm { padding: 4px 12px; font-size: 13px; }
</style>

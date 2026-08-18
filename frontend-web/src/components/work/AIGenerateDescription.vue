<template>
  <div class="ai-desc-panel">
    <div v-if="loading" class="ai-desc-loading">
      <div class="spinner" />
      <span>AI 生成中...</span>
    </div>
    <div v-else-if="result" class="ai-desc-result">
      <div class="desc-field">
        <label>标题</label>
        <input v-model="result.title" class="desc-input" />
      </div>
      <div class="desc-field">
        <label>描述</label>
        <textarea v-model="result.description" class="desc-textarea" rows="4" />
      </div>
      <div class="desc-field" v-if="result.specs?.length">
        <label>规格</label>
        <div class="desc-specs">
          <span v-for="(s, i) in result.specs" :key="i" class="spec-item">{{ s }}</span>
        </div>
      </div>
      <div class="desc-field" v-if="result.tags?.length">
        <label>标签</label>
        <div class="desc-tags">
          <span v-for="(t, i) in result.tags" :key="i" class="tag-pill">{{ t }}</span>
        </div>
      </div>
      <div class="desc-field">
        <label>价格建议</label>
        <input v-model="result.price_range" class="desc-input" />
      </div>
      <div class="desc-actions">
        <button class="btn btn-primary" @click="applyResult">应用</button>
        <button class="btn btn-secondary" @click="onRetry">重新生成</button>
        <button class="btn btn-ghost" @click="$emit('close')">关闭</button>
      </div>
    </div>
    <div v-else class="ai-desc-empty">
      <p>点击「AI 生成描述」按钮开始生成作品描述</p>
      <button class="btn btn-primary" @click="generate" :disabled="disabled">✨ AI 生成描述</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import client from '@/api/client'

const props = defineProps<{ workId: string; disabled?: boolean }>()
const emit = defineEmits<{ apply: [data: { title: string; description: string; specs: string[]; tags: string[]; price_range: string }], close: [] }>()

const loading = ref(false)
const result = ref<{ title: string; description: string; specs: string[]; tags: string[]; price_range: string } | null>(null)

async function generate() {
  loading.value = true
  try {
    const resp = await client.post(`/works/${props.workId}/describe`, {})
    const data = resp.data.data
    result.value = {
      title: data.title || '',
      description: data.description || '',
      specs: data.specs || [],
      tags: data.tags || [],
      price_range: data.price_range || '',
    }
  } catch (e: any) {
    console.error('describe_work failed:', e)
  } finally {
    loading.value = false
  }
}

function applyResult() {
  if (!result.value) return
  emit('apply', result.value)
}

function onRetry() {
  result.value = null
  generate()
}
</script>

<style scoped>
.ai-desc-panel { padding: 16px; }
.ai-desc-loading { display: flex; align-items: center; gap: 12px; padding: 24px; color: #64748B; }
.spinner { width: 20px; height: 20px; border: 2px solid rgba(220,38,38, 1); border-top-color: #64748B; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-desc-result { display: flex; flex-direction: column; gap: 12px; }
.desc-field { display: flex; flex-direction: column; gap: 4px; }
.desc-field label { font-size: 12px; font-weight: 600; color: 0284C7; text-transform: uppercase; letter-spacing: 0.05em; }
.desc-input, .desc-textarea {
  width: 100%; padding: 8px 12px; border: 1px solid #E2E8F0; border-radius: var(--m-radius-md, 12px);
  font-size: 14px; color: #0F172A; background: #FFFFFF;
  font-family: inherit; resize: vertical;
}
.desc-input:focus, .desc-textarea:focus { outline: none; border-color: #64748B; }
.desc-specs { display: flex; flex-direction: column; gap: 4px; }
.spec-item { font-size: 13px; color: 0284C7; padding: 2px 0; }
.desc-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-pill {
  padding: 2px 10px; border-radius: var(--m-radius-lg, 16px); font-size: 12px;
  background: #E2E8F0; color: 0284C7;
}
.desc-actions { display: flex; gap: 8px; margin-top: 4px; }
.btn { padding: 8px 16px; border-radius: var(--m-radius-md, 12px); font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.btn-primary { background: #64748B; color: white; }
.btn-secondary { background: #E2E8F0; color: #334155; }
.btn-ghost { background: transparent; color: #64748B; border: 1px solid #E2E8F0; }
.ai-desc-empty { text-align: center; padding: 32px 16px; color: #64748B; }
.ai-desc-empty p { margin-bottom: 16px; font-size: 14px; }
</style>

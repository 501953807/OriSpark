<template>
  <div class="ai-session-panel">
    <h3>AI 创作会话记录</h3>

    <!-- 新增表单 -->
    <div class="add-form">
      <input v-model="newTool" placeholder="工具名称 (如 Midjourney)" class="input" />
      <input v-model="newPrompt" placeholder="提示词 (prompt)" class="input" />
      <input v-model="newModel" placeholder="模型 (如 v6.0)" class="input" />
      <button class="btn-add" @click="addSession" :disabled="!newTool || !newPrompt">
        记录会话
      </button>
    </div>

    <!-- 时间线 -->
    <div class="timeline">
      <div v-if="sessions.length === 0" class="empty">暂无 AI 会话记录</div>
      <div v-for="(s, i) in sessions" :key="s.id" class="timeline-item">
        <div class="timeline-dot" :class="{ active: i === 0 }"></div>
        <div class="timeline-content">
          <div class="timeline-header">
            <span class="tool-name">{{ s.tool_name }}</span>
            <span v-if="s.model_name" class="model-name">{{ s.model_name }}</span>
            <span class="time">{{ s.created_at ? new Date(s.created_at).toLocaleString('zh-CN') : '' }}</span>
          </div>
          <div class="prompt-text">{{ s.prompt }}</div>
          <div v-if="s.seed" class="seed-info">Seed: {{ s.seed }}</div>
          <button class="btn-delete" @click="$emit('delete', s.id)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { AiSession } from '@/types/illustrator'

const props = defineProps<{ workId: string }>()
const emit = defineEmits<{
  delete: [sessionId: string]
  add: [session: { tool_name: string; prompt: string; model_name?: string }]
}>()

defineSlots<{
  default?: unknown
}>()

const sessions = defineModel<AiSession[]>('sessions', { required: true })

const newTool = ref('')
const newPrompt = ref('')
const newModel = ref('')

function addSession() {
  if (!newTool.value || !newPrompt.value) return
  emit('add', {
    tool_name: newTool.value,
    prompt: newPrompt.value,
    model_name: newModel.value || undefined,
  })
  newTool.value = ''
  newPrompt.value = ''
  newModel.value = ''
}
</script>

<style scoped>
.ai-session-panel { padding: 16px 0; }
h3 { font-size: 1rem; margin-bottom: 12px; }
.add-form { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.input { flex: 1; min-width: 120px; padding: 6px 10px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.85rem; }
.btn-add { padding: 6px 16px; background: var(--accent); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.85rem; white-space: nowrap; }
.btn-add:disabled { opacity: 0.5; cursor: not-allowed; }
.timeline { position: relative; padding-left: 20px; }
.timeline-item { position: relative; padding: 10px 0 10px 16px; border-left: 2px solid var(--border); }
.timeline-dot { position: absolute; left: -7px; top: 14px; width: 12px; height: 12px; border-radius: 50%; background: var(--border); }
.timeline-dot.active { background: var(--accent); }
.timeline-content { font-size: 0.85rem; }
.timeline-header { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; }
.tool-name { font-weight: 600; }
.model-name { color: var(--muted); font-size: 0.8rem; }
.time { margin-left: auto; color: var(--muted); font-size: 0.75rem; }
.prompt-text { color: var(--text-secondary); line-height: 1.4; margin-bottom: 4px; }
.seed-info { font-size: 0.75rem; color: var(--muted); }
.btn-delete { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.75rem; margin-top: 4px; }
.empty { color: var(--muted); font-size: 0.85rem; padding: 20px 0; text-align: center; }
</style>

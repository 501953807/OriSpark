<template>
  <div class="ai-session-timeline">
    <div class="timeline-header">
      <h4>AI 创作时间线</h4>
      <button class="btn-add" @click="showForm = !showForm">
        {{ showForm ? '收起' : '+ 记录会话' }}
      </button>
    </div>

    <!-- Add form -->
    <div v-if="showForm" class="add-form">
      <input v-model="form.tool_name" class="input" placeholder="工具名称 (如 Midjourney)" />
      <input v-model="form.model_name" class="input" placeholder="模型/版本 (如 v6.0)" />
      <textarea v-model="form.prompt" class="textarea" rows="2" placeholder="提示词 (prompt)" />
      <input v-model="form.seed" class="input" placeholder="Seed (可选)" type="number" />
      <button class="btn-save" :disabled="!form.tool_name || !form.prompt" @click="addSession">
        保存记录
      </button>
    </div>

    <!-- Timeline -->
    <div v-if="sessions.length === 0" class="empty">
      暂无 AI 创作会话记录，点击上方按钮添加。
    </div>
    <div v-else class="timeline">
      <div v-for="(session, index) in sessions" :key="session.id" class="session-item">
        <div class="session-dot" :class="{ active: index === 0 }"></div>
        <div class="session-content">
          <div class="session-header">
            <span class="tool-name">{{ session.tool_name }}</span>
            <span v-if="session.model_name" class="model-name">{{ session.model_name }}</span>
            <span class="time">{{ formatTime(session.created_at) }}</span>
            <button class="btn-delete" @click="deleteSession(session.id)">删除</button>
          </div>
          <div v-if="session.prompt" class="prompt-text">{{ session.prompt }}</div>
          <div v-if="session.seed" class="seed-info">Seed: {{ session.seed }}</div>
          <div v-if="session.lora_names?.length" class="lora-info">
            LoRA: {{ session.lora_names.join(', ') }}
          </div>
          <div v-if="session.human_interventions?.length" class="intervention-info">
            人工干预: {{ session.human_interventions.join('、') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { illustratorApi } from '@/api/illustrator'
import type { AiSession } from '@/types/illustrator'

const props = defineProps<{ workId: string }>()

const sessions = ref<AiSession[]>([])
const showForm = ref(false)
const form = ref({
  tool_name: '',
  model_name: '',
  prompt: '',
  seed: null as number | null,
})

async function fetchSessions() {
  try {
    const res = await illustratorApi.getSessions(props.workId)
    sessions.value = res.data.data || []
  } catch {
    // ignore
  }
}

async function addSession() {
  if (!form.value.tool_name || !form.value.prompt) return
  try {
    await illustratorApi.createSession(props.workId, {
      tool_name: form.value.tool_name,
      model_name: form.value.model_name || undefined,
      prompt: form.value.prompt,
      seed: form.value.seed !== null ? form.value.seed : undefined,
    })
    form.value = { tool_name: '', model_name: '', prompt: '', seed: null }
    showForm.value = false
    await fetchSessions()
  } catch {
    // ignore
  }
}

async function deleteSession(sessionId: string) {
  try {
    await illustratorApi.deleteSession(props.workId, sessionId)
    await fetchSessions()
  } catch {
    // ignore
  }
}

function formatTime(dateStr: string | null) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(fetchSessions)
</script>

<style scoped>
.ai-session-timeline { padding: 12px 0; }
.timeline-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.timeline-header h4 { margin: 0; font-size: 0.95rem; }
.btn-add {
  background: none; border: 1px solid var(--border); border-radius: var(--m-radius-sm);
  padding: 4px 12px; font-size: 0.8rem; cursor: pointer; color: var(--fg);
}
.btn-add:hover { border-color: var(--accent); color: var(--accent); }
.add-form {
  display: flex; flex-direction: column; gap: 8px; padding: 12px;
  background: var(--surface-2); border-radius: var(--m-radius-sm); margin-bottom: 12px;
}
.input, .textarea {
  padding: 7px 10px; border: 1px solid var(--border); border-radius: var(--m-radius-sm);
  font-size: 0.85rem; font-family: Inter; color: var(--fg); background: var(--surface); outline: none;
}
.input:focus, .textarea:focus { border-color: var(--accent); }
.textarea { resize: vertical; }
.btn-save {
  padding: 7px 16px; background: var(--accent); color: #fff; border: none;
  border-radius: var(--m-radius-sm); font-size: 0.85rem; cursor: pointer; font-weight: 600;
}
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
.empty { color: var(--muted); font-size: 0.85rem; text-align: center; padding: 20px 0; }
.timeline { position: relative; padding-left: 20px; }
.session-item { position: relative; padding: 10px 0 10px 16px; border-left: 2px solid var(--border); }
.session-dot {
  position: absolute; left: -7px; top: 14px; width: 12px; height: 12px;
  border-radius: 50%; background: var(--border);
}
.session-dot.active { background: var(--accent); }
.session-header { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; }
.tool-name { font-weight: 600; font-size: 0.9rem; }
.model-name { color: var(--muted); font-size: 0.78rem; }
.time { margin-left: auto; color: var(--muted); font-size: 0.75rem; }
.prompt-text { color: var(--text-secondary); line-height: 1.5; margin-bottom: 4px; font-size: 0.85rem; }
.seed-info, .lora-info, .intervention-info { font-size: 0.78rem; color: var(--muted); margin-bottom: 2px; }
.btn-delete { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.75rem; }
</style>

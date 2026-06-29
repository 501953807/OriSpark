<template>
  <div class="project-info-card card">
    <div class="card-header-row">
      <h3>📁 所属项目</h3>
      <button v-if="work?.project_id" class="btn btn-ghost btn-sm" @click="showChange = true">更换</button>
      <button v-else class="btn btn-ghost btn-sm" @click="showChange = true">分配项目</button>
    </div>
    <div v-if="work?.project" class="project-display">
      <span class="project-name">{{ work.project.name }}</span>
      <span class="project-count">{{ work.project.work_count || 0 }} 个作品</span>
    </div>
    <div v-else class="project-none">未分配项目</div>

    <!-- Change project modal -->
    <div v-if="showChange" class="modal-overlay" @click.self="showChange = false">
      <div class="modal-card">
        <h3>更换项目</h3>
        <select v-model="selectedProjectId" class="form-input">
          <option :value="null">未分配</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.name }} ({{ p.work_count || 0 }} 个作品)
          </option>
        </select>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showChange = false">取消</button>
          <button class="btn btn-primary" @click="handleChangeProject">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { worksApi } from '@/api/works'

const props = defineProps<{
  work: {
    id: string
    project_id?: string | null
    project?: { name: string; id: string; work_count?: number } | null
  } | null
}>()

const emit = defineEmits<{
  projectChanged: []
}>()

const showChange = ref(false)
const selectedProjectId = ref<string | null>(null)
const projects = ref<any[]>([])

watch(() => props.work?.project_id, (pid) => {
  selectedProjectId.value = pid || null
}, { immediate: true })

async function loadProjects() {
  try {
    const res = await worksApi.listProjects()
    projects.value = res.data.data || []
  } catch {
    projects.value = []
  }
}

loadProjects()

async function handleChangeProject() {
  if (!props.work) return
  try {
    if (selectedProjectId.value) {
      await worksApi.assignProject(props.work.id, selectedProjectId.value)
    } else {
      await worksApi.update(props.work.id, { project_id: null })
    }
    showChange.value = false
    emit('projectChanged')
    ;(window as any).$toast?.show('项目已更新', 'success')
  } catch {
    ;(window as any).$toast?.show('更新项目失败', 'error')
  }
}
</script>

<style scoped>
.project-info-card { padding: 16px 20px; }
.project-info-card h3 { margin: 0; font-size: 0.88rem; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-header-row h3 { margin: 0; font-size: 0.88rem; }
.project-display { display: flex; align-items: center; gap: 8px; }
.project-name { font-size: 0.88rem; font-weight: 600; }
.project-count { font-size: 0.72rem; color: var(--muted); }
.project-none { font-size: 0.82rem; color: var(--muted); font-style: italic; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.form-input {
  padding: 9px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none; width: 100%;
}
</style>

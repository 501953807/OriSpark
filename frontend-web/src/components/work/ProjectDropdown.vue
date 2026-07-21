<template>
  <div class="project-dropdown">
    <select :value="modelValue" @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value || null)">
      <option value="">未分组</option>
      <option v-for="p in projects" :key="p.id" :value="p.id">
        {{ p.name }} ({{ p.work_count || 0 }})
      </option>
    </select>
    <button class="btn-create" @click="showCreate = true" title="新建项目">+</button>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header">
          <h3>新建项目</h3>
          <button class="modal-close-btn" @click="showCreate = false">×</button>
        </div>
        <div class="form-group">
          <label>项目名称</label>
          <input v-model="form.name" class="form-input" placeholder="如: 山海经系列" autofocus />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="form.description" class="form-textarea" rows="2" placeholder="可选…" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="handleCreate">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { worksApi } from '@/api/works'

const props = defineProps<{
  modelValue?: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [val: string | null]
}>()

const projects = ref<any[]>([])
const showCreate = ref(false)
const form = ref({ name: '', description: '' })

onMounted(async () => {
  try {
    const res = await worksApi.listProjects()
    projects.value = res.data.data || []
  } catch { projects.value = [] }
})

async function handleCreate() {
  if (!form.value.name.trim()) return
  try {
    await worksApi.createProject(form.value)
    showCreate.value = false
    form.value = { name: '', description: '' }
    const res = await worksApi.listProjects()
    projects.value = res.data.data || []
  } catch {
    ;(window as any).$toast?.show('创建项目失败', 'error')
  }
}
</script>

<style scoped>
.project-dropdown {
  display: flex;
  align-items: center;
  gap: 6px;
}

select {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-family: var(--font-body);
  color: var(--fg);
  background: var(--surface);
  cursor: pointer;
  outline: none;
  min-width: 180px;
}

select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}

.btn-create {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--surface);
  cursor: pointer;
  font-size: 1rem;
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-create:hover {
  background: oklch(56% 0.12 170 / 0.08);
  color: var(--accent);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: oklch(0 0 0 / 0.4);
  backdrop-filter: blur(4px);
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-card {
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 28px;
  max-width: 440px;
  width: 90%;
  box-shadow: 0 16px 64px oklch(0 0 0 / 0.16);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 { margin: 0; }

.modal-close-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.4rem;
  color: var(--muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.form-group { display: flex; flex-direction: column; gap: 4px; }

.form-group label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
}

.form-input, .form-textarea {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
  font-family: var(--font-body);
  color: var(--fg);
  background: var(--surface);
  outline: none;
}

.form-input:focus, .form-textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}

.form-textarea { resize: vertical; }

.btn {
  padding: 9px 18px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-family: var(--font-body);
}

.btn-primary { background: var(--accent); color: #fff; }
.btn-secondary {
  background: var(--surface);
  color: var(--fg);
  border: 1px solid var(--border);
}

.animate-scale-in {
  animation: scaleIn 0.15s ease;
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>

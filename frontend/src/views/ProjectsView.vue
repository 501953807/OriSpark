<template>
  <div class="projects-view">
    <!-- 规则说明 -->
    <div class="pv-rules card" style="padding:16px 20px;font-size:.85rem">
      <h3 style="margin:0 0 8px;font-size:.95rem">📁 项目分组说明</h3>
      <p style="margin:0 0 8px;color:var(--muted)">项目分组用于组织和管理你的创意资产。你可以按系列、客户、年份等维度创建分组，将作品归入对应分组以便查找。</p>
      <ul style="margin:0;padding-left:20px;color:var(--muted);line-height:1.8">
        <li>默认包含一个 <strong>"未分类"</strong> 分组</li>
        <li>点击分组卡片可快速筛选该分组下的所有作品</li>
        <li>删除分组不会删除其中的作品，作品将移入"未分类"</li>
      </ul>
    </div>

    <div class="actions-bar">
      <h2>📁 项目分组</h2>
      <button class="btn btn-primary" @click="showCreate = true">+ 新建项目</button>
    </div>

    <LoadingSpinner v-if="loading" />

    <EmptyState v-else-if="!projects.length" icon="📁" title="暂无项目" description="创建项目来组织你的作品" />

    <div v-else class="projects-grid">
      <div v-for="p in projects" :key="p.id" class="project-card card" @click="$router.push(`/app/works?project_id=${p.id}`)">
        <div class="proj-cover">
          <span class="proj-icon">📁</span>
          <span class="proj-count">{{ p.work_count || 0 }} 个作品</span>
        </div>
        <div class="proj-body">
          <div class="proj-name">{{ p.name }}</div>
          <div v-if="p.description" class="proj-desc">{{ p.description }}</div>
          <div class="proj-date">{{ p.created_at?.slice(0, 10) }}</div>
        </div>
        <div class="proj-actions">
          <button class="btn btn-ghost btn-sm" @click.stop="editProject(p)">✏️</button>
          <button class="btn btn-ghost btn-sm" @click.stop="deleteProject(p)">🗑️</button>
        </div>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-card animate-scale-in" style="max-width:440px">
        <div class="modal-header"><h3>{{ editing ? '编辑' : '新建' }}项目</h3><button class="modal-close-btn" @click="showCreate = false">×</button></div>
        <div class="form-group"><label>项目名称</label><input v-model="form.name" class="form-input" placeholder="如: 2026春季系列" /></div>
        <div class="form-group"><label>描述</label><textarea v-model="form.description" class="form-textarea" rows="2" placeholder="项目描述..."></textarea></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="saveProject">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { worksApi } from '@/api/works'

const projects = ref<any[]>([])
const loading = ref(true)
const showCreate = ref(false)
const editing = ref<any>(null)
const form = ref({ name: '', description: '' })

async function loadProjects() {
  loading.value = true
  try {
    const res = await worksApi.listProjects()
    projects.value = res.data.data || []
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '加载项目失败'
    ;(window as any).$toast?.show(msg, 'error')
  } finally {
    loading.value = false
  }
}

function editProject(p: any) {
  editing.value = p
  form.value = { name: p.name, description: p.description || '' }
  showCreate.value = true
}

async function saveProject() {
  if (!form.value.name.trim()) {
    ;(window as any).$toast?.show('请输入项目名称', 'error')
    return
  }
  try {
    if (editing.value) {
      await worksApi.updateProject(editing.value.id, form.value)
    } else {
      await worksApi.createProject(form.value)
    }
    showCreate.value = false
    editing.value = null
    form.value = { name: '', description: '' }
    ;(window as any).$toast?.show('项目已保存', 'success')
    loadProjects()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存项目失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function deleteProject(p: any) {
  if (!confirm(`确定删除项目"${p.name}"？作品不会被删除。`)) return
  try {
    await worksApi.deleteProject(p.id)
    ;(window as any).$toast?.show('项目已删除', 'info')
    loadProjects()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '删除项目失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

onMounted(() => loadProjects())
</script>

<style scoped>
.projects-view { display:flex; flex-direction:column; gap:20px; }
.actions-bar { display:flex; justify-content:space-between; align-items:center; }
.actions-bar h2 { margin:0; font-size:1.2rem; }
.projects-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }
.project-card { padding:0; overflow:hidden; cursor:pointer; }
.proj-cover {
  height:120px; background:oklch(56% 0.12 170 / 0.08);
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px;
}
.proj-icon { font-size:3rem; }
.proj-count { font-size:.75rem; color:var(--muted); }
.proj-body { padding:16px; }
.proj-name { font-weight:700; font-size:.95rem; }
.proj-desc { font-size:.8rem; color:var(--muted); margin-top:4px; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.proj-date { font-size:.7rem; color:var(--muted); margin-top:8px; }
.proj-actions { padding:0 16px 12px; display:flex; justify-content:flex-end; gap:4px; }
.btn-sm { padding:5px 10px; font-size:.75rem; }
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; }
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group label { font-size:.82rem; font-weight:600; color:var(--muted); }
.form-input,.form-textarea { padding:10px 14px; border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.88rem; font-family:var(--font-body); color:var(--fg); background:var(--surface); outline:none; }
.form-input:focus,.form-textarea:focus { border-color:var(--accent); box-shadow:0 0 0 3px oklch(56% 0.12 170 / .1); }
.form-textarea { resize:vertical; }
</style>

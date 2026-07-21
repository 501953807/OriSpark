<template>
  <div class="case-study-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>案例知识库</h2>
      <p class="subtitle">成功案例 · 失败教训 · 经验沉淀</p>

      <!-- 统计 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ store.stats?.total || 0 }}</div>
          <div class="stat-label">总案例</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ store.stats?.by_type?.success || 0 }}</div>
          <div class="stat-label">成功案例</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ store.stats?.by_type?.lesson || 0 }}</div>
          <div class="stat-label">教训案例</div>
        </div>
      </div>

      <!-- 分类筛选 -->
      <div class="filter-bar">
        <select v-model="filterCategory" @change="handleFilter" class="form-select">
          <option value="">全部分类</option>
          <option v-for="c in categories" :key="c.key" :value="c.key">{{ c.name_zh }}</option>
        </select>
        <select v-model="filterType" @change="handleFilter" class="form-select">
          <option value="">全部类型</option>
          <option value="success">成功案例</option>
          <option value="lesson">教训案例</option>
        </select>
        <button class="btn-add" @click="showForm = !showForm">
          {{ showForm ? '取消' : '+ 新建案例' }}
        </button>
      </div>

      <!-- 新建表单 -->
      <div v-if="showForm" class="section form-section">
        <h3>新建案例</h3>
        <input v-model="form.title" placeholder="标题" class="form-input" />
        <select v-model="form.category" class="form-select">
          <option value="">选择分类</option>
          <option v-for="c in categories" :key="c.key" :value="c.key">{{ c.name_zh }}</option>
        </select>
        <select v-model="form.case_type" class="form-select">
          <option value="success">成功案例</option>
          <option value="lesson">教训案例</option>
        </select>
        <textarea v-model="form.description" placeholder="描述" class="form-input form-textarea" />
        <input v-model="form.tagsStr" placeholder="标签 (逗号分隔)" class="form-input" />
        <button class="btn-confirm" @click="handleCreate">创建</button>
      </div>

      <!-- 案例列表 -->
      <div class="case-list">
        <div v-for="c in filteredCases" :key="c.id" class="case-card" :class="c.case_type">
          <div class="case-header">
            <strong>{{ c.title }}</strong>
            <span class="case-badge" :class="c.case_type">
              {{ c.case_type === 'success' ? '成功' : '教训' }}
            </span>
          </div>
          <p class="case-desc">{{ c.description }}</p>
          <div class="case-meta">
            <span class="case-category">{{ CATEGORY_LABELS[c.category] || c.category }}</span>
            <span v-for="t in c.tags" :key="t" class="case-tag">{{ t }}</span>
          </div>
          <div v-if="c.takeaways.length > 0" class="case-takeaways">
            <strong>关键经验:</strong>
            <ul>
              <li v-for="tw in c.takeaways" :key="tw">{{ tw }}</li>
            </ul>
          </div>
        </div>
        <div v-if="filteredCases.length === 0" class="empty-state">
          暂无案例，点击上方按钮添加。
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { useCaseStudyStore } from '@/stores/useCaseStudyStore'

const store = useCaseStudyStore()
const categories = ref<Array<{key: string; name_zh: string}>>([])
const filterCategory = ref('')
const filterType = ref('')
const showForm = ref(false)
const form = ref({
  title: '', category: '', case_type: 'success' as 'success' | 'lesson',
  description: '', tagsStr: '',
})

const CATEGORY_LABELS: Record<string, string> = {
  monetization: '变现策略', copyright: '版权保护',
  platform_growth: '平台增长', brand_collab: '品牌合作',
  failure_lesson: '失败教训',
}

const filteredCases = computed(() => {
  let cases = store.cases
  if (filterCategory.value) cases = cases.filter(c => c.category === filterCategory.value)
  if (filterType.value) cases = cases.filter(c => c.case_type === filterType.value)
  return cases
})

async function handleFilter() { await store.loadAll({ category: filterCategory.value, case_type: filterType.value }) }

async function handleCreate() {
  if (!form.value.title || !form.value.category) return
  await store.create({
    title: form.value.title,
    category: form.value.category,
    case_type: form.value.case_type,
    description: form.value.description,
    tags: form.value.tagsStr.split(',').map(t => t.trim()).filter(Boolean),
    takeaways: [],
  })
  form.value = { title: '', category: '', case_type: 'success', description: '', tagsStr: '' }
  showForm.value = false
}

onMounted(async () => {
  const catsRes = await fetch('/api/case-studies/categories')
  if (catsRes.ok) categories.value = await catsRes.json()
  await Promise.all([store.loadAll(), store.loadStats()])
})
</script>

<style scoped>
.case-study-view { max-width: 900px; margin: 0 auto; }
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; text-align: center; }
.stat-value { font-size: 1.8rem; font-weight: 800; color: var(--accent); }
.stat-label { font-size: 0.8rem; color: var(--muted); }

.filter-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.form-select { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.85rem; }
.btn-add { background: none; border: 1px dashed var(--border); padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.85rem; color: var(--accent); }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 12px; font-size: 1rem; }
.form-section .form-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.85rem; margin-bottom: 8px; }
.form-textarea { min-height: 60px; resize: vertical; }
.btn-confirm { background: var(--accent); color: white; border: none; padding: 8px 16px; border-radius: var(--radius-sm); cursor: pointer; }

.case-list { display: grid; gap: 12px; }
.case-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.case-card.success { border-left: 4px solid #22c55e; }
.case-card.lesson { border-left: 4px solid #f59e0b; }
.case-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.case-header strong { font-size: 1rem; }
.case-badge { font-size: 0.75rem; padding: 2px 10px; border-radius: 10px; font-weight: 600; }
.case-badge.success { background: #dcfce7; color: #16a34a; }
.case-badge.lesson { background: #fef3c7; color: #d97706; }
.case-desc { font-size: 0.85rem; color: var(--muted); margin: 0 0 8px; }
.case-meta { display: flex; gap: 8px; align-items: center; font-size: 0.8rem; flex-wrap: wrap; }
.case-category { background: #e0e7ff; color: #4338ca; padding: 2px 8px; border-radius: 10px; }
.case-tag { background: #f3f4f6; padding: 2px 8px; border-radius: 10px; }
.case-takeaways { margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
.case-takeaways strong { font-size: 0.85rem; }
.case-takeaways ul { margin: 4px 0 0; padding-left: 20px; font-size: 0.85rem; }
.empty-state { text-align: center; color: var(--muted); padding: 32px; font-size: 0.85rem; }
</style>

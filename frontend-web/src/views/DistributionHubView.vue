<template>
  <div class="distribution-hub-view">
      <!-- 顶部统计 -->
      <div class="stats-grid stats-grid-4" style="margin-bottom: 16px">
        <div class="stat-card">
          <div class="stat-value">{{ stats.totalLinks }}</div>
          <div class="stat-label">总链接数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.totalClicks }}</div>
          <div class="stat-label">总点击量</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ (stats.conversionRate * 100).toFixed(1) }}%</div>
          <div class="stat-label">转化率</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.activePlatforms }}</div>
          <div class="stat-label">活跃平台</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center">
          <span>分发短链管理</span>
          <button class="btn btn-primary" @click="showCreate = true">创建短链</button>
        </div>

        <table class="data-table">
          <thead>
            <tr>
              <th>平台</th>
              <th>短链代码</th>
              <th>作品 ID</th>
              <th>点击量</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in links" :key="row.id">
              <td>{{ platformLabel(row.platform_code) }}</td>
              <td><code>{{ row.short_code }}</code></td>
              <td>{{ row.work_id }}</td>
              <td>{{ row.click_count }}</td>
              <td>
                <span class="badge" :class="row.is_active ? 'badge-success' : 'badge-default'">
                  {{ row.is_active ? '活跃' : '已停用' }}
                </span>
              </td>
              <td>
                <button class="btn btn-sm btn-ghost" @click="viewAnalytics(row.id)">分析</button>
                <button class="btn btn-sm btn-ghost btn-danger" @click="handleDelete(row.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 创建短链弹窗 -->
      <div class="modal-overlay" v-if="showCreate">
        <div class="modal-card">
          <h3 style="margin: 0 0 16px">创建分发短链</h3>
          <div class="form-group" v-for="field in createFormFields" :key="field.model">
            <label class="form-label">{{ field.label }}</label>
            <select v-if="field.model === 'platform_code'" class="form-select" :value="createForm[field.model as keyof typeof createForm]">
              <option v-for="opt in field.options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
            <textarea v-else-if="field.type === 'textarea'" class="form-textarea" v-model="createForm[field.model as keyof typeof createForm]" :placeholder="field.placeholder" />
            <input v-else class="form-input" v-model="createForm[field.model as keyof typeof createForm]" :placeholder="field.placeholder" />
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary" @click="showCreate = false">取消</button>
            <button class="btn btn-primary" @click="handleCreate">创建</button>
          </div>
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/reverseTrace'

const router = useRouter()
const showCreate = ref(false)

const stats = reactive({
  totalLinks: 0,
  totalClicks: 0,
  conversionRate: 0,
  activePlatforms: 0,
})

const links = ref<any[]>([])
const showCreateLink = ref(false)

const createForm = reactive({
  work_id: '',
  platform_code: 'weixin',
  original_url: '',
  utm_source: '',
})

const platformOptions = [
  { label: '微信 WeChat', value: 'weixin' },
  { label: '抖音 Douyin', value: 'douyin' },
  { label: '小红书 Xiaohongshu', value: 'xhs' },
  { label: 'YouTube', value: 'youtube' },
  { label: 'Twitter', value: 'twitter' },
]

const createFormFields = [
  { label: '作品 ID', model: 'work_id', placeholder: 'work-001' },
  { label: '平台', model: 'platform_code', placeholder: '', options: platformOptions },
  { label: '原始 URL', model: 'original_url', placeholder: '', type: 'textarea' },
  { label: 'UTM 来源', model: 'utm_source', placeholder: '' },
]

function platformLabel(code: string): string {
  const opt = platformOptions.find(o => o.value === code)
  return opt?.label || code
}

async function fetchLinks() {
  try {
    const res = await api.list()
    links.value = res.data || []
    stats.totalLinks = links.value.length
    stats.totalClicks = links.value.reduce((s, l) => s + (l.click_count || 0), 0)
    stats.activePlatforms = new Set(links.value.map(l => l.platform_code)).size
  } catch {
    // ignore
  }
}

async function handleCreate() {
  try {
    await api.create(createForm)
    console.warn('短链已创建')
    showCreate.value = false
    fetchLinks()
  } catch {
    console.warn('创建失败')
  }
}

async function handleDelete(id: string) {
  try {
    await api.delete(id)
    console.warn('已删除')
    fetchLinks()
  } catch {
    console.warn('删除失败')
  }
}

function viewAnalytics(linkId: string) {
  router.push({ path: '/app/distribution/attribution', query: { linkId } })
}

fetchLinks()
</script>

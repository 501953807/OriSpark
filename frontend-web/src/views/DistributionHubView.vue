<template>
  <div class="distribution-hub-view">
    <n-page title="分发回流引擎" size="large">
      <!-- 顶部统计 -->
      <n-grid :cols="4" :x-gap="12" responsive="screen" style="margin-bottom: 16px">
        <n-gi>
          <n-statistic label="总链接数" :value="stats.totalLinks" />
        </n-gi>
        <n-gi>
          <n-statistic label="总点击量" :value="stats.totalClicks" />
        </n-gi>
        <n-gi>
          <n-statistic label="转化率" :value="`${(stats.conversionRate * 100).toFixed(1)}%`" />
        </n-gi>
        <n-gi>
          <n-statistic label="活跃平台" :value="stats.activePlatforms" />
        </n-gi>
      </n-grid>

      <n-card>
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center">
            <span>分发短链管理</span>
            <n-button type="primary" @click="showCreate = true">创建短链</n-button>
          </div>
        </template>

        <n-table :rows="links">
          <template #header-columns>
            <n-th>平台</n-th>
            <n-th>短链代码</n-th>
            <n-th>作品 ID</n-th>
            <n-th>点击量</n-th>
            <n-th>状态</n-th>
            <n-th>操作</n-th>
          </template>
          <template #row-columns="{ row }">
            <n-td>{{ platformLabel(row.platform_code) }}</n-td>
            <n-td><code>{{ row.short_code }}</code></n-td>
            <n-td>{{ row.work_id }}</n-td>
            <n-td>{{ row.click_count }}</n-td>
            <n-td>
              <n-tag :type="row.is_active ? 'success' : 'default'" size="small">
                {{ row.is_active ? '活跃' : '已停用' }}
              </n-tag>
            </n-td>
            <n-td>
              <n-button text type="primary" size="tiny" @click="viewAnalytics(row.id)">分析</n-button>
              <n-button text type="error" size="tiny" @click="handleDelete(row.id)">删除</n-button>
            </n-td>
          </template>
        </n-table>
      </n-card>

      <!-- 创建短链弹窗 -->
      <n-modal v-model:show="showCreate" preset="dialog" title="创建分发短链">
        <n-form :model="createForm" label-placement="left" label-width="100">
          <n-form-item label="作品 ID">
            <n-input v-model:value="createForm.work_id" placeholder="work-001" />
          </n-form-item>
          <n-form-item label="平台">
            <n-select v-model:value="createForm.platform_code" :options="platformOptions" />
          </n-form-item>
          <n-form-item label="原始 URL">
            <n-input v-model:value="createForm.original_url" type="textarea" />
          </n-form-item>
          <n-form-item label="UTM 来源">
            <n-input v-model:value="createForm.utm_source" />
          </n-form-item>
        </n-form>
        <template #action>
          <n-space>
            <n-button @click="showCreate = false">取消</n-button>
            <n-button type="primary" @click="handleCreate">创建</n-button>
          </n-space>
        </template>
      </n-modal>
    </n-page>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  NPage, NGrid, NGi, NStatistic, NCard, NTable, NTh, NTd, NButton, NTag, NModal, NForm, NFormItem, NInput, NSelect, NSpace,
} from 'naive-ui'
import { useMessage } from 'naive-ui'
import api from '@/api/reverseTrace'

const router = useRouter()
const message = useMessage()
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
    message.success('短链已创建')
    showCreate.value = false
    fetchLinks()
  } catch {
    message.error('创建失败')
  }
}

async function handleDelete(id: string) {
  try {
    await api.delete(id)
    message.success('已删除')
    fetchLinks()
  } catch {
    message.error('删除失败')
  }
}

function viewAnalytics(linkId: string) {
  router.push({ path: '/app/distribution/attribution', query: { linkId } })
}

fetchLinks()
</script>

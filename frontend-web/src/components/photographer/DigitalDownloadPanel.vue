<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePhotographerStore } from '@/stores/usePhotographerStore'
import type { DigitalDownload } from '@/api/photographer'

const store = usePhotographerStore()

interface FormState {
  work_id: string
  product_id: string
  download_url: string
  max_downloads: number
}

const form = ref<FormState>({
  work_id: '',
  product_id: '',
  download_url: '',
  max_downloads: 0,
})
const creating = ref(false)
const errorMsg = ref('')

async function handleCreate() {
  if (!form.value.work_id) {
    errorMsg.value = '请选择关联作品'
    return
  }
  creating.value = true
  try {
    await store.createDigitalDownload({
      work_id: form.value.work_id,
      product_id: form.value.product_id || null,
      download_url: form.value.download_url || null,
      max_downloads: form.value.max_downloads || null,
    })
    form.value = { work_id: '', product_id: '', download_url: '', max_downloads: 0 }
    await store.fetchDigitalDownloads()
    errorMsg.value = ''
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    creating.value = false
  }
}

async function handleDelete(dd: DigitalDownload) {
  if (!confirm(`确定删除数字预设 ${dd.id}？`)) return
  try {
    await store.deleteDigitalDownload(dd.id)
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '删除失败'
  }
}

onMounted(() => {
  store.fetchDigitalDownloads()
})
</script>

<template>
  <div class="digital-download-panel">
    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

    <!-- Create form -->
    <div class="panel-card">
      <h3 class="section-title">新建数字预设</h3>
      <div class="form-row">
        <input v-model="form.work_id" placeholder="作品 ID" class="form-input" />
        <input v-model="form.product_id" placeholder="产品 ID（可选）" class="form-input" />
        <input v-model="form.download_url" placeholder="下载链接（可选）" class="form-input" />
        <input v-model.number="form.max_downloads" type="number" placeholder="最大下载次数" class="form-input" />
        <button :disabled="creating" class="btn btn-primary" @click="handleCreate">
          {{ creating ? '创建中...' : '创建' }}
        </button>
      </div>
    </div>

    <!-- List -->
    <div class="panel-card">
      <h3 class="section-title">数字预设列表</h3>
      <table v-if="store.digitalDownloads.length" class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>作品 ID</th>
            <th>产品 ID</th>
            <th>下载链接</th>
            <th>最大次数</th>
            <th>已下载</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="dd in store.digitalDownloads" :key="dd.id">
            <td>{{ dd.id }}</td>
            <td>{{ dd.work_id }}</td>
            <td>{{ dd.product_id || '-' }}</td>
            <td>{{ dd.download_url || '-' }}</td>
            <td>{{ dd.max_downloads ?? '-' }}</td>
            <td>{{ dd.download_count }}</td>
            <td>
              <button class="btn btn-sm btn-danger" @click="handleDelete(dd)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无数字预设</div>
    </div>
  </div>
</template>

<style scoped>
.digital-download-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.panel-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
.form-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.form-input {
  flex: 1;
  min-width: 120px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.data-table th, .data-table td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border);
  text-align: left;
}
.data-table th {
  background: var(--bg);
  font-weight: 600;
}
.empty-state {
  padding: 32px;
  text-align: center;
  color: var(--muted);
}
.error-banner {
  padding: 10px 14px;
  background: oklch(65% 0.18 20);
  color: #fff;
  border-radius: var(--radius);
  font-size: 0.88rem;
}
</style>

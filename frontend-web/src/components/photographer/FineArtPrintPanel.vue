<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePhotographerStore } from '@/stores/usePhotographerStore'
import type { FineArtPrintConfig } from '@/api/photographer'

const store = usePhotographerStore()

interface FormState {
  work_id: string
  paper_type: string
  max_width_cm: number
  max_height_cm: number
  framing_available: boolean
  price_multiplier: number
}

const form = ref<FormState>({
  work_id: '',
  paper_type: 'cotton_rag',
  max_width_cm: 120,
  max_height_cm: 180,
  framing_available: false,
  price_multiplier: 1.0,
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
    await store.createFineArtPrint({
      work_id: form.value.work_id,
      paper_type: form.value.paper_type,
      max_width_cm: form.value.max_width_cm || null,
      max_height_cm: form.value.max_height_cm || null,
      framing_available: form.value.framing_available,
      price_multiplier: form.value.price_multiplier || 1.0,
    })
    form.value = {
      work_id: '',
      paper_type: 'cotton_rag',
      max_width_cm: 120,
      max_height_cm: 180,
      framing_available: false,
      price_multiplier: 1.0,
    }
    await store.fetchFineArtPrints()
    errorMsg.value = ''
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '创建失败'
  } finally {
    creating.value = false
  }
}

async function handleDelete(fap: FineArtPrintConfig) {
  if (!confirm(`确定删除艺术微喷配置 ${fap.id}？`)) return
  try {
    await store.deleteFineArtPrint(fap.id)
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : '删除失败'
  }
}

onMounted(() => {
  store.fetchFineArtPrints()
})
</script>

<template>
  <div class="fine-art-print-panel">
    <div v-if="errorMsg" class="error-banner">{{ errorMsg }}</div>

    <!-- Create form -->
    <div class="panel-card">
      <h3 class="section-title">新建艺术微喷配置</h3>
      <div class="form-row">
        <input v-model="form.work_id" placeholder="作品 ID" class="form-input" />
        <select v-model="form.paper_type" class="form-input">
          <option value="cotton_rag">纯棉无酸纸</option>
          <option value="fine_art">高级艺术纸</option>
          <option value="photo_paper">相纸</option>
          <option value="canvas">帆布</option>
        </select>
        <input v-model.number="form.max_width_cm" type="number" placeholder="最大宽度(cm)" class="form-input" />
        <input v-model.number="form.max_height_cm" type="number" placeholder="最大高度(cm)" class="form-input" />
        <label class="checkbox-label">
          <input v-model="form.framing_available" type="checkbox" />
          可装框
        </label>
        <input v-model.number="form.price_multiplier" type="number" step="0.1" placeholder="价格倍数" class="form-input" />
        <button :disabled="creating" class="btn btn-primary" @click="handleCreate">
          {{ creating ? '创建中...' : '创建' }}
        </button>
      </div>
    </div>

    <!-- List -->
    <div class="panel-card">
      <h3 class="section-title">艺术微喷配置列表</h3>
      <table v-if="store.fineArtPrints.length" class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>作品 ID</th>
            <th>纸张类型</th>
            <th>最大尺寸</th>
            <th>可装框</th>
            <th>价格倍数</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fap in store.fineArtPrints" :key="fap.id">
            <td>{{ fap.id }}</td>
            <td>{{ fap.work_id }}</td>
            <td>{{ fap.paper_type }}</td>
            <td>{{ fap.max_width_cm ?? '-' }} × {{ fap.max_height_cm ?? '-' }} cm</td>
            <td>{{ fap.framing_available ? '✅' : '❌' }}</td>
            <td>{{ fap.price_multiplier }}x</td>
            <td>{{ fap.is_active ? '🟢 激活' : '⚫ 停用' }}</td>
            <td>
              <button class="btn btn-sm btn-danger" @click="handleDelete(fap)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">暂无艺术微喷配置</div>
    </div>
  </div>
</template>

<style scoped>
.fine-art-print-panel {
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
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
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

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ipCommercializationApi } from '@/api/marketplace'

const props = defineProps<{ licenseId: string }>()

const contract = ref('')
const loading = ref(true)
const expiring = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await ipCommercializationApi.getContract(props.licenseId)
    contract.value = res.data.contract_text
  } catch { /* handled */ } finally { loading.value = false }

  try {
    const res = await ipCommercializationApi.getExpiringSoon(30)
    expiring.value = res.data.licenses || []
  } catch { /* handled */ }
})

function copyContract() {
  navigator.clipboard.writeText(contract.value)
}
</script>

<template>
  <div class="contract-preview card">
    <h3>授权合同预览</h3>

    <div v-if="loading" class="loading">加载中...</div>
    <template v-else>
      <div class="contract-body">
        <pre>{{ contract || '暂无合同内容' }}</pre>
      </div>
      <button class="btn btn-sm btn-secondary" @click="copyContract">复制合同</button>
    </template>

    <div v-if="expiring.length" class="expiring-section">
      <h4>即将到期（30天内）</h4>
      <ul class="expiring-list">
        <li v-for="lic in expiring" :key="lic.id">
          <span>{{ lic.work_title }}</span>
          <span class="days-badge" :class="{ urgent: lic.days_remaining <= 7 }">
            {{ lic.days_remaining }}天
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.contract-body { background: #fafafa; padding: 20px; border-radius: 8px; margin-bottom: 16px; }
.contract-body pre { white-space: pre-wrap; font-family: inherit; font-size: 0.9rem; line-height: 1.6; }
.expiring-section { margin-top: 16px; }
.expiring-list { list-style: none; padding: 0; }
.expiring-list li { display: flex; justify-content: space-between; padding: 6px 0; font-size: 0.85rem; border-bottom: 1px solid var(--border); }
.days-badge { padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; background: #fef3c7; }
.days-badge.urgent { background: #fee2e2; color: #991b1b; }
</style>

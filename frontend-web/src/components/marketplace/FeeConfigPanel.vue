<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { tradingFeeApi } from '@/api/marketplace'

const config = ref<Record<string, unknown>>({})
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await tradingFeeApi.getConfig()
    config.value = res.data
  } catch { /* handled */ } finally { loading.value = false }
})

const editable = ref({
  base_rate_bps: config.value.base_rate_bps as number || 300,
  vip_discount_bps: config.value.vip_discount_bps as number || 50,
  vip_threshold: config.value.vip_threshold as number || 10000,
})

async function save() {
  try {
    await tradingFeeApi.updateConfig('default', editable.value)
  } catch { /* handled */ }
}
</script>

<template>
  <div class="fee-config-panel card">
    <h3>交易费率配置</h3>

    <div v-if="loading" class="loading">加载中...</div>
    <template v-else>
      <div class="config-fields">
        <label>
          基础费率（bps）
          <input type="number" v-model.number="editable.base_rate_bps" />
        </label>
        <label>
          VIP 折扣（bps）
          <input type="number" v-model.number="editable.vip_discount_bps" />
        </label>
        <label>
          VIP 门槛（元）
          <input type="number" v-model.number="editable.vip_threshold" />
        </label>
      </div>
      <div class="rate-summary">
        <p>当前费率: {{ (editable.base_rate_bps / 100).toFixed(2) }}%</p>
        <p>VIP 费率: {{ ((editable.base_rate_bps - editable.vip_discount_bps) / 100).toFixed(2) }}%</p>
        <p>VIP 门槛: ¥{{ editable.vip_threshold.toLocaleString() }}/月</p>
      </div>
      <button class="btn btn-primary" @click="save">保存配置</button>
    </template>
  </div>
</template>

<style scoped>
.config-fields { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }
.config-fields label { display: flex; flex-direction: column; gap: 4px; font-size: 0.85rem; }
.config-fields input { padding: 8px; border: 1px solid var(--border); border-radius: 6px; }
.rate-summary { font-size: 0.85rem; color: var(--muted); margin-bottom: 12px; }
</style>

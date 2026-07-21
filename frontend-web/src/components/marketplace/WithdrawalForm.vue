<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { commissionApi } from '@/api/marketplace'
import type { CommissionBalance, WithdrawalRequest } from '@/api/marketplace'

const balance = ref<CommissionBalance | null>(null)
const withdrawals = ref<WithdrawalRequest[]>([])
const loading = ref(true)
const withdrawing = ref(false)

const withdrawAmount = ref('')
const withdrawMethod = ref('bank_transfer')
const accountInfo = ref({ bank_name: '', account_number: '', holder_name: '' })
const error = ref('')

const feeRate = 0.01
const minNet = 10

const estimatedFee = computed(() => {
  const amt = parseFloat(withdrawAmount.value) || 0
  return Math.round(amt * feeRate * 100) / 100
})

const estimatedNet = computed(() => {
  const amt = parseFloat(withdrawAmount.value) || 0
  return Math.max(0, amt - estimatedFee.value)
})

onMounted(async () => {
  try {
    const [balRes, wdRes] = await Promise.all([
      commissionApi.getBalance(),
      commissionApi.getWithdrawals({ limit: 10 }),
    ])
    balance.value = balRes.data
    withdrawals.value = wdRes.data
  } catch { /* handled */ } finally { loading.value = false }
})

async function doWithdraw() {
  const amt = parseFloat(withdrawAmount.value)
  if (!amt || amt <= 0) { error.value = '请输入有效金额'; return }
  if (estimatedNet.value < minNet) { error.value = `提现后净额不足 ${minNet} 元`; return }
  if (balance.value && amt > balance.value.available_yuan) { error.value = '余额不足'; return }

  error.value = ''
  withdrawing.value = true
  try {
    await commissionApi.withdraw({
      amount_yuan: amt,
      method: withdrawMethod.value,
      account_info: accountInfo.value,
    })
    withdrawAmount.value = ''
    await onMounted() // reload
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '提现失败'
  } finally { withdrawing.value = false }
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    pending: '待审核', approved: '已通过', rejected: '已拒绝',
    settled: '已到账', cancelled: '已取消',
  }
  return map[s] || s
}
</script>

<template>
  <div class="withdrawal-form card">
    <h3>佣金余额与提现</h3>

    <div v-if="loading" class="loading">加载中...</div>
    <template v-else-if="balance">
      <div class="balance-cards">
        <div class="balance-card available">
          <div class="label">可用余额</div>
          <div class="value">¥{{ balance.available_yuan.toFixed(2) }}</div>
        </div>
        <div class="balance-card frozen">
          <div class="label">冻结金额</div>
          <div class="value">{{ balance.frozen_yuan.toFixed(2) }}</div>
        </div>
        <div class="balance-card total">
          <div class="label">累计收入</div>
          <div class="value">{{ balance.total_earned_yuan.toFixed(2) }}</div>
        </div>
      </div>

      <div class="withdraw-section">
        <h4>申请提现</h4>
        <div class="withdraw-fields">
          <label>
            提现方式
            <select v-model="withdrawMethod">
              <option value="bank_transfer">银行转账</option>
              <option value="wechat">微信支付</option>
              <option value="alipay">支付宝</option>
            </select>
          </label>
          <label>
            提现金额（元）
            <input type="number" v-model="withdrawAmount" placeholder="输入金额" />
          </label>
        </div>

        <div class="fee-preview" v-if="parseFloat(withdrawAmount.value) > 0">
          <span>手续费 (1%): ¥{{ estimatedFee.toFixed(2) }}</span>
          <span>到账: ¥{{ estimatedNet.toFixed(2) }}</span>
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>
        <button class="btn btn-primary" @click="doWithdraw" :disabled="withdrawing">
          {{ withdrawing ? '提交中...' : '提交提现申请' }}
        </button>
      </div>

      <div class="withdrawal-history">
        <h4>提现记录</h4>
        <table v-if="withdrawals.length" class="data-table">
          <thead>
            <tr><th>金额</th><th>到账</th><th>手续费</th><th>状态</th><th>时间</th></tr>
          </thead>
          <tbody>
            <tr v-for="w in withdrawals" :key="w.id">
              <td>¥{{ w.amount_yuan.toFixed(2) }}</td>
              <td>¥{{ w.net_amount_yuan.toFixed(2) }}</td>
              <td>¥{{ w.fee_yuan.toFixed(2) }}</td>
              <td>{{ statusLabel(w.status) }}</td>
              <td>{{ new Date(w.created_at).toLocaleDateString('zh-CN') }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty">暂无提现记录</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.balance-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.balance-card { padding: 16px; border-radius: 8px; text-align: center; }
.balance-card.available { background: #d1fae5; }
.balance-card.frozen { background: #fef3c7; }
.balance-card.total { background: #dbeafe; }
.label { font-size: 0.8rem; opacity: 0.7; margin-bottom: 4px; }
.value { font-size: 1.3rem; font-weight: 600; }
.withdraw-section { margin-bottom: 20px; }
.withdraw-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
.withdraw-fields select, .withdraw-fields input { padding: 8px; border: 1px solid var(--border); border-radius: 6px; }
.fee-preview { display: flex; gap: 16px; font-size: 0.85rem; color: var(--muted); margin-bottom: 8px; }
.error-msg { color: #ef4444; font-size: 0.85rem; margin-bottom: 8px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.data-table th, .data-table td { padding: 6px 10px; border-bottom: 1px solid var(--border); text-align: left; }
.empty { color: var(--muted); font-size: 0.85rem; }
</style>

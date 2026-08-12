<template>
  <div class="page-contract-detail">
    <div class="container">
      <NuxtLink to="/market" class="back-link">← 返回行情列表</NuxtLink>

      <div v-if="loading" class="loading-state">加载中...</div>
      <div v-else-if="error" class="error-state">{{ error }}</div>
      <div v-else-if="contract" class="contract-layout">

        <!-- 左侧：作品预览 -->
        <div class="preview-panel">
          <div class="preview-img" v-if="contract.thumbnail">
            <img :src="contract.thumbnail" :alt="contract.title" />
          </div>
          <div class="preview-img preview-placeholder" v-else>
            <div>
              <div class="placeholder-icon">🖼️</div>
              <div class="placeholder-text">作品预览图</div>
              <div class="placeholder-sub">受保护内容已脱敏</div>
            </div>
          </div>
          <div class="preview-meta">
            <div class="pm-item">
              <span class="pm-key">创作者</span>
              <span class="pm-val">{{ contract.creator_name }}</span>
            </div>
            <div class="pm-item">
              <span class="pm-key">上传时间</span>
              <span class="pm-val data-mono">{{ formatDate(contract.created_at) }}</span>
            </div>
            <div class="pm-item">
              <span class="pm-key">存证状态</span>
              <span class="pm-val" style="color:var(--spark-green);">✓ L1-L4 已存证</span>
            </div>
            <div class="pm-item">
              <span class="pm-key">SCR 信誉</span>
              <span class="pm-val" style="color:var(--spark-gold);">★★★★★ 4.8</span>
            </div>
          </div>
          <div class="preview-tags">
            <span class="tag" v-for="tag in (contract.tags ?? ['艺术创作'])" :key="tag">{{ tag }}</span>
          </div>
        </div>

        <!-- 中间：合约信息 -->
        <div class="info-panel">
          <div class="info-header">
            <h1 class="contract-title">{{ contract.title }}</h1>
            <span class="status-badge" :class="'status-' + contract.status">{{ statusLabel(contract.status) }}</span>
          </div>
          <p class="contract-desc">{{ contract.description }}</p>

          <div class="info-grid">
            <div class="info-card">
              <div class="ic-label">合约类型</div>
              <div class="ic-value">{{ contractTypeLabel(contract.contract_type) }}</div>
            </div>
            <div class="info-card">
              <div class="ic-label">挂牌金额</div>
              <div class="ic-value data-mono" style="font-size:1.4rem;">{{ contract.currency }} {{ (contract.total_amount ?? 0).toLocaleString() }}</div>
            </div>
            <div class="info-card">
              <div class="ic-label">分润规则</div>
              <div class="ic-value">创作者 70% / 平台 3% / 保险 2%</div>
            </div>
            <div class="info-card">
              <div class="ic-label">使用范围</div>
              <div class="ic-value">{{ contract.scope_usage }}</div>
            </div>
            <div class="info-card">
              <div class="ic-label">地域范围</div>
              <div class="ic-value">{{ contract.scope_geography }}</div>
            </div>
            <div class="info-card">
              <div class="ic-label">风险等级</div>
              <div class="ic-value"><span class="risk-badge risk-low">低风险</span></div>
            </div>
          </div>

          <!-- 合约时间线 -->
          <div class="contract-timeline">
            <div class="ct-title">合约生命周期</div>
            <div class="ct-steps">
              <div class="ct-step" :class="{ active: stepActive(contract.status, 'draft'), done: isStepDone(contract.status, 'draft') }">
                <div class="cs-num">1</div>
                <div class="cs-label">草稿</div>
              </div>
              <div class="ct-step-arrow">→</div>
              <div class="ct-step" :class="{ active: stepActive(contract.status, 'listed'), done: isStepDone(contract.status, 'listed') }">
                <div class="cs-num">2</div>
                <div class="cs-label">挂牌</div>
              </div>
              <div class="ct-step-arrow">→</div>
              <div class="ct-step" :class="{ active: stepActive(contract.status, 'subscribed'), done: isStepDone(contract.status, 'subscribed') }">
                <div class="cs-num">3</div>
                <div class="cs-label">认购</div>
              </div>
              <div class="ct-step-arrow">→</div>
              <div class="ct-step" :class="{ active: stepActive(contract.status, 'escrowed'), done: isStepDone(contract.status, 'escrowed') }">
                <div class="cs-num">4</div>
                <div class="cs-label">托管</div>
              </div>
              <div class="ct-step-arrow">→</div>
              <div class="ct-step" :class="{ active: stepActive(contract.status, 'insured'), done: isStepDone(contract.status, 'insured') }">
                <div class="cs-num">5</div>
                <div class="cs-label">投保</div>
              </div>
              <div class="ct-step-arrow">→</div>
              <div class="ct-step" :class="{ active: stepActive(contract.status, 'executing'), done: isStepDone(contract.status, 'executing') }">
                <div class="cs-num">6</div>
                <div class="cs-label">执行</div>
              </div>
              <div class="ct-step-arrow">→</div>
              <div class="ct-step" :class="{ active: stepActive(contract.status, 'completed'), done: isStepDone(contract.status, 'completed') }">
                <div class="cs-num">7</div>
                <div class="cs-label">完成</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：认购操作面板 -->
        <div class="action-panel">
          <div class="ap-header">
            <div class="ap-price">
              <span class="ap-label">挂牌价</span>
              <span class="ap-value data-mono">{{ contract.currency }} {{ (contract.total_amount ?? 0).toLocaleString() }}</span>
            </div>
            <div class="ap-fee">
              <span>平台手续费 3‰</span>
              <span class="data-mono">¥{{ ((contract.total_amount ?? 0) * 0.003).toFixed(2) }}</span>
            </div>
          </div>

          <!-- 认购向导 -->
          <div class="subscribe-wizard">
            <div class="wizard-title">认购流程向导</div>
            <div class="wizard-steps">
              <div class="ws-step" :class="{ active: wizardStep === 1, done: wizardStep > 1 }">
                <div class="ws-num">1</div>
                <div class="ws-label">选择数量</div>
              </div>
              <div class="ws-step" :class="{ active: wizardStep === 2, done: wizardStep > 2 }">
                <div class="ws-num">2</div>
                <div class="ws-label">确认分润</div>
              </div>
              <div class="ws-step" :class="{ active: wizardStep === 3, done: wizardStep > 3 }">
                <div class="ws-num">3</div>
                <div class="ws-label">支付托管</div>
              </div>
              <div class="ws-step" :class="{ active: wizardStep === 4 }">
                <div class="ws-num">4</div>
                <div class="ws-label">生成合约</div>
              </div>
            </div>

            <!-- Step 1: 选择数量 -->
            <div v-if="wizardStep === 1" class="wizard-content">
              <div class="wc-label">认购数量</div>
              <div class="qty-selector">
                <button class="qty-btn" @click="qty = Math.max(1, qty - 1)">−</button>
                <span class="qty-value data-mono">{{ qty }}</span>
                <button class="qty-btn" @click="qty = Math.min(100, qty + 1)">+</button>
              </div>
              <div class="wc-total">
                <span>合计金额</span>
                <span class="data-mono total-price">{{ formatCurrency((contract.total_amount ?? 0) * qty) }}</span>
              </div>
              <button class="btn-next" @click="wizardStep = 2">下一步：确认分润 →</button>
            </div>

            <!-- Step 2: 确认分润 -->
            <div v-if="wizardStep === 2" class="wizard-content">
              <div class="wc-label">分润明细</div>
              <div class="split-table">
                <div class="st-row st-header"><span>参与方</span><span>比例</span><span class="data-mono">金额</span></div>
                <div class="st-row"><span>🎨 创作者</span><span>70%</span><span class="data-mono">{{ formatCurrency((contract.total_amount ?? 0) * qty * 0.7) }}</span></div>
                <div class="st-row"><span>🏛️ 平台</span><span>3%</span><span class="data-mono">{{ formatCurrency((contract.total_amount ?? 0) * qty * 0.03) }}</span></div>
                <div class="st-row"><span>🛡️ 保险方</span><span>2%</span><span class="data-mono">{{ formatCurrency((contract.total_amount ?? 0) * qty * 0.02) }}</span></div>
                <div class="st-row st-total"><span>其他参与方</span><span>25%</span><span class="data-mono">{{ formatCurrency((contract.total_amount ?? 0) * qty * 0.25) }}</span></div>
              </div>
              <div class="wizard-nav">
                <button class="btn-back" @click="wizardStep = 1">← 上一步</button>
                <button class="btn-next" @click="wizardStep = 3">确认并继续 →</button>
              </div>
            </div>

            <!-- Step 3: 支付托管 -->
            <div v-if="wizardStep === 3" class="wizard-content">
              <div class="wc-label">选择支付方式</div>
              <div class="pay-options">
                <div class="pay-option" :class="{ selected: paymentMethod === 'stripe' }" @click="paymentMethod = 'stripe'">
                  <span class="pay-icon">💳</span>
                  <span class="pay-name">Stripe</span>
                  <span class="pay-desc">信用卡 / 借记卡</span>
                </div>
                <div class="pay-option" :class="{ selected: paymentMethod === 'paypal' }" @click="paymentMethod = 'paypal'">
                  <span class="pay-icon">🅿️</span>
                  <span class="pay-name">PayPal</span>
                  <span class="pay-desc">PayPal 账户</span>
                </div>
                <div class="pay-option" :class="{ selected: paymentMethod === 'worldfirst' }" @click="paymentMethod = 'worldfirst'">
                  <span class="pay-icon">🌐</span>
                  <span class="pay-name">WorldFirst</span>
                  <span class="pay-desc">跨境结算</span>
                </div>
              </div>
              <div class="payment-total">
                <span>应付总额</span>
                <span class="data-mono payment-amount">{{ formatCurrency((contract.total_amount ?? 0) * qty) }}</span>
              </div>
              <div class="wizard-nav">
                <button class="btn-back" @click="wizardStep = 2">← 上一步</button>
                <button class="btn-next btn-pay" :disabled="subscribing" @click="handlePay">
                  {{ subscribing ? '认购中...' : '支付并托管' }}
                </button>
              </div>
            </div>

            <!-- Step 4: 完成 -->
            <div v-if="wizardStep === 4" class="wizard-content wizard-success">
              <div class="success-icon">✓</div>
              <div class="success-title">认购成功！</div>
              <div class="success-desc">合约已进入托管状态，创作者将收到通知。资金将在合约执行完毕后按分润规则自动结算。</div>
              <NuxtLink to="/market" class="btn-back" style="margin-top:16px;">返回行情列表</NuxtLink>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">未找到该合约</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Contract } from '~/types/public'
import { fetchPublicContracts, subscribeContract } from '~/composables/usePublicApi'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const contract = ref<Contract | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const wizardStep = ref(1)
const qty = ref(1)
const paymentMethod = ref('stripe')
const subscribing = ref(false)

const routeParams = route.params as { id?: string }

async function loadContract() {
  const id = routeParams.id
  if (!id) { error.value = '合约 ID 缺失'; return }
  loading.value = true
  error.value = null
  try {
    const res = await fetchPublicContracts()
    const found = (res ?? []).find((c: Contract) => c.id === id)
    contract.value = found ?? null
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load contract'
  } finally {
    loading.value = false
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿', listed: '挂牌中', active: '活跃',
    escrowed: '托管中', insured: '已投保', executing: '执行中',
    completed: '已完成', dispute: '争议中', resolved: '已解决',
    refunded: '已退款', cancelled: '已取消',
  }
  return labels[status] ?? status
}

function contractTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    exclusive_license: '独占许可', non_exclusive_license: '非独占许可',
    transfer: '转让', commission: '委托创作',
  }
  return labels[type] ?? type
}

function formatCurrency(value?: number): string {
  if (value == null) return '¥0'
  return `¥${value.toLocaleString('zh-CN')}`
}

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function stepActive(status: string, step: string): boolean {
  const order = ['draft', 'listed', 'subscribed', 'escrowed', 'insured', 'executing', 'completed']
  return status === step
}

function isStepDone(status: string, step: string): boolean {
  const order = ['draft', 'listed', 'subscribed', 'escrowed', 'insured', 'executing', 'completed']
  const currentIdx = order.indexOf(status)
  const stepIdx = order.indexOf(step)
  return currentIdx > stepIdx
}

async function handlePay() {
  if (!auth.isLoggedIn) {
    navigateTo('/auth/login')
    return
  }
  if (!contract.value) return
  subscribing.value = true
  try {
    const result = await subscribeContract(contract.value.id)
    console.log('Subscribed:', result)
    wizardStep.value = 4
  } catch (e) {
    error.value = e instanceof Error ? e.message : '认购失败，请稍后重试'
  } finally {
    subscribing.value = false
  }
}

onMounted(loadContract)
</script>

<style scoped>
.page-contract-detail {
  min-height: 100vh;
  background: #f8fafc;
  padding: 24px;
}
.container { max-width: 1400px; margin: 0 auto; }

.back-link {
  display: inline-flex; align-items: center; gap: 4px;
  margin-bottom: 20px; color: #64748b; text-decoration: none; font-size: 14px;
}
.back-link:hover { color: #3b82f6; }

.loading-state, .error-state, .empty-state {
  text-align: center; padding: 80px 0; color: #94a3b8; font-size: 16px;
}
.error-state { color: #ef4444; }

/* --- THREE-COLUMN LAYOUT --- */
.contract-layout {
  display: grid;
  grid-template-columns: 1fr 1.5fr 0.75fr;
  gap: 24px;
  align-items: start;
}

/* --- PREVIEW PANEL --- */
.preview-panel {
  background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden;
}
.preview-img { aspect-ratio: 4/3; background: #f1f5f9; overflow: hidden; }
.preview-img img { width: 100%; height: 100%; object-fit: cover; }
.preview-placeholder { display: flex; align-items: center; justify-content: center; color: #94a3b8; }
.placeholder-icon { font-size: 48px; margin-bottom: 8px; }
.placeholder-text { font-size: 14px; font-weight: 600; color: #64748b; }
.placeholder-sub { font-size: 12px; color: #94a3b8; margin-top: 4px; }
.preview-meta { padding: 16px; display: flex; flex-direction: column; gap: 10px; border-bottom: 1px solid #e2e8f0; }
.pm-item { display: flex; justify-content: space-between; align-items: center; }
.pm-key { font-size: 12px; color: #94a3b8; }
.pm-val { font-size: 13px; font-weight: 600; color: #1e293b; }
.preview-tags { padding: 12px 16px; display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 3px 10px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 100px; font-size: 11px; color: #64748b; }

/* --- INFO PANEL --- */
.info-panel { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 24px; }
.info-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.contract-title { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0; line-height: 1.3; }
.contract-desc { font-size: 14px; color: #64748b; line-height: 1.7; margin-bottom: 20px; }

.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 24px; }
.info-card { padding: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; }
.ic-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.ic-value { font-size: 14px; font-weight: 600; color: #1e293b; }

.risk-badge { display: inline-block; padding: 3px 10px; border-radius: 100px; font-size: 12px; font-weight: 600; }
.risk-low { background: #d1fae5; color: #065f46; }
.risk-mid { background: #fef3c7; color: #92400e; }
.risk-high { background: #fee2e2; color: #991b1b; }

/* --- CONTRACT TIMELINE --- */
.contract-timeline { padding: 16px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
.ct-title { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em; }
.ct-steps { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.ct-step { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.cs-num { width: 28px; height: 28px; border-radius: 50%; background: #e2e8f0; color: #94a3b8; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
.cs-label { font-size: 11px; color: #94a3b8; }
.ct-step.active .cs-num { background: #3b82f6; color: #fff; box-shadow: 0 0 0 3px rgba(59,130,246,0.2); }
.ct-step.active .cs-label { color: #3b82f6; font-weight: 600; }
.ct-step.done .cs-num { background: #10b981; color: #fff; }
.ct-step-arrow { font-size: 14px; color: #cbd5e1; }

/* --- ACTION PANEL --- */
.action-panel { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; position: sticky; top: 80px; }
.ap-header { padding: 20px; border-bottom: 1px solid #e2e8f0; }
.ap-price { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
.ap-label { font-size: 12px; color: #94a3b8; }
.ap-value { font-size: 24px; font-weight: 700; color: #1e293b; }
.ap-fee { display: flex; justify-content: space-between; font-size: 12px; color: #64748b; }

/* --- WIZARD --- */
.subscribe-wizard { padding: 20px; }
.wizard-title { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.05em; }
.wizard-steps { display: flex; gap: 0; margin-bottom: 20px; }
.ws-step { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; position: relative; }
.ws-num { width: 24px; height: 24px; border-radius: 50%; background: #e2e8f0; color: #94a3b8; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; }
.ws-label { font-size: 10px; color: #94a3b8; text-align: center; }
.ws-step.active .ws-num { background: #3b82f6; color: #fff; }
.ws-step.active .ws-label { color: #3b82f6; font-weight: 600; }
.ws-step.done .ws-num { background: #10b981; color: #fff; }

.wizard-content { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.wc-label { font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 10px; }
.qty-selector { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.qty-btn { width: 36px; height: 36px; border: 1px solid #e2e8f0; background: #f8fafc; border-radius: 6px; font-size: 18px; cursor: pointer; color: #374151; }
.qty-btn:hover { background: #fff; border-color: #3b82f6; }
.qty-value { font-size: 20px; font-weight: 700; color: #1e293b; min-width: 40px; text-align: center; }
.wc-total { display: flex; justify-content: space-between; padding: 12px; background: #f8fafc; border-radius: 6px; margin-bottom: 16px; font-size: 14px; }
.total-price { font-size: 18px; font-weight: 700; color: #1e293b; }

.btn-next { width: 100%; padding: 12px; background: #3b82f6; color: #fff; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.15s; }
.btn-next:hover { background: #2563eb; }
.btn-pay { background: #10b981; }
.btn-pay:hover { background: #059669; }

.wizard-nav { display: flex; gap: 10px; margin-top: 12px; }
.btn-back { flex: 1; padding: 10px; background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 14px; cursor: pointer; text-decoration: none; text-align: center; transition: all 0.15s; }
.btn-back:hover { background: #fff; color: #374151; }

/* Split table */
.split-table { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-bottom: 16px; }
.st-row { display: grid; grid-template-columns: 1fr 0.6fr 1fr; padding: 10px 14px; font-size: 13px; border-bottom: 1px solid #f1f5f9; }
.st-header { background: #f8fafc; font-weight: 600; color: #94a3b8; font-size: 11px; text-transform: uppercase; }
.st-total { background: #eff6ff; font-weight: 600; }

/* Payment options */
.pay-options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.pay-option { display: flex; align-items: center; gap: 12px; padding: 14px; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; transition: all 0.15s; }
.pay-option:hover { border-color: #3b82f6; background: #f8fafc; }
.pay-option.selected { border-color: #3b82f6; background: #eff6ff; }
.pay-icon { font-size: 24px; }
.pay-name { font-size: 14px; font-weight: 600; color: #1e293b; }
.pay-desc { font-size: 12px; color: #94a3b8; margin-left: auto; }
.payment-total { display: flex; justify-content: space-between; padding: 14px; background: #f8fafc; border-radius: 8px; margin-bottom: 16px; font-size: 14px; }
.payment-amount { font-size: 20px; font-weight: 700; color: #1e293b; }

/* Success */
.wizard-success { text-align: center; padding: 24px 0; }
.success-icon { font-size: 48px; color: #10b981; margin-bottom: 12px; }
.success-title { font-size: 20px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.success-desc { font-size: 14px; color: #64748b; line-height: 1.6; }

/* Status badges */
.status-badge { display: inline-block; padding: 4px 12px; border-radius: 100px; font-size: 12px; font-weight: 600; white-space: nowrap; }
.status-listed { background: #fef3c7; color: #92400e; }
.status-active { background: #d1fae5; color: #065f46; }
.status-executing { background: #dbeafe; color: #1e40af; }
.status-completed { background: #e5e7eb; color: #374151; }
.status-dispute { background: #fee2e2; color: #991b1b; }

.data-mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; font-variant-numeric: tabular-nums; }

/* Responsive */
@media (max-width: 1024px) {
  .contract-layout { grid-template-columns: 1fr 1fr; }
  .action-panel { grid-column: span 2; position: static; }
}
@media (max-width: 768px) {
  .contract-layout { grid-template-columns: 1fr; }
  .action-panel { grid-column: span 1; }
  .info-grid { grid-template-columns: 1fr; }
  .page-contract-detail { padding: 16px; }
}
</style>

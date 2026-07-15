<template>
  <div class="verify-page">
    <div class="verify-card card">
      <div class="verify-brand">
        <div class="brand-logo">O</div>
        <h1>OriStudio 证书验证</h1>
        <p>扫描二维码或输入证书 ID 验证作品存证信息</p>
      </div>

      <div v-if="!verified" class="verify-form">
        <div class="form-group">
          <label>证书 ID</label>
          <input
            v-model="certId"
            class="form-input"
            placeholder="输入证书 ID 或扫描二维码..."
            @keyup.enter="verify"
          />
        </div>
        <button class="btn btn-primary" style="width:100%;justify-content:center" @click="verify" :disabled="verifying">
          {{ verifying ? '验证中...' : '🔍 验证' }}
        </button>
      </div>

      <div v-else-if="result" class="verify-result animate-fade-in">
        <div v-if="result.valid" class="result-success">
          <div class="result-icon">✅</div>
          <h2>验证通过</h2>
          <div class="result-details">
            <div class="detail-row"><span class="dl">作品名称</span><span class="dv">{{ result.work_title }}</span></div>
            <div class="detail-row"><span class="dl">SHA-256</span><code class="dv mono">{{ result.sha256 }}</code></div>
            <div class="detail-row"><span class="dl">存证平台</span><span class="dv">{{ result.platform }}</span></div>
            <div class="detail-row"><span class="dl">存证时间</span><span class="dv">{{ result.confirmed_at }}</span></div>
            <div v-if="result.transaction_hash" class="detail-row">
              <span class="dl">交易哈希</span><code class="dv mono">{{ result.transaction_hash }}</code>
            </div>
          </div>
        </div>
        <div v-else class="result-fail">
          <div class="result-icon">❌</div>
          <h2>验证失败</h2>
          <p>{{ result.error }}</p>
        </div>
        <button class="btn btn-secondary" style="margin-top:16px" @click="reset">验证其他证书</button>
      </div>

      <div class="verify-footer">
        <p>🔒 数据基于创作者本地的 SHA-256 哈希计算</p>
        <p>本验证服务仅供存证参考，不构成法律意见</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import client from '@/api/client'

const certId = ref('')
const verifying = ref(false)
const verified = ref(false)
const result = ref<any>(null)

async function verify() {
  if (!certId.value.trim()) return
  verifying.value = true
  try {
    const resp = await client.get(`/notary/verify/${certId.value.trim()}`)
    verified.value = true
    result.value = resp.data.data || { valid: false, error: resp.data.message }
  } catch {
    verified.value = true
    result.value = { valid: false, error: '验证服务不可用' }
  } finally {
    verifying.value = false
  }
}

function reset() {
  verified.value = false
  certId.value = ''
  result.value = null
}
</script>

<style scoped>
.verify-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: 20px;
}
.verify-card {
  max-width: 520px;
  width: 100%;
  padding: 40px;
  text-align: center;
}
.brand-logo {
  width: 56px; height: 56px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 800; font-size: 1.6rem;
  margin-bottom: 12px;
}
.verify-brand h1 { font-size: 1.3rem; margin: 0 0 4px; }
.verify-brand p { color: var(--muted); font-size: 0.85rem; margin: 0; }
.verify-form { margin-top: 24px; display: flex; flex-direction: column; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 6px; text-align: left; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input { padding: 12px 16px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 0.9rem; font-family: var(--font-body); color: var(--fg); background: var(--surface); outline: none; }
.form-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1); }
.result-icon { font-size: 3rem; margin-bottom: 8px; }
.result-details { text-align: left; margin-top: 16px; }
.detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid oklch(93% 0.003 240); font-size: 0.85rem; }
.dl { font-weight: 600; color: var(--muted); }
.dv { max-width: 60%; word-break: break-all; text-align: right; }
.mono { font-family: monospace; font-size: 0.72rem; }
.result-fail h2 { color: #e53e3e; }
.verify-footer { margin-top: 24px; font-size: 0.75rem; color: var(--muted); }
.verify-footer p { margin: 4px 0; }
</style>

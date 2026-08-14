<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useRuntimeConfig } from '#app'

definePageMeta({ layout: 'default' })

const auth = useAuthStore()
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const participantRoles = ref<string[]>([])
const submitting = ref(false)
const errorMsg = ref('')

const roles = [
  { key: 'operator', label: '运营方', desc: '作品运营与推广代理' },
  { key: 'trader', label: '采购方', desc: '商业授权采购者' },
  { key: 'legal_rep', label: '法务代表', desc: '法律事务代理人' },
  { key: 'tax_agent', label: '税务代理', desc: '税务申报与合规代理' },
  { key: 'logistics', label: '物流方', desc: '实体商品配送' },
  { key: 'insurer', label: '保险方', desc: '版权/履约保险' },
  { key: 'payment_provider', label: '支付托管方', desc: '资金托管与结算' },
]

async function handleRegister() {
  if (!username.value || !email.value || !password.value) {
    errorMsg.value = '请填写完整信息'
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次密码不一致'
    return
  }
  if (participantRoles.value.length === 0) {
    errorMsg.value = '请选择至少一个身份角色'
    return
  }
  submitting.value = true
  errorMsg.value = ''
  try {
    const apiBase = useRuntimeConfig().public.apiBase
    const resp = await $fetch(`${apiBase}/auth/register/operator`, {
      method: 'POST',
      body: {
        username: username.value,
        email: email.value,
        password: password.value,
        participant_roles: participantRoles.value,
      },
    })
    const data = resp.data as { token: string; user: Record<string, unknown> }
    auth.token = data.token
    auth.user = data.user
    localStorage.setItem('orispark-token', data.token)
    localStorage.setItem('orispark-user', JSON.stringify(data.user))
    navigateTo('/market')
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : '注册失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-layout">
    <!-- Left Panel -->
    <div class="auth-left">
      <div class="auth-left-bg">
        <div class="auth-left-shapes">
          <div class="auth-shape auth-shape-1" />
          <div class="auth-shape auth-shape-2" />
          <div class="auth-shape auth-shape-3" />
        </div>
      </div>
      <div class="auth-left-content">
        <div class="auth-illustration">
          <svg viewBox="0 0 400 400" class="auth-svg">
            <circle cx="200" cy="200" r="160" fill="rgba(255,255,255,0.1)" />
            <circle cx="200" cy="140" r="45" fill="rgba(255,255,255,0.9)" />
            <path d="M120 300 Q200 200 280 300" stroke="rgba(255,255,255,0.9)" stroke-width="20" fill="none" stroke-linecap="round" />
            <circle cx="100" cy="120" r="20" fill="#8C57FF" opacity="0.8" />
            <circle cx="300" cy="160" r="15" fill="#56CA00" opacity="0.8" />
          </svg>
        </div>
        <h2 class="auth-left-title">加入 OriSpark</h2>
        <p class="auth-left-desc">成为创作者生态的合作伙伴</p>
        <div class="auth-stats">
          <div class="auth-stat">
            <div class="auth-stat-value">13k+</div>
            <div class="auth-stat-label">创作者</div>
          </div>
          <div class="auth-stat-divider" />
          <div class="auth-stat">
            <div class="auth-stat-value">50k+</div>
            <div class="auth-stat-label">作品存证</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Panel -->
    <div class="auth-right">
      <div class="auth-right-inner">
        <div class="auth-header">
          <NuxtLink to="/" class="auth-logo">
            <span class="auth-logo-icon">⚡</span>
            <span class="auth-logo-text">OriSpark</span>
          </NuxtLink>
          <p class="auth-welcome">创建您的账户</p>
          <p class="auth-desc">填写以下信息完成注册</p>
        </div>

        <form @submit.prevent="handleRegister" class="auth-form">
          <!-- Username -->
          <div class="form-field">
            <label class="form-label">用户名</label>
            <div class="form-input-wrapper">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
              </svg>
              <input v-model="username" class="form-input" placeholder="创作者名称" required />
            </div>
          </div>

          <!-- Email -->
          <div class="form-field">
            <label class="form-label">邮箱</label>
            <div class="form-input-wrapper">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
              </svg>
              <input v-model="email" type="email" class="form-input" placeholder="your@email.com" required />
            </div>
          </div>

          <!-- Password -->
          <div class="form-field">
            <label class="form-label">密码</label>
            <div class="form-input-wrapper">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input v-model="password" type="password" class="form-input" placeholder="至少6位" required minlength="6" />
            </div>
          </div>

          <!-- Confirm Password -->
          <div class="form-field">
            <label class="form-label">确认密码</label>
            <div class="form-input-wrapper">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input v-model="confirmPassword" type="password" class="form-input" placeholder="再次输入密码" required />
            </div>
          </div>

          <!-- Role Selection -->
          <div class="form-field">
            <label class="form-label">身份角色 <span class="form-required">*</span></label>
            <div class="role-grid">
              <label v-for="role in roles" :key="role.key" class="role-item">
                <input type="checkbox" :value="role.key" v-model="participantRoles" />
                <div class="role-info">
                  <div class="role-label">{{ role.label }}</div>
                  <div class="role-desc">{{ role.desc }}</div>
                </div>
              </label>
            </div>
          </div>

          <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

          <button type="submit" class="btn-primary" :disabled="submitting">
            <span v-if="submitting">处理中...</span>
            <span v-else>注册</span>
          </button>
        </form>

        <div class="auth-footer">
          <p>已有账号？<NuxtLink to="/auth/login" class="auth-link">立即登录</NuxtLink></p>
          <p class="auth-redirect">创作者请前往 <a href="http://localhost:5174" target="_blank">OriStudio</a> 注册</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-layout { min-height: 100dvh; display: flex; }
.auth-left {
  flex: 1; position: relative;
  background: linear-gradient(135deg, #8C57FF 0%, #6A3FCC 50%, #4A2D99 100%);
  display: flex; align-items: center; justify-content: center; overflow: hidden; min-height: 100dvh;
}
.auth-left-bg { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(140,87,255,0.95) 0%, rgba(106,63,204,0.95) 100%); }
.auth-left-shapes { position: absolute; inset: 0; }
.auth-shape { position: absolute; border-radius: 50%; opacity: 0.15; background: white; }
.auth-shape-1 { width: 300px; height: 300px; top: -50px; right: -50px; }
.auth-shape-2 { width: 200px; height: 200px; bottom: 50px; left: -30px; }
.auth-shape-3 { width: 150px; height: 150px; bottom: -30px; right: 100px; }
.auth-left-content { position: relative; z-index: 1; text-align: center; padding: 2rem; color: white; }
.auth-illustration { margin-bottom: 1.5rem; }
.auth-svg { width: 180px; height: 180px; filter: drop-shadow(0 10px 30px rgba(0,0,0,0.2)); }
.auth-left-title { font-size: 1.75rem; font-weight: 700; margin: 0 0 0.5rem; }
.auth-left-desc { font-size: 0.9375rem; opacity: 0.8; margin: 0 0 2rem; }
.auth-stats { display: flex; align-items: center; gap: 2rem; justify-content: center; }
.auth-stat { text-align: center; }
.auth-stat-value { font-size: 1.5rem; font-weight: 700; line-height: 1.2; }
.auth-stat-label { font-size: 0.8125rem; opacity: 0.8; }
.auth-stat-divider { width: 1px; height: 40px; background: rgba(255,255,255,0.3); }
.auth-right { flex: 1; display: flex; align-items: center; justify-content: center; background: #FFFFFF; padding: 2rem; }
.auth-right-inner { width: 100%; max-width: 480px; }
.auth-header { margin-bottom: 2rem; }
.auth-logo { display: inline-flex; align-items: center; gap: 0.5rem; text-decoration: none; margin-bottom: 1rem; }
.auth-logo-icon { font-size: 2rem; }
.auth-logo-text { font-size: 1.5rem; font-weight: 700; background: linear-gradient(135deg, #8C57FF, #6A3FCC); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.auth-welcome { font-size: 1.25rem; font-weight: 600; color: #1F2937; margin: 0 0 0.25rem; }
.auth-desc { font-size: 0.875rem; color: #64748B; margin: 0 0 1.5rem; }
.auth-form { display: flex; flex-direction: column; gap: 1.25rem; }
.form-field { display: flex; flex-direction: column; gap: 0.375rem; }
.form-label { font-size: 0.8125rem; font-weight: 500; color: #374151; }
.form-required { color: #EF4444; }
.form-input-wrapper {
  position: relative; display: flex; align-items: center;
  border: 1.5px solid #E5E7EB; border-radius: 8px;
  transition: all 0.15s; background: #FFFFFF;
}
.form-input-wrapper:focus-within { border-color: #8C57FF; box-shadow: 0 0 0 3px rgba(140, 87, 255, 0.1); }
.form-input-icon { position: absolute; left: 12px; color: #9CA3AF; pointer-events: none; }
.form-input {
  flex: 1; height: 44px; padding: 0 0.75rem 0 2.75rem;
  border: none; outline: none; font-size: 0.9375rem;
  font-family: inherit; color: #1F2937; background: transparent;
}
.form-input::placeholder { color: #9CA3AF; }
.form-error { color: #EF4444; font-size: 0.8125rem; margin: 0; }

/* Role Grid */
.role-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;
}
.role-item {
  display: flex; align-items: flex-start; gap: 0.5rem;
  padding: 0.75rem; border: 1.5px solid #E5E7EB;
  border-radius: 8px; cursor: pointer;
  transition: all 0.15s;
}
.role-item:hover { border-color: #8C57FF; background: rgba(140, 87, 255, 0.04); }
.role-item input[type="checkbox"] { margin-top: 3px; accent-color: #8C57FF; }
.role-info { flex: 1; min-width: 0; }
.role-label { font-size: 0.8125rem; font-weight: 600; color: #1F2937; }
.role-desc { font-size: 0.6875rem; color: #9CA3AF; margin-top: 2px; }

.btn-primary {
  height: 44px; padding: 0 1.5rem;
  background: linear-gradient(135deg, #8C57FF 0%, #7E4EE6 100%);
  color: white; border: none; border-radius: 8px;
  font-size: 0.9375rem; font-weight: 600; cursor: pointer;
  transition: all 0.15s;
}
.btn-primary:hover:not(:disabled) { background: linear-gradient(135deg, #7E4EE6 0%, #6A3FCC 100%); box-shadow: 0 4px 12px rgba(140, 87, 255, 0.4); }
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }

.auth-footer { margin-top: 1.5rem; text-align: center; }
.auth-footer p { font-size: 0.875rem; color: #64748B; margin: 0.5rem 0; }
.auth-link { color: #8C57FF; text-decoration: none; font-weight: 600; }
.auth-link:hover { text-decoration: underline; }
.auth-redirect { font-size: 0.75rem; color: #9CA3AF; }
.auth-redirect a { color: #8C57FF; }

@media (max-width: 768px) {
  .auth-left { display: none; }
  .auth-right { flex: 1; }
  .role-grid { grid-template-columns: 1fr; }
}
</style>

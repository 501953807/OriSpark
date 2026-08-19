<template>
  <div class="auth-layout">
    <!-- Left Panel -->
    <div class="auth-left">
      <div class="auth-left-bg"></div>
      <div class="auth-left-shapes">
        <div class="auth-shape auth-shape-1" />
        <div class="auth-shape auth-shape-2" />
        <div class="auth-shape auth-shape-3" />
        <div class="auth-shape auth-shape-4" />
      </div>
      <div class="auth-left-content">
        <!-- Brand identity -->
        <div class="auth-brand">
          <span class="auth-brand-icon">🎨</span>
          <span class="auth-brand-name">OriStudio</span>
        </div>

        <!-- Hero illustration -->
        <div class="auth-illustration">
          <svg viewBox="0 0 400 400" class="auth-svg">
            <circle cx="200" cy="200" r="160" fill="rgba(255,255,255,0.06)" />
            <circle cx="200" cy="140" r="45" fill="rgba(255,255,255,0.85)" />
            <path d="M120 300 Q200 200 280 300" stroke="rgba(255,255,255,0.85)" stroke-width="20" fill="none" stroke-linecap="round" />
            <circle cx="100" cy="120" r="20" fill="var(--m-primary, #4F46E5)" opacity="0.7" />
            <circle cx="300" cy="160" r="15" fill="#16A34A" opacity="0.7" />
            <circle cx="140" cy="260" r="10" fill="#F59E0B" opacity="0.6" />
          </svg>
        </div>

        <!-- Headline -->
        <h2 class="auth-left-title">创作的价值，从这里被看见</h2>
        <p class="auth-left-desc">作品存证 · 权益保护 · 合约交易 · AI增长</p>

        <!-- Floating benefit cards -->
        <div class="auth-benefits">
          <div class="auth-benefit-card">
            <span class="auth-benefit-icon">🛡️</span>
            <span class="auth-benefit-text">作品存证</span>
          </div>
          <div class="auth-benefit-card">
            <span class="auth-benefit-icon">📋</span>
            <span class="auth-benefit-text">IP 登记</span>
          </div>
          <div class="auth-benefit-card">
            <span class="auth-benefit-icon">🤝</span>
            <span class="auth-benefit-text">合约挂牌</span>
          </div>
        </div>

        <!-- Stats row -->
        <div class="auth-stats">
          <div class="auth-stat">
            <div class="auth-stat-value">13k+</div>
            <div class="auth-stat-label">活跃创作者</div>
          </div>
          <div class="auth-stat-divider" />
          <div class="auth-stat">
            <div class="auth-stat-value">50k+</div>
            <div class="auth-stat-label">作品存证</div>
          </div>
          <div class="auth-stat-divider" />
          <div class="auth-stat">
            <div class="auth-stat-value">2k+</div>
            <div class="auth-stat-label">IP 登记</div>
          </div>
        </div>
      </div>
    </div>

        <!-- Right Panel -->
    <div class="auth-right">
      <div class="auth-right-inner">
        <div class="auth-header">
          <div class="auth-logo">
            <span class="auth-logo-icon">🎨</span>
            <span class="auth-logo-text">OriStudio</span>
          </div>
          <p class="auth-welcome">{{ mode === 'login' ? '登录账户' : '创建账户' }}</p>
          <p class="auth-desc">{{ mode === 'login' ? '输入邮箱和密码继续' : '填写信息开始创作之旅' }}</p>
        </div>

        <!-- Tabs -->
        <div class="auth-tabs" role="tablist">
          <button role="tab" :aria-selected="mode === 'login'" :class="['auth-tab', { active: mode === 'login' }]" @click="mode = 'login'">登录</button>
          <button role="tab" :aria-selected="mode === 'register'" :class="['auth-tab', { active: mode === 'register' }]" @click="mode = 'register'">注册</button>
        </div>

        <!-- OAuth Buttons -->
        <div class="oauth-section">
          <button class="oauth-btn" @click="oauthLogin('google')">
            <svg class="oauth-icon" width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            <span>Google</span>
          </button>
          <button class="oauth-btn" @click="oauthLogin('wechat')">
            <svg class="oauth-icon" width="18" height="18" viewBox="0 0 24 24" fill="#07C160">
              <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05a6.127 6.127 0 0 1-.253-1.736c0-3.723 3.527-6.744 7.88-6.744.275 0 .543.018.811.045C16.957 4.988 13.118 2.188 8.691 2.188zm-2.6 4.408c.56 0 1.016.454 1.016 1.016 0 .56-.455 1.016-1.016 1.016a1.017 1.017 0 0 1-1.016-1.016c0-.562.457-1.016 1.016-1.016zm5.199 0c.56 0 1.016.454 1.016 1.016 0 .56-.456 1.016-1.016 1.016a1.017 1.017 0 0 1-1.016-1.016c0-.562.455-1.016 1.016-1.016z"/>
              <path d="M23.844 14.721c0-3.472-3.46-6.29-7.724-6.29-4.264 0-7.725 2.818-7.725 6.29 0 3.473 3.46 6.291 7.725 6.291.918 0 1.803-.143 2.614-.39a.722.722 0 0 1 .599.08l1.598.936a.273.273 0 0 0 .14.047c.134 0 .24-.11.24-.247 0-.06-.023-.12-.038-.179l-.328-1.233a.494.494 0 0 1 .177-.553C22.753 18.596 23.844 16.82 23.844 14.72zm-10.268-1.19a.945.945 0 0 1-.94-.94.945.945 0 0 1 .94-.94.945.945 0 0 1 .94.94.945.945 0 0 1-.94.94zm4.793 0a.945.945 0 0 1-.94-.94.945.945 0 0 1 .94-.94.945.945 0 0 1 .94.94.945.945 0 0 1-.94.94z"/>
            </svg>
            <span>微信</span>
          </button>
        </div>

        <!-- Divider -->
        <div class="auth-divider">
          <span>或者使用邮箱登录</span>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="auth-form">
          <div v-if="mode === 'register'" class="form-group">
            <label class="form-label" for="username">用户名</label>
            <div class="form-input">
              <svg class="form-input__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
              </svg>
              <input id="username" :value="form.username" @input="form.username = ($event.target as HTMLInputElement).value" type="text" class="form-input__field" placeholder="创作者名称" autocomplete="username" required />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="email">邮箱</label>
            <div class="form-input">
              <svg class="form-input__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
              </svg>
              <input id="email" :value="form.email" @input="form.email = ($event.target as HTMLInputElement).value" type="email" class="form-input__field" placeholder="your@email.com" autocomplete="email" required />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="password">密码</label>
            <div class="form-input" :class="{ 'form-input--error': errorMsg }">
              <svg class="form-input__icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input id="password" :value="form.password" @input="form.password = ($event.target as HTMLInputElement).value" :type="showPassword ? 'text' : 'password'" class="form-input__field" placeholder="••••••" autocomplete="current-password" required />
              <button type="button" class="form-input__toggle" @click="togglePassword" aria-label="显示密码">
                <svg v-if="!showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
          </div>

          <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

          <button type="submit" class="btn-primary" :disabled="loading">
            <span v-if="loading">处理中...</span>
            <span v-else>{{ mode === 'login' ? '登录' : '注册' }}</span>
          </button>

          <!-- 快速选择账号 -->
          <div class="quick-accounts">
            <button class="btn-quick-toggle" @click="showAccounts = !showAccounts">
              🎯 快速选择账号
              <svg width="12" height="12" viewBox="0 0 12 12" :class="{ open: showAccounts }"><path d="M2 4l4 4 4-4"/></svg>
            </button>
            <div v-if="showAccounts" class="quick-accounts-list">
              <button v-for="acc in ACCOUNTS" :key="acc.email" class="quick-account-btn" @click="quickLogin(acc)">
                <span class="qa-label">{{ acc.label }}</span>
                <span class="qa-email">{{ acc.email }}</span>
                <span class="qa-pwd">{{ acc.password }}</span>
              </button>
            </div>
          </div>
        </form>

        <div class="auth-footer">
          <p>创作者平台 · 权益保护 · 商业撮合</p>
          <p class="auth-redirect">交易后台请前往 <a href="http://localhost:3000" target="_blank">OriSpark</a></p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'
import { useGlobalState } from '@/stores/useGlobalState'

const router = useRouter()
const auth = useAuthStore()
const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)
const showAccounts = ref(false)
const form = ref({ username: '', email: '', password: '' })

// 演示账号
const ACCOUNTS = [
  { label: '🎨 创作者 (OriStudio)', email: 'local@oristudio', password: 'local' },
  { label: '📊 运营方', email: 'operator@test.oristudio.com', password: 'Test1234!' },
  { label: '📸 采购方 (trader)', email: 'trader@test.oristudio.com', password: 'Test1234!' },
  { label: '⚖️ 法务代表', email: 'legal_rep@test.oristudio.com', password: 'Test1234!' },
  { label: '💱 税务代理', email: 'tax_agent@test.oristudio.com', password: 'Test1234!' },
  { label: '🚚 物流方', email: 'logistics@test.oristudio.com', password: 'Test1234!' },
  { label: '🛡️ 保险方', email: 'insurer@test.oristudio.com', password: 'Test1234!' },
  { label: '💳 支付托管', email: 'payment_provider@test.oristudio.com', password: 'Test1234!' },
  { label: '🏢 平台方', email: 'platform@test.oristudio.com', password: 'Test1234!' },
]

function quickLogin(account: typeof ACCOUNTS[0]) {
  form.value.email = account.email
  form.value.password = account.password
  errorMsg.value = ''
}

async function handleSubmit() {
  errorMsg.value = ''
  loading.value = true

  try {
    const success = mode.value === 'login'
      ? await auth.login({ email: form.value.email, password: form.value.password })
      : await auth.register({ username: form.value.username, email: form.value.email, password: form.value.password })

    if (success) {
      const globalState = useGlobalState()
      const savedUser = localStorage.getItem('oristudio-user')
      const user = savedUser ? JSON.parse(savedUser) : null

      // Local 用户直接进入工作台，跳过 Onboarding
      if (user?.role === 'local' || user?.participant_roles?.includes('creator')) {
        globalState.setCreatorType(user?.creator_type || 'illustrator')
        globalState.setParticipantRole('creator')
        globalState.markOnboarded()
        router.push('/app')
        return
      }

      if (!globalState.isOnboarded) {
        router.push('/onboarding')
      } else {
        router.push('/app')
      }
    } else {
      errorMsg.value = auth.error || (mode.value === 'login' ? '登录失败' : '注册失败')
    }
  } catch (err: unknown) {
    errorMsg.value = err instanceof Error ? err.message : '操作失败'
  } finally {
    loading.value = false
  }
}

function oauthLogin(provider: string) {
  const messages: Record<string, string> = {
    google: 'Google 登录需要配置 GOOGLE_CLIENT_ID 后启用',
    wechat: '微信登录需要配置 WECHAT_APPID 后启用',
  }
  const msg = messages[provider] || `${provider} OAuth 暂未配置`
  const toast = (window as any)?.$toast
  if (toast && typeof toast.show === 'function') {
    toast.show(msg, 'info')
  }
}

function togglePassword() {
  showPassword.value = !showPassword.value
}
</script>

<style scoped>
.auth-layout { min-height: 100dvh; display: flex; }

/* ── Left Panel ── */
.auth-left {
  flex: 1;
  position: relative;
  background: linear-gradient(145deg, #312E81 0%, #4F46E5 45%, #6366F1 75%, #818CF8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  min-height: 100dvh;
}
.auth-left-bg {
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 70% 50% at 70% 30%, rgba(255,255,255,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 40% 30% at 20% 80%, rgba(99,102,241,0.3) 0%, transparent 50%);
}
.auth-left-shapes { position: absolute; inset: 0; }
.auth-shape {
  position: absolute; border-radius: 50%; background: white; opacity: 0.07;
}
.auth-shape-1 { width: 320px; height: 320px; top: -60px; right: -60px; }
.auth-shape-2 { width: 220px; height: 220px; bottom: 40px; left: -40px; }
.auth-shape-3 { width: 140px; height: 140px; bottom: -20px; right: 80px; }
.auth-shape-4 { width: 80px; height: 80px; top: 30%; left: 10%; opacity: 0.05; }

.auth-left-content {
  position: relative; z-index: 1; text-align: center; padding: 2.5rem 2rem; color: white; max-width: 420px;
}

/* Brand */
.auth-brand {
  display: inline-flex; align-items: center; gap: 0.5rem;
  font-size: 1.125rem; font-weight: 700; color: white; margin-bottom: 1.75rem;
  letter-spacing: -0.02em;
}
.auth-brand-icon { font-size: 1.5rem; }

/* Illustration */
.auth-illustration { margin-bottom: 1.75rem; }
.auth-svg { width: 160px; height: 160px; filter: drop-shadow(0 12px 32px rgba(0,0,0,0.2)); }

/* Headline */
.auth-left-title {
  font-size: 1.625rem; font-weight: 800; margin: 0 0 0.5rem;
  letter-spacing: -0.02em; line-height: 1.25; color: white;
  text-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
.auth-left-desc {
  font-size: 0.875rem; opacity: 0.75; margin: 0 0 2rem;
  letter-spacing: 0.02em; font-weight: 500;
}

/* Floating benefit cards */
.auth-benefits {
  display: flex; gap: 0.625rem; justify-content: center; margin-bottom: 2rem; flex-wrap: wrap;
}
.auth-benefit-card {
  display: inline-flex; align-items: center; gap: 0.375rem;
  padding: 6px 14px; border-radius: 9999px;
  background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.22);
  backdrop-filter: blur(8px); font-size: 0.8125rem; font-weight: 500; color: white;
  transition: background 0.15s;
}
.auth-benefit-card:hover { background: rgba(255,255,255,0.22); }
.auth-benefit-icon { font-size: 1rem; }

/* Stats */
.auth-stats { display: flex; align-items: center; gap: 1.5rem; justify-content: center; }
.auth-stat { text-align: center; }
.auth-stat-value { font-size: 1.625rem; font-weight: 800; line-height: 1.2; }
.auth-stat-label { font-size: 0.75rem; opacity: 0.7; margin-top: 2px; }
.auth-stat-divider { width: 1px; height: 40px; background: rgba(255,255,255,0.25); }

/* ── Right Panel ── */
.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--m-surface, #fff);
  padding: 2rem;
}
.auth-right-inner { width: 100%; max-width: 440px; }
.auth-header { margin-bottom: 1.5rem; }
.auth-logo { display: inline-flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
.auth-logo-icon { font-size: 2rem; }
.auth-logo-text {
  font-size: 1.5rem; font-weight: 800;
  background: linear-gradient(135deg, #4F46E5, #6366F1);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}
.auth-welcome { font-size: 1.375rem; font-weight: 700; color: #0F172A; margin: 0 0 0.25rem; letter-spacing: -0.01em; }
.auth-desc { font-size: 0.875rem; color: #64748B; margin: 0 0 1.5rem; }

/* ── Tabs ── */
.auth-tabs {
  display: flex; gap: 4px; margin-bottom: 1.5rem;
  background: #F1F5F9; border-radius: var(--m-radius-md, 12px); padding: 4px;
}
.auth-tab {
  flex: 1; padding: 8px; border: none; border-radius: var(--m-radius-sm, 8px);
  font-size: 0.9375rem; font-weight: 600;
  background: transparent; color: #94A3B8; cursor: pointer; transition: all 0.15s; font-family: inherit;
}
.auth-tab.active {
  background: #fff; color: #0F172A;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* ── OAuth ── */
.oauth-section { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; }
.oauth-btn {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 0.5rem;
  padding: 10px 16px; border: 1.5px solid #E2E8F0; border-radius: var(--m-radius-md, 12px);
  font-size: 0.875rem; font-weight: 600; background: #fff; color: #0F172A;
  cursor: pointer; transition: all 0.15s; font-family: inherit;
}
.oauth-btn:hover { border-color: #4F46E5; background: rgba(79,70,229,0.04); color: #4F46E5; }

/* ── Divider ── */
.auth-divider {
  display: flex; align-items: center; gap: 0.75rem; margin: 1.5rem 0;
  color: #94A3B8; font-size: 0.8125rem;
}
.auth-divider::before, .auth-divider::after { content: ''; flex: 1; height: 1px; background: #E2E8F0; }

/* ── Form ── */
.auth-form { display: flex; flex-direction: column; gap: 1.25rem; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 0.8125rem; font-weight: 500; color: rgba(46, 38, 61, 0.9); }
.form-error { color: #DC2626; font-size: 0.8125rem; }

/* ── Nuxt-style form-input ── */
.form-input {
  position: relative;
  display: flex;
  align-items: center;
  border: 1.5px solid #E5E7EB;
  border-radius: 10px;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
  background: #F9FAFB;
}
.form-input:focus-within {
  border-color: #4F46E5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
  background: #FFFFFF;
}
.form-input--error {
  border-color: #DC2626;
}
.form-input--error:focus-within {
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.12);
}
.form-input__icon {
  position: absolute;
  left: 12px;
  width: 18px;
  height: 18px;
  color: #9CA3AF;
  pointer-events: none;
  flex-shrink: 0;
}
.form-input__field {
  flex: 1;
  height: 46px;
  padding: 0 44px 0 42px;
  border: none;
  outline: none;
  font-size: 0.9375rem;
  font-family: inherit;
  color: #1F2937;
  background: transparent;
}
.form-input__field::placeholder { color: #9CA3AF; }

/* Password toggle */
.form-input__toggle {
  position: absolute;
  right: 12px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #9CA3AF;
  cursor: pointer;
  border-radius: 6px;
  transition: color 0.15s;
}
.form-input__toggle:hover { color: #4F46E5; }
.form-input__toggle svg { width: 18px; height: 18px; }

/* ── Primary Button ── */
.btn-primary {
  height: 48px; padding: 0 1.5rem;
  background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
  color: white; border: none; border-radius: var(--m-radius-md, 12px);
  font-size: 0.9375rem; font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: inherit;
  box-shadow: 0 4px 16px rgba(79,70,229,0.28);
}
.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%);
  box-shadow: 0 6px 24px rgba(79,70,229,0.38); transform: translateY(-1px);
}
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }

/* ── Quick Account Picker ── */
.quick-accounts { margin-top: 1.25rem; }
.btn-quick-toggle {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px 16px; border: 1.5px dashed rgba(79,70,229,0.25); border-radius: 10px;
  background: rgba(79,70,229,0.03); color: #4F46E5; font-size: 0.8125rem;
  font-weight: 500; cursor: pointer; transition: all 0.15s; font-family: inherit;
}
.btn-quick-toggle:hover { background: rgba(79,70,229,0.07); border-color: #4F46E5; }
.btn-quick-toggle svg { transition: transform 0.2s; }
.btn-quick-toggle svg.open { transform: rotate(180deg); }
.quick-accounts-list {
  margin-top: 8px; display: flex; flex-direction: column; gap: 6px;
  max-height: 260px; overflow-y: auto;
}
.quick-account-btn {
  display: flex; flex-direction: column; align-items: flex-start;
  padding: 8px 12px; border: 1px solid #E5E7EB; border-radius: 8px;
  background: #F9FAFB; cursor: pointer; transition: all 0.15s; text-align: left;
}
.quick-account-btn:hover { border-color: #4F46E5; background: rgba(79,70,229,0.04); }
.qa-label { font-size: 0.8125rem; font-weight: 600; color: #1F2937; }
.qa-email { font-size: 0.6875rem; color: #6B7280; font-family: monospace; }
.qa-pwd { font-size: 0.6875rem; color: #9CA3AF; font-family: monospace; }

/* ── Footer ── */
.auth-footer { margin-top: 1.5rem; text-align: center; }
.auth-footer p { font-size: 0.8125rem; color: #94A3B8; margin: 0.25rem 0; }
.auth-footer a { color: #4F46E5; text-decoration: none; font-weight: 500; }
.auth-footer a:hover { text-decoration: underline; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .auth-left { display: none; }
  .auth-right { flex: 1; }
  .oauth-section { flex-direction: column; }
}
</style>

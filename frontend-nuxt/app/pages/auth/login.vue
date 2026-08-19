<!-- OriSpark Login Page — Materio Demo-5 Style
     Left: Illustration + OriSpark intro | Right: White form panel -->
<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'default' })

const auth = useAuthStore()

// 演示账号（MVP 阶段使用）
const DEMO_EMAIL = 'demo@orispark'
const DEMO_PASSWORD = 'orispark2026'

const email = ref(DEMO_EMAIL)
const password = ref(DEMO_PASSWORD)
const submitting = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)
const remember = ref(false)
const showAccounts = ref(false)

// 演示账号
const ACCOUNTS = [
  { label: '📊 运营方 (operator)', email: 'operator@test.oristudio.com', password: 'Test1234!' },
  { label: '📸 采购方 (trader)', email: 'trader@test.oristudio.com', password: 'Test1234!' },
  { label: '⚖️ 法务代表', email: 'legal_rep@test.oristudio.com', password: 'Test1234!' },
  { label: '💱 税务代理', email: 'tax_agent@test.oristudio.com', password: 'Test1234!' },
  { label: '🚚 物流方', email: 'logistics@test.oristudio.com', password: 'Test1234!' },
  { label: '🛡️ 保险方', email: 'insurer@test.oristudio.com', password: 'Test1234!' },
  { label: '💳 支付托管', email: 'payment_provider@test.oristudio.com', password: 'Test1234!' },
  { label: '🏢 平台方', email: 'platform@test.oristudio.com', password: 'Test1234!' },
  { label: '🎨 创作者 (去 OriStudio)', email: 'local@oristudio', password: 'local' },
]

function quickLogin(account: typeof ACCOUNTS[0]) {
  email.value = account.email
  password.value = account.password
  errorMsg.value = ''
  showAccounts.value = false
}

async function handleLogin() {
  if (!email.value || !password.value) {
    errorMsg.value = '请输入邮箱和密码'
    return
  }
  submitting.value = true
  errorMsg.value = ''
  const success = await auth.login(email.value, password.value)
  submitting.value = false
  if (success) {
    navigateTo('/market')
  } else {
    errorMsg.value = auth.error || '登录失败，请检查账号密码'
  }
}

/** 一键演示登录 — 自动填入超级管理员账号并登录 */
async function handleDemoLogin() {
  email.value = DEMO_EMAIL
  password.value = DEMO_PASSWORD
  errorMsg.value = ''
  submitting.value = true
  const success = await auth.login(DEMO_EMAIL, DEMO_PASSWORD)
  submitting.value = false
  if (success) {
    navigateTo('/market')
  } else {
    errorMsg.value = auth.error || '登录失败，请检查账号密码'
  }
}
</script>

<template>
  <div class="auth-page">
    <!-- ═══════════════════════════════════════════════════════════
         LEFT PANEL — Branding & Illustration
         ═══════════════════════════════════════════════════════════ -->
    <div class="auth-left">
      <div class="auth-left__bg" />
      <div class="auth-left__overlay" />

      <!-- Floating decorative cards -->
      <div class="auth-left__floats">
        <div class="auth-float auth-float--1">
          <div class="auth-float__icon">📊</div>
          <div class="auth-float__text">合约增长</div>
          <div class="auth-float__value">+48.5%</div>
        </div>
        <div class="auth-float auth-float--2">
          <div class="auth-float__icon">💰</div>
          <div class="auth-float__text">交易额</div>
          <div class="auth-float__value">¥21,845</div>
        </div>
        <div class="auth-float auth-float--3">
          <div class="auth-float__icon">🔗</div>
          <div class="auth-float__text">存证</div>
          <div class="auth-float__value">50k+</div>
        </div>
      </div>

      <!-- Left content -->
      <div class="auth-left__content">
        <!-- Logo -->
        <div class="auth-left__logo">
          <svg class="auth-left__logo-icon" width="32" height="26" viewBox="0 0 30 24" fill="none">
            <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
            <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
            <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
            <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
          </svg>
          <span class="auth-left__logo-text">OriSpark</span>
        </div>

        <!-- 3D character illustration (SVG) -->
        <div class="auth-left__illustration">
          <svg viewBox="0 0 300 300" class="auth-left__svg" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Platform -->
            <ellipse cx="150" cy="260" rx="100" ry="20" fill="rgba(255,255,255,0.08)"/>
            <ellipse cx="150" cy="255" rx="80" ry="14" fill="rgba(255,255,255,0.06)"/>
            <!-- Body -->
            <rect x="115" y="130" width="70" height="100" rx="16" fill="rgba(255,255,255,0.15)"/>
            <rect x="115" y="130" width="70" height="100" rx="16" fill="url(#bodyGrad)"/>
            <!-- Head -->
            <circle cx="150" cy="95" r="42" fill="rgba(255,255,255,0.9)"/>
            <!-- Hair -->
            <ellipse cx="150" cy="72" rx="38" ry="24" fill="#FF6B6B"/>
            <ellipse cx="150" cy="78" rx="40" ry="18" fill="#FF8E8E"/>
            <!-- Eyes -->
            <circle cx="137" cy="95" r="4" fill="#1F2937"/>
            <circle cx="163" cy="95" r="4" fill="#1F2937"/>
            <circle cx="138" cy="94" r="1.5" fill="white"/>
            <circle cx="164" cy="94" r="1.5" fill="white"/>
            <!-- Smile -->
            <path d="M142 108 Q150 116 158 108" stroke="#1F2937" stroke-width="2.5" fill="none" stroke-linecap="round"/>
            <!-- Arms -->
            <rect x="80" y="145" width="35" height="14" rx="7" fill="rgba(255,255,255,0.85)" transform="rotate(-15 97 152)"/>
            <rect x="185" y="145" width="35" height="14" rx="7" fill="rgba(255,255,255,0.85)" transform="rotate(15 202 152)"/>
            <!-- Laptop -->
            <rect x="100" y="160" width="55" height="35" rx="4" fill="#4F46E5" opacity="0.9"/>
            <rect x="103" y="163" width="49" height="26" rx="2" fill="#A5B4FC" opacity="0.6"/>
            <!-- Legs -->
            <rect x="125" y="225" width="18" height="40" rx="9" fill="rgba(255,255,255,0.7)"/>
            <rect x="157" y="225" width="18" height="40" rx="9" fill="rgba(255,255,255,0.7)"/>
            <!-- Shoes -->
            <ellipse cx="134" cy="268" rx="14" ry="7" fill="#3B82F6"/>
            <ellipse cx="166" cy="268" rx="14" ry="7" fill="#3B82F6"/>
            <!-- Gradient defs -->
            <defs>
              <linearGradient id="bodyGrad" x1="115" y1="130" x2="185" y2="230">
                <stop offset="0%" stop-color="rgba(124,58,237,0.5)"/>
                <stop offset="100%" stop-color="rgba(59,130,246,0.3)"/>
              </linearGradient>
            </defs>
          </svg>
        </div>

        <!-- Text content -->
        <h1 class="auth-left__title">欢迎来到 OriSpark 👋</h1>
        <p class="auth-left__desc">登录您的账户，开始探索创作者经济的信任枢纽</p>

        <!-- Stats -->
        <div class="auth-left__stats">
          <div class="auth-left__stat">
            <div class="auth-left__stat-value">13k+</div>
            <div class="auth-left__stat-label">创作者</div>
          </div>
          <div class="auth-left__stat-divider" />
          <div class="auth-left__stat">
            <div class="auth-left__stat-value">50k+</div>
            <div class="auth-left__stat-label">作品存证</div>
          </div>
          <div class="auth-left__stat-divider" />
          <div class="auth-left__stat">
            <div class="auth-left__stat-value">99.9%</div>
            <div class="auth-left__stat-label">可信度</div>
          </div>
        </div>

        <!-- Decorative plants -->
        <div class="auth-left__plant auth-left__plant--1">
          <svg viewBox="0 0 60 100" fill="none">
            <rect x="25" y="70" width="10" height="25" rx="3" fill="rgba(255,255,255,0.2)"/>
            <ellipse cx="30" cy="55" rx="20" ry="30" fill="rgba(167,139,250,0.3)"/>
            <ellipse cx="20" cy="40" rx="14" ry="22" fill="rgba(139,92,246,0.35)"/>
            <ellipse cx="40" cy="42" rx="12" ry="18" fill="rgba(167,139,250,0.25)"/>
          </svg>
        </div>
        <div class="auth-left__plant auth-left__plant--2">
          <svg viewBox="0 0 50 80" fill="none">
            <rect x="20" y="55" width="10" height="20" rx="3" fill="rgba(255,255,255,0.15)"/>
            <ellipse cx="25" cy="42" rx="16" ry="24" fill="rgba(139,92,246,0.25)"/>
            <ellipse cx="18" cy="30" rx="11" ry="18" fill="rgba(167,139,250,0.3)"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         RIGHT PANEL — Login Form
         ═══════════════════════════════════════════════════════════ -->
    <div class="auth-right">
      <div class="auth-right__inner">
        <!-- Logo (small, top) -->
        <NuxtLink to="/" class="auth-right__logo">
          <svg class="auth-right__logo-icon" width="28" height="22" viewBox="0 0 30 24" fill="none">
            <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
            <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
            <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
            <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
          </svg>
          <span class="auth-right__logo-text">OriSpark</span>
        </NuxtLink>

        <!-- Welcome text -->
        <div class="auth-right__welcome">
          <h2 class="auth-right__heading">欢迎来到 OriSpark！👋</h2>
          <p class="auth-right__subheading">请登录您的账户，开启创作者交易之旅</p>
        </div>

        <!-- Login form -->
        <form @submit.prevent="handleLogin" class="auth-form">
          <!-- Email -->
          <div class="form-group">
            <label class="form-label" for="email">邮箱</label>
            <div class="form-input" :class="{ 'form-input--error': errorMsg }">
              <i class="material-icons form-input__icon">mail</i>
              <input
                id="email"
                v-model="email"
                type="email"
                class="form-input__field"
                placeholder="your@email.com"
                autocomplete="email"
                required
              />
            </div>
          </div>

          <!-- Password -->
          <div class="form-group">
            <label class="form-label" for="password">密码</label>
            <div class="form-input">
              <i class="material-icons form-input__icon">lock</i>
              <input
                id="password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input__field"
                placeholder="••••••••"
                autocomplete="current-password"
                required
              />
              <button type="button" class="form-input__toggle" @click="showPassword = !showPassword" aria-label="显示密码">
                <i class="material-icons">{{ showPassword ? 'visibility_off' : 'visibility' }}</i>
              </button>
            </div>
          </div>

          <!-- Error -->
          <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

          <!-- Remember + Forgot -->
          <div class="form-options">
            <label class="form-checkbox">
              <input v-model="remember" type="checkbox" />
              <span class="form-checkbox__box" />
              <span>记住我</span>
            </label>
            <NuxtLink to="/auth/forgot-password" class="form-link">忘记密码？</NuxtLink>
          </div>

          <!-- Submit -->
          <button type="submit" class="btn-submit" :disabled="submitting">
            <svg v-if="submitting" class="btn-submit__spinner" viewBox="0 0 24 24" width="18" height="18">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2.5" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>
            </svg>
            {{ submitting ? '登录中...' : '登录' }}
          </button>

          <!-- Demo quick login -->
          <button type="button" class="btn-demo" :disabled="submitting" @click="handleDemoLogin">
            <i class="material-icons">bolt</i>
            快速演示登录（超级管理员）
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

        <!-- Register link -->
        <p class="auth-footer-text">
          还没有账号？<NuxtLink to="/auth/register" class="auth-footer-link">立即注册</NuxtLink>
        </p>

        <!-- Divider -->
        <div class="auth-divider">
          <span>或者</span>
        </div>

        <!-- OAuth -->
        <div class="oauth-group">
          <button class="btn-oauth" type="button">
            <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l-3.15 3.15c-.73.55-1.63.88-2.69.88-2.08 0-3.85-1.35-4.57-3.25l-2.85 2.22C2.19 11.55 7.07 8 12 8z" fill="#EA4335"/></svg>
            Google
          </button>
          <button class="btn-oauth" type="button">
            <span class="oauth-icon">💬</span>
            微信
          </button>
        </div>

        <!-- Redirect -->
        <p class="auth-redirect-text">
          创作者请前往 <a href="http://localhost:5174" target="_blank">OriStudio</a>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   PAGE LAYOUT
   ═══════════════════════════════════════════════════════════ */
.auth-page {
  min-height: 100dvh;
  display: flex;
  background: #FFFFFF;
}

/* ═══════════════════════════════════════════════════════════
   LEFT PANEL
   ═══════════════════════════════════════════════════════════ */
.auth-left {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  min-height: 100dvh;
  background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 30%, #C7D2FE 60%, #A5B4FC 100%);
}
.auth-left__bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 60% 40%, rgba(139,92,246,0.3) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 20% 80%, rgba(59,130,246,0.2) 0%, transparent 50%);
}
.auth-left__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(139,92,246,0.05) 0%, rgba(88,28,135,0.15) 100%);
}

/* Floating cards */
.auth-left__floats {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.auth-float {
  position: absolute;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(8px);
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  border: 1px solid rgba(255,255,255,0.6);
}
.auth-float--1 { top: 15%; left: 10%; animation: floatSlow 7s ease-in-out infinite; }
.auth-float--2 { top: 25%; right: 8%; animation: floatSlow 8s ease-in-out infinite 1s; }
.auth-float--3 { bottom: 25%; left: 15%; animation: floatSlow 6s ease-in-out infinite 0.5s; }
.auth-float__icon { font-size: 20px; margin-bottom: 4px; }
.auth-float__text { font-size: 11px; color: #6B7280; }
.auth-float__value { font-size: 16px; font-weight: 700; color: #1F2937; }

@keyframes floatSlow {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

/* Left content */
.auth-left__content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 2rem;
  color: white;
  max-width: 400px;
}
.auth-left__logo {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2rem;
  color: white;
  text-decoration: none;
}
.auth-left__logo-icon { color: white; }
.auth-left__logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.auth-left__illustration {
  margin-bottom: 2rem;
}
.auth-left__svg {
  width: 220px;
  height: 220px;
  filter: drop-shadow(0 20px 40px rgba(0,0,0,0.15));
}
.auth-left__title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
  color: white;
  text-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.auth-left__desc {
  font-size: 0.9375rem;
  opacity: 0.85;
  margin: 0 0 2rem;
  line-height: 1.6;
}

/* Stats */
.auth-left__stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
}
.auth-left__stat { text-align: center; }
.auth-left__stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.2;
}
.auth-left__stat-label {
  font-size: 0.75rem;
  opacity: 0.8;
}
.auth-left__stat-divider {
  width: 1px;
  height: 36px;
  background: rgba(255,255,255,0.35);
}

/* Plants */
.auth-left__plant {
  position: absolute;
  bottom: 0;
  opacity: 0.6;
}
.auth-left__plant--1 { left: 5%; }
.auth-left__plant--2 { right: 8%; }

/* ═══════════════════════════════════════════════════════════
   RIGHT PANEL
   ═══════════════════════════════════════════════════════════ */
.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #FFFFFF;
  padding: 2rem;
  min-height: 100dvh;
}
.auth-right__inner {
  width: 100%;
  max-width: 400px;
}

/* Logo */
.auth-right__logo {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  margin-bottom: 2rem;
  color: #1F2937;
}
.auth-right__logo-icon { color: #4F46E5; }
.auth-right__logo-text {
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #4F46E5, #3B82F6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* Welcome */
.auth-right__welcome { margin-bottom: 2rem; }
.auth-right__heading {
  font-size: 1.375rem;
  font-weight: 700;
  color: #1F2937;
  margin: 0 0 4px;
}
.auth-right__subheading {
  font-size: 0.875rem;
  color: #6B728B;
  margin: 0;
}

/* Form */
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: rgba(46, 38, 61, 0.9);
}
.form-input {
  position: relative;
  display: flex;
  align-items: center;
  border: 1.5px solid #E5E7EB;
  border-radius: 10px;
  transition: all 0.15s;
  background: #F9FAFB;
}
.form-input:focus-within {
  border-color: #4F46E5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
  background: #FFFFFF;
}
.form-input--error {
  border-color: #EF4444;
}
.form-input--error:focus-within {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.12);
}
.form-input__icon {
  position: absolute;
  left: 12px;
  font-size: 18px;
  color: #9CA3AF;
  pointer-events: none;
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
.form-input__toggle:hover { color: #6B7280; }

/* Error */
.form-error {
  color: #EF4444;
  font-size: 0.8125rem;
  margin: 0;
}

/* Options */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.form-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.8125rem;
  color: #4B5563;
  user-select: none;
}
.form-checkbox input { display: none; }
.form-checkbox__box {
  width: 18px;
  height: 18px;
  border: 2px solid #D1D5DB;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}
.form-checkbox input:checked + .form-checkbox__box {
  background: #4F46E5;
  border-color: #4F46E5;
}
.form-checkbox input:checked + .form-checkbox__box::after {
  content: '✓';
  color: white;
  font-size: 12px;
  font-weight: 700;
}
.form-link {
  font-size: 0.8125rem;
  color: #4F46E5;
  text-decoration: none;
  font-weight: 500;
}
.form-link:hover { text-decoration: underline; }

/* Submit button */
.btn-submit {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: inherit;
}
.btn-submit:hover:not(:disabled) {
  background: linear-gradient(135deg, #4338CA 0%, #3730A3 100%);
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35);
  transform: translateY(-1px);
}
.btn-submit:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
.btn-submit__spinner { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Demo button */
.btn-demo {
  width: 100%;
  height: 42px;
  background: transparent;
  border: 1.5px dashed rgba(79, 70, 229, 0.35);
  border-radius: 10px;
  color: #4F46E5;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-family: inherit;
  margin-top: -4px;
}
.btn-demo:hover:not(:disabled) {
  background: rgba(79, 70, 229, 0.06);
  border-color: #4F46E5;
}
.btn-demo:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-demo .material-icons { font-size: 16px; }

/* ── Quick Account Picker ── */
.quick-accounts { margin-top: 1.25rem; }
.btn-quick-toggle {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px 16px; border: 1.5px dashed rgba(79, 70, 229, 0.25); border-radius: 10px;
  background: rgba(79, 70, 229, 0.03); color: #4F46E5; font-size: 0.8125rem;
  font-weight: 500; cursor: pointer; transition: all 0.15s; font-family: inherit;
}
.btn-quick-toggle:hover { background: rgba(79, 70, 229, 0.07); border-color: #4F46E5; }
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
.quick-account-btn:hover { border-color: #4F46E5; background: rgba(79, 70, 229, 0.04); }
.qa-label { font-size: 0.8125rem; font-weight: 600; color: #1F2937; }
.qa-email { font-size: 0.6875rem; color: #6B7280; font-family: monospace; }
.qa-pwd { font-size: 0.6875rem; color: #9CA3AF; font-family: monospace; }

/* Footer text */
.auth-footer-text {
  text-align: center;
  font-size: 0.875rem;
  color: #6B728B;
  margin: 1.5rem 0 0;
}
.auth-footer-link {
  color: #4F46E5;
  text-decoration: none;
  font-weight: 600;
}
.auth-footer-link:hover { text-decoration: underline; }

/* Divider */
.auth-divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
  color: #9CA3AF;
  font-size: 0.8125rem;
}
.auth-divider::before, .auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #E5E7EB;
}

/* OAuth */
.oauth-group {
  display: flex;
  gap: 12px;
}
.btn-oauth {
  flex: 1;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1.5px solid #E5E7EB;
  border-radius: 10px;
  background: white;
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(46, 38, 61, 0.9);
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.btn-oauth:hover {
  border-color: #4F46E5;
  background: rgba(79, 70, 229, 0.04);
  color: #4F46E5;
}
.oauth-icon { font-size: 18px; }

/* Redirect */
.auth-redirect-text {
  text-align: center;
  font-size: 0.75rem;
  color: #9CA3AF;
  margin: 1rem 0 0;
}
.auth-redirect-text a {
  color: #4F46E5;
  text-decoration: none;
}
.auth-redirect-text a:hover { text-decoration: underline; }

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 900px) {
  .auth-left { display: none; }
  .auth-right { flex: 1; }
}
</style>

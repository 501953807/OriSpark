<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'default' })

const auth = useAuthStore()
const email = ref('')
const password = ref('')
const submitting = ref(false)
const errorMsg = ref('')
const remember = ref(false)

async function handleLogin() {
  if (!email.value || !password.value) {
    errorMsg.value = '请输入邮箱和密码'
    return
  }
  submitting.value = true
  errorMsg.value = ''
  const success = await auth.login(email.value, password.value, remember.value)
  submitting.value = false
  if (success) {
    navigateTo('/market')
  } else {
    errorMsg.value = auth.error || '登录失败，请检查账号密码'
  }
}
</script>

<template>
  <div class="auth-layout">
    <!-- Left Panel: Illustration -->
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
            <!-- Background circle -->
            <circle cx="200" cy="200" r="160" fill="rgba(255,255,255,0.1)" />
            <!-- Abstract person -->
            <circle cx="200" cy="140" r="45" fill="rgba(255,255,255,0.9)" />
            <path d="M120 300 Q200 200 280 300" stroke="rgba(255,255,255,0.9)" stroke-width="20" fill="none" stroke-linecap="round" />
            <!-- Floating elements -->
            <circle cx="100" cy="120" r="20" fill="#5585FF" opacity="0.8" />
            <circle cx="300" cy="160" r="15" fill="#56CA00" opacity="0.8" />
            <rect x="80" y="240" width="30" height="30" rx="6" fill="#16B1FF" opacity="0.8" transform="rotate(15 95 255)" />
            <rect x="290" y="260" width="25" height="25" rx="4" fill="#FFB400" opacity="0.8" transform="rotate(-10 302 272)" />
          </svg>
        </div>
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
          <div class="auth-stat-divider" />
          <div class="auth-stat">
            <div class="auth-stat-value">99.9%</div>
            <div class="auth-stat-label">可信度</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Panel: Form -->
    <div class="auth-right">
      <div class="auth-right-inner">
        <div class="auth-header">
          <NuxtLink to="/" class="auth-logo">
            <span class="auth-logo-icon">⚡</span>
            <span class="auth-logo-text">OriSpark</span>
          </NuxtLink>
          <p class="auth-welcome">欢迎回来！请登录您的账户</p>
        </div>

        <form @submit.prevent="handleLogin" class="auth-form">
          <!-- Email -->
          <div class="form-field">
            <label for="email" class="form-label">邮箱</label>
            <div class="form-input-wrapper" :class="{ 'form-input-wrapper--error': errorMsg }">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
              </svg>
              <input
                id="email"
                v-model="email"
                type="email"
                class="form-input"
                placeholder="your@email.com"
                autocomplete="email"
                required
              />
            </div>
          </div>

          <!-- Password -->
          <div class="form-field">
            <label for="password" class="form-label">密码</label>
            <div class="form-input-wrapper">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input
                id="password"
                v-model="password"
                type="password"
                class="form-input"
                placeholder="••••••••"
                autocomplete="current-password"
                required
              />
            </div>
          </div>

          <!-- Error -->
          <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

          <!-- Remember + Forgot -->
          <div class="form-extras">
            <label class="form-checkbox">
              <input v-model="remember" type="checkbox" />
              <span class="form-checkbox-mark" />
              <span>记住我</span>
            </label>
            <NuxtLink to="/auth/forgot-password" class="form-link">忘记密码？</NuxtLink>
          </div>

          <!-- Submit -->
          <button type="submit" class="btn-primary" :disabled="submitting">
            <span v-if="submitting">
              <svg class="btn-spinner" viewBox="0 0 24 24" width="16" height="16">
                <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2.5" stroke-dasharray="31.4 31.4" stroke-linecap="round" />
              </svg>
              登录中...
            </span>
            <span v-else>登录</span>
          </button>
        </form>

        <!-- Divider -->
        <div class="auth-divider">
          <span>或者</span>
        </div>

        <!-- OAuth -->
        <div class="oauth-buttons">
          <button class="btn-oauth" @click="auth.loginWith('google')">
            <span>G</span> Google
          </button>
          <button class="btn-oauth" @click="auth.loginWith('wechat')">
            <span>💬</span> 微信
          </button>
        </div>

        <!-- Register link -->
        <p class="auth-footer">
          还没有账号？<NuxtLink to="/auth/register" class="auth-link">立即注册</NuxtLink>
        </p>
        <p class="auth-redirect">
          创作者请前往 <a href="http://localhost:5174" target="_blank">OriStudio</a>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  min-height: 100dvh;
  display: flex;
}

/* ── Left Panel ── */
.auth-left {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, #5585FF 0%, #2A52B0 50%, #4A2D99 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  min-height: 100dvh;
}
.auth-left-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(140,87,255,0.95) 0%, rgba(106,63,204,0.95) 100%);
}
.auth-left-shapes {
  position: absolute;
  inset: 0;
}
.auth-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
  background: white;
}
.auth-shape-1 { width: 300px; height: 300px; top: -50px; right: -50px; }
.auth-shape-2 { width: 200px; height: 200px; bottom: 50px; left: -30px; }
.auth-shape-3 { width: 150px; height: 150px; bottom: -30px; right: 100px; }
.auth-left-content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 2rem;
  color: white;
}
.auth-illustration {
  margin-bottom: 2rem;
}
.auth-svg {
  width: 200px;
  height: 200px;
  filter: drop-shadow(0 10px 30px rgba(0,0,0,0.2));
}
.auth-stats {
  display: flex;
  align-items: center;
  gap: 2rem;
  justify-content: center;
}
.auth-stat { text-align: center; }
.auth-stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.2;
}
.auth-stat-label {
  font-size: 0.8125rem;
  opacity: 0.8;
}
.auth-stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255,255,255,0.3);
}

/* ── Right Panel ── */
.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #FFFFFF;
  padding: 2rem;
}
.auth-right-inner {
  width: 100%;
  max-width: 420px;
}
.auth-header { margin-bottom: 2rem; }
.auth-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  margin-bottom: 1rem;
}
.auth-logo-icon { font-size: 2rem; }
.auth-logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #5585FF, #2A52B0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.auth-welcome {
  font-size: 1rem;
  color: #64748B;
  margin: 0;
}

/* ── Form ── */
.auth-form { display: flex; flex-direction: column; gap: 1.25rem; }
.form-field { display: flex; flex-direction: column; gap: 0.375rem; }
.form-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #374151;
}
.form-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  border: 1.5px solid #E5E7EB;
  border-radius: 8px;
  transition: all 0.15s;
  background: #FFFFFF;
}
.form-input-wrapper:focus-within {
  border-color: #5585FF;
  box-shadow: 0 0 0 3px rgba(85, 133, 255, 0.1);
}
.form-input-wrapper--error {
  border-color: #EF4444;
}
.form-input-icon {
  position: absolute;
  left: 12px;
  color: #9CA3AF;
  pointer-events: none;
}
.form-input {
  flex: 1;
  height: 44px;
  padding: 0 0.75rem 0 2.75rem;
  border: none;
  outline: none;
  font-size: 0.9375rem;
  font-family: inherit;
  color: #1F2937;
  background: transparent;
}
.form-input::placeholder { color: #9CA3AF; }
.form-error {
  color: #EF4444;
  font-size: 0.8125rem;
  margin: 0;
}
.form-extras {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.form-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.8125rem;
  color: #4B5563;
}
.form-checkbox input { display: none; }
.form-checkbox-mark {
  width: 16px;
  height: 16px;
  border: 2px solid #D1D5DB;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.form-checkbox input:checked + .form-checkbox-mark {
  background: #5585FF;
  border-color: #5585FF;
}
.form-checkbox input:checked + .form-checkbox-mark::after {
  content: '✓';
  color: white;
  font-size: 10px;
  font-weight: 700;
}
.form-link {
  font-size: 0.8125rem;
  color: #5585FF;
  text-decoration: none;
}
.form-link:hover { text-decoration: underline; }

/* ── Buttons ── */
.btn-primary {
  height: 44px;
  padding: 0 1.5rem;
  background: linear-gradient(135deg, #5585FF 0%, #3D6DD6 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}
.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #3D6DD6 0%, #2A52B0 100%);
  box-shadow: 0 4px 12px rgba(85, 133, 255, 0.4);
}
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }
.btn-spinner { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Divider ── */
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

/* ── OAuth ── */
.oauth-buttons { display: flex; flex-direction: column; gap: 0.75rem; }
.btn-oauth {
  height: 44px;
  padding: 0 1rem;
  border: 1.5px solid #E5E7EB;
  border-radius: 8px;
  background: white;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #374151;
}
.btn-oauth:hover {
  border-color: #5585FF;
  background: rgba(85, 133, 255, 0.04);
}

/* ── Footer ── */
.auth-footer {
  text-align: center;
  font-size: 0.875rem;
  color: #64748B;
  margin: 1.5rem 0 0.5rem;
}
.auth-link {
  color: #5585FF;
  text-decoration: none;
  font-weight: 600;
}
.auth-link:hover { text-decoration: underline; }
.auth-redirect {
  text-align: center;
  font-size: 0.75rem;
  color: #9CA3AF;
  margin: 0.5rem 0 0;
}
.auth-redirect a { color: #5585FF; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .auth-left { display: none; }
  .auth-right { flex: 1; }
}
</style>

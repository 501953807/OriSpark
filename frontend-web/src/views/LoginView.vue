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
        <h2 class="auth-left-title">欢迎回来</h2>
        <p class="auth-left-desc">登录您的创作者工作台</p>
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
          <div v-if="mode === 'register'" class="form-field">
            <label class="form-label">用户名</label>
            <div class="form-input-wrapper">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
              </svg>
              <input v-model="form.username" class="form-input" placeholder="创作者名称" autocomplete="username" />
            </div>
          </div>

          <div class="form-field">
            <label class="form-label">邮箱</label>
            <div class="form-input-wrapper">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
              </svg>
              <input v-model="form.email" type="email" class="form-input" placeholder="creator@example.com" required autocomplete="email" />
            </div>
          </div>

          <div class="form-field">
            <label class="form-label">密码</label>
            <div class="form-input-wrapper">
              <svg class="form-input-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input v-model="form.password" type="password" class="form-input" placeholder="••••••" required minlength="1" autocomplete="current-password" />
            </div>
          </div>

          <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

          <button type="submit" class="btn-primary" :disabled="loading">
            <span v-if="loading">处理中...</span>
            <span v-else>{{ mode === 'login' ? '登录' : '注册' }}</span>
          </button>
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
const form = ref({ username: '', email: '', password: '' })

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
</script>

<style scoped>
.auth-layout { min-height: 100dvh; display: flex; }

/* ── Left Panel ── */
.auth-left {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, #8C57FF 0%, #6A3FCC 50%, #4A2D99 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  min-height: 100dvh;
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

/* ── Right Panel ── */
.auth-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #FFFFFF;
  padding: 2rem;
}
.auth-right-inner { width: 100%; max-width: 480px; }
.auth-header { margin-bottom: 1.5rem; }
.auth-logo { display: inline-flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
.auth-logo-icon { font-size: 2rem; }
.auth-logo-text {
  font-size: 1.5rem; font-weight: 700;
  background: linear-gradient(135deg, #8C57FF, #6A3FCC);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.auth-welcome { font-size: 1.25rem; font-weight: 600; color: #1F2937; margin: 0 0 0.25rem; }
.auth-desc { font-size: 0.875rem; color: #64748B; margin: 0 0 1.5rem; }

/* ── Tabs ── */
.auth-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 1.5rem;
  background: #F4F5FA;
  border-radius: 8px;
  padding: 4px;
}
.auth-tab {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 600;
  background: transparent;
  color: #9CA3AF;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.auth-tab.active {
  background: #FFFFFF;
  color: #1F2937;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* ── OAuth ── */
.oauth-section { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; }
.oauth-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 10px 16px;
  border: 1.5px solid #E5E7EB;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  background: #FFFFFF;
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.oauth-btn:hover { border-color: #8C57FF; background: rgba(140,87,255,0.04); }

/* ── Divider ── */
.auth-divider {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1.5rem 0;
  color: #9CA3AF;
  font-size: 0.8125rem;
}
.auth-divider::before, .auth-divider::after { content: ''; flex: 1; height: 1px; background: #E5E7EB; }

/* ── Form ── */
.auth-form { display: flex; flex-direction: column; gap: 1.25rem; }
.form-field { display: flex; flex-direction: column; gap: 0.375rem; }
.form-label { font-size: 0.8125rem; font-weight: 500; color: #374151; }
.form-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  border: 1.5px solid #E5E7EB;
  border-radius: 8px;
  transition: all 0.15s;
  background: #FFFFFF;
}
.form-input-wrapper:focus-within { border-color: #8C57FF; box-shadow: 0 0 0 3px rgba(140, 87, 255, 0.1); }
.form-input-icon { position: absolute; left: 12px; color: #9CA3AF; pointer-events: none; }
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
.form-error { color: #EF4444; font-size: 0.8125rem; }

/* ── Primary Button ── */
.btn-primary {
  height: 44px;
  padding: 0 1.5rem;
  background: linear-gradient(135deg, #8C57FF 0%, #7E4EE6 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #7E4EE6 0%, #6A3FCC 100%);
  box-shadow: 0 4px 12px rgba(140, 87, 255, 0.4);
}
.btn-primary:disabled { opacity: 0.7; cursor: not-allowed; }

/* ── Footer ── */
.auth-footer { margin-top: 1.5rem; text-align: center; }
.auth-footer p { font-size: 0.8125rem; color: #9CA3AF; margin: 0.25rem 0; }
.auth-footer a { color: #8C57FF; text-decoration: none; font-weight: 500; }
.auth-footer a:hover { text-decoration: underline; }

/* ── Responsive ── */
@media (max-width: 768px) {
  .auth-left { display: none; }
  .auth-right { flex: 1; }
  .oauth-section { flex-direction: column; }
}
</style>

<template>
  <div class="login-page">
    <div class="login-card" role="main" aria-label="登录页面">
      <div class="login-brand">
        <div class="brand-logo" aria-hidden="true">O</div>
        <h1>OriStudio</h1>
        <p>创作者全链路助手 · 本地运行</p>
      </div>

      <!-- OAuth Buttons -->
      <div class="oauth-section">
        <button class="oauth-btn google" @click="oauthLogin('google')">
          <span class="oauth-icon">G</span>
          <span>使用 Google 登录</span>
        </button>
        <button class="oauth-btn wechat" @click="oauthLogin('wechat')">
          <span class="oauth-icon">💬</span>
          <span>使用微信登录</span>
        </button>
        <button class="oauth-btn douyin" @click="oauthLogin('douyin')">
          <span class="oauth-icon">🎵</span>
          <span>使用抖音登录</span>
        </button>
      </div>

      <!-- Divider -->
      <div class="login-divider">
        <span>或者使用邮箱</span>
      </div>

      <!-- Tabs -->
      <div class="login-tabs" role="tablist" aria-label="登录方式">
        <button role="tab" :aria-selected="mode === 'login'" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button role="tab" :aria-selected="mode === 'register'" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <!-- Error -->
      <div v-if="errorMsg" class="login-error animate-shake">{{ errorMsg }}</div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="login-form" aria-label="登录表单">
        <div v-if="mode === 'register'" class="form-group">
          <label for="reg-username">用户名</label>
          <input id="reg-username" v-model="form.username" class="form-input" placeholder="创作者名称" required autocomplete="username" />
        </div>
        <div class="form-group">
          <label for="login-email">邮箱</label>
          <input id="login-email" v-model="form.email" type="email" class="form-input" placeholder="creator@example.com" required autocomplete="email" />
        </div>
        <div class="form-group">
          <label for="login-password">密码</label>
          <input id="login-password" v-model="form.password" type="password" class="form-input" placeholder="••••••" required minlength="6" autocomplete="current-password" />
        </div>
        <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" :disabled="loading">
          {{ loading ? '处理中...' : mode === 'login' ? '登录' : '注册' }}
        </button>
      </form>

      <!-- Divider -->
      <div class="login-divider">
        <span>或</span>
      </div>

      <!-- Skip button -->
      <router-link to="/app" class="btn btn-ghost" style="justify-content:center;width:100%">
        💡 跳过登录，直接进入（本地模式）
      </router-link>

      <!-- Back to landing -->
      <router-link to="/" class="login-back">← 返回首页</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'

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
      const onboarded = localStorage.getItem('oristudio-onboarded')
      if (!onboarded) {
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
    douyin: '抖音登录需要配置 DOUYIN_CLIENT_KEY 后启用',
  }
  ;(window as any).$toast?.show(messages[provider] || `${provider} OAuth 暂未配置`, 'info')
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: 20px;
}
.login-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 40px;
  max-width: 440px;
  width: 100%;
  box-shadow: 0 16px 64px oklch(0 0 0 / 0.08);
}
.login-brand { text-align: center; margin-bottom: 24px; }
.brand-logo {
  width: 56px; height: 56px;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  display: inline-flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 800; font-size: 1.6rem;
  margin-bottom: 12px;
}
.login-brand h1 { font-family: var(--font-display); font-size: 1.4rem; margin: 0 0 4px; }
.login-brand p { color: var(--muted); font-size: 0.85rem; margin: 0; }

/* OAuth buttons */
.oauth-section { display: flex; flex-direction: column; gap: 8px; margin-bottom: 20px; }
.oauth-btn {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; padding: 10px 16px; border-radius: var(--radius-sm);
  font-size: 0.9rem; font-weight: 600; font-family: var(--font-body);
  cursor: pointer; border: 1px solid var(--border); background: var(--surface);
  color: var(--fg); transition: all 0.2s;
}
.oauth-btn:hover { background: oklch(96% 0.004 240); }
.oauth-btn.google:hover { border-color: #4285f4; background: oklch(56% 0.12 260 / 0.05); }
.oauth-btn.wechat:hover { border-color: #07c160; background: oklch(56% 0.12 160 / 0.05); }
.oauth-btn.douyin:hover { border-color: #fe2c55; background: oklch(56% 0.18 10 / 0.05); }
.oauth-icon {
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.85rem;
}

.login-tabs {
  display: flex; gap: 4px; margin-bottom: 20px;
  background: oklch(96% 0.004 240); border-radius: var(--radius); padding: 4px;
}
.login-tabs button {
  flex: 1; padding: 8px; border: none; border-radius: var(--radius-sm);
  font-size: 0.88rem; font-weight: 600; background: transparent;
  color: var(--muted); font-family: var(--font-body); cursor: pointer;
  transition: all 0.2s;
}
.login-tabs button.active {
  background: var(--surface); color: var(--fg);
  box-shadow: 0 1px 3px oklch(0 0 0 / 0.06);
}
.login-form { display: flex; flex-direction: column; gap: 14px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.9rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none;
}
.form-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1); }
.login-error {
  padding: 10px 14px; background: oklch(58% 0.18 30 / 0.08); border-radius: var(--radius-sm);
  color: #e53e3e; font-size: 0.85rem; font-weight: 600; margin-bottom: 8px;
}
.login-divider {
  display: flex; align-items: center; gap: 12px;
  margin: 20px 0; color: var(--muted); font-size: 0.82rem;
}
.login-divider::before, .login-divider::after {
  content: ''; flex: 1; height: 1px; background: var(--border);
}
.login-back {
  display: block; text-align: center; margin-top: 16px;
  font-size: 0.85rem; color: var(--muted); text-decoration: none;
}
.login-back:hover { color: var(--fg); }
</style>

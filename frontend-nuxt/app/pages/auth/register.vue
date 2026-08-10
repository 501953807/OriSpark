<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '~/stores/auth'

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
    const data = resp.data as { token: string; user: any }
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
  <div class="register-page">
    <div class="register-card">
      <div class="register-header">
        <NuxtLink to="/" class="logo">
          <span class="logo-icon">⚡</span>
          <span class="logo-text">OriSpark</span>
        </NuxtLink>
        <p class="register-subtitle">注册运营者账号</p>
      </div>
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input id="username" v-model="username" type="text" placeholder="您的用户名" required />
        </div>
        <div class="form-group">
          <label for="email">邮箱</label>
          <input id="email" v-model="email" type="email" placeholder="your@email.com" required />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input id="password" v-model="password" type="password" placeholder="至少6位" required minlength="6" />
        </div>
        <div class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input id="confirmPassword" v-model="confirmPassword" type="password" placeholder="再次输入密码" required />
        </div>
        <div class="form-group">
          <label>身份角色（可多选）</label>
          <div class="role-grid">
            <label v-for="role in roles" :key="role.key" class="role-item">
              <input type="checkbox" :value="role.key" v-model="participantRoles" />
              <span class="role-label">{{ role.label }}</span>
              <span class="role-desc">{{ role.desc }}</span>
            </label>
          </div>
        </div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
        <button type="submit" class="btn-register" :disabled="submitting">
          {{ submitting ? '注册中...' : '注册' }}
        </button>
      </form>
      <div class="register-footer">
        <p>已有账号？<NuxtLink to="/auth/login" class="link">立即登录</NuxtLink></p>
        <p class="hint">创作者请前往 <a href="http://localhost:5174" target="_blank">OriStudio</a> 注册</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 24px;
}
.register-card {
  width: 100%;
  max-width: 480px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  padding: 40px 32px;
}
.register-header {
  text-align: center;
  margin-bottom: 32px;
}
.logo {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  margin-bottom: 12px;
}
.logo-icon { font-size: 28px; }
.logo-text { font-size: 24px; font-weight: 700; color: #1e293b; }
.register-subtitle { font-size: 14px; color: #64748b; margin: 0; }
.register-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}
.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="password"] {
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.15s;
}
.form-group input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
}
.role-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}
.role-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.role-item:hover { border-color: #3b82f6; background: #f8fafc; }
.role-item input[type="checkbox"] { margin-top: 3px; }
.role-label { font-size: 13px; font-weight: 600; color: #1e293b; display: block; }
.role-desc { font-size: 11px; color: #94a3b8; }
.error-msg { color: #ef4444; font-size: 13px; margin: 0; }
.btn-register {
  padding: 12px;
  background: #1e293b;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-register:hover:not(:disabled) { background: #334155; }
.btn-register:disabled { opacity: 0.6; cursor: not-allowed; }
.register-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;
  color: #64748b;
}
.register-footer .link { color: #3b82f6; text-decoration: none; }
.register-footer a { color: #3b82f6; text-decoration: none; }
.register-footer .hint { margin-top: 8px; font-size: 12px; color: #94a3b8; }
</style>

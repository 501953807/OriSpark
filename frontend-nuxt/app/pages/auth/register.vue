<!-- OriSpark Register Page — Materio Demo-5 Style
     Left: Illustration + OriSpark intro | Right: White form panel -->
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
const showPassword = ref(false)
const agreeTerms = ref(false)

const roles = [
  { key: 'operator',     label: '运营方',   icon: 'business_center', desc: '作品包装、授权管理、分润体系' },
  { key: 'trader',       label: '采购方',   icon: 'shopping_cart',   desc: '合约认购、批量采购、供应链对接' },
  { key: 'legal_rep',    label: '法务代表', icon: 'gavel',           desc: '合同审核、版权保护、争议处理' },
  { key: 'tax_agent',    label: '税务代理', icon: 'calculate',       desc: '税费计算、合规申报、跨境税务' },
  { key: 'logistics',    label: '物流方',   icon: 'local_shipping',  desc: '发货跟踪、签收确认、仓储管理' },
  { key: 'insurer',      label: '保险方',   icon: 'security',        desc: '版权保险、履约担保、风险承保' },
  { key: 'payment_provider', label: '支付托管方', icon: 'account_balance_wallet', desc: '资金托管、结算分润、支付担保' },
  { key: 'platform',     label: '平台方',   icon: 'dashboard',       desc: '运营管理、数据监控、生态治理' },
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
  if (!agreeTerms.value) {
    errorMsg.value = '请同意隐私政策与服务条款'
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
          <div class="auth-float__icon">🤝</div>
          <div class="auth-float__text">合作</div>
          <div class="auth-float__value">8+角色</div>
        </div>
        <div class="auth-float auth-float--2">
          <div class="auth-float__icon">🔗</div>
          <div class="auth-float__text">存证</div>
          <div class="auth-float__value">C2PA</div>
        </div>
        <div class="auth-float auth-float--3">
          <div class="auth-float__icon">🌍</div>
          <div class="auth-float__text">分润</div>
          <div class="auth-float__value">全球</div>
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

        <!-- 3D character illustration (different pose from login) -->
        <div class="auth-left__illustration">
          <svg viewBox="0 0 300 300" class="auth-left__svg" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- Platform -->
            <ellipse cx="150" cy="265" rx="90" ry="16" fill="rgba(255,255,255,0.08)"/>
            <!-- Body - slightly different pose -->
            <rect x="120" y="140" width="60" height="90" rx="14" fill="url(#bodyGrad2)"/>
            <!-- Head -->
            <circle cx="150" cy="100" r="40" fill="rgba(255,255,255,0.9)"/>
            <!-- Hair (different style) -->
            <ellipse cx="150" cy="76" rx="36" ry="22" fill="#F59E0B"/>
            <ellipse cx="140" cy="82" rx="20" ry="14" fill="#FCD34D"/>
            <!-- Eyes (excited) -->
            <circle cx="138" cy="96" r="4" fill="#1F2937"/>
            <circle cx="162" cy="96" r="4" fill="#1F2937"/>
            <circle cx="139" cy="95" r="1.5" fill="white"/>
            <circle cx="163" cy="95" r="1.5" fill="white"/>
            <!-- Big smile -->
            <path d="M138 110 Q150 122 162 110" stroke="#1F2937" stroke-width="2.5" fill="none" stroke-linecap="round"/>
            <!-- Arms raised -->
            <rect x="78" y="150" width="32" height="13" rx="6.5" fill="rgba(255,255,255,0.85)" transform="rotate(-30 94 156)"/>
            <rect x="190" y="150" width="32" height="13" rx="6.5" fill="rgba(255,255,255,0.85)" transform="rotate(30 206 156)"/>
            <!-- Rocket in hand -->
            <g transform="translate(200, 110) rotate(30)">
              <rect x="-8" y="-20" width="16" height="36" rx="8" fill="#EF4444"/>
              <polygon points="-8,-20 0,-32 8,-20" fill="#FCA5A5"/>
              <rect x="-4" y="-8" width="8" height="6" rx="2" fill="#FCA5A5"/>
              <polygon points="-6,16 0,26 6,16" fill="#FCA5A5"/>
            </g>
            <!-- Legs -->
            <rect x="128" y="225" width="16" height="38" rx="8" fill="rgba(255,255,255,0.7)"/>
            <rect x="156" y="225" width="16" height="38" rx="8" fill="rgba(255,255,255,0.7)"/>
            <!-- Shoes -->
            <ellipse cx="136" cy="266" rx="13" ry="6" fill="#7C3AED"/>
            <ellipse cx="164" cy="266" rx="13" ry="6" fill="#7C3AED"/>
            <!-- Stars decoration -->
            <text x="60" y="80" font-size="20" opacity="0.6">⭐</text>
            <text x="220" y="70" font-size="16" opacity="0.5">✨</text>
            <text x="80" y="200" font-size="14" opacity="0.4">💫</text>
            <text x="230" y="190" font-size="18" opacity="0.5">🚀</text>
            <defs>
              <linearGradient id="bodyGrad2" x1="120" y1="140" x2="180" y2="230">
                <stop offset="0%" stop-color="rgba(124,58,237,0.4)"/>
                <stop offset="100%" stop-color="rgba(59,130,246,0.25)"/>
              </linearGradient>
            </defs>
          </svg>
        </div>

        <!-- Text content -->
        <h1 class="auth-left__title">加入 OriSpark 🚀</h1>
        <p class="auth-left__desc">成为创作者生态的合作伙伴，开启您的交易之旅</p>

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
         RIGHT PANEL — Register Form
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
          <h2 class="auth-right__heading">Adventure starts here 🚀</h2>
          <p class="auth-right__subheading">创建您的账户，开始探索创作者经济</p>
        </div>

        <!-- Register form -->
        <form @submit.prevent="handleRegister" class="auth-form">
          <!-- Username -->
          <div class="form-group">
            <label class="form-label" for="username">用户名</label>
            <div class="form-input">
              <i class="material-icons form-input__icon">person</i>
              <input
                id="username"
                v-model="username"
                type="text"
                class="form-input__field"
                placeholder="创作者名称"
                required
              />
            </div>
          </div>

          <!-- Email -->
          <div class="form-group">
            <label class="form-label" for="reg-email">邮箱</label>
            <div class="form-input">
              <i class="material-icons form-input__icon">mail</i>
              <input
                id="reg-email"
                v-model="email"
                type="email"
                class="form-input__field"
                placeholder="your@email.com"
                required
              />
            </div>
          </div>

          <!-- Password -->
          <div class="form-group">
            <label class="form-label" for="reg-password">密码</label>
            <div class="form-input">
              <i class="material-icons form-input__icon">lock</i>
              <input
                id="reg-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input__field"
                placeholder="至少6位"
                required
                minlength="6"
              />
              <button type="button" class="form-input__toggle" @click="showPassword = !showPassword" aria-label="显示密码">
                <i class="material-icons">{{ showPassword ? 'visibility_off' : 'visibility' }}</i>
              </button>
            </div>
          </div>

          <!-- Confirm Password -->
          <div class="form-group">
            <label class="form-label" for="confirm-password">确认密码</label>
            <div class="form-input" :class="{ 'form-input--error': errorMsg && errorMsg.includes('密码') }">
              <i class="material-icons form-input__icon">lock_outline</i>
              <input
                id="confirm-password"
                v-model="confirmPassword"
                :type="showPassword ? 'text' : 'password'"
                class="form-input__field"
                placeholder="再次输入密码"
                required
              />
              <button type="button" class="form-input__toggle" @click="showPassword = !showPassword" aria-label="显示密码">
                <i class="material-icons">{{ showPassword ? 'visibility_off' : 'visibility' }}</i>
              </button>
            </div>
          </div>

          <!-- Role Selection -->
          <div class="form-group">
            <label class="form-label">
              身份角色
              <span class="form-required">*</span>
            </label>
            <div class="role-grid">
              <label v-for="role in roles" :key="role.key" class="role-item">
                <input type="checkbox" :value="role.key" v-model="participantRoles" />
                <div class="role-item__icon-wrap">
                  <i class="material-icons role-item__icon">{{ role.icon }}</i>
                </div>
                <div class="role-item__body">
                  <div class="role-item__name">{{ role.label }}</div>
                  <div class="role-item__desc">{{ role.desc }}</div>
                </div>
              </label>
            </div>
          </div>

          <!-- Terms -->
          <label class="form-checkbox-inline">
            <input v-model="agreeTerms" type="checkbox" />
            <span class="form-checkbox__box" />
            <span>我同意 <a href="#" class="form-checkbox__link" @click.prevent>隐私政策与服务条款</a></span>
          </label>

          <!-- Error -->
          <div v-if="errorMsg" class="form-error">{{ errorMsg }}</div>

          <!-- Submit -->
          <button type="submit" class="btn-submit" :disabled="submitting">
            <svg v-if="submitting" class="btn-submit__spinner" viewBox="0 0 24 24" width="18" height="18">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2.5" stroke-dasharray="31.4 31.4" stroke-linecap="round"/>
            </svg>
            {{ submitting ? '注册中...' : '注册' }}
          </button>
        </form>

        <!-- Login link -->
        <p class="auth-footer-text">
          已有账号？<NuxtLink to="/auth/login" class="auth-footer-link">立即登录</NuxtLink>
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
   LEFT PANEL (same as login)
   ═══════════════════════════════════════════════════════════ */
.auth-left {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  min-height: 100dvh;
  background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 30%, #C4B5FD 60%, #A78BFA 100%);
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
.auth-left__illustration { margin-bottom: 2rem; }
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
.auth-left__plant {
  position: absolute;
  bottom: 0;
  opacity: 0.6;
}
.auth-left__plant--1 { left: 5%; }
.auth-left__plant--2 { right: 8%; }

/* ═══════════════════════════════════════════════════════════
   RIGHT PANEL (same structure as login)
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
  max-width: 440px;
}
.auth-right__logo {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  margin-bottom: 2rem;
  color: #1F2937;
}
.auth-right__logo-icon { color: #7C3AED; }
.auth-right__logo-text {
  font-size: 1.375rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #7C3AED, #3B82F6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
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
  gap: 1.125rem;
}
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: #374151;
}
.form-required { color: #EF4444; }
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
  border-color: #7C3AED;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12);
  background: #FFFFFF;
}
.form-input--error { border-color: #EF4444; }
.form-input--error:focus-within { box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.12); }
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
.form-error { color: #EF4444; font-size: 0.8125rem; margin: 0; }

/* Role Grid */
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
  border: 1.5px solid #E5E7EB;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  position: relative;
}
.role-item:hover {
  border-color: #7C3AED;
  background: rgba(124, 58, 237, 0.04);
}
.role-item input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.role-item:has(input:checked) {
  border-color: #7C3AED;
  background: rgba(124, 58, 237, 0.08);
}
.role-item__icon-wrap {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  background: rgba(124, 58, 237, 0.10);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.role-item:has(input:checked) .role-item__icon-wrap { background: rgba(124, 58, 237, 0.18); }
.role-item__icon { font-size: 18px; color: #7C3AED; }
.role-item__body { flex: 1; min-width: 0; }
.role-item__name { font-size: 0.8125rem; font-weight: 600; color: #1F2937; }
.role-item__desc { font-size: 0.6875rem; color: #9CA3AF; margin-top: 2px; }

/* Checkbox inline (terms) */
.form-checkbox-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 0.8125rem;
  color: #4B5563;
  user-select: none;
}
.form-checkbox-inline input { display: none; }
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
.form-checkbox-inline input:checked + .form-checkbox__box {
  background: #7C3AED;
  border-color: #7C3AED;
}
.form-checkbox-inline input:checked + .form-checkbox__box::after {
  content: '✓';
  color: white;
  font-size: 12px;
  font-weight: 700;
}
.form-checkbox__link {
  color: #7C3AED;
  text-decoration: none;
  font-weight: 500;
}
.form-checkbox__link:hover { text-decoration: underline; }

/* Submit button */
.btn-submit {
  width: 100%;
  height: 48px;
  background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%);
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
  background: linear-gradient(135deg, #6D28D9 0%, #5B21B6 100%);
  box-shadow: 0 6px 20px rgba(124, 58, 237, 0.35);
  transform: translateY(-1px);
}
.btn-submit:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
.btn-submit__spinner { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Footer text */
.auth-footer-text {
  text-align: center;
  font-size: 0.875rem;
  color: #6B728B;
  margin: 1.5rem 0 0;
}
.auth-footer-link {
  color: #7C3AED;
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
.oauth-group { display: flex; gap: 12px; }
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
  color: #374151;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}
.btn-oauth:hover {
  border-color: #7C3AED;
  background: rgba(124, 58, 237, 0.04);
  color: #7C3AED;
}
.oauth-icon { font-size: 18px; }

/* Redirect */
.auth-redirect-text {
  text-align: center;
  font-size: 0.75rem;
  color: #9CA3AF;
  margin: 1rem 0 0;
}
.auth-redirect-text a { color: #7C3AED; text-decoration: none; }
.auth-redirect-text a:hover { text-decoration: underline; }

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 900px) {
  .auth-left { display: none; }
  .auth-right { flex: 1; }
}
@media (max-width: 640px) {
  .role-grid { grid-template-columns: 1fr; }
}
</style>

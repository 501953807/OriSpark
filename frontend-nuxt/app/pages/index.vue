<!-- Hero / Landing Page for OriSpark — No navigation, pure marketing page -->
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const stats = ref({ totalWorks: 0, totalContracts: 0, activeCreators: 0, avgSplit: 0 })
const targetStats = ref({ totalWorks: 0, totalContracts: 0, activeCreators: 0, avgSplit: 0 })
const displayStats = ref({ totalWorks: 0, totalContracts: 0, activeCreators: 0, avgSplit: 0 })
const featuredWorks = ref<any[]>([])
const featuredContracts = ref<any[]>([])
let rollingTimer: ReturnType<typeof requestAnimationFrame> | null = null

const roles = [
  { key: 'operator',    label: '运营方',     icon: 'business_center', desc: '作品包装、授权管理、分润体系' },
  { key: 'trader',      label: '采购方',     icon: 'shopping_cart',    desc: '合约认购、批量采购、供应链对接' },
  { key: 'legal_rep',   label: '法务代表',   icon: 'gavel',            desc: '合同审核、版权保护、争议处理' },
  { key: 'tax_agent',   label: '税务代理',   icon: 'calculate',        desc: '税费计算、合规申报、跨境税务' },
  { key: 'logistics',   label: '物流方',     icon: 'local_shipping',   desc: '发货跟踪、签收确认、仓储管理' },
  { key: 'insurer',     label: '保险方',     icon: 'security',         desc: '版权保险、履约担保、风险承保' },
  { key: 'payment_provider', label: '支付托管方', icon: 'account_balance_wallet', desc: '资金托管、结算分润、支付担保' },
  { key: 'platform',    label: '平台方',     icon: 'dashboard',        desc: '运营管理、数据监控、生态治理' },
]

function animateNumber(target: number, duration: number = 1200): number {
  if (target === 0) return 0
  const start = performance.now()
  const step = (now: number) => {
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
    displayStats.value.totalWorks     = Math.round(eased * targetStats.value.totalWorks)
    displayStats.value.totalContracts = Math.round(eased * targetStats.value.totalContracts)
    displayStats.value.activeCreators = Math.round(eased * targetStats.value.activeCreators)
    displayStats.value.avgSplit       = Math.round(eased * targetStats.value.avgSplit)
    if (progress < 1) rollingTimer = requestAnimationFrame(step)
  }
  rollingTimer = requestAnimationFrame(step)
  return 0
}

function stopRolling() { if (rollingTimer) { cancelAnimationFrame(rollingTimer); rollingTimer = null } }

onMounted(async () => {
  try {
    const apiBase = useRuntimeConfig().public.apiBase
    const [statsRes, worksRes, contractsRes] = await Promise.allSettled([
      $fetch(`${apiBase}/public/dashboard-stats`),
      $fetch(`${apiBase}/public/works?featured=true&limit=6`),
      $fetch(`${apiBase}/public/contracts?recent=true&limit=5`),
    ])
    if (statsRes.status === 'fulfilled') {
      const raw = {
        totalWorks: statsRes.value?.total_works || 0,
        totalContracts: statsRes.value?.total_contracts || 0,
        activeCreators: statsRes.value?.active_creators || 0,
        avgSplit: statsRes.value?.avg_split_rate || 0,
      }
      targetStats.value = raw
      animateNumber(raw.totalWorks)
    }
    if (worksRes.status === 'fulfilled' && Array.isArray(worksRes.value)) {
      featuredWorks.value = worksRes.value.slice(0, 6)
    }
    if (contractsRes.status === 'fulfilled' && Array.isArray(contractsRes.value)) {
      featuredContracts.value = contractsRes.value.slice(0, 5)
    }
  } catch { /* API not available in dev */ }
})

onUnmounted(() => stopRolling())
</script>

<template>
  <div class="landing">
    <!-- ═══════════════════════════════════════════════════════════
         TOP BAR — minimal, no nav menu
         ═══════════════════════════════════════════════════════════ -->
    <header class="landing-header">
      <div class="landing-header__inner">
        <NuxtLink to="/" class="landing-header__brand">
          <svg class="landing-header__logo" width="28" height="22" viewBox="0 0 30 24" fill="none">
            <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
            <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
            <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
            <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
          </svg>
          <span class="landing-header__name">OriSpark</span>
        </NuxtLink>
        <div class="landing-header__actions">
          <NuxtLink to="/auth/login" class="landing-header__btn landing-header__btn--ghost">登录</NuxtLink>
          <NuxtLink to="/auth/register" class="landing-header__btn landing-header__btn--primary">进入 OriSpark</NuxtLink>
        </div>
      </div>
    </header>

    <!-- ═══════════════════════════════════════════════════════════
         HERO SECTION
         ═══════════════════════════════════════════════════════════ -->
    <section class="hero">
      <div class="hero__bg">
        <div class="hero__bg-orb hero__bg-orb--1" />
        <div class="hero__bg-orb hero__bg-orb--2" />
        <div class="hero__bg-orb hero__bg-orb--3" />
      </div>
      <div class="hero__inner">
        <div class="hero__content">
          <div class="hero__badge">🚀 AI 时代的创作者信任基础设施</div>
          <h1 class="hero__title">
            作品存证 · 合约交易<br />
            <span class="hero__title-accent">全球分润</span>
          </h1>
          <p class="hero__desc">
            OriSpark 为创作者与 8 种市场交易角色提供可信赖的数字化交易枢纽，
            让每一笔作品授权、每一份合约交易、每一次全球分润都安全、透明、可追溯。
          </p>
          <div class="hero__actions">
            <NuxtLink to="/auth/register" class="btn btn--lg btn--primary">
              免费开始
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </NuxtLink>
            <NuxtLink to="/gallery" class="btn btn--lg btn--outline">浏览作品画廊</NuxtLink>
          </div>
          <div class="hero__trust">
            <div class="hero__trust-item">
              <span class="hero__trust-num">{{ displayStats.totalWorks.toLocaleString() }}+</span>
              <span class="hero__trust-label">作品存证</span>
            </div>
            <div class="hero__trust-divider" />
            <div class="hero__trust-item">
              <span class="hero__trust-num">{{ displayStats.totalContracts.toLocaleString() }}+</span>
              <span class="hero__trust-label">活跃合约</span>
            </div>
            <div class="hero__trust-divider" />
            <div class="hero__trust-item">
              <span class="hero__trust-num">{{ displayStats.activeCreators.toLocaleString() }}+</span>
              <span class="hero__trust-label">创作者</span>
            </div>
            <div class="hero__trust-divider" />
            <div class="hero__trust-item">
              <span class="hero__trust-num">99.9%</span>
              <span class="hero__trust-label">可信度</span>
            </div>
          </div>
        </div>
        <div class="hero__visual">
          <!-- Abstract illustration: floating cards with charts -->
          <div class="hero-visual">
            <div class="hv-card hv-card--1">
              <div class="hv-card__icon">📊</div>
              <div class="hv-card__label">合约增长</div>
              <div class="hv-card__value">+48.5%</div>
              <div class="hv-card__sparkline">
                <svg viewBox="0 0 80 30" preserveAspectRatio="none">
                  <polyline points="0,25 15,20 30,22 45,12 60,15 80,5" fill="none" stroke="rgb(85,133,255)" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
            </div>
            <div class="hv-card hv-card--2">
              <div class="hv-card__icon">💰</div>
              <div class="hv-card__label">总交易额</div>
              <div class="hv-card__value">¥21,845</div>
              <div class="hv-card__badge hv-card__badge--up">↑ 15.6%</div>
            </div>
            <div class="hv-card hv-card--3">
              <div class="hv-card__icon">🔗</div>
              <div class="hv-card__label">作品存证</div>
              <div class="hv-card__value">50k+</div>
              <div class="hv-card__mini">区块链锚定</div>
            </div>
            <div class="hv-card hv-card--4">
              <div class="hv-card__icon">🌍</div>
              <div class="hv-card__label">全球分润</div>
              <div class="hv-card__value">{{ displayStats.avgSplit }}%</div>
              <div class="hv-card__mini">实时结算</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         8 ROLES
         ═══════════════════════════════════════════════════════════ -->
    <section class="roles-section">
      <div class="container">
        <div class="section-header">
          <span class="section-label">参与角色</span>
          <h2 class="section-title">8 种市场交易角色，一站式协作</h2>
          <p class="section-desc">从创作者到运营方，从法务到物流，OriSpark 连接产业链全链路</p>
        </div>
        <div class="roles-grid">
          <div v-for="role in roles" :key="role.key" class="role-card">
            <div class="role-card__icon-wrap">
              <i class="material-icons role-card__icon">{{ role.icon }}</i>
            </div>
            <div class="role-card__body">
              <h3 class="role-card__name">{{ role.label }}</h3>
              <p class="role-card__desc">{{ role.desc }}</p>
            </div>
            <NuxtLink to="/auth/register" class="role-card__arrow">
              <i class="material-icons">arrow_forward</i>
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         FEATURED WORKS
         ═══════════════════════════════════════════════════════════ -->
    <section class="works-section">
      <div class="container">
        <div class="section-header section-header--light">
          <span class="section-label">精选作品</span>
          <h2 class="section-title">高质量作品，可信存证</h2>
          <NuxtLink to="/gallery" class="view-all">查看全部 →</NuxtLink>
        </div>
        <div v-if="featuredWorks.length" class="works-grid">
          <div v-for="work in featuredWorks" :key="work.id" class="work-card">
            <div class="work-card__thumb" :style="{ backgroundImage: `url(${work.thumbnail || work.thumbnail_path || ''})` }">
              <div class="work-card__thumb-placeholder">
                <i class="material-icons">image</i>
              </div>
              <div class="work-card__certified">
                <i class="material-icons">verified</i> C2PA 存证
              </div>
            </div>
            <div class="work-card__info">
              <h3 class="work-card__title">{{ work.title }}</h3>
              <p class="work-card__creator">{{ work.creator_name || '匿名创作者' }}</p>
            </div>
          </div>
        </div>
        <div v-else class="works-empty">
          <div class="works-empty__icon">🎨</div>
          <p>更多作品即将上线</p>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         RECENT CONTRACTS
         ═══════════════════════════════════════════════════════════ -->
    <section class="contracts-section">
      <div class="container">
        <div class="section-header">
          <span class="section-label">最新合约</span>
          <h2 class="section-title">实时交易动态</h2>
          <NuxtLink to="/contracts" class="view-all">查看全部 →</NuxtLink>
        </div>
        <div v-if="featuredContracts.length" class="contracts-list">
          <div v-for="contract in featuredContracts" :key="contract.id" class="contract-row">
            <div class="contract-row__left">
              <div class="contract-row__icon">
                <i class="material-icons">handshake</i>
              </div>
              <div>
                <div class="contract-row__title">{{ contract.title }}</div>
                <div class="contract-row__type">{{ contract.contract_type || '标准合约' }}</div>
              </div>
            </div>
            <div class="contract-row__meta">
              <span class="contract-row__amount">¥{{ contract.total_amount?.toLocaleString() || '0' }}</span>
              <span class="contract-status" :class="contract.status">{{ contract.status_label || contract.status }}</span>
            </div>
          </div>
        </div>
        <div v-else class="contracts-empty">
          <div class="contracts-empty__icon">📋</div>
          <p>更多合约即将上线</p>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         CORE CAPABILITIES
         ═══════════════════════════════════════════════════════════ -->
    <section class="capabilities-section">
      <div class="container">
        <div class="section-header section-header--light">
          <span class="section-label">核心能力</span>
          <h2 class="section-title">为什么选择 OriSpark</h2>
          <p class="section-desc">四大核心能力，构建创作者经济信任基础设施</p>
        </div>
        <div class="capabilities-grid">
          <div class="cap-card">
            <div class="cap-card__icon">🛡️</div>
            <h3 class="cap-card__title">权益保护</h3>
            <p class="cap-card__desc">C2PA 数字存证 · 区块链锚定 · 全网侵权监测</p>
          </div>
          <div class="cap-card">
            <div class="cap-card__icon">📝</div>
            <h3 class="cap-card__title">合约交易</h3>
            <p class="cap-card__desc">挂牌认购 · 第三方支付托管 · 市场化分润机制</p>
          </div>
          <div class="cap-card">
            <div class="cap-card__icon">🤝</div>
            <h3 class="cap-card__title">运营合作</h3>
            <p class="cap-card__desc">包装授权 · 工厂对接 POD · 全球分销网络</p>
          </div>
          <div class="cap-card">
            <div class="cap-card__icon">📊</div>
            <h3 class="cap-card__title">数据洞察</h3>
            <p class="cap-card__desc">创作者排行 · 品类趋势 · 行业白皮书</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         FINAL CTA
         ═══════════════════════════════════════════════════════════ -->
    <section class="cta-section">
      <div class="container">
        <div class="cta-section__inner">
          <h2 class="cta-section__title">开启您的 OriSpark 之旅</h2>
          <p class="cta-section__desc">注册账号，加入创作者经济的新生态</p>
          <div class="cta-section__actions">
            <NuxtLink to="/auth/register" class="btn btn--lg btn--primary btn--lg">
              免费注册
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
            </NuxtLink>
            <a href="http://localhost:5174" target="_blank" class="btn btn--lg btn--outline">
              创作者入口 →
            </a>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════
         FOOTER
         ═══════════════════════════════════════════════════════════ -->
    <footer class="landing-footer">
      <div class="container">
        <div class="landing-footer__inner">
          <div class="landing-footer__brand">
            <svg class="landing-footer__logo" width="24" height="19" viewBox="0 0 30 24" fill="none">
              <path d="M1.476 0.435L6.799 3.722C7.084 3.898 7.258 4.21 7.258 4.546V19.56C7.258 19.901 7.079 20.216 6.787 20.391L1.465 23.578C1.006 23.852 0.412 23.703 0.137 23.244C0.047 23.094 0 22.922 0 22.747V1.259C0 0.724 0.433 0.291 0.968 0.291C1.147 0.291 1.323 0.341 1.476 0.435Z" fill="currentColor"/>
              <path d="M28.525 0.432L23.203 3.707C22.916 3.883 22.742 4.196 22.742 4.532V19.56C22.742 19.901 22.921 20.216 23.213 20.391L28.535 23.578C28.994 23.852 29.588 23.703 29.863 23.244C29.952 23.094 30 22.922 30 22.747V1.256C30 0.722 29.567 0.288 29.032 0.288C28.853 0.288 28.678 0.338 28.525 0.432Z" fill="currentColor"/>
              <path d="M1.473 0.427L15 8.722V16.709L0 8.114V1.253C0 0.718 0.433 0.285 0.968 0.285C1.146 0.285 1.321 0.334 1.473 0.427Z" fill="currentColor"/>
              <path d="M28.527 0.427L15 8.722V16.709L30 8.114V1.253C30 0.718 29.567 0.285 29.032 0.285C28.854 0.285 28.679 0.334 28.527 0.427Z" fill="currentColor"/>
            </svg>
            <span>OriSpark</span>
          </div>
          <p class="landing-footer__copy">© 2026 OriSpark — AI Creator Trust Hub</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════
   CSS VARIABLES (Materio-inspired)
   ═══════════════════════════════════════════════════════════ */
:global(:root) {
  --m-primary: #5585FF;
  --m-primary-dark: #3D6DD6;
  --m-on-primary: #FFFFFF;
  --m-surface: #FFFFFF;
  --m-bg: #F4F5FA;
  --m-bg-elevated: #FFFFFF;
  --m-on-surface: #1F2937;
  --m-on-surface-muted: #64748B;
  --m-grey-100: #F4F5FA;
  --m-grey-200: #E5E7EB;
  --m-grey-300: #D1D5DB;
  --m-grey-500: #6B7280;
  --m-grey-600: #4B5563;
  --m-border: rgba(46, 38, 61, 0.10);
  --m-radius-sm: 8px;
  --m-radius-md: 12px;
  --m-radius-lg: 16px;
  --m-radius-xl: 24px;
  --m-font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --m-shadow-sm: 0 1px 3px rgba(46,38,61,0.08), 0 1px 2px rgba(46,38,61,0.06);
  --m-shadow-md: 0 4px 12px rgba(46,38,61,0.10), 0 2px 4px rgba(46,38,61,0.06);
  --m-shadow-lg: 0 12px 32px rgba(46,38,61,0.12), 0 4px 8px rgba(46,38,61,0.06);
}

/* ═══════════════════════════════════════════════════════════
   LAYOUT
   ═══════════════════════════════════════════════════════════ */
.landing {
  min-height: 100dvh;
  background: var(--m-bg);
  font-family: var(--m-font);
  color: var(--m-on-surface);
}
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ═══════════════════════════════════════════════════════════
   HEADER
   ═══════════════════════════════════════════════════════════ */
.landing-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--m-border);
}
.landing-header__inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.landing-header__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--m-on-surface);
}
.landing-header__logo {
  color: var(--m-primary);
}
.landing-header__name {
  font-size: 1.125rem;
  font-weight: 700;
  background: linear-gradient(135deg, #5585FF, #2A52B0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.landing-header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.landing-header__btn {
  height: 36px;
  padding: 0 16px;
  border-radius: var(--m-radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
}
.landing-header__btn--ghost {
  color: var(--m-grey-600);
}
.landing-header__btn--ghost:hover { background: var(--m-grey-100); }
.landing-header__btn--primary {
  background: var(--m-primary);
  color: white;
}
.landing-header__btn--primary:hover {
  background: var(--m-primary-dark);
  box-shadow: 0 4px 12px rgba(85, 133, 255, 0.35);
}

/* ═══════════════════════════════════════════════════════════
   HERO
   ═══════════════════════════════════════════════════════════ */
.hero {
  position: relative;
  padding: 80px 0 100px;
  overflow: hidden;
  background: linear-gradient(180deg, #FFFFFF 0%, var(--m-bg) 100%);
}
.hero__bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.hero__bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}
.hero__bg-orb--1 {
  width: 500px; height: 500px;
  top: -150px; right: -100px;
  background: radial-gradient(circle, rgba(85,133,255,0.25) 0%, transparent 70%);
}
.hero__bg-orb--2 {
  width: 400px; height: 400px;
  bottom: -100px; left: -100px;
  background: radial-gradient(circle, rgba(140,87,255,0.15) 0%, transparent 70%);
}
.hero__bg-orb--3 {
  width: 300px; height: 300px;
  top: 50%; left: 40%;
  background: radial-gradient(circle, rgba(86,202,0,0.10) 0%, transparent 70%);
}
.hero__inner {
  position: relative;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  gap: 64px;
}
.hero__content { flex: 1; max-width: 560px; }
.hero__badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(85, 133, 255, 0.08);
  border: 1px solid rgba(85, 133, 255, 0.20);
  border-radius: 100px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--m-primary);
  margin-bottom: 24px;
}
.hero__title {
  font-size: clamp(2rem, 4vw, 3.25rem);
  font-weight: 800;
  line-height: 1.15;
  color: var(--m-on-surface);
  margin: 0 0 20px;
  letter-spacing: -0.02em;
}
.hero__title-accent {
  background: linear-gradient(135deg, #5585FF, #8B5CF6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero__desc {
  font-size: 1.0625rem;
  line-height: 1.7;
  color: var(--m-on-surface-muted);
  margin: 0 0 36px;
  max-width: 480px;
}
.hero__actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 48px;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: var(--m-radius-sm);
  font-size: 0.9375rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
}
.btn--lg { padding: 14px 28px; font-size: 1rem; }
.btn--primary {
  background: var(--m-primary);
  color: white;
  box-shadow: 0 2px 8px rgba(85,133,255,0.25);
}
.btn--primary:hover {
  background: var(--m-primary-dark);
  box-shadow: 0 6px 20px rgba(85,133,255,0.35);
  transform: translateY(-1px);
}
.btn--outline {
  background: white;
  color: var(--m-on-surface);
  border: 1.5px solid var(--m-grey-200);
}
.btn--outline:hover {
  border-color: var(--m-primary);
  color: var(--m-primary);
  background: rgba(85,133,255,0.04);
}

/* Trust row */
.hero__trust {
  display: flex;
  align-items: center;
  gap: 24px;
}
.hero__trust-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.hero__trust-num {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--m-on-surface);
}
.hero__trust-label {
  font-size: 0.75rem;
  color: var(--m-on-surface-muted);
}
.hero__trust-divider {
  width: 1px;
  height: 32px;
  background: var(--m-grey-200);
}

/* Hero visual */
.hero__visual { flex: 1; max-width: 480px; position: relative; min-height: 400px; }
.hero-visual { position: relative; width: 100%; height: 400px; }
.hv-card {
  position: absolute;
  background: white;
  border-radius: var(--m-radius-md);
  box-shadow: var(--m-shadow-lg);
  padding: 16px 20px;
  border: 1px solid var(--m-border);
}
.hv-card--1 { top: 0; left: 20px; width: 170px; animation: float1 6s ease-in-out infinite; }
.hv-card--2 { top: 40px; right: 0; width: 160px; animation: float2 7s ease-in-out infinite; }
.hv-card--3 { bottom: 60px; left: 40px; width: 160px; animation: float3 5s ease-in-out infinite; }
.hv-card--4 { bottom: 0; right: 20px; width: 170px; animation: float1 8s ease-in-out infinite; }
.hv-card__icon { font-size: 24px; margin-bottom: 6px; }
.hv-card__label { font-size: 0.75rem; color: var(--m-on-surface-muted); margin-bottom: 2px; }
.hv-card__value { font-size: 1.375rem; font-weight: 700; color: var(--m-on-surface); }
.hv-card__badge { display: inline-block; padding: 2px 8px; border-radius: 100px; font-size: 0.6875rem; font-weight: 600; margin-top: 4px; }
.hv-card__badge--up { background: rgba(16, 185, 129, 0.12); color: #059669; }
.hv-card__mini { font-size: 0.6875rem; color: var(--m-on-surface-muted); margin-top: 4px; }
.hv-card__sparkline { margin-top: 8px; }
.hv-card__sparkline svg { width: 100%; height: 30px; }

@keyframes float1 {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
@keyframes float2 {
  0%, 100% { transform: translateY(0) rotate(1deg); }
  50% { transform: translateY(-8px) rotate(-1deg); }
}
@keyframes float3 {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

/* ═══════════════════════════════════════════════════════════
   SECTION COMMON
   ═══════════════════════════════════════════════════════════ */
.section-header {
  text-align: center;
  margin-bottom: 48px;
}
.section-header--light { color: white; }
.section-label {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(85, 133, 255, 0.08);
  color: var(--m-primary);
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 12px;
}
.section-title {
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  font-weight: 700;
  color: var(--m-on-surface);
  margin: 0 0 12px;
  letter-spacing: -0.01em;
}
.section-desc {
  font-size: 1rem;
  color: var(--m-on-surface-muted);
  max-width: 560px;
  margin: 0 auto;
  line-height: 1.6;
}
.view-all {
  font-size: 0.875rem;
  color: var(--m-primary);
  text-decoration: none;
  font-weight: 600;
}
.view-all:hover { text-decoration: underline; }

/* ═══════════════════════════════════════════════════════════
   ROLES
   ═══════════════════════════════════════════════════════════ */
.roles-section {
  padding: 80px 0;
  background: white;
}
.roles-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.role-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: var(--m-bg);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-md);
  transition: all 0.2s;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}
.role-card:hover {
  border-color: var(--m-primary);
  background: rgba(85, 133, 255, 0.04);
  box-shadow: var(--m-shadow-sm);
  transform: translateY(-2px);
}
.role-card__icon-wrap {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  background: rgba(85, 133, 255, 0.10);
  border-radius: var(--m-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}
.role-card__icon {
  font-size: 20px;
  color: var(--m-primary);
}
.role-card__body { flex: 1; min-width: 0; }
.role-card__name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--m-on-surface);
  margin: 0 0 2px;
}
.role-card__desc {
  font-size: 0.75rem;
  color: var(--m-on-surface-muted);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.role-card__arrow {
  flex-shrink: 0;
  color: var(--m-grey-300);
  transition: color 0.15s;
}
.role-card:hover .role-card__arrow { color: var(--m-primary); }

/* ═══════════════════════════════════════════════════════════
   WORKS
   ═══════════════════════════════════════════════════════════ */
.works-section {
  padding: 80px 0;
  background: var(--m-bg);
}
.works-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.work-card {
  background: white;
  border-radius: var(--m-radius-md);
  border: 1px solid var(--m-border);
  overflow: hidden;
  transition: all 0.2s;
  text-decoration: none;
  color: inherit;
}
.work-card:hover {
  box-shadow: var(--m-shadow-md);
  transform: translateY(-3px);
}
.work-card__thumb {
  height: 160px;
  background-size: cover;
  background-position: center;
  background-color: var(--m-grey-100);
  position: relative;
}
.work-card__thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--m-grey-300);
}
.work-card__thumb-placeholder i { font-size: 32px; }
.work-card__certified {
  position: absolute;
  bottom: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: rgba(255,255,255,0.95);
  border-radius: 100px;
  font-size: 0.6875rem;
  font-weight: 600;
  color: #059669;
  backdrop-filter: blur(4px);
}
.work-card__certified i { font-size: 14px; }
.work-card__info { padding: 14px 16px; }
.work-card__title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--m-on-surface);
  margin: 0 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.work-card__creator {
  font-size: 0.75rem;
  color: var(--m-on-surface-muted);
  margin: 0;
}
.works-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--m-on-surface-muted);
}
.works-empty__icon { font-size: 48px; margin-bottom: 12px; }

/* ═══════════════════════════════════════════════════════════
   CONTRACTS
   ═══════════════════════════════════════════════════════════ */
.contracts-section {
  padding: 80px 0;
  background: white;
}
.contracts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 720px;
  margin: 0 auto;
}
.contract-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--m-bg);
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-md);
  transition: all 0.15s;
}
.contract-row:hover {
  border-color: rgba(85,133,255,0.3);
  box-shadow: var(--m-shadow-sm);
}
.contract-row__left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  flex: 1;
}
.contract-row__icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  background: rgba(85,133,255,0.10);
  border-radius: var(--m-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--m-primary);
}
.contract-row__icon i { font-size: 20px; }
.contract-row__title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--m-on-surface);
  margin: 0 0 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.contract-row__type {
  font-size: 0.75rem;
  color: var(--m-on-surface-muted);
  margin: 0;
}
.contract-row__meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.contract-row__amount {
  font-size: 1rem;
  font-weight: 700;
  color: var(--m-on-surface);
}
.contract-status {
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 0.6875rem;
  font-weight: 600;
}
.contract-status.active, .contract-status.listed { background: #dcfce7; color: #16a34a; }
.contract-status.subscribed { background: #fef3c7; color: #d97706; }
.contract-status.pending { background: #e0e7ff; color: #4f46e5; }
.contracts-empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--m-on-surface-muted);
}
.contracts-empty__icon { font-size: 48px; margin-bottom: 12px; }

/* ═══════════════════════════════════════════════════════════
   CAPABILITIES
   ═══════════════════════════════════════════════════════════ */
.capabilities-section {
  padding: 80px 0;
  background: linear-gradient(135deg, #1a1f36 0%, #2d3561 50%, #1a1f36 100%);
  color: white;
}
.capabilities-section .section-label {
  background: rgba(85,133,255,0.20);
  color: #8BA8FF;
}
.capabilities-section .section-title { color: white; }
.capabilities-section .section-desc { color: rgba(255,255,255,0.65); }
.capabilities-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}
.cap-card {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: var(--m-radius-lg);
  padding: 32px 24px;
  text-align: center;
  transition: all 0.2s;
  backdrop-filter: blur(8px);
}
.cap-card:hover {
  background: rgba(255,255,255,0.10);
  border-color: rgba(85,133,255,0.4);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.3);
}
.cap-card__icon { font-size: 36px; margin-bottom: 16px; }
.cap-card__title {
  font-size: 1.0625rem;
  font-weight: 700;
  color: white;
  margin: 0 0 8px;
}
.cap-card__desc {
  font-size: 0.8125rem;
  color: rgba(255,255,255,0.60);
  margin: 0;
  line-height: 1.6;
}

/* ═══════════════════════════════════════════════════════════
   CTA
   ═══════════════════════════════════════════════════════════ */
.cta-section {
  padding: 80px 0;
  background: var(--m-bg);
}
.cta-section__inner {
  text-align: center;
  max-width: 560px;
  margin: 0 auto;
}
.cta-section__title {
  font-size: clamp(1.5rem, 3vw, 2rem);
  font-weight: 700;
  color: var(--m-on-surface);
  margin: 0 0 12px;
}
.cta-section__desc {
  font-size: 1rem;
  color: var(--m-on-surface-muted);
  margin: 0 0 32px;
}
.cta-section__actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

/* ═══════════════════════════════════════════════════════════
   FOOTER
   ═══════════════════════════════════════════════════════════ */
.landing-footer {
  padding: 24px 0;
  background: white;
  border-top: 1px solid var(--m-border);
}
.landing-footer__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.landing-footer__brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 700;
  color: var(--m-on-surface);
}
.landing-footer__logo {
  color: var(--m-primary);
}
.landing-footer__copy {
  font-size: 0.8125rem;
  color: var(--m-on-surface-muted);
  margin: 0;
}

/* ═══════════════════════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 1023px) {
  .hero__inner { flex-direction: column; text-align: center; }
  .hero__content { max-width: 100%; }
  .hero__desc { margin-left: auto; margin-right: auto; }
  .hero__actions { justify-content: center; }
  .hero__trust { justify-content: center; }
  .hero__visual { display: none; }
  .roles-grid { grid-template-columns: repeat(2, 1fr); }
  .capabilities-grid { grid-template-columns: repeat(2, 1fr); }
  .works-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .hero { padding: 48px 0 64px; }
  .hero__title { font-size: 1.75rem; }
  .hero__trust { flex-wrap: wrap; gap: 16px; }
  .roles-grid { grid-template-columns: 1fr; }
  .capabilities-grid { grid-template-columns: 1fr; }
  .works-grid { grid-template-columns: 1fr; }
  .landing-footer__inner { flex-direction: column; gap: 8px; text-align: center; }
}
</style>

<template>
  <div class="landing-page">
    <!-- Fixed Nav -->
    <nav :class="['nav', { scrolled: isScrolled }]">
      <router-link to="/" class="brand">
        <div class="brand-logo">O</div>
        OriStudio
      </router-link>
      <ul class="nav-links">
        <li><a href="#features">功能</a></li>
        <li><a href="#workflow">协作流程</a></li>
        <li><a href="#trust">信任体系</a></li>
        <li><router-link to="/onboarding">新手指引</router-link></li>
      </ul>
      <div class="nav-btns">
        <router-link to="/login" class="btn btn-secondary">登录</router-link>
        <router-link to="/app" class="btn btn-primary">开始使用</router-link>
      </div>
    </nav>

    <!-- HERO -->
    <main>
      <div class="hero-wrapper">
        <div class="hero-bg-deco"></div>
        <div class="hero-bg-deco2"></div>
        <div class="hero">
          <div class="hero-text">
            <div class="hero-badge"><span class="dot"></span> v5.0 · 多边撮合 + 信任枢纽</div>
            <h1>创作者的<br><span class="em">合约市场与信任引擎</span></h1>
            <p class="hero-desc">
              连接创作者、运营者、税务代理、物流商、保险商等 9 种参与角色，
              提供合约挂牌、智能撮合、分润执行、L1-L4 四级版权防御与 AIGC 溯源审计，
              让每一次协作都有据可查、有保可投。
            </p>
            <div class="hero-actions">
              <router-link to="/app" class="btn btn-primary" style="font-size:1rem;padding:14px 28px;">进入工作台 →</router-link>
              <router-link to="/onboarding" class="btn btn-secondary">了解原理</router-link>
            </div>
          </div>
          <div class="hero-visual">
            <div class="hero-card-3d">
              <div class="hc-header">
                <div class="hc-avatar">🔗</div>
                <div>
                  <div class="hc-title">合约市场概览</div>
                  <div class="hc-sub">多边协作 · 实时撮合 · 智能分润</div>
                </div>
              </div>
              <div class="hc-stats">
                <div class="hc-stat"><div class="hc-stat-val">9</div><div class="hc-stat-label">参与角色</div></div>
                <div class="hc-stat"><div class="hc-stat-val">12</div><div class="hc-stat-label">合约状态</div></div>
                <div class="hc-stat"><div class="hc-stat-val">3‰</div><div class="hc-stat-label">平台费率</div></div>
              </div>
              <div class="hc-modules">
                <div class="hc-mod"><span class="hc-mod-dot blue"></span>合约挂牌</div>
                <div class="hc-mod"><span class="hc-mod-dot green"></span>智能撮合</div>
                <div class="hc-mod"><span class="hc-mod-dot orange"></span>支付托管</div>
                <div class="hc-mod"><span class="hc-mod-dot purple"></span>分润执行</div>
                <div class="hc-mod"><span class="hc-mod-dot pink"></span>版权保险</div>
                <div class="hc-mod"><span class="hc-mod-dot cyan"></span>AIGC 溯源</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- CORE FEATURES -->
      <section class="section" id="features">
        <div class="section-header">
          <div class="section-tag">核心能力</div>
          <h2>9 方参与者 · 12 种合约状态 · 4 层版权防御</h2>
          <p class="section-sub">从创作署名到合约分润，从侵权监测到全球申报——全流程数字化、可审计、可追溯。</p>
        </div>
        <div class="features-grid">
          <!-- Feature 1: 合约市场 -->
          <div class="feature-card feature-card--wide">
            <div class="fc-icon" style="background: oklch(56% 0.12 170 / 0.12); color: oklch(56% 0.12 170);">🔗</div>
            <div class="fc-title">合约市场</div>
            <div class="fc-desc">合约挂牌、智能撮合、支付托管、分润执行一站式完成。12 状态流转保证每一笔交易的可追溯性，3‰ 平台手续费保证低成本运转。</div>
            <ul class="fc-features">
              <li>合约挂牌/搜索/订阅/取消</li>
              <li>标签/地域/评分智能撮合</li>
              <li>支付托管 + 多方分润</li>
              <li>平台 3‰ 手续费自动结算</li>
            </ul>
          </div>
          <!-- Feature 2: 权益保护 -->
          <div class="feature-card">
            <div class="fc-icon" style="background: oklch(62% 0.16 260 / 0.12); color: oklch(62% 0.16 260);">🛡️</div>
            <div class="fc-title">L1-L4 四级版权防御</div>
            <div class="fc-desc">零成本存证到专属法律顾问，4 层防御矩阵根据作品价值和侵权场景自动推荐最优维权路径。</div>
            <ul class="fc-features">
              <li>L1: ECDSA 本地签名存证</li>
              <li>L2: 平台工具自动监测</li>
              <li>L3: CNIPA 律师审核登记</li>
              <li>L4: 司法链/区块链锚定</li>
            </ul>
          </div>
          <!-- Feature 3: AIGC 溯源 -->
          <div class="feature-card">
            <div class="fc-icon" style="background: oklch(58% 0.14 245 / 0.12); color: oklch(58% 0.14 245);">🔍</div>
            <div class="fc-title">AIGC 痕迹审计</div>
            <div class="fc-desc">四层溯源链：平台日志 → MCP 事件流 → AI 自声明 → 人类贡献度评分。区分人机协作比例，保障原创权益。</div>
            <ul class="fc-features">
              <li>人类贡献度评分器（≥0.60 通过）</li>
              <li>C2PA + TSA + 区块链三重锚定</li>
              <li>AI 会话记录交叉验证</li>
              <li>溯源审计报告 PDF 生成</li>
            </ul>
          </div>
          <!-- Feature 4: 合约撮合 -->
          <div class="feature-card">
            <div class="fc-icon" style="background: oklch(62% 0.18 55 / 0.12); color: oklch(62% 0.18 55);">⚡</div>
            <div class="fc-title">合约撮合引擎</div>
            <div class="fc-desc">基于创作者标签、地域分布、历史评分的智能匹配，让优质创作快速找到合适的交易方。</div>
            <ul class="fc-features">
              <li>多维标签匹配算法</li>
              <li>地域适配推荐</li>
              <li>SCR 信誉分加权排序</li>
            </ul>
          </div>
          <!-- Feature 5: 分润执行 -->
          <div class="feature-card">
            <div class="fc-icon" style="background: oklch(58% 0.16 350 / 0.12); color: oklch(58% 0.16 350);">💰</div>
            <div class="fc-title">分润执行引擎</div>
            <div class="fc-desc">市场化的分润规则配置，支持多参与方按比例自动分账，每一笔分润都留下审计日志。</div>
            <ul class="fc-features">
              <li>灵活分润规则配置</li>
              <li>多角色按比例自动分账</li>
              <li>分润执行日志可审计</li>
            </ul>
          </div>
          <!-- Feature 6: 回流引擎 -->
          <div class="feature-card">
            <div class="fc-icon" style="background: oklch(60% 0.12 200 / 0.12); color: oklch(60% 0.12 200);">↩️</div>
            <div class="fc-title">分发回流引擎</div>
            <div class="fc-desc">短链生成 + 归因事件追踪，追踪作品的分发路径和回流来源，帮助创作者理解流量来源。</div>
            <ul class="fc-features">
              <li>短链生成 + 品牌域名</li>
              <li>点击/浏览/转化归因</li>
              <li>跨平台分发效果分析</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- PARTICIPANT ROLES -->
      <section class="section section--alt" id="roles">
        <div class="section-header">
          <div class="section-tag">9 方参与者</div>
          <h2>每一种角色都有价值</h2>
          <p class="section-sub">创作者、运营者、法务、税务代理、物流商、保险商、采购商、支付方、平台——9 种角色各司其职，构成完整的创作生态。</p>
        </div>
        <div class="roles-grid">
          <div class="role-card" v-for="role in PARTICIPANT_ROLES" :key="role.key">
            <div class="role-icon">{{ role.icon }}</div>
            <div class="role-name">{{ role.name }}</div>
            <div class="role-desc">{{ role.desc }}</div>
          </div>
        </div>
      </section>

      <!-- TRUST SYSTEM -->
      <section class="section" id="trust">
        <div class="section-header">
          <div class="section-tag">信任体系</div>
          <h2>每一笔交易都有据可查</h2>
          <p class="section-sub">从 L1 本地签名到 L4 司法链锚定，从 C2PA 元数据到区块链存证——多层信任机制保障每一份合约的可靠性。</p>
        </div>
        <div class="defense-tiers">
          <div class="tier tier-zero">
            <div class="tier-label">L1</div>
            <div class="tier-name">本地签名存证</div>
            <div class="tier-desc">ECDSA 本地哈希签名，零成本即时存证</div>
          </div>
          <div class="tier tier-low">
            <div class="tier-label">L2</div>
            <div class="tier-name">平台工具监测</div>
            <div class="tier-desc">C2PA 元数据 + 反向图片搜索 + RSS 订阅</div>
          </div>
          <div class="tier tier-mid">
            <div class="tier-label">L3</div>
            <div class="tier-name">法律登记确证</div>
            <div class="tier-desc">CNIPA 律师审核 + 版权/商标正式登记</div>
          </div>
          <div class="tier tier-high">
            <div class="tier-label">L4</div>
            <div class="tier-name">司法链/区块链锚定</div>
            <div class="tier-desc">司法链 + Polygon 链上存证，全球可验证</div>
          </div>
        </div>
      </section>

      <!-- WORKFLOW -->
      <section class="section" id="workflow">
        <div class="section-header">
          <div class="section-tag">协作流程</div>
          <h2>从创作到变现的完整闭环</h2>
          <p class="section-sub">四步完成从作品创作到合约分润的全流程，每一步都有存证、可审计、可追溯。</p>
        </div>
        <div class="steps-flow">
          <div class="step">
            <div class="step-num">1</div>
            <div class="step-title">上传存证</div>
            <div class="step-desc">SHA-256 哈希 + ECDSA 签名 + C2PA 元数据</div>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <div class="step-title">合约挂牌</div>
            <div class="step-desc">定价、分润规则、授权范围一键发布</div>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <div class="step-title">智能撮合</div>
            <div class="step-desc">标签匹配 + 地域适配 + SCR 信誉加权</div>
          </div>
          <div class="step">
            <div class="step-num">4</div>
            <div class="step-title">分润结算</div>
            <div class="step-desc">托管支付 → 多方分润 → 分润审计日志</div>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="cta-section">
        <div class="cta-card">
          <h3>开启你的创作合约之旅</h3>
          <p>9 方参与者 · 12 状态流转 · 4 层版权防御 · AIGC 溯源审计</p>
          <router-link to="/app" class="btn btn-cta">🚀 开始使用</router-link>
        </div>
      </section>
    </main>

    <!-- FOOTER -->
    <footer class="footer">
      <div class="footer-brand">
        <div class="brand-logo" style="width:28px;height:28px;font-size:0.8rem;">O</div>
        <div>
          <div style="font-weight:600;">OriStudio</div>
          <div style="font-size:0.75rem;color:var(--muted);">创作者合约市场与信任枢纽 · v5.0</div>
        </div>
      </div>
      <span>数据主权归你所有 · MIT 开源许可 · 2026</span>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isScrolled = ref(false)

function onScroll() {
  isScrolled.value = window.scrollY > 10
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const PARTICIPANT_ROLES = [
  { key: 'creator', icon: '🎨', name: '创作者', desc: '作品的原创者，上传作品、设定合约条款' },
  { key: 'operator', icon: '📋', name: '运营者', desc: '作品的运营推广，对接市场需求' },
  { key: 'legal', icon: '⚖️', name: '法务代理', desc: '合同审查、争议解决、法律合规' },
  { key: 'tax', icon: '🧾', name: '税务代理', desc: '跨国税务合规、Avalara 申报' },
  { key: 'logistics', icon: '📦', name: '物流商', desc: '实物商品配送、物流追踪' },
  { key: 'insurer', icon: '🛡️', name: '保险商', desc: '版权保险、理赔处理' },
  { key: 'buyer', icon: '🛒', name: '采购商', desc: '购买作品授权、订阅合约' },
  { key: 'payer', icon: '💳', name: '支付方', desc: '支付托管、多币种结算' },
  { key: 'platform', icon: '🏛️', name: '平台方', desc: '撮合交易、分润执行、监管合规' },
]
</script>

<style scoped>
.landing-page { background: var(--bg, #f8fafc); color: var(--fg, #1f2937); line-height: 1.6; overflow-x: hidden; }

/* --- NAV --- */
.nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  padding: 0 clamp(16px, 4vw, 80px);
  height: 64px;
  display: flex; align-items: center; justify-content: space-between;
  background: oklch(98% 0.004 240 / 0.82);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  border-bottom: 1px solid oklch(90% 0.006 240);
  transition: box-shadow 0.3s ease;
}
.nav.scrolled { box-shadow: 0 1px 0 oklch(0 0 0 / 0.04), 0 4px 24px oklch(0 0 0 / 0.06); }

.brand {
  display: flex; align-items: center; gap: 10px;
  font-family: var(--font-display, system-ui); font-weight: 700; font-size: 1.35rem;
  letter-spacing: -0.015em; color: var(--fg, #1f2937); text-decoration: none;
}
.brand-logo {
  width: 36px; height: 36px; border-radius: var(--radius-sm, 6px);
  background: linear-gradient(135deg, var(--grad1, #0ea5e9), var(--grad2, #3b82f6));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 1.1rem; font-weight: 800;
  box-shadow: 0 2px 12px oklch(56% 0.12 170 / 0.3);
}
.brand:hover .brand-logo { box-shadow: 0 4px 20px oklch(56% 0.12 170 / 0.45); }

.nav-links { display: flex; gap: 32px; align-items: center; list-style: none; }
.nav-links a {
  text-decoration: none; color: var(--muted, #6b7280); font-size: 0.925rem;
  font-weight: 500; transition: color 0.2s; position: relative;
}
.nav-links a:hover { color: var(--fg, #1f2937); }
.nav-links a::after {
  content: ''; position: absolute; bottom: -4px; left: 0; width: 0; height: 2px;
  background: var(--accent, #0ea5e9); border-radius: 1px; transition: width 0.25s ease;
}
.nav-links a:hover::after { width: 100%; }
.nav-btns { display: flex; gap: 8px; }

.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 22px; border-radius: var(--radius, 8px);
  font-family: var(--font-body, system-ui); font-size: 0.925rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease;
  text-decoration: none; border: none; white-space: nowrap;
}
.btn-primary {
  background: linear-gradient(135deg, var(--grad1, #0ea5e9), var(--grad2, #3b82f6));
  color: #fff; box-shadow: 0 2px 14px oklch(56% 0.12 170 / 0.3);
}
.btn-primary:hover { box-shadow: 0 6px 24px oklch(56% 0.12 170 / 0.45); transform: translateY(-1px); }
.btn-secondary {
  background: var(--surface, #fff); color: var(--fg, #1f2937);
  border: 1px solid var(--border, #e5e7eb);
}
.btn-secondary:hover { background: oklch(96% 0.004 240); border-color: var(--muted, #6b7280); }

/* --- HERO --- */
.hero-wrapper {
  padding: 120px clamp(16px, 6vw, 80px) 80px;
  background: linear-gradient(180deg, oklch(96% 0.006 240) 0%, var(--bg, #f8fafc) 100%);
  position: relative; overflow: hidden;
}
.hero-bg-deco {
  position: absolute; top: -120px; right: -80px; width: 600px; height: 600px;
  background: radial-gradient(circle, oklch(56% 0.12 170 / 0.08) 0%, transparent 70%);
  border-radius: 50%; pointer-events: none;
}
.hero-bg-deco2 {
  position: absolute; bottom: -80px; left: -40px; width: 400px; height: 400px;
  background: radial-gradient(circle, oklch(62% 0.16 260 / 0.06) 0%, transparent 70%);
  border-radius: 50%; pointer-events: none;
}
.hero {
  max-width: 1200px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center;
  position: relative; z-index: 1;
}
.hero-text { display: flex; flex-direction: column; gap: 24px; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 100px;
  background: oklch(56% 0.12 170 / 0.1); color: var(--accent, #0ea5e9);
  font-size: 0.8rem; font-weight: 600; letter-spacing: 0.02em;
  width: fit-content;
}
.hero-badge .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent, #0ea5e9); animation: pulse-dot 2s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.35} }

h1 { font-family: var(--font-display, system-ui); font-size: clamp(2.5rem, 5.5vw, 4rem); font-weight: 700; line-height: 1.12; letter-spacing: -0.025em; }
h1 .em { background: linear-gradient(135deg, var(--grad1, #0ea5e9), var(--grad2, #3b82f6)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-desc { font-size: 1.15rem; color: var(--muted, #6b7280); line-height: 1.7; max-width: 480px; }
.hero-actions { display: flex; gap: 14px; flex-wrap: wrap; }

.hero-visual { display: flex; align-items: center; justify-content: center; perspective: 1000px; }
.hero-card-3d {
  width: 100%; max-width: 520px;
  background: var(--surface, #fff); border-radius: var(--radius-xl, 16px);
  box-shadow: 0 0 0 1px oklch(0 0 0 / 0.04), 0 8px 32px oklch(0 0 0 / 0.06), 0 24px 80px oklch(0 0 0 / 0.08);
  padding: 28px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.hero-card-3d:hover { transform: translateY(-4px); box-shadow: 0 0 0 1px oklch(0 0 0 / 0.05), 0 12px 40px oklch(0 0 0 / 0.08), 0 32px 100px oklch(0 0 0 / 0.12); }
.hc-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border, #e5e7eb); }
.hc-avatar { width: 44px; height: 44px; border-radius: var(--radius-sm, 6px); background: linear-gradient(135deg, oklch(56% 0.12 170 / 0.2), oklch(62% 0.16 260 / 0.2)); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
.hc-title { font-weight: 600; font-size: 0.95rem; }
.hc-sub { font-size: 0.78rem; color: var(--muted, #6b7280); }
.hc-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.hc-stat { background: oklch(96% 0.006 240); border-radius: var(--radius, 8px); padding: 14px; text-align: center; }
.dark .hc-stat { background: oklch(24% 0.01 240); }
.hc-stat-val { font-size: 1.6rem; font-weight: 700; color: var(--primary, #0ea5e9); }
.hc-stat-label { font-size: 0.7rem; color: var(--muted, #6b7280); margin-top: 2px; }
.hc-modules { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.hc-mod { display: flex; align-items: center; gap: 6px; padding: 10px 12px; border-radius: var(--radius-sm, 6px); font-size: 0.78rem; font-weight: 500; background: oklch(96% 0.006 240); transition: background 0.2s; }
.dark .hc-mod { background: oklch(24% 0.01 240); }
.hc-mod:hover { background: oklch(56% 0.12 170 / 0.08); }
.hc-mod-dot { width: 8px; height: 8px; border-radius: 3px; }
.hc-mod-dot.blue { background: oklch(58% 0.14 245); }
.hc-mod-dot.green { background: oklch(56% 0.12 170); }
.hc-mod-dot.orange { background: oklch(62% 0.18 55); }
.hc-mod-dot.purple { background: oklch(56% 0.12 280); }
.hc-mod-dot.pink { background: oklch(58% 0.16 350); }
.hc-mod-dot.cyan { background: oklch(60% 0.12 200); }

/* --- SECTIONS --- */
.section { max-width: 1200px; margin: 0 auto; padding: 80px clamp(16px, 6vw, 80px); }
.section--alt { background: oklch(97% 0.004 240); margin: 0; max-width: 100%; padding: 80px clamp(16px, 6vw, 80px); }
.section-header { text-align: center; margin-bottom: 56px; display: flex; flex-direction: column; gap: 12px; }
.section-tag { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: var(--accent, #0ea5e9); }
h2 { font-family: var(--font-display, system-ui); font-size: clamp(1.8rem, 3.8vw, 2.8rem); font-weight: 700; letter-spacing: -0.015em; line-height: 1.2; }
.section-sub { font-size: 1.05rem; color: var(--muted, #6b7280); max-width: 560px; margin: 0 auto; }

/* --- FEATURE CARDS --- */
.features-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem; align-items: start; }
.feature-card--wide { grid-column: span 2; }
.feature-card {
  background: var(--surface, #fff); border-radius: var(--radius-lg, 12px);
  border: 1px solid var(--border, #e5e7eb); padding: 32px 28px;
  display: flex; flex-direction: column; gap: 14px;
  transition: all 0.3s ease;
}
.feature-card:hover { transform: translateY(-4px); box-shadow: 0 12px 32px var(--accent, #0ea5e9) / 0.12; border-color: transparent; }
.fc-icon { width: 48px; height: 48px; border-radius: var(--radius, 8px); display: flex; align-items: center; justify-content: center; font-size: 1.4rem; }
.fc-title { font-family: var(--font-display, system-ui); font-size: 1.15rem; font-weight: 700; letter-spacing: -0.01em; }
.fc-desc { font-size: 0.9rem; color: var(--muted, #6b7280); line-height: 1.6; }
.fc-features { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.fc-features li { font-size: 0.82rem; color: var(--muted, #6b7280); display: flex; align-items: center; gap: 6px; }
.fc-features li::before { content: '•'; color: var(--accent, #0ea5e9); font-weight: 700; }

/* --- PARTICIPANT ROLES --- */
.roles-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; max-width: 1000px; margin: 0 auto; }
.role-card {
  background: var(--surface, #fff); border-radius: var(--radius-lg, 12px);
  border: 1px solid var(--border, #e5e7eb); padding: 24px;
  display: flex; flex-direction: column; align-items: center; text-align: center; gap: 10px;
  transition: all 0.3s ease;
}
.role-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px oklch(0 0 0 / 0.08); border-color: var(--accent, #0ea5e9); }
.role-icon { font-size: 2rem; }
.role-name { font-weight: 700; font-size: 1rem; }
.role-desc { font-size: 0.82rem; color: var(--muted, #6b7280); line-height: 1.5; }

/* --- DEFENSE TIERS --- */
.defense-tiers { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; max-width: 1000px; margin: 0 auto; }
.tier {
  border-radius: var(--radius-lg, 12px); padding: 28px 20px; text-align: center;
  border: 1px solid var(--border, #e5e7eb); background: var(--surface, #fff);
  transition: all 0.3s ease;
}
.tier:hover { transform: translateY(-4px); box-shadow: 0 8px 24px oklch(0 0 0 / 0.08); }
.tier-zero { border-color: oklch(80% 0.01 240); background: oklch(98% 0.004 240); }
.tier-low { border-color: oklch(56% 0.12 170 / 0.3); background: oklch(98% 0.006 170); }
.tier-mid { border-color: oklch(62% 0.18 55 / 0.3); background: oklch(98% 0.008 55); }
.tier-high { border-color: oklch(58% 0.14 245 / 0.3); background: oklch(97% 0.006 245); }
.tier-label { font-family: var(--font-display, system-ui); font-size: 1.5rem; font-weight: 700; margin-bottom: 8px; }
.tier-zero .tier-label { color: oklch(50% 0.01 240); }
.tier-low .tier-label { color: oklch(56% 0.12 170); }
.tier-mid .tier-label { color: oklch(62% 0.18 55); }
.tier-high .tier-label { color: oklch(58% 0.14 245); }
.tier-name { font-weight: 700; font-size: 0.95rem; margin-bottom: 8px; }
.tier-desc { font-size: 0.8rem; color: var(--muted, #6b7280); line-height: 1.5; }

/* --- PROOF --- */
.proof-section { background: linear-gradient(180deg, var(--surface, #fff) 0%, oklch(96% 0.006 240) 100%); padding: 80px clamp(16px, 6vw, 80px); }
.proof-grid { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.proof-stat { text-align: center; }
.proof-num { font-family: var(--font-display, system-ui); font-size: 2.6rem; font-weight: 700; background: linear-gradient(135deg, var(--grad1, #0ea5e9), var(--grad2, #3b82f6)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.proof-label { font-size: 0.85rem; color: var(--muted, #6b7280); margin-top: 4px; }

/* --- STEPS FLOW --- */
.steps-flow {
  max-width: 900px; margin: 0 auto; display: flex; align-items: flex-start;
  justify-content: space-between; position: relative;
}
.steps-flow::before {
  content: ''; position: absolute; top: 32px; left: 60px; right: 60px; height: 2px;
  background: var(--border, #e5e7eb); z-index: 0;
}
.step {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  position: relative; z-index: 1; text-align: center; flex: 1;
}
.step-num {
  width: 64px; height: 64px; border-radius: 50%;
  background: var(--surface, #fff); border: 2px solid var(--border, #e5e7eb);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display, system-ui); font-size: 1.3rem; font-weight: 700;
  color: var(--accent, #0ea5e9); transition: all 0.3s ease;
}
.step:hover .step-num {
  background: var(--accent, #0ea5e9); color: #fff; border-color: var(--accent, #0ea5e9);
  box-shadow: 0 8px 28px oklch(56% 0.12 170 / 0.3); transform: scale(1.08);
}
.step-title { font-weight: 700; font-size: 0.95rem; }
.step-desc { font-size: 0.8rem; color: var(--muted, #6b7280); }

/* --- CTA --- */
.cta-section { text-align: center; padding: 80px clamp(16px, 6vw, 80px); }
.cta-card {
  max-width: 700px; margin: 0 auto;
  background: linear-gradient(135deg, var(--grad1, #0ea5e9), var(--grad2, #3b82f6));
  border-radius: var(--radius-xl, 16px); padding: 56px 48px; color: #fff;
  position: relative; overflow: hidden;
  box-shadow: 0 16px 56px oklch(56% 0.12 170 / 0.3);
}
.cta-card::before { content: ''; position: absolute; top: -60px; right: -60px; width: 200px; height: 200px; background: oklch(100% 0 0 / 0.08); border-radius: 50%; }
.cta-card::after { content: ''; position: absolute; bottom: -40px; left: -40px; width: 140px; height: 140px; background: oklch(100% 0 0 / 0.06); border-radius: 50%; }
.cta-card h3 { font-family: var(--font-display, system-ui); font-size: 2rem; font-weight: 700; position: relative; z-index: 1; margin-bottom: 12px; }
.cta-card p { font-size: 1.05rem; opacity: 0.85; position: relative; z-index: 1; margin-bottom: 28px; }
.btn-cta { background: #fff; color: var(--accent, #0ea5e9); padding: 12px 28px; font-size: 0.95rem; font-weight: 700; box-shadow: 0 4px 16px oklch(0 0 0 / 0.15); position: relative; z-index: 1; }
.btn-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 28px oklch(0 0 0 / 0.2); }

/* --- FOOTER --- */
.footer {
  max-width: 1200px; margin: 0 auto;
  padding: 40px clamp(16px, 6vw, 80px);
  border-top: 1px solid var(--border, #e5e7eb);
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px; font-size: 0.85rem; color: var(--muted, #6b7280);
}
.footer-brand { display: flex; align-items: center; gap: 10px; }

/* --- RESPONSIVE --- */
@media (max-width: 1024px) {
  .hero { grid-template-columns: 1fr; gap: 48px; text-align: center; }
  .hero-desc { max-width: 100%; }
  .hero-actions { justify-content: center; }
  .hero-card-3d { transform: none; max-width: 420px; }
  .features-grid { grid-template-columns: 1fr; }
  .feature-card--wide { grid-column: span 1; }
  .roles-grid { grid-template-columns: repeat(2, 1fr); }
  .defense-tiers { grid-template-columns: repeat(2, 1fr); }
  .proof-grid { grid-template-columns: repeat(2, 1fr); }
  .steps-flow { flex-direction: column; align-items: center; gap: 24px; }
  .steps-flow::before { display: none; }
}
@media (max-width: 640px) {
  .nav-links { display: none; }
  .roles-grid { grid-template-columns: 1fr; }
  .defense-tiers { grid-template-columns: 1fr; }
  .proof-grid { grid-template-columns: repeat(2, 1fr); }
  .hero-wrapper { padding: 100px 16px 56px; }
  .section, .cta-section { padding: 56px 16px; }
  .cta-card { padding: 40px 24px; }
  .hc-stats { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .hc-modules { grid-template-columns: repeat(2, 1fr); }
}

@media (prefers-reduced-motion: reduce) {
  .hero-card-3d { transition: none; }
  .feature-card { transition: none; }
  .role-card { transition: none; }
  .tier { transition: none; }
  .step-num { transition: none; }
  .btn-primary { transition: none; }
  .btn-cta { transition: none; }
  * { animation-duration: 0.01ms !important; }
}
</style>

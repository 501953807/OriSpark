<template>
  <div class="landing-page">
    <!-- Fixed Nav — 轻奢风深色 -->
    <nav :class="['nav', { scrolled: isScrolled }]">
      <router-link to="/" class="brand">
        <div class="brand-logo">O</div>
        <span>OriStudio</span>
        <span class="brand-tag">创作者专属</span>
      </router-link>
      <ul class="nav-links">
        <li><a href="#features">核心能力</a></li>
        <li><a href="#trust">信任体系</a></li>
        <li><a href="#workflow">协作流程</a></li>
        <li><router-link to="/onboarding">新手引导</router-link></li>
      </ul>
      <div class="nav-btns">
        <router-link to="/login" class="btn btn-secondary">创作者登录</router-link>
        <router-link to="/app" class="btn btn-primary">进入工作台 →</router-link>
      </div>
    </nav>

    <!-- HERO — 深色轻奢风 -->
    <main>
      <div class="hero-wrapper">
        <div class="hero-grid-overlay"></div>
        <div class="hero">
          <div class="hero-text">
            <div class="hero-badge">
              <span class="dot green"></span>
              v6.0 · 独立创作者工作台
            </div>
            <h1>
              你的创作<br>
              <span class="em">权益与合约守护引擎</span>
            </h1>
            <p class="hero-desc">
              为独立创作者提供从存证保护到合约挂牌的全链路工具。
              L1-L4 四级版权防御、智能撮合、多方分润——
              让你的每一笔创作交易都有据可查、有保可投。
            </p>
            <div class="hero-actions">
              <router-link to="/app" class="btn btn-primary" style="font-size:1rem;padding:14px 28px;">
                进入创作者工作台 →
              </router-link>
              <router-link to="/onboarding" class="btn btn-secondary">了解原理</router-link>
            </div>
            <p class="creator-note">
              <span class="note-icon">🔒</span> 仅面向独立创作者开放 · 非创作者请前往
              <a href="https://orispark.local" target="_blank">OriSpark 交易后台</a>
            </p>
          </div>
          <div class="hero-visual">
            <div class="hero-card-3d">
              <div class="hc-header">
                <div class="hc-avatar">🎨</div>
                <div>
                  <div class="hc-title">创作者工作台</div>
                  <div class="hc-sub">存证 · 挂牌 · 撮合 · 分润</div>
                </div>
              </div>
              <div class="hc-stats">
                <div class="hc-stat">
                  <div class="hc-stat-val data-mono">4</div>
                  <div class="hc-stat-label">防御层级</div>
                </div>
                <div class="hc-stat">
                  <div class="hc-stat-val data-mono">3‰</div>
                  <div class="hc-stat-label">平台费率</div>
                </div>
                <div class="hc-stat">
                  <div class="hc-stat-val data-mono">12</div>
                  <div class="hc-stat-label">合约状态</div>
                </div>
              </div>
              <div class="hc-modules">
                <div class="hc-mod"><span class="hc-mod-dot green"></span>作品存证</div>
                <div class="hc-mod"><span class="hc-mod-dot blue"></span>合约挂牌</div>
                <div class="hc-mod"><span class="hc-mod-dot orange"></span>智能撮合</div>
                <div class="hc-mod"><span class="hc-mod-dot purple"></span>支付托管</div>
                <div class="hc-mod"><span class="hc-mod-dot pink"></span>多方分润</div>
                <div class="hc-mod"><span class="hc-mod-dot cyan"></span>版权保险</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- CORE FEATURES -->
      <section class="section" id="features">
        <div class="section-header">
          <div class="section-tag">核心能力</div>
          <h2>创作者全链路权益守护</h2>
          <p class="section-sub">从创作署名到合约分润，从侵权监测到全球申报——全流程数字化、可审计、可追溯。</p>
        </div>
        <div class="features-grid">
          <div class="feature-card">
            <div class="fc-icon" style="color: oklch(56% 0.12 170);">🛡️</div>
            <div class="fc-title">L1-L4 四级版权防御</div>
            <div class="fc-desc">零成本存证到专属法律顾问，4 层防御矩阵根据作品价值自动推荐最优维权路径。</div>
            <ul class="fc-features">
              <li>L1: ECDSA 本地签名存证</li>
              <li>L2: 平台工具自动监测</li>
              <li>L3: CNIPA 律师审核登记</li>
              <li>L4: 司法链/区块链锚定</li>
            </ul>
          </div>
          <div class="feature-card">
            <div class="fc-icon" style="color: oklch(58% 0.14 245);">🔍</div>
            <div class="fc-title">AIGC 痕迹审计</div>
            <div class="fc-desc">四层溯源链：平台日志 → MCP 事件流 → AI 自声明 → 人类贡献度评分。</div>
            <ul class="fc-features">
              <li>人类贡献度评分器（≥0.60 通过）</li>
              <li>C2PA + TSA + 区块链三重锚定</li>
              <li>AI 会话记录交叉验证</li>
            </ul>
          </div>
          <div class="feature-card">
            <div class="fc-icon" style="color: oklch(62% 0.18 55);">⚡</div>
            <div class="fc-title">合约挂牌与撮合</div>
            <div class="fc-desc">一键发布合约、智能匹配交易方、支付托管、多方分润自动执行。</div>
            <ul class="fc-features">
              <li>合约挂牌/搜索/订阅/取消</li>
              <li>标签/地域/评分智能撮合</li>
              <li>支付托管 + 多方分润</li>
              <li>平台 3‰ 手续费自动结算</li>
            </ul>
          </div>
          <div class="feature-card">
            <div class="fc-icon" style="color: oklch(58% 0.16 350);">💰</div>
            <div class="fc-title">分润执行引擎</div>
            <div class="fc-desc">灵活分润规则配置，支持多参与方按比例自动分账，每一笔分润可审计。</div>
            <ul class="fc-features">
              <li>灵活分润规则配置</li>
              <li>多角色按比例自动分账</li>
              <li>分润执行日志可审计</li>
            </ul>
          </div>
          <div class="feature-card">
            <div class="fc-icon" style="color: oklch(60% 0.12 200);">↩️</div>
            <div class="fc-title">分发回流引擎</div>
            <div class="fc-desc">短链生成 + 归因事件追踪，帮助创作者理解流量来源和分发效果。</div>
            <ul class="fc-features">
              <li>短链生成 + 品牌域名</li>
              <li>点击/浏览/转化归因</li>
              <li>跨平台分发效果分析</li>
            </ul>
          </div>
          <div class="feature-card">
            <div class="fc-icon" style="color: oklch(56% 0.12 280);">🤝</div>
            <div class="fc-title">协同创作</div>
            <div class="fc-desc">多个创作者共同参与创作，人类贡献度评分器量化每个参与者的价值。</div>
            <ul class="fc-features">
              <li>多创作者协作工作区</li>
              <li>人类贡献度自动评分</li>
              <li>贡献比例合约化</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- TRUST SYSTEM -->
      <section class="section" id="trust">
        <div class="section-header">
          <div class="section-tag">信任体系</div>
          <h2>每一笔交易都有据可查</h2>
          <p class="section-sub">从 L1 本地签名到 L4 司法链锚定，从 C2PA 元数据到区块链存证——多层信任机制。</p>
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
          <p>L1-L4 四级版权防御 · 智能撮合 · 多方分润 · AIGC 溯源审计</p>
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
          <div style="font-size:0.75rem;color:var(--muted);">创作者专属工作台 · v6.0</div>
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
</script>

<style scoped>
.landing-page {
  background: var(--bg, #0f172a);
  color: var(--fg, #f1f5f9);
  line-height: 1.6;
  overflow-x: hidden;
}

/* --- HERO OVERLAY GRID --- */
.hero-grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(212,168,83,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(212,168,83,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}

/* --- NAV --- */
.nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  padding: 0 clamp(16px, 4vw, 80px);
  height: 64px;
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(20px) saturate(140%);
  -webkit-backdrop-filter: blur(20px) saturate(140%);
  border-bottom: 1px solid rgba(51, 65, 85, 0.8);
  transition: box-shadow 0.3s ease;
}
.nav.scrolled { box-shadow: 0 2px 24px rgba(0,0,0,0.5); }

.brand {
  display: flex; align-items: center; gap: 10px;
  font-family: var(--font-display, system-ui); font-weight: 700; font-size: 1.35rem;
  letter-spacing: -0.015em; color: var(--fg); text-decoration: none;
}
.brand-logo {
  width: 36px; height: 36px; border-radius: var(--radius-sm, 4px);
  background: linear-gradient(135deg, var(--gold, #d4a853), var(--grad2, #b8912e));
  display: flex; align-items: center; justify-content: center;
  color: #0f172a; font-size: 1.1rem; font-weight: 800;
  box-shadow: 0 2px 12px rgba(212, 168, 83, 0.3);
}
.brand-tag {
  font-size: 0.65rem; font-weight: 600; color: var(--gold);
  background: rgba(212, 168, 83, 0.12); border: 1px solid rgba(212, 168, 83, 0.25);
  padding: 2px 8px; border-radius: 100px; letter-spacing: 0.05em;
}
.nav-links { display: flex; gap: 28px; align-items: center; list-style: none; }
.nav-links a {
  text-decoration: none; color: var(--muted); font-size: 0.9rem;
  font-weight: 500; transition: color 0.2s;
}
.nav-links a:hover { color: var(--gold); }
.nav-btns { display: flex; gap: 8px; }

.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 22px; border-radius: var(--radius, 8px);
  font-family: var(--font-body, system-ui); font-size: 0.925rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease;
  text-decoration: none; border: none; white-space: nowrap;
}
.btn-primary {
  background: linear-gradient(135deg, var(--gold, #d4a853), var(--grad2, #b8912e));
  color: #0f172a; box-shadow: 0 2px 14px rgba(212, 168, 83, 0.25);
}
.btn-primary:hover { box-shadow: 0 6px 24px rgba(212, 168, 83, 0.4); transform: translateY(-1px); }
.btn-secondary {
  background: transparent; color: var(--fg);
  border: 1px solid var(--border, #334155);
}
.btn-secondary:hover { background: rgba(255,255,255,0.04); border-color: var(--gold); }

/* --- HERO --- */
.hero-wrapper {
  padding: 120px clamp(16px, 6vw, 80px) 80px;
  background: linear-gradient(180deg, rgba(15,23,42,1) 0%, var(--bg, #0f172a) 100%);
  position: relative; overflow: hidden;
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
  background: rgba(212, 168, 83, 0.1); color: var(--gold, #d4a853);
  font-size: 0.78rem; font-weight: 600; letter-spacing: 0.02em;
  width: fit-content; border: 1px solid rgba(212, 168, 83, 0.2);
}
.hero-badge .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--gold, #d4a853); animation: pulse-dot 2s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.35} }

h1 {
  font-family: var(--font-display, system-ui);
  font-size: clamp(2.2rem, 5vw, 3.5rem); font-weight: 700;
  line-height: 1.12; letter-spacing: -0.025em;
}
h1 .em {
  background: linear-gradient(135deg, var(--gold, #d4a853), #e8c478);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-desc { font-size: 1.05rem; color: var(--muted); line-height: 1.7; max-width: 480px; }
.hero-actions { display: flex; gap: 14px; flex-wrap: wrap; }

.creator-note {
  font-size: 0.82rem; color: var(--muted); display: flex; align-items: center; gap: 6px;
}
.creator-note a { color: var(--gold); text-decoration: underline; text-underline-offset: 3px; }
.creator-note a:hover { color: #e8c478; }
.note-icon { font-size: 0.9rem; }

.hero-visual { display: flex; align-items: center; justify-content: center; perspective: 1000px; }
.hero-card-3d {
  width: 100%; max-width: 500px;
  background: var(--surface, #1e293b); border-radius: var(--radius-xl, 16px);
  border: 1px solid var(--border, #334155);
  box-shadow: 0 0 0 1px rgba(51,65,85,0.5), 0 16px 48px rgba(0,0,0,0.5);
  padding: 28px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.hero-card-3d:hover {
  transform: translateY(-4px) rotateX(2deg);
  box-shadow: 0 0 0 1px rgba(212,168,83,0.2), 0 24px 64px rgba(0,0,0,0.6);
}
.hc-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border, #334155); }
.hc-avatar { width: 44px; height: 44px; border-radius: var(--radius-sm, 4px); background: linear-gradient(135deg, rgba(212,168,83,0.2), rgba(184,145,46,0.2)); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
.hc-title { font-weight: 600; font-size: 0.95rem; color: var(--fg); }
.hc-sub { font-size: 0.78rem; color: var(--muted); }
.hc-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.hc-stat { background: var(--bg, #0f172a); border: 1px solid var(--border, #334155); border-radius: var(--radius, 8px); padding: 14px; text-align: center; }
.hc-stat-val { font-size: 1.5rem; font-weight: 700; color: var(--gold, #d4a853); font-family: var(--font-mono, monospace); }
.hc-stat-label { font-size: 0.7rem; color: var(--muted); margin-top: 2px; }
.hc-modules { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.hc-mod { display: flex; align-items: center; gap: 6px; padding: 10px 12px; border-radius: var(--radius-sm, 4px); font-size: 0.78rem; font-weight: 500; background: var(--bg, #0f172a); border: 1px solid var(--border, #334155); transition: background 0.2s, border-color 0.2s; }
.hc-mod:hover { background: rgba(212,168,83,0.08); border-color: rgba(212,168,83,0.25); }
.hc-mod-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.hc-mod-dot.green { background: oklch(56% 0.12 170); }
.hc-mod-dot.blue { background: oklch(58% 0.14 245); }
.hc-mod-dot.orange { background: oklch(62% 0.18 55); }
.hc-mod-dot.purple { background: oklch(56% 0.12 280); }
.hc-mod-dot.pink { background: oklch(58% 0.16 350); }
.hc-mod-dot.cyan { background: oklch(60% 0.12 200); }

/* --- SECTIONS --- */
.section { max-width: 1200px; margin: 0 auto; padding: 80px clamp(16px, 6vw, 80px); }
.section-header { text-align: center; margin-bottom: 56px; display: flex; flex-direction: column; gap: 12px; }
.section-tag {
  font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
  color: var(--gold, #d4a853); background: rgba(212,168,83,0.1);
  border: 1px solid rgba(212,168,83,0.2); padding: 4px 14px; border-radius: 100px;
  width: fit-content; margin: 0 auto;
}
h2 {
  font-family: var(--font-display, system-ui);
  font-size: clamp(1.6rem, 3.5vw, 2.4rem); font-weight: 700;
  letter-spacing: -0.015em; line-height: 1.2;
}
.section-sub { font-size: 1rem; color: var(--muted); max-width: 560px; margin: 0 auto; }

/* --- FEATURE CARDS --- */
.features-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; }
.feature-card {
  background: var(--surface, #1e293b); border-radius: var(--radius-lg, 12px);
  border: 1px solid var(--border, #334155); padding: 32px 28px;
  display: flex; flex-direction: column; gap: 14px; transition: all 0.3s ease;
}
.feature-card:hover {
  transform: translateY(-2px); border-color: rgba(212,168,83,0.4);
  box-shadow: 0 0 0 1px rgba(212,168,83,0.15), 0 12px 32px rgba(0,0,0,0.4);
}
.fc-icon { font-size: 2rem; }
.fc-title { font-family: var(--font-display, system-ui); font-size: 1.1rem; font-weight: 700; letter-spacing: -0.01em; }
.fc-desc { font-size: 0.88rem; color: var(--muted); line-height: 1.6; }
.fc-features { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.fc-features li { font-size: 0.8rem; color: var(--muted); display: flex; align-items: center; gap: 6px; }
.fc-features li::before { content: '›'; color: var(--gold, #d4a853); font-weight: 700; font-size: 1.1em; }

/* --- DEFENSE TIERS --- */
.defense-tiers { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; max-width: 1000px; margin: 0 auto; }
.tier {
  border-radius: var(--radius-lg, 12px); padding: 28px 20px; text-align: center;
  border: 1px solid var(--border, #334155); background: var(--surface, #1e293b);
  transition: all 0.3s ease;
}
.tier:hover { transform: translateY(-3px); border-color: rgba(212,168,83,0.3); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.tier-zero { border-color: rgba(148,163,184,0.2); background: rgba(148,163,184,0.04); }
.tier-low { border-color: rgba(99,179,113,0.3); background: rgba(99,179,113,0.06); }
.tier-mid { border-color: rgba(237,137,54,0.3); background: rgba(237,137,54,0.06); }
.tier-high { border-color: rgba(139,92,246,0.3); background: rgba(139,92,246,0.06); }
.tier-label {
  font-family: var(--font-mono, monospace);
  font-size: 1.4rem; font-weight: 700; margin-bottom: 8px;
}
.tier-zero .tier-label { color: var(--silver, #c0c8d4); }
.tier-low .tier-label { color: #63b371; }
.tier-mid .tier-label { color: #ed8936; }
.tier-high .tier-label { color: #8b5cf6; }
.tier-name { font-weight: 700; font-size: 0.95rem; margin-bottom: 8px; }
.tier-desc { font-size: 0.78rem; color: var(--muted); line-height: 1.5; }

/* --- STEPS FLOW --- */
.steps-flow {
  max-width: 900px; margin: 0 auto; display: flex; align-items: flex-start;
  justify-content: space-between; position: relative;
}
.steps-flow::before {
  content: ''; position: absolute; top: 32px; left: 60px; right: 60px; height: 2px;
  background: var(--border, #334155); z-index: 0;
}
.step {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  position: relative; z-index: 1; text-align: center; flex: 1;
}
.step-num {
  width: 64px; height: 64px; border-radius: 50%;
  background: var(--surface, #1e293b); border: 2px solid var(--border, #334155);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono, monospace); font-size: 1.2rem; font-weight: 700;
  color: var(--gold, #d4a853); transition: all 0.3s ease;
}
.step:hover .step-num {
  background: rgba(212,168,83,0.15); border-color: var(--gold, #d4a853);
  box-shadow: 0 0 20px rgba(212,168,83,0.2);
}
.step-title { font-weight: 700; font-size: 0.95rem; }
.step-desc { font-size: 0.8rem; color: var(--muted); max-width: 180px; }

/* --- CTA --- */
.cta-section { text-align: center; padding: 80px clamp(16px, 6vw, 80px); }
.cta-card {
  max-width: 700px; margin: 0 auto;
  background: linear-gradient(135deg, rgba(212,168,83,0.15), rgba(184,145,46,0.08));
  border: 1px solid rgba(212,168,83,0.3);
  border-radius: var(--radius-xl, 16px); padding: 56px 48px;
  position: relative; overflow: hidden;
  box-shadow: 0 16px 56px rgba(0,0,0,0.3);
}
.cta-card::before {
  content: ''; position: absolute; top: -60px; right: -60px; width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(212,168,83,0.1), transparent 70%); border-radius: 50%;
}
.cta-card h3 {
  font-family: var(--font-display, system-ui);
  font-size: 2rem; font-weight: 700; position: relative; z-index: 1; margin-bottom: 12px;
}
.cta-card p { font-size: 1rem; color: var(--muted); position: relative; z-index: 1; margin-bottom: 28px; }
.btn-cta {
  background: linear-gradient(135deg, var(--gold, #d4a853), var(--grad2, #b8912e));
  color: #0f172a; padding: 12px 28px; font-size: 0.95rem; font-weight: 700;
  box-shadow: 0 4px 16px rgba(212,168,83,0.3); position: relative; z-index: 1;
}
.btn-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(212,168,83,0.4); }

/* --- FOOTER --- */
.footer {
  max-width: 1200px; margin: 0 auto;
  padding: 40px clamp(16px, 6vw, 80px);
  border-top: 1px solid var(--border, #334155);
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px; font-size: 0.85rem; color: var(--muted);
}
.footer-brand { display: flex; align-items: center; gap: 10px; }

/* --- RESPONSIVE --- */
@media (max-width: 1024px) {
  .hero { grid-template-columns: 1fr; gap: 48px; text-align: center; }
  .hero-desc { max-width: 100%; }
  .hero-actions { justify-content: center; }
  .hero-card-3d { max-width: 420px; }
  .features-grid { grid-template-columns: 1fr; }
  .defense-tiers { grid-template-columns: repeat(2, 1fr); }
  .steps-flow { flex-direction: column; align-items: center; gap: 24px; }
  .steps-flow::before { display: none; }
}
@media (max-width: 640px) {
  .nav-links { display: none; }
  .defense-tiers { grid-template-columns: 1fr; }
  .hero-wrapper { padding: 100px 16px 56px; }
  .section, .cta-section { padding: 56px 16px; }
  .cta-card { padding: 40px 24px; }
  .hc-stats { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .hc-modules { grid-template-columns: repeat(2, 1fr); }
}

@media (prefers-reduced-motion: reduce) {
  .hero-card-3d { transition: none; }
  .feature-card { transition: none; }
  .tier { transition: none; }
  .step-num { transition: none; }
  .btn-primary, .btn-cta { transition: none; }
  * { animation-duration: 0.01ms !important; }
}
</style>

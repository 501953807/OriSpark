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
        <li><a href="#how">使用流程</a></li>
        <li><router-link to="/onboarding">新手指引</router-link></li>
      </ul>
      <div class="nav-btns">
        <router-link to="/login" class="btn btn-secondary">登录</router-link>
        <router-link to="/app" class="btn btn-primary">开始创作</router-link>
      </div>
    </nav>

    <!-- HERO -->
    <main>
      <div class="hero-wrapper">
        <div class="hero-bg-deco"></div>
        <div class="hero-bg-deco2"></div>
        <div class="hero">
          <div class="hero-text">
            <div class="hero-badge"><span class="dot"></span> v2.0 · 全面升级</div>
            <h1>让独立创作者<br><span class="em">拥有完整的工具链</span></h1>
            <p class="hero-desc">从作品管理到存证确权、从侵权监测到多平台发布——OriStudio 为独立创作者打造了一个本地运行、全链路闭环的创作助手，数据永远在你手上。</p>
            <div class="hero-actions">
              <router-link to="/app" class="btn btn-primary" style="font-size:1rem;padding:14px 28px;">进入工作台 →</router-link>
              <router-link to="/onboarding" class="btn btn-secondary">新手指引</router-link>
            </div>
          </div>
          <div class="hero-visual">
            <div class="hero-card-3d">
              <div class="hc-header">
                <div class="hc-avatar">🎨</div>
                <div>
                  <div class="hc-title">Morning Studio</div>
                  <div class="hc-sub">今日创作 · 3 个活跃项目</div>
                </div>
              </div>
              <div class="hc-stats">
                <div class="hc-stat"><div class="hc-stat-val">247</div><div class="hc-stat-label">作品总量</div></div>
                <div class="hc-stat"><div class="hc-stat-val">156</div><div class="hc-stat-label">已存证</div></div>
                <div class="hc-stat"><div class="hc-stat-val">12</div><div class="hc-stat-label">上架产品</div></div>
              </div>
              <div class="hc-modules">
                <div class="hc-mod"><span class="hc-mod-dot purple"></span>作品库</div>
                <div class="hc-mod"><span class="hc-mod-dot green"></span>存证中心</div>
                <div class="hc-mod"><span class="hc-mod-dot orange"></span>侵权监测</div>
                <div class="hc-mod"><span class="hc-mod-dot blue"></span>IP 登记</div>
                <div class="hc-mod"><span class="hc-mod-dot pink"></span>供应链</div>
                <div class="hc-mod"><span class="hc-mod-dot cyan"></span>发布变现</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- FEATURES -->
      <section class="section" id="features">
        <div class="section-header">
          <div class="section-tag">六大核心模块</div>
          <h2>全链路覆盖，不重复造轮子</h2>
          <p class="section-sub">一个工具覆盖创作→存证→监测→登记→生产→上架全流程，所有数据本地存储，隐私安全可控。</p>
        </div>
        <div class="features-grid">
          <router-link to="/app/works" class="feature-card" style="text-decoration:none;color:inherit;">
            <div class="fc-icon g1">📂</div>
            <div class="fc-title">作品管理</div>
            <div class="fc-desc">拖拽导入、自动分类、元数据提取、版本快照——像管理代码一样管理你的创作资产。</div>
            <ul class="fc-features"><li>批量导入 + 自动去重</li><li>FTS5 全文搜索</li><li>图片/音频/视频预览</li></ul>
          </router-link>
          <router-link to="/app/notary" class="feature-card" style="text-decoration:none;color:inherit;">
            <div class="fc-icon g2">🔒</div>
            <div class="fc-title">存证确权</div>
            <div class="fc-desc">本地 SHA-256 哈希 + 多平台区块链存证，一键生成 PDF 证书，保护你的版权。</div>
            <ul class="fc-features"><li>版权家/蚂蚁链/至信链</li><li>PDF 证书 + 验证二维码</li><li>C2PA 元数据嵌入</li></ul>
          </router-link>
          <router-link to="/app/monitor" class="feature-card" style="text-decoration:none;color:inherit;">
            <div class="fc-icon g3">🛡️</div>
            <div class="fc-title">侵权监测</div>
            <div class="fc-desc">百度识图 + Google Vision 定时扫描，发现侵权自动生成投诉材料。</div>
            <ul class="fc-features"><li>以图搜图 + 文本查重</li><li>Celery 定时扫描</li><li>维权材料一键打包</li></ul>
          </router-link>
          <router-link to="/app/ipr" class="feature-card" style="text-decoration:none;color:inherit;">
            <div class="fc-icon g4">📋</div>
            <div class="fc-title">IP 登记</div>
            <div class="fc-desc">版权/商标/专利申请指引，材料清单 + 官方链接，帮助你顺利注册。</div>
            <ul class="fc-features"><li>材料清单 + 费用参考</li><li>商标类别推荐</li><li>进度追踪 + 续展提醒</li></ul>
          </router-link>
          <router-link to="/app/supply" class="feature-card" style="text-decoration:none;color:inherit;">
            <div class="fc-icon g5">💰</div>
            <div class="fc-title">创作变现引擎</div>
            <div class="fc-desc">5条变现路径 × 10种材质 × 60+产品品类，从设计到收入的完整工作台。</div>
            <ul class="fc-features"><li>POD按需打印 / 众筹 / IP授权</li><li>全球60+产品品类</li><li>收入追踪 + 趋势分析</li></ul>
          </router-link>
          <router-link to="/app/publish" class="feature-card" style="text-decoration:none;color:inherit;">
            <div class="fc-icon g6">📊</div>
            <div class="fc-title">产品数据中心</div>
            <div class="fc-desc">JSON Product Feed + MCP Server，标准化输出供ERP/AI Agent消费。</div>
            <ul class="fc-features"><li>多平台风格AI描述生成</li><li>Verified 原创认证徽章</li><li>MCP Server 标准AI协议</li></ul>
          </router-link>
        </div>
      </section>

      <!-- PROOF -->
      <div class="proof-section">
        <div class="proof-grid">
          <div class="proof-stat"><div class="proof-num">100%</div><div class="proof-label">数据本地存储</div></div>
          <div class="proof-stat"><div class="proof-num">6</div><div class="proof-label">核心模块</div></div>
          <div class="proof-stat"><div class="proof-num">3</div><div class="proof-label">分发方式</div></div>
          <div class="proof-stat"><div class="proof-num">0</div><div class="proof-label">服务器依赖</div></div>
        </div>
      </div>

      <!-- HOW IT WORKS -->
      <section class="section" id="how">
        <div class="section-header">
          <div class="section-tag">使用流程</div>
          <h2>全流程闭环</h2>
          <p class="section-sub">四步搭建你的创作者工作流，从资产管理的起点到商业变现的终点。</p>
        </div>
        <div class="steps-flow">
          <div class="step">
            <div class="step-num">1</div>
            <div class="step-title">导入作品</div>
            <div class="step-desc">批量导入 · 自动分类 · SHA-256 哈希</div>
          </div>
          <div class="step">
            <div class="step-num">2</div>
            <div class="step-title">存证确权</div>
            <div class="step-desc">区块链存证 · PDF 证书 · C2PA 元数据</div>
          </div>
          <div class="step">
            <div class="step-num">3</div>
            <div class="step-title">监测维权</div>
            <div class="step-desc">定时扫描 · 侵权发现 · 证据打包</div>
          </div>
          <div class="step">
            <div class="step-num">4</div>
            <div class="step-title">发布变现</div>
            <div class="step-desc">AI 描述 · CSV 导出 · 一键上架</div>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="cta-section">
        <div class="cta-card">
          <h3>准备好开始了吗？</h3>
          <p>免费、不锁数据、开源可审计。开始你的创作之旅。</p>
          <router-link to="/app" class="btn btn-cta">🚀 开始创作</router-link>
        </div>
      </section>
    </main>

    <!-- FOOTER -->
    <footer class="footer">
      <div class="footer-brand">
        <div class="brand-logo" style="width:28px;height:28px;font-size:0.8rem;">O</div>
        OriStudio — 创作者全链路助手
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
/* ====== 完全从 design/landing.html 提取的设计 ====== */
.landing-page { background: var(--bg); color: var(--fg); line-height: 1.6; overflow-x: hidden; }

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
  transition: all 0.35s ease;
}
.nav.scrolled { box-shadow: 0 1px 0 oklch(0 0 0 / 0.04), 0 4px 24px oklch(0 0 0 / 0.06); }

.brand {
  display: flex; align-items: center; gap: 10px;
  font-family: var(--font-display); font-weight: 700; font-size: 1.35rem;
  letter-spacing: -0.015em; color: var(--fg); text-decoration: none;
}
.brand-logo {
  width: 36px; height: 36px; border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 1.1rem; font-weight: 800;
  box-shadow: 0 2px 12px oklch(56% 0.12 170 / 0.3);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.brand:hover .brand-logo { transform: scale(1.08) rotate(-2deg); box-shadow: 0 4px 20px oklch(56% 0.12 170 / 0.45); }

.nav-links { display: flex; gap: 32px; align-items: center; list-style: none; }
.nav-links a {
  text-decoration: none; color: var(--muted); font-size: 0.925rem;
  font-weight: 500; transition: color 0.2s; position: relative;
}
.nav-links a:hover { color: var(--fg); }
.nav-links a::after {
  content: ''; position: absolute; bottom: -4px; left: 0; width: 0; height: 2px;
  background: var(--accent); border-radius: 1px; transition: width 0.25s ease;
}
.nav-links a:hover::after { width: 100%; }
.nav-btns { display: flex; gap: 8px; }

.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 22px; border-radius: var(--radius);
  font-family: var(--font-body); font-size: 0.925rem; font-weight: 600;
  cursor: pointer; transition: all 0.25s ease;
  text-decoration: none; border: none; white-space: nowrap;
}
.btn-primary {
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  color: #fff; box-shadow: 0 2px 14px oklch(56% 0.12 170 / 0.3);
  position: relative; overflow: hidden;
}
.btn-primary::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, transparent 40%, oklch(100% 0 0 / 0.15) 50%, transparent 60%);
  transform: translateX(-100%); transition: transform 0.6s ease;
}
.btn-primary:hover::before { transform: translateX(100%); }
.btn-primary:hover { box-shadow: 0 6px 24px oklch(56% 0.12 170 / 0.45); transform: translateY(-1px); }
.btn-secondary {
  background: var(--surface); color: var(--fg);
  border: 1px solid var(--border);
}
.btn-secondary:hover { background: oklch(96% 0.004 240); border-color: var(--muted); }

/* --- HERO --- */
.hero-wrapper {
  padding: 120px clamp(16px, 6vw, 80px) 80px;
  background: linear-gradient(180deg, oklch(96% 0.006 240) 0%, var(--bg) 100%);
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
  background: oklch(56% 0.12 170 / 0.1); color: var(--accent);
  font-size: 0.8rem; font-weight: 600; letter-spacing: 0.02em;
  width: fit-content;
}
.hero-badge .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); animation: pulse-dot 2s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.35} }

h1 { font-family: var(--font-display); font-size: clamp(2.5rem, 5.5vw, 4rem); font-weight: 700; line-height: 1.12; letter-spacing: -0.025em; }
h1 .em { background: linear-gradient(135deg, var(--grad1), var(--grad2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-desc { font-size: 1.15rem; color: var(--muted); line-height: 1.7; max-width: 480px; }
.hero-actions { display: flex; gap: 14px; flex-wrap: wrap; }

.hero-visual { display: flex; align-items: center; justify-content: center; perspective: 1000px; }
.hero-card-3d {
  width: 100%; max-width: 520px;
  background: var(--surface); border-radius: var(--radius-xl);
  box-shadow: 0 0 0 1px oklch(0 0 0 / 0.04), 0 8px 32px oklch(0 0 0 / 0.06), 0 24px 80px oklch(0 0 0 / 0.08);
  padding: 28px;
  transform: rotateY(-4deg) rotateX(2deg);
  transition: transform 0.6s ease, box-shadow 0.6s ease;
}
.hero-card-3d:hover { transform: rotateY(-1deg) rotateX(0.5deg); box-shadow: 0 0 0 1px oklch(0 0 0 / 0.05), 0 12px 40px oklch(0 0 0 / 0.08), 0 32px 100px oklch(0 0 0 / 0.12); }
.hc-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
.hc-avatar { width: 44px; height: 44px; border-radius: var(--radius-sm); background: linear-gradient(135deg, oklch(56% 0.12 170 / 0.2), oklch(62% 0.16 260 / 0.2)); display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
.hc-title { font-weight: 600; font-size: 0.95rem; }
.hc-sub { font-size: 0.78rem; color: var(--muted); }
.hc-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.hc-stat { background: oklch(96% 0.006 240); border-radius: var(--radius); padding: 14px; text-align: center; transition: transform 0.2s ease, box-shadow 0.2s ease; }
.dark .hc-stat { background: oklch(24% 0.01 240); }
.hc-stat:hover { transform: translateY(-2px); box-shadow: 0 4px 16px oklch(0 0 0 / 0.06); }
.hc-stat-val { font-family: var(--font-display); font-size: 1.6rem; font-weight: 700; color: var(--accent); }
.hc-stat-label { font-size: 0.7rem; color: var(--muted); margin-top: 2px; }
.hc-modules { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.hc-mod { display: flex; align-items: center; gap: 6px; padding: 10px 12px; border-radius: var(--radius-sm); font-size: 0.78rem; font-weight: 500; background: oklch(96% 0.006 240); transition: background 0.2s, transform 0.2s; }
.dark .hc-mod { background: oklch(24% 0.01 240); }
.hc-mod:hover { background: oklch(56% 0.12 170 / 0.08); transform: translateY(-1px); }
.hc-mod-dot { width: 8px; height: 8px; border-radius: 3px; }
.hc-mod-dot.purple { background: oklch(56% 0.12 280); }
.hc-mod-dot.green { background: oklch(56% 0.12 170); }
.hc-mod-dot.orange { background: oklch(62% 0.18 55); }
.hc-mod-dot.blue { background: oklch(58% 0.14 245); }
.hc-mod-dot.pink { background: oklch(58% 0.16 350); }
.hc-mod-dot.cyan { background: oklch(60% 0.12 200); }

/* --- SECTIONS --- */
.section { max-width: 1200px; margin: 0 auto; padding: 80px clamp(16px, 6vw, 80px); }
.section-header { text-align: center; margin-bottom: 56px; display: flex; flex-direction: column; gap: 12px; }
.section-tag { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: var(--accent); }
h2 { font-family: var(--font-display); font-size: clamp(1.8rem, 3.8vw, 2.8rem); font-weight: 700; letter-spacing: -0.015em; line-height: 1.2; }
.section-sub { font-size: 1.05rem; color: var(--muted); max-width: 560px; margin: 0 auto; }

/* --- FEATURE CARDS --- */
.features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.feature-card {
  background: var(--surface); border-radius: var(--radius-lg);
  border: 1px solid var(--border); padding: 32px 28px;
  display: flex; flex-direction: column; gap: 14px;
  transition: all 0.35s ease; cursor: default; position: relative; overflow: hidden;
}
.feature-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--grad1), var(--grad2));
  opacity: 0; transition: opacity 0.35s ease;
}
.feature-card:hover { transform: translateY(-6px); box-shadow: 0 16px 48px oklch(0 0 0 / 0.08); border-color: transparent; }
.feature-card:hover::before { opacity: 1; }
.fc-icon { width: 48px; height: 48px; border-radius: var(--radius); display: flex; align-items: center; justify-content: center; font-size: 1.4rem; }
.fc-icon.g1 { background: oklch(56% 0.12 170 / 0.12); color: oklch(56% 0.12 170); }
.fc-icon.g2 { background: oklch(62% 0.16 260 / 0.12); color: oklch(62% 0.16 260); }
.fc-icon.g3 { background: oklch(62% 0.18 55 / 0.12); color: oklch(62% 0.18 55); }
.fc-icon.g4 { background: oklch(58% 0.14 245 / 0.12); color: oklch(58% 0.14 245); }
.fc-icon.g5 { background: oklch(58% 0.16 350 / 0.12); color: oklch(58% 0.16 350); }
.fc-icon.g6 { background: oklch(60% 0.12 200 / 0.12); color: oklch(60% 0.12 200); }
.fc-title { font-family: var(--font-display); font-size: 1.15rem; font-weight: 700; letter-spacing: -0.01em; }
.fc-desc { font-size: 0.9rem; color: var(--muted); line-height: 1.6; }
.fc-features { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.fc-features li { font-size: 0.82rem; color: var(--muted); display: flex; align-items: center; gap: 6px; }
.fc-features li::before { content: '→'; color: var(--accent); font-weight: 600; }

/* --- PROOF --- */
.proof-section { background: linear-gradient(180deg, var(--surface) 0%, oklch(96% 0.006 240) 100%); padding: 80px clamp(16px, 6vw, 80px); }
.proof-grid { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.proof-stat { text-align: center; }
.proof-num { font-family: var(--font-display); font-size: 2.6rem; font-weight: 700; background: linear-gradient(135deg, var(--grad1), var(--grad2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.proof-label { font-size: 0.85rem; color: var(--muted); margin-top: 4px; }

/* --- STEPS FLOW --- */
.steps-flow {
  max-width: 900px; margin: 0 auto; display: flex; align-items: flex-start;
  justify-content: space-between; position: relative;
}
.steps-flow::before {
  content: ''; position: absolute; top: 32px; left: 60px; right: 60px; height: 2px;
  background: var(--border); z-index: 0;
}
.step {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  position: relative; z-index: 1; text-align: center; flex: 1;
}
.step-num {
  width: 64px; height: 64px; border-radius: 50%;
  background: var(--surface); border: 2px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-size: 1.3rem; font-weight: 700;
  color: var(--accent); transition: all 0.35s ease;
}
.step:hover .step-num {
  background: var(--accent); color: #fff; border-color: var(--accent);
  box-shadow: 0 8px 28px oklch(56% 0.12 170 / 0.3); transform: scale(1.08);
}
.step-title { font-weight: 700; font-size: 0.95rem; }
.step-desc { font-size: 0.8rem; color: var(--muted); }

/* --- CTA --- */
.cta-section { text-align: center; padding: 80px clamp(16px, 6vw, 80px); }
.cta-card {
  max-width: 700px; margin: 0 auto;
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  border-radius: var(--radius-xl); padding: 56px 48px; color: #fff;
  position: relative; overflow: hidden;
  box-shadow: 0 16px 56px oklch(56% 0.12 170 / 0.3);
}
.cta-card::before { content: ''; position: absolute; top: -60px; right: -60px; width: 200px; height: 200px; background: oklch(100% 0 0 / 0.08); border-radius: 50%; }
.cta-card::after { content: ''; position: absolute; bottom: -40px; left: -40px; width: 140px; height: 140px; background: oklch(100% 0 0 / 0.06); border-radius: 50%; }
.cta-card h3 { font-family: var(--font-display); font-size: 2rem; font-weight: 700; position: relative; z-index: 1; margin-bottom: 12px; }
.cta-card p { font-size: 1.05rem; opacity: 0.85; position: relative; z-index: 1; margin-bottom: 28px; }
.btn-cta { background: #fff; color: var(--accent); padding: 12px 28px; font-size: 0.95rem; font-weight: 700; box-shadow: 0 4px 16px oklch(0 0 0 / 0.15); position: relative; z-index: 1; }
.btn-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 28px oklch(0 0 0 / 0.2); }

/* --- FOOTER --- */
.footer {
  max-width: 1200px; margin: 0 auto;
  padding: 40px clamp(16px, 6vw, 80px);
  border-top: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 16px; font-size: 0.85rem; color: var(--muted);
}
.footer-brand { display: flex; align-items: center; gap: 10px; }

/* --- RESPONSIVE --- */
@media (max-width: 1024px) {
  .hero { grid-template-columns: 1fr; gap: 48px; text-align: center; }
  .hero-desc { max-width: 100%; }
  .hero-actions { justify-content: center; }
  .hero-card-3d { transform: none; max-width: 420px; }
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .proof-grid { grid-template-columns: repeat(2, 1fr); }
  .steps-flow { flex-direction: column; align-items: center; gap: 24px; }
  .steps-flow::before { display: none; }
}
@media (max-width: 640px) {
  .nav-links { display: none; }
  .features-grid { grid-template-columns: 1fr; }
  .proof-grid { grid-template-columns: repeat(2, 1fr); }
  .hero-wrapper { padding: 100px 16px 56px; }
  .section, .cta-section { padding: 56px 16px; }
  .proof-section { padding: 56px 16px; }
  .cta-card { padding: 40px 24px; }
  .hc-stats { grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .hc-modules { grid-template-columns: repeat(2, 1fr); }
}
</style>

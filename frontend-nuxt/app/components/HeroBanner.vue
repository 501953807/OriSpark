<template>
  <section class="hero-banner">
    <div class="hero-content">
      <h1 class="hero-title">AI 时代的创作者信任枢纽</h1>
      <p class="hero-subtitle">
        从创作前风险预警到合约撮合变现，为独立创作者提供全流程权益保护与多边撮合平台
      </p>
      <div class="hero-actions">
        <a href="https://studio.orispark.local" target="_blank" class="btn-hero">
          进入 OriStudio
        </a>
        <NuxtLink to="/gallery" class="btn-hero-secondary">
          浏览作品画廊
        </NuxtLink>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
</script>

<style scoped>
.hero-banner {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: #fff;
  padding: 80px 32px;
  text-align: center;
}

.hero-title {
  font-size: 40px;
  font-weight: 700;
  margin: 0 0 16px;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: 18px;
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto 32px;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-hero {
  padding: 12px 32px;
  background: #fff;
  color: #059669;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}

.btn-hero:hover {
  background: #f0fdf4;
}

.btn-hero-secondary {
  padding: 12px 32px;
  background: transparent;
  color: #fff;
  border: 2px solid #fff;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}

.btn-hero-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 28px;
  }

  .hero-subtitle {
    font-size: 16px;
  }
}
</style>

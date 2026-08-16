<!-- app/components/HeroBanner.vue -->
<script setup lang="ts">
</script>

<template>
  <section class="hero-banner">
    <div class="hero-content">
      <h1 class="hero-title">
        OriSpark — AI 时代的创作者信任枢纽
      </h1>
      <p class="hero-subtitle">
        从创作前风险预警到合约撮合变现，为独立创作者提供全流程权益保护与多边撮合平台
      </p>
      <div class="hero-actions">
        <a href="https://studio.orispark.local" target="_blank" class="btn-hero">
          进入 OriSpark
        </a>
        <NuxtLink to="/gallery" class="btn-hero-secondary">
          浏览作品画廊
        </NuxtLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero-banner {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #0f172a;
}

.hero-content {
  position: relative;
  z-index: 10;
  text-align: center;
  padding: 2rem;
  max-width: 900px;
  width: 100%;
}

.hero-title {
  font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: clamp(2.5rem, 5vw, 4rem);
  font-weight: 700;
  margin: 0 0 1.5rem;
  line-height: 1.1;
  background: linear-gradient(135deg, #ffffff, #e0e7ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-family: 'Merriweather', Georgia, serif;
  font-size: clamp(1.1rem, 2.5vw, 1.3rem);
  color: var(--m-grey-300);
  margin: 0 0 2.5rem;
  line-height: 1.6;
  opacity: 0.95;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.btn-hero {
  padding: 0.875rem 2rem;
  background: var(--motion-brand-linear-gradient, linear-gradient(135deg, var(--m-primary-dark), var(--m-primary)));
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
}

.btn-hero:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(14, 165, 233, 0.4);
}

.btn-hero:active {
  transform: translateY(-1px) scale(0.98);
}

.btn-hero-secondary {
  padding: 0.875rem 2rem;
  background: transparent;
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.btn-hero-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.6);
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }

  .hero-subtitle {
    font-size: 1rem;
  }

  .hero-actions {
    flex-direction: column;
    align-items: center;
  }

  .btn-hero, .btn-hero-secondary {
    width: 100%;
    max-width: 300px;
  }
}
</style>

<!-- app/components/HeroBanner.vue -->
<script setup lang="ts">
import { useMotionStore } from '@/stores/motion'
import ThreeScene from '@/components/ThreeScene.vue'
import DynamicWaveFill from '@/components/DynamicWaveFill.vue'

const motionStore = useMotionStore()
</script>

<template>
  <section class="hero-banner">
    <!-- Three.js 粒子背景 -->
    <ThreeScene v-if="motionStore.shouldAnimate" />

    <!-- SVG 波浪覆盖层 -->
    <DynamicWaveFill v-if="motionStore.immersiveEnabled" />

    <!-- 内容层 -->
    <div class="hero-content">
      <h1 class="hero-title" :class="{ 'brand-entrance': motionStore.shouldAnimate }">
        OriSpark — AI 时代的创作者信任枢纽
      </h1>
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
  color: #cbd5e1;
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
  background: var(--motion-brand-linear-gradient, linear-gradient(135deg, #0ea5e9, #3b82f6));
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
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
  transition: all 0.3s ease;
}

.btn-hero-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

/* 品牌入口动画：蓝脉流动效应 */
.brand-entrance {
  animation: brandEntrance 1.2s ease-out forwards;
}

@keyframes brandEntrance {
  0% {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  20% {
    transform: translateY(10px) scale(1.02);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 按钮入场序列 */
.btn-hero, .btn-hero-secondary {
  animation: buttonEntrance 1s ease-out forwards;
  opacity: 0;
}

.btn-hero { animation-delay: 0.3s; }
.btn-hero-secondary { animation-delay: 0.5s; }

@keyframes buttonEntrance {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 减速模式时简化动画 */
@media (prefers-reduced-motion: reduce) {
  .brand-entrance, .btn-hero, .btn-hero-secondary {
    animation: none !important;
    transition: none !important;
  }

  .btn-hero { opacity: 1; transform: none; }
  .btn-hero-secondary { opacity: 1; transform: none; }
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

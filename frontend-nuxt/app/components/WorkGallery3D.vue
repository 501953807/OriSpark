<!-- app/components/WorkGallery3D.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Work } from '~/types/public'
import GalleryCard from '@/components/GalleryCard.vue'

const works = ref<Work[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

try {
  const res = await fetchPublicWorks({ limit: '6' })
  works.value = (res ?? []) as Work[]
} catch (e) {
  error.value = e instanceof Error ? e.message : 'Failed to load works'
} finally {
  loading.value = false
}

const featuredWorks = computed(() => works.value.slice(0, 6))
</script>

<template>
  <section class="gallery-section-3d">
    <div class="section-header-3d">
      <h2 class="section-title-3d">精选作品画廊</h2>
      <NuxtLink to="/gallery" class="view-all-3d">查看全部 →</NuxtLink>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else class="works-grid-3d">
      <GalleryCard
        v-for="work in featuredWorks"
        :key="work.id"
        :title="work.title || '未命名作品'"
        :thumbnail="work.thumbnail || '/images/placeholder-work.svg'"
        :id="work.id"
      />
    </div>
  </section>
</template>

<style scoped>
.gallery-section-3d {
  padding: 48px 32px;
  background: white;
}

.section-header-3d {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 32px;
}

.section-title-3d {
  font-family: 'Satoshi', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.view-all-3d {
  color: var(--brand-primary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition: color 0.3s ease;
}

.view-all-3d:hover {
  color: var(--brand-primary-dark);
}

/* 3D 画廊容器 - 应用透视效果 */
.works-grid-3d {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  perspective: 1500px; /* 为卡片提供3D空间 */
}

/* 卡片入场动画序列 */
.works-grid-3d .gallery-card {
  animation: cardEntrance 0.6s ease-out forwards;
  opacity: 0;
  transform: translateY(30px);
}

.works-grid-3d .gallery-card:nth-child(1) { animation-delay: 0.1s; }
.works-grid-3d .gallery-card:nth-child(2) { animation-delay: 0.2s; }
.works-grid-3d .gallery-card:nth-child(3) { animation-delay: 0.3s; }
.works-grid-3d .gallery-card:nth-child(4) { animation-delay: 0.4s; }
.works-grid-3d .gallery-card:nth-child(5) { animation-delay: 0.5s; }
.works-grid-3d .gallery-card:nth-child(6) { animation-delay: 0.6s; }

@keyframes cardEntrance {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 减速模式时禁用动画 */
@media (prefers-reduced-motion: reduce) {
  .works-grid-3d .gallery-card {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
}

/* 加载状态骨架屏 */
.loading-state {
  text-align: center;
  color: #6b7280;
  padding: 48px 0;
  font-size: 16px;
}

.error-state {
  text-align: center;
  color: #ef4444;
  padding: 48px 0;
  font-size: 16px;
}

@media (max-width: 768px) {
  .works-grid-3d {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .section-header-3d {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .works-grid-3d {
    grid-template-columns: 1fr;
  }
}
</style>

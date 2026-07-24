<template>
  <section class="gallery-section">
    <div class="section-header">
      <h2 class="section-title">精选作品画廊</h2>
      <NuxtLink to="/gallery" class="view-all">查看全部 →</NuxtLink>
    </div>
    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else class="works-grid">
      <div
        v-for="work in featuredWorks"
        :key="work.id"
        class="work-card"
      >
        <div class="work-thumbnail">
          <span class="placeholder-icon">&#9998;</span>
        </div>
        <div class="work-info">
          <h3 class="work-title">{{ work.title }}</h3>
          <p class="work-creator">by {{ work.creator_name || '创作者' }}</p>
          <div class="work-tags">
            <span v-for="tag in work.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { Work } from '~/types/public'

const works = ref<Work[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

try {
  loading.value = true
  const res = await fetchPublicWorks({ limit: '6' })
  works.value = (res ?? []) as Work[]
} catch (e) {
  error.value = e instanceof Error ? e.message : 'Failed to load works'
} finally {
  loading.value = false
}

const featuredWorks = computed(() => works.value.slice(0, 6))
</script>

<style scoped>
.gallery-section {
  padding: 48px 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto 32px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.view-all {
  color: #059669;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.works-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.work-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
}

.work-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.work-thumbnail {
  height: 180px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: #d1d5db;
}

.work-info {
  padding: 16px;
}

.work-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 4px;
}

.work-creator {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 8px;
}

.work-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  padding: 2px 8px;
  background: #ecfdf5;
  color: #059669;
  border-radius: 4px;
  font-size: 12px;
}

.loading-state,
.error-state {
  text-align: center;
  color: #6b7280;
  padding: 48px 0;
}

@media (max-width: 768px) {
  .works-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .works-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<template>
  <div class="page-work-detail">
    <NuxtLink to="/gallery" class="back-link">&larr; 返回画廊</NuxtLink>
    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else-if="work" class="work-detail">
      <div class="work-thumbnail">
        <span class="placeholder-icon">&#9998;</span>
      </div>
      <div class="work-info">
        <h1 class="work-title">{{ work.title }}</h1>
        <p class="work-creator">by {{ work.creator_name || '创作者' }}</p>
        <p class="work-desc">{{ work.description }}</p>
        <div class="work-tags">
          <span v-for="tag in work.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Work } from '~/types/public'

const route = useRoute()
const workId = route.params.id as string

const work = ref<Work | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

try {
  loading.value = true
  const res = await fetchPublicWork(workId)
  work.value = (res ?? null) as Work | null
} catch (e) {
  error.value = e instanceof Error ? e.message : 'Failed to load work'
} finally {
  loading.value = false
}

useHead({
  title: () => work.value?.title ?? '作品详情 — OriSpark',
})
</script>

<style scoped>
.page-work-detail {
  padding: 32px;
  max-width: 800px;
  margin: 0 auto;
}

.back-link {
  color: #059669;
  font-size: 14px;
  text-decoration: none;
}

.work-detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  margin-top: 24px;
}

.work-thumbnail {
  height: 300px;
  background: #f3f4f6;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64px;
  color: #d1d5db;
}

.work-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px;
}

.work-creator {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 16px;
}

.work-desc {
  font-size: 14px;
  color: #374151;
  line-height: 1.6;
  margin: 0 0 16px;
}

.work-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  padding: 4px 10px;
  background: #ecfdf5;
  color: #059669;
  border-radius: 4px;
  font-size: 13px;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 48px 0;
  color: #6b7280;
}

.error-state {
  color: #ef4444;
}

@media (max-width: 768px) {
  .work-detail {
    grid-template-columns: 1fr;
  }
}
</style>

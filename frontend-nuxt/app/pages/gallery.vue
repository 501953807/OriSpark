<template>
  <div class="page-gallery">
    <h1 class="page-title">作品画廊</h1>

    <div class="filter-bar">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索作品..."
        class="search-input"
      />
      <select v-model="selectedCategory" class="category-select">
        <option value="">全部分类</option>
        <option value="image">插画/摄影</option>
        <option value="video">视频</option>
        <option value="audio">音乐</option>
        <option value="document">文档</option>
        <option value="code">代码</option>
        <option value="design">设计</option>
      </select>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else class="gallery-grid">
      <div
        v-for="work in works"
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
            <span v-for="tag in work.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!works.length && !loading" class="empty-state">
      暂无作品
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Work } from '~/types/public'

useHead({
  title: '作品画廊 — OriSpark',
})

const searchQuery = ref('')
const selectedCategory = ref('')
const works = ref<Work[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

try {
  loading.value = true
  const params: Record<string, string> = { limit: '50' }
  if (searchQuery.value) params.search = searchQuery.value
  if (selectedCategory.value) params.category = selectedCategory.value
  const res = await fetchPublicWorks(params)
  works.value = (res ?? []) as Work[]
} catch (e) {
  error.value = e instanceof Error ? e.message : 'Failed to load gallery'
} finally {
  loading.value = false
}
</script>

<style scoped>
.page-gallery {
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 24px;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.search-input {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}

.category-select {
  padding: 10px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.work-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: #6b7280;
}

.error-state {
  color: #ef4444;
}

@media (max-width: 768px) {
  .gallery-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .gallery-grid {
    grid-template-columns: 1fr;
  }
}
</style>

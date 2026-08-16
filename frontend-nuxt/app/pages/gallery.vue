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
definePageMeta({ layout: 'materio-topnav' })
import { ref, onMounted, watch } from 'vue'
import type { Work } from '~/types/public'
import { fetchPublicWorks } from '~/composables/usePublicApi'

useHead({
  title: '作品画廊 — OriSpark',
})

const searchQuery = ref('')
const selectedCategory = ref('')
const works = ref<Work[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function loadWorks() {
  loading.value = true
  error.value = null
  try {
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
}

onMounted(loadWorks)
watch([searchQuery, selectedCategory], loadWorks)
</script>

<style scoped>
.page-gallery {
  padding: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--m-on-surface);
  padding: 0 24px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 0 24px;
}

.search-input {
  flex: 1;
  padding: 8px 14px;
  border: 1px solid var(--m-border);
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  color: var(--m-on-surface);
  background: #FFFFFF;
}

.category-select {
  padding: 8px 14px;
  border: 1px solid var(--m-border);
  border-radius: 6px;
  font-size: 14px;
  background: #FFFFFF;
  color: var(--m-on-surface);
  font-family: inherit;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  padding: 0 24px;
}

.work-card {
  background: #FFFFFF;
  border-radius: 6px;
  border: none;
  box-shadow: var(--m-shadow-md);
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.work-card:hover {
  box-shadow: rgba(46, 38, 61, 0.2) 0px 4px 10px 0px;
}

.work-thumbnail {
  height: 180px;
  background: var(--m-grey-100);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: rgba(46, 38, 61, 0.2);
}

.work-info {
  padding: 16px;
}

.work-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 4px;
  color: var(--m-on-surface);
}

.work-creator {
  font-size: 13px;
  color: var(--m-grey-500);
  margin: 0 0 8px;
}

.work-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  padding: 2px 8px;
  background: rgba(140, 87, 255, 0.1);
  color: var(--m-primary);
  border-radius: 100px;
  font-size: 12px;
  font-weight: 500;
}

.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--m-grey-500);
}

.error-state {
  color: var(--m-error);
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

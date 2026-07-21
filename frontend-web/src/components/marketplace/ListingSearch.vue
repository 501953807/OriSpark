<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { supplyApi } from '@/api/supply'
import { listingBatchApi } from '@/api/marketplace'
import type { ListingDetail } from '@/types/supply'

const listings = ref<ListingDetail[]>([])
const loading = ref(true)
const searchParams = ref({
  category: '', creator_type: '', price_min: '', price_max: '', tags: '', sort_by: 'created_at',
})

async function loadListings() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (searchParams.value.category) params.category = searchParams.value.category
    if (searchParams.value.creator_type) params.creator_type = searchParams.value.creator_type
    if (searchParams.value.price_min) params.price_min_yuan = searchParams.value.price_min
    if (searchParams.value.price_max) params.price_max_yuan = searchParams.value.price_max
    if (searchParams.value.tags) params.tags = searchParams.value.tags
    if (searchParams.value.sort_by) params.sort_by = searchParams.value.sort_by

    const res = await listingBatchApi.search(params)
    listings.value = res.data as ListingDetail[]
  } catch { /* handled */ } finally { loading.value = false }
}

function doSearch() { loadListings() }

onMounted(loadListings)
</script>

<template>
  <div class="listing-search card">
    <h3>高级搜索</h3>
    <div class="search-bar">
      <input v-model="searchParams.category" placeholder="分类" />
      <input v-model="searchParams.creator_type" placeholder="创作者类型" />
      <input v-model.number="searchParams.price_min" type="number" placeholder="最低价" />
      <input v-model.number="searchParams.price_max" type="number" placeholder="最高价" />
      <input v-model="searchParams.tags" placeholder="标签（逗号分隔）" />
      <select v-model="searchParams.sort_by">
        <option value="created_at">最新</option>
        <option value="price_asc">价格升序</option>
        <option value="price_desc">价格降序</option>
        <option value="score">匹配分</option>
      </select>
      <button class="btn btn-primary" @click="doSearch">搜索</button>
    </div>

    <div v-if="loading" class="loading">搜索中...</div>
    <div v-else-if="listings.length === 0" class="empty-state">暂无结果</div>
    <div v-else class="listing-grid">
      <div v-for="l in listings" :key="l.id" class="listing-card">
        <h4>{{ l.title }}</h4>
        <p class="price">¥{{ l.asking_price_yuan?.toLocaleString() ?? '--' }}</p>
        <span class="status-chip" :class="l.status">{{ l.status }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-bar { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.search-bar input, .search-bar select { padding: 8px; border: 1px solid var(--border); border-radius: 6px; }
.listing-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.listing-card { padding: 12px; border: 1px solid var(--border); border-radius: 8px; }
.price { font-size: 1.2rem; font-weight: 600; color: #059669; margin: 4px 0; }
.status-chip { font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; }
</style>

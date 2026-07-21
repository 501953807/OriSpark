<template>
  <div class="brand-panel">
    <!-- Header + Register form -->
    <div class="brand-header card">
      <div class="brand-header-top">
        <h3 class="section-title">品牌监测</h3>
        <button class="btn btn-primary" @click="showForm = !showForm">
          {{ showForm ? '取消' : '+ 注册品牌' }}
        </button>
      </div>

      <!-- Registration form -->
      <form v-if="showForm" class="brand-form" @submit.prevent="handleRegister">
        <div class="form-row">
          <div class="form-field">
            <label>品牌名称 *</label>
            <input v-model="form.brand_name" type="text" placeholder="输入品牌名称" required />
          </div>
          <div class="form-field">
            <label>关键词 (逗号分隔)</label>
            <input v-model="form.keywordsStr" type="text" placeholder="品牌, logo, 产品名" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-field">
            <label>监测平台</label>
            <div class="platform-checks">
              <label v-for="p in platforms" :key="p.value" class="check-label">
                <input type="checkbox" :value="p.value" v-model="form.platforms" />
                {{ p.label }}
              </label>
            </div>
          </div>
        </div>
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="!form.brand_name.trim()">注册品牌</button>
        </div>
      </form>
    </div>

    <!-- Brand cards -->
    <div v-if="brands.length === 0" class="empty-hint">
      暂无品牌监测，点击"注册品牌"开始监测电商平台上的品牌侵权
    </div>

    <div class="brands-grid">
      <div v-for="brand in brands" :key="brand.id" class="brand-card card" :class="{ inactive: !brand.is_active }">
        <div class="brand-card-header">
          <span class="brand-name">{{ brand.brand_name }}</span>
          <div class="brand-actions">
            <span class="brand-status" :class="brand.is_active ? 'active' : 'paused'">
              {{ brand.is_active ? '监测中' : '已暂停' }}
            </span>
            <button class="btn btn-secondary btn-sm" @click="handleScan(brand.id)" :disabled="scanning === brand.id">
              {{ scanning === brand.id ? '扫描中...' : '扫描' }}
            </button>
            <button class="btn btn-ghost btn-sm" @click="handleDelete(brand.id)">删除</button>
          </div>
        </div>

        <div class="brand-meta">
          <span v-if="brand.keywords && brand.keywords.length">
            关键词: {{ brand.keywords.join(', ') }}
          </span>
          <span v-if="brand.platforms && brand.platforms.length">
            平台: {{ brand.platforms.map(p => platformLabel(p)).join(', ') }}
          </span>
        </div>

        <div class="brand-stats">
          <span>扫描次数: {{ brand.total_matches || 0 }} 个匹配</span>
          <span v-if="brand.last_scan_at">上次扫描: {{ brand.last_scan_at?.slice(0, 16) }}</span>
        </div>

        <!-- Scan results for this brand -->
        <div v-if="brandResults[brand.id] && brandResults[brand.id].length > 0" class="brand-results">
          <div class="result-subtitle">扫描结果</div>
          <div v-for="res in brandResults[brand.id].slice(0, 5)" :key="res.id" class="brand-result-item">
            <div class="result-platform">{{ platformLabel(res.platform) }}</div>
            <div class="result-title">{{ res.item_title || '未命名商品' }}</div>
            <div class="result-meta">
              <span class="result-sim" :class="simClass(res.similarity)">{{ res.similarity.toFixed(1) }}%</span>
              <span class="result-url">{{ res.item_url }}</span>
            </div>
            <div v-if="res.notes" class="result-note">{{ res.notes }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { monitorApi } from '@/api/monitor'
import type { BrandWatch, BrandScanResult } from '@/types/monitor'

const brands = ref<BrandWatch[]>([])
const brandResults = ref<Record<string, BrandScanResult[]>>({})
const showForm = ref(false)
const scanning = ref<string | null>(null)

const platforms = [
  { value: 'taobao', label: '淘宝' },
  { value: 'jd', label: '京东' },
  { value: 'pinduoduo', label: '拼多多' },
  { value: 'amazon', label: 'Amazon' },
]

const platformLabel = (p: string) => {
  const found = platforms.find(x => x.value === p)
  return found ? found.label : p
}

const simClass = (sim: number) => {
  if (sim >= 80) return 'high'
  if (sim >= 50) return 'mid'
  return 'low'
}

const form = reactive({
  brand_name: '',
  keywordsStr: '',
  platforms: ['taobao', 'jd', 'pinduoduo'] as string[],
})

async function fetchBrands() {
  try {
    const res = await monitorApi.brandWatches()
    brands.value = res.data.data
  } catch { /* handle silently */ }
}

async function handleRegister() {
  const keywords = form.keywordsStr
    ? form.keywordsStr.split(',').map((k: string) => k.trim()).filter(Boolean)
    : []
  try {
    await monitorApi.createBrandWatch({
      brand_name: form.brand_name.trim(),
      keywords,
      platforms: form.platforms,
    })
    form.brand_name = ''
    form.keywordsStr = ''
    form.platforms = ['taobao', 'jd', 'pinduoduo']
    showForm.value = false
    ;(window as any).$toast?.show('品牌注册成功', 'success')
    await fetchBrands()
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || '注册失败', 'error')
  }
}

async function handleScan(brandId: string) {
  scanning.value = brandId
  try {
    const res = await monitorApi.brandScan(brandId)
    ;(window as any).$toast?.show(
      res.data.message || '扫描完成',
      res.data.data?.is_mock_data ? 'warning' : 'success'
    )
    // Load results
    const resultsRes = await monitorApi.brandResults(brandId)
    brandResults.value[brandId] = resultsRes.data.data
    await fetchBrands()
  } catch (e: any) {
    ;(window as any).$toast?.show('扫描失败', 'error')
  } finally {
    scanning.value = null
  }
}

async function handleDelete(brandId: string) {
  try {
    await monitorApi.deleteBrandWatch(brandId)
    ;(window as any).$toast?.show('品牌已删除', 'success')
    await fetchBrands()
  } catch { /* handle silently */ }
}

onMounted(fetchBrands)
</script>

<style scoped>
.brand-panel { display: flex; flex-direction: column; gap: 16px; }
.section-title { font-size: 1rem; font-weight: 700; font-family: var(--font-display); margin: 0; }
.brand-header { padding: 20px; }
.brand-header-top { display: flex; justify-content: space-between; align-items: center; }
.brand-form { margin-top: 16px; display: flex; flex-direction: column; gap: 12px; }
.form-row { display: flex; gap: 16px; flex-wrap: wrap; }
.form-field { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 6px; }
.form-field label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-field input { padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 0.85rem; background: var(--surface); color: var(--fg); }
.platform-checks { display: flex; gap: 12px; flex-wrap: wrap; }
.check-label { display: flex; align-items: center; gap: 4px; font-size: 0.82rem; cursor: pointer; }
.form-actions { display: flex; gap: 8px; }
.empty-hint { font-size: 0.85rem; color: var(--muted); padding: 24px; text-align: center; }
.brands-grid { display: flex; flex-direction: column; gap: 12px; }
.brand-card { padding: 16px 20px; transition: opacity 0.2s; }
.brand-card.inactive { opacity: 0.5; }
.brand-card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
.brand-name { font-weight: 700; font-size: 1rem; }
.brand-actions { display: flex; align-items: center; gap: 8px; }
.brand-status { font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; }
.brand-status.active { background: oklch(96% 0.05 145); color: oklch(40% 0.08 145); }
.brand-status.paused { background: oklch(96% 0.01 90); color: var(--muted); }
.brand-meta { display: flex; gap: 16px; font-size: 0.8rem; color: var(--muted); margin-top: 8px; }
.brand-stats { display: flex; gap: 16px; font-size: 0.78rem; color: var(--muted); margin-top: 4px; }
.brand-results { margin-top: 12px; border-top: 1px solid var(--border); padding-top: 12px; }
.result-subtitle { font-size: 0.8rem; font-weight: 600; color: var(--muted); margin-bottom: 8px; }
.brand-result-item { padding: 8px 0; border-bottom: 1px solid var(--border-light); }
.brand-result-item:last-child { border-bottom: none; }
.result-platform { font-size: 0.72rem; font-weight: 600; color: var(--accent); text-transform: uppercase; }
.result-title { font-size: 0.85rem; font-weight: 500; margin-top: 2px; }
.result-meta { display: flex; gap: 8px; font-size: 0.75rem; color: var(--muted); margin-top: 2px; }
.result-sim { font-weight: 700; }
.result-sim.high { color: #e53e3e; }
.result-sim.mid { color: var(--orange); }
.result-sim.low { color: var(--muted); }
.result-url { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 300px; }
.result-note { font-size: 0.72rem; color: var(--orange); margin-top: 2px; font-style: italic; }
.btn-sm { padding: 6px 12px; font-size: 0.78rem; }
</style>

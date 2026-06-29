<!-- TemplateBrowserView — 产品库浏览

Browse all product templates organized by material category.
Shows specs, cost ranges, and supported platforms for each template.
-->
<template>
  <div class="template-browser">
    <h2>🏗️ 产品库</h2>
    <p class="subtitle">浏览所有产品模板及其规格要求</p>

    <!-- Material filter tabs -->
    <div class="material-tabs">
      <button
        v-for="mat in materials"
        :key="mat.id"
        :class="['mat-tab', { active: activeMaterial === mat.id }]"
        @click="activeMaterial = mat.id"
      >
        {{ mat.label }}
      </button>
      <button :class="['mat-tab', { active: activeMaterial === '' }]" @click="activeMaterial = ''">
        全部
      </button>
    </div>

    <!-- Category cards -->
    <div class="category-grid">
      <div
        v-for="cat in filteredCategories"
        :key="cat.id"
        class="category-card"
      >
        <div class="card-header">
          <span class="cat-icon">{{ cat.icon }}</span>
          <div>
            <div class="cat-name-zh">{{ cat.name_zh }}</div>
            <div class="cat-name-en">{{ cat.name_en }}</div>
          </div>
        </div>

        <div class="card-specs">
          <div class="spec-row">
            <span class="spec-label">尺寸:</span>
            <span>{{ cat.size_spec?.width_mm }}×{{ cat.size_spec?.height_mm }}mm</span>
          </div>
          <div class="spec-row">
            <span class="spec-label">DPI:</span>
            <span>≥{{ cat.dpi_requirement }}</span>
          </div>
          <div class="spec-row">
            <span class="spec-label">色彩:</span>
            <span>{{ cat.color_mode || 'sRGB' }}</span>
          </div>
          <div class="spec-row">
            <span class="spec-label">出血:</span>
            <span>{{ cat.bleed_mm || 0 }}mm</span>
          </div>
        </div>

        <div class="card-pricing">
          <div class="price-range">
            ¥{{ cat.cost_range?.[0] || '—' }} - ¥{{ cat.cost_range?.[1] || '—' }}
          </div>
          <div class="suggested-price">
            建议售价: ¥{{ cat.suggested_price_cny || '—' }}
          </div>
        </div>

        <div class="card-platforms">
          <span v-for="p in cat.platforms || ['—']" :key="p" class="platform-tag">{{ p }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { supplyApi } from '@/api/supply'

interface Category {
  id: string
  name_zh: string
  name_en: string
  material_category: string
  icon?: string
  size_spec?: { width_mm: number; height_mm: number }
  dpi_requirement: number
  color_mode?: string
  bleed_mm?: number
  cost_range?: [number, number]
  suggested_price_cny?: number
  platforms?: string[]
}

const categories = ref<Category[]>([])
const materials = [
  { id: 'textile', label: '纺织' },
  { id: 'paper', label: '纸质' },
  { id: 'hard_goods', label: '硬质' },
  { id: 'plastic_3c', label: '3C' },
  { id: 'toys', label: '玩具' },
]

const activeMaterial = ref('')

const filteredCategories = computed(() => {
  if (!activeMaterial.value) return categories.value
  return categories.value.filter(c => c.material_category === activeMaterial.value)
})

async function loadCategories() {
  try {
    const { data } = await supplyApi.productCategories()
    const grouped = (data as any)?.categories_by_material || {}
    const all: Category[] = []
    for (const mat of Object.values(grouped)) {
      const m = mat as any
      for (const cat of m.categories) {
        all.push(cat)
      }
    }
    categories.value = all
  } catch {
    // Use fallback data
  }
}

onMounted(loadCategories)
</script>

<style scoped>
.template-browser { padding: 20px; max-width: 1200px; margin: 0 auto; }

.template-browser h2 { margin: 0 0 4px; font-size: 1.3rem; }
.subtitle { color: var(--muted); font-size: .82rem; margin-bottom: 20px; }

/* Material tabs */
.material-tabs { display: flex; gap: 4px; margin-bottom: 16px; flex-wrap: wrap; }

.mat-tab {
  padding: 6px 14px; border: 1px solid var(--border); border-radius: 100px;
  background: none; cursor: pointer; font-size: .78rem;
}

.mat-tab.active {
  background: var(--accent); color: #fff; border-color: var(--accent);
}

/* Grid */
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}

.category-card {
  border: 1px solid var(--border); border-radius: var(--radius-md);
  padding: 14px; background: var(--surface);
  transition: border-color 0.2s;
}

.category-card:hover { border-color: var(--accent); }

.card-header { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 10px; }

.cat-icon { font-size: 1.5rem; }

.cat-name-zh { font-weight: 700; font-size: .9rem; }
.cat-name-en { font-size: .7rem; color: var(--muted); }

/* Specs */
.card-specs { margin-bottom: 10px; }

.spec-row {
  display: flex; justify-content: space-between;
  font-size: .72rem; padding: 2px 0;
}

.spec-label { color: var(--muted); }

/* Pricing */
.card-pricing {
  padding-top: 8px;
  border-top: 1px solid var(--border);
  margin-bottom: 8px;
}

.price-range { font-weight: 700; font-size: .82rem; color: var(--accent); }
.suggested-price { font-size: .68rem; color: var(--muted); }

/* Platforms */
.card-platforms { display: flex; gap: 4px; flex-wrap: wrap; }

.platform-tag {
  font-size: .62rem; padding: 1px 6px;
  background: var(--muted-bg); border-radius: 100px;
}
</style>

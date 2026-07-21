<template>
  <nav v-if="crumbs.length > 1" class="breadcrumb" aria-label="面包屑导航">
    <ol class="breadcrumb-list">
      <li v-for="(crumb, i) in crumbs" :key="crumb.path" class="breadcrumb-item">
        <router-link
          v-if="i < crumbs.length - 1"
          :to="crumb.path"
          class="breadcrumb-link"
        >
          {{ crumb.label }}
        </router-link>
        <span v-else class="breadcrumb-current" aria-current="page">
          {{ crumb.label }}
        </span>
        <span v-if="i < crumbs.length - 1" class="breadcrumb-sep" aria-hidden="true">/</span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

interface Crumb {
  path: string
  label: string
}

const route = useRoute()

const routeLabels: Record<string, string> = {
  dashboard: '工作台',
  works: '作品管理',
  'work-detail': '作品详情',
  rights: '权利保护',
  ipr: 'IP 登记',
  supply: '商业转化',
  listings: '转化列表',
  'listing-detail': '交易详情',
  templates: '模板库',
  publish: '内容分发',
  business: '经营数据',
  commissions: '委托看板',
  settings: '偏好设置',
  integrations: '第三方对接',
  watermarks: '水印预设',
  'metadata-templates': '模板管理',
  'work-variants': '作品变体',
  culling: '审片视图',
  subscriptions: '订阅管理',
  projects: '项目分组',
  recycle: '回收站',
}

const crumbs = computed<Crumb[]>(() => {
  // route.matched already gives us the parent-to-child chain
  const matched = route.matched

  // Build crumbs from matched routes
  const result: Crumb[] = matched.map((routeDef, index) => {
    // Construct the path by joining parent path + current path
    const fullPath = matched.slice(0, index + 1).map(r => r.path).join('')
    const name = String(routeDef.name || '')
    const label = routeLabels[name] || name.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')

    return { path: fullPath, label }
  })

  // Filter out empty path and duplicates
  return result.filter((c, i) => c.path && (i === 0 || c.path !== result[i - 1].path))
})
</script>

<style scoped>
.breadcrumb {
  padding: 8px 0;
  font-size: 0.82rem;
  color: var(--muted);
}
.breadcrumb-list {
  display: flex;
  align-items: center;
  gap: 4px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.breadcrumb-link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.15s;
}
.breadcrumb-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}
.breadcrumb-current {
  color: var(--fg);
  font-weight: 600;
}
.breadcrumb-sep {
  color: var(--border);
  margin: 0 2px;
}
</style>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

interface MenuItem { label: string; path: string }

const typeMenuMap: Record<string, MenuItem[]> = {
  illustrator: [
    { label: '工作台', path: '/app/illustrator' },
    { label: '版权登记', path: '/app/ipr' },
    { label: '授权交易', path: '/app/listings' },
    { label: '维权中心', path: '/app/enforcement' },
    { label: '导航', path: '/app/navigation' },
  ],
  photographer: [
    { label: '工作台', path: '/app/photographer' },
    { label: '图库管理', path: '/app/photographer?tab=stock' },
    { label: '维权中心', path: '/app/enforcement' },
    { label: '导航', path: '/app/navigation' },
  ],
  video: [
    { label: '工作台', path: '/app/video' },
    { label: '品牌合作', path: '/app/video?tab=campaigns' },
    { label: '分发', path: '/app/video?tab=distribute' },
    { label: '维权中心', path: '/app/enforcement' },
    { label: '导航', path: '/app/navigation' },
  ],
  craftsman: [
    { label: '工作台', path: '/app/craftsman' },
    { label: '订单管理', path: '/app/craftsman?tab=orders' },
    { label: '原材料库存', path: '/app/craftsman?tab=materials' },
    { label: '工厂', path: '/app/craftsman?tab=factories' },
    { label: '导航', path: '/app/navigation' },
  ],
  musician: [
    { label: '工作台', path: '/app/musician' },
    { label: '发行', path: '/app/musician?tab=releases' },
    { label: '分成协议', path: '/app/musician?tab=splits' },
    { label: '导航', path: '/app/navigation' },
  ],
  writer: [
    { label: '工作台', path: '/app/writer' },
    { label: '文章管理', path: '/app/writer?tab=articles' },
    { label: '书籍管理', path: '/app/writer?tab=books' },
    { label: '手稿编辑', path: '/app/writer?tab=manuscripts' },
    { label: '导航', path: '/app/navigation' },
  ],
}

const route = useRoute()
const currentType = computed(() => (route.query.type as string) || 'illustrator')
const menuItems = computed(() => typeMenuMap[currentType.value] || typeMenuMap.illustrator)
</script>

<template>
  <nav class="creator-sidebar">
    <div class="sidebar-header">创作者导航</div>
    <ul class="menu-list">
      <li v-for="item in menuItems" :key="item.path" class="menu-item">
        <router-link :to="item.path">{{ item.label }}</router-link>
      </li>
    </ul>
  </nav>
</template>

<style scoped>
.creator-sidebar { width: 200px; background: #1f2937; color: #fff; min-height: 100vh; padding: 16px 0; }
.sidebar-header { padding: 0 16px 16px; font-size: 16px; font-weight: 600; border-bottom: 1px solid #374151; }
.menu-list { list-style: none; padding: 0; margin: 0; }
.menu-item a { display: block; padding: 10px 16px; color: #d1d5db; text-decoration: none; font-size: 14px; }
.menu-item a:hover, .menu-item a.router-link-active { background: #374151; color: #fff; }
</style>

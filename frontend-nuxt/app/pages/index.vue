<!-- app/pages/index.vue -->
<script setup lang="ts">
useHead({
  title: 'OriSpark — AI Creator Trust Hub',
  meta: [
    { name: 'description', content: 'AI时代的创作者权益保护与多边撮合信任枢纽平台' },
    { property: 'og:url', content: 'https://orispark.local' },
  ],
})

// 导入新组件
import HeroBanner from '@/components/HeroBanner.vue'
import PlatformStats from '@/components/PlatformStats.vue'
import WorkGallery3D from '@/components/WorkGallery3D.vue'
</script>

<template>
  <div class="page-index">
    <!-- Hero Banner with 3D particle background -->
    <HeroBanner />

    <!-- Stats Section with animated counters -->
    <PlatformStats />

    <!-- 3D Gallery with parallax cards -->
    <WorkGallery3D />

    <!-- Other components (unchanged) -->
    <CoreCapabilities />
    <RecentContracts />
    <DownloadCta />
  </div>
</template>

<style scoped>
.page-index {
  max-width: 1200px;
  margin: 0 auto;
}
</style>

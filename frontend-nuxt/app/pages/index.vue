<template>
  <div class="page-index">
    <HeroBanner />
    <PlatformStats />
    <CoreCapabilities />
    <WorkGallery />
    <RecentContracts />
    <DownloadCta />
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'OriSpark — AI Creator Trust Hub',
  meta: [
    { name: 'description', content: 'AI时代的创作者权益保护与多边撮合信任枢纽平台' },
    { property: 'og:url', content: 'https://orispark.local' },
  ],
})
</script>

<style scoped>
.page-index {
  max-width: 1200px;
  margin: 0 auto;
}
</style>

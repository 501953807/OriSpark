<script setup lang="ts">
import { ref, onMounted } from 'vue'
import HeroBanner from '@/components/HeroBanner.vue'
import PlatformStats from '@/components/PlatformStats.vue'
import WorkGallery3D from '@/components/WorkGallery3D.vue'
import CoreCapabilities from '@/components/CoreCapabilities.vue'
import RecentContracts from '@/components/RecentContracts.vue'
import DownloadCta from '@/components/DownloadCta.vue'
import { fetchPublicWorks, fetchPublicContracts } from '~/composables/usePublicApi'

useHead({
  title: 'OriSpark — AI 时代创作者信任枢纽',
  meta: [
    { name: 'description', content: 'AI时代的创作者权益保护与多边撮合信任枢纽平台' },
    { property: 'og:url', content: 'https://orispark.local' },
  ],
})

const featuredWorks = ref<Array<{ id: string; title: string; thumbnail: string | null }>>([])
const featuredContracts = ref<Array<{ id: string; title: string; total_amount: number; status: string }>>([])
const heroError = ref<string | null>(null)

onMounted(async () => {
  try {
    const [worksRes, contractsRes] = await Promise.allSettled([
      fetchPublicWorks({ limit: '6' }),
      fetchPublicContracts({ limit: '5' }),
    ])
    if (worksRes.status === 'fulfilled' && Array.isArray(worksRes.value)) {
      featuredWorks.value = worksRes.value.slice(0, 6).map((w: any) => ({
        id: w.id,
        title: w.title,
        thumbnail: w.thumbnail_path || w.thumbnail || null,
      }))
    }
    if (contractsRes.status === 'fulfilled' && Array.isArray(contractsRes.value)) {
      featuredContracts.value = contractsRes.value.slice(0, 5).map((c: any) => ({
        id: c.id,
        title: c.title,
        total_amount: c.total_amount || 0,
        status: c.status || 'active',
      }))
    }
  } catch (e) {
    heroError.value = e instanceof Error ? e.message : '加载失败'
  }
})
</script>

<template>
  <div class="page-index">
    <HeroBanner
      :featured-works="featuredWorks"
      :featured-contracts="featuredContracts"
      :error="heroError"
    />
    <PlatformStats />
    <WorkGallery3D />
    <CoreCapabilities />
    <RecentContracts :contracts="featuredContracts" />
    <DownloadCta />
  </div>
</template>

<style scoped>
.page-index {
  width: 100%;
}
</style>

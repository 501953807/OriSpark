<!-- app/components/GalleryCard.vue -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

defineProps<{
  title: string
  thumbnail: string
  id: number
}>()

const card = ref<HTMLDivElement | null>(null)
const tiltX = ref(0)
const tiltY = ref(0)

// 触摸事件支持（移动端）
const handleMove = (e: MouseEvent | TouchEvent) => {
  if (!card.value) return

  const clientX = e instanceof MouseEvent ? e.clientX : e.touches[0].clientX
  const clientY = e instanceof MouseEvent ? e.clientY : e.touches[0].clientY

  const rect = card.value.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2

  // 计算倾斜角度（限制在 ±5°）
  const tiltLimit = 5
  const calculateTilt = (pos: number, center: number, size: number) => {
    const offset = (pos - center) / (size / 2)
    return Math.max(-tiltLimit, Math.min(tiltLimit, offset * tiltLimit))
  }

  tiltX.value = calculateTilt(clientY, centerY, rect.height)
  tiltY.value = calculateTilt(clientX, centerX, rect.width)
}

const handleLeave = () => {
  if (card.value) {
    tiltX.value = 0
    tiltY.value = 0
  }
}

onMounted(() => {
  if (card.value) {
    card.value.addEventListener('mousemove', handleMove)
    card.value.addEventListener('mouseleave', handleLeave)

    // 触摸事件
    card.value.addEventListener('touchmove', handleMove, { passive: true })
    card.value.addEventListener('touchend', handleLeave)
    card.value.addEventListener('touchcancel', handleLeave)
  }
}

onBeforeUnmount(() => {
  if (card.value) {
    card.value.removeEventListener('mousemove', handleMove)
    card.value.removeEventListener('mouseleave', handleLeave)
    card.value.removeEventListener('touchmove', handleMove)
    card.value.removeEventListener('touchend', handleLeave)
    card.value.removeEventListener('touchcancel', handleLeave)
  }
}
</script>

<template>
  <div
    ref="card"
    class="gallery-card"
    :style="{
      transform: `rotateX(${tiltX}deg) rotateY(${tiltY}deg)`
    }"
  >
    <img
      :src="thumbnail"
      :alt="title"
      class="gallery-card-image"
      loading="lazy"
    >
    <div class="gallery-card-content">
      <h3 class="gallery-card-title">{{ title }}</h3>
    </div>
  </div>
</template>

<style scoped>
.gallery-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  perspective: 1000px; /* 启用3D空间 */
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: box-shadow 0.3s ease, transform 0.1s ease-out;
  transform-style: preserve-3d;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.gallery-card:hover {
  box-shadow: 0 20px 50px rgba(14, 165, 233, 0.25);
  transform: translateY(-8px) !important; /* hover覆盖tilt */
}

.gallery-card-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  display: block;
  transition: transform 0.3s ease;
}

.gallery-card:hover .gallery-card-image {
  transform: scale(1.05);
}

.gallery-card-content {
  padding: 1rem;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.gallery-card-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  font-family: 'Satoshi', sans-serif;
}

/* 减速模式时禁用3D效果 */
@media (prefers-reduced-motion: reduce) {
  .gallery-card {
    transform: none !important;
    transition: none;
  }

  .gallery-card:hover {
    transform: translateY(-8px) !important;
  }
}
</style>

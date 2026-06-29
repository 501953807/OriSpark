<template>
  <div class="media-player" :class="{ 'is-video': type === 'video' }">
    <!-- Video with Plyr -->
    <video v-if="type === 'video'" ref="videoRef" class="plyr-video" :src="src" controls :crossorigin="''" playsinline>
      <source :src="src" :type="mimeType" />
      <p>您的浏览器不支持视频播放，请<a :href="src" download>下载文件</a>。</p>
    </video>

    <!-- Audio with Plyr -->
    <audio v-if="type === 'audio'" ref="audioRef" class="plyr-audio" :src="src" controls>
      <source :src="src" :type="mimeType" />
    </audio>

    <!-- Image fallback -->
    <img v-if="type === 'image'" :src="src" :alt="alt" class="media-image" loading="lazy" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = withDefaults(defineProps<{
  src: string
  type?: 'video' | 'audio' | 'image'
  mimeType?: string
  alt?: string
  autoplay?: boolean
}>(), {
  type: 'video',
  mimeType: 'video/mp4',
  alt: '',
})

const videoRef = ref<HTMLVideoElement>()
const audioRef = ref<HTMLAudioElement>()
let player: any = null

onMounted(() => {
  const el = props.type === 'video' ? videoRef.value : audioRef.value
  if (!el) return

  // Plyr 通过 CDN 或手动安装，这里使用原生 controls 作为默认
  // 当 plyr 通过 script tag 加载后自动初始化
  const Plyr = (window as any).Plyr
  if (Plyr) {
    player = new Plyr(el, {
      controls: ['play-large', 'play', 'progress', 'current-time', 'duration', 'mute', 'volume', 'pip', 'fullscreen'],
      autoplay: props.autoplay,
      ratio: '16:9',
    })
  }
})

onUnmounted(() => {
  player?.destroy()
})
</script>

<style scoped>
.media-player {
  width: 100%;
  border-radius: var(--radius);
  overflow: hidden;
  background: oklch(15% 0.005 240);
}
.media-player:not(.is-video) {
  max-width: 500px;
}
.media-image {
  width: 100%;
  height: auto;
  display: block;
  border-radius: var(--radius);
}
.plyr-video, .plyr-audio {
  width: 100%;
  display: block;
}
</style>

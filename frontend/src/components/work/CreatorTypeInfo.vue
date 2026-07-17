<template>
  <div v-if="visible" class="creator-type-info animate-fade-in">
    <div class="panel-header">
      <div class="header-main">
        <span class="type-badge" :class="badgeClass">{{ typeLabel }}</span>
        <span class="header-title">创作者信息</span>
      </div>
      <button class="close-btn" @click="dismiss">&times;</button>
    </div>

    <div class="panel-body">
      <Transition name="fade-panel" mode="out-in">
        <!-- Dynamic panel rendering -->
        <div v-if="panelLoading" key="loading" class="panel-placeholder">
          <div class="spinner" />
          <span>加载中…</span>
        </div>

        <component
          v-else-if="resolvedComponent"
          :key="currentCreatorType"
          :is="resolvedComponent"
          v-bind="panelProps"
        />

        <!-- No type-specific panel available -->
        <div v-else key="empty" class="panel-empty">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M12 6v6l4 2" stroke-linecap="round" />
            <circle cx="12" cy="12" r="10" />
          </svg>
          <p class="empty-title">暂无类型专属信息</p>
          <p class="empty-hint">该创作者类型的差异化面板尚未实现</p>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, shallowRef, watch } from 'vue'

// ------------------------------------------------------------------
// Props
// ------------------------------------------------------------------
interface Props {
  visible: boolean
  creatorType: string | null
  workData?: Record<string, any>
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  creatorType: null,
  workData: () => ({}),
})

const emit = defineEmits<{
  dismiss: []
  panelReady: [type: string, data: Record<string, any>]
}>()

// ------------------------------------------------------------------
// Panel registry — lazy-loaded via defineAsyncComponent
// ------------------------------------------------------------------
const panelMap: Record<string, string> = {
  illustrator:    '@/components/work/IllustratorPanel.vue',
  photographer:   '@/components/work/PhotographerExifPanel.vue',
  musician:       '@/components/work/MusicMetadataPanel.vue',
  writer:         '@/components/work/WriterStatsPanel.vue',
  video:          '@/components/work/VideoMetadataPanel.vue',
  craftsman:      '@/components/work/CraftsmanInfoPanel.vue',
}

// We use shallowRef per type to avoid SSR hydration issues with dynamic imports
const loadedPanels: Record<string, ReturnType<typeof shallowRef>> = {}
for (const typeName of Object.keys(panelMap)) {
  // eslint-disable-next-line @typescript-eslint/no-loop-func
  loadedPanels[typeName] = shallowRef(null)
}

const currentComponent = shallowRef<unknown | null>(null)
const panelLoading = ref(false)

// ------------------------------------------------------------------
// Computed helpers
// ------------------------------------------------------------------
const currentCreatorType = computed(() => props.creatorType ?? '')

const typeLabel = computed(() => {
  const labels: Record<string, string> = {
    illustrator: '插画师',
    photographer: '摄影师',
    musician: '音乐人',
    writer: '文字作者',
    video: '视频创作者',
    craftsman: '手工艺人',
  }
  return labels[currentCreatorType.value] || currentCreatorType.value
})

const badgeClass = computed(() => {
  const cls: Record<string, string> = {
    photographer: 'photo',
    musician: 'music',
    writer: 'writer',
    video: 'video',
    craftsman: 'craftsman',
    illustrator: 'illustrator',
  }
  return cls[currentCreatorType.value] || ''
})

const resolvedComponent = computed(() => currentComponent.value)

const panelProps = computed(() => {
  const wd = props.workData ?? {}
  return {
    work: wd,
    exifData: wd.exif_data ?? wd.custom_metadata?.exif,
    metadata: wd.custom_metadata ?? {},
    tags: wd.tags ?? [],
    rights: wd.rights ?? {},
  }
})

// ------------------------------------------------------------------
// Async loader
// ------------------------------------------------------------------
async function loadPanel(type: string): Promise<unknown> {
  const entry = panelMap[type]
  if (!entry) return null

  // Already cached?
  const cached = loadedPanels[type]
  if (cached?.value) return cached.value

  panelLoading.value = true
  try {
    // Dynamic import — matches the defineAsyncComponent pattern from PublishView.vue
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const mod = await import(entry)
    const comp = mod.default ?? mod
    if (loadedPanels[type]) loadedPanels[type].value = comp
    return comp
  } catch (_err: unknown) {
    console.warn(`[CreatorTypeInfo] Failed to load panel for "${type}"`, _err)
    return null
  } finally {
    panelLoading.value = false
  }
}

// ------------------------------------------------------------------
// Watch for type / visibility changes
// ------------------------------------------------------------------
let latestResolve: (() => void) | null = null

watch(
  () => [props.visible, props.creatorType] as const,
  async ([vis, type]) => {
    if (!vis || !type) {
      currentComponent.value = null
      latestResolve?.()
      latestResolve = null
      return
    }

    const comp = await loadPanel(type)
    currentComponent.value = comp

    // Fire readiness event once panel loads
    emit('panelReady', type, props.workData)
  },
)

// ------------------------------------------------------------------
// Actions
// ------------------------------------------------------------------
function dismiss() {
  emit('dismiss')
}
</script>

<style scoped>
/* --- Container --- */
.creator-type-info {
  position: fixed;
  inset: 0;
  z-index: 9990;
  display: flex;
  align-items: center;
  justify-content: center;
  background: oklch(0 0 0 / 0.25);
  backdrop-filter: blur(4px);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border, #e5e7eb);
}

.header-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--accent, #06b6d4);
  background: oklch(var(--accent, #06b6d4) / 0.1);
}

.header-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--fg, #111);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.3rem;
  cursor: pointer;
  color: var(--muted, #6b7280);
  padding: 0 4px;
  line-height: 1;
}

.close-btn:hover {
  color: var(--fg, #111);
}

.panel-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  align-items: stretch;
  justify-content: center;
}

/* --- Placeholder / Loading --- */
.panel-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--muted, #6b7280);
  font-size: 0.85rem;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border, #e5e7eb);
  border-top-color: var(--accent, #06b6d4);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* --- Empty --- */
.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 24px;
  color: var(--muted, #6b7280);
}

.empty-icon {
  width: 48px;
  height: 48px;
  opacity: 0.4;
}

.empty-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--fg, #111);
}

.empty-hint {
  font-size: 0.8rem;
}

/* --- Transitions --- */
.animate-fade-in {
  animation: fadeIn 0.18s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.fade-panel-enter-active,
.fade-panel-leave-active {
  transition: opacity 0.15s ease;
}

.fade-panel-enter-from,
.fade-panel-leave-to {
  opacity: 0;
}

/* --- Badge colours --- */
.type-badge.photo {
  background: oklch(56% 0.12 250 / 0.12);
  color: oklch(45% 0.1 250);
}
.type-badge.music {
  background: oklch(56% 0.15 330 / 0.12);
  color: oklch(45% 0.12 330);
}
.type-badge.writer {
  background: oklch(60% 0.08 140 / 0.12);
  color: oklch(40% 0.07 140);
}
.type-badge.video {
  background: oklch(60% 0.12 280 / 0.12);
  color: oklch(45% 0.1 280);
}
.type-badge.craftsman {
  background: oklch(65% 0.12 85 / 0.12);
  color: oklch(40% 0.1 85);
}
.type-badge.illustrator {
  background: oklch(65% 0.18 35 / 0.12);
  color: oklch(45% 0.15 35);
}
</style>

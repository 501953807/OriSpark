<template>
  <nav
    class="creator-switcher"
    role="tablist"
    aria-label="创作者类型切换"
  >
    <button
      v-for="creator in creators"
      :key="creator.type"
      role="tab"
      :aria-selected="creator.type === currentType"
      :class="[
        'creator-switcher-item',
        { active: creator.type === currentType },
        { collapsed: compact },
      ]"
      :title="creator.description"
      @click="handleSwitch(creator.type)"
    >
      <span class="creator-switcher-icon" :style="{ color: creator.color }">
        {{ iconMap[creator.icon] ?? '⭐' }}
      </span>
      <span v-if="!compact" class="creator-switcher-label">
        {{ creator.label }}
      </span>
    </button>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useCreatorTypeStore } from '@/stores/useCreatorTypeStore'
import { CREATOR_TYPES, getAllCreators } from '@/types/creator'
import type { CreatorType } from '@/types/creator'

const props = withDefaults(
  defineProps<{
    /** When true, show only icons (no labels) */
    compact?: boolean
  }>(),
  { compact: false },
)

const store = useCreatorTypeStore()
const currentType = computed(() => store.currentType)
const creators = getAllCreators()

const iconMap: Record<string, string> = {
  Palette: '🎨',
  Camera: '📸',
  Video: '🎬',
  Hammer: '🔨',
  Music: '🎵',
  Feather: '✒️',
}

function handleSwitch(type: CreatorType) {
  store.switchType(type)
}
</script>

<style scoped>
.creator-switcher {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: oklch(100% 0 0 / 0.5);
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
  scrollbar-width: none;
}
.creator-switcher::-webkit-scrollbar {
  display: none;
}

.creator-switcher-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--muted);
  transition: all 0.2s ease;
  white-space: nowrap;
  font-family: var(--font-body);
}
.creator-switcher-item:hover {
  background: oklch(56% 0.12 170 / 0.06);
  color: var(--fg);
}
.creator-switcher-item.active {
  border-color: currentColor;
  font-weight: 600;
}
.creator-switcher-item.collapsed {
  padding: 6px 10px;
}
.creator-switcher-icon {
  font-size: 1.1rem;
  line-height: 1;
}
.creator-switcher-label {
  line-height: 1.2;
}
</style>

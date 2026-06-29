<template>
  <nav class="chain-bar" aria-label="业务链">
    <div class="chain-steps">
      <template v-for="(step, idx) in steps" :key="step.key">
        <router-link :to="step.route" :class="['chain-step', { active: step.active, done: step.done }]" :aria-current="step.active ? 'step' : undefined">
          <span class="step-icon">{{ step.done ? '✅' : step.icon }}</span>
          <span class="step-label">{{ step.label }}</span>
        </router-link>
        <span v-if="idx < steps.length - 1" class="chain-arrow">→</span>
      </template>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/useAppStore'

const route = useRoute()
const appStore = useAppStore()

const steps = computed(() => {
  const currentName = (route.name as string) || ''
  const hasWorks = appStore.workCount > 0

  return [
    { key: 'works', label: '创意资产', icon: '🎨', route: '/app/works', active: currentName === 'works', done: hasWorks && currentName !== 'works' },
    { key: 'ipr', label: 'IP登记', icon: '📋', route: '/app/ipr', active: currentName === 'ipr', done: false },
    { key: 'notary', label: '权利保护', icon: '🛡️', route: '/app/rights', active: currentName === 'rights', done: hasWorks && appStore.notaryCount > 0 && currentName !== 'rights' },
    { key: 'publish', label: '内容分发', icon: '📱', route: '/app/publish', active: currentName === 'publish', done: false },
    { key: 'supply', label: '商业转化', icon: '💰', route: '/app/supply', active: currentName === 'supply', done: false },
    { key: 'business', label: '经营管理', icon: '📈', route: '/app/business', active: currentName === 'business', done: false },
  ]
})
</script>

<style scoped>
.chain-bar {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 10px 16px; margin-bottom: 20px;
}
.chain-steps { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.chain-step {
  display: flex; align-items: center; gap: 4px;
  padding: 5px 12px; border-radius: 100px;
  font-size: 0.8rem; text-decoration: none; color: var(--muted);
  transition: all 0.2s; white-space: nowrap;
  border: 1px solid transparent;
}
.chain-step:hover { background: oklch(56% 0.12 170 / 0.05); color: var(--fg); }
.chain-step.active { background: var(--accent); color: #fff; font-weight: 600; }
.chain-step.done { color: var(--fg); }
.step-icon { font-size: 0.85rem; }
.chain-arrow { color: var(--border); font-size: 0.75rem; }
@media (max-width: 767px) { .chain-bar { overflow-x: auto; } .chain-steps { flex-wrap: nowrap; } }
</style>

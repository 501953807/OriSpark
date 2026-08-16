<!-- Materio Nav/List Navigation Component -->
<template>
  <nav class="m-nav">
    <div v-for="(group, gi) in groups" :key="gi" class="m-nav__group">
      <div v-if="group.title" class="m-nav__group-title">{{ group.title }}</div>
      <a v-for="(item, ii) in group.items" :key="ii"
         class="m-nav__item"
         :class="{ 'm-nav__item--active': activeKey === item.key, 'm-nav__item--disabled': item.disabled }"
         :href="item.href"
         @click="item.click && item.click()">
        <span v-if="item.icon" class="m-nav__icon"><slot :name="`icon-${item.key}`" :item="item" /></span>
        <span class="m-nav__label">{{ item.label }}</span>
        <span v-if="item.badge !== undefined" class="m-nav__badge">{{ item.badge }}</span>
      </a>
    </div>
  </nav>
</template>

<script setup lang="ts">
defineProps<{
  groups: { title?: string; items: { key: string; label: string; href?: string; icon?: boolean; badge?: number | string; disabled?: boolean; click?: () => void }[] }[]
  activeKey?: string
}>()
</script>

<style scoped>
.m-nav { display: flex; flex-direction: column; gap: 4px; padding: 8px; }
.m-nav__group { display: flex; flex-direction: column; gap: 2px; }
.m-nav__group-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--m-grey-500); padding: 8px 12px 4px; }
.m-nav__item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; border-radius: var(--m-radius-sm);
  font-size: 14px; font-weight: 500; color: var(--m-grey-700);
  text-decoration: none; cursor: pointer;
  transition: all var(--m-transition-fast);
}
.m-nav__item:hover { background: var(--m-grey-100); color: var(--m-on-surface); }
.m-nav__item--active { background: var(--m-primary-light); color: var(--m-primary); }
.m-nav__item--disabled { opacity: var(--m-disabled-opacity); cursor: not-allowed; }
.m-nav__icon { display: flex; align-items: center; flex-shrink: 0; }
.m-nav__badge {
  margin-inline-start: auto;
  background: var(--m-error); color: #fff;
  font-size: 11px; font-weight: 600;
  padding: 1px 6px; border-radius: 100px; min-width: 18px; text-align: center;
}
</style>

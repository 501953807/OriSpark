<!-- Materio Vuetify-Style Card Component -->
<template>
  <div
    class="m-card"
    :class="[
      `m-card--variant-${variant}`,
      { 'm-card--hover': hoverable },
      `m-card--elevation-${elevation}`,
    ]"
    v-bind="$attrs"
  >
    <!-- Title -->
    <div v-if="$slots.title || title" class="m-card__title">
      <slot name="title">
        <h3>{{ title }}</h3>
      </slot>
    </div>

    <!-- Subtitle -->
    <div v-if="$slots.subtitle || subtitle" class="m-card__subtitle">
      <slot name="subtitle">
        <p>{{ subtitle }}</p>
      </slot>
    </div>

    <!-- Image -->
    <div v-if="$slots.image" class="m-card__image">
      <slot name="image" />
    </div>

    <!-- Content -->
    <div class="m-card__content">
      <slot />
    </div>

    <!-- Actions -->
    <div v-if="$slots.actions" class="m-card__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  subtitle?: string
  variant?: 'flat' | 'outlined' | 'elevated'
  hoverable?: boolean
  elevation?: 0 | 1 | 2 | 3 | 4 | 5
}>()
</script>

<style scoped>
.m-card {
  position: relative;
  background: var(--m-surface);
  border-radius: var(--m-radius-lg);
  overflow: hidden;
  transition: all var(--m-transition);
}

/* ── Variants ── */
.m-card--variant-flat {
  box-shadow: var(--m-shadow-sm);
}
.m-card--variant-outlined {
  border: 1px solid var(--m-border);
  box-shadow: none;
}
.m-card--variant-elevated {
  box-shadow: var(--m-shadow-md);
}

/* ── Elevation ── */
.m-card--elevation-0 { box-shadow: none; }
.m-card--elevation-1 { box-shadow: var(--m-shadow-xs); }
.m-card--elevation-2 { box-shadow: var(--m-shadow-sm); }
.m-card--elevation-3 { box-shadow: var(--m-shadow-md); }
.m-card--elevation-4 { box-shadow: var(--m-shadow-lg); }
.m-card--elevation-5 { box-shadow: var(--m-shadow-xl); }

/* ── Hover ── */
.m-card--hover:hover {
  box-shadow: var(--m-shadow-md);
  transform: translateY(-2px);
}

/* ── Title ── */
.m-card__title {
  padding: 1.25rem 1.25rem 0;
  font-size: 1.125rem;
  font-weight: var(--m-font-weight-semibold);
  color: var(--m-on-surface);
}
.m-card__title h3 {
  margin: 0;
  font-size: inherit;
  font-weight: inherit;
}

/* ── Subtitle ── */
.m-card__subtitle {
  padding: 0.25rem 1.25rem;
  font-size: 0.875rem;
  color: var(--m-grey-600);
}
.m-card__subtitle p {
  margin: 0;
}

/* ── Image ── */
.m-card__image {
  width: 100%;
  overflow: hidden;
}
.m-card__image :deep(img) {
  width: 100%;
  height: auto;
  display: block;
}

/* ── Content ── */
.m-card__content {
  padding: 1rem 1.25rem;
}

/* ── Actions ── */
.m-card__actions {
  padding: 0.5rem 1.25rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>

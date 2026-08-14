<!-- Nuxt Default Layout - wraps all pages without topnav (for auth pages) -->
<template>
  <div class="nuxt-default-layout">
    <slot />
  </div>
</template>

<style scoped>
.nuxt-default-layout {
  min-height: 100dvh;
}
</style>

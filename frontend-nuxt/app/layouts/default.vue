<!-- app/layouts/default.vue -->
<script setup lang="ts">
</script>

<template>
  <div class="portal-layout">
    <PortalHeader />
    <main class="portal-main">
      <slot />
    </main>
    <PortalFooter />
  </div>
</template>

<style scoped>
.portal-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.portal-main {
  flex: 1;
}
</style>

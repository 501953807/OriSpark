<template>
  <div class="portal-layout">
    <PortalHeader />
    <main class="portal-main">
      <slot />
    </main>
    <PortalFooter />
  </div>
</template>

<script setup lang="ts">
</script>

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

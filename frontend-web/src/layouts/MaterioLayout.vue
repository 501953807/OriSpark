<!-- Materio Sidebar Layout for OriStudio -->
<template>
  <div class="m-sidebar-layout" :class="{ 'm-sidebar-layout--collapsed': isCollapsed, 'm-sidebar-layout--mobile-open': mobileOpen }">
    <!-- Mobile Overlay -->
    <div v-if="mobileOpen" class="m-sidebar-overlay" @click="mobileOpen = false" />

    <!-- Sidebar -->
    <AppSidebar :class="{ 'mobile-visible': mobileOpen }" />

    <!-- Main Area -->
    <div class="m-main">
      <!-- Topbar -->
      <AppTopbar :is-collapsed="isCollapsed" @toggle-mobile="mobileOpen = !mobileOpen" />
      <div class="m-topbar-spacer"></div>
      <Breadcrumb />
      <BusinessChainBar />

      <!-- Content -->
      <main class="m-main__content">
        <router-view v-slot="{ Component, route }">
          <Transition :name="transitionName" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/useAppStore'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppTopbar from '@/components/layout/AppTopbar.vue'
import Breadcrumb from '@/components/common/Breadcrumb.vue'
import BusinessChainBar from '@/components/layout/BusinessChainBar.vue'

const appStore = useAppStore()
const isCollapsed = computed(() => appStore.sidebarCollapsed)
const mobileOpen = computed(() => appStore.sidebarCollapsed ? false : false) // controlled by AppSidebar
const transitionName = computed(() => 'page-fade')
</script>

<style scoped>
/* ── Layout ── */
.m-sidebar-layout {
  display: flex;
  min-height: 100dvh;
  background: var(--m-bg-subtle-materio, #F4F5FA);
}

/* ── Main ── */
.m-main {
  flex: 1;
  margin-inline-start: 256px;
  display: flex;
  flex-direction: column;
  min-height: 100dvh;
  transition: margin-inline-start 0.3s ease;
}
.m-sidebar-layout--collapsed .m-main {
  margin-inline-start: 80px;
}

/* Topbar spacer for breadcrumb */
.m-topbar-spacer {
  height: 2px;
  background: var(--m-border, rgba(46,38,61,0.08));
  flex-shrink: 0;
}

/* ── Content ── */
.m-main__content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

/* ── Responsive ── */
@media (max-width: 1023px) {
  .m-main { margin-inline-start: 0 !important; }
}

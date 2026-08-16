<template>
  <div class="hope-page-wrapper" :class="{ 'hope-with-collapsed-sidebar': isCollapsed }">
    <!-- Sidebar -->
    <aside
      class="hope-sidebar"
      :class="{ 'hope-sidebar-collapsed': isCollapsed, 'hope-sidebar-mobile-open': mobileOpen }"
    >
      <div class="hope-sidebar-header">
        <NuxtLink to="/" class="hope-sidebar-logo">
          <span class="hope-sidebar-logo-text">OriSpark</span>
        </NuxtLink>
        <button
          class="hope-sidebar-toggle"
          aria-label="折叠/展开侧边栏"
          @click="toggleSidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline :points="isCollapsed ? '9 18 15 12 9 6' : '15 18 9 12 15 6'"></polyline>
          </svg>
        </button>
      </div>

      <div class="hope-sidebar-body hope-scroll-theme">
        <ul class="hope-sidebar-nav">
          <li v-for="(item, idx) in navItems" :key="idx" class="hope-sidebar-nav-item">
            <!-- 子菜单 -->
            <template v-if="item.children">
              <button
                class="hope-sidebar-nav-link"
                :class="{ 'hope-sidebar-nav-active': activeGroup === item.key }"
                @click="toggleGroup(item.key)"
              >
                <span class="hope-icon hope-icon-md" v-html="item.icon"></span>
                <span class="hope-sidebar-nav-link-text">{{ item.label }}</span>
                <span class="hope-sidebar-nav-link-arrow">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline :points="expandedGroups.includes(item.key) ? '6 9 12 15 18 9' : '9 6 15 12 9 18'"></polyline>
                  </svg>
                </span>
              </button>
              <ul class="hope-sidebar-nav-sub" v-show="expandedGroups.includes(item.key)">
                <li v-for="(child, cIdx) in item.children" :key="cIdx">
                  <NuxtLink
                    :to="child.path"
                    class="hope-sidebar-nav-link"
                    :class="{ 'hope-sidebar-nav-active': route.path === child.path }"
                    @click="closeMobileSidebar"
                  >
                    <span class="hope-icon hope-icon-sm" v-html="child.icon || item.icon"></span>
                    <span class="hope-sidebar-nav-link-text">{{ child.label }}</span>
                  </NuxtLink>
                </li>
              </ul>
            </template>
            <!-- 普通项 -->
            <template v-else>
              <NuxtLink
                :to="item.path"
                class="hope-sidebar-nav-link"
                :class="{ 'hope-sidebar-nav-active': route.path === item.path }"
                @click="closeMobileSidebar"
              >
                <span class="hope-icon hope-icon-md" v-html="item.icon"></span>
                <span class="hope-sidebar-nav-link-text">{{ item.label }}</span>
              </NuxtLink>
            </template>
          </li>
        </ul>
      </div>

      <div class="hope-sidebar-footer">
        <div v-if="!isCollapsed || !mobileOpen" class="hope-user-info">
          <div class="hope-avatar hope-avatar-sm hope-avatar-status hope-avatar-online">U</div>
          <div class="hope-user-meta">
            <div class="hope-user-name">用户</div>
            <div class="hope-user-role" style="font-size:11px;color:var(--hope-text-muted)">运营者</div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Mobile overlay -->
    <div
      v-if="mobileOpen"
      class="hope-sidebar-mobile-overlay"
      @click="mobileOpen = false"
      style="position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:55"
    ></div>

    <!-- Main area -->
    <div class="hope-content-area">
      <!-- Top Navbar -->
      <header class="hope-navbar">
        <button
          class="hope-navbar-toggle"
          aria-label="打开菜单"
          @click="mobileOpen = !mobileOpen"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <NuxtLink to="/" class="hope-navbar-brand">OriSpark</NuxtLink>
        <nav class="hope-navbar-nav">
          <NuxtLink
            v-for="(item, idx) in navItems.filter(i => !i.children)"
            :key="idx"
            :to="item.path"
            class="hope-navbar-link"
            :class="{ 'hope-navbar-active': route.path === item.path }"
          >
            {{ item.label }}
          </NuxtLink>
        </nav>
        <div class="hope-navbar-actions" style="display:flex;gap:8px;align-items:center;">
          <NuxtLink to="/auth/login" class="hope-btn hope-btn-ghost hope-btn-sm">登录</NuxtLink>
          <NuxtLink to="/auth/register" class="hope-btn hope-btn-primary hope-btn-sm">注册</NuxtLink>
        </div>
      </header>

      <!-- Page content -->
      <main class="hope-page-inner">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const route = useRoute()
const isCollapsed = ref(false)
const mobileOpen = ref(false)
const expandedGroups = ref<string[]>([])

const toggleSidebar = () => { isCollapsed.value = !isCollapsed.value }
const toggleGroup = (key: string) => {
  const idx = expandedGroups.value.indexOf(key)
  idx >= 0 ? expandedGroups.value.splice(idx, 1) : expandedGroups.value.push(key)
}
const closeMobileSidebar = () => { if (import.meta.client && window.innerWidth < 1024) mobileOpen.value = false }

const navItems = [
  { key: 'dashboard', label: '数据看板', path: '/data', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>' },
  { key: 'gallery',   label: '作品画廊', path: '/gallery',   icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/></svg>' },
  { key: 'contracts', label: '合约市场', path: '/contracts', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' },
  { key: 'market',    label: '行情数据', path: '/market',    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/></svg>' },
  { key: 'ops',       label: '运营合作', path: '/operations', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' },
  { key: 'supply',    label: '供应链',   path: '/supply',    icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>' },
]
</script>

<style scoped>
.hope-sidebar-mobile-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); z-index: 55; }
.hope-user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
}
.hope-user-meta { overflow: hidden; }
.hope-user-name {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--hope-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.hope-navbar-actions { display: flex; gap: 8px; align-items: center; }
@media (max-width: 1023px) {
  .hope-navbar-nav { display: none !important; }
}
</style>

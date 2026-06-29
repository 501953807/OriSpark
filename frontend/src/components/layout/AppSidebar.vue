<template>
  <aside :class="['sidebar', { collapsed: isCollapsed, 'mobile-visible': mobileVisible }]" role="navigation" aria-label="主导航">
    <router-link to="/app" class="sb-brand" aria-label="OriStudio 首页">
      <div class="sb-logo" aria-hidden="true">O</div>
      <div v-if="!isCollapsed" class="sb-brand-text-wrap">
        <div class="sb-brand-text">OriStudio</div>
        <div class="sb-brand-sub">创作者全链路助手</div>
      </div>
    </router-link>

    <nav class="sb-nav">
      <!-- 概览 -->
      <div v-if="!isCollapsed" class="sb-section-title">{{ t('sidebar.overview') }}</div>
      <router-link to="/app" class="sb-link" exact-active-class="active" :title="isCollapsed ? '工作台' : ''" aria-label="工作台">
        <span class="sb-icon" aria-hidden="true">📊</span>
        <span v-if="!isCollapsed">工作台</span>
      </router-link>

      <!-- 核心业务链 (按真实IP运营顺序排列) -->
      <div v-if="!isCollapsed" class="sb-section-title">核心业务</div>
      <router-link to="/app/works" class="sb-link" active-class="active" :title="isCollapsed ? '创意资产' : ''" aria-label="创意资产">
        <span class="sb-icon" aria-hidden="true">🎨</span>
        <span v-if="!isCollapsed">创意资产</span>
        <span v-if="!isCollapsed" class="sb-badge">{{ appStore.workCount }}</span>
      </router-link>
      <router-link to="/app/ipr" class="sb-link" active-class="active" :title="isCollapsed ? 'IP登记' : ''" aria-label="IP登记">
        <span class="sb-icon" aria-hidden="true">📋</span>
        <span v-if="!isCollapsed">IP登记</span>
      </router-link>
      <router-link to="/app/rights" class="sb-link" active-class="active" :title="isCollapsed ? '权利保护' : ''" aria-label="权利保护">
        <span class="sb-icon" aria-hidden="true">🛡️</span>
        <span v-if="!isCollapsed">权利保护</span>
        <span v-if="!isCollapsed" class="sb-badge">{{ appStore.notaryCount }}</span>
        <span v-if="!isCollapsed && appStore.alertCount > 0" class="sb-badge new">{{ appStore.alertCount }}</span>
      </router-link>
      <router-link to="/app/publish" class="sb-link" active-class="active" :title="isCollapsed ? '内容分发' : ''" aria-label="内容分发">
        <span class="sb-icon" aria-hidden="true">📱</span>
        <span v-if="!isCollapsed">内容分发</span>
      </router-link>
      <router-link to="/app/supply" class="sb-link" active-class="active" :title="isCollapsed ? '商业转化' : ''" aria-label="商业转化">
        <span class="sb-icon" aria-hidden="true">💰</span>
        <span v-if="!isCollapsed">商业转化</span>
      </router-link>

      <!-- 经营管理 -->
      <div v-if="!isCollapsed" class="sb-section-title">经营管理</div>
      <router-link to="/app/business" class="sb-link" active-class="active" :title="isCollapsed ? '经营数据' : ''" aria-label="经营数据">
        <span class="sb-icon" aria-hidden="true">📈</span>
        <span v-if="!isCollapsed">经营数据</span>
      </router-link>
      <router-link to="/app/recycle" class="sb-link" active-class="active" :title="isCollapsed ? '回收站' : ''" aria-label="回收站">
        <span class="sb-icon" aria-hidden="true">🗑️</span>
        <span v-if="!isCollapsed">回收站</span>
      </router-link>
      <router-link to="/app/projects" class="sb-link" active-class="active" :title="isCollapsed ? '项目分组' : ''" aria-label="项目分组">
        <span class="sb-icon" aria-hidden="true">📂</span>
        <span v-if="!isCollapsed">项目分组</span>
      </router-link>
      <router-link to="/app/works/cull" class="sb-link" active-class="active" :title="isCollapsed ? '审片视图' : ''" aria-label="审片视图">
        <span class="sb-icon" aria-hidden="true">🔍</span>
        <span v-if="!isCollapsed">审片视图</span>
      </router-link>
      <router-link to="/app/business/commissions" class="sb-link" active-class="active" :title="isCollapsed ? '委托看板' : ''" aria-label="委托看板">
        <span class="sb-icon" aria-hidden="true">📋</span>
        <span v-if="!isCollapsed">委托看板</span>
      </router-link>

      <!-- 设置 -->
      <div v-if="!isCollapsed" class="sb-section-title">{{ t('sidebar.settings') }}</div>
      <router-link to="/app/settings" class="sb-link" active-class="active" :title="isCollapsed ? '设置' : ''" aria-label="偏好设置">
        <span class="sb-icon" aria-hidden="true">⚙️</span>
        <span v-if="!isCollapsed">偏好设置</span>
      </router-link>
      <router-link to="/app/integrations" class="sb-link" active-class="active" :title="isCollapsed ? '对接' : ''" aria-label="第三方对接">
        <span class="sb-icon" aria-hidden="true">🔌</span>
        <span v-if="!isCollapsed">第三方对接</span>
      </router-link>
      <router-link to="/app/settings/watermarks" class="sb-link" active-class="active" :title="isCollapsed ? '水印预设' : ''" aria-label="水印预设">
        <span class="sb-icon" aria-hidden="true">🖊️</span>
        <span v-if="!isCollapsed">水印预设</span>
      </router-link>
      <router-link to="/app/settings/templates" class="sb-link" active-class="active" :title="isCollapsed ? '模板管理' : ''" aria-label="模板管理">
        <span class="sb-icon" aria-hidden="true">📄</span>
        <span v-if="!isCollapsed">模板管理</span>
      </router-link>
      <router-link to="/app/settings/subscriptions" class="sb-link" active-class="active" :title="isCollapsed ? '订阅管理' : ''" aria-label="订阅管理">
        <span class="sb-icon" aria-hidden="true">💎</span>
        <span v-if="!isCollapsed">订阅管理</span>
      </router-link>
    </nav>

    <!-- 折叠按钮 -->
    <button class="sb-collapse-btn" @click="appStore.toggleSidebar()" :title="isCollapsed ? '展开菜单' : '折叠菜单'">
      {{ isCollapsed ? '▶' : '◀' }}
    </button>

    <!-- 用户 footer -->
    <div v-if="!isCollapsed" class="sb-footer">
      <div class="sb-avatar">创</div>
      <div>
        <div class="sb-user-name">创作者</div>
        <div class="sb-user-role">本地用户</div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { useI18n } from '@/composables/useI18n'

defineProps<{ mobileVisible?: boolean }>()

const appStore = useAppStore()
const isCollapsed = computed(() => appStore.sidebarCollapsed)
const { t } = useI18n()
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0; left: 0; bottom: 0;
  width: var(--sidebar-w);
  background: oklch(96% 0.004 240);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.3s ease, transform 0.3s ease;
  overflow: hidden;
}
.sidebar.collapsed {
  width: 60px;
}
.dark .sidebar {
  background: oklch(22% 0.01 240);
}
.sb-brand {
  padding: 16px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  color: inherit;
  min-height: 64px;
}
.sb-logo {
  width: 34px; height: 34px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 800; font-size: 1rem;
  flex-shrink: 0;
}
.sb-brand-text { font-family: var(--font-display); font-weight: 700; font-size: 0.95rem; }
.sb-brand-sub { font-size: 0.62rem; color: var(--muted); }
.sb-nav { flex: 1; padding: 8px 0; overflow-y: auto; overflow-x: hidden; }
.sb-section-title {
  padding: 8px 14px 4px;
  font-size: 0.62rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--muted);
}
.sb-link {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 14px; margin: 1px 6px;
  border-radius: var(--radius-sm); font-size: 0.85rem;
  font-weight: 500; color: var(--muted);
  text-decoration: none; transition: all 0.2s ease;
  white-space: nowrap;
}
.sb-link:hover { background: oklch(56% 0.12 170 / 0.06); color: var(--fg); }
.sb-link.active {
  background: var(--surface); color: var(--accent);
  box-shadow: 0 1px 4px oklch(0 0 0 / 0.04);
  font-weight: 600;
}
.collapsed .sb-link { padding: 12px; justify-content: center; }
.collapsed .sb-link .sb-icon { margin: 0; font-size: 1.2rem; }
.sb-icon { font-size: 1.05rem; width: 22px; text-align: center; flex-shrink: 0; }
.sb-badge {
  margin-left: auto; padding: 1px 8px; border-radius: 100px;
  font-size: 0.65rem; font-weight: 700;
  background: oklch(62% 0.18 55 / 0.15); color: var(--orange);
}
.sb-badge.new {
  background: oklch(56% 0.12 170 / 0.15); color: var(--accent);
  animation: pulse-badge 2s infinite;
}
.sb-collapse-btn {
  padding: 10px; border: none; border-top: 1px solid var(--border);
  background: transparent; cursor: pointer;
  font-size: 0.75rem; color: var(--muted);
  transition: color 0.2s;
}
.sb-collapse-btn:hover { color: var(--fg); }
.sb-footer {
  padding: 10px 14px; border-top: 1px solid var(--border);
  display: flex; align-items: center; gap: 10px;
}
.sb-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, var(--grad1), var(--grad2));
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 600; font-size: 0.8rem;
  flex-shrink: 0;
}
.sb-user-name { font-size: 0.82rem; font-weight: 600; }
.sb-user-role { font-size: 0.68rem; color: var(--muted); }
</style>

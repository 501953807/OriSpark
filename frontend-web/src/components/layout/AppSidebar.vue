<template>
  <aside
    :class="[
      'sidebar',
      { collapsed: isCollapsed, 'mobile-visible': mobileVisible, 'hover-expand': isCollapsed && isHovering },
    ]"
    role="navigation"
    aria-label="主导航"
    @mouseenter="isCollapsed && (isHovering = true)"
    @mouseleave="isHovering = false"
  >
    <router-link to="/app" class="sb-brand" aria-label="OriStudio 首页">
      <div class="sb-logo" aria-hidden="true">O</div>
      <div v-if="!isCollapsed" class="sb-brand-text-wrap">
        <div class="sb-brand-text">OriStudio</div>
        <div class="sb-brand-sub">创作者全链路助手</div>
      </div>
    </router-link>

    <nav class="sb-nav">
      <!-- 概览 -->
      <div v-if="!isCollapsed" class="sb-section-title">概览</div>
      <router-link to="/app" class="sb-link" exact-active-class="active" title="工作台：系统概览与数据统计">
        <span class="sb-icon material-icons">dashboard</span>
        <span v-if="!isCollapsed">工作台</span>
      </router-link>

      <!-- 核心业务 -->
      <div v-if="!isCollapsed" class="sb-section-title">核心业务</div>
      <router-link to="/app/works" class="sb-link" active-class="active" title="创意资产：原创作品素材存储仓库">
        <span class="sb-icon material-icons">inventory_2</span>
        <span v-if="!isCollapsed">创意资产</span>
        <span v-if="!isCollapsed" class="sb-badge">{{ appStore.workCount }}</span>
      </router-link>
      <router-link to="/app/ipr" class="sb-link" active-class="active" title="IP登记：版权确权、商标注册、外观设计专利申请">
        <span class="sb-icon material-icons">description</span>
        <span v-if="!isCollapsed">IP登记</span>
      </router-link>
      <router-link to="/app/rights" class="sb-link" active-class="active" title="权利保护：侵权监测、维权投诉、证据存证">
        <span class="sb-icon material-icons">security</span>
        <span v-if="!isCollapsed">权利保护</span>
        <span v-if="!isCollapsed" class="sb-badge">{{ appStore.notaryCount }}</span>
        <span v-if="!isCollapsed && appStore.alertCount > 0" class="sb-badge sb-badge--danger">{{ appStore.alertCount }}</span>
      </router-link>
      <router-link to="/app/publish" class="sb-link" active-class="active" title="内容分发：多平台内容发布与管理">
        <span class="sb-icon material-icons">publish</span>
        <span v-if="!isCollapsed">内容分发</span>
      </router-link>
      <router-link to="/app/contract-market" class="sb-link" active-class="active" title="商业转化：授权变现、交易撮合、合同管理">
        <span class="sb-icon material-icons">payments</span>
        <span v-if="!isCollapsed">商业转化</span>
      </router-link>

      <!-- 经营管理 -->
      <div v-if="!isCollapsed" class="sb-section-title">经营管理</div>
      <router-link to="/app/business" class="sb-link" active-class="active" title="经营管理：业务收入统计与数据分析">
        <span class="sb-icon material-icons">analytics</span>
        <span v-if="!isCollapsed">经营管理</span>
      </router-link>
      <router-link to="/app/recycle" class="sb-link" active-class="active" title="回收站：已删除作品的临时存放区，保留30天">
        <span class="sb-icon material-icons">delete_forever</span>
        <span v-if="!isCollapsed">回收站</span>
      </router-link>
      <router-link to="/app/projects" class="sb-link" active-class="active" title="项目分组：按系列/客户/年份组织作品">
        <span class="sb-icon material-icons">folder</span>
        <span v-if="!isCollapsed">项目分组</span>
      </router-link>
      <router-link to="/app/works/cull" class="sb-link" active-class="active" title="审片视图：作品批量筛选与审核">
        <span class="sb-icon material-icons">filter_list</span>
        <span v-if="!isCollapsed">审片视图</span>
      </router-link>
      <router-link to="/app/business/commissions" class="sb-link" active-class="active" title="委托看板：客户委托任务管理">
        <span class="sb-icon material-icons">assignment</span>
        <span v-if="!isCollapsed">委托看板</span>
      </router-link>

      <!-- 风险合规 -->
      <div v-if="!isCollapsed" class="sb-section-title">风险合规</div>
      <router-link to="/app/risk-warning" class="sb-link" active-class="active" title="风险预警：侵权预警、到期提醒">
        <span class="sb-icon material-icons">warning</span>
        <span v-if="!isCollapsed">风险预警</span>
        <span v-if="!isCollapsed && appStore.alertCount > 0" class="sb-badge sb-badge--danger">{{ appStore.alertCount }}</span>
      </router-link>

      <!-- 系统设置 -->
      <div v-if="!isCollapsed" class="sb-section-title">系统设置</div>
      <router-link to="/app/settings" class="sb-link" active-class="active" title="偏好设置：主题、语言、通知等系统配置">
        <span class="sb-icon material-icons">settings</span>
        <span v-if="!isCollapsed">偏好设置</span>
      </router-link>
      <router-link to="/app/integrations" class="sb-link" active-class="active" title="第三方对接：连接外部平台与服务">
        <span class="sb-icon material-icons">integration_instructions</span>
        <span v-if="!isCollapsed">第三方对接</span>
      </router-link>
      <router-link to="/app/settings/watermarks" class="sb-link" active-class="active" title="水印预设：自定义图片/视频水印样式">
        <span class="sb-icon material-icons">watermark</span>
        <span v-if="!isCollapsed">水印预设</span>
      </router-link>
      <router-link to="/app/settings/templates" class="sb-link" active-class="active" title="模板管理：合同/协议模板管理">
        <span class="sb-icon material-icons">article</span>
        <span v-if="!isCollapsed">模板管理</span>
      </router-link>
      <router-link to="/app/settings/subscriptions" class="sb-link" active-class="active" title="订阅管理：查看和升级会员订阅">
        <span class="sb-icon material-icons">stars</span>
        <span v-if="!isCollapsed">订阅管理</span>
      </router-link>
    </nav>

    <!-- 折叠按钮 -->
    <button class="sb-collapse-btn" @click="toggleSidebar()" :title="isCollapsed ? '展开菜单' : '折叠菜单'">
      <span class="material-icons">{{ isCollapsed ? 'chevron_right' : 'chevron_left' }}</span>
    </button>

    <!-- 用户 footer -->
    <div v-if="!isCollapsed" class="sb-footer">
      <div class="sb-avatar" :style="{ background: avatarGradient }">
        <span v-if="authStore.user?.avatar_url" class="sb-avatar-img" :src="authStore.user.avatar_url" />
        <span v-else>{{ displayName.charAt(0).toUpperCase() }}</span>
      </div>
      <div class="sb-footer-info">
        <div class="sb-user-name">{{ displayName }}</div>
        <div class="sb-user-role">{{ authStore.user?.role || '创作者' }}</div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useLayoutContext } from '@/composables/useLayoutContext'
import { useAppStore } from '@/stores/useAppStore'
import { useAuthStore } from '@/stores/useAuthStore'

defineProps<{ mobileVisible?: boolean }>()

const { sidebarCollapsed: isCollapsed, toggleSidebar, displayName, user } = useLayoutContext()
const appStore = useAppStore()
const authStore = useAuthStore()
const isHovering = ref(false)

const avatarGradient = computed(() => {
  const hue = Math.floor(Math.random() * 360)
  return `linear-gradient(135deg, hsl(${hue},70%,60%), hsl(${(hue + 30) % 360},70%,45%))`
})
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 256px;
  background: #ffffff;
  border-right: 1px solid rgba(46, 38, 61, 0.12);
  box-shadow: 0 0.25rem 0.5rem rgba(46, 38, 61, 0.18);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
.sidebar.collapsed {
  width: 80px;
}
.sidebar.collapsed.hover-expand {
  width: 256px;
}
.sb-brand {
  padding: 16px 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(46, 38, 61, 0.12);
  text-decoration: none;
  color: inherit;
  min-height: 64px;
  flex-shrink: 0;
}
.sb-logo {
  width: 34px;
  height: 34px;
  border-radius: 6px;
  background: linear-gradient(135deg, #8C57FF, #6A3FCC);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 800;
  font-size: 1rem;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}
.sb-brand-text {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  font-size: 0.95rem;
  color: #2e263d;
}
.sb-brand-sub {
  font-size: 0.62rem;
  color: #8a8d93;
}
.sb-nav {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
  overflow-x: hidden;
}
.sb-section-title {
  padding: 10px 14px 4px;
  font-size: 0.62rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #8a8d93;
  flex-shrink: 0;
}
.sb-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  margin: 1px 6px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #8a8d93;
  text-decoration: none;
  transition: all 0.15s ease;
  white-space: nowrap;
}
.sb-link:hover {
  background: #f4f5fa;
  color: #2e263d;
}
.sb-link.active {
  background: linear-gradient(135deg, #8C57FF, #6A3FCC);
  color: #ffffff;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.35);
}
.collapsed .sb-link {
  padding: 12px;
  justify-content: center;
}
.sb-icon {
  font-size: 1.25rem !important;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sb-badge {
  margin-left: auto;
  padding: 1px 7px;
  border-radius: 100px;
  font-size: 0.65rem;
  font-weight: 700;
  background: rgba(139, 92, 246, 0.12);
  color: #8C57FF;
}
.sb-badge--danger {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  animation: pulse-badge 2s infinite;
}
.sb-collapse-btn {
  padding: 10px;
  border: none;
  border-top: 1px solid rgba(46, 38, 61, 0.12);
  background: transparent;
  cursor: pointer;
  color: #8a8d93;
  transition: color 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.sb-collapse-btn:hover {
  color: #2e263d;
}
.sb-footer {
  padding: 10px 14px;
  border-top: 1px solid rgba(46, 38, 61, 0.12);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.sb-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8C57FF, #6A3FCC);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-weight: 600;
  font-size: 0.8rem;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(139, 92, 246, 0.25);
  overflow: hidden;
}
.sb-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.sb-footer-info {
  overflow: hidden;
}
.sb-user-name {
  font-size: 0.82rem;
  font-weight: 600;
  color: #2e263d;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sb-user-role {
  font-size: 0.68rem;
  color: #8a8d93;
}
@keyframes pulse-badge {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>

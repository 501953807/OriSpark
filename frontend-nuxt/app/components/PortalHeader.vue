<template>
  <header class="portal-header">
    <NuxtLink to="/" class="logo">
      <span class="logo-text">OriSpark</span>
    </NuxtLink>
    <nav class="nav-links">
      <NuxtLink to="/gallery">作品画廊</NuxtLink>
      <NuxtLink to="/contracts">合约市场</NuxtLink>
      <NuxtLink to="/market">市场数据</NuxtLink>
      <NuxtLink to="/opportunities">合作机会</NuxtLink>
    </nav>
    <div class="nav-actions">
      <NuxtLink to="https://studio.orispark.local" target="_blank" class="btn-primary">
        进入 OriStudio
      </NuxtLink>
    </div>
  </header>
</template>

<script setup lang="ts">
</script>

<style scoped>
.portal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}

.logo {
  text-decoration: none;
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: #059669;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-links a {
  text-decoration: none;
  color: #374151;
  font-size: 14px;
  font-weight: 500;
}

.nav-links a.router-link-active {
  color: #059669;
}

.nav-actions {
  display: flex;
  gap: 12px;
}

.btn-primary {
  padding: 8px 20px;
  background: #059669;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}

.btn-primary:hover {
  background: #047857;
}

@media (max-width: 768px) {
  .portal-header {
    flex-direction: column;
    gap: 12px;
    padding: 12px 16px;
  }

  .nav-links {
    gap: 16px;
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>

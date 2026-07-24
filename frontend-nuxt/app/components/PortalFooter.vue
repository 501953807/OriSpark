<template>
  <footer class="portal-footer">
    <div class="footer-content">
      <div class="footer-section">
        <h3>OriSpark</h3>
        <p>AI时代的创作者权益保护与多边撮合信任枢纽平台</p>
      </div>
      <div class="footer-section">
        <h4>快速链接</h4>
        <ul>
          <li><NuxtLink to="/">首页</NuxtLink></li>
          <li><NuxtLink to="/gallery">作品画廊</NuxtLink></li>
          <li><NuxtLink to="/contracts">合约市场</NuxtLink></li>
          <li><NuxtLink to="/market">市场数据</NuxtLink></li>
        </ul>
      </div>
      <div class="footer-section">
        <h4>进入 OriStudio</h4>
        <ul>
          <li><a href="https://studio.orispark.local" target="_blank">创作者工作台</a></li>
          <li><a href="https://studio.orispark.local/login" target="_blank">登录</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; {{ new Date().getFullYear() }} OriSpark. All rights reserved.</p>
    </div>
  </footer>
</template>

<script setup lang="ts">
</script>

<style scoped>
.portal-footer {
  background: #1f2937;
  color: #e5e7eb;
  padding: 48px 32px 24px;
}

.footer-content {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.footer-section h3 {
  color: #059669;
  font-size: 20px;
  margin-bottom: 12px;
}

.footer-section h4 {
  font-size: 14px;
  margin-bottom: 12px;
  color: #f3f4f6;
}

.footer-section p {
  font-size: 14px;
  line-height: 1.6;
  color: #9ca3af;
}

.footer-section ul {
  list-style: none;
  padding: 0;
}

.footer-section li {
  margin-bottom: 8px;
}

.footer-section a {
  color: #9ca3af;
  text-decoration: none;
  font-size: 14px;
}

.footer-section a:hover {
  color: #059669;
}

.footer-bottom {
  max-width: 1200px;
  margin: 32px auto 0;
  padding-top: 24px;
  border-top: 1px solid #374151;
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

@media (max-width: 768px) {
  .footer-content {
    grid-template-columns: 1fr;
    gap: 24px;
  }
}
</style>

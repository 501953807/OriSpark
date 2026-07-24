<template>
  <section class="download-cta">
    <div class="cta-content">
      <h2>下载 OriStudio</h2>
      <p>创作者工作台，支持 Electron 桌面端和 Web 双形态</p>
      <a href="https://studio.orispark.local/download" target="_blank" class="btn-download">
        免费下载
      </a>
    </div>
  </section>
</template>

<script setup lang="ts">
</script>

<style scoped>
.download-cta {
  padding: 48px 32px;
  background: linear-gradient(135deg, #065f46 0%, #047857 100%);
  color: #fff;
  text-align: center;
}

.cta-content h2 {
  font-size: 28px;
  margin: 0 0 12px;
}

.cta-content p {
  font-size: 16px;
  opacity: 0.9;
  margin: 0 0 24px;
}

.btn-download {
  display: inline-block;
  padding: 12px 32px;
  background: #fff;
  color: #059669;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
}

.btn-download:hover {
  background: #f0fdf4;
}
</style>

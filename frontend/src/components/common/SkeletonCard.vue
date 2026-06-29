<template>
  <div class="skeleton-card card">
    <div class="sk-thumb"></div>
    <div class="sk-body">
      <div class="sk-line sk-title"></div>
      <div class="sk-line sk-meta"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-card { padding: 0; overflow: hidden; }
.sk-thumb {
  height: 160px;
  background: linear-gradient(90deg, oklch(93% 0.003 240) 25%, oklch(96% 0.004 240) 50%, oklch(93% 0.003 240) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
.sk-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; }
.sk-line { height: 14px; border-radius: 4px; background: oklch(93% 0.003 240); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
.sk-title { width: 70%; }
.sk-meta { width: 45%; height: 10px; }
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>

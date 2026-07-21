<template>
  <div class="stage-assets-strip card">
    <div class="card-header-row">
      <h3>📎 阶段素材</h3>
      <span v-if="assets.length" class="asset-total">{{ assets.length }} 个文件</span>
    </div>

    <div v-if="!assets.length" class="empty-hint">
      此阶段暂无上传的素材文件
    </div>

    <div v-else class="assets-grid">
      <div v-for="(asset, ai) in assets" :key="ai" class="asset-card">
        <img v-if="asset.type?.startsWith('image')" :src="asset.url" class="asset-img" :alt="asset.caption" />
        <video v-else-if="asset.type?.startsWith('video')" :src="asset.url" class="asset-img" controls />
        <div v-else class="asset-file-icon">📄</div>
        <div class="asset-caption">{{ asset.caption || '未命名' }}</div>
      </div>
    </div>

    <!-- Stage notes -->
    <div v-if="notes" class="stage-notes">
      <strong>说明：</strong>{{ notes }}
    </div>
  </div>
</template>

<script setup lang="ts">
interface StageAsset {
  url: string
  caption?: string
  type?: string
  size?: number
}

defineProps<{
  stageKey: string
  assets: StageAsset[]
  notes: string
}>()
</script>

<style scoped>
.stage-assets-strip { padding: 12px 16px; }
.card-header-row {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
}
.card-header-row h3 { margin: 0; font-size: 0.82rem; }
.asset-total { font-size: 0.7rem; color: var(--muted); }

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
}
.asset-card { }
.asset-img {
  width: 100%;
  height: 72px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.asset-file-icon {
  width: 100%;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  background: oklch(96% 0.003 240);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.asset-caption {
  font-size: 0.65rem;
  color: var(--muted);
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-hint {
  font-size: 0.78rem;
  color: var(--muted);
  text-align: center;
  padding: 16px 8px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
}

.stage-notes {
  font-size: 0.75rem;
  color: var(--fg);
  margin-top: 10px;
  padding: 8px 10px;
  background: oklch(96% 0.003 240);
  border-radius: var(--radius-sm);
  line-height: 1.5;
}
.stage-notes strong { color: var(--accent); }
</style>

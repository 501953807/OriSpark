<template>
  <div class="version-strip card">
    <div class="card-header-row">
      <h3>📸 版本历史 ({{ versions.length }})</h3>
      <button class="btn btn-ghost btn-sm" @click="$emit('snapshot')">+ 快照</button>
    </div>
    <div v-if="!versions.length" class="card-empty">
      编辑作品后创建版本快照，可随时回滚到历史版本
    </div>
    <div v-else class="version-list">
      <div v-for="v in versions" :key="v.id" class="version-item">
        <span class="v-num">v{{ v.version_num }}</span>
        <span class="v-date">{{ v.created_at?.slice(0, 16) }}</span>
        <code class="v-hash mono" :title="v.file_hash">{{ v.file_hash?.slice(0, 8) }}…</code>
        <button
          v-if="v.version_num !== latestVersionNum"
          class="btn btn-ghost btn-sm"
          @click="$emit('rollback', v.id)"
          title="回滚到此版本"
        >↩</button>
        <span v-else class="v-current">当前</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  versions: any[]
  latestVersionNum: number
}>()

defineEmits<{
  snapshot: []
  rollback: [versionId: string]
}>()
</script>

<style scoped>
.version-strip { padding: 12px 16px; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-header-row h3 { margin: 0; font-size: 0.82rem; }
.card-empty { font-size: 0.78rem; color: var(--muted); padding: 8px 0; }
.version-list { display: flex; flex-direction: column; gap: 4px; max-height: 180px; overflow-y: auto; }
.version-item { display: flex; align-items: center; gap: 8px; padding: 5px 8px; border-radius: var(--radius-sm); font-size: 0.74rem; }
.version-item:hover { background: oklch(96% 0.003 240); }
.v-num { font-weight: 700; color: var(--accent); min-width: 28px; }
.v-date { color: var(--muted); flex: 1; }
.v-hash { font-size: 0.65rem; color: var(--muted); }
.v-current { font-size: 0.65rem; background: oklch(56% 0.12 170 / .1); color: var(--accent); padding: 2px 6px; border-radius: 100px; font-weight: 600; }
.mono { font-family: monospace; }
.btn-sm { padding: 3px 8px; font-size: 0.7rem; }
</style>

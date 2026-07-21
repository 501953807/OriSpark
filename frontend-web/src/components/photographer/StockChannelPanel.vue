<template>
  <div class="stock-channel-panel">
    <div v-if="!props.shot" class="empty-hint">
      <span class="hint-icon">📦</span>
      <p>请选择一张作品进行管理</p>
    </div>

    <template v-else>
      <!-- Header -->
      <div class="panel-header">
        <span class="shot-name">{{ props.shot.name }}</span>
        <span class="channel-count">{{ channels.length }} 个渠道</span>
      </div>

      <!-- Channel list -->
      <div class="channel-list">
        <div
          v-for="ch in channels"
          :key="ch.channel"
          :class="['channel-entry', `status-${ch.status}`]"
        >
          <div class="channel-info">
            <span class="channel-icon">{{ statusIcon(ch.status) }}</span>
            <span class="channel-name">{{ ch.channel }}</span>
          </div>
          <div class="channel-actions">
            <span :class="['channel-badge', `badge-${ch.status}`]">
              {{ STATUS_LABELS[ch.status] ?? ch.status }}
            </span>
            <button class="btn btn-xs btn-ghost" @click="removeChannel(ch.channel)" title="移除">
              &times;
            </button>
          </div>
        </div>

        <div v-if="channels.length === 0" class="empty-channels">
          <p>尚未添加任何销售渠道</p>
        </div>
      </div>

      <!-- Add channel form -->
      <div class="add-channel-form">
        <label class="form-label">添加渠道</label>
        <div class="form-row">
          <select v-model="newChannel" class="form-select">
            <option value="" disabled>-- 选择渠道 --</option>
            <option value="500px">500px</option>
            <option value="图虫">图虫</option>
            <option value="Fotolia">Fotolia</option>
            <option value="Shutterstock">Shutterstock</option>
            <option value="Adobe Stock">Adobe Stock</option>
          </select>
          <button
            class="btn btn-sm btn-primary"
            :disabled="!newChannel || hasChannel(newChannel)"
            @click="addChannel"
          >
            + 添加
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { PhotographerShot } from '@/types/photographer'

interface Props {
  shot: PhotographerShot | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'channel-added': [shotId: string, channel: string]
  'channel-removed': [shotId: string, channel: string]
}>()

const STATUS_LABELS: Record<string, string> = {
  submitted: '⏳ 已提交',
  active: '✅ 上架',
  rejected: '❌ 拒绝',
}

const newChannel = ref('')

// ── Computed channels ──────────────────────────────────────────
const channels = computed(() => {
  if (!props.shot?.stock_channels) return []
  return [...props.shot.stock_channels]
})

// ── Actions ────────────────────────────────────────────────────
function hasChannel(name: string): boolean {
  return channels.value.some((c: { channel: string }) => c.channel === name)
}

async function addChannel() {
  if (!props.shot || !newChannel.value || hasChannel(newChannel.value)) return

  try {
    emit('channel-added', props.shot.id, newChannel.value)
    newChannel.value = ''
    ;(window as any).$toast?.show(`${newChannel.value || '渠道'} 已添加`, 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '添加失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function removeChannel(channelName: string) {
  if (!props.shot) return

  try {
    emit('channel-removed', props.shot.id, channelName)
    ;(window as any).$toast?.show(`已移除 ${channelName}`, 'info')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '移除失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

function statusIcon(status: string): string {
  const icons: Record<string, string> = {
    submitted: '⏳',
    active: '✅',
    rejected: '❌',
  }
  return icons[status] ?? '○'
}
</script>

<style scoped>
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--muted);
  gap: 12px;
}

.hint-icon {
  font-size: 2.5rem;
}

/* ── Panel header ──────────────────────────────────────────── */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.shot-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--fg);
}

.channel-count {
  font-size: 0.78rem;
  color: var(--muted);
  background: var(--bg);
  padding: 2px 10px;
  border-radius: 100px;
}

/* ── Channel list ──────────────────────────────────────────── */
.channel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 0;
}

.channel-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: border-color 0.2s;
}

.channel-entry:hover {
  border-color: var(--muted);
}

.channel-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.channel-icon {
  font-size: 0.9rem;
}

.channel-name {
  font-size: 0.88rem;
  font-weight: 500;
  color: var(--fg);
}

.channel-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.channel-badge {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}

.badge-submitted {
  background: oklch(50% 0.02 240 / 0.15);
  color: var(--fg);
}

.badge-active {
  background: #16a34a;
  color: #fff;
}

.badge-rejected {
  background: #ef4444;
  color: #fff;
}

/* ── Empty states ──────────────────────────────────────────── */
.empty-channels {
  text-align: center;
  padding: 24px;
  color: var(--muted);
  font-size: 0.88rem;
  background: var(--bg);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border);
}

/* ── Add form ──────────────────────────────────────────────── */
.add-channel-form {
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.form-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.form-row {
  display: flex;
  gap: 8px;
}

.form-select {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
}

.form-select:focus {
  outline: none;
  border-color: var(--accent);
}

.btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: background 0.2s;
}

.btn:hover { background: var(--bg); }

.btn-sm { padding: 8px 16px; font-size: 0.84rem; }

.btn-xs {
  padding: 4px 8px;
  font-size: 0.9rem;
  line-height: 1;
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
}

.btn-xs:hover { color: #ef4444; }

.btn-ghost {
  background: transparent;
  color: var(--muted);
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>

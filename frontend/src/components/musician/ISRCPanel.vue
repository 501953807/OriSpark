<template>
  <div class="isrc-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3 class="panel-title">&#127993; ISRC 注册</h3>
      <span class="panel-desc">国际标准录音代码 (International Standard Recording Code)</span>
    </div>

    <!-- ISRC request form -->
    <div class="section">
      <h4 class="section-title">申请新 ISRC</h4>
      <div class="form-grid">
        <div class="form-group">
          <label class="form-label">曲目标题 *</label>
          <input
            v-model.trim="form.title"
            class="form-input"
            placeholder="请输入曲目标题"
            maxlength="200"
          />
        </div>

        <div class="form-group">
          <label class="form-label">艺术家 *</label>
          <input
            v-model.trim="form.artist"
            class="form-input"
            placeholder="表演者名称"
            maxlength="200"
          />
        </div>

        <div class="form-group">
          <label class="form-label">流派</label>
          <select v-model="form.genre" class="form-select">
            <option value="">请选择流派</option>
            <option value="pop">流行</option>
            <option value="rock">摇滚</option>
            <option value="hiphop">嘻哈</option>
            <option value="electronic">电子</option>
            <option value="rnb">R&B</option>
            <option value="jazz">爵士</option>
            <option value="classical">古典</option>
            <option value="folk">民谣</option>
            <option value="country">乡村</option>
            <option value="other">其他</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">格式</label>
          <select v-model="form.format" class="form-select">
            <option value="">请选择格式</option>
            <option value="mp3">MP3</option>
            <option value="flac">FLAC</option>
            <option value="wav">WAV</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">时长 (秒) *</label>
          <input
            v-model.number="form.duration"
            class="form-input"
            type="number"
            min="1"
            placeholder="例如 210"
          />
        </div>
      </div>

      <button
        class="btn btn-primary btn-full"
        :disabled="!isValidForm || submitting"
        @click="handleApply"
      >
        <span v-if="submitting" class="spinner-xs"></span>
        {{ submitting ? '提交中...' : '申请 ISRC' }}
      </button>
    </div>

    <!-- Release ISRC list -->
    <div class="section">
      <h4 class="section-title">发行列表</h4>

      <div v-if="releases.length === 0" class="empty-state">
        暂无发行记录
      </div>

      <div v-else class="isrc-table-wrapper">
        <table class="isrc-table">
          <thead>
            <tr>
              <th>曲目</th>
              <th>ISRC</th>
              <th>格式</th>
              <th>BPM</th>
              <th>流派</th>
              <th>情绪</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="release in releases" :key="release.id">
              <td class="cell-title">{{ release.title }}</td>
              <td class="cell-isrc">
                <span v-if="release.isrc">{{ release.isrc }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td>{{ release.format }}</td>
              <td>{{ release.bpm ?? '—' }}</td>
              <td>{{ release.genre ?? '—' }}</td>
              <td>{{ release.mood ?? '—' }}</td>
              <td>
                <span
                  class="status-badge"
                  :class="`status-${getStatus(release)}`"
                >
                  {{ getStatusLabel(getStatus(release)) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { MusicRelease, ReleaseFormat } from '@/types/musician'

interface Props {
  releases: MusicRelease[]
}

const props = defineProps<Props>()

interface FormState {
  title: string
  artist: string
  genre: string
  format: ReleaseFormat | ''
  duration: number
}

const form = ref<FormState>({
  title: '',
  artist: '',
  genre: '',
  format: '',
  duration: 0,
})

const submitting = ref(false)

const isValidForm = computed(() => {
  return (
    form.value.title.length > 0 &&
    form.value.artist.length > 0 &&
    form.value.duration > 0
  )
})

// ISRC status: not-applied / applied / assigned
function getStatus(release: MusicRelease): 'not-applied' | 'applied' | 'assigned' {
  if (release.isrc) return 'assigned'
  if (release.distribution_status === 'pending') return 'applied'
  return 'not-applied'
}

function getStatusLabel(status: 'not-applied' | 'applied' | 'assigned'): string {
  switch (status) {
    case 'not-applied':
      return '未申请'
    case 'applied':
      return '已申请'
    case 'assigned':
      return '已分配'
  }
}

async function handleApply() {
  if (!isValidForm.value) return

  submitting.value = true
  try {
    // Simulate API call — replace with actual store action
    await new Promise<void>((resolve) => {
      setTimeout(resolve, 800)
    })

    // Emit success event so parent can refresh releases list
    emit('applied', {
      title: form.value.title,
      artist: form.value.artist,
      genre: form.value.genre,
      format: form.value.format || 'mp3',
      duration_seconds: form.value.duration,
    })

    // Reset form immutably
    form.value = { title: '', artist: '', genre: '', format: '', duration: 0 }

    ;(window as any)?.$toast?.show('ISRC 申请已提交', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '申请失败'
    ;(window as any)?.$toast?.show(msg, 'error')
  } finally {
    submitting.value = false
  }
}

const emit = defineEmits<{
  applied: [payload: { title: string; artist: string; genre: string; format: ReleaseFormat; duration_seconds: number }]
}>()
</script>

<style scoped>
.isrc-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ── Panel header ─────────────────────────────────────────────── */
.panel-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.panel-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0;
}

.panel-desc {
  font-size: 0.82rem;
  color: var(--muted);
}

/* ── Sections ─────────────────────────────────────────────────── */
.section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0;
}

/* ── Form ─────────────────────────────────────────────────────── */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-input,
.form-select {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--accent);
}

/* ── Table ────────────────────────────────────────────────────── */
.isrc-table-wrapper {
  overflow-x: auto;
}

.isrc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.isrc-table th,
.isrc-table td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.isrc-table th {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.cell-title {
  font-weight: 500;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.cell-isrc {
  font-family: monospace;
  font-size: 0.82rem;
  color: var(--accent);
}

.text-muted {
  color: var(--muted);
}

/* ── Status badges ────────────────────────────────────────────── */
.status-badge {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 100px;
}

.status-not-applied {
  background: oklch(50% 0.02 240 / 0.1);
  color: var(--muted);
}

.status-applied {
  background: oklch(60% 0.12 85 / 0.15);
  color: #d97706;
}

.status-assigned {
  background: oklch(60% 0.12 150 / 0.15);
  color: #16a34a;
}

/* ── Button ────────────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border);
  font-family: inherit;
  transition: opacity 0.2s;
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-full {
  width: 100%;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.spinner-xs {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── Empty ────────────────────────────────────────────────────── */
.empty-state {
  padding: 24px;
  text-align: center;
  font-size: 0.88rem;
  color: var(--muted);
  font-style: italic;
  border: 1px dashed var(--border);
  border-radius: var(--radius);
}
</style>

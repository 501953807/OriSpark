<template>
  <div class="manuscript-editor">
    <!-- Panel header -->
    <div class="panel-header">
      <div>
        <h3 class="panel-title">📝 手稿编辑器</h3>
        <span class="panel-desc">编辑章节内容、管理版本和状态</span>
      </div>

      <span
        class="status-badge"
        :class="statusClass"
      >
        {{ statusLabel }}
      </span>
    </div>

    <!-- Chapter info form -->
    <div class="form-section">
      <div class="form-row">
        <label class="form-label">章节号</label>
        <input
          v-model.number="chapterNumber"
          type="number"
          min="1"
          class="form-input"
          @input="markDirty"
        />
      </div>

      <div class="form-row">
        <label class="form-label">章节标题</label>
        <input
          v-model="chapterTitle"
          type="text"
          class="form-input form-input-lg"
          placeholder="输入章节标题..."
          @input="markDirty"
        />
      </div>
    </div>

    <!-- Content editor -->
    <div class="editor-section">
      <div class="editor-toolbar">
        <span class="toolbar-label">Markdown 内容</span>
        <div class="word-count">
          <span class="count-total">{{ totalCount }} 字</span>
          <span class="count-separator">/</span>
          <span class="count-original">{{ manuscript.word_count ?? 0 }} 字</span>
        </div>
      </div>

      <textarea
        ref="editorRef"
        v-model="content"
        class="editor-textarea"
        placeholder="在此输入 Markdown 内容..."
        @input="onContentChange"
      ></textarea>
    </div>

    <!-- Version info -->
    <div class="version-bar">
      <span class="version-label">版本: {{ manuscript.version ?? 1 }}</span>
      <span v-if="manuscript.updated_at" class="version-time">
        最后更新: {{ formatDate(manuscript.updated_at) }}
      </span>
    </div>

    <!-- Actions -->
    <div class="action-section">
      <button
        class="btn btn-secondary"
        :disabled="!hasChanges || saving"
        @click="handleSave"
      >
        <span v-if="saving" class="spinner"></span>
        {{ saving ? '保存中...' : '保存草稿' }}
      </button>

      <button
        class="btn btn-primary"
        :disabled="!hasChanges || saving"
        @click="handlePublish"
      >
        <span v-if="saving" class="spinner"></span>
        {{ saving ? '发布中...' : '发布' }}
      </button>

      <select
        v-model="nextStatus"
        class="form-select-sm"
        :disabled="!hasChanges || saving"
      >
        <option value="draft">草稿</option>
        <option value="revising">修订中</option>
        <option value="final">终稿</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Manuscript, ManuscriptStatus } from '@/types/writer'

interface Props {
  manuscript: Manuscript
  onSave?: (manuscript: Manuscript, content: string) => Promise<void>
  onPublish?: (manuscript: Manuscript, content: string, status: ManuscriptStatus) => Promise<void>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  update: [manuscript: Manuscript]
}>()

// ── Local editable state ────────────────────────────────────────
const chapterNumber = ref(props.manuscript.chapter_number ?? 1)
const chapterTitle = ref('')
const content = ref('')
const nextStatus = ref<ManuscriptStatus>('draft')

// Track if anything has changed from the original
const hasChanges = ref(false)
const saving = ref(false)
const editorRef = ref<HTMLTextAreaElement | null>(null)

// ── Sync with props when manuscript changes ────────────────────
watch(
  () => props.manuscript,
  (ms) => {
    chapterNumber.value = ms.chapter_number ?? 1
    chapterTitle.value = ms.title ?? ''
    content.value = ms.content ?? ''
    nextStatus.value = ms.status as ManuscriptStatus ?? 'draft'
    hasChanges.value = false
  },
  { deep: true },
)

// ── Computed ───────────────────────────────────────────────────
const statusKey = computed<ManuscriptStatus>(() => props.manuscript.status)

const STATUS_LABELS: Record<ManuscriptStatus, string> = {
  draft: '草稿',
  revising: '修订中',
  final: '终稿',
}

const STATUS_CLASSES: Record<ManuscriptStatus, string> = {
  draft: 'status-draft',
  revising: 'status-revising',
  final: 'status-final',
}

const statusLabel = computed(() => STATUS_LABELS[statusKey.value])
const statusClass = computed(() => STATUS_CLASSES[statusKey.value])

const totalCount = computed(() => {
  return content.value.length
})

// ── Change detection ───────────────────────────────────────────
function onContentChange() {
  markDirty()
}

function markDirty() {
  hasChanges.value = true
}

// ── Actions ────────────────────────────────────────────────────
async function handleSave() {
  if (!hasChanges.value) {
    ;(window as any)?.$toast?.show('没有内容更改', 'info')
    return
  }

  saving.value = true
  try {
    if (props.onSave) {
      await props.onSave(props.manuscript, content.value)
    }
    hasChanges.value = false
    ;(window as any)?.$toast?.show('保存成功', 'success')
    emit('update', props.manuscript)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存失败'
    ;(window as any)?.$toast?.show(msg, 'error')
  } finally {
    saving.value = false
  }
}

async function handlePublish() {
  if (!hasChanges.value) {
    ;(window as any)?.$toast?.show('没有内容更改', 'info')
    return
  }

  saving.value = true
  try {
    const newStatus = nextStatus.value

    if (props.onPublish) {
      await props.onPublish(props.manuscript, content.value, newStatus)
    }

    hasChanges.value = false
    ;(window as any)?.$toast?.show(
      `已${newStatus === 'final' ? '发布为终稿' : '发布'}`,
      'success',
    )
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '发布失败'
    ;(window as any)?.$toast?.show(msg, 'error')
  } finally {
    saving.value = false
  }
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.manuscript-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Panel header ─────────────────────────────────────────────── */
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
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

.status-badge {
  padding: 4px 12px;
  border-radius: 100px;
  font-size: 0.76rem;
  font-weight: 600;
  flex-shrink: 0;
}

.status-draft {
  background: oklch(90% 0.04 260 / 0.15);
  color: #7c3aed;
}

.status-revising {
  background: oklch(88% 0.1 35 / 0.15);
  color: #d97706;
}

.status-final {
  background: oklch(85% 0.12 145 / 0.15);
  color: #16a34a;
}

/* ── Form section ─────────────────────────────────────────────── */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  display: block;
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: var(--accent);
}

.form-input-lg {
  font-size: 1rem;
  font-weight: 600;
  padding: 10px 14px;
}

/* ── Editor ───────────────────────────────────────────────────── */
.editor-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar-label {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.word-count {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: 0.8rem;
}

.count-total {
  font-weight: 600;
  color: var(--fg);
}

.count-separator {
  color: var(--muted);
}

.count-original {
  color: var(--muted);
  font-size: 0.76rem;
}

.editor-textarea {
  width: 100%;
  min-height: 280px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  line-height: 1.7;
  background: var(--surface);
  color: var(--fg);
  font-family: 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', monospace;
  resize: vertical;
  transition: border-color 0.2s;
}

.editor-textarea::placeholder {
  color: var(--muted);
  font-style: italic;
}

.editor-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

/* ── Version bar ──────────────────────────────────────────────── */
.version-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  font-size: 0.78rem;
  color: var(--muted);
}

.version-label {
  font-weight: 600;
  color: var(--fg);
}

/* ── Actions ──────────────────────────────────────────────────── */
.action-section {
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: background 0.2s, opacity 0.2s;
  flex: 1;
}

.btn:hover:not(:disabled) {
  background: var(--bg);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.form-select-sm {
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  cursor: pointer;
}

.form-select-sm:focus {
  outline: none;
  border-color: var(--accent);
}

/* ── Spinner ──────────────────────────────────────────────────── */
.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.btn-secondary .spinner {
  border-color: rgba(0, 0, 0, 0.2);
  border-top-color: #666;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

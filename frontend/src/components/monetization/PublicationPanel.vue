<!-- PublicationPanel — POD发布管理

Shows publication records for a listing across POD platforms.
Supports: view status, jump to platform, add new publication.
-->
<template>
  <div class="publication-panel">
    <!-- Header -->
    <div class="panel-header">
      <h4>🖨️ POD 发布管理</h4>
      <button class="btn-add" @click="showAddDialog = true">+ 添加发布</button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-state">加载中...</div>

    <!-- Empty state -->
    <div v-else-if="!publications.length" class="empty-state">
      <span class="empty-icon">📦</span>
      <p>暂无发布记录</p>
      <button class="btn-add" @click="showAddDialog = true">添加第一个发布</button>
    </div>

    <!-- Publication list -->
    <div v-else class="pub-list">
      <div v-for="pub in publications" :key="pub.id" class="pub-item">
        <div class="pub-info">
          <div class="pub-platform">{{ pub.platform }}</div>
          <div class="pub-url" v-if="pub.listing_url">
            <a :href="pub.listing_url" target="_blank" rel="noopener">{{ pub.listing_url }}</a>
          </div>
          <div class="pub-meta">
            <span :class="['pub-status', pub.status]">{{ statusLabel(pub.status) }}</span>
            <span v-if="pub.published_at" class="pub-date">
              发布于 {{ formatDate(pub.published_at) }}
            </span>
          </div>
        </div>
        <div class="pub-actions">
          <a v-if="pub.listing_url" :href="pub.listing_url" target="_blank" rel="noopener" class="pub-link-btn" title="前往平台">
            🔗 前往
          </a>
          <button class="pub-edit-btn" @click="editPub(pub)" title="编辑">✏️</button>
          <button class="pub-delete-btn" @click="deletePub(pub.id)" title="删除">🗑️</button>
        </div>
      </div>
    </div>

    <!-- Add/Edit dialog -->
    <div v-if="showAddDialog" class="modal-overlay" @click.self="showAddDialog = false">
      <div class="modal">
        <h4>{{ editingPub ? '编辑发布' : '添加 POD 发布' }}</h4>
        <div class="form-group">
          <label>平台</label>
          <select v-model="form.platform" class="form-select">
            <option v-for="p in platforms" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>商品链接</label>
          <input v-model="form.listing_url" placeholder="https://..." class="form-input" />
        </div>
        <div class="form-group">
          <label>状态</label>
          <select v-model="form.status" class="form-select">
            <option value="draft">草稿</option>
            <option value="published">已发布</option>
            <option value="paused">暂停</option>
          </select>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="cancel">取消</button>
          <button class="btn-save" @click="savePub" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { supplyApi } from '@/api/supply'

interface Props {
  listingId: string
}
const props = defineProps<Props>()

const emit = defineEmits<{ (e: 'publish', id: string): void }>()

interface PubRecord {
  id: string
  platform: string
  status: string
  listing_url: string | null
  published_at: string | null
}

const publications = ref<PubRecord[]>([])
const loading = ref(false)
const saving = ref(false)
const showAddDialog = ref(false)
const editingPub = ref<PubRecord | null>(null)

const platforms = [
  { id: 'printful', name: 'Printful' },
  { id: 'redbubble', name: 'Redbubble' },
  { id: 'printify', name: 'Printify' },
  { id: 'society6', name: 'Society6' },
  { id: 'yingge', name: '印鸽' },
  { id: 'gelato', name: 'Gelato' },
]

const form = ref({ platform: 'printful', listing_url: '', status: 'draft' })

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    draft: '草稿', published: '已发布', paused: '暂停',
  }
  return map[s] || s
}

function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('zh-CN')
}

async function loadPublications() {
  loading.value = true
  try {
    const { data } = await supplyApi.getListing(props.listingId)
    publications.value = (data as any).publications || []
  } catch {
    // Fallback: empty list
  } finally {
    loading.value = false
  }
}

function editPub(pub: PubRecord) {
  editingPub.value = pub
  form.value = {
    platform: pub.platform,
    listing_url: pub.listing_url || '',
    status: pub.status,
  }
  showAddDialog.value = true
}

async function savePub() {
  saving.value = true
  try {
    await supplyApi.addListingPublication(props.listingId, {
      platform: form.value.platform,
      listing_url: form.value.listing_url,
      status: form.value.status,
    })
    showAddDialog.value = false
    editingPub.value = null
    await loadPublications()
  } catch {
    // Error toast
  } finally {
    saving.value = false
  }
}

function cancel() {
  showAddDialog.value = false
  editingPub.value = null
}

async function deletePub(id: string) {
  if (!confirm('确定删除此发布记录？')) return
  try {
    // Soft delete via PATCH
    await supplyApi.updateListing(props.listingId, { status: 'discontinued' })
    await loadPublications()
  } catch {
    // Error toast
  }
}

onMounted(loadPublications)
</script>

<style scoped>
.publication-panel { padding: 0 4px; }

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel-header h4 { margin: 0; font-size: .9rem; }

.btn-add {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: .78rem;
  cursor: pointer;
}

.loading-state, .empty-state {
  text-align: center;
  padding: 32px 0;
  color: var(--muted);
}

.empty-icon { font-size: 2rem; display: block; margin-bottom: 8px; }

.pub-list { display: flex; flex-direction: column; gap: 8px; }

.pub-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
}

.pub-platform { font-weight: 700; font-size: .88rem; }

.pub-url { font-size: .72rem; color: var(--muted); margin-top: 2px; }
.pub-url a { color: var(--accent); word-break: break-all; }

.pub-meta { display: flex; gap: 8px; align-items: center; margin-top: 4px; }

.pub-status {
  padding: 1px 8px;
  border-radius: 100px;
  font-size: .65rem;
  font-weight: 600;
}

.pub-status.published { background: oklch(56% 0.12 140 / .15); color: oklch(56% 0.12 140); }
.pub-status.draft { background: oklch(75% 0.08 80 / .15); color: oklch(65% 0.1 80); }
.pub-status.paused { background: oklch(56% 0.12 20 / .15); color: oklch(56% 0.12 20); }

.pub-date { font-size: .68rem; color: var(--muted); }

.pub-actions { display: flex; gap: 4px; }
.pub-link-btn, .pub-edit-btn, .pub-delete-btn {
  background: none; border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 4px 8px; cursor: pointer; font-size: .82rem;
}
.pub-link-btn:hover { border-color: var(--accent); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: oklch(20% 0.02 180 / .5);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 24px;
  width: 400px;
  max-width: 90vw;
}

.modal h4 { margin: 0 0 16px; }

.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: .78rem; margin-bottom: 4px; color: var(--muted); }

.form-select, .form-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: .85rem;
  background: var(--surface);
}

.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 6px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: none; cursor: pointer; font-size: .82rem;
}
.btn-save {
  padding: 6px 16px; border: none; border-radius: var(--radius-sm);
  background: var(--accent); color: #fff; cursor: pointer; font-size: .82rem;
}
.btn-save:disabled { opacity: .5; cursor: not-allowed; }
</style>

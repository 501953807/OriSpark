<template>
  <div class="musician-view">
    <!-- Error banner -->
    <div v-if="store.errorMsg" class="error-banner">
      <span>{{ store.errorMsg }}</span>
      <button @click="store.errorMsg = ''">&times;</button>
    </div>
    <!-- Stats bar -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">&#127925; 总发行</span>
        <span class="stat-value">{{ statsDisplay.total_releases }}</span>
      </div>
      <div class="stat-item stat-albums">
        <span class="stat-label">&#127911; 专辑</span>
        <span class="stat-value">{{ statsDisplay.total_albums }}</span>
      </div>
      <div class="stat-item stat-distributed">
        <span class="stat-label">&#128268; 已分发</span>
        <span class="stat-value">{{ statsDisplay.distributed_count }}</span>
      </div>
      <div class="stat-item stat-splits">
        <span class="stat-label">&#128200; 待签署分成</span>
        <span class="stat-value">{{ statsDisplay.pending_splits }}</span>
      </div>
      <div class="stat-item stat-revenue">
        <span class="stat-label">&#128176; 本月营收</span>
        <span class="stat-value">&yen;{{ statsDisplay.monthly_revenue.toLocaleString() }}</span>
      </div>
    </div>
    <!-- Tab bar -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.icon }} {{ tab.label }}
      </button>
    </div>
    <!-- ============================================ -->
    <!-- ── Releases tab ──────────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'releases'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">音乐发行</h2>
        <button class="btn btn-primary btn-sm" @click="showReleaseForm = !showReleaseForm">
          {{ showReleaseForm ? '取消' : '+ 新建发行' }}
        </button>
      </div>
      <!-- Create release form -->
      <div v-if="showReleaseForm" class="form-card">
        <h3 class="form-title">新建发行</h3>
        <div class="form-grid">
          <input v-model="releaseForm.title" class="form-input" placeholder="曲目标题" />
          <input v-model="releaseForm.isrc" class="form-input" placeholder="ISRC (可选)" />
          <select v-model="releaseForm.format" class="form-input">
            <option disabled value="">选择格式</option>
            <option value="mp3">MP3</option>
            <option value="flac">FLAC</option>
            <option value="wav">WAV</option>
          </select>
          <input v-model="releaseForm.genre" class="form-input" placeholder="流派" />
          <input v-model="releaseForm.mood" class="form-input" placeholder="情绪" />
          <input
            v-model.number="releaseForm.bpm"
            type="number"
            class="form-input"
            placeholder="BPM"
          />
          <input
            v-model.number="releaseForm.duration_seconds"
            type="number"
            class="form-input"
            placeholder="时长 (秒)"
          />
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" @click="handleCreateRelease">创建</button>
          <button class="btn btn-outline" @click="showReleaseForm = false">取消</button>
        </div>
      </div>
      <!-- Release list -->
      <div v-if="store.releases.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">&#127925;</span>
        <p>暂无音乐发行，点击上方按钮创建第一个发行。</p>
      </div>
      <div v-else class="release-grid">
        <div v-for="r in store.releases" :key="r.id" class="release-card">
          <div class="release-card-top">
            <span class="release-title">{{ r.title || '未命名' }}</span>
            <span :class="['badge', 'badge-status', statusBadgeClass(r.distribution_status)]">
              {{ statusLabel(r.distribution_status) }}
            </span>
          </div>
          <div class="release-meta">
            <span v-if="r.isrc" class="meta-item">&#128218; {{ r.isrc }}</span>
            <span class="meta-item">&#127926; {{ r.format.toUpperCase() }}</span>
            <span v-if="r.bpm" class="meta-item">&#9835; {{ r.bpm }} BPM</span>
          </div>
          <div class="release-meta">
            <span v-if="r.genre" class="meta-item">{{ r.genre }}</span>
            <span v-if="r.mood" class="meta-item">{{ r.mood }}</span>
            <span v-if="r.duration_seconds" class="meta-item">
              {{ Math.floor(r.duration_seconds / 60) }}:{{ String(r.duration_seconds % 60).padStart(2, '0') }}
            </span>
          </div>
          <div class="release-actions">
            <button class="btn btn-sm btn-outline" @click="handleDeleteRelease(r.id)">删除</button>
          </div>
        </div>
      </div>
    </div>
    <!-- ============================================ -->
    <!-- ── Albums tab ────────────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'albums'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">专辑管理</h2>
        <button class="btn btn-primary btn-sm" @click="showAlbumForm = !showAlbumForm">
          {{ showAlbumForm ? '取消' : '+ 新建专辑' }}
        </button>
      </div>
      <!-- Create album form -->
      <div v-if="showAlbumForm" class="form-card">
        <h3 class="form-title">新建专辑</h3>
        <div class="form-grid">
          <input v-model="albumForm.title" class="form-input" placeholder="专辑标题" />
          <select v-model="albumForm.album_type" class="form-input">
            <option disabled value="">专辑类型</option>
            <option value="single">Single</option>
            <option value="ep">EP</option>
            <option value="album">Album</option>
            <option value="compilation">Compilation</option>
          </select>
          <input v-model="albumForm.label" class="form-input" placeholder="厂牌/唱片公司" />
          <input
            v-model.number="albumForm.total_tracks"
            type="number"
            class="form-input"
            placeholder="曲目数"
          />
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" @click="handleCreateAlbum">创建</button>
          <button class="btn btn-outline" @click="showAlbumForm = false">取消</button>
        </div>
      </div>
      <!-- Album list -->
      <div v-if="store.albums.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">&#127911;</span>
        <p>暂无专辑，点击上方按钮创建第一个专辑。</p>
      </div>
      <div v-else class="album-grid">
        <div v-for="a in store.albums" :key="a.id" class="album-card">
          <div class="album-cover-placeholder">
            <span class="album-icon">&#127911;</span>
          </div>
          <div class="album-info">
            <span class="album-title">{{ a.title || '未命名专辑' }}</span>
            <span :class="['badge', 'badge-album-type', badgeClass(a.album_type)]">
              {{ albumTypeLabel(a.album_type) }}
            </span>
            <div class="album-meta">
              <span v-if="a.label" class="meta-item">&#127990; {{ a.label }}</span>
              <span v-if="a.total_tracks" class="meta-item">{{ a.total_tracks }} 首</span>
              <span v-if="a.release_date" class="meta-item">{{ a.release_date.slice(0, 10) }}</span>
            </div>
          </div>
          <div class="album-actions">
            <button class="btn btn-sm btn-outline" @click="handleDeleteAlbum(a.id)">删除</button>
          </div>
        </div>
      </div>
    </div>
    <!-- ============================================ -->
    <!-- ── Split Sheets tab ──────────────────────── -->
    <!-- ============================================ -->
    <div v-if="activeTab === 'splits'" class="tab-panel">
      <div class="panel-header">
        <h2 class="section-title">分成协议</h2>
        <button class="btn btn-primary btn-sm" @click="showSplitForm = !showSplitForm">
          {{ showSplitForm ? '取消' : '+ 新建分成' }}
        </button>
      </div>
      <!-- Create split sheet form -->
      <div v-if="showSplitForm" class="form-card">
        <h3 class="form-title">新建分成协议</h3>
        <div class="form-grid">
          <input v-model="splitForm.title" class="form-input" placeholder="协议标题" />
          <input
            v-model.number="splitForm.publishing_share"
            type="number"
            step="0.01"
            class="form-input"
            placeholder="词曲版权分成 (%)"
          />
          <input
            v-model.number="splitForm.master_share"
            type="number"
            step="0.01"
            class="form-input"
            placeholder="录音版权分成 (%)"
          />
        </div>
        <div class="form-actions">
          <button class="btn btn-primary" @click="handleCreateSplitSheet">创建</button>
          <button class="btn btn-outline" @click="showSplitForm = false">取消</button>
        </div>
      </div>
      <!-- Split sheet list -->
      <div v-if="store.splitSheets.length === 0 && !store.loading" class="empty-state">
        <span class="empty-icon">&#128200;</span>
        <p>暂无分成协议。</p>
      </div>
      <div v-else class="split-list">
        <div v-for="s in store.splitSheets" :key="s.id" class="split-card">
          <div class="split-header">
            <span class="split-title">{{ s.title || '未命名协议' }}</span>
            <span :class="['badge', 'badge-split', splitStatusBadgeClass(s.status)]">
              {{ splitStatusLabel(s.status) }}
            </span>
          </div>
          <div class="split-meta">
            <span v-if="s.publishing_share != null" class="meta-item">
              &#9835; 词曲: {{ s.publishing_share }}%
            </span>
            <span v-if="s.master_share != null" class="meta-item">
              &#127925; 录音: {{ s.master_share }}%
            </span>
            <span v-if="s.splits?.length" class="meta-item">
              &#128101; {{ s.splits.length }} 方分成
            </span>
          </div>
        </div>
      </div>
    </div>
    <!-- Loading overlay -->
    <div v-if="store.loading" class="loading-overlay">
      <div class="spinner">&#8987; 加载中...</div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useMusicianStore } from '@/stores/useMusicianStore'
import type {
  DistributionStatus,
  SplitSheetStatus,
  AlbumType,
} from '@/types/musician'

const store = useMusicianStore()

// ── Tabs ──────────────────────────────────────────────────────
const tabs = [
  { key: 'releases', label: '发行', icon: '&#127925;' },
  { key: 'albums', label: '专辑', icon: '&#127911;' },
  { key: 'splits', label: '分成协议', icon: '&#128200;' },
]
const activeTab = ref<string>('releases')

// ── Stats ─────────────────────────────────────────────────────
const statsDisplay = computed(() => store.stats ?? {
  total_releases: 0,
  total_albums: 0,
  distributed_count: 0,
  pending_splits: 0,
  monthly_revenue: 0,
})

// ── Release form ──────────────────────────────────────────────
const showReleaseForm = ref(false)
const releaseForm = reactive({
  title: '',
  isrc: '',
  format: 'mp3' as 'mp3' | 'flac' | 'wav',
  genre: '',
  mood: '',
  bpm: undefined as number | undefined,
  duration_seconds: undefined as number | undefined,
})

async function handleCreateRelease() {
  if (!releaseForm.title.trim()) {
    ;(window as any).$toast?.show('请填写曲目标题', 'error')
    return
  }
  try {
    await store.createRelease({
      title: releaseForm.title,
      isrc: releaseForm.isrc || undefined,
      format: releaseForm.format,
      genre: releaseForm.genre || undefined,
      mood: releaseForm.mood || undefined,
      bpm: releaseForm.bpm,
      duration_seconds: releaseForm.duration_seconds,
    })
    ;(window as any).$toast?.show('发行创建成功', 'success')
    Object.assign(releaseForm, { title: '', isrc: '', genre: '', mood: '', bpm: undefined, duration_seconds: undefined })
    showReleaseForm.value = false
    await store.fetchReleases()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleDeleteRelease(id: string) {
  try {
    await store.deleteRelease(id)
    ;(window as any).$toast?.show('发行已删除', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '删除失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Album form ────────────────────────────────────────────────
const showAlbumForm = ref(false)
const albumForm = reactive({
  title: '',
  album_type: 'album' as AlbumType,
  label: '',
  total_tracks: undefined as number | undefined,
})

const albumTypeLabels: Record<AlbumType, string> = {
  single: '单曲',
  ep: 'EP',
  album: '专辑',
  compilation: '合辑',
}

function albumTypeLabel(t: AlbumType): string {
  return albumTypeLabels[t] ?? t
}

function badgeClass(at: AlbumType): string {
  return at || 'album'
}

async function handleCreateAlbum() {
  if (!albumForm.title.trim()) {
    ;(window as any).$toast?.show('请填写专辑标题', 'error')
    return
  }
  try {
    await store.createAlbum({
      title: albumForm.title,
      album_type: albumForm.album_type,
      label: albumForm.label || undefined,
      total_tracks: albumForm.total_tracks,
    })
    ;(window as any).$toast?.show('专辑创建成功', 'success')
    Object.assign(albumForm, { title: '', label: '', total_tracks: undefined })
    showAlbumForm.value = false
    await store.fetchAlbums()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleDeleteAlbum(id: string) {
  try {
    await store.deleteRelease(id)
    ;(window as any).$toast?.show('专辑已删除', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '删除失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Split sheet form ──────────────────────────────────────────
const showSplitForm = ref(false)
const splitForm = reactive({
  title: '',
  publishing_share: undefined as number | undefined,
  master_share: undefined as number | undefined,
})

const splitStatusLabels: Record<SplitSheetStatus, string> = {
  draft: '草稿',
  signing: '签署中',
  signed: '已签署',
  active: '生效',
}

function splitStatusLabel(s: SplitSheetStatus): string {
  return splitStatusLabels[s] ?? s
}

function splitStatusBadgeClass(s: SplitSheetStatus): string {
  const map: Record<SplitSheetStatus, string> = {
    draft: 'badge-draft',
    signing: 'badge-signing',
    signed: 'badge-signed',
    active: 'badge-active',
  }
  return map[s] ?? 'badge-draft'
}

async function handleCreateSplitSheet() {
  if (!splitForm.title.trim()) {
    ;(window as any).$toast?.show('请填写协议标题', 'error')
    return
  }
  try {
    await store.createSplitSheet({
      title: splitForm.title,
      publishing_share: splitForm.publishing_share,
      master_share: splitForm.master_share,
    })
    ;(window as any).$toast?.show('分成协议创建成功', 'success')
    Object.assign(splitForm, { title: '', publishing_share: undefined, master_share: undefined })
    showSplitForm.value = false
    await store.fetchSplitSheets()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Helpers ───────────────────────────────────────────────────
const statusLabels: Record<DistributionStatus, string> = {
  pending: '待分发',
  distributing: '分发中',
  distributed: '已分发',
}

function statusLabel(s: DistributionStatus): string {
  return statusLabels[s] ?? s
}

function statusBadgeClass(s: DistributionStatus): string {
  const map: Record<DistributionStatus, string> = {
    pending: 'badge-pending',
    distributing: 'badge-distributing',
    distributed: 'badge-distributed',
  }
  return map[s] ?? 'badge-pending'
}

// ── Lifecycle ─────────────────────────────────────────────────
onMounted(async () => {
  try {
    await store.fetchAll()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '加载失败'
    store.errorMsg = msg
  }
})
</script>
<style scoped>
.musician-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.loading-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(2px);
  z-index: 100;
  font-size: 0.9rem;
  color: var(--muted);
  font-weight: 500;
}
.spinner {
  display: flex;
  align-items: center;
  gap: 8px;
}
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: oklch(65% 0.18 20);
  color: #fff;
  border-radius: var(--radius);
  font-size: 0.88rem;
}
.error-banner button {
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.8;
}
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}
.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  flex: 1;
  min-width: 160px;
}
.stat-label {
  font-size: 0.82rem;
  color: var(--muted);
  white-space: nowrap;
}
.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--fg);
  font-family: var(--font-display);
}
.stat-albums .stat-value { color: #7c3aed; }
.stat-distributed .stat-value { color: #16a34a; }
.stat-splits .stat-value { color: #ea580c; }
.stat-revenue .stat-value { color: #9333ea; }
.tab-bar {
  display: flex;
  gap: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px;
}
.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: calc(var(--radius) - 6px);
  background: transparent;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  font-family: inherit;
}
.tab-btn:hover {
  color: var(--fg);
  background: var(--bg);
}
.tab-btn.active {
  background: var(--accent);
  color: #fff;
}
.tab-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.section-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0;
}
.form-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}
.form-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0 0 16px 0;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
.form-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  background: var(--bg);
  color: var(--fg);
  font-family: inherit;
}
.form-actions {
  display: flex;
  gap: 8px;
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
.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}
.btn-primary:hover {
  opacity: 0.9;
  background: var(--accent);
}
.btn-outline {
  background: transparent;
  border-color: var(--muted);
}
.badge {
  display: inline-block;
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.badge-status {
  background: var(--bg);
  color: var(--muted);
}
.badge-pending { background: #fef3c7; color: #92400e; }
.badge-distributing { background: #dbeafe; color: #1d4ed8; }
.badge-distributed { background: #dcfce7; color: #166534; }
.badge-album-type {
  background: oklch(85% 0.08 280);
  color: oklch(35% 0.08 280);
}
.badge-album-type.single { background: #ede9fe; color: #5b21b6; }
.badge-album-type.ep { background: #fce7f3; color: #9d174d; }
.badge-album-type.compilation { background: #ffedd5; color: #9a3412; }
.badge-split { background: var(--bg); color: var(--muted); }
.badge-draft { background: #f1f5f9; color: #475569; }
.badge-signing { background: #fef3c7; color: #92400e; }
.badge-signed { background: #dbeafe; color: #1d4ed8; }
.badge-active { background: #dcfce7; color: #166534; }
.release-grid,
.album-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.release-card,
.album-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  transition: box-shadow 0.2s;
}
.release-card:hover,
.album-card:hover {
  box-shadow: 0 4px 16px oklch(0 0 0 / 0.08);
}
.release-card-top,
.split-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.release-title,
.split-title,
.album-title {
  flex: 1;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.release-meta,
.album-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.8rem;
  color: var(--muted);
}
.release-actions,
.album-actions {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}
.album-cover-placeholder {
  width: 100%;
  aspect-ratio: 1;
  background: linear-gradient(135deg, var(--bg), var(--surface));
  border: 1px solid var(--border);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  opacity: 0.6;
}
.album-info {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.meta-item {
  white-space: nowrap;
}
.split-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.split-card {
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--muted);
  font-size: 0.9rem;
  text-align: center;
  gap: 12px;
}
.empty-icon {
  font-size: 2.5rem;
  opacity: 0.5;
}
</style>

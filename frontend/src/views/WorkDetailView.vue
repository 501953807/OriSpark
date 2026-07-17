<template>
  <div class="detail-card">
    <!-- ===== Toolbar ===== -->
    <div class="detail-toolbar">
      <router-link to="/app/works" class="btn btn-ghost btn-sm">← 返回作品列表</router-link>
      <span class="toolbar-title">{{ work?.title || '未命名作品' }}</span>
      <div class="toolbar-actions">
        <a v-if="previewUrl" :href="previewUrl" download class="btn btn-secondary btn-sm">📥 下载</a>
        <button v-if="!work?.is_verified" class="btn btn-secondary btn-sm" @click="doNotarize">🔒 存证</button>
        <button class="btn btn-primary btn-sm" @click="showEditPanel = true">✏️ 编辑</button>
        <div class="dropdown-wrapper">
          <button class="btn btn-ghost btn-sm" @click="showMoreMenu = !showMoreMenu">⋯</button>
          <div v-if="showMoreMenu" class="dropdown-menu">
            <button class="dropdown-item" @click="doMonitorScan">🔍 侵权扫描</button>
            <button class="dropdown-item" @click="handleDelete">🗑️ 删除作品</button>
          </div>
        </div>
      </div>
    </div>

    <LoadingSpinner v-if="loading" text="加载中..." />

    <div v-else-if="!work" class="detail-empty">
      <p>作品不存在或已被删除</p>
      <router-link to="/app/works" class="btn btn-primary btn-sm">返回作品列表</router-link>
    </div>

    <div v-else class="detail-content">
      <!-- ===== Main body: Preview + Grouped Info ===== -->
      <div class="detail-body">
        <!-- Left: Preview -->
        <div class="detail-preview">
          <div class="preview-inner">
            <img v-if="work.file_type === 'image' && work.file_url" :src="work.file_url" :alt="work.title" />
            <audio v-else-if="work.file_type === 'audio'" controls :src="work.file_url || undefined" />
            <video v-else-if="work.file_type === 'video'" controls :src="work.file_url || undefined" />
            <div v-else class="preview-fallback">
              <span class="preview-icon">📄</span>
              <p>{{ work.file_name || work.title }}</p>
            </div>
          </div>
        </div>

        <!-- Right: Grouped Info Panel -->
        <div class="detail-info">
          <!-- Group 1: Basic Info -->
          <section class="info-group">
            <h4 class="info-group-title">基本信息</h4>
            <div class="info-row">
              <span class="info-label">类型</span>
              <span class="info-value">{{ work.file_type }} / {{ work.file_extension?.toUpperCase() }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">尺寸</span>
              <span class="info-value">{{ work.width || '—' }} × {{ work.height || '—' }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">大小</span>
              <span class="info-value">{{ formatFileSize(work.file_size) }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">导入</span>
              <span class="info-value">{{ work.imported_at?.slice(0, 16) || '—' }}</span>
            </div>
          </section>

          <!-- Group 2: Stage Management -->
          <section class="info-group">
            <h4 class="info-group-title">阶段管理</h4>
            <div class="stage-status">
              <span class="stage-current-label">当前:</span>
              <span class="stage-current-badge" :style="{ borderColor: stageColor }">{{ stageLabel }}</span>
            </div>
          </section>

          <!-- Group 3: Rights Info -->
          <section class="info-group" v-if="authorName || work.copyright_year || work.license_type">
            <h4 class="info-group-title">权利信息</h4>
            <div class="info-row" v-if="authorName">
              <span class="info-label">作者</span>
              <span class="info-value">{{ authorName }}</span>
            </div>
            <div class="info-row" v-if="work.copyright_year">
              <span class="info-label">版权</span>
              <span class="info-value">© {{ work.copyright_year }}</span>
            </div>
            <div class="info-row" v-if="work.license_type">
              <span class="info-label">许可</span>
              <span class="info-value">{{ work.license_type }}</span>
            </div>
          </section>

          <!-- Group 4: Creation Info -->
          <section class="info-group" v-if="work.custom_metadata?.creation_tool || work.custom_metadata?.creation_location">
            <h4 class="info-group-title">创作信息</h4>
            <div class="info-row" v-if="work.custom_metadata?.creation_tool">
              <span class="info-label">工具</span>
              <span class="info-value">{{ work.custom_metadata.creation_tool }}</span>
            </div>
            <div class="info-row" v-if="work.custom_metadata?.creation_location">
              <span class="info-label">地点</span>
              <span class="info-value">{{ work.custom_metadata.creation_location }}</span>
            </div>
          </section>

          <!-- Group 5: Project & Tags -->
          <section class="info-group" v-if="work.project?.name || work.tags?.length">
            <h4 class="info-group-title">项目与标签</h4>
            <div class="info-row" v-if="work.project?.name">
              <span class="info-label">项目</span>
              <span class="info-value project-link" @click="navigateToProject(work.project!.id)">{{ work.project.name }}</span>
            </div>
            <div class="info-row" v-if="work.tags?.length">
              <span class="info-label">标签</span>
              <span class="info-value tags-value">
                <span v-for="t in work.tags" :key="t.id" class="tag-pill">{{ t.tag }}</span>
              </span>
            </div>
          </section>

          <!-- Group 5.6: AI Generation Panel -->
          <section class="info-group">
            <AIGenerationPanel :work-id="work.id" />
          </section>

          <!-- Group 6: Synopsis -->
          <section class="info-group" v-if="work.synopsis || work.description">
            <h4 class="info-group-title">简介</h4>
            <p class="synopsis-text">{{ work.synopsis || work.description }}</p>
          </section>
        </div>
      </div>

      <!-- ===== Bottom: Timeline + Stage Detail ===== -->
      <div class="detail-bottom">
        <StageTimeline
          :work="work"
          @stage-change="handleStageChange"
          @stage-select="onStageSelect"
        />

        <!-- Stage Detail Panel (two-column layout) -->
        <Transition name="expand">
          <div v-if="activeStageKey" class="stage-detail-panel">
            <div class="stage-detail-header">
              <h3>
                <span class="stage-dot" :style="{ background: activeStageColor }"></span>
                {{ activeStageLabel }}
              </h3>
              <span class="stage-index">{{ activeStageIndex + 1 }} / {{ stageCount }}</span>
            </div>

            <div class="stage-detail-body">
              <!-- Left column: Assets + Notes -->
              <div class="stage-detail-left">
                <!-- Section: Stage Assets -->
                <div class="detail-section">
                  <div class="section-header">
                    <span>📎 阶段素材</span>
                    <span v-if="activeStageAssets.length" class="count">{{ activeStageAssets.length }} 个文件</span>
                  </div>
                  <div v-if="!activeStageAssets.length" class="section-empty">
                    此阶段暂无上传的素材文件
                  </div>
                  <div v-else class="assets-grid">
                    <div v-for="(asset, ai) in activeStageAssets" :key="ai" class="asset-card">
                      <img v-if="asset.type?.startsWith('image')" :src="asset.url" class="asset-thumb" :alt="asset.caption" />
                      <video v-else-if="asset.type?.startsWith('video')" :src="asset.url" class="asset-thumb" controls />
                      <div v-else class="asset-file-icon">📄</div>
                      <div class="asset-caption">{{ asset.caption || '未命名' }}</div>
                    </div>
                  </div>
                </div>

                <!-- Section: Stage Notes -->
                <div class="detail-section">
                  <div class="section-header">
                    <span>📝 创作说明</span>
                    <button v-if="!editingNotes" class="btn-edit-note" @click="startEditNotes">✏️ 编辑</button>
                    <template v-else>
                      <button class="btn-save-note" @click="saveNotes">保存</button>
                      <button class="btn-cancel-note" @click="cancelEditNotes">取消</button>
                    </template>
                  </div>
                  <template v-if="editingNotes">
                    <textarea
                      v-model="notesEditValue"
                      class="notes-textarea"
                      placeholder="记录此阶段的创作说明、想法、注意事项…"
                      rows="4"
                    />
                  </template>
                  <template v-else>
                    <div v-if="activeStageNotes" class="notes-display">{{ activeStageNotes }}</div>
                    <div v-else class="section-empty">此阶段暂无说明文字</div>
                  </template>
                </div>
              </div>

              <!-- Right column: Versions + Notarization -->
              <div class="stage-detail-right">
                <!-- Section: Version History -->
                <div class="detail-section">
                  <div class="section-header">
                    <span>📸 版本历史</span>
                    <button class="btn-snapshot" @click="snapshotVersion">+ 快照</button>
                  </div>
                  <div v-if="!versions.length" class="section-empty">
                    编辑作品后创建版本快照，可随时回滚到历史版本
                  </div>
                  <div v-else class="version-list">
                    <div v-for="v in versions" :key="v.id" class="version-item">
                      <span class="v-num">v{{ v.version_num }}</span>
                      <span class="v-date">{{ v.created_at?.slice(0, 16) }}</span>
                      <code class="v-hash mono" :title="v.file_hash">{{ v.file_hash?.slice(0, 8) }}…</code>
                      <button
                        v-if="v.version_num !== latestVersionNum"
                        class="btn-ghost btn-sm"
                        @click="rollbackTo(v.id)"
                        title="回滚到此版本"
                      >↩</button>
                      <span v-else class="v-current">当前</span>
                    </div>
                  </div>
                </div>

                <!-- Section: Notarization -->
                <div class="detail-section">
                  <div class="section-header">
                    <span>🔒 存证记录</span>
                    <span v-if="notaryCount" class="count">{{ notaryCount }} 条</span>
                  </div>
                  <div v-if="!notaryCount" class="section-empty">
                    此作品暂无存证记录，点击上方"存证"按钮创建
                  </div>
                  <div v-else class="notary-summary">
                    已存证 ✅ 最近存证: {{ work.verified_date || '—' }}
                    <router-link :to="`/app/notary?work_id=${work.id}`" class="view-link">查看完整记录 →</router-link>
                  </div>
                  <div class="c2pa-actions" v-if="work.id">
                    <button class="btn btn-sm btn-secondary" @click="generateC2PA" :disabled="c2paGenerating">
                      {{ c2paGenerating ? '生成中...' : '📝 生成 C2PA 凭证' }}
                    </button>
                    <button class="btn btn-sm btn-secondary" @click="verifyC2PA" :disabled="c2paVerifying">
                      {{ c2paVerifying ? '验证中...' : '✅ 验证 C2PA 凭证' }}
                    </button>
                  </div>
                  <div v-if="c2paResult" class="c2pa-result">
                    <div v-if="c2paResult.success" class="c2pa-success">
                      <div>Manifest Hash: <code>{{ c2paResult.hash }}</code></div>
                      <div>签名时间: {{ c2paResult.timestamp }}</div>
                      <div v-if="c2paResult.public_key_fingerprint">公钥指纹: {{ c2paResult.public_key_fingerprint }}</div>
                    </div>
                    <div v-else class="c2pa-error">
                      {{ c2paResult.error }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Edit Panel -->
    <WorkEditPanel
      :visible="showEditPanel"
      :work="work"
      @close="showEditPanel = false"
      @save="handleSave"
      @delete="handleDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWorkStore } from '@/stores/useWorkStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import WorkEditPanel from '@/components/work/WorkEditPanel.vue'
import StageTimeline from '@/components/work/StageTimeline.vue'
import { worksApi } from '@/api/works'
import { notaryApi } from '@/api/notary'
import { systemApi } from '@/api/system'
import { monitorApi } from '@/api/monitor'
import type { Work } from '@/types/work'
import { getAllStages, getStagesForFileType, getStageColor as getStageColorUtil } from '@/composables/useWorkStages'
import AIGenerationPanel from '@/components/ai/AIGenerationPanel.vue'

const route = useRoute()
const router = useRouter()
const workStore = useWorkStore()
const work = ref<Work | null>(null)
const versions = ref<any[]>([])
const loading = ref(true)
const showEditPanel = ref(false)
const showMoreMenu = ref(false)
const notaryCount = ref(0)

// C2PA
const c2paGenerating = ref(false)
const c2paVerifying = ref(false)
const c2paResult = ref<any>(null)

async function generateC2PA() {
  if (!work.value?.id) return
  c2paGenerating.value = true
  c2paResult.value = null
  try {
    const res = await systemApi.generateC2PA(work.value.id)
    const d = res.data.data || {}
    c2paResult.value = {
      success: true,
      hash: d.manifest_hash || d.hash || '—',
      timestamp: d.timestamp || new Date().toISOString(),
      public_key_fingerprint: d.public_key_fingerprint || d.key_fp || '',
    }
    ;(window as any).$toast?.show('C2PA 凭证已生成', 'success')
  } catch {
    c2paResult.value = { success: false, error: '生成失败' }
    ;(window as any).$toast?.show('C2PA 生成失败', 'error')
  } finally {
    c2paGenerating.value = false
  }
}

async function verifyC2PA() {
  if (!work.value?.id) return
  c2paVerifying.value = true
  c2paResult.value = null
  try {
    const res = await systemApi.verifyC2PA(work.value.id)
    const d = res.data.data || {}
    c2paResult.value = {
      success: d.valid !== false,
      hash: d.manifest_hash || d.hash || '—',
      timestamp: d.timestamp || d.verified_at || '—',
      public_key_fingerprint: d.public_key_fingerprint || d.key_fp || '',
      details: d.details || '验证通过',
    }
    ;(window as any).$toast?.show('C2PA 验证完成', 'success')
  } catch {
    c2paResult.value = { success: false, error: '验证失败' }
    ;(window as any).$toast?.show('C2PA 验证失败', 'error')
  } finally {
    c2paVerifying.value = false
  }
}

// Active stage content (synced with StageTimeline)
const activeStageKey = ref<string | null>(null)
const activeStageAssets = ref<any[]>([])
const activeStageNotes = ref('')

// Stage notes editing
const editingNotes = ref(false)
const notesEditValue = ref('')

const previewUrl = computed(() => work.value?.file_url || '')

const latestVersionNum = computed(() => {
  if (!versions.value.length) return 0
  return Math.max(...versions.value.map((v: any) => v.version_num))
})

const stageLabel = computed(() => {
  if (!work.value?.current_stage) return '未设置'
  const stage = work.value.current_stage
  const all = getAllStages()
  const found = all.find((s: any) => s.value === stage)
  return found?.label || stage
})

const stageColor = computed(() => {
  return work.value?.current_stage ? getStageColorUtil(work.value.current_stage) : '#6B7280'
})

const authorName = computed(() => {
  if (!work.value) return '未设置'
  return work.value.rights?.author_name
    || work.value.custom_metadata?.author_name
    || work.value.custom_metadata?.author
    || '未设置'
})

const activeStageLabel = computed(() => {
  if (!activeStageKey.value) return ''
  const all = getAllStages()
  const found = all.find((s: any) => s.value === activeStageKey.value)
  return found?.label || activeStageKey.value
})

const activeStageColor = computed(() => {
  return activeStageKey.value ? getStageColorUtil(activeStageKey.value) : '#6B7280'
})

const activeStageIndex = computed(() => {
  if (!work.value || !activeStageKey.value) return -1
  const stages = getStagesForFileType(work.value.file_type)
  return stages.findIndex(s => s.value === activeStageKey.value)
})

const stageCount = computed(() => {
  return work.value ? getStagesForFileType(work.value.file_type).length : 0
})

async function loadWork() {
  const id = route.params.id as string
  try {
    work.value = await workStore.fetchWork(id)
    try {
      const res = await worksApi.listVersions(id)
      versions.value = res.data.data || []
    } catch { versions.value = [] }
    try {
      const nr = await notaryApi.list({ work_id: id })
      notaryCount.value = nr.data.data?.total || 0
    } catch { notaryCount.value = 0 }
    autoExpandLastStage()
  } catch (e) {
    console.error('Failed to load work:', e)
    ;(window as any).$toast?.show('加载作品失败', 'error')
    work.value = null
  } finally {
    loading.value = false
  }
}

/** Select a stage and load its content */
function onStageSelect(stageKey: string, assets: any[], notes: string) {
  activeStageKey.value = stageKey
  activeStageAssets.value = assets
  activeStageNotes.value = notes
  // Reset notes editing state
  editingNotes.value = false
  notesEditValue.value = notes
}

/** Find the last stage that has assets or notes */
function autoExpandLastStage() {
  if (!work.value) return
  const fileStages = getStagesForFileType(work.value.file_type)
  const stageMeta = work.value.custom_metadata?.stages as Record<string, any> | undefined
  for (let i = fileStages.length - 1; i >= 0; i--) {
    const key = fileStages[i].value
    const data = stageMeta?.[key]
    if (data?.assets?.length || data?.notes) {
      onStageSelect(key, data.assets, data.notes)
      ;(window as any).__expandStage?.(key)
      return
    }
  }
  // If no stage has content, select the current stage
  if (work.value.current_stage) {
    const data = stageMeta?.[work.value.current_stage]
    onStageSelect(work.value.current_stage, data?.assets || [], data?.notes || '')
    ;(window as any).__expandStage?.(work.value.current_stage)
  }
}

async function handleStageChange(stage: string) {
  if (!work.value) return
  await workStore.updateWork(work.value.id, { current_stage: stage })
  const label = getStageLabel(stage)
  ;(window as any).$toast?.show(`阶段已更新为「${label}」`, 'success')
  await loadWork()
}

function getStageLabel(stage: string): string {
  const all = getAllStages()
  const found = all.find((s: any) => s.value === stage)
  return found?.label || stage
}

// Notes editing
function startEditNotes() {
  editingNotes.value = true
  notesEditValue.value = activeStageNotes.value
}

async function saveNotes() {
  if (!work.value || !activeStageKey.value) return
  try {
    const stageMeta = work.value.custom_metadata?.stages || {}
    const stageData = stageMeta[activeStageKey.value] || { assets: [], notes: '' }
    stageData.notes = notesEditValue.value
    stageMeta[activeStageKey.value] = stageData

    await workStore.updateWork(work.value.id, {
      custom_metadata: { ...(work.value.custom_metadata || {}), stages: stageMeta },
    } as any)

    activeStageNotes.value = notesEditValue.value
    editingNotes.value = false
    ;(window as any).$toast?.show('创作说明已保存', 'success')
  } catch {
    ;(window as any).$toast?.show('保存失败', 'error')
  }
}

function cancelEditNotes() {
  editingNotes.value = false
  notesEditValue.value = activeStageNotes.value
}

async function snapshotVersion() {
  if (!work.value) return
  try {
    await worksApi.createVersion(work.value.id, '手动创建快照，哈希: ' + (work.value.sha256?.slice(0, 8) || ''))
    ;(window as any).$toast?.show('版本快照已创建', 'success')
    await loadWork()
  } catch { ;(window as any).$toast?.show('创建快照失败', 'error') }
}

async function rollbackTo(versionId: string) {
  if (!work.value) return
  if (!confirm('回滚到该版本将更新作品的 SHA-256 哈希为对应版本的哈希，确定回滚吗？')) return
  try {
    await worksApi.rollback(work.value.id, versionId)
    ;(window as any).$toast?.show('已回滚到历史版本', 'success')
    await loadWork()
  } catch { ;(window as any).$toast?.show('回滚失败', 'error') }
}

async function doNotarize() {
  if (!work.value) return
  try {
    await notaryApi.create({ work_id: work.value.id, platform: 'banquanjia' })
    await notaryApi.confirm(work.value.id)
    ;(window as any).$toast?.show('快速存证已完成', 'success')
    await loadWork()
  } catch { ;(window as any).$toast?.show('存证失败', 'error') }
}

async function doMonitorScan() {
  if (!work.value) return
  showMoreMenu.value = false
  try {
    await monitorApi.createTask({ work_id: work.value.id, platform: 'baidu', search_type: 'image' })
    const tasksRes = await monitorApi.tasks({ work_id: work.value.id })
    if (tasksRes.data.data.length) {
      await monitorApi.scan(tasksRes.data.data[0].id)
    }
    ;(window as any).$toast?.show('扫描完成，请前往侵权监测页面查看结果', 'success')
  } catch { ;(window as any).$toast?.show('扫描失败', 'error') }
}

async function handleSave(data: any) {
  if (!work.value) return
  const tags = data.tagsStr.split(',').map((t: string) => t.trim()).filter(Boolean)
  const metadata: Record<string, any> = {}
  for (const [k, v] of Object.entries(data.metadata || {})) {
    if (v) metadata[k] = v
  }

  // Persist stage_notes into custom_metadata.stages[current_stage].notes
  const newStage = data.currentStage || data.current_stage || work.value.current_stage
  if (data.stage_notes && newStage) {
    const stageMeta = metadata.stages || {}
    stageMeta[newStage] = {
      ...stageMeta[newStage],
      notes: data.stage_notes,
    }
    metadata.stages = stageMeta
  }

  await workStore.updateWork(work.value.id, {
    title: data.title,
    description: data.description,
    synopsis: data.synopsis,
    tags,
    project_id: data.projectId || null,
    custom_metadata: metadata,
    current_stage: newStage,
  } as any)
  showEditPanel.value = false
  ;(window as any).$toast?.show('已保存', 'success')
  await loadWork()
}

async function handleDelete() {
  showMoreMenu.value = false
  showEditPanel.value = false
  if (!work.value) return
  if (!confirm(`确定删除"${work.value.title}"？作品将被移入回收站，30天内可恢复。`)) return
  await workStore.deleteWork(work.value.id)
  ;(window as any).$toast?.show('已移入回收站', 'info')
  router.push('/app/works')
}

function navigateToProject(projectId: string) {
  router.push(`/app/projects/${projectId}`)
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Close dropdown on outside click
function handleClickOutside(e: MouseEvent) {
  const el = (e.target as HTMLElement).closest('.dropdown-wrapper')
  if (!el) showMoreMenu.value = false
}
onMounted(() => {
  loadWork().catch((e) => console.error('WorkDetailView mount error:', e))
  document.addEventListener('click', handleClickOutside)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* ===== Outer Container ===== */
.detail-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* ===== Toolbar ===== */
.detail-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.toolbar-title {
  flex: 1;
  text-align: center;
  font-size: 1rem;
  font-weight: 700;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

/* Dropdown */
.dropdown-wrapper {
  position: relative;
  display: inline-block;
}
.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 8px 32px oklch(0 0 0 / 0.1);
  z-index: 100;
  min-width: 180px;
  padding: 4px 0;
}
.dropdown-item {
  display: block;
  width: 100%;
  padding: 8px 14px;
  font-size: 0.82rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  color: var(--fg);
  font-family: var(--font-body);
  white-space: nowrap;
}
.dropdown-item:hover {
  background: oklch(96% 0.003 240);
}

/* ===== Main Body: Preview + Info ===== */
.detail-body {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 24px;
}
@media (max-width: 1024px) {
  .detail-body { grid-template-columns: 1fr; }
}

/* Preview */
.detail-preview {
  background: oklch(15% 0.005 240);
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  overflow: hidden;
}
.preview-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 200px;
}
.preview-inner img {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
}
.preview-inner audio,
.preview-inner video {
  max-width: 100%;
}
.preview-fallback {
  text-align: center;
  color: #fff;
  padding: 60px;
}
.preview-icon {
  font-size: 4rem;
  display: block;
  margin-bottom: 12px;
}

/* ===== Info Panel ===== */
.detail-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 4px;
}
.detail-info::-webkit-scrollbar { width: 4px; }
.detail-info::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

/* Info Groups */
.info-group {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.info-group:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.info-group-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent);
  margin: 0 0 10px 0;
}

/* Info Rows */
.info-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 0.85rem;
  margin-bottom: 6px;
}
.info-row:last-child { margin-bottom: 0; }
.info-label {
  color: var(--muted);
  font-weight: 600;
  font-size: 0.8rem;
  min-width: 60px;
  flex-shrink: 0;
}
.info-value {
  color: var(--fg);
  font-size: 0.85rem;
  word-break: break-word;
}
.project-link {
  color: var(--accent);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.project-link:hover { opacity: 0.8; }

/* Tags */
.tags-value {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.tag-pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 100px;
  font-size: 0.75rem;
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--accent);
  font-weight: 600;
}

/* Stage Status */
.stage-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}
.stage-current-label {
  color: var(--muted);
  font-weight: 600;
  font-size: 0.8rem;
}
.stage-current-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 12px;
  border-radius: 100px;
  border: 2px solid;
  font-weight: 600;
  font-size: 0.82rem;
}

/* Synopsis */
.synopsis-text {
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--fg);
  white-space: pre-wrap;
  margin: 0;
}

/* ===== Bottom: Timeline + Stage Detail ===== */
.detail-bottom {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Stage Detail Panel */
.stage-detail-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.stage-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}
.stage-detail-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.stage-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.stage-index {
  font-size: 0.75rem;
  color: var(--muted);
  font-weight: 600;
}

/* Two-column layout for stage detail */
.stage-detail-body {
  display: flex;
  gap: 24px;
}
.stage-detail-left {
  flex: 2;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.stage-detail-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
@media (max-width: 768px) {
  .stage-detail-body { flex-direction: column; }
}

/* Detail Sections */
.detail-section {
  padding: 0;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--fg);
}
.count {
  font-size: 0.72rem;
  color: var(--muted);
  font-weight: 400;
}
.section-empty {
  font-size: 0.78rem;
  color: var(--muted);
  text-align: center;
  padding: 16px 8px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
}

/* Assets Grid */
.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 8px;
}
.asset-thumb {
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

/* Notes */
.notes-display {
  font-size: 0.82rem;
  line-height: 1.6;
  color: var(--fg);
  padding: 10px 12px;
  background: oklch(96% 0.003 240);
  border-radius: var(--radius-sm);
}
.notes-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-family: var(--font-body);
  color: var(--fg);
  background: var(--surface);
  outline: none;
  resize: vertical;
  line-height: 1.6;
}
.notes-textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}
.btn-edit-note, .btn-save-note, .btn-cancel-note {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 2px 10px;
  font-size: 0.72rem;
  cursor: pointer;
  font-weight: 600;
}
.btn-edit-note { color: var(--accent); }
.btn-save-note { color: #2ECC71; border-color: #2ECC71; }
.btn-cancel-note { color: var(--muted); }

/* Version List */
.version-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
}
.version-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.74rem;
}
.version-item:hover { background: oklch(96% 0.003 240); }
.v-num { font-weight: 700; color: var(--accent); min-width: 28px; }
.v-date { color: var(--muted); flex: 1; }
.v-hash { font-size: 0.65rem; color: var(--muted); }
.v-current {
  font-size: 0.65rem;
  background: oklch(56% 0.12 170 / .1);
  color: var(--accent);
  padding: 2px 6px;
  border-radius: 100px;
  font-weight: 600;
}
.mono { font-family: monospace; }

/* Notary Summary */
.notary-summary {
  font-size: 0.82rem;
  color: var(--fg);
  padding: 8px 10px;
  background: oklch(96% 0.003 240);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 8px;
}
.view-link {
  font-size: 0.78rem;
  color: var(--accent);
  margin-left: auto;
}

/* C2PA Actions */
.c2pa-actions {
  display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap;
}
.c2pa-actions .btn { font-size: 0.78rem; padding: 4px 12px; }
.c2pa-result { margin-top: 10px; padding: 10px 14px; border-radius: var(--radius-sm); font-size: 0.8rem; background: var(--surface); border: 1px solid var(--border); }
.c2pa-success { color: var(--fg); line-height: 1.6; }
.c2pa-success code { background: oklch(0 0 0 / 0.04); padding: 1px 6px; border-radius: 3px; font-size: 0.75rem; font-family: monospace; }
.c2pa-error { color: oklch(56% 0.18 20); }

/* ===== Buttons ===== */
.btn {
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-family: var(--font-body);
}
.btn-sm { padding: 5px 10px; font-size: 0.78rem; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-secondary { background: var(--surface); color: var(--fg); border: 1px solid var(--border); }
.btn-ghost { background: none; border: none; cursor: pointer; font-size: 0.85rem; padding: 2px 6px; color: var(--muted); }
.btn-ghost:hover { background: oklch(0 0 0 / 0.04); }
.text-danger { color: #e53e3e; }

/* Transitions */
.expand-enter-active, .expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.expand-enter-from, .expand-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Empty state */
.detail-empty {
  text-align: center;
  padding: 80px 20px;
  color: var(--muted);
}
.detail-empty p {
  margin: 0 0 16px;
  font-size: 0.95rem;
}
</style>

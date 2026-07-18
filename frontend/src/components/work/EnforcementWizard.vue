<template>
  <div class="enforcement-wizard-overlay" v-if="visible">
    <div class="wizard-backdrop" @click="close"></div>

    <div class="wizard-panel">
      <!-- Header -->
      <div class="wizard-header">
        <h3>
          <span class="step-icon">{{ stepIcons[stepIndex] }}</span>
          {{ stepTitles[stepIndex] }}
        </h3>
        <button class="btn-close" @click="close">&times;</button>
      </div>

      <!-- Progress bar -->
      <div class="progress-bar">
        <div
          v-for="(label, i) in stepTitles"
          :key="i"
          :class="['progress-step', { active: i <= stepIndex, done: i < stepIndex }]"
        >
          <span class="step-num">{{ i + 1 }}</span>
          <span class="step-label">{{ label }}</span>
        </div>
      </div>

      <!-- Step 1: Check matches -->
      <Transition name="fade" mode="out-in">
        <div v-if="stepIndex === 0" key="check" class="wizard-body">
          <p class="hint">扫描该作品是否有侵权监测结果，并自动生成维权行动。</p>

          <LoadingSpinner v-if="scanning" text="扫描中..." />

          <div v-else-if="scanResult" class="scan-result">
            <div v-if="scanResult.status === 'matches_found'" class="result-positive">
              <span class="icon">&#x2705;</span>
              <p>发现 <strong>{{ scanResult.action_ids?.length || 0 }}</strong> 个待处理侵权行为</p>
              <ul v-if="scanResult.action_ids" class="action-list">
                <li v-for="(id, i) in scanResult.action_ids" :key="i">
                  维权行动 #{{ i + 1 }} — ID: {{ id.slice(0, 8) }}...
                </li>
              </ul>
            </div>

            <div v-else-if="scanResult.status === 'no_matches'" class="result-neutral">
              <span class="icon">&#x26A0;</span>
              <p>{{ scanResult.message || '未检测到侵权行为，建议继续监测' }}</p>
            </div>

            <div v-else class="result-warning">
              <span class="icon">&#x2757;</span>
              <p>该作品已有维权记录，无需重复创建。</p>
            </div>
          </div>
        </div>

        <!-- Step 2: Evidence preview -->
        <div v-else-if="stepIndex === 1" key="evidence" class="wizard-body">
          <p class="hint">系统已聚合以下证据材料，可用于投诉提交。</p>

          <LoadingSpinner v-if="loadingEvidence" text="加载中..." />

          <div v-else-if="evidenceData" class="evidence-preview">
            <div class="evidence-grid">
              <div class="evidence-card" v-if="evidenceData.notary_records?.length">
                <div class="card-icon">&#x1F512;</div>
                <div class="card-info">
                  <strong>区块链存证</strong>
                  <span>{{ evidenceData.notary_records.length }} 条</span>
                </div>
              </div>
              <div class="evidence-card" v-if="evidenceData.c2pa_manifests?.length">
                <div class="card-icon">&#x1F4DD;</div>
                <div class="card-info">
                  <strong>C2PA 凭证</strong>
                  <span>{{ evidenceData.c2pa_manifests.length }} 个</span>
                </div>
              </div>
              <div class="evidence-card" v-if="evidenceData.ai_sessions?.length">
                <div class="card-icon">&#x1F916;</div>
                <div class="card-info">
                  <strong>AI 创作记录</strong>
                  <span>{{ evidenceData.ai_sessions.length }} 条</span>
                </div>
              </div>
              <div class="evidence-card" v-if="evidenceData.infringement_evidence?.length">
                <div class="card-icon">&#x1F50D;</div>
                <div class="card-info">
                  <strong>侵权证据</strong>
                  <span>{{ evidenceData.infringement_evidence.length }} 条</span>
                </div>
              </div>
              <div class="evidence-card" v-if="evidenceData.work_versions?.length">
                <div class="card-icon">&#x1F4BE;</div>
                <div class="card-info">
                  <strong>版本历史</strong>
                  <span>{{ evidenceData.work_versions.length }} 个</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Step 3: Templates -->
        <div v-else-if="stepIndex === 2" key="templates" class="wizard-body">
          <p class="hint">选择投诉模板，系统将自动预填作品信息。</p>

          <LoadingSpinner v-if="loadingTemplates" text="加载中..." />

          <div v-else class="template-list">
            <div
              v-for="tpl in templates"
              :key="tpl.id"
              :class="['template-card', { selected: selectedTemplateId === tpl.id }]"
              @click="selectedTemplateId = tpl.id"
            >
              <div class="template-header">
                <strong>{{ tpl.title }}</strong>
                <span class="template-badge">{{ tpl.platform }}</span>
              </div>
              <p class="template-desc">{{ tpl.body_template.slice(0, 100) }}...</p>
              <div class="template-meta">
                <span>管辖: {{ tpl.jurisdiction }}</span>
                <span v-if="tpl.filing_url">
                  <a :href="tpl.filing_url" target="_blank" rel="noopener">提交链接 &rarr;</a>
                </span>
              </div>
            </div>
          </div>

          <div v-if="!templates.length" class="empty-hint">
            <p>暂无可用模板</p>
            <button class="btn-secondary" @click="handleSeed">初始化默认模板</button>
          </div>
        </div>

        <!-- Step 4: Submit -->
        <div v-else-if="stepIndex === 3" key="submit" class="wizard-body">
          <p class="hint">确认提交后，系统将生成投诉信并更新维权状态。</p>

          <LoadingSpinner v-if="submitting" text="提交中..." />

          <div v-else-if="submitResult" class="submit-result">
            <div class="result-success">
              <span class="icon">&#x2705;</span>
              <p>投诉已提交</p>
              <pre class="complaint-text">{{ submitResult.complaint_text }}</pre>
              <div v-if="submitResult.prefilled_url" class="prefill-link">
                <a :href="submitResult.prefilled_url" target="_blank" rel="noopener">打开预填表单 &rarr;</a>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Footer -->
      <div class="wizard-footer">
        <button
          v-if="stepIndex > 0 && !submitting"
          class="btn-secondary"
          @click="stepIndex--"
          :disabled="loadingEvidence || loadingTemplates"
        >
          &larr; 上一步
        </button>
        <div></div>
        <button
          v-if="stepIndex < stepTitles.length - 1"
          class="btn-primary"
          @click="nextStep"
          :disabled="stepIndex === 0 ? scanning : false"
        >
          下一步 &rarr;
        </button>
        <button
          v-else-if="stepIndex === 3 && !submitResult && !submitting"
          class="btn-primary"
          @click="handleSubmit"
          :disabled="loadingTemplates"
        >
          提交投诉
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { enforcementApi } from '@/api/enforcement'
import type { EnforcementTemplate, EvidencePackage } from '@/types/enforcement'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

// ------------------------------------------------------------------
// Props / Emits
// ------------------------------------------------------------------

interface Props {
  visible: boolean
  workId: string
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  workId: '',
})

const emit = defineEmits<{
  close: []
  success: [actionIds: string[]]
}>()

// ------------------------------------------------------------------
// State
// ------------------------------------------------------------------

const stepIndex = ref(0)
const scanning = ref(false)
const scanResult = ref<any>(null)
const actionIds = ref<string[]>([])
const loadingEvidence = ref(false)
const evidenceData = ref<EvidencePackage | null>(null)
const loadingTemplates = ref(false)
const templates = ref<EnforcementTemplate[]>([])
const selectedTemplateId = ref('')
const submitting = ref(false)
const submitResult = ref<any>(null)

const stepTitles = ['扫描', '证据', '模板', '提交']
const stepIcons = ['🔍', '📍', '📝', '📤']

// ------------------------------------------------------------------
// Computed
// ------------------------------------------------------------------

const hasScanResult = computed(() => !!scanResult.value)
const canProceed = computed(() => {
  if (stepIndex.value === 0) return hasScanResult.value && scanResult.value?.status === 'matches_found'
  return true
})

// ------------------------------------------------------------------
// Step handlers
// ------------------------------------------------------------------

async function nextStep() {
  if (!canProceed.value) return

  if (stepIndex.value === 0) {
    // Move to evidence step — no additional API call needed (data is already loaded)
    stepIndex.value++
  } else if (stepIndex.value === 1) {
    // Load templates for this step
    await loadTemplates()
    stepIndex.value++
  } else if (stepIndex.value === 2) {
    stepIndex.value++
  }
}

async function handleScan() {
  scanning.value = true
  scanResult.value = null
  try {
    const res = await enforcementApi.createFromWork(props.workId)
    scanResult.value = res.data
    actionIds.value = res.data.action_ids || []
    // Auto-proceed if there are matches
    if (res.data.status === 'matches_found') {
      setTimeout(() => { stepIndex.value = 1 }, 800)
    }
  } catch {
    ;(window as any).$toast?.show('扫描失败', 'error')
  } finally {
    scanning.value = false
  }
}

async function loadTemplates() {
  loadingTemplates.value = true
  try {
    const res = await enforcementApi.listTemplates()
    templates.value = res.data || []
  } catch {
    templates.value = []
  } finally {
    loadingTemplates.value = false
  }
}

async function handleSubmit() {
  submitting.value = true
  submitResult.value = null
  try {
    if (actionIds.value.length === 0) {
      // Re-scan to get fresh action IDs
      const scanRes = await enforcementApi.createFromWork(props.workId)
      if (scanRes.data.status !== 'matches_found' || !scanRes.data.action_ids?.length) {
        ;(window as any).$toast?.show('无可用维权行动', 'warning')
        return
      }
      actionIds.value = scanRes.data.action_ids
    }
    // Submit complaint for first action
    const res = await enforcementApi.submitComplaint(actionIds.value[0])
    submitResult.value = res.data
    ;(window as any).$toast?.show('投诉已提交', 'success')
    emit('success', actionIds.value)
  } catch {
    ;(window as any).$toast?.show('提交失败', 'error')
  } finally {
    submitting.value = false
  }
}

async function handleSeed() {
  try {
    await enforcementApi.seedTemplates()
    await loadTemplates()
    ;(window as any).$toast?.show('模板已初始化', 'success')
  } catch {
    ;(window as any).$toast?.show('模板初始化失败', 'error')
  }
}

function close() {
  reset()
  emit('close')
}

function reset() {
  stepIndex.value = 0
  scanResult.value = null
  evidenceData.value = null
  templates.value = []
  selectedTemplateId.value = ''
  submitting.value = false
  submitResult.value = null
}

// ------------------------------------------------------------------
// Lifecycle
// ------------------------------------------------------------------

let stopWatch: ReturnType<typeof setInterval> | null = null

function startWatching() {
  if (stopWatch) clearInterval(stopWatch)
  stopWatch = setInterval(() => {
    if (props.visible) handleScan()
  }, 2000)
}

// Watch visibility prop changes
watch(() => props.visible, (val) => {
  if (val) {
    reset()
    startWatching()
  } else {
    if (stopWatch) clearInterval(stopWatch)
    stopWatch = null
  }
}, { immediate: true })
</script>

<style scoped>
/* Overlay */
.enforcement-wizard-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.wizard-backdrop {
  position: absolute;
  inset: 0;
  background: oklch(15% 0.005 240 / 0.6);
  backdrop-filter: blur(4px);
}

/* Panel */
.wizard-panel {
  position: relative;
  width: 90%;
  max-width: 640px;
  max-height: 85vh;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.wizard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.wizard-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}
.step-icon {
  font-size: 1.1rem;
}
.btn-close {
  background: none;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  color: var(--muted);
  line-height: 1;
  padding: 4px;
}
.btn-close:hover { color: var(--fg); }

/* Progress bar */
.progress-bar {
  display: flex;
  padding: 0 20px;
  border-bottom: 1px solid var(--border);
}
.progress-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 4px 8px;
  font-size: 0.7rem;
  color: var(--muted);
  position: relative;
}
.progress-step::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 10%;
  right: 10%;
  height: 3px;
  background: var(--border);
  border-radius: 2px;
}
.progress-step.active::after { background: var(--accent); }
.progress-step.done::after { background: #22c55e; }
.step-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  background: var(--border);
  color: var(--muted);
}
.progress-step.active .step-num {
  background: var(--accent);
  color: #fff;
}
.progress-step.done .step-num {
  background: #22c55e;
  color: #fff;
}
.step-label {
  font-weight: 600;
}

/* Body */
.wizard-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.hint {
  font-size: 0.82rem;
  color: var(--muted);
  margin: 0 0 16px;
}

/* Scan results */
.scan-result { margin-top: 12px; }
.result-positive, .result-neutral, .result-warning {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px;
  border-radius: var(--radius);
  gap: 8px;
}
.result-positive { background: #dcfce7; }
.result-neutral { background: #fef3c7; }
.result-warning { background: #fee2e2; }
.result-positive p, .result-neutral p, .result-warning p {
  margin: 0;
  font-size: 0.9rem;
}
.icon { font-size: 2rem; }
.action-list {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  text-align: left;
  font-size: 0.8rem;
  width: 100%;
}
.action-list li {
  padding: 6px 10px;
  background: #fff;
  border-radius: 4px;
  margin-bottom: 4px;
}

/* Evidence grid */
.evidence-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}
.evidence-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg);
}
.card-icon { font-size: 1.4rem; }
.card-info {
  display: flex;
  flex-direction: column;
  font-size: 0.8rem;
}
.card-info strong { font-weight: 700; color: var(--fg); }
.card-info span { color: var(--muted); font-size: 0.75rem; }

/* Template list */
.template-list { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
.template-card {
  padding: 14px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: border-color 0.15s;
}
.template-card:hover { border-color: var(--accent); }
.template-card.selected { border-color: var(--accent); background: oklch(56% 0.12 170 / 0.05); }
.template-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.template-header strong { font-size: 0.9rem; }
.template-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  background: var(--border);
  border-radius: 100px;
  color: var(--muted);
  text-transform: uppercase;
}
.template-desc {
  font-size: 0.78rem;
  color: var(--muted);
  margin: 0 0 8px;
  line-height: 1.4;
}
.template-meta {
  display: flex;
  gap: 12px;
  font-size: 0.72rem;
  color: var(--muted);
}
.template-meta a { color: var(--accent); }

.empty-hint {
  text-align: center;
  padding: 24px;
  color: var(--muted);
}

/* Submit result */
.submit-result { margin-top: 12px; }
.result-success {
  background: #dcfce7;
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
}
.complaint-text {
  font-size: 0.78rem;
  white-space: pre-wrap;
  max-height: 160px;
  overflow-y: auto;
  background: #fff;
  padding: 10px;
  border-radius: 4px;
  width: 100%;
  text-align: left;
  margin: 0;
  font-family: var(--font-body);
}
.prefill-link { font-size: 0.82rem; }
.prefill-link a { color: var(--accent); font-weight: 600; }

/* Footer */
.wizard-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-top: 1px solid var(--border);
}
.wizard-footer button {
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-family: var(--font-body);
}
.wizard-footer button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-primary { background: var(--accent); color: #fff; }
.btn-secondary {
  background: var(--surface);
  color: var(--fg);
  border: 1px solid var(--border) !important;
}

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: all 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateX(12px); }
</style>

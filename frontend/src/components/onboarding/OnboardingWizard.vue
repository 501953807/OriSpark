<template>
  <div class="onboarding-card animate-fade-in">
    <!-- ===== Step 0: 选择创作者类型 ===== -->
    <div v-if="currentStep === 0">
      <div class="ob-header">
        <span class="ob-badge">Step 1/3</span>
        <h2 class="ob-title">👋 欢迎来到 OriStudio</h2>
        <p class="ob-desc">选择你的创作者类型，系统会自动调整最合适的功能</p>
      </div>

      <div class="creator-grid">
        <div v-for="ct in creatorTypes" :key="ct.key"
          :class="['creator-card', { selected: selectedCreator === ct.key, highlighted: ct.key === 'illustrator', disabled: ct.status !== 'full' }]"
          @click="selectCreator(ct.key)"
        >
          <span v-if="ct.key === 'illustrator'" class="creator-recommend">✨ 推荐</span>
          <span v-else-if="ct.status === 'basic'" class="creator-badge">🚧 规划中</span>
          <span class="creator-icon">{{ ct.icon }}</span>
          <strong>{{ ct.label }}</strong>
          <p>{{ ct.shortDesc }}</p>
          <small>{{ ct.statusText }}</small>
        </div>
      </div>

      <div class="ob-actions">
        <button class="btn btn-primary btn-lg" :disabled="!selectedCreator" @click="nextStep">
          {{ selectedCreator ? '下一步 →' : '请先选择创作者类型' }}
        </button>
      </div>
    </div>

    <!-- ===== Step 1: 导入第一批作品 ===== -->
    <div v-else-if="currentStep === 1">
      <div class="ob-header">
        <span class="ob-badge">Step 2/3</span>
        <h2 class="ob-title">📂 导入你的第一批作品</h2>
        <p class="ob-desc">拖拽文件或文件夹到下方区域，支持批量导入</p>
      </div>

      <FileDropZone
        :multiple="true"
        @uploaded="onFilesImported"
      />

      <div class="ob-actions">
        <button class="btn btn-secondary" @click="prevStep">← 上一步</button>
        <button class="btn btn-link" @click="skipImport">跳过，稍后导入 →</button>
      </div>
    </div>

    <!-- ===== Step 2: 快速上手 ===== -->
    <div v-else-if="currentStep === 2">
      <div class="ob-header">
        <div class="ob-success-icon">✨</div>
        <h2 class="ob-title">你已经准备好了！</h2>
        <p class="ob-desc">系统已根据你选择的创作者类型自动配置</p>
      </div>

      <div class="workflow-cards">
        <div class="wf-card">
          <span class="wf-icon">🎨</span>
          <strong>管理作品</strong>
          <p>{{ importCount > 0 ? `查看刚导入的 ${importCount} 个作品` : '拖拽导入作品' }}</p>
        </div>
        <div class="wf-arrow">→</div>
        <div class="wf-card">
          <span class="wf-icon">🛡️</span>
          <strong>保护版权</strong>
          <p>选中作品一键存证</p>
        </div>
        <div class="wf-arrow">→</div>
        <div class="wf-card">
          <span class="wf-icon">💰</span>
          <strong>开始变现</strong>
          <p>将作品变成产品销售</p>
        </div>
      </div>

      <div class="ob-actions">
        <button class="btn btn-secondary" @click="prevStep">← 上一步</button>
        <button class="btn btn-primary btn-lg" @click="handleFinish">🎉 开始使用，进入工作台</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import FileDropZone from '@/components/common/FileDropZone.vue'

const props = withDefaults(defineProps<{
  initialCreatorType?: string
  autoStart?: boolean
}>(), {
  autoStart: true,
})

const emit = defineEmits<{
  finish: [payload: { creatorType: string; importCount: number }]
  skip: []
}>()

const currentStep = ref(0)
const selectedCreator = ref(props.initialCreatorType || '')
const importCount = ref(0)

const creatorTypes = [
  {
    key: 'illustrator', icon: '🎨', label: '插画师 / AIGC艺术家',
    shortDesc: '插画、角色设计、AI生成图像', status: 'full',
    statusText: '✅ v1 完整支持 — 全链路功能可用',
  },
  {
    key: 'photographer', icon: '📷', label: '摄影师',
    shortDesc: '摄影后期、图库销售、预设包', status: 'basic',
    statusText: '🚧 规划中 — v2 将提供完整支持（RAW/选片/水印/图库API）',
  },
  {
    key: 'video_creator', icon: '🎬', label: '视频作者',
    shortDesc: '短视频、动画、品牌商单', status: 'basic',
    statusText: '🚧 规划中 — v3 将提供完整支持（工程文件/视频指纹/商单流程）',
  },
  {
    key: 'crafter', icon: '🖐', label: '手工艺人',
    shortDesc: '陶瓷、木器、布艺、首饰', status: 'basic',
    statusText: '🚧 规划中 — v3 将提供完整支持（原件/库存/批次/Etsy API）',
  },
  {
    key: 'musician', icon: '🎵', label: '音乐人',
    shortDesc: '原创音乐、配乐、采样包', status: 'basic',
    statusText: '🚧 规划中 — v4 将提供完整支持（ISRC/发行/Split Sheets）',
  },
  {
    key: 'writer', icon: '✍️', label: '文字作者',
    shortDesc: '小说、剧本、商业撰稿', status: 'basic',
    statusText: '🚧 规划中 — v4 将提供完整支持（章节/EPUB/抄袭检测）',
  },
]

function selectCreator(key: string) {
  selectedCreator.value = key
}

function nextStep() {
  if (selectedCreator.value) {
    localStorage.setItem('oristudio-creator-type', selectedCreator.value)
    currentStep.value++
  }
}

function prevStep() {
  currentStep.value--
}

function onFilesImported(_count?: number) {
  importCount.value = _count || 0
  currentStep.value++
}

function skipImport() {
  currentStep.value++
}

function handleFinish() {
  emit('finish', {
    creatorType: selectedCreator.value,
    importCount: importCount.value,
  })
}

onMounted(() => {
  // Restore from localStorage if no initial prop
  if (props.autoStart && !selectedCreator.value) {
    const saved = localStorage.getItem('oristudio-creator-type')
    if (saved) {
      selectedCreator.value = saved
    }
  }
})
</script>

<style scoped>
.onboarding-card {
  max-width: 700px; width: 100%; padding: 40px;
  background: var(--bg-card, #fff); border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}
.animate-fade-in {
  animation: fade-in 0.3s ease;
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.ob-header { text-align: center; margin-bottom: 32px; }
.ob-badge { font-size: 0.78rem; color: var(--muted); }
.ob-title { font-size: 1.5rem; font-weight: 700; margin: 8px 0 4px; color: var(--text-primary); }
.ob-desc { font-size: 0.92rem; color: var(--text-secondary); margin: 0; }

.creator-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 24px; }
.creator-card {
  position: relative; padding: 16px; border: 2px solid var(--border); border-radius: 12px;
  cursor: pointer; transition: all 0.2s; text-align: center; background: var(--surface);
}
.creator-card:hover { border-color: var(--accent); }
.creator-card.selected { border-color: var(--accent); background: oklch(56% 0.12 170 / 0.04); }
.creator-card.disabled { opacity: 0.65; }
.creator-card.highlighted { border-color: var(--accent); border-width: 3px; box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.12); }
.creator-icon { font-size: 2rem; display: block; margin-bottom: 8px; }
.creator-card strong { font-size: 0.9rem; display: block; color: var(--text-primary); }
.creator-card p { font-size: 0.76rem; color: var(--text-secondary); margin: 4px 0; }
.creator-card small { font-size: 0.7rem; color: var(--muted); display: block; margin-top: 4px; }
.creator-recommend { position: absolute; top: -8px; right: -8px; padding: 2px 10px; border-radius: 100px; font-size: 0.72rem; font-weight: 700; background: var(--accent); color: #fff; }
.creator-badge { position: absolute; top: 8px; right: 8px; padding: 1px 6px; border-radius: 4px; font-size: 0.65rem; background: oklch(62% 0.18 55 / 0.1); color: var(--orange); }

.workflow-cards { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.wf-card { padding: 16px; border: 1px solid var(--border); border-radius: 12px; text-align: center; min-width: 120px; background: var(--surface); }
.wf-icon { font-size: 1.6rem; display: block; margin-bottom: 6px; }
.wf-card strong { font-size: 0.85rem; display: block; color: var(--text-primary); }
.wf-card p { font-size: 0.74rem; color: var(--text-secondary); margin: 2px 0 0; }
.wf-arrow { font-size: 1.2rem; color: var(--accent); font-weight: 700; }

.ob-actions { text-align: center; margin-top: 24px; display: flex; gap: 12px; justify-content: center; align-items: center; }
.ob-success-icon { font-size: 3rem; animation: pop-in 0.5s ease; margin-bottom: 8px; }
@keyframes pop-in { 0% { transform: scale(0); } 70% { transform: scale(1.2); } 100% { transform: scale(1); } }

.btn { padding: 10px 20px; border-radius: 8px; font-size: 0.88rem; cursor: pointer; border: none; font-family: inherit; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: var(--surface); color: var(--text-primary); border: 1px solid var(--border); }
.btn-lg { padding: 14px 36px; font-size: 1rem; font-weight: 600; }
.btn-link { background: none; border: none; color: var(--muted); font-size: 0.84rem; cursor: pointer; text-decoration: underline; }

@media (max-width: 768px) {
  .creator-grid { grid-template-columns: 1fr 1fr; }
  .onboarding-card { padding: 24px; }
}
@media (max-width: 480px) {
  .creator-grid { grid-template-columns: 1fr; }
}
</style>

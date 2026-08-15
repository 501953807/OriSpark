<template>
  <div class="onboarding-card animate-fade-in">
    <!-- ===== Step 0: 选择创作者类型 ===== -->
    <div v-if="currentStep === 0">
      <div class="ob-header">
        <span class="ob-badge">Step 1/3</span>
        <h2 class="ob-title">🎨 欢迎来到 OriStudio</h2>
        <p class="ob-desc">选择你的创作者类型，系统会自动调整最合适的功能</p>
      </div>

      <div class="creator-grid">
        <div v-for="ct in creatorTypes" :key="ct.key"
          :class="['creator-card', { selected: selectedCreator === ct.key, highlighted: ct.key === 'illustrator' }]"
          @click="selectCreator(ct.key)"
        >
          <span v-if="ct.key === 'illustrator'" class="creator-recommend">✨ 推荐</span>
          <span class="creator-icon">{{ ct.icon }}</span>
          <strong>{{ ct.label }}</strong>
          <p>{{ ct.shortDesc }}</p>
          <small>{{ ct.statusText }}</small>
        </div>
      </div>

      <div class="ob-actions">
        <button class="btn btn-primary btn-lg" :disabled="!selectedCreator" @click="nextStep">
          {{ selectedCreator ? '下一步 →' : '请选择创作者类型' }}
        </button>
      </div>
    </div>

    <!-- ===== Step 1: 导入作品（可选）===== -->
    <div v-else-if="currentStep === 1">
      <div class="ob-header">
        <span class="ob-badge">Step 2/3</span>
        <h2 class="ob-title">📂 导入你的作品（可选）</h2>
        <p class="ob-desc">你可以上传作品素材到工作室，也可以稍后导入</p>
      </div>

      <FileDropZone
        v-if="selectedCreator"
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
        <p class="ob-desc">系统已为你配置好 {{ creatorLabel }} 功能</p>
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
          <span class="wf-icon">📋</span>
          <strong>IP登记</strong>
          <p>版权/商标/专利申请</p>
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
import { ref, computed } from 'vue'
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

const creatorLabel = computed(() => {
  const types: Record<string, string> = {
    illustrator: '插画师',
    photographer: '摄影师',
    video: '视频创作者',
    craftsman: '手工艺人',
    musician: '音乐人',
    writer: '文字作者',
  }
  return types[selectedCreator.value] || '创作者'
})

const creatorTypes = [
  {
    key: 'illustrator', icon: '🎨', label: '插画师 / AIGC艺术家',
    shortDesc: '插画、角色设计、AI生成图像', status: 'full',
    statusText: '✅ v1 完整支持',
  },
  {
    key: 'photographer', icon: '📷', label: '摄影师',
    shortDesc: '摄影后期、图库销售、预设包', status: 'full',
    statusText: '✅ v2 完整支持',
  },
  {
    key: 'video', icon: '🎬', label: '视频创作者',
    shortDesc: '短视频、动画、品牌商单', status: 'full',
    statusText: '✅ v3 完整支持',
  },
  {
    key: 'craftsman', icon: '🖐', label: '手工艺人',
    shortDesc: '陶瓷、木器、布艺、首饰', status: 'full',
    statusText: '✅ v3b 完整支持',
  },
  {
    key: 'musician', icon: '🎵', label: '音乐人',
    shortDesc: '原创音乐、配乐、采样包', status: 'full',
    statusText: '✅ v4 完整支持',
  },
  {
    key: 'writer', icon: '✍️', label: '文字作者',
    shortDesc: '小说、剧本、商业撰稿', status: 'full',
    statusText: '✅ v4 完整支持',
  },
]

function selectCreator(key: string) {
  selectedCreator.value = key
  localStorage.setItem('oristudio-creator-type', key)
}

function nextStep() {
  if (currentStep.value === 0) {
    currentStep.value = 1
  } else if (currentStep.value === 1) {
    currentStep.value = 2
  }
}

function prevStep() {
  currentStep.value--
}

function onFilesImported(count?: number) {
  importCount.value = count || 0
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
.ob-title { font-size: 1.5rem; font-weight: 700; margin: 8px 0 4px; color: var(--fg); }
.ob-desc { font-size: 0.92rem; color: var(--muted); margin: 0; }

.creator-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.creator-card {
  position: relative; padding: 16px; border: 2px solid var(--border); border-radius: 12px;
  cursor: pointer; transition: all 0.2s; text-align: center; background: var(--surface);
}
.creator-card:hover { border-color: var(--accent); }
.creator-card.selected { border-color: var(--accent); background: rgba(85, 133, 255, 0.04); }
.creator-card.highlighted { border-color: var(--accent); border-width: 3px; box-shadow: 0 0 0 3px rgba(85, 133, 255, 0.1); }
.creator-icon { font-size: 2rem; display: block; margin-bottom: 8px; }
.creator-card strong { font-size: 0.9rem; display: block; color: var(--fg); }
.creator-card p { font-size: 0.76rem; color: var(--muted); margin: 4px 0; }
.creator-card small { font-size: 0.7rem; color: var(--muted); display: block; margin-top: 4px; }
.creator-recommend { position: absolute; top: -8px; right: -8px; padding: 2px 10px; border-radius: 100px; font-size: 0.72rem; font-weight: 700; background: var(--accent); color: #fff; }

.workflow-cards { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.wf-card { padding: 16px; border: 1px solid var(--border); border-radius: 12px; text-align: center; min-width: 120px; background: var(--surface); }
.wf-icon { font-size: 1.6rem; display: block; margin-bottom: 6px; }
.wf-card strong { font-size: 0.85rem; display: block; color: var(--fg); }
.wf-card p { font-size: 0.74rem; color: var(--muted); margin: 2px 0 0; }
.wf-arrow { font-size: 1.2rem; color: var(--accent); font-weight: 700; }

.ob-actions { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.btn { padding: 10px 20px; border-radius: var(--m-radius-sm); font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.2s; border: none; font-family: Inter; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: var(--surface); color: var(--fg); border: 1px solid var(--border); }
.btn-secondary:hover { background: var(--surface-hover); }
.btn-link { background: none; color: var(--accent); padding: 10px 0; }
.btn-link:hover { text-decoration: underline; }
.btn-lg { padding: 14px 28px; font-size: 1rem; }

.ob-success-icon { font-size: 3rem; margin-bottom: 12px; }
</style>

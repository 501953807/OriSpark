<template>
  <div class="stage-timeline">
    <div class="timeline-header">
      <span class="timeline-title">创作阶段</span>
      <span v-if="currentLabel" class="current-badge">当前: {{ currentLabel }}</span>
    </div>

    <div class="timeline-track">
      <div
        v-for="(stage, i) in stages"
        :key="stage.value"
        class="timeline-step"
        :class="{ 'active': expandedStage === stage.value }"
        @click="toggleStage(stage)"
      >
        <!-- Left: vertical node line -->
        <div class="step-line-wrap">
          <div class="step-node" :class="stepNodeClass(i)">
            <img
              v-if="i < currentIndex && getStageThumbnail(stage.value)"
              :src="getStageThumbnail(stage.value)!"
              class="node-thumb"
              alt=""
            />
            <span v-else-if="i < currentIndex" class="node-check">✓</span>
            <span v-else-if="i === currentIndex" class="node-active" :style="{ background: stage.color }"></span>
            <span v-else class="node-future"></span>
          </div>
          <div v-if="i < stages.length - 1" class="step-connector" :class="{ 'completed': i < currentIndex }" />
        </div>

        <!-- Right: step card -->
        <div class="step-card">
          <div class="step-header">
            <span class="step-label" :class="stepLabelClass(i)">{{ stage.label }}</span>
            <span v-if="getStageAssetCount(stage.value)" class="step-count">{{ getStageAssetCount(stage.value) }} 个文件</span>
          </div>
          <div class="step-desc" :class="stepDescClass(i)">
            {{ stepDescription(stage.value) }}
          </div>

          <!-- Expanded content: assets + notes + upload -->
          <Transition name="expand">
            <div v-if="expandedStage === stage.value" class="step-expanded">
              <!-- Assets grid -->
              <div v-if="getStageAssets(stage.value)?.length" class="expanded-assets">
                <div
                  v-for="(asset, ai) in getStageAssets(stage.value)"
                  :key="ai"
                  class="expanded-asset"
                >
                  <img v-if="asset.type?.startsWith('image')" :src="asset.url" class="expanded-thumb" :alt="asset.caption" />
                  <video v-else-if="asset.type?.startsWith('video')" :src="asset.url" class="expanded-thumb" controls />
                  <div v-else class="expanded-file-icon">📄</div>
                  <div class="expanded-asset-caption">{{ asset.caption || '未命名' }}</div>
                  <button class="asset-remove-btn" @click.stop="removeAsset(stage.value, ai)" title="删除">×</button>
                </div>
              </div>
              <div v-else class="expanded-empty">
                暂无素材，点击下方按钮上传
              </div>

              <!-- Notes -->
              <div v-if="getStageNotes(stage.value)" class="expanded-notes">
                <strong>说明：</strong>{{ getStageNotes(stage.value) }}
              </div>
              <div v-else class="expanded-notes-empty">
                此阶段暂无说明文字
              </div>

              <!-- Actions -->
              <div class="expanded-actions">
                <button class="btn-upload" @click.stop="triggerUpload(stage)">+ 上传素材</button>
                <button v-if="i > currentIndex" class="btn-set-current" @click.stop="advanceTo(i)">设为当前阶段</button>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      multiple
      accept="image/*,video/*,audio/*,.pdf,.txt,.doc,.docx"
      class="hidden-input"
      @change="handleFileUpload"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { getStagesForFileType, getStageColor } from '@/composables/useWorkStages'
import type { StageOption } from '@/composables/useWorkStages'

interface StageAsset {
  url: string
  caption?: string
  type?: string
  size?: number
}

interface StageData {
  assets: StageAsset[]
  notes: string
}

const props = defineProps<{
  work: {
    id: string
    file_type: string
    current_stage?: string | null
    custom_metadata?: Record<string, any> | null
  } | null
}>()

const emit = defineEmits<{
  stageChange: [stage: string]
  stageSelect: [stageKey: string, assets: StageAsset[], notes: string]
}>()

// --- Stage content data ---
const stageData = ref<Record<string, StageData>>({})
if (props.work?.custom_metadata?.stages) {
  const meta = props.work.custom_metadata.stages as Record<string, StageData>
  Object.entries(meta).forEach(([key, val]) => {
    stageData.value[key] = val
  })
}

const stages = computed(() => props.work ? getStagesForFileType(props.work.file_type) : [])
const currentIndex = computed(() => {
  if (!props.work?.current_stage) return -1
  return stages.value.findIndex(s => s.value === props.work!.current_stage)
})
const currentLabel = computed(() => {
  if (currentIndex.value < 0) return ''
  return stages.value[currentIndex.value]?.label
})

const expandedStage = ref<string | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// Expose for parent to trigger auto-expand
function setExpandedStage(key: string) {
  expandedStage.value = key
}

// Make available for parent via window/global
;(window as any).__expandStage = setExpandedStage

function toggleStage(stage: StageOption) {
  const wasExpanded = expandedStage.value === stage.value
  expandedStage.value = wasExpanded ? null : stage.value

  // Notify parent of selected stage content
  if (!wasExpanded) {
    emit('stageSelect', stage.value, getStageAssets(stage.value), getStageNotes(stage.value))
  }
}

function stepNodeClass(i: number): string {
  const idx = currentIndex.value
  if (i < idx) return 'completed'
  if (i === idx) return 'current'
  return 'future'
}

function stepLabelClass(i: number): string {
  const idx = currentIndex.value
  if (i < idx) return 'completed'
  if (i === idx) return 'current'
  return 'future'
}

function stepDescClass(i: number): string {
  const idx = currentIndex.value
  if (i < idx) return 'completed'
  if (i === idx) return 'current'
  return 'future'
}

function stepDescription(stageValue: string): string {
  const descs: Record<string, string> = {
    inspiration: '收集灵感素材，参考图片与文字描述',
    sketch: '绘制初步构思，草图与大致布局',
    lineart: '完成线稿，勾勒清晰轮廓',
    coloring: '进行上色，确定色彩方案',
    detail: '细化局部，完善画面细节',
    final: '最终定稿，完成全部创作内容',
    script: '编写剧本脚本，确定故事框架',
    storyboard: '制作分镜草图，规划镜头语言',
    roughcut: '粗剪拼接，搭建影片骨架',
    finecut: '精剪优化，调整节奏与过渡',
    colorgrade: '调色处理，统一视觉风格',
    idea: '音乐构思，确定风格与情绪走向',
    arrangement: '编曲配器，搭建音乐结构',
    recording: '录音录制，采集原始音轨',
    mixing: '混音处理，平衡各轨道音量',
    mastering: '母带处理，优化最终音质',
    release: '发行发布，准备分发渠道',
    outline: '制定大纲，梳理内容框架',
    draft: '撰写初稿，完成主要内容',
    revision: '修订完善，调整结构与措辞',
    formatting: '排版设计，统一文档格式',
    publish: '发布定稿，准备分发渠道',
    concept: '概念设计，确定整体风格方向',
    modeling: '三维建模，构建模型结构',
    texturing: '贴图绘制，添加材质与纹理',
    rigging: '骨骼绑定，设置动画控制器',
    animation: '动画制作，赋予模型动态表现',
    render: '渲染输出，生成最终画面',
    design: '架构设计，确定技术方案',
    prototype: '原型开发，实现核心功能',
    develop: '编码开发，完成全部功能模块',
    test: '测试调试，修复发现的问题',
    deploy: '部署上线，发布到生产环境',
    maintain: '维护迭代，持续优化性能',
  }
  return descs[stageValue] || ''
}

function getStageAssets(stageValue: string): StageAsset[] {
  return stageData.value[stageValue]?.assets || []
}

function getStageThumbnail(stageValue: string): string | null {
  const assets = getStageAssets(stageValue)
  return assets.length > 0 ? assets[0].url : null
}

function getStageAssetCount(stageValue: string): number {
  return getStageAssets(stageValue).length
}

function getStageNotes(stageValue: string): string {
  return stageData.value[stageValue]?.notes || ''
}

function advanceTo(index: number) {
  if (!props.work || index < 0 || index >= stages.value.length) return
  const stage = stages.value[index]
  emit('stageChange', stage.value)
}

function triggerUpload(stage: StageOption) {
  expandedStage.value = stage.value
  nextTick(() => {
    fileInputRef.value?.click()
  })
}

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const files = target.files
  if (!files || !expandedStage.value) return

  const stageValue = expandedStage.value
  if (!stageData.value[stageValue]) {
    stageData.value[stageValue] = { assets: [], notes: '' }
  }

  Array.from(files).forEach(file => {
    const url = URL.createObjectURL(file)
    stageData.value[stageValue].assets.push({
      url,
      caption: file.name,
      type: file.type,
      size: file.size,
    })
  })

  target.value = ''
}

function removeAsset(stageValue: string, index: number) {
  if (stageData.value[stageValue]?.assets[index]) {
    URL.revokeObjectURL(stageData.value[stageValue].assets[index].url)
    stageData.value[stageValue].assets.splice(index, 1)
  }
}
</script>

<style scoped>
/* ===== Container ===== */
.stage-timeline {
  padding: 0;
}
.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 0;
}
.timeline-title {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--fg);
}
.current-badge {
  font-size: 0.72rem;
  color: var(--accent);
  font-weight: 600;
  background: oklch(56% 0.12 170 / 0.1);
  padding: 2px 8px;
  border-radius: 100px;
}

/* ===== Vertical track ===== */
.timeline-track {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 16px 24px 24px;
  gap: 0;
}

.timeline-track::before {
  content: '';
  position: absolute;
  left: 15px;
  top: 16px;
  bottom: 24px;
  width: 2px;
  background: oklch(88% 0.008 240);
  z-index: 0;
}

/* ===== Each step ===== */
.timeline-step {
  display: flex;
  gap: 16px;
  position: relative;
  z-index: 1;
  min-height: 72px;
}

.step-line-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  padding-top: 8px;
}

/* Node circle */
.step-node {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
  transition: all 0.2s;
}

.step-node.completed {
  background: var(--accent);
  border: 3px solid var(--accent);
}
.node-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}
.node-check {
  color: #fff;
  font-size: 0.95rem;
  font-weight: 700;
}

.step-node.current {
  border: 3px solid var(--accent);
  background: #fff;
}
.node-active {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.step-node.future {
  border: 2px solid oklch(78% 0.01 240);
  background: oklch(95% 0.003 240);
}
.node-future {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: oklch(82% 0.008 240);
}

/* Connector line */
.step-connector {
  width: 2px;
  flex-grow: 1;
  min-height: 24px;
  background: oklch(88% 0.008 240);
  transition: background 0.3s;
}
.step-connector.completed {
  background: var(--accent);
}

/* ===== Step card ===== */
.step-card {
  flex: 1;
  padding: 8px 12px 8px 0;
  cursor: pointer;
  border-radius: var(--radius);
  transition: background 0.15s;
}
.step-card:hover {
  background: oklch(97% 0.003 240);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-label {
  font-size: 0.88rem;
  font-weight: 600;
  transition: color 0.2s;
}
.step-label.completed { color: var(--accent); }
.step-label.current { color: var(--accent); font-weight: 700; }
.step-label.future { color: oklch(55% 0.01 240); }

.step-count {
  font-size: 0.7rem;
  color: var(--muted);
  background: oklch(93% 0.005 240);
  padding: 1px 8px;
  border-radius: 100px;
}

.step-desc {
  font-size: 0.78rem;
  margin-top: 2px;
  transition: color 0.2s;
  line-height: 1.4;
}
.step-desc.completed { color: oklch(50% 0.01 240); }
.step-desc.current { color: var(--fg); }
.step-desc.future { color: oklch(70% 0.008 240); }

/* ===== Expanded content ===== */
.expanded-assets {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 10px;
  margin-top: 12px;
}
.expanded-asset {
  position: relative;
}
.expanded-thumb {
  width: 100%;
  height: 90px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  transition: border-color 0.15s;
}
.expanded-asset:hover .expanded-thumb {
  border-color: var(--accent);
}
.expanded-file-icon {
  width: 100%;
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  background: oklch(96% 0.003 240);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}
.expanded-asset-caption {
  font-size: 0.68rem;
  color: var(--muted);
  margin-top: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.asset-remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: oklch(0 0 0 / 0.5);
  color: #fff;
  border: none;
  font-size: 0.75rem;
  cursor: pointer;
  display: none;
  align-items: center;
  justify-content: center;
  line-height: 1;
}
.expanded-asset:hover .asset-remove-btn {
  display: flex;
}

.expanded-empty {
  font-size: 0.78rem;
  color: var(--muted);
  margin-top: 10px;
  text-align: center;
  padding: 14px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
}

.expanded-notes {
  font-size: 0.78rem;
  color: var(--fg);
  margin-top: 12px;
  padding: 8px 10px;
  background: oklch(96% 0.003 240);
  border-radius: var(--radius-sm);
  line-height: 1.5;
}
.expanded-notes strong { color: var(--accent); }
.expanded-notes-empty {
  font-size: 0.75rem;
  color: oklch(65% 0.008 240);
  margin-top: 10px;
  font-style: italic;
}

.expanded-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}
.btn-upload {
  padding: 6px 14px;
  font-size: 0.78rem;
  border: 1px dashed var(--accent);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  transition: background 0.15s;
}
.btn-upload:hover { background: oklch(56% 0.12 170 / 0.08); }
.btn-set-current {
  padding: 6px 14px;
  font-size: 0.78rem;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  font-weight: 600;
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.expand-enter-from, .expand-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.hidden-input { display: none; }
</style>

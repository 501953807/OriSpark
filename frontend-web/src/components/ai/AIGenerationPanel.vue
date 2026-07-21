<template>
  <div class="ai-generation-panel">
    <!-- Config status banner -->
    <div v-if="!configured" class="ai-unconfigured">
      <span class="ai-icon">🤖</span>
      <span>AI 功能未启用。请在后端配置 AI_API_KEY 后启用。</span>
    </div>

    <template v-else>
      <!-- Tabs -->
      <div class="ai-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['ai-tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- Tab: Smart Tags -->
      <div v-show="activeTab === 'tags'" class="ai-tab-content">
        <h3 class="ai-section-title">智能标签</h3>
        <p class="ai-section-desc">输入作品 ID，AI 自动分析并生成相关标签。</p>
        <div class="ai-input-group">
          <input
            v-model="tagWorkId"
            class="ai-input"
            placeholder="请输入作品 ID"
          />
          <button
            class="ai-btn ai-btn-primary"
            :disabled="!tagWorkId || tagsLoading"
            @click="doAutoTag"
          >
            {{ tagsLoading ? '生成中...' : '✨ AI 生成标签' }}
          </button>
        </div>
        <div v-if="tagResult" class="ai-tags-output">
          <div class="ai-tags-list">
            <span
              v-for="tag in tagResult.tags"
              :key="tag"
              class="ai-tag-pill"
              @click="onTagClick(tag)"
            >
              {{ tag }}
              <span v-if="tagResult.confidence" class="ai-tag-conf">
                {{ Math.round(tagResult.confidence * 100) }}%
              </span>
            </span>
          </div>
        </div>
        <AiErrorDisplay :error="error" />
      </div>

      <!-- Tab: Smart Description -->
      <div v-show="activeTab === 'desc'" class="ai-tab-content">
        <h3 class="ai-section-title">智能描述</h3>
        <p class="ai-section-desc">输入作品 ID，AI 自动生成作品描述文案。</p>
        <div class="ai-input-group">
          <input
            v-model="descWorkId"
            class="ai-input"
            placeholder="请输入作品 ID"
          />
          <button
            class="ai-btn ai-btn-primary"
            :disabled="!descWorkId || descLoading"
            @click="doAutoDescription"
          >
            {{ descLoading ? '生成中...' : '✨ AI 生成描述' }}
          </button>
        </div>
        <div v-if="descResult" class="ai-desc-output">
          <textarea class="ai-textarea" readonly rows="6" :value="descResult.description" />
          <button class="ai-btn ai-btn-secondary" @click="copyText(descResult.description)">
            📋 复制
          </button>
        </div>
        <AiErrorDisplay :error="error" />
      </div>

      <!-- Tab: Article Draft -->
      <div v-show="activeTab === 'article'" class="ai-tab-content">
        <h3 class="ai-section-title">文章草稿</h3>
        <p class="ai-section-desc">提供提示词，AI 辅助起草文章或书籍段落。</p>
        <div class="ai-input-group ai-input-group--stacked">
          <textarea
            v-model="articlePrompt"
            class="ai-textarea"
            rows="3"
            placeholder="请输入写作提示，例如：写一篇关于传统手工艺与现代设计融合的文章"
          />
          <div class="ai-row">
            <select v-model="articleTone" class="ai-select">
              <option value="professional">专业严谨</option>
              <option value="casual">轻松随意</option>
              <option value="academic">学术风格</option>
              <option value="poetic">诗意抒情</option>
            </select>
            <input
              v-model.number="articleMaxWords"
              type="number"
              class="ai-input ai-input--short"
              placeholder="最大字数"
              min="100"
              max="10000"
            />
          </div>
          <button
            class="ai-btn ai-btn-primary"
            :disabled="!articlePrompt.trim() || articleLoading"
            @click="doDraftArticle"
          >
            {{ articleLoading ? '生成中...' : '📝 生成草稿' }}
          </button>
        </div>
        <div v-if="articleResult" class="ai-article-output">
          <textarea class="ai-textarea" readonly rows="8" :value="articleResult" />
          <button class="ai-btn ai-btn-secondary" @click="copyText(articleResult)">
            📋 复制
          </button>
        </div>
        <AiErrorDisplay :error="error" />
      </div>

      <!-- Tab: Content Moderation -->
      <div v-show="activeTab === 'moderate'" class="ai-tab-content">
        <h3 class="ai-section-title">内容审核</h3>
        <p class="ai-section-desc">检测文本是否存在违规内容。</p>
        <div class="ai-input-group ai-input-group--stacked">
          <textarea
            v-model="moderationText"
            class="ai-textarea"
            rows="5"
            placeholder="请输入需要审核的文本内容"
          />
          <button
            class="ai-btn ai-btn-primary"
            :disabled="!moderationText.trim() || moderateLoading"
            @click="doModerate"
          >
            {{ moderateLoading ? '审核中...' : '🔍 审核' }}
          </button>
        </div>
        <div v-if="modResult" class="ai-moderate-output">
          <div
            :class="['ai-status-badge', modResult.safe ? 'safe' : 'unsafe']"
          >
            {{ modResult.safe ? '✅ 内容安全' : '❌ 内容违规' }}
          </div>
          <p v-if="modResult.reason" class="ai-moderate-reason">{{ modResult.reason }}</p>
          <div v-if="Object.keys(modResult.categories).length" class="ai-categories">
            <span
              v-for="(v, k) in modResult.categories"
              :key="k"
              :class="['ai-cat-pill', v ? 'flagged' : 'ok']"
            >
              {{ k }}: {{ v ? '违规' : '正常' }}
            </span>
          </div>
        </div>
        <AiErrorDisplay :error="error" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAiGenerateStore, type TagResult, type DescriptionResult, type ModerationResult } from '@/stores/useAiGenerateStore'

const store = useAiGenerateStore()

const activeTab = ref('tags')

const configured = computed(() => store.config?.configured ?? false)

// Props — auto-populate workId from parent
interface Props {
  workId?: string
}
const props = withDefaults(defineProps<Props>(), {
  workId: '',
})

const tabs = [
  { key: 'tags', label: '智能标签', icon: '🏷️' },
  { key: 'desc', label: '智能描述', icon: '📝' },
  { key: 'article', label: '文章草稿', icon: '📄' },
  { key: 'moderate', label: '内容审核', icon: '🔍' },
]

// Tags
const tagWorkId = ref(props.workId || '')
const tagsLoading = ref(false)
const tagResult = ref<TagResult | null>(null)

async function doAutoTag() {
  if (!tagWorkId.value) return
  tagsLoading.value = true
  tagResult.value = null
  try {
    const r = await store.autoTag(tagWorkId.value)
    tagResult.value = r
    if (r) {
      ;(window as any).$toast?.show('标签生成完成', 'success')
    }
  } finally {
    tagsLoading.value = false
  }
}

function onTagClick(tag: string) {
  ;(window as any).$toast?.show(`已选择标签: ${tag}`, 'info')
}

// Description
const descWorkId = ref(props.workId || '')
const descLoading = ref(false)
const descResult = ref<DescriptionResult | null>(null)

async function doAutoDescription() {
  if (!descWorkId.value) return
  descLoading.value = true
  descResult.value = null
  try {
    const r = await store.autoDescription(descWorkId.value)
    descResult.value = r
    if (r) {
      ;(window as any).$toast?.show('描述生成完成', 'success')
    }
  } finally {
    descLoading.value = false
  }
}

// Article
const articlePrompt = ref('')
const articleTone = ref('professional')
const articleMaxWords = ref(2000)
const articleLoading = ref(false)
const articleResult = ref<string | null>(null)

async function doDraftArticle() {
  if (!articlePrompt.value.trim()) return
  articleLoading.value = true
  articleResult.value = null
  try {
    const r = await store.draftArticle(articlePrompt.value, articleTone.value, articleMaxWords.value)
    articleResult.value = r
    if (r) {
      ;(window as any).$toast?.show('文章草稿生成完成', 'success')
    }
  } finally {
    articleLoading.value = false
  }
}

// Moderation
const moderationText = ref('')
const moderateLoading = ref(false)
const modResult = ref<ModerationResult | null>(null)

async function doModerate() {
  if (!moderationText.value.trim()) return
  moderateLoading.value = true
  modResult.value = null
  try {
    const r = await store.moderateContent(moderationText.value)
    modResult.value = r
    if (r) {
      const msg = r.safe ? '内容审核通过' : '检测到违规内容'
      ;(window as any).$toast?.show(msg, r.safe ? 'success' : 'error')
    }
  } finally {
    moderateLoading.value = false
  }
}

// Copy helper
function copyText(text: string) {
  navigator.clipboard.writeText(text).then(
    () => (window as any).$toast?.show('已复制到剪贴板', 'success'),
    () => (window as any).$toast?.show('复制失败，请手动复制', 'error'),
  )
}

const error = computed(() => store.error)

onMounted(() => {
  store.loadConfig()
})
</script>

<style scoped>
.ai-generation-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Unconfigured banner */
.ai-unconfigured {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: oklch(96% 0.003 240);
  border: 1px dashed var(--border);
  border-radius: var(--radius);
  font-size: 0.85rem;
  color: var(--muted);
}
.ai-icon {
  font-size: 1.3rem;
}

/* Tabs */
.ai-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0;
}
.ai-tab {
  padding: 8px 14px;
  font-size: 0.82rem;
  font-weight: 600;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  color: var(--muted);
  font-family: var(--font-body);
  transition: all 0.15s ease;
  border-radius: 0;
}
.ai-tab:hover {
  color: var(--fg);
  background: oklch(96% 0.003 240);
}
.ai-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

/* Tab content */
.ai-tab-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 12px;
}
.ai-section-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}
.ai-section-desc {
  margin: 0;
  font-size: 0.8rem;
  color: var(--muted);
}

/* Inputs */
.ai-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ai-input-group--stacked {
  gap: 8px;
}
.ai-input {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-family: var(--font-body);
  color: var(--fg);
  background: var(--surface);
  outline: none;
  transition: border-color 0.15s;
}
.ai-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}
.ai-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-family: var(--font-body);
  color: var(--fg);
  background: var(--surface);
  outline: none;
  resize: vertical;
  line-height: 1.5;
  transition: border-color 0.15s;
}
.ai-textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}
.ai-textarea[readonly] {
  background: oklch(96% 0.003 240);
  cursor: default;
}
.ai-row {
  display: flex;
  gap: 8px;
  align-items: center;
}
.ai-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-family: var(--font-body);
  color: var(--fg);
  background: var(--surface);
  outline: none;
  cursor: pointer;
}
.ai-input--short {
  width: 100px;
}

/* Buttons */
.ai-btn {
  padding: 7px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-family: var(--font-body);
  transition: all 0.15s;
  white-space: nowrap;
}
.ai-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.ai-btn-primary {
  background: var(--accent);
  color: #fff;
}
.ai-btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}
.ai-btn-secondary {
  background: var(--surface);
  color: var(--fg);
  border: 1px solid var(--border);
}
.ai-btn-secondary:hover:not(:disabled) {
  background: oklch(96% 0.003 240);
}

/* Tags output */
.ai-tags-output {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ai-tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.ai-tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 100px;
  font-size: 0.78rem;
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--accent);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}
.ai-tag-pill:hover {
  background: oklch(56% 0.12 170 / 0.2);
}
.ai-tag-conf {
  font-size: 0.68rem;
  opacity: 0.7;
}

/* Description output */
.ai-desc-output {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Article output */
.ai-article-output {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Moderation output */
.ai-moderate-output {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ai-status-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 100px;
  font-size: 0.85rem;
  font-weight: 700;
}
.ai-status-badge.safe {
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--green);
}
.ai-status-badge.unsafe {
  background: oklch(56% 0.18 20 / 0.1);
  color: oklch(56% 0.18 20);
}
.ai-moderate-reason {
  margin: 0;
  font-size: 0.82rem;
  color: var(--fg);
  line-height: 1.5;
}
.ai-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.ai-cat-pill {
  padding: 2px 10px;
  border-radius: 100px;
  font-size: 0.72rem;
  font-weight: 600;
}
.ai-cat-pill.flagged {
  background: oklch(56% 0.18 20 / 0.1);
  color: oklch(56% 0.18 20);
}
.ai-cat-pill.ok {
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--green);
}

/* Error display */
.ai-error {
  padding: 8px 12px;
  background: oklch(56% 0.18 20 / 0.06);
  border: 1px solid oklch(56% 0.18 20 / 0.15);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  color: oklch(56% 0.18 20);
}
</style>

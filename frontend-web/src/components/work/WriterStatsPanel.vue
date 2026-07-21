<template>
  <div class="writer-panel">
    <!-- Article Info -->
    <section class="info-group" v-if="articleGroup.length">
      <h4 class="info-group-title">文章信息</h4>
      <div v-for="item in articleGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Content Stats -->
    <section class="info-group" v-if="statsGroup.length">
      <h4 class="info-group-title">内容统计</h4>
      <div v-for="item in statsGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Categories & Tags -->
    <section class="info-group" v-if="tagsGroup.length">
      <h4 class="info-group-title">分类与标签</h4>
      <div v-for="item in tagsGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">
          <template v-if="item.isTagList">
            <span v-for="tag in item.tags" :key="tag" class="tag-chip">{{ tag }}</span>
          </template>
          <template v-else>{{ item.value }}</template>
        </span>
      </div>
    </section>

    <!-- Book Info -->
    <section class="info-group" v-if="bookGroup.length">
      <h4 class="info-group-title">书籍信息</h4>
      <div v-for="item in bookGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Empty state -->
    <div v-if="!hasAnyData" class="empty-hint">
      <span class="hint-icon">✎</span>
      <p>暂无写作数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Work } from '@/types/work'

interface Props {
  work: Work | null
  exifData: Record<string, any> | null
}

const props = withDefaults(defineProps<Props>(), {
  work: null,
  exifData: null,
})

const raw = computed(() => {
  if (props.exifData && typeof props.exifData === 'object') return props.exifData
  if (props.work?.custom_metadata?.writing && typeof props.work.custom_metadata.writing === 'object')
    return props.work.custom_metadata.writing
  return null
})

const articleMeta = computed(() => raw.value?.article ?? {})
const bookMeta = computed(() => raw.value?.book ?? {})

const wordCount = computed(() => raw.value?.word_count ?? null)
const readingTime = computed(() => raw.value?.reading_time_minutes ?? null)
const category = computed(() => articleMeta.value?.category ?? null)
const tags = computed(() => {
  const t = articleMeta.value?.tags ?? props.work?.tags ?? []
  return Array.isArray(t) ? t : []
})
const status = computed(() => articleMeta.value?.status ?? null)
const publishedAt = computed(() => articleMeta.value?.published_at ?? null)

const bookTitle = computed(() => bookMeta.value?.title ?? null)
const bookGenre = computed(() => bookMeta.value?.genre ?? null)
const bookChapters = computed(() => bookMeta.value?.total_chapters ?? null)
const bookPublisher = computed(() => bookMeta.value?.publisher ?? null)
const bookIsbn = computed(() => bookMeta.value?.isbn ?? null)
const bookStatus = computed(() => bookMeta.value?.status ?? null)

function fmt(val: string | number | null | undefined): string {
  if (val == null || val === '') return '—'
  return String(val)
}

const articleGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (props.work?.title) items.push({ label: '标题', value: fmt(props.work.title) })
  if (category.value) items.push({ label: '分类', value: fmt(category.value) })
  if (status.value) items.push({ label: '状态', value: fmt(status.value) })
  if (publishedAt.value) items.push({ label: '发布时间', value: fmt(publishedAt.value) })
  return items
})

const statsGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (wordCount.value != null) items.push({ label: '字数', value: fmt(wordCount.value.toLocaleString()) })
  if (readingTime.value != null) items.push({ label: '阅读时间', value: fmt(`${readingTime.value} 分钟`) })
  return items
})

const tagsGroup = computed(() => {
  const items: Array<{ label: string; value: string; isTagList?: boolean; tags?: string[] }> = []
  if (tags.value.length) items.push({ label: '标签', value: '', isTagList: true, tags: tags.value })
  return items
})

const bookGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (bookTitle.value) items.push({ label: '书名', value: fmt(bookTitle.value) })
  if (bookGenre.value) items.push({ label: '体裁', value: fmt(bookGenre.value) })
  if (bookChapters.value != null) items.push({ label: '章节', value: fmt(String(bookChapters.value)) })
  if (bookPublisher.value) items.push({ label: '出版社', value: fmt(bookPublisher.value) })
  if (bookIsbn.value) items.push({ label: 'ISBN', value: fmt(bookIsbn.value) })
  if (bookStatus.value) items.push({ label: '状态', value: fmt(bookStatus.value) })
  return items
})

const hasAnyData = computed(() => {
  return !!(
    wordCount.value ||
    readingTime.value ||
    category.value ||
    tags.value.length ||
    status.value ||
    bookTitle.value ||
    bookGenre.value ||
    bookChapters.value
  )
})
</script>

<style scoped>
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--muted);
  gap: 8px;
}

.hint-icon { font-size: 2rem; opacity: 0.6; }

.info-group {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.info-group:last-child { border-bottom: none; padding-bottom: 0; }

.info-group-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent);
  margin: 0 0 10px 0;
}

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

.tag-chip {
  display: inline-block;
  padding: 2px 10px;
  margin: 2px 4px 2px 0;
  border-radius: 10px;
  font-size: 0.78rem;
  background: oklch(56% 0.12 170 / 0.1);
  color: #16a34a;
  font-weight: 500;
}
</style>

<!-- ListingCard — 商品卡片

Used in: ListingListView grid/list mode
Shows: thumbnail, title, price, profit, tags, status, quick actions
-->
<template>
  <div class="listing-card" :class="{ 'list-mode': listMode }">
    <!-- Thumbnail -->
    <div class="card-thumb" @click="handleView">
      <img
        v-if="listing.mockup_image_path"
        :src="listing.mockup_image_path"
        :alt="listing.title"
        class="thumb-img"
      />
      <div v-else class="thumb-placeholder">
        <span class="placeholder-icon">📦</span>
      </div>
      <!-- Status badge -->
      <span
        class="status-badge"
        :class="listing.status"
      >
        {{ statusLabel(listing.status) }}
      </span>
    </div>

    <!-- Content -->
    <div class="card-content">
      <div class="card-title" @click="handleView">{{ listing.title }}</div>
      <div class="card-price-row">
        <span class="card-price">¥{{ listing.price }}</span>
        <span class="card-profit">
          利润 ¥{{ calcProfit() }} ({{ calcMargin() }}%)
        </span>
      </div>

      <!-- Tags -->
      <div class="card-tags">
        <span v-if="listing.monetization_path" class="tag tag-path">
          {{ pathLabel(listing.monetization_path) }}
        </span>
        <span class="tag tag-status">{{ listing.status }}</span>
      </div>

      <!-- Quick actions -->
      <div class="card-actions">
        <button class="action-btn" title="查看" @click="handleView">👁</button>
        <button class="action-btn" title="编辑" @click="handleEdit">✏️</button>
        <button class="action-btn" title="复制为新商品" @click="handleDuplicate">📋</button>
        <button class="action-btn" title="发布" @click="handlePublish" :disabled="listing.status === 'draft'">📤</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { DesignListing } from '@/types/supply'

interface Props {
  listing: DesignListing
  listMode?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'view', id: string): void
  (e: 'edit', id: string): void
  (e: 'duplicate', id: string): void
  (e: 'publish', id: string): void
}>()

function calcProfit(): number {
  return Math.max(0, +(props.listing.price - props.listing.cost).toFixed(2))
}

function calcMargin(): number {
  if (!props.listing.price) return 0
  return Math.round((calcProfit() / props.listing.price) * 100)
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: '草稿',
    active: '在售',
    discontinued: '已下架',
  }
  return map[status] || status
}

function pathLabel(path: string): string {
  const map: Record<string, string> = {
    pod: 'POD',
    crowdfunding: '众筹',
    licensing: 'IP授权',
    digital: '数字产品',
    custom_mfg: '定制制造',
  }
  return map[path] || path
}

function handleView() { emit('view', props.listing.id) }
function handleEdit() { emit('edit', props.listing.id) }
function handleDuplicate() { emit('duplicate', props.listing.id) }
function handlePublish() { emit('publish', props.listing.id) }
</script>

<style scoped>
.listing-card {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: all 0.2s;
  background: var(--surface);
}

.listing-card:hover {
  border-color: var(--accent);
  box-shadow: 0 4px 12px oklch(56% 0.12 170 / .1);
}

.listing-card.list-mode {
  display: grid;
  grid-template-columns: 120px 1fr auto;
  align-items: center;
  gap: 16px;
}

/* Thumbnail */
.card-thumb {
  position: relative;
  aspect-ratio: 1;
  background: var(--muted-bg);
  cursor: pointer;
  overflow: hidden;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 2rem;
}

.status-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  padding: 2px 8px;
  border-radius: 100px;
  font-size: .65rem;
  font-weight: 600;
}

.status-badge.active {
  background: oklch(56% 0.12 140 / .2);
  color: oklch(56% 0.12 140);
}

.status-badge.draft {
  background: oklch(75% 0.08 80 / .2);
  color: oklch(65% 0.1 80);
}

.status-badge.discontinued {
  background: oklch(56% 0.12 20 / .15);
  color: oklch(56% 0.12 20);
}

/* Content */
.card-content {
  padding: 12px 16px 16px;
}

.list-mode .card-content {
  padding: 0 16px;
}

.card-title {
  font-size: .92rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-mode .card-title {
  font-size: 1rem;
}

.card-title:hover {
  color: var(--accent);
}

.card-price-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 4px;
}

.card-price {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--accent);
}

.card-profit {
  font-size: .72rem;
  color: var(--muted);
}

/* Tags */
.card-tags {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.tag {
  padding: 1px 8px;
  border-radius: 100px;
  font-size: .65rem;
  font-weight: 600;
}

.tag-path {
  background: oklch(65% 0.1 270 / .12);
  color: oklch(55% 0.15 270);
}

.tag-status {
  background: oklch(75% 0.05 80 / .12);
  color: oklch(65% 0.08 80);
}

/* Actions */
.card-actions {
  display: flex;
  gap: 4px;
  margin-top: 10px;
}

.list-mode .card-actions {
  flex-direction: row;
  margin-top: 0;
  justify-content: flex-end;
}

.action-btn {
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 4px 8px;
  cursor: pointer;
  font-size: .82rem;
  transition: all 0.15s;
}

.action-btn:hover {
  border-color: var(--accent);
  background: oklch(56% 0.12 170 / .04);
}

.action-btn:disabled {
  opacity: .4;
  cursor: not-allowed;
}
</style>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Chapter { id: string; title: string; order: number }

const props = defineProps<{
  chapters?: Chapter[]
  authorName?: string
  bookTitle?: string
  visible: boolean
}>()
const emit = defineEmits<{ close: [] }>()

const form = ref({
  title: props.bookTitle || '',
  author: props.authorName || 'OriStudio Creator',
  tocEnabled: true,
})
const coverImage = ref<string | null>(null)

const sortedChapters = computed(() => [...(props.chapters || [])].sort((a, b) => a.order - b.order))

function onCoverSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) coverImage.value = file.name
}

function doExport() {
  alert(`导出 EPUB: ${form.value.title}`)
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="epub-export-modal-overlay">
      <div class="epub-export-modal">
        <div class="modal-header">
          <h3>导出 EPUB</h3>
          <button class="btn-close" @click="emit('close')">×</button>
        </div>
        <form @submit.prevent="doExport" class="modal-body">
          <div class="form-group">
            <label>书名</label>
            <input v-model="form.title" placeholder="请输入书名" />
          </div>
          <div class="form-group">
            <label>作者</label>
            <input v-model="form.author" placeholder="作者名称" />
          </div>
          <div class="form-group">
            <label>封面图片</label>
            <input type="file" accept="image/*" @change="onCoverSelect" />
            <span v-if="coverImage" class="cover-name">{{ coverImage }}</span>
          </div>
          <div class="form-group">
            <label><input type="checkbox" v-model="form.tocEnabled" /> 自动生成目录</label>
          </div>
          <div v-if="form.tocEnabled && sortedChapters.length" class="toc-preview">
            <h4>目录预览</h4>
            <ul><li v-for="ch in sortedChapters" :key="ch.id">{{ ch.title }}</li></ul>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline" @click="emit('close')">取消</button>
            <button type="submit" class="btn btn-primary">导出 EPUB</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.epub-export-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 200; }
.epub-export-modal { background: #fff; border-radius: 12px; width: 480px; max-width: 90vw; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #e5e7eb; }
.modal-header h3 { margin: 0; font-size: 18px; }
.btn-close { background: none; border: none; font-size: 20px; cursor: pointer; color: #9ca3af; }
.modal-body { padding: 20px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #374151; }
.form-group input[type="text"], .form-group input[type="file"] { width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; }
.cover-name { display: block; font-size: 12px; color: #6b7280; margin-top: 4px; }
.toc-preview { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; margin-bottom: 16px; }
.toc-preview h4 { margin: 0 0 8px; font-size: 14px; }
.toc-preview ul { list-style: none; padding: 0; margin: 0; }
.toc-preview li { padding: 4px 0; font-size: 13px; color: #374151; }
.modal-footer { display: flex; gap: 8px; justify-content: flex-end; padding-top: 12px; border-top: 1px solid #e5e7eb; }
</style>

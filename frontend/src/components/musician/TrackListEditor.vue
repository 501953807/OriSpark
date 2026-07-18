<script setup lang="ts">
import { ref, computed } from 'vue'

interface Track {
  id: string
  album_id: string
  track_number: number
  title: string
  isrc?: string
  duration_seconds?: number
  is_explicit?: boolean
}

const props = defineProps<{
  albumId: string
  initialTracks?: Track[]
}>()

const emit = defineEmits<{
  save: [tracks: Track[]]
  cancel: []
}>()

const tracks = ref<Track[]>(props.initialTracks || [])
const draggingIndex = ref<number | null>(null)

const sortedTracks = computed(() => [...tracks.value].sort((a, b) => a.track_number - b.track_number))

function addTrack() {
  const maxNum = tracks.value.reduce((max, t) => Math.max(max, t.track_number), 0)
  tracks.value.push({
    id: crypto.randomUUID?.() || Math.random().toString(36).slice(2),
    album_id: props.albumId,
    track_number: maxNum + 1,
    title: '',
  })
}

function deleteTrack(id: string) {
  tracks.value = tracks.value.filter(t => t.id !== id)
  renumber()
}

function renumber() {
  for (let i = 0; i < tracks.value.length; i++) {
    tracks.value[i].track_number = i + 1
  }
}

function onDragStart(index: number) {
  draggingIndex.value = index
}

function onDrop(targetIndex: number) {
  if (draggingIndex.value === null || draggingIndex.value === targetIndex) return
  const moved = tracks.value.splice(draggingIndex.value, 1)[0]
  tracks.value.splice(targetIndex, 0, moved)
  renumber()
  draggingIndex.value = null
}

function onSave() {
  emit('save', [...tracks.value])
}

function onCancel() {
  emit('cancel')
}
</script>

<template>
  <div class="track-list-editor">
    <div v-for="(track, index) in sortedTracks" :key="track.id"
         class="track-row" draggable @dragstart="onDragStart(index)" @dragover.prevent @drop="onDrop(index)">
      <span class="drag-handle" title="拖拽排序">⋮⋮</span>
      <span class="track-num">{{ track.track_number }}</span>
      <input v-model="track.title" class="track-title" placeholder="曲目名称" />
      <input v-model="track.isrc" class="track-isrc" placeholder="ISRC" maxlength="20" />
      <input v-model.number="track.duration_seconds" class="track-duration" type="number" placeholder="秒" min="0" />
      <button class="btn-icon btn-delete" @click="deleteTrack(track.id)" title="删除">×</button>
    </div>
    <button class="btn-add-track" @click="addTrack">+ 添加曲目</button>
    <div class="track-actions">
      <button class="btn btn-primary" @click="onSave">保存</button>
      <button class="btn btn-outline" @click="onCancel">取消</button>
    </div>
  </div>
</template>

<style scoped>
.track-list-editor { display: flex; flex-direction: column; gap: 4px; }
.track-row {
  display: flex; align-items: center; gap: 8px; padding: 8px;
  border: 1px solid #e5e7eb; border-radius: 6px; background: #fff;
}
.track-row:hover { border-color: #93c5fd; }
.drag-handle { cursor: grab; color: #9ca3af; font-size: 14px; user-select: none; }
.track-num { width: 24px; text-align: center; color: #6b7280; font-weight: 600; }
.track-title { flex: 1; padding: 4px 8px; border: 1px solid transparent; border-radius: 4px; }
.track-title:focus { border-color: #3b82f6; outline: none; }
.track-isrc { width: 120px; padding: 4px 8px; border: 1px solid #e5e7eb; border-radius: 4px; font-family: monospace; }
.track-duration { width: 80px; padding: 4px 8px; border: 1px solid #e5e7eb; border-radius: 4px; }
.btn-icon { background: none; border: none; cursor: pointer; color: #9ca3af; font-size: 16px; }
.btn-delete:hover { color: #ef4444; }
.btn-add-track { align-self: flex-start; margin-top: 8px; padding: 6px 12px; border: 1px dashed #d1d5db; border-radius: 6px; background: none; cursor: pointer; color: #6b7280; }
.btn-add-track:hover { border-color: #3b82f6; color: #3b82f6; }
.track-actions { display: flex; gap: 8px; margin-top: 12px; justify-content: flex-end; }
</style>

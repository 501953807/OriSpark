<template>
  <Teleport to="body">
    <div v-if="visible" class="edit-overlay" @click.self="$emit('close')">
      <div class="edit-panel animate-slide-right">
        <div class="panel-header">
          <h3>编辑作品</h3>
          <button class="close-btn" @click="$emit('close')">×</button>
        </div>

        <div class="panel-body">
          <!-- Basic Info -->
          <div class="section-label">基础信息</div>
          <div class="form-group">
            <label>作品名称</label>
            <input v-model="form.title" class="form-input" placeholder="输入作品名称" />
          </div>
          <div class="form-group">
            <label>简介</label>
            <textarea v-model="form.synopsis" class="form-textarea" rows="2" placeholder="作品简介…" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="form.description" class="form-textarea" rows="2" placeholder="添加描述…" />
          </div>
          <div class="form-group">
            <label>完成日期</label>
            <input v-model="form.completion_date" type="date" class="form-input" />
          </div>
          <div class="form-group">
            <label>创作工具</label>
            <input v-model="form.creation_tool" class="form-input" placeholder="如: Procreate, Photoshop" />
          </div>
          <div class="form-group">
            <label>创作地点</label>
            <input v-model="form.creation_location" class="form-input" placeholder="如: 北京" />
          </div>

          <!-- Rights Info -->
          <div class="section-label">权利信息</div>
          <div class="form-group">
            <label>作者署名</label>
            <input v-model="form.author_name" class="form-input" placeholder="创作者署名" />
          </div>
          <div class="form-group">
            <label>版权年份</label>
            <input v-model.number="form.copyright_year" type="number" class="form-input" placeholder="2026" min="1900" max="2100" />
          </div>
          <div class="form-group">
            <label>许可证</label>
            <LicenseSelector v-model="form.license_type" />
          </div>
          <div class="form-group">
            <label>署名文本</label>
            <input v-model="form.attribution_text" class="form-input" placeholder="© 山海画师 2026" />
          </div>

          <!-- Rights Toggles -->
          <div class="section-label">权利开关</div>
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.allow_reproduction" />
              允许复制
            </label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.allow_derivatives" />
              允许改编
            </label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="form.allow_commercial" />
              允许商用
            </label>
          </div>

          <!-- Stage -->
          <div class="section-label">过程管理</div>
          <div class="form-group">
            <label>当前阶段</label>
            <StageSelector v-model="form.current_stage" :file-type="work?.file_type || 'image'" />
          </div>

          <!-- Stage Notes (创作说明 — tied to current stage) -->
          <div class="form-group">
            <label>创作说明</label>
            <textarea v-model="form.stage_notes" class="form-textarea" rows="3" placeholder="记录当前阶段的创作思路、注意事项、参考链接…" />
            <span class="form-hint">此说明与当前选择的阶段关联，可在作品详情页的阶段详情面板中查看</span>
          </div>

          <!-- Project -->
          <div class="section-label">归属</div>
          <div class="form-group">
            <label>项目</label>
            <ProjectDropdown v-model="form.project_id" />
          </div>
          <div class="form-group">
            <label>标签</label>
            <TagInput v-model="form.tags" />
          </div>

          <!-- Type-Specific Fields -->
          <template v-if="work?.creator_type === 'photographer'">
            <div class="section-label">摄影参数</div>
            <div class="form-group">
              <label>相机型号</label>
              <input v-model="form.camera_model" class="form-input" placeholder="如: Sony A7IV" />
            </div>
            <div class="form-group">
              <label>镜头</label>
              <input v-model="form.lens" class="form-input" placeholder="如: FE 24-70mm f/2.8 GM" />
            </div>
            <div class="form-group">
              <label>RAW 文件路径</label>
              <input v-model="form.raw_file_path" class="form-input" placeholder="/path/to/raw/file" />
            </div>
          </template>

          <template v-if="work?.creator_type === 'musician'">
            <div class="section-label">音乐信息</div>
            <div class="form-group">
              <label>ISRC</label>
              <input v-model="form.isrc" class="form-input" placeholder="CN-xxx-xx-00001" />
            </div>
            <div class="form-group">
              <label>BPM</label>
              <input v-model.number="form.bpm" type="number" class="form-input" min="1" max="999" />
            </div>
            <div class="form-group">
              <label>调性</label>
              <input v-model="form.music_key" class="form-input" placeholder="如: C大调" />
            </div>
          </template>

          <template v-if="work?.creator_type === 'writer'">
            <div class="section-label">文稿信息</div>
            <div class="form-group">
              <label>字数</label>
              <input v-model.number="form.word_count" type="number" class="form-input" min="0" />
            </div>
            <div class="form-group">
              <label>章节数</label>
              <input v-model.number="form.chapter_count" type="number" class="form-input" min="0" />
            </div>
            <div class="form-group">
              <label>体裁</label>
              <input v-model="form.genre" class="form-input" placeholder="小说/散文/诗歌…" />
            </div>
          </template>

          <!-- Notes -->
          <div class="section-label">备注</div>
          <div class="form-group">
            <textarea v-model="form.description" class="form-textarea" rows="3" placeholder="备注信息…" />
          </div>
        </div>

        <div class="panel-footer">
          <button class="btn btn-secondary" @click="$emit('close')">取消</button>
          <button class="btn btn-danger" @click="$emit('delete')">删除</button>
          <button class="btn btn-primary" @click="handleSave">保存</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import StageSelector from './StageSelector.vue'
import ProjectDropdown from './ProjectDropdown.vue'
import TagInput from './TagInput.vue'
import LicenseSelector from './LicenseSelector.vue'
import type { WorkTag } from '@/types/work'
import { getStagesForFileType } from '@/composables/useWorkStages'

const props = defineProps<{
  visible: boolean
  work: {
    id: string
    title?: string
    description?: string | null
    tags?: WorkTag[]
    project_id?: string | null
    custom_metadata?: Record<string, any> | null
    rights?: Record<string, any> | null
    license_type?: string | null
    file_type?: string
    synopsis?: string | null
    completion_date?: string | null
    current_stage?: string | null
    copyright_year?: number | null
  } | null
}>()

const emit = defineEmits<{
  close: []
  save: [data: Record<string, any>]
  delete: []
}>()

const form = reactive({
  title: '',
  description: '',
  synopsis: '',
  completion_date: '',
  current_stage: '',
  stage_notes: '',  // 创作说明 — tied to current stage
  copyright_year: null as number | null,
  author_name: '',
  license_type: '',
  attribution_text: '',
  allow_reproduction: false,
  allow_derivatives: false,
  allow_commercial: false,
  creation_tool: '',
  creation_location: '',
  project_id: '',
  tags: [] as WorkTag[],
  // Photographer
  camera_model: '',
  lens: '',
  raw_file_path: '',
  // Musician
  isrc: '',
  bpm: null as number | null,
  music_key: '',
  // Writer
  word_count: null as number | null,
  chapter_count: null as number | null,
  genre: '',
})

watch(() => props.work, (w) => {
  if (w) {
    form.title = w.title || ''
    form.description = w.description || ''
    form.synopsis = w.synopsis || ''
    form.completion_date = w.completion_date || ''
    form.current_stage = w.current_stage || ''
    form.copyright_year = w.copyright_year || null

    // Rights from top-level rights JSON
    const rights = w.rights || {}
    form.author_name = rights.author_name || w.custom_metadata?.author_name || ''
    form.license_type = w.license_type || rights.license_type || ''
    form.attribution_text = rights.attribution_text || ''
    form.allow_reproduction = !!rights.allow_reproduction
    form.allow_derivatives = !!rights.allow_derivatives
    form.allow_commercial = !!rights.commercial_use

    // Custom metadata
    const cm = w.custom_metadata || {}
    form.creation_tool = cm.creation_tool || cm.creation_tool_name || ''
    form.creation_location = cm.creation_location || ''

    // Type-specific fields from custom_metadata
    form.camera_model = cm.camera_model || ''
    form.lens = cm.lens || ''
    form.raw_file_path = cm.raw_file_path || ''
    form.isrc = cm.isrc || ''
    form.bpm = cm.bpm ?? null
    form.music_key = cm.music_key || ''
    form.word_count = cm.word_count ?? null
    form.chapter_count = cm.chapter_count ?? null
    form.genre = cm.genre || ''

    // Tags
    form.tags = (w.tags || []).map(t => ({ ...t }))

    // Project
    form.project_id = w.project_id || ''

    // Stage notes: read from custom_metadata.stages[current_stage].notes
    const cs = w.current_stage
    const stageMeta = w.custom_metadata?.stages as Record<string, any> | undefined
    form.stage_notes = cs && stageMeta?.[cs]?.notes ? stageMeta[cs].notes : ''
  }
}, { immediate: true })

// When stage changes in edit panel, swap stage_notes to the new stage's notes
watch(() => form.current_stage, (newStage, oldStage) => {
  if (!oldStage || !newStage) return
  // Read from the previously loaded work's custom_metadata.stages
  const stageMeta = props.work?.custom_metadata?.stages as Record<string, any> | undefined
  if (stageMeta?.[newStage]?.notes) {
    form.stage_notes = stageMeta[newStage].notes
  } else {
    form.stage_notes = ''
  }
})

function handleSave() {
  const tagsStr = form.tags.map(t => t.tag).join(', ')
  const rights: Record<string, any> = {
    author_name: form.author_name,
    copyright_year: form.copyright_year,
    attribution_text: form.attribution_text,
    allow_reproduction: form.allow_reproduction,
    allow_derivatives: form.allow_derivatives,
    commercial_use: form.allow_commercial,
  }

  const metadata: Record<string, any> = {
    creation_tool: form.creation_tool,
    creation_location: form.creation_location,
  }

  // Type-specific metadata
  if (form.camera_model) metadata.camera_model = form.camera_model
  if (form.lens) metadata.lens = form.lens
  if (form.raw_file_path) metadata.raw_file_path = form.raw_file_path
  if (form.isrc) metadata.isrc = form.isrc
  if (form.bpm !== null) metadata.bpm = form.bpm
  if (form.music_key) metadata.music_key = form.music_key
  if (form.word_count !== null) metadata.word_count = form.word_count
  if (form.chapter_count !== null) metadata.chapter_count = form.chapter_count
  if (form.genre) metadata.genre = form.genre

  emit('save', {
    title: form.title,
    description: form.description,
    synopsis: form.synopsis,
    completion_date: form.completion_date,
    current_stage: form.current_stage,
    currentStage: form.current_stage,  // alias for WorkDetailView
    stage_notes: form.stage_notes,  // 创作说明
    copyright_year: form.copyright_year,
    license_type: form.license_type,
    project_id: form.project_id || null,
    tagsStr,
    tags: form.tags.map(t => t.tag),
    rights,
    custom_metadata: metadata,
  })
}
</script>

<style scoped>
.edit-overlay { position: fixed; inset: 0; background: oklch(0 0 0 / 0.3); z-index: 9998; }
.edit-panel {
  position: fixed; top: 0; right: 0; bottom: 0;
  width: 420px; max-width: 92vw;
  background: var(--surface); box-shadow: -4px 0 32px oklch(0 0 0 / 0.1);
  display: flex; flex-direction: column;
  overflow-y: auto;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  position: sticky; top: 0; background: var(--surface); z-index: 1;
}
.panel-header h3 { margin: 0; font-size: 1.1rem; }
.close-btn { background: none; border: none; font-size: 1.4rem; cursor: pointer; color: var(--muted); }
.panel-body { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.panel-footer {
  padding: 14px 20px; border-top: 1px solid var(--border);
  display: flex; justify-content: flex-end; gap: 10px;
  position: sticky; bottom: 0; background: var(--surface); z-index: 1;
}
.section-label {
  font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--accent);
  padding-top: 4px; border-top: 1px solid var(--border);
}
.section-label:first-child { border-top: none; padding-top: 0; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 0.8rem; font-weight: 600; color: var(--muted); }
.form-input, .form-textarea {
  padding: 9px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none;
}
.form-input:focus, .form-textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1); }
.form-textarea { resize: vertical; }
.form-hint {
  font-size: 0.7rem;
  color: var(--muted);
  font-style: italic;
  line-height: 1.4;
}
.btn { padding: 9px 18px; border-radius: var(--radius-sm); font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; font-family: var(--font-body); }
.btn-primary { background: var(--accent); color: #fff; }
.btn-secondary { background: var(--surface); color: var(--fg); border: 1px solid var(--border); }
.btn-danger { background: #e53e3e; color: #fff; }
.animate-slide-right { animation: slideRight 0.2s ease; }
@keyframes slideRight { from { transform: translateX(100%); } to { transform: translateX(0); } }
.checkbox-group { gap: 8px; }
.checkbox-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.85rem; cursor: pointer; font-weight: 400; color: var(--fg);
}
</style>

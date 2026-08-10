<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>发起合作要约</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>作品 ID</label>
          <input v-model="form.work_id" class="input" placeholder="输入作品ID" />
          <span v-if="workInfo" class="work-info">
            作品: {{ workInfo.title }} · 创作者: {{ workInfo.creator_name }}
          </span>
          <span v-if="workError" class="field-error">{{ workError }}</span>
        </div>

        <div class="form-group">
          <label>授权地区</label>
          <div class="multi-select">
            <label v-for="opt in REGION_OPTIONS" :key="opt.value" class="option-label">
              <input type="checkbox" :value="opt.value" v-model="form.scope.regions" />
              {{ opt.label }}
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>销售渠道</label>
          <div class="multi-select">
            <label v-for="opt in CHANNEL_OPTIONS" :key="opt.value" class="option-label">
              <input type="checkbox" :value="opt.value" v-model="form.scope.channels" />
              {{ opt.label }}
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>产品类型</label>
          <div class="multi-select">
            <label v-for="opt in PRODUCT_OPTIONS" :key="opt.value" class="option-label">
              <input type="checkbox" :value="opt.value" v-model="form.scope.products" />
              {{ opt.label }}
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>改编权利</label>
          <div class="multi-select">
            <label v-for="opt in TRANSFORM_RIGHTS_OPTIONS" :key="opt.key" class="option-label">
              <input type="checkbox" :value="true"
                     :checked="form.scope.transform_rights?.[opt.key]"
                     @change="toggleTransform(opt.key, $event)" />
              {{ opt.label }}
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>合作期限（月）</label>
          <input v-model.number="form.scope.duration_months" class="input" type="number" min="1" max="120" />
        </div>

        <div class="form-group">
          <label>备注说明</label>
          <textarea v-model="form.notes" class="textarea" rows="3"
                    placeholder="描述合作意向、预期用途等..."></textarea>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-submit" :disabled="submitting" @click="handleSubmit">
          {{ submitting ? '提交中...' : '发起要约' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { proposeCooperation, fetchWorkPublic } from '~/composables/useOperationApi'
import {
  REGION_OPTIONS, CHANNEL_OPTIONS, PRODUCT_OPTIONS, TRANSFORM_RIGHTS_OPTIONS,
} from '~/utils/operation'

defineEmits<{ (e: 'close'): void; (e: 'submitted'): void }>()

const form = ref({
  work_id: '',
  scope: {
    regions: [] as string[],
    channels: [] as string[],
    products: [] as string[],
    transform_rights: {} as Record<string, boolean>,
    duration_months: 12,
  },
  notes: '',
})

const workInfo = ref<any>(null)
const workError = ref('')
const submitting = ref(false)

let workFetchTimer: ReturnType<typeof setTimeout>

watch(() => form.value.work_id, (id) => {
  workInfo.value = null
  workError.value = ''
  clearTimeout(workFetchTimer)
  if (!id.trim()) return
  workFetchTimer = setTimeout(async () => {
    try {
      const info = await fetchWorkPublic(id)
      if (info) {
        workInfo.value = info
      } else {
        workError.value = '作品不存在'
      }
    } catch {
      workError.value = '查询失败，请检查作品ID'
    }
  }, 500)
})

function toggleTransform(key: string, event: Event) {
  const checked = (event.target as HTMLInputElement).checked
  form.value.scope.transform_rights = { ...form.value.scope.transform_rights, [key]: checked }
}

async function handleSubmit() {
  if (!form.value.work_id.trim()) {
    workError.value = '请输入作品ID'
    return
  }
  if (form.value.scope.regions.length === 0 &&
      form.value.scope.channels.length === 0 &&
      form.value.scope.products.length === 0) {
    workError.value = '请至少选择一个授权范围'
    return
  }
  submitting.value = true
  try {
    await proposeCooperation(form.value)
    emit('submitted')
  } catch (e) {
    workError.value = e instanceof Error ? e.message : '提交失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.modal {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 0 4px;
}

.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}

.input, .textarea {
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
}

.input:focus, .textarea:focus {
  outline: none;
  border-color: #059669;
}

.textarea {
  resize: vertical;
  min-height: 80px;
}

.work-info {
  font-size: 13px;
  color: #059669;
  padding: 8px 12px;
  background: #ecfdf5;
  border-radius: 6px;
}

.field-error {
  font-size: 13px;
  color: #ef4444;
}

.multi-select {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  transition: all 0.2s;
}

.option-label:hover {
  border-color: #059669;
  background: #ecfdf5;
}

.option-label input[type="checkbox"] {
  accent-color: #059669;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.btn-cancel {
  padding: 10px 20px;
  background: #fff;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.btn-submit {
  padding: 10px 20px;
  background: #059669;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-submit:hover:not(:disabled) {
  background: #047857;
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

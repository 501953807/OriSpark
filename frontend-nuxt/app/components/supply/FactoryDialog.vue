<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>注册新工厂</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>工厂名称 *</label>
          <input v-model="form.name" class="input" placeholder="如：东莞XX服饰有限公司" />
        </div>

        <div class="form-group">
          <label>所在地区</label>
          <input v-model="form.location" class="input" placeholder="如：广东省东莞市" />
        </div>

        <div class="form-group">
          <label>联系人</label>
          <input v-model="form.contact" class="input" placeholder="联系人姓名" />
        </div>

        <div class="form-group">
          <label>联系电话</label>
          <input v-model="form.phone" class="input" placeholder="手机号或座机" />
        </div>

        <div class="form-group">
          <label>邮箱</label>
          <input v-model="form.email" class="input" type="email" placeholder="工厂邮箱" />
        </div>

        <div class="form-group">
          <label>主营品类</label>
          <div class="multi-select">
            <label v-for="opt in CATEGORY_OPTIONS" :key="opt.value" class="option-label">
              <input type="checkbox" :value="opt.value" v-model="form.categories" />
              {{ opt.label }}
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>可生产产品</label>
          <div class="multi-select">
            <label v-for="opt in PRODUCT_OPTIONS" :key="opt.value" class="option-label">
              <input type="checkbox" :value="opt.value" v-model="form.product_categories" />
              {{ opt.label }}
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>最小起订量 (MOQ)</label>
          <input v-model.number="form.moq" class="input" type="number" min="1" />
        </div>

        <div class="form-group">
          <label>典型交期（天）</label>
          <input v-model.number="form.typical_lead_time_days" class="input" type="number" min="1" />
        </div>

        <div class="form-group">
          <label>备注</label>
          <textarea v-model="form.notes" class="textarea" rows="2"
                    placeholder="工厂简介、资质信息等..."></textarea>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-submit" :disabled="submitting" @click="handleSubmit">
          {{ submitting ? '提交中...' : '注册工厂' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { createFactory } from '~/composables/useSupplyApi'

defineEmits<{ (e: 'close'): void; (e: 'submitted'): void }>()

const CATEGORY_OPTIONS = [
  { value: 'clothing', label: '服饰' },
  { value: 'home_decor', label: '家居装饰' },
  { value: 'accessories', label: '配饰' },
  { value: 'stationery', label: '文具' },
  { value: 'toys', label: '玩具' },
  { value: 'sports', label: '运动用品' },
]

const PRODUCT_OPTIONS = [
  { value: 't_shirt', label: 'T恤' },
  { value: 'hoodie', label: '连帽衫' },
  { value: 'pin', label: '徽章' },
  { value: 'sticker', label: '贴纸' },
  { value: 'plush_toy', label: '毛绒玩具' },
  { value: 'poster', label: '海报' },
  { value: 'mug', label: '马克杯' },
  { value: 'phone_case', label: '手机壳' },
]

const form = ref({
  name: '',
  location: '',
  contact: '',
  phone: '',
  email: '',
  categories: [] as string[],
  product_categories: [] as string[],
  material_capabilities: [] as string[],
  moq: null as number | null,
  typical_lead_time_days: null as number | null,
  notes: '',
})

const submitting = ref(false)

async function handleSubmit() {
  if (!form.value.name.trim()) return
  submitting.value = true
  try {
    await createFactory(form.value)
    emit('submitted')
  } catch (e) {
    console.error('Failed to create factory:', e)
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
  background: rgba(46, 38, 61, 0.04);
  border: 1px solid rgba(46, 38, 61, 0.12);
  border-radius: 16px;
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(46, 38, 61, 0.12);
}

.modal-header h2 {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: rgba(46, 38, 61, 0.9);
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: rgba(46, 38, 61, 0.5);
}

.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(46, 38, 61, 0.5);
}

.input, .textarea {
  padding: 10px 14px;
  border: 1px solid rgba(46, 38, 61, 0.12);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
  background: rgba(46, 38, 61, 0.02);
  color: rgba(46, 38, 61, 0.9);
}

.input:focus, .textarea:focus {
  outline: none;
  border-color: var(--m-warning);
}

.textarea {
  resize: vertical;
  min-height: 60px;
}

.multi-select {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: rgba(46, 38, 61, 0.5);
  cursor: pointer;
  padding: 4px 10px;
  border: 1px solid rgba(46, 38, 61, 0.12);
  border-radius: 6px;
  transition: all 0.2s;
}

.option-label:hover {
  border-color: var(--m-warning);
  background: rgba(255, 180, 0, 0.08);
}

.option-label input[type="checkbox"] {
  accent-color: var(--m-warning);
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid rgba(46, 38, 61, 0.12);
}

.btn-cancel {
  padding: 10px 20px;
  background: transparent;
  color: rgba(46, 38, 61, 0.5);
  border: 1px solid rgba(46, 38, 61, 0.12);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.btn-submit {
  padding: 10px 20px;
  background: var(--m-warning);
  color: #0f172a;
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

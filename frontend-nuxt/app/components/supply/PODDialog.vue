<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>配置 POD 平台</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>平台 *</label>
          <select v-model="form.platform" class="input">
            <option v-for="opt in PLATFORM_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>API Key *</label>
          <input v-model="form.api_key" class="input" type="password" placeholder="输入 API Key" />
        </div>

        <div class="form-group">
          <label>API Secret</label>
          <input v-model="form.api_secret" class="input" type="password" placeholder="输入 API Secret" />
        </div>

        <div class="form-group">
          <label>默认店铺 ID</label>
          <input v-model="form.default_store_id" class="input" placeholder="平台店铺ID" />
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-submit" :disabled="submitting" @click="handleSubmit">
          {{ submitting ? '提交中...' : '保存配置' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { createPODConfig } from '~/composables/useSupplyApi'

defineEmits<{ (e: 'close'): void; (e: 'submitted'): void }>()

const PLATFORM_OPTIONS = [
  { value: 'printful', label: 'Printful' },
  { value: 'printify', label: 'Printify' },
  { value: 'gelato', label: 'Gelato' },
  { value: 'custom', label: '自定义' },
]

const form = ref({
  platform: 'printful',
  api_key: '',
  api_secret: '',
  default_store_id: '',
})

const submitting = ref(false)

async function handleSubmit() {
  if (!form.value.api_key.trim()) return
  submitting.value = true
  try {
    await createPODConfig(form.value)
    emit('submitted')
  } catch (e) {
    console.error('Failed to create POD config:', e)
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
  max-width: 440px;
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

.input {
  padding: 10px 14px;
  border: 1px solid rgba(46, 38, 61, 0.12);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  background: rgba(46, 38, 61, 0.02);
  color: rgba(46, 38, 61, 0.9);
}

.input:focus {
  outline: none;
  border-color: var(--m-warning);
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

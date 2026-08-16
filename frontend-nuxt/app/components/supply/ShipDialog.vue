<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>标记发货</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>物流方式</label>
          <input v-model="form.shipping_method" class="input" placeholder="如：顺丰快递" />
        </div>

        <div class="form-group">
          <label>快递单号</label>
          <input v-model="form.tracking_number" class="input" placeholder="输入快递单号" />
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-submit" :disabled="submitting" @click="handleSubmit">
          {{ submitting ? '提交中...' : '确认发货' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { shipOrder } from '~/composables/useSupplyApi'

const props = defineProps<{ id: string }>()
defineEmits<{ (e: 'close'): void; (e: 'submitted'): void }>()

const form = ref({
  shipping_method: '',
  tracking_number: '',
})

const submitting = ref(false)

async function handleSubmit() {
  submitting.value = true
  try {
    await shipOrder(props.id, form.value)
    emit('submitted')
  } catch (e) {
    console.error('Failed to ship:', e)
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
  max-width: 400px;
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
  color: rgba(46, 38, 61, 0.9);
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

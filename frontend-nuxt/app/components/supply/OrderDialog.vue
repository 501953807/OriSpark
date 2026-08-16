<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h2>创建生产订单</h2>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label>产品名称 *</label>
          <input v-model="form.product_name" class="input" placeholder="如：IP联名T恤" />
        </div>

        <div class="form-group">
          <label>关联工厂</label>
          <select v-model="form.factory_id" class="input">
            <option value="">暂不指定</option>
            <option v-for="f in factories" :key="f.id" :value="f.id">
              {{ f.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>产品品类</label>
          <select v-model="form.product_category" class="input">
            <option value="">不指定</option>
            <option value="apparel">服饰</option>
            <option value="accessories">配饰</option>
            <option value="home_decor">家居装饰</option>
            <option value="stationery">文具</option>
            <option value="toys">玩具</option>
            <option value="digital">数字产品</option>
          </select>
        </div>

        <div class="form-group" style="display: flex; gap: 12px;">
          <div style="flex: 1;">
            <label>数量</label>
            <input v-model.number="form.quantity" class="input" type="number" min="1" />
          </div>
          <div style="flex: 1;">
            <label>单价 (¥)</label>
            <input v-model.number="form.unit_price" class="input" type="number" min="0" step="0.01" />
          </div>
        </div>

        <div class="form-group">
          <label>预计交期</label>
          <input v-model="form.expected_date" class="input" type="date" />
        </div>

        <div class="form-group">
          <label>备注</label>
          <textarea v-model="form.notes" class="textarea" rows="2"
                    placeholder="特殊要求、工艺说明等..."></textarea>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-submit" :disabled="submitting" @click="handleSubmit">
          {{ submitting ? '提交中...' : '创建订单' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { createOrder } from '~/composables/useSupplyApi'

const props = defineProps<{ factories: any[] }>()
defineEmits<{ (e: 'close'): void; (e: 'submitted'): void }>()

const form = ref({
  factory_id: '',
  product_name: '',
  product_category: '',
  quantity: 10,
  unit_price: 0,
  expected_date: '',
  notes: '',
})

const submitting = ref(false)

async function handleSubmit() {
  if (!form.value.product_name.trim()) return
  submitting.value = true
  try {
    await createOrder(form.value)
    emit('submitted')
  } catch (e) {
    console.error('Failed to create order:', e)
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
  max-width: 480px;
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

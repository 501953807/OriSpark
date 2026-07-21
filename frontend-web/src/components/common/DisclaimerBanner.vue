<template>
  <!-- mode="modal": Full-screen modal with confirm button, used for first-time entry -->
  <div v-if="mode === 'modal' && visible" class="disclaimer-overlay" @click.self="onDismiss">
    <div class="disclaimer-modal card">
      <div class="disclaimer-modal-header">
        <span class="disclaimer-modal-icon">{{ icon }}</span>
        <h2>{{ title }}</h2>
      </div>
      <div class="disclaimer-modal-body">
        <p v-for="(item, idx) in messages" :key="idx" class="disclaimer-message">{{ item }}</p>
      </div>
      <div class="disclaimer-modal-footer">
        <label v-if="requireCheckbox" class="disclaimer-checkbox">
          <input v-model="checked" type="checkbox" />
          <span>{{ checkboxLabel }}</span>
        </label>
        <button
          class="btn btn-primary"
          :disabled="requireCheckbox && !checked"
          @click="onConfirm"
        >
          {{ confirmText }}
        </button>
      </div>
    </div>
  </div>

  <!-- mode="banner": Yellow warning bar at top of page/section, optionally dismissible -->
  <div v-else-if="mode === 'banner'" class="disclaimer-banner">
    <span class="disclaimer-banner-icon">⚠️</span>
    <div class="disclaimer-banner-content">
      <strong v-if="title">{{ title }}</strong>
      <p v-for="(item, idx) in messages" :key="idx">{{ item }}</p>
    </div>
    <button v-if="dismissible" class="disclaimer-banner-close" @click="onDismiss" title="关闭">&times;</button>
  </div>

  <!-- mode="footer": Subtle text at bottom of section -->
  <div v-else-if="mode === 'footer'" class="disclaimer-footer">
    <p v-for="(item, idx) in messages" :key="idx">{{ item }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = withDefaults(defineProps<{
  /** Display mode */
  mode: 'modal' | 'banner' | 'footer'
  /** Icon displayed in modal header */
  icon?: string
  /** Title text */
  title?: string
  /** Disclaimer message lines */
  messages: string[]
  /** Whether a checkbox confirmation is required (modal mode) */
  requireCheckbox?: boolean
  /** Checkbox label text */
  checkboxLabel?: string
  /** Confirm button text */
  confirmText?: string
  /** Whether the banner can be dismissed by user */
  dismissible?: boolean
  /** Whether modal is visible (modal mode) */
  visible?: boolean
}>(), {
  icon: '⚖️',
  title: '',
  messages: () => [],
  requireCheckbox: false,
  checkboxLabel: '我已阅读并理解上述声明',
  confirmText: '确认并继续',
  dismissible: false,
  visible: true,
})

const emit = defineEmits<{
  confirm: []
  dismiss: []
}>()

const checked = ref(false)

function onConfirm() {
  emit('confirm')
}

function onDismiss() {
  emit('dismiss')
}
</script>

<style scoped>
/* === Modal === */
.disclaimer-overlay {
  position: fixed; inset: 0; z-index: 9999;
  background: rgba(0, 0, 0, 0.5);
  display: flex; align-items: center; justify-content: center;
  padding: 20px;
}
.disclaimer-modal {
  max-width: 560px; width: 100%; max-height: 80vh; overflow-y: auto;
  background: var(--bg-card, #fff);
  border-radius: 12px; padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}
.disclaimer-modal-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
}
.disclaimer-modal-icon { font-size: 2rem; }
.disclaimer-modal-header h2 { font-size: 1.2rem; font-weight: 700; margin: 0; color: var(--text-primary); }
.disclaimer-message {
  font-size: 0.9rem; line-height: 1.6; color: var(--text-secondary);
  margin: 0 0 12px 0;
  padding-left: 16px; border-left: 3px solid var(--warning, #f0a020);
}
.disclaimer-modal-footer { margin-top: 24px; text-align: right; }
.disclaimer-checkbox {
  display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
  font-size: 0.88rem; color: var(--text-secondary);
}

/* === Banner === */
.disclaimer-banner {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 14px 16px; margin-bottom: 16px;
  background: #fff8e1; border: 1px solid #f0c040; border-radius: 8px;
  color: #6d4c00; font-size: 0.88rem; line-height: 1.5;
}
.disclaimer-banner-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }
.disclaimer-banner-content { flex: 1; }
.disclaimer-banner-content strong { display: block; margin-bottom: 2px; }
.disclaimer-banner-content p { margin: 0; }
.disclaimer-banner-close {
  background: none; border: none; font-size: 1.3rem; cursor: pointer;
  color: #6d4c00; opacity: 0.6; padding: 0 4px; line-height: 1;
}
.disclaimer-banner-close:hover { opacity: 1; }

/* === Footer === */
.disclaimer-footer {
  padding: 8px 0; text-align: center;
  font-size: 0.78rem; color: var(--text-muted, #999); line-height: 1.4;
}
.disclaimer-footer p { margin: 0; }

.btn { padding: 8px 24px; border-radius: 8px; font-size: 0.9rem; cursor: pointer; border: none; }
.btn-primary { background: var(--primary, #5b5fe3); color: #fff; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>

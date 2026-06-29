<template>
  <div class="license-selector">
    <div v-for="group in licenseGroups" :key="group.id" class="license-group">
      <div class="group-header">{{ group.label }}</div>
      <div class="group-options">
        <button
          v-for="opt in group.options"
          :key="opt.value"
          class="license-option"
          :class="{ selected: modelValue === opt.value }"
          @click="selectLicense(opt)"
          :title="opt.tooltip"
        >
          <span class="license-name">{{ opt.label }}</span>
          <span class="license-icon">{{ opt.icon }}</span>
        </button>
      </div>
    </div>

    <!-- Rights toggles (editable, auto-populated) -->
    <div v-if="modelValue" class="rights-toggles">
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
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

interface LicenseOption {
  value: string
  label: string
  icon: string
  tooltip: string
}

interface LicenseGroup {
  id: string
  label: string
  options: LicenseOption[]
}

const props = defineProps<{
  modelValue?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | undefined]
}>()

// Auto-rights mapping per license
const LICENSE_DEFAULTS: Record<string, { reproduction: boolean; derivatives: boolean; commercial: boolean }> = {
  'CC BY 4.0': { reproduction: true, derivatives: true, commercial: true },
  'CC BY-SA 4.0': { reproduction: true, derivatives: true, commercial: true },
  'CC BY-NC 4.0': { reproduction: true, derivatives: true, commercial: false },
  'CC BY-ND 4.0': { reproduction: true, derivatives: false, commercial: true },
  'CC BY-NC-SA 4.0': { reproduction: true, derivatives: true, commercial: false },
  'CC BY-NC-ND 4.0': { reproduction: true, derivatives: false, commercial: false },
  'CC0 1.0': { reproduction: true, derivatives: true, commercial: true },
  'All Rights Reserved': { reproduction: false, derivatives: false, commercial: false },
  'Public Domain': { reproduction: true, derivatives: true, commercial: true },
  'Custom': { reproduction: false, derivatives: false, commercial: false },
}

const form = reactive({
  allow_reproduction: false,
  allow_derivatives: false,
  allow_commercial: false,
})

// Sync form when modelValue changes externally
watch(() => props.modelValue, (val) => {
  if (val && LICENSE_DEFAULTS[val]) {
    const d = LICENSE_DEFAULTS[val]
    form.allow_reproduction = d.reproduction
    form.allow_derivatives = d.derivatives
    form.allow_commercial = d.commercial
  }
}, { immediate: true })

const licenseGroups: LicenseGroup[] = [
  {
    id: 'cc',
    label: '知识共享 (Creative Commons)',
    options: [
      { value: 'CC BY 4.0', label: 'CC BY 4.0', icon: '📢', tooltip: '署名 — 必须署名原作者，可商用，可修改' },
      { value: 'CC BY-SA 4.0', label: 'CC BY-SA 4.0', icon: '🔄', tooltip: '署名-相同方式共享 — 衍生作品必须使用相同许可证' },
      { value: 'CC BY-NC 4.0', label: 'CC BY-NC 4.0', icon: '🚫', tooltip: '署名-非商用 — 不可用于商业用途' },
      { value: 'CC BY-ND 4.0', label: 'CC BY-ND 4.0', icon: '🔒', tooltip: '署名-禁止改编 — 可商用但不得修改原作' },
      { value: 'CC BY-NC-SA 4.0', label: 'CC BY-NC-SA 4.0', icon: '🚫🔄', tooltip: '署名-非商用-相同方式共享' },
      { value: 'CC BY-NC-ND 4.0', label: 'CC BY-NC-ND 4.0', icon: '🚫🔒', tooltip: '署名-非商用-禁止改编 — 最限制的知识共享协议' },
      { value: 'CC0 1.0', label: 'CC0 1.0', icon: '🌍', tooltip: '公共领域贡献 — 放弃所有权利，任何人都可自由使用' },
    ],
  },
  {
    id: 'public',
    label: '公共领域',
    options: [
      { value: 'Public Domain', label: '公共领域', icon: '🏛️', tooltip: '无版权保护，任何人都可自由使用' },
    ],
  },
  {
    id: 'reserved',
    label: '保留所有权利',
    options: [
      { value: 'All Rights Reserved', label: '保留所有权利', icon: '©', tooltip: '默认版权 — 未经许可不得使用、复制或修改' },
    ],
  },
  {
    id: 'custom',
    label: '自定义',
    options: [
      { value: 'Custom', label: '自定义许可证', icon: '✏️', tooltip: '自定义条款，请自行设置下方权利开关' },
    ],
  },
]

function selectLicense(opt: LicenseOption) {
  emit('update:modelValue', opt.value)
  const defaults = LICENSE_DEFAULTS[opt.value]
  if (defaults) {
    form.allow_reproduction = defaults.reproduction
    form.allow_derivatives = defaults.derivatives
    form.allow_commercial = defaults.commercial
  }
}
</script>

<style scoped>
.license-selector { display: flex; flex-direction: column; gap: 12px; }
.license-group { display: flex; flex-direction: column; gap: 6px; }
.group-header {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  padding-bottom: 2px;
  border-bottom: 1px solid var(--border);
}
.group-options { display: flex; flex-wrap: wrap; gap: 4px; }
.license-option {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  cursor: pointer;
  font-size: 0.78rem;
  color: var(--fg);
  transition: all 0.15s;
}
.license-option:hover {
  border-color: var(--accent);
  background: oklch(56% 0.12 170 / 0.05);
}
.license-option.selected {
  border-color: var(--accent);
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--accent);
  font-weight: 600;
}
.license-icon { font-size: 0.85rem; }
.rights-toggles {
  padding: 10px 0;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  cursor: pointer;
}
.checkbox-label input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; }
</style>

<!-- Spec Remediation Panel — P2

Displays when spec validation fails (error_count > 0):
1. Recommended compatible products that WOULD pass
2. Minimum requirements info
3. Actionable remediation suggestions
4. Override option (checkbox + confirm)
-->
<template>
  <div class="spec-remediation-panel card">
    <!-- Error Banner -->
    <div v-if="errors.length" class="error-banner">
      <span class="error-icon">❌</span>
      <strong>规格校验未通过</strong>
      <span class="error-count">{{ errors.length }} 项错误</span>
    </div>

    <!-- Compatible Products Recommendation -->
    <div v-if="compatible.length" class="compatible-section">
      <h4>
        <span class="check-icon">✅</span>
        以下产品可以使用此设计稿:
      </h4>
      <div class="compatible-grid">
        <div
          v-for="t in compatible"
          :key="t.template_id"
          :class="['compatible-item', { selected: t.template_id === selectedTemplate }]"
          @click="handleSelect(t.template_id)"
        >
          <div class="compatible-name">{{ t.name_zh }}</div>
          <div class="compatible-en">{{ t.name_en }}</div>
          <div class="compatible-score">
            匹配度: {{ Math.round(t.compatibility_score * 100) }}%
          </div>
          <div class="compatible-req">
            需要 ≥ {{ t.min_required_px }}
          </div>
          <span v-if="t.current_meets" class="tag tag-pass">通过</span>
          <span v-else-if="t.spec_result === 'warning'" class="tag tag-warn">警告</span>
        </div>
      </div>
    </div>

    <!-- Remediation Suggestions -->
    <div v-if="suggestions.length" class="remediation-section">
      <h4>🔧 修复建议</h4>
      <div class="remediation-list">
        <div v-for="(s, i) in suggestions" :key="i" class="remediation-item">
          <span class="rem-type">{{ typeLabel(s.type) }}</span>
          <span class="rem-desc">{{ s.description }}</span>
          <span v-if="s.current && s.required" class="rem-change">
            {{ s.current }} → {{ s.required }}
          </span>
          <span v-if="s.scale_factor" class="rem-scale">
            需放大 {{ s.scale_factor }}
          </span>
        </div>
      </div>
    </div>

    <!-- Override Option -->
    <div class="override-section">
      <label class="override-label">
        <input type="checkbox" v-model="acknowledged" />
        我已知晓规格不达标，仍要创建此商品
      </label>
      <button
        class="btn btn-warning btn-sm"
        :disabled="!acknowledged"
        @click="$emit('override')"
      >
        确认继续
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { CompatibleTemplate, RemediationSuggestion } from '@/types/supply'

interface Props {
  errors: Array<{ check: string; message: string; suggestion: string }>
  compatible: CompatibleTemplate[]
  suggestions: RemediationSuggestion[]
}

defineProps<Props>()
const acknowledged = ref(false)
const emit = defineEmits<{
  (e: 'select-template', templateId: string): void
  (e: 'override'): void
}>()

const selectedTemplate = ref('')

function handleSelect(id: string) {
  selectedTemplate.value = id
  emit('select-template', id)
}

function typeLabel(type: string): string {
  const labels: Record<string, string> = {
    resize: '📐 尺寸',
    dpi: '🔍 DPI',
    color_mode: '🎨 色彩',
    format: '📁 格式',
    transparency: '💎 透明',
  }
  return labels[type] || type
}
</script>

<style scoped>
.spec-remediation-panel {
  padding: 18px 20px;
  margin-top: 12px;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  background: oklch(56% 0.18 20 / .1);
  color: oklch(56% 0.18 20);
  font-size: .88rem;
  margin-bottom: 16px;
}

.error-icon { font-size: 1.2rem; }
.error-count { margin-left: auto; font-weight: 600; }

/* Compatible products */
.compatible-section {
  margin-bottom: 16px;
}

.compatible-section h4 {
  font-size: .88rem;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.check-icon { font-size: 1.1rem; }

.compatible-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.compatible-item {
  padding: 10px 12px;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all .2s;
  font-size: .78rem;
}

.compatible-item:hover {
  border-color: var(--accent);
  background: oklch(56% 0.12 170 / .04);
}

.compatible-item.selected {
  border-color: var(--accent);
  background: oklch(56% 0.12 170 / .08);
}

.compatible-name {
  font-weight: 700;
  font-size: .84rem;
}

.compatible-en {
  color: var(--muted);
  font-size: .72rem;
}

.compatible-score {
  margin-top: 4px;
  font-weight: 600;
  color: var(--accent);
}

.compatible-req {
  font-size: .7rem;
  color: var(--muted);
}

/* Remediation */
.remediation-section {
  margin-bottom: 16px;
}

.remediation-section h4 {
  font-size: .88rem;
  margin-bottom: 10px;
}

.remediation-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.remediation-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: .78rem;
}

.rem-type {
  font-weight: 700;
  color: oklch(56% 0.18 20);
  white-space: nowrap;
  min-width: 60px;
}

.rem-desc {
  flex: 1;
}

.rem-change {
  color: var(--muted);
  font-size: .72rem;
}

.rem-scale {
  font-weight: 700;
  color: oklch(56% 0.18 20);
  font-size: .76rem;
}

/* Override */
.override-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.override-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: .82rem;
  color: var(--muted);
  cursor: pointer;
}

.override-label input {
  width: 16px;
  height: 16px;
}

.btn-warning {
  background: oklch(75% 0.18 80);
  color: #000;
  border: none;
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: .78rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-warning:disabled {
  opacity: .4;
  cursor: not-allowed;
}

.tag {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 100px;
  font-size: .62rem;
  margin-top: 4px;
}

.tag-pass {
  background: oklch(56% 0.12 140 / .15);
  color: oklch(56% 0.12 140);
}

.tag-warn {
  background: oklch(75% 0.12 80 / .15);
  color: oklch(56% 0.12 80);
}
</style>

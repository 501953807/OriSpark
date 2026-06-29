<template>
  <div class="code-viewer">
    <div class="code-header">
      <span class="code-lang">{{ language }}</span>
      <button class="code-copy btn btn-ghost btn-sm" @click="copyCode">{{ copied ? '✅ 已复制' : '📋 复制' }}</button>
    </div>
    <div class="code-body" ref="codeBodyRef">
      <pre><code :class="langClass" v-text="codeText"></code></pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const props = withDefaults(defineProps<{
  code?: string
  filePath?: string
  language?: string
}>(), {
  language: '',
})

const codeText = ref('')
const copied = ref(false)
const codeBodyRef = ref<HTMLElement>()

const langMap: Record<string, string> = {
  py: 'python', js: 'javascript', ts: 'typescript',
  vue: 'html', jsx: 'javascript', tsx: 'typescript',
  html: 'html', css: 'css', json: 'json',
  md: 'markdown', yaml: 'yaml', xml: 'xml',
  sh: 'bash', sql: 'sql', go: 'go', rs: 'rust',
  java: 'java', cpp: 'cpp', c: 'c',
}

const langClass = computed(() => {
  const ext = props.language?.toLowerCase() || ''
  return `language-${langMap[ext] || ext || 'text'}`
})

onMounted(() => {
  if (props.filePath) {
    fetch(props.filePath)
      .then(r => r.text())
      .then(t => { codeText.value = t })
      .catch(() => { codeText.value = props.code || '// 无法加载文件内容' })
  } else if (props.code) {
    codeText.value = props.code
  }
})

async function copyCode() {
  try {
    await navigator.clipboard.writeText(codeText.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    // fallback
  }
}
</script>

<style scoped>
.code-viewer {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  background: oklch(20% 0.01 260);
}
.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: oklch(25% 0.01 260);
  border-bottom: 1px solid oklch(30% 0.005 260);
}
.code-lang {
  font-size: 0.75rem;
  color: oklch(70% 0.01 260);
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.code-copy {
  color: oklch(70% 0.01 260) !important;
}
.code-body {
  padding: 16px;
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}
.code-body pre {
  margin: 0;
}
.code-body code {
  font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: 0.82rem;
  line-height: 1.6;
  color: oklch(90% 0.005 260);
  tab-size: 2;
}
.btn-sm { padding: 4px 10px; font-size: 0.72rem; }
</style>

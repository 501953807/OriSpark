<template>
  <div class="onboarding-card animate-fade-in">
    <!-- ===== Step 0: 选择参与角色 ===== -->
    <div v-if="currentStep === 0">
      <div class="ob-header">
        <span class="ob-badge">Step 1/4</span>
        <h2 class="ob-title">👋 欢迎来到 OriStudio</h2>
        <p class="ob-desc">选择你在合约市场中的参与角色，每个账户只能选择一个主身份</p>
      </div>

      <div class="role-grid">
        <div v-for="role in participantRoles" :key="role.key"
          :class="['role-card', { selected: selectedRole === role.key }]"
          @click="selectRole(role.key)"
        >
          <span class="role-icon">{{ role.icon }}</span>
          <strong>{{ role.label }}</strong>
          <p>{{ role.description }}</p>
          <small v-if="role.requires_license" class="license-hint">🏢 需公司资质认证</small>
          <small v-else class="personal-hint">👤 个人可注册</small>
        </div>
      </div>

      <div class="ob-actions">
        <button class="btn btn-primary btn-lg" :disabled="!selectedRole" @click="nextStep">
          {{ selectedRole ? '下一步 →' : '请选择参与角色' }}
        </button>
      </div>
    </div>

    <!-- ===== Step 1: 公司资质信息（非创作者角色）===== -->
    <div v-else-if="currentStep === 1 && selectedRole && selectedRole !== 'creator'">
      <div class="ob-header">
        <span class="ob-badge">Step 2/4</span>
        <h2 class="ob-title">🏢 公司资质信息</h2>
        <p class="ob-desc">请填写您的公司信息，用于合约市场身份验证</p>
      </div>

      <div class="company-form">
        <div class="form-group">
          <label>公司名称 *</label>
          <input v-model="companyForm.company_name" class="form-input" placeholder="请输入公司全称" />
        </div>
        <div class="form-group">
          <label>统一社会信用代码</label>
          <input v-model="companyForm.company_license_no" class="form-input" placeholder="18位统一社会信用代码" />
        </div>
        <div class="form-group">
          <label>公司地址</label>
          <input v-model="companyForm.company_address" class="form-input" placeholder="请输入公司地址" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>联系人</label>
            <input v-model="companyForm.company_contact" class="form-input" placeholder="联系人姓名" />
          </div>
          <div class="form-group">
            <label>联系电话</label>
            <input v-model="companyForm.company_phone" class="form-input" placeholder="联系电话" />
          </div>
        </div>
        <div class="form-group">
          <label>公司邮箱</label>
          <input v-model="companyForm.company_email" class="form-input" type="email" placeholder="company@example.com" />
        </div>
      </div>

      <div class="ob-actions">
        <button class="btn btn-secondary" @click="prevStep">← 上一步</button>
        <button class="btn btn-primary btn-lg" :disabled="!companyForm.company_name" @click="nextStep">
          下一步 →
        </button>
      </div>
    </div>

    <!-- ===== Step 1: 创作者类型（仅 creator 角色显示）===== -->
    <div v-else-if="currentStep === 1 && selectedRole === 'creator'">
      <div class="ob-header">
        <span class="ob-badge">Step 2/4</span>
        <h2 class="ob-title">🎨 选择创作者类型</h2>
        <p class="ob-desc">选择你的创作者类型，系统会自动调整最合适的功能</p>
      </div>

      <div class="creator-grid">
        <div v-for="ct in creatorTypes" :key="ct.key"
          :class="['creator-card', { selected: selectedCreator === ct.key, highlighted: ct.key === 'illustrator' }]"
          @click="selectCreator(ct.key)"
        >
          <span v-if="ct.key === 'illustrator'" class="creator-recommend">✨ 推荐</span>
          <span class="creator-icon">{{ ct.icon }}</span>
          <strong>{{ ct.label }}</strong>
          <p>{{ ct.shortDesc }}</p>
          <small>{{ ct.statusText }}</small>
        </div>
      </div>

      <div class="ob-actions">
        <button class="btn btn-secondary" @click="prevStep">← 上一步</button>
        <button class="btn btn-primary btn-lg" :disabled="!selectedCreator" @click="nextStep">
          {{ selectedCreator ? '下一步 →' : '请先选择创作者类型' }}
        </button>
      </div>
    </div>

    <!-- ===== Step 2: 导入作品（可选）===== -->
    <div v-else-if="currentStep === 2">
      <div class="ob-header">
        <span class="ob-badge">Step 3/4</span>
        <h2 class="ob-title">📂 导入你的作品（可选）</h2>
        <p class="ob-desc">如果你是创作者，可以导入作品；其他角色可跳过此步骤</p>
      </div>

      <FileDropZone
        v-if="selectedRole === 'creator'"
        :multiple="true"
        @uploaded="onFilesImported"
      />

      <div class="ob-actions">
        <button class="btn btn-secondary" @click="prevStep">← 上一步</button>
        <button class="btn btn-link" @click="skipImport">跳过，稍后导入 →</button>
      </div>
    </div>

    <!-- ===== Step 3: 快速上手 ===== -->
    <div v-else-if="currentStep === 3">
      <div class="ob-header">
        <div class="ob-success-icon">✨</div>
        <h2 class="ob-title">你已经准备好了！</h2>
        <p class="ob-desc">系统已根据你的角色 {{ roleLabel }} 自动配置</p>
      </div>

      <div class="workflow-cards">
        <div v-if="selectedRole === 'creator'" class="wf-card">
          <span class="wf-icon">🎨</span>
          <strong>管理作品</strong>
          <p>{{ importCount > 0 ? `查看刚导入的 ${importCount} 个作品` : '拖拽导入作品' }}</p>
        </div>
        <div v-if="selectedRole === 'creator'" class="wf-arrow">→</div>
        <div v-if="selectedRole === 'creator'" class="wf-card">
          <span class="wf-icon">🛡️</span>
          <strong>保护版权</strong>
          <p>选中作品一键存证</p>
        </div>
        <div v-if="selectedRole === 'creator'" class="wf-arrow">→</div>
        <div v-if="selectedRole === 'creator'" class="wf-card">
          <span class="wf-icon">💰</span>
          <strong>商业转化</strong>
          <p>授权变现、交易撮合</p>
        </div>
        <div v-else class="wf-card">
          <span class="wf-icon">{{ roleIcon }}</span>
          <strong>{{ roleLabel }}</strong>
          <p>开始使用 {{ roleLabel }} 功能</p>
        </div>
      </div>

      <div class="ob-actions">
        <button class="btn btn-secondary" @click="prevStep">← 上一步</button>
        <button class="btn btn-primary btn-lg" @click="handleFinish">🎉 开始使用，进入工作台</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import FileDropZone from '@/components/common/FileDropZone.vue'
import { systemApi } from '@/api/system'
import { PARTICIPANT_ROLES } from '@/types/roles'
import type { ParticipantRole } from '@/types/roles'

const props = withDefaults(defineProps<{
  initialCreatorType?: string
  autoStart?: boolean
}>(), {
  autoStart: true,
})

const emit = defineEmits<{
  finish: [payload: { creatorType: string; participantRole: string; importCount: number; companyInfo?: any }]
  skip: []
}>()

const currentStep = ref(0)
const selectedRole = ref<ParticipantRole>('creator')
const selectedCreator = ref(props.initialCreatorType || '')
const importCount = ref(0)
const participantRoles = ref<any[]>([])

// 公司资质表单
const companyForm = ref({
  company_name: '',
  company_license_no: '',
  company_address: '',
  company_contact: '',
  company_phone: '',
  company_email: '',
})

const roleLabel = computed(() => {
  if (!selectedRole.value) return ''
  return PARTICIPANT_ROLES[selectedRole.value]?.label || selectedRole.value
})

const roleIcon = computed(() => {
  if (!selectedRole.value) return '🎨'
  return PARTICIPANT_ROLES[selectedRole.value]?.icon || '🎨'
})

const creatorTypes = [
  {
    key: 'illustrator', icon: '🎨', label: '插画师 / AIGC艺术家',
    shortDesc: '插画、角色设计、AI生成图像', status: 'full',
    statusText: '✅ v1 完整支持 — 全链路功能可用',
  },
  {
    key: 'photographer', icon: '📷', label: '摄影师',
    shortDesc: '摄影后期、图库销售、预设包', status: 'full',
    statusText: '✅ v2 完整支持 — RAW/选片/水印/图库API/GPS',
  },
  {
    key: 'video', icon: '🎬', label: '视频创作者',
    shortDesc: '短视频、动画、品牌商单', status: 'full',
    statusText: '✅ v3 完整支持 — 工程文件/视频指纹/商单流程',
  },
  {
    key: 'craftsman', icon: '🖐', label: '手工艺人',
    shortDesc: '陶瓷、木器、布艺、首饰', status: 'full',
    statusText: '✅ v3b 完整支持 — 原件/库存/批次/询价/Etsy',
  },
  {
    key: 'musician', icon: '🎵', label: '音乐人',
    shortDesc: '原创音乐、配乐、采样包', status: 'full',
    statusText: '✅ v4 完整支持 — ISRC/发行/Split Sheets/分发',
  },
  {
    key: 'writer', icon: '✍️', label: '文字作者',
    shortDesc: '小说、剧本、商业撰稿', status: 'full',
    statusText: '✅ v4 完整支持 — 文章/书籍/手稿/出版',
  },
]

function selectRole(key: string) {
  selectedRole.value = key as ParticipantRole
  localStorage.setItem('oristudio-participant-role', key)
  // Reset company form when switching roles
  if (key !== 'creator') {
    companyForm.value = {
      company_name: '',
      company_license_no: '',
      company_address: '',
      company_contact: '',
      company_phone: '',
      company_email: '',
    }
  }
}

function selectCreator(key: string) {
  selectedCreator.value = key
  localStorage.setItem('oristudio-creator-type', key)
}

function nextStep() {
  if (currentStep.value === 0) {
    // 从角色选择跳转到下一步
    if (selectedRole.value === 'creator') {
      currentStep.value = 1 // 创作者类型
    } else {
      currentStep.value = 1 // 公司资质
    }
  } else if (currentStep.value === 1) {
    // 从创作者类型或公司资质跳转到导入作品
    currentStep.value = 2
  } else if (currentStep.value === 2) {
    // 从导入作品跳转到完成
    currentStep.value = 3
  }
}

function prevStep() {
  currentStep.value--
}

function onFilesImported(_count?: number) {
  importCount.value = _count || 0
  currentStep.value++
}

function skipImport() {
  currentStep.value++
}

function handleFinish() {
  emit('finish', {
    creatorType: selectedRole.value === 'creator' ? selectedCreator.value : '',
    participantRole: selectedRole.value,
    importCount: importCount.value,
    companyInfo: selectedRole.value !== 'creator' ? {
      company_name: companyForm.value.company_name,
      company_license_no: companyForm.value.company_license_no,
      company_address: companyForm.value.company_address,
      company_contact: companyForm.value.company_contact,
      company_phone: companyForm.value.company_phone,
      company_email: companyForm.value.company_email,
    } : undefined,
  })
}

onMounted(async () => {
  try {
    const res = await systemApi.participantRoles()
    participantRoles.value = res.data.data || []
  } catch {
    // Fallback to static definition
    participantRoles.value = Object.values(PARTICIPANT_ROLES)
  }

  // Restore from localStorage if no initial prop
  if (props.autoStart) {
    const savedRole = localStorage.getItem('oristudio-participant-role')
    const savedCreator = localStorage.getItem('oristudio-creator-type')
    if (savedRole) {
      selectedRole.value = savedRole as ParticipantRole
      if (savedCreator && selectedRole.value === 'creator') {
        selectedCreator.value = savedCreator
        currentStep.value = 2 // Skip to import step
      } else if (savedRole !== 'creator') {
        currentStep.value = 1 // Skip to company qualification step
      } else {
        currentStep.value = 1
      }
    }
  }
})
</script>

<style scoped>
.onboarding-card {
  max-width: 700px; width: 100%; padding: 40px;
  background: var(--bg-card, #fff); border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}
.animate-fade-in {
  animation: fade-in 0.3s ease;
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.ob-header { text-align: center; margin-bottom: 32px; }
.ob-badge { font-size: 0.78rem; color: var(--muted); }
.ob-title { font-size: 1.5rem; font-weight: 700; margin: 8px 0 4px; color: var(--text-primary); }
.ob-desc { font-size: 0.92rem; color: var(--text-secondary); margin: 0; }

.role-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px; }
.role-card {
  position: relative; padding: 16px; border: 2px solid var(--border); border-radius: 12px;
  cursor: pointer; transition: all 0.2s; text-align: center; background: var(--surface);
}
.role-card:hover { border-color: var(--accent); }
.role-card.selected { border-color: var(--accent); background: oklch(56% 0.12 170 / 0.04); }
.role-icon { font-size: 2rem; display: block; margin-bottom: 8px; }
.role-card strong { font-size: 0.9rem; display: block; color: var(--text-primary); }
.role-card p { font-size: 0.76rem; color: var(--text-secondary); margin: 4px 0; }
.role-card small { font-size: 0.7rem; display: block; margin-top: 4px; }
.license-hint { color: #f59e0b; }
.personal-hint { color: var(--muted); }

.creator-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 24px; }
.creator-card {
  position: relative; padding: 16px; border: 2px solid var(--border); border-radius: 12px;
  cursor: pointer; transition: all 0.2s; text-align: center; background: var(--surface);
}
.creator-card:hover { border-color: var(--accent); }
.creator-card.selected { border-color: var(--accent); background: oklch(56% 0.12 170 / 0.04); }
.creator-card.highlighted { border-color: var(--accent); border-width: 3px; box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.12); }
.creator-icon { font-size: 2rem; display: block; margin-bottom: 8px; }
.creator-card strong { font-size: 0.9rem; display: block; color: var(--text-primary); }
.creator-card p { font-size: 0.76rem; color: var(--text-secondary); margin: 4px 0; }
.creator-card small { font-size: 0.7rem; color: var(--muted); display: block; margin-top: 4px; }
.creator-recommend { position: absolute; top: -8px; right: -8px; padding: 2px 10px; border-radius: 100px; font-size: 0.72rem; font-weight: 700; background: var(--accent); color: #fff; }

/* 公司资质表单 */
.company-form {
  display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px;
  padding: 20px; background: var(--surface-hover); border-radius: 12px;
}
.dark .company-form { background: var(--sidebar-bg, oklch(12% 0.012 280)); }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-group label {
  font-size: 0.82rem; font-weight: 600; color: var(--muted);
}
.form-input {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--m-radius-sm);
  font-size: 0.9rem; font-family: Inter; color: var(--fg);
  background: var(--surface); outline: none; transition: border-color 0.2s;
}
.form-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(86,202,0,0.1); }

.workflow-cards { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.wf-card { padding: 16px; border: 1px solid var(--border); border-radius: 12px; text-align: center; min-width: 120px; background: var(--surface); }
.wf-icon { font-size: 1.6rem; display: block; margin-bottom: 6px; }
.wf-card strong { font-size: 0.85rem; display: block; color: var(--text-primary); }
.wf-card p { font-size: 0.74rem; color: var(--text-secondary); margin: 2px 0 0; }
.wf-arrow { font-size: 1.2rem; color: var(--accent); font-weight: 700; }

.ob-actions { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.btn { padding: 10px 20px; border-radius: var(--m-radius-sm); font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.2s; border: none; font-family: Inter; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: var(--surface); color: var(--fg); border: 1px solid var(--border); }
.btn-secondary:hover { background: var(--surface-hover); }
.btn-link { background: none; color: var(--accent); padding: 10px 0; }
.btn-link:hover { text-decoration: underline; }
.btn-lg { padding: 14px 28px; font-size: 1rem; }

.ob-success-icon { font-size: 3rem; margin-bottom: 12px; }
</style>

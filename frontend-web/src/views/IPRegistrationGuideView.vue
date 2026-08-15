<template>
  <div class="ipg-view">
    <h2>IP 登记指引</h2>
    <p class="subtle">根据您的作品信息推荐尼斯分类，追踪登记进度</p>

    <div class="ipg-layout">
      <!-- Left: Recommendation + Steps -->
      <div class="ipg-left">
        <div class="card">
          <div class="card-header">类别推荐</div>
          <div class="form-group">
            <label>IP 类型</label>
            <select v-model="form.ip_type" class="form-select">
              <option value="copyright">著作权</option>
              <option value="trademark">商标</option>
              <option value="design_patent">外观设计</option>
              <option value="utility_patent">专利</option>
            </select>
          </div>
          <div class="form-group">
            <label>作品描述 / 关键词</label>
            <textarea v-model="form.description" class="form-textarea" rows="4" placeholder="描述您的作品，如：插画角色设计，时尚潮牌服饰，玩具盲盒周边..."></textarea>
          </div>
          <button class="btn btn-primary" @click="recommend" :disabled="loading">
            {{ loading ? '推荐中...' : '推荐分类' }}
          </button>

          <div v-if="recommendResult.length > 0" class="recommend-list">
            <div v-for="(item, idx) in recommendResult" :key="idx" class="recommend-item">
              <div class="recommend-rank">#{{ idx + 1 }}</div>
              <div class="recommend-body">
                <div class="recommend-name">{{ item.class_name }}</div>
                <div class="recommend-sub">{{ item.class_name_en }}</div>
                <div class="recommend-desc">{{ item.description }}</div>
              </div>
              <div class="recommend-confidence">
                <span class="conf-badge" :class="confidenceLevel(item.confidence)">{{ confidenceLabel(item.confidence) }}</span>
                <span class="conf-pct">{{ (item.confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Progress tracker -->
      <div class="ipg-right">
        <div class="card">
          <div class="card-header">进度追踪</div>
          <div class="step-bar">
            <div v-for="(step, idx) in steps" :key="step.key"
              :class="['step-item', { active: currentStep >= idx, done: currentStep > idx, current: currentStep === idx }]">
              <div class="step-dot">{{ idx + 1 }}</div>
              <div class="step-label">{{ step.label }}</div>
            </div>
          </div>
          <div class="step-desc">{{ steps[currentStep]?.desc }}</div>
          <div class="step-actions">
            <button v-if="currentStep < steps.length - 1" class="btn btn-primary" @click="advanceStep">
              推进到{{ steps[currentStep + 1]?.label }}
            </button>
            <button v-if="currentStep > 0" class="btn btn-secondary" @click="currentStep--">
              回退
            </button>
            <span v-if="currentStep === steps.length - 1" class="step-complete">登记完成</span>
          </div>
          <textarea v-if="showNote" v-model="stepNote" class="form-textarea" rows="2" placeholder="备注（可选）"></textarea>
          <button v-if="showNote" class="btn btn-sm btn-secondary" @click="showNote = false">取消</button>
        </div>

        <div class="card" style="margin-top:12px">
          <div class="card-header">材料清单 · {{ steps[currentStep]?.label }}</div>
          <div class="material-section">
            <div class="material-title">必需材料</div>
            <ul class="material-list">
              <li v-for="(m, i) in materialList.required" :key="i" class="material-item">
                <span class="mi-name">{{ m.name }}</span>
                <span class="mi-desc">{{ m.description }}</span>
              </li>
            </ul>
          </div>
          <div class="material-section" v-if="materialList.optional.length > 0">
            <div class="material-title">可选材料</div>
            <ul class="material-list">
              <li v-for="(m, i) in materialList.optional" :key="i" class="material-item">
                <span class="mi-name">{{ m.name }}</span>
                <span class="mi-desc">{{ m.description }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import client from '@/api/client'

const form = ref({ ip_type: 'copyright', description: '' })
const loading = ref(false)
const recommendResult = ref<any[]>([])
const currentStep = ref(0)
const stepNote = ref('')
const showNote = ref(false)

const steps = [
  { key: 'draft', label: '草稿', desc: '填写基本信息，选择类别' },
  { key: 'submitted', label: '已提交', desc: '材料已提交官方机构' },
  { key: 'under_review', label: '审查中', desc: '官方正在审查申请' },
  { key: 'approved', label: '已通过', desc: '申请已获批准' },
  { key: 'registered', label: '已注册', desc: '登记完成，获得证书' },
]

const materialList = computed(() => {
  const templates: Record<string, Record<string, { required: any[]; optional: any[] }>> = {
    copyright: {
      draft: {
        required: [
          { name: '作品名称', description: '作品完整标题' },
          { name: '作者身份证明', description: '身份证/营业执照扫描件' },
          { name: '作品原件或清晰复印件', description: 'JPG/PNG格式，分辨率不低于300dpi' },
        ],
        optional: [
          { name: '作品创作说明', description: '创作背景、构思来源等' },
        ],
      },
      submitted: {
        required: [
          { name: '作品名称', description: '作品完整标题' },
          { name: '作者身份证明', description: '身份证/营业执照扫描件' },
          { name: '作品原件或清晰复印件', description: 'JPG/PNG格式，分辨率不低于300dpi' },
          { name: '申请表（已填写）', description: '在线填写并签名' },
        ],
        optional: [
          { name: '首次发表证明', description: '如已公开发表需提供' },
        ],
      },
      under_review: {
        required: [
          { name: '作品名称', description: '作品完整标题' },
          { name: '作者身份证明', description: '身份证/营业执照扫描件' },
          { name: '补正材料（如有）', description: '根据审查意见补充的材料' },
        ],
        optional: [],
      },
      approved: {
        required: [
          { name: '作品名称', description: '作品完整标题' },
          { name: '作者身份证明', description: '身份证/营业执照扫描件' },
        ],
        optional: [],
      },
      registered: {
        required: [{ name: '著作权登记证书', description: '官方颁发的登记证书' }],
        optional: [],
      },
    },
    trademark: {
      draft: {
        required: [
          { name: '商标图样', description: '清晰的商标图样（JPG格式）' },
          { name: '申请人身份证明', description: '个人身份证/企业营业执照' },
          { name: '拟注册类别及商品/服务项目', description: '尼斯分类选择' },
        ],
        optional: [
          { name: '商标说明', description: '商标设计理念、颜色说明等' },
        ],
      },
      submitted: {
        required: [
          { name: '商标图样', description: '清晰的商标图样（JPG格式）' },
          { name: '申请人身份证明', description: '个人身份证/企业营业执照' },
          { name: '商标注册申请表（已填写）', description: '在线填写并提交' },
        ],
        optional: [],
      },
      under_review: {
        required: [
          { name: '商标图样', description: '清晰的商标图样（JPG格式）' },
          { name: '申请人身份证明', description: '个人身份证/企业营业执照' },
          { name: '补正材料（如有）', description: '根据审查意见补充的材料' },
        ],
        optional: [],
      },
      approved: {
        required: [
          { name: '商标图样', description: '清晰的商标图样（JPG格式）' },
          { name: '申请人身份证明', description: '个人身份证/企业营业执照' },
        ],
        optional: [],
      },
      registered: {
        required: [{ name: '商标注册证', description: '官方颁发的商标注册证' }],
        optional: [],
      },
    },
    design_patent: {
      draft: {
        required: [
          { name: '外观设计图片或照片', description: '六面视图' },
          { name: '产品简要说明', description: '产品名称、用途、设计要点' },
          { name: '申请人身份证明', description: '个人身份证/企业营业执照' },
        ],
        optional: [],
      },
      submitted: {
        required: [
          { name: '外观设计图片或照片', description: '六面视图' },
          { name: '外观设计专利申请请求书', description: '在线填写并提交' },
        ],
        optional: [],
      },
      under_review: {
        required: [
          { name: '外观设计图片或照片', description: '六面视图' },
          { name: '补正材料（如有）', description: '根据审查意见补充的材料' },
        ],
        optional: [],
      },
      approved: {
        required: [{ name: '外观设计图片或照片', description: '六面视图' }],
        optional: [],
      },
      registered: {
        required: [{ name: '外观设计专利证书', description: '官方颁发的专利证书' }],
        optional: [],
      },
    },
  }
  const ipType = form.value.ip_type
  const template = templates[ipType] || templates['copyright']
  return template[steps[currentStep.value]?.key] || template['draft']
})

async function recommend() {
  loading.value = true
  try {
    const res = await client.post('/ipr/recommend-categories', {
      description: form.value.description,
      ip_type: form.value.ip_type,
    })
    recommendResult.value = res.data?.data || []
  } catch {
    recommendResult.value = []
  } finally {
    loading.value = false
  }
}

function advanceStep() {
  showNote.value = true
}

function confidenceLevel(c: number): string {
  if (c >= 0.7) return 'high'
  if (c >= 0.4) return 'medium'
  return 'low'
}

function confidenceLabel(c: number): string {
  if (c >= 0.7) return '高'
  if (c >= 0.4) return '中'
  return '低'
}
</script>

<style scoped>
.ipg-view { padding: 24px; max-width: 1100px; margin: 0 auto; }
.ipg-view h2 { margin: 0 0 4px; font-size: 1.4rem; font-weight: 700; }
.ipg-view .subtle { margin: 0 0 20px; color: var(--m-grey-500); font-size: 0.88rem; }
.ipg-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

/* Recommendation list */
.recommend-list { margin-top: 16px; }
.recommend-item { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid var(--m-border); border-radius: var(--m-radius-sm); margin-bottom: 8px; }
.recommend-rank { font-size: 1.2rem; font-weight: 700; color: rgb(85, 133, 255); min-width: 24px; }
.recommend-body { flex: 1; }
.recommend-name { font-weight: 600; font-size: 0.95rem; }
.recommend-sub { font-size: 0.78rem; color: var(--m-grey-500); }
.recommend-desc { font-size: 0.78rem; color: var(--m-grey-500); margin-top: 2px; }
.recommend-confidence { text-align: right; }
.conf-badge { display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 0.72rem; font-weight: 600; }
.conf-badge.high { background: oklch(60% 0.2 150 / .15); color: oklch(50% 0.18 150); }
.conf-badge.medium { background: oklch(80% 0.15 80 / .15); color: oklch(55% 0.2 80); }
.conf-badge.low { background: oklch(80% 0.1 30 / .15); color: oklch(55% 0.22 30); }
.conf-pct { display: block; font-size: 0.82rem; font-weight: 600; margin-top: 2px; }

/* Step bar */
.step-bar { display: flex; gap: 0; margin: 16px 0; }
.step-item { flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; }
.step-item:not(:last-child)::after {
  content: ''; position: absolute; top: 14px; left: 55%; right: -45%;
  height: 2px; background: var(--m-border); z-index: 0;
}
.step-item.done:not(:last-child)::after { background: rgb(85, 133, 255); }
.step-dot {
  width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 0.82rem; font-weight: 600; border: 2px solid var(--m-border); background: var(--m-surface);
  position: relative; z-index: 1; color: var(--m-grey-500);
}
.step-item.active .step-dot, .step-item.done .step-dot { border-color: rgb(85, 133, 255); background: rgb(85, 133, 255); color: #fff; }
.step-label { font-size: 0.72rem; color: var(--m-grey-500); margin-top: 4px; text-align: center; }
.step-item.active .step-label { color: var(--m-on-surface); font-weight: 600; }
.step-desc { font-size: 0.85rem; color: var(--m-grey-500); padding: 8px 0; border-top: 1px solid var(--m-border); }
.step-actions { display: flex; gap: 8px; margin-top: 12px; align-items: center; }
.step-complete { font-size: 0.9rem; color: oklch(50% 0.18 150); font-weight: 600; }

/* Material list */
.material-section { margin-bottom: 12px; }
.material-title { font-size: 0.82rem; font-weight: 600; color: var(--m-grey-500); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 6px; }
.material-list { list-style: none; padding: 0; margin: 0; }
.material-item { display: flex; justify-content: space-between; align-items: baseline; padding: 6px 0; border-bottom: 1px solid var(--border-subtle); font-size: 0.85rem; }
.mi-name { font-weight: 500; }
.mi-desc { font-size: 0.78rem; color: var(--m-grey-500); text-align: right; max-width: 60%; }

.form-select { padding: 10px 14px; border: 1px solid var(--m-border); border-radius: var(--m-radius-sm); font-size: .88rem; background: var(--m-surface); color: var(--m-on-surface); width: 100%; }
.form-textarea { padding: 10px 14px; border: 1px solid var(--m-border); border-radius: var(--m-radius-sm); font-size: .88rem; font-family: Inter; color: var(--m-on-surface); background: var(--m-surface); outline: none; resize: vertical; width: 100%; }
.form-textarea:focus { border-color: rgb(85, 133, 255); }

@media (max-width: 768px) {
  .ipg-layout { grid-template-columns: 1fr; }
  .material-item { flex-direction: column; gap: 2px; }
  .mi-desc { text-align: left; }
}
</style>

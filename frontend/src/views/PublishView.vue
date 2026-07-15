<template>
  <div class="publish-view">
    <!-- Loading state -->
    <div v-if="checking" class="publish-loading" style="text-align:center;padding:60px;color:var(--muted)">加载中...</div>

    <!-- 前置校验: 无作品时拦截 -->
    <EmptyState
      v-else-if="!hasWorks"
      icon="📱"
      title="暂无已确权作品"
      description="内容分发需要先上传作品并完成 IP 登记确权"
      :show-action="true"
      :primary-action="{ label: '前往上传作品', onClick: goToWorks }"
      :tips="['上传作品 → 完成 IP 登记 → 开启内容分发']"
    />

    <template v-else>
    <!-- Tabs -->
    <div class="cat-tabs">
      <button v-for="tab in tabs" :key="tab.key" :class="['cat-tab', { active: activeTab === tab.key }]" @click="activeTab = tab.key">{{ tab.label }}</button>
    </div>

    <!-- Products -->
    <div v-if="activeTab === 'products'" class="animate-fade-in">
      <div class="actions-bar">
        <button class="btn btn-primary" @click="showProductModal = true">+ 新商品</button>
      </div>
      <EmptyState v-if="!products.length" icon="🚀" title="暂无商品" description="创建你的第一个商品，AI将帮你生成多平台风格描述" />
      <div v-else class="product-grid">
        <div v-for="p in products" :key="p.id" class="product-card card">
          <div class="product-header">
            <h3>{{ p.title }}</h3>
            <span class="product-price">¥{{ p.price }}</span>
          </div>
          <p class="product-desc">{{ p.ai_description || p.description || '暂无描述' }}</p>
          <div class="product-meta">
            <span>📂 {{ p.category || '未分类' }}</span>
            <span v-if="p.csv_export_path">📥 CSV 已导出</span>
          </div>
          <div class="product-actions">
            <button class="btn btn-secondary btn-sm" @click="openDescribePanel(p.id)">🤖 AI描述</button>
            <button class="btn btn-secondary btn-sm" @click="exportCsv(p.id)">📥 CSV</button>
            <button class="btn btn-secondary btn-sm" @click="openBadgePanel(p.id)">🏷️ 徽章</button>
            <button class="btn btn-primary btn-sm" @click="publishProduct(p.id)">🚀 发布</button>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Description Panel (P1.6.2) -->
    <div v-if="activeTab === 'ai-desc'" class="animate-fade-in">
      <DisclaimerBanner
        mode="banner"
        title="AI内容标注要求（声明 #5）"
        :messages="['系统AI生成的内容，建议按各平台规则标注AI辅助生成。AI文案基于模板生成，不保证原创性，发布前请人工审核。']"
      />
      <div class="panel-header"><h3>🤖 AI 商品描述生成</h3><p class="panel-subtitle">选择平台风格，AI 自动生成营销文案</p></div>

      <div class="style-grid" v-if="describeStyles.length">
        <div v-for="s in describeStyles" :key="s.key"
          :class="['style-card', 'card', { selected: selectedStyle === s.key }]"
          @click="selectedStyle = s.key">
          <div class="style-icon">{{ s.icon }}</div>
          <div class="style-name">{{ s.name }}</div>
          <div class="style-desc">{{ s.description }}</div>
        </div>
      </div>

      <div class="form-row" v-if="products.length">
        <label>选择商品</label>
        <select v-model="selectedProductId" class="form-select">
          <option value="">-- 选择商品 --</option>
          <option v-for="p in products" :key="p.id" :value="p.id">{{ p.title }}</option>
        </select>
      </div>

      <div class="actions-bar">
        <button class="btn btn-primary" :disabled="!selectedStyle || !selectedProductId" @click="generateDescription">
          🤖 生成 AI 描述
        </button>
      </div>

      <div v-if="generatedResult" class="card result-card">
        <div class="result-header">
          <span class="result-style">{{ generatedResult.style_name }}</span>
          <span class="result-source" :class="generatedResult.source">{{ generatedResult.source === 'ollama' ? 'Ollama AI' : '本地模板' }}</span>
        </div>
        <pre class="result-content">{{ generatedResult.description }}</pre>
        <div class="result-actions">
          <button class="btn btn-secondary btn-sm" @click="copyToClipboard(generatedResult.description)">📋 复制</button>
        </div>
      </div>
    </div>

    <!-- Verified Badge Panel (P1.6.4) -->
    <div v-if="activeTab === 'badge'" class="animate-fade-in">
      <div class="panel-header"><h3>🏷️ OriStudio Verified 徽章</h3><p class="panel-subtitle">生成原创认证徽章，嵌入商品页证明原创</p></div>

      <div class="form-row" v-if="products.length">
        <label>选择商品</label>
        <select v-model="selectedProductId" class="form-select">
          <option value="">-- 选择商品 --</option>
          <option v-for="p in products" :key="p.id" :value="p.id">{{ p.title }}</option>
        </select>
      </div>

      <div class="actions-bar">
        <button class="btn btn-primary" :disabled="!selectedProductId" @click="generateBadge">
          🏷️ 生成 Verified 徽章
        </button>
      </div>

      <div v-if="badgeResult" class="card badge-result-card">
        <div class="badge-preview">
          <div v-if="badgeResult.badge_svg" v-html="badgeResult.badge_svg" style="max-width:360px"></div>
        </div>

        <div class="badge-meta">
          <div class="meta-item">
            <span class="meta-label">验证URL</span>
            <code class="meta-value">{{ badgeResult.verify_url }}</code>
          </div>
          <div class="meta-item">
            <span class="meta-label">QR 码</span>
            <img v-if="badgeResult.qr_url" :src="badgeResult.qr_url" style="width:80px;height:80px" alt="QR" />
          </div>
        </div>

        <div class="badge-download-options">
          <h4>下载选项</h4>
          <div class="btn-group">
            <button class="btn btn-secondary btn-sm" @click="downloadBadgeSVG">📥 SVG</button>
            <button class="btn btn-secondary btn-sm" @click="downloadBadgePNG">📥 PNG</button>
            <button class="btn btn-secondary btn-sm" @click="loadEmbedCode">📋 嵌入代码</button>
          </div>
        </div>

        <div v-if="embedCode" class="embed-code-block card">
          <h4>HTML 嵌入代码</h4>
          <pre class="embed-code">{{ embedCode.html }}</pre>
          <button class="btn btn-secondary btn-sm" @click="copyToClipboard(embedCode.html)">📋 复制</button>
        </div>
      </div>
    </div>

    <!-- Feed Export Panel (P1.6.8) -->
    <div v-if="activeTab === 'feed'" class="animate-fade-in">
      <div class="panel-header"><h3>📦 JSON Product Feed 导出</h3><p class="panel-subtitle">标准产品数据导出，兼容 Google / Shopify / 主流ERP</p></div>

      <div class="feed-options card">
        <div class="form-group">
          <label>目标平台</label>
          <div class="platform-grid">
            <button v-for="fp in feedPlatforms" :key="fp.key"
              :class="['btn', 'btn-sm', feedPlatform === fp.key ? 'btn-primary' : 'btn-secondary']"
              @click="feedPlatform = fp.key"
              :title="fp.description">
              {{ fp.name }}
              <span v-if="fp.status === 'planned'" class="badge-planned">计划中</span>
            </button>
          </div>
        </div>
        <div class="form-group">
          <label>品类筛选 (可选)</label>
          <select v-model="feedCategory" class="form-select">
            <option value="">全部</option>
            <option v-for="c in uniqueCategories" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="exportFeed">📤 导出 Feed</button>
      </div>

      <div v-if="feedResult" class="feed-result card">
        <div class="feed-meta">
          <span>版本: {{ feedResult.feed?.version }}</span>
          <span>产品数: {{ feedResult.feed?.total_products }}</span>
          <span>目标: {{ feedResult.feed?.target || 'universal' }}</span>
        </div>
        <div class="feed-actions">
          <button class="btn btn-secondary btn-sm" @click="downloadFeed">📥 下载 JSON</button>
          <button class="btn btn-secondary btn-sm" @click="copyToClipboard(JSON.stringify(feedResult, null, 2))">📋 复制</button>
        </div>
        <pre class="feed-preview">{{ JSON.stringify(feedResult, null, 2).substring(0, 3000) }}{{ JSON.stringify(feedResult, null, 2).length > 3000 ? '...' : '' }}</pre>
      </div>
    </div>

    <!-- Revenue -->
    <div v-if="activeTab === 'revenue'" class="animate-fade-in">
      <div class="actions-bar">
        <button class="btn btn-primary" @click="showRevenueModal = true">+ 记录收入</button>
        <button class="btn btn-secondary" @click="showImportModal = true">📥 导入CSV</button>
        <select v-model="revenuePeriod" class="form-select form-select-sm" @change="loadRevenueSummary" style="width:120px">
          <option value="month">本月</option>
          <option value="year">本年</option>
          <option value="all">全部</option>
        </select>
      </div>

      <!-- Revenue Summary Stats -->
      <div v-if="revenueSummary" class="revenue-summary card">
        <div class="summary-item"><span class="summary-label">{{ revenueSummary.label }}收入</span><span class="summary-value">¥{{ revenueSummary.total_amount.toFixed(2) }}</span></div>
        <div class="summary-item"><span class="summary-label">订单数</span><span class="summary-value">{{ revenueSummary.total_orders }}</span></div>
        <div class="summary-item"><span class="summary-label">退款</span><span class="summary-value">¥{{ revenueSummary.total_refunds.toFixed(2) }}</span></div>
        <div class="summary-item"><span class="summary-label">平台数</span><span class="summary-value">{{ revenueSummary.platform_count }}</span></div>
      </div>

      <!-- Platform Breakdown -->
      <div v-if="revenueSummary && Object.keys(revenueSummary.by_platform).length" class="card" style="margin-top:16px">
        <h4 style="margin:0 0 12px">按平台</h4>
        <div class="platform-breakdown">
          <div v-for="(amount, platform) in revenueSummary.by_platform" :key="platform" class="platform-bar-row">
            <span class="platform-name">{{ platform }}</span>
            <div class="platform-bar-track">
              <div class="platform-bar" :style="{ width: (amount / maxPlatformAmount * 100) + '%' }"></div>
            </div>
            <span class="platform-amount">¥{{ amount.toFixed(0) }}</span>
          </div>
        </div>
      </div>

      <EmptyState v-if="!revenues.length" icon="💰" title="暂无收入记录" description="手动添加各平台的销售收入，或导入对账单CSV" />
      <div v-else>
        <RevenueCharts v-if="revenues.length >= 2" :revenues="revenues" />
        <div class="revenue-list">
          <div v-for="r in revenues" :key="r.id" class="revenue-row">
            <span>{{ r.platform }}</span>
            <span>¥{{ r.amount }}</span>
            <span>{{ r.order_count }} 单</span>
            <span class="revenue-date">{{ r.date?.slice(0,10) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Product Modal -->
    <div v-if="showProductModal" class="modal-overlay" @click.self="showProductModal = false">
      <div class="modal-card animate-scale-in" style="max-width:480px">
        <div class="modal-header"><h3>创建商品</h3><button class="modal-close-btn" @click="showProductModal = false">×</button></div>
        <div class="form-group"><label>标题</label><input v-model="productForm.title" class="form-input" /></div>
        <div class="form-group"><label>价格</label><input v-model.number="productForm.price" type="number" class="form-input" /></div>
        <div class="form-group"><label>品类</label><input v-model="productForm.category" class="form-input" /></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showProductModal = false">取消</button>
          <button class="btn btn-primary" @click="createProduct">创建</button>
        </div>
      </div>
    </div>

    <!-- Revenue Modal -->
    <div v-if="showRevenueModal" class="modal-overlay" @click.self="showRevenueModal = false">
      <div class="modal-card animate-scale-in" style="max-width:400px">
        <div class="modal-header"><h3>记录收入</h3><button class="modal-close-btn" @click="showRevenueModal = false">×</button></div>
        <div class="form-group"><label>平台</label><input v-model="revenueForm.platform" class="form-input" placeholder="淘宝/小红书/抖音" /></div>
        <div class="form-group"><label>金额</label><input v-model.number="revenueForm.amount" type="number" class="form-input" /></div>
        <div class="form-group"><label>日期</label><input v-model="revenueForm.date" type="date" class="form-input" /></div>
        <div class="form-group"><label>订单数</label><input v-model.number="revenueForm.order_count" type="number" class="form-input" /></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showRevenueModal = false">取消</button>
          <button class="btn btn-primary" @click="addRevenue">保存</button>
        </div>
      </div>
    </div>

    <!-- CSV Import Modal -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal-card animate-scale-in" style="max-width:440px">
        <div class="modal-header"><h3>导入对账单 CSV</h3><button class="modal-close-btn" @click="showImportModal = false">×</button></div>
        <p style="font-size:.82rem;color:var(--muted)">支持淘宝/抖音/通用格式的 CSV 对账单。自动检测格式。</p>
        <div class="form-group">
          <input type="file" accept=".csv" @change="onFileSelected" class="form-input" />
        </div>
        <div v-if="importResult" class="card" style="margin-top:12px;padding:12px">
          <div style="color:var(--accent);font-weight:600">导入完成</div>
          <div>记录数: {{ importResult.imported }}</div>
          <div>总金额: ¥{{ importResult.total_amount }}</div>
          <div>格式: {{ importResult.detected_format }}</div>
          <div v-if="importResult.errors?.length" style="color:red;font-size:.8rem;margin-top:8px">
            {{ importResult.errors.length }} 条失败
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showImportModal = false">关闭</button>
          <button class="btn btn-primary" @click="importCsv" :disabled="!selectedFile">导入</button>
        </div>
      </div>
    </div>

    <!-- Platform select modal -->
    <div v-if="showPublishModal" class="modal-overlay" @click.self="showPublishModal = false">
      <div class="modal-card animate-scale-in" style="max-width:360px">
        <div class="modal-header"><h3>选择发布平台</h3><button class="modal-close-btn" @click="showPublishModal = false">×</button></div>
        <div class="platform-list">
          <button v-for="pl in publishPlatforms" :key="pl.key" class="btn btn-secondary" style="width:100%;justify-content:center;margin-bottom:8px" @click="doPublish(publishProductId!, pl.key)">{{ pl.name }}</button>
        </div>
      </div>
    </div>

    <!-- Schedule Tab (P2) -->
    <div v-if="activeTab === 'schedule'" class="animate-fade-in">
      <div class="actions-bar">
        <button class="btn btn-primary" @click="showScheduleModal = true">+ 新建排期</button>
      </div>
      <EmptyState v-if="!schedules.length" icon="📅" title="暂无排期发布" description="提前安排内容发布时间，保持稳定的内容产出节奏" />
      <div v-else class="schedule-list">
        <div v-for="s in schedules" :key="s.id" class="schedule-row card">
          <div class="schedule-info">
            <strong>{{ s.platform }}</strong>
            <span class="schedule-time">{{ s.scheduled_time?.slice(0, 16) || '—' }}</span>
          </div>
          <span :class="['status-badge', s.status]">{{ statusLabel(s.status) }}</span>
          <div class="schedule-actions">
            <button v-if="s.status === 'scheduled'" class="btn btn-danger btn-sm" @click="cancelSchedule(s.id)">取消</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Analytics Tab (P2) -->
    <div v-if="activeTab === 'analytics'" class="animate-fade-in">
      <div class="actions-bar">
        <button class="btn btn-primary" @click="showAnalyticsModal = true">+ 录入数据</button>
        <select v-model="analyticsPlatform" class="form-select form-select-sm" style="width:140px" @change="loadAnalytics">
          <option value="">全部平台</option>
          <option v-for="p in publishPlatforms" :key="p.key" :value="p.key">{{ p.name }}</option>
        </select>
      </div>
      <EmptyState v-if="!analyticsData.length" icon="📊" title="暂无影响力数据" description="手动录入各平台的浏览量、点赞、评论等数据，查看增长趋势" />
      <div v-else>
        <!-- Summary cards -->
        <div class="analytics-summary card">
          <div class="summary-item"><span class="summary-label">总浏览</span><span class="summary-value">{{ analyticsData.reduce((s, a) => s + (a.views || 0), 0).toLocaleString() }}</span></div>
          <div class="summary-item"><span class="summary-label">总点赞</span><span class="summary-value">{{ analyticsData.reduce((s, a) => s + (a.likes || 0), 0).toLocaleString() }}</span></div>
          <div class="summary-item"><span class="summary-label">总评论</span><span class="summary-value">{{ analyticsData.reduce((s, a) => s + (a.comments || 0), 0).toLocaleString() }}</span></div>
          <div class="summary-item"><span class="summary-label">总分享</span><span class="summary-value">{{ analyticsData.reduce((s, a) => s + (a.shares || 0), 0).toLocaleString() }}</span></div>
        </div>
        <RevenueCharts v-if="analyticsData.length >= 2" :revenues="analyticsData" />
        <div class="analytics-list">
          <div v-for="a in analyticsData" :key="a.id" class="analytics-row">
            <span>{{ a.platform }}</span>
            <span>{{ a.views }} 浏览</span>
            <span>{{ a.likes }} 赞</span>
            <span>{{ a.comments }} 评</span>
            <span class="analytics-date">{{ a.date?.slice(0, 10) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Schedule Modal (P2) -->
    <div v-if="showScheduleModal" class="modal-overlay" @click.self="showScheduleModal = false">
      <div class="modal-card animate-scale-in" style="max-width:440px">
        <div class="modal-header"><h3>新建排期</h3><button class="modal-close-btn" @click="showScheduleModal = false">×</button></div>
        <div class="form-group"><label>平台</label><input v-model="scheduleForm.platform" class="form-input" placeholder="小红书/微博/B站" /></div>
        <div class="form-group"><label>排期时间</label><input v-model="scheduleForm.scheduled_time" type="datetime-local" class="form-input" /></div>
        <div class="form-group"><label>文案预览</label><textarea v-model="scheduleForm.content_preview" class="form-input" rows="3" placeholder="发布文案预览..." /></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showScheduleModal = false">取消</button>
          <button class="btn btn-primary" @click="createSchedule">创建</button>
        </div>
      </div>
    </div>

    <!-- Analytics Modal (P2) -->
    <div v-if="showAnalyticsModal" class="modal-overlay" @click.self="showAnalyticsModal = false">
      <div class="modal-card animate-scale-in" style="max-width:400px">
        <div class="modal-header"><h3>录入影响力数据</h3><button class="modal-close-btn" @click="showAnalyticsModal = false">×</button></div>
        <div class="form-group"><label>平台</label><input v-model="analyticsForm.platform" class="form-input" placeholder="小红书/微博/B站" /></div>
        <div class="form-group"><label>日期</label><input v-model="analyticsForm.date" type="date" class="form-input" /></div>
        <div class="form-group"><label>浏览量</label><input v-model.number="analyticsForm.views" type="number" class="form-input" /></div>
        <div class="form-group"><label>点赞</label><input v-model.number="analyticsForm.likes" type="number" class="form-input" /></div>
        <div class="form-group"><label>评论</label><input v-model.number="analyticsForm.comments" type="number" class="form-input" /></div>
        <div class="form-group"><label>分享</label><input v-model.number="analyticsForm.shares" type="number" class="form-input" /></div>
        <div class="form-group"><label>收藏</label><input v-model.number="analyticsForm.saves" type="number" class="form-input" /></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAnalyticsModal = false">取消</button>
          <button class="btn btn-primary" @click="addAnalytics">保存</button>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/useAppStore'
import EmptyState from '@/components/common/EmptyState.vue'
import DisclaimerBanner from '@/components/common/DisclaimerBanner.vue'
import { publishApi } from '@/api/publish'
import { worksApi } from '@/api/works'

// Lazy-load RevenueCharts (pulls in echarts ~1MB)
const RevenueCharts = defineAsyncComponent(() => import('@/components/common/RevenueCharts.vue'))

const router = useRouter()
const appStore = useAppStore()
const hasWorks = ref(false)
const checking = ref(true)
const goToWorks = () => router.push('/app/works')

const activeTab = ref('products')
const tabs = [
  { key: 'products', label: '📦 商品' },
  { key: 'ai-desc', label: '🤖 AI描述' },
  { key: 'badge', label: '🏷️ 徽章' },
  { key: 'feed', label: '📦 Feed导出' },
  { key: 'revenue', label: '💰 收入' },
  { key: 'schedule', label: '📅 排期发布' },
  { key: 'analytics', label: '📊 影响力' },
]

const products = ref<any[]>([])
const revenues = ref<any[]>([])
const publishPlatforms = ref<any[]>([])

// ─── Modals ───
const showProductModal = ref(false)
const showRevenueModal = ref(false)
const showImportModal = ref(false)
const showPublishModal = ref(false)
const publishProductId = ref<string | null>(null)

// ─── Forms ───
const productForm = ref({ title: '', price: 0, category: '' })
const revenueForm = ref({ platform: '', amount: 0, order_count: 1, date: new Date().toISOString().slice(0, 10) })
const selectedFile = ref<File | null>(null)
const importResult = ref<any>(null)
const revenuePeriod = ref('month')

// ─── Computed ───
const totalRevenue = computed(() => revenues.value.reduce((s, r) => s + (r.amount||0), 0))
const totalOrders = computed(() => revenues.value.reduce((s, r) => s + (r.order_count||0), 0))
const platformCount = computed(() => new Set(revenues.value.map(r => r.platform)).size)

// ─── P1.6.2: AI Description ───
const describeStyles = ref<any[]>([])
const selectedStyle = ref('xiaohongshu')
const selectedProductId = ref('')
const generatedResult = ref<any>(null)

// ─── P1.6.4: Verified Badge ───
const badgeResult = ref<any>(null)
const embedCode = ref<any>(null)

// ─── P1.6.8: Feed Export ───
const feedPlatforms = ref<any[]>([])
const feedPlatform = ref('universal')
const feedCategory = ref('')
const feedResult = ref<any>(null)

// ─── Revenue Summary ───
const revenueSummary = ref<any>(null)
const maxPlatformAmount = computed(() => {
  if (!revenueSummary.value?.by_platform) return 1
  return Math.max(1, ...Object.values(revenueSummary.value.by_platform) as number[])
})
const uniqueCategories = computed(() => [...new Set(products.value.map(p => p.category).filter(Boolean))] as string[])

// ─── Schedule (P2) ───
const schedules = ref<any[]>([])
const showScheduleModal = ref(false)
const scheduleForm = ref({ product_id: '', platform: '', scheduled_time: '', content_preview: '' })

// ─── Analytics (P2) ───
const analyticsData = ref<any[]>([])
const showAnalyticsModal = ref(false)
const analyticsForm = ref({ platform: '', views: 0, likes: 0, comments: 0, shares: 0, saves: 0, date: new Date().toISOString().slice(0, 10), notes: '' })
const analyticsPlatform = ref('')

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    scheduled: '待发布', executing: '执行中', succeeded: '已发布', failed: '失败', cancelled: '已取消',
  }
  return map[status] || status
}

// ─── Data loading ───
async function loadProducts() { try { const res = await publishApi.products(); products.value = res.data.data } catch (e) { /* ignore */ } }
async function loadRevenue() { try { const res = await publishApi.revenue(); revenues.value = res.data.data } catch (e) { /* ignore */ } }
async function loadPlatforms() { try { const res = await publishApi.platforms(); publishPlatforms.value = res.data.data } catch (e) { /* ignore */ } }
async function loadDescribeStyles() { try { const res = await publishApi.describeStyles(); describeStyles.value = res.data.data } catch (e) { /* ignore */ } }
async function loadFeedPlatforms() { try { const res = await publishApi.getFeedPlatforms(); feedPlatforms.value = res.data.data } catch (e) { /* ignore */ } }
async function loadRevenueSummary() {
  try {
    const res = await publishApi.revenueSummary(revenuePeriod.value)
    revenueSummary.value = res.data.data
  } catch (e) { /* ignore */ }
}

// ─── Product CRUD ───
async function createProduct() {
  if (!productForm.value.title?.trim()) {
    ;(window as any).$toast?.show('请输入商品标题', 'warning')
    return
  }
  if (!productForm.value.price || productForm.value.price <= 0) {
    ;(window as any).$toast?.show('价格必须大于0', 'warning')
    return
  }
  try {
    await publishApi.createProduct(productForm.value)
    showProductModal.value = false
    productForm.value = { title: '', price: 0, category: '' }
    ;(window as any).$toast?.show('商品已创建', 'success')
    loadProducts()
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || '创建商品失败', 'error')
  }
}

async function exportCsv(id: string) {
  try {
    const res = await publishApi.exportCsv(id)
    ;(window as any).$toast?.show(`CSV 已导出: ${res.data.data.platform}`, 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || 'CSV导出失败', 'error')
  }
}

function publishProduct(id: string) { publishProductId.value = id; showPublishModal.value = true }

async function doPublish(id: string, platform: string) {
  try {
    showPublishModal.value = false
    const res = await publishApi.publish(id, platform)
    ;(window as any).$toast?.show(res.data.message, 'success')
  } catch (e: any) {
    showPublishModal.value = false
    ;(window as any).$toast?.show(e?.response?.data?.detail || '发布失败', 'error')
  }
}

// ─── P1.6.2: AI Description ───
function openDescribePanel(productId: string) {
  selectedProductId.value = productId
  activeTab.value = 'ai-desc'
}

async function generateDescription() {
  if (!selectedStyle.value || !selectedProductId.value) return
  try {
    ;(window as any).$toast?.show('AI 正在生成描述...', 'info')
    const res = await publishApi.generateDescription(selectedProductId.value, { style: selectedStyle.value })
    generatedResult.value = res.data.data
    ;(window as any).$toast?.show('描述已生成', 'success')
    loadProducts()
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || 'AI描述生成失败', 'error')
  }
}

// ─── P1.6.4: Verified Badge ───
function openBadgePanel(productId: string) {
  selectedProductId.value = productId
  activeTab.value = 'badge'
}

async function generateBadge() {
  if (!selectedProductId.value) return
  try {
    ;(window as any).$toast?.show('正在生成徽章...', 'info')
    const res = await publishApi.generateVerifiedBadge(selectedProductId.value)
    badgeResult.value = res.data.data
    embedCode.value = null
    ;(window as any).$toast?.show('徽章已生成', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || '徽章生成失败', 'error')
  }
}

function downloadBadgeSVG() {
  if (!badgeResult.value?.badge_svg) return
  const blob = new Blob([badgeResult.value.badge_svg], { type: 'image/svg+xml' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = 'oristudio-verified-badge.svg'; a.click()
  URL.revokeObjectURL(url)
}

function downloadBadgePNG() {
  if (!badgeResult.value?.badge_png_b64) return
  const a = document.createElement('a'); a.href = badgeResult.value.badge_png_b64; a.download = 'oristudio-verified-badge.png'; a.click()
}

async function loadEmbedCode() {
  if (!selectedProductId.value) return
  try {
    const res = await publishApi.getVerifiedEmbed(selectedProductId.value)
    embedCode.value = res.data.data
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || '加载嵌入代码失败', 'error')
  }
}

// ─── P1.6.8: Feed Export ───
async function exportFeed() {
  try {
    ;(window as any).$toast?.show('正在导出 Feed...', 'info')
    const res = await publishApi.exportFeed(feedPlatform.value, feedCategory.value || undefined)
    feedResult.value = res.data.data
    ;(window as any).$toast?.show('Feed 导出完成', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || 'Feed导出失败', 'error')
  }
}

function downloadFeed() {
  if (!feedResult.value) return
  const blob = new Blob([JSON.stringify(feedResult.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = `oristudio-feed-${feedPlatform.value}.json`; a.click()
  URL.revokeObjectURL(url)
}

// ─── Revenue ───
async function addRevenue() {
  if (!revenueForm.value.platform?.trim()) {
    ;(window as any).$toast?.show('请输入平台名称', 'warning')
    return
  }
  if (!revenueForm.value.amount || revenueForm.value.amount <= 0) {
    ;(window as any).$toast?.show('金额必须大于0', 'warning')
    return
  }
  try {
    await publishApi.addRevenue(revenueForm.value)
    showRevenueModal.value = false
    revenueForm.value = { platform: '', amount: 0, order_count: 1, date: new Date().toISOString().slice(0, 10) }
    ;(window as any).$toast?.show('收入已记录', 'success')
    loadRevenue()
    loadRevenueSummary()
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || '记录收入失败', 'error')
  }
}

function onFileSelected(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) selectedFile.value = target.files[0]
}

async function importCsv() {
  if (!selectedFile.value) return
  try {
    ;(window as any).$toast?.show('正在导入...', 'info')
    const res = await publishApi.importRevenue(selectedFile.value)
    importResult.value = res.data.data
    ;(window as any).$toast?.show(`已导入 ${res.data.data.imported} 条记录`, 'success')
    loadRevenue()
    loadRevenueSummary()
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || 'CSV导入失败', 'error')
  }
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).then(() => {
    ;(window as any).$toast?.show('已复制到剪贴板', 'success')
  }).catch(() => {
    ;(window as any).$toast?.show('复制失败', 'error')
  })
}

onMounted(async () => {
  if (appStore.workCount > 0) {
    hasWorks.value = true
    checking.value = false
  } else {
    try {
      const res = await worksApi.list({ page_size: 1 })
      hasWorks.value = (res.data.data?.items?.length || res.data.data?.length || 0) > 0
    } catch {
      hasWorks.value = false
    } finally {
      checking.value = false
    }
  }
  loadProducts(); loadRevenue(); loadPlatforms()
  loadDescribeStyles(); loadFeedPlatforms(); loadRevenueSummary()
  loadSchedules(); loadAnalytics()
})

watch(() => appStore.workCount, (val) => {
  hasWorks.value = val > 0
})

// ─── Schedule (P2) ───
async function loadSchedules() {
  try { const res = await publishApi.listSchedules(); schedules.value = res.data.data || [] } catch { /* ignore */ }
}

async function createSchedule() {
  if (!scheduleForm.value.platform?.trim()) {
    ;(window as any).$toast?.show('请输入平台名称', 'warning')
    return
  }
  if (!scheduleForm.value.scheduled_time) {
    ;(window as any).$toast?.show('请选择排期时间', 'warning')
    return
  }
  try {
    await publishApi.createSchedule(scheduleForm.value)
    showScheduleModal.value = false
    scheduleForm.value = { product_id: '', platform: '', scheduled_time: '', content_preview: '' }
    ;(window as any).$toast?.show('排期已创建', 'success')
    loadSchedules()
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || '创建排期失败', 'error')
  }
}

async function cancelSchedule(id: string) {
  try {
    await publishApi.deleteSchedule(id)
    ;(window as any).$toast?.show('排期已取消', 'success')
    loadSchedules()
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || '取消排期失败', 'error')
  }
}

// ─── Analytics (P2) ───
async function loadAnalytics() {
  try { const res = await publishApi.listAnalytics(); analyticsData.value = res.data.data || [] } catch { /* ignore */ }
}

async function addAnalytics() {
  if (!analyticsForm.value.platform?.trim()) {
    ;(window as any).$toast?.show('请输入平台名称', 'warning')
    return
  }
  if (!analyticsForm.value.date) {
    ;(window as any).$toast?.show('请选择日期', 'warning')
    return
  }
  try {
    await publishApi.addAnalytics(analyticsForm.value)
    showAnalyticsModal.value = false
    analyticsForm.value = { platform: '', views: 0, likes: 0, comments: 0, shares: 0, saves: 0, date: new Date().toISOString().slice(0, 10), notes: '' }
    ;(window as any).$toast?.show('影响力数据已录入', 'success')
    loadAnalytics()
  } catch (e: any) {
    ;(window as any).$toast?.show(e?.response?.data?.detail || '录入失败', 'error')
  }
}
</script>

<style scoped>
.publish-view { display:flex; flex-direction:column; gap:20px; }
.cat-tabs { display:flex; gap:8px; flex-wrap:wrap; }
.cat-tab { padding:8px 18px; border-radius:100px; font-size:.84rem; font-weight:600; cursor:pointer; border:1px solid var(--border); background:var(--surface); color:var(--muted); font-family:var(--font-body); transition:all .2s; }
.cat-tab.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.actions-bar { display:flex; justify-content:flex-end; gap:8px; align-items:center; }
.panel-header { margin-bottom:16px; }
.panel-header h3 { margin:0; font-size:1.1rem; }
.panel-subtitle { margin:4px 0 0; font-size:.82rem; color:var(--muted); }

/* Product Grid */
.product-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:16px; }
.product-card { padding:20px; display:flex; flex-direction:column; gap:10px; }
.product-header { display:flex; justify-content:space-between; align-items:center; }
.product-header h3 { margin:0; font-size:1rem; }
.product-price { font-weight:700; color:var(--accent); font-size:1.1rem; }
.product-desc { font-size:.82rem; color:var(--muted); line-height:1.5; overflow:hidden; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; }
.product-meta { display:flex; gap:12px; font-size:.75rem; color:var(--muted); }
.product-actions { display:flex; gap:8px; flex-wrap:wrap; }
.btn-sm { padding:6px 12px; font-size:.78rem; }

/* AI Description Style Cards (P1.6.2) */
.style-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:12px; margin-bottom:16px; }
.style-card { padding:16px; cursor:pointer; transition:all .2s; text-align:center; }
.style-card:hover { transform:translateY(-2px); box-shadow:0 4px 16px oklch(0 0 0 / .08); }
.style-card.selected { border-color:var(--accent); box-shadow:0 0 0 2px oklch(56% 0.12 170 / .2); }
.style-icon { font-size:2rem; margin-bottom:8px; }
.style-name { font-weight:700; font-size:.9rem; margin-bottom:4px; }
.style-desc { font-size:.75rem; color:var(--muted); line-height:1.4; }
.form-row { margin-bottom:12px; }
.form-row label { display:block; font-size:.82rem; font-weight:600; color:var(--muted); margin-bottom:4px; }
.form-select { width:100%; padding:10px 14px; border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.88rem; background:var(--surface); color:var(--fg); }
.form-select-sm { width:auto !important; padding:6px 10px; font-size:.8rem; }

/* Result */
.result-card { margin-top:16px; padding:20px; }
.result-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.result-style { font-weight:700; font-size:.9rem; }
.result-source { font-size:.75rem; padding:2px 8px; border-radius:100px; }
.result-source.ollama { background:oklch(56% 0.12 170 / .1); color:oklch(56% 0.12 170); }
.result-source.template { background:oklch(70% 0.02 90 / .15); color:oklch(50% 0.05 90); }
.result-content { white-space:pre-wrap; font-size:.84rem; line-height:1.6; background:var(--surface); padding:16px; border-radius:var(--radius-sm); border:1px solid var(--border); max-height:400px; overflow-y:auto; font-family:var(--font-body); }
.result-actions { margin-top:12px; display:flex; gap:8px; }

/* Badge Preview */
.badge-result-card { margin-top:16px; padding:20px; }
.badge-preview { display:flex; justify-content:center; margin-bottom:16px; padding:16px; background:var(--surface); border-radius:var(--radius-sm); border:1px solid var(--border); overflow-x:auto; }
.badge-meta { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px; }
.meta-item { display:flex; flex-direction:column; gap:4px; }
.meta-label { font-size:.75rem; font-weight:600; color:var(--muted); }
.meta-value { font-size:.78rem; font-family:monospace; word-break:break-all; }
.badge-download-options { margin-bottom:16px; }
.badge-download-options h4 { font-size:.85rem; margin:0 0 8px; }
.btn-group { display:flex; gap:8px; flex-wrap:wrap; }
.embed-code-block { margin-top:12px; padding:16px; }
.embed-code-block h4 { font-size:.85rem; margin:0 0 8px; }
.embed-code { font-size:.75rem; max-height:200px; overflow-y:auto; background:var(--surface); padding:12px; border-radius:var(--radius-sm); border:1px solid var(--border); font-family:monospace; white-space:pre-wrap; }

/* Feed Export */
.feed-options { padding:20px; display:flex; flex-direction:column; gap:16px; }
.platform-grid { display:flex; gap:8px; flex-wrap:wrap; }
.badge-planned { font-size:.7rem; background:var(--border); padding:1px 6px; border-radius:100px; margin-left:4px; }
.feed-result { margin-top:16px; padding:20px; }
.feed-meta { display:flex; gap:16px; margin-bottom:12px; font-size:.82rem; }
.feed-actions { display:flex; gap:8px; margin-bottom:12px; }
.feed-preview { font-size:.75rem; max-height:400px; overflow-y:auto; background:var(--surface); padding:12px; border-radius:var(--radius-sm); border:1px solid var(--border); font-family:monospace; white-space:pre-wrap; }

/* Revenue */
.revenue-summary { padding:20px; display:grid; grid-template-columns:repeat(4,1fr); gap:16px; text-align:center; }
@media (max-width:768px) { .revenue-summary { grid-template-columns:repeat(2,1fr); } }
.summary-label { font-size:.78rem; color:var(--muted); }
.summary-value { font-size:1.5rem; font-weight:700; font-family:var(--font-display); }
.revenue-list { display:flex; flex-direction:column; gap:4px; margin-top:16px; }
.revenue-row { display:grid; grid-template-columns:2fr 1.5fr 1fr 1fr; gap:8px; padding:10px 16px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.85rem; align-items:center; }
.revenue-date { font-size:.75rem; color:var(--muted); }

/* Platform Breakdown Bars */
.platform-breakdown { display:flex; flex-direction:column; gap:10px; }
.platform-bar-row { display:flex; align-items:center; gap:10px; }
.platform-name { width:80px; font-size:.82rem; font-weight:600; text-align:right; }
.platform-bar-track { flex:1; height:20px; background:var(--surface); border-radius:10px; overflow:hidden; }
.platform-bar { height:100%; background:linear-gradient(90deg, oklch(56% 0.12 170), oklch(62% 0.16 260)); border-radius:10px; min-width:4px; transition:width .3s; }
.platform-amount { width:80px; font-size:.82rem; font-weight:600; color:var(--accent); }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; max-height:90vh; overflow-y:auto; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; }
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group label { font-size:.82rem; font-weight:600; color:var(--muted); }
.form-input { padding:10px 14px; border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.88rem; font-family:var(--font-body); color:var(--fg); background:var(--surface); outline:none; }
.form-input:focus { border-color:var(--accent); box-shadow:0 0 0 3px oklch(56% 0.12 170 / .1); }
.platform-list { display:flex; flex-direction:column; gap:4px; }

/* Schedule (P2) */
.schedule-list { display:flex; flex-direction:column; gap:8px; }
.schedule-row { display:flex; align-items:center; gap:16px; padding:14px 16px; }
.schedule-info { display:flex; flex-direction:column; gap:2px; flex:1; }
.schedule-info strong { font-size:.9rem; }
.schedule-time { font-size:.78rem; color:var(--muted); }
.status-badge { font-size:.72rem; padding:2px 8px; border-radius:100px; font-weight:600; }
.status-badge.scheduled { background:oklch(70% 0.02 90 / .15); color:oklch(50% 0.05 90); }
.status-badge.executing { background:oklch(70% 0.12 260 / .1); color:oklch(56% 0.12 260); }
.status-badge.succeeded { background:oklch(62% 0.16 170 / .1); color:oklch(56% 0.12 170); }
.status-badge.failed { background:oklch(62% 0.2 25 / .1); color:oklch(56% 0.2 25); }
.status-badge.cancelled { background:var(--border); color:var(--muted); }

/* Analytics (P2) */
.analytics-summary { padding:20px; display:grid; grid-template-columns:repeat(4,1fr); gap:16px; text-align:center; }
@media (max-width:768px) { .analytics-summary { grid-template-columns:repeat(2,1fr); } }
.analytics-list { display:flex; flex-direction:column; gap:4px; margin-top:16px; }
.analytics-row { display:grid; grid-template-columns:2fr 1.5fr 1fr 1fr 1fr; gap:8px; padding:10px 16px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.85rem; align-items:center; }
.analytics-date { font-size:.75rem; color:var(--muted); }
</style>
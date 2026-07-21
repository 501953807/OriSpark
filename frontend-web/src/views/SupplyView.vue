<template>
  <div class="supply-view">
    <!-- Loading state -->
    <div v-if="checking" class="supply-loading" style="text-align:center;padding:60px;color:var(--muted)">加载中...</div>

    <!-- 前置校验: 无作品时拦截 -->
    <EmptyState
      v-else-if="!hasWorks"
      icon="💰"
      title="暂无已确权作品"
      description="商业转化需要先上传作品并完成 IP 登记确权"
      :show-action="true"
      :primary-action="{ label: '前往上传作品', onClick: goToWorks }"
      :tips="['上传作品 → 完成 IP 登记 → 开启商业转化']"
    />

    <template v-else>
    <div class="cat-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['cat-tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 1: 变现仪表盘 (P1.5.11)
         ═══════════════════════════════════════════════════════════ -->

    <!-- ═══════════════════════════════════════════════════════════
         Tab 2: 设计→产品转化器 (P1.5.5-P1.5.8)
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'designer'" class="animate-fade-in">
      <!-- Step indicator -->
      <div class="wizard-steps">
        <div
          v-for="(step, i) in wizardSteps"
          :key="i"
          :class="['wizard-step', { active: wizardStep === i, done: wizardStep > i }]"
          @click="wizardStep = i"
        >
          <span class="step-num">{{ wizardStep > i ? '✓' : i + 1 }}</span>
          <span class="step-label">{{ step }}</span>
        </div>
      </div>

      <!-- Step 1: Select Design (from works) -->
      <div v-if="wizardStep === 0" class="wizard-panel card">
        <h3>Step 1: 选择设计稿</h3>
        <p class="wizard-hint">从你的作品库中选择要变现的设计</p>
        <div v-if="works.length === 0" class="empty-hint">暂无作品，请先上传作品</div>
        <div v-else class="works-grid">
          <div
            v-for="w in works"
            :key="w.id"
            :class="['work-card', { selected: designer.work_id === w.id }]"
            @click="selectWork(w)"
          >
            <div class="work-thumb" v-if="w.thumbnail_url">
              <img :src="w.thumbnail_url" alt="" />
            </div>
            <div class="work-thumb-placeholder" v-else>🎨</div>
            <div class="work-info">
              <strong>{{ w.title }}</strong>
              <span class="work-meta">{{ w.width }}x{{ w.height }}px {{ w.dpi ? w.dpi + 'DPI' : '' }}</span>
            </div>
          </div>
        </div>
        <div class="wizard-actions" v-if="designer.work_id">
          <button class="btn btn-primary" @click="wizardStep = 1">下一步: 选择变现路径 →</button>
        </div>
      </div>

      <!-- Step 2: Choose Monetization Path -->
      <div v-if="wizardStep === 1" class="wizard-panel card">
        <h3>Step 2: 选择变现路径</h3>
        <p class="wizard-hint">选择适合你的变现方式</p>
        <div class="path-cards">
          <div
            v-for="p in monetizationPaths"
            :key="p.id"
            :class="['path-card', { selected: designer.monetization_path === p.id }]"
            @click="designer.monetization_path = p.id"
          >
            <div class="path-card-icon">{{ p.icon }}</div>
            <div class="path-card-name">{{ p.name_zh }}</div>
            <div class="path-card-desc">{{ p.desc }}</div>
            <div class="path-card-tags">
              <span v-for="pro in p.pros" :key="pro" class="tag tag-green">{{ pro }}</span>
            </div>
          </div>
        </div>
        <div class="wizard-actions" v-if="designer.monetization_path">
          <button class="btn btn-secondary" @click="wizardStep = 0">← 上一步</button>
          <button class="btn btn-primary" @click="wizardStep = 2">下一步: 选择产品品类 →</button>
        </div>
      </div>

      <!-- Step 3: Choose Product Category (with material filter) -->
      <div v-if="wizardStep === 2" class="wizard-panel card">
        <h3>Step 3: 选择产品品类</h3>
        <p class="wizard-hint">按材质分组选择目标产品</p>

        <!-- Material tabs -->
        <div class="cat-tabs" style="margin-bottom:16px">
          <button
            v-for="m in materialCategories"
            :key="m.id"
            :class="['cat-tab', { active: selectedMaterial === m.id }]"
            @click="selectedMaterial = m.id"
          >
            {{ m.icon }} {{ m.label_zh }}
          </button>
        </div>

        <!-- Filter by monetization path -->
        <div v-if="selectedMaterial" class="product-grid">
          <div
            v-for="c in filteredCategories"
            :key="c.id"
            :class="['product-card', { selected: designer.product_category_id === c.id }]"
            @click="designer.product_category_id = c.id; designer.product_template = c"
          >
            <div class="product-card-name">{{ c.name_zh }}</div>
            <div class="product-card-en">{{ c.name_en }}</div>
            <div class="product-card-price">¥{{ c.suggested_price_cny }}</div>
            <div class="product-card-margin">毛利率 ~{{ c.margin_pct }}%</div>
            <div class="product-card-tags">
              <span v-for="p in c.recommended_pod_platforms?.slice(0, 3)" :key="p" class="tag">{{ p }}</span>
            </div>
          </div>
        </div>

        <div class="wizard-actions" v-if="designer.product_category_id">
          <button class="btn btn-secondary" @click="wizardStep = 1">← 上一步</button>
          <button class="btn btn-primary" @click="wizardStep = 3; runSpecCheck()">下一步: 规格适配 →</button>
        </div>
      </div>

      <!-- Step 4: Spec Adaptation Preview (P1.5.3-P1.5.4) -->
      <div v-if="wizardStep === 3" class="wizard-panel card">
        <h3>Step 4: 规格适配预览</h3>
        <p class="wizard-hint">校验设计稿是否满足目标产品规格</p>

        <div v-if="specResult" class="spec-result">
          <div :class="['spec-status-banner', specResult.overall_status]">
            <span v-if="specResult.overall_status === 'pass'">✅ 规格校验通过</span>
            <span v-else-if="specResult.overall_status === 'warning'">⚠️ 存在警告 ({{
              specResult.warning_count }} 项)</span>
            <span v-else>❌ 存在错误 ({{ specResult.error_count }} 项)</span>
          </div>
          <div class="spec-checks">
            <div v-for="c in specResult.checks" :key="c.check" :class="['spec-check', c.status]">
              <span class="spec-check-icon">{{ c.status === 'pass' ? '✅' : c.status === 'warning' ? '⚠️' : '❌' }}</span>
              <div class="spec-check-body">
                <span class="spec-check-msg">{{ c.message }}</span>
                <span class="spec-check-suggestion" v-if="c.suggestion">{{ c.suggestion }}</span>
              </div>
            </div>
          </div>

          <!-- Compatible products recommendation when there are errors -->
          <SpecRemediationPanel
            v-if="specResult.error_count > 0"
            :errors="specResult.checks.filter((c: any) => c.status === 'error')"
            :compatible="compatibleTemplates"
            :suggestions="remediationSuggestions"
            @select-template="handleCompatibleSelect"
            @override="specOverrideConfirmed = true"
          />
        </div>
        <div v-else class="spec-loading">校验中...</div>

        <div class="wizard-actions">
          <button class="btn btn-secondary" @click="wizardStep = 2">← 上一步</button>
          <button
            class="btn btn-primary"
            @click="wizardStep = 4"
            :disabled="needsErrorBlock && !specOverrideConfirmed"
            :title="needsErrorBlock ? '存在规格错误，请修复或勾选覆盖确认' : ''"
          >
            下一步: 定价与发布 →
          </button>
        </div>
      </div>

      <!-- Step 5: Effect Preview (Canvas + Printful) -->
      <div v-if="wizardStep === 4" class="wizard-panel card">
        <h3>Step 5: 效果预览</h3>
        <p class="wizard-hint">预览设计稿在产品上的效果</p>

        <!-- Preview mode toggle -->
        <div class="preview-toggle">
          <button :class="['mode-btn', { active: previewMode === 'canvas' }]" @click="previewMode = 'canvas'">Canvas 平面预览</button>
          <button :class="['mode-btn', { active: previewMode === 'printful' }]" @click="previewMode = 'printful'">Printful 照片级</button>
          <button :class="['mode-btn', { active: previewMode === 'ai' }]" @click="previewMode = 'ai'">AI 增强</button>
        </div>

        <!-- Canvas preview -->
        <div v-if="previewMode === 'canvas'" class="canvas-preview-area">
          <div class="preview-canvas-placeholder">
            <span class="placeholder-icon">🎨</span>
            <p>Canvas 平面预览</p>
            <span class="hint-text">拖拽调整位置 / 滚轮缩放</span>
          </div>
          <div class="preview-controls">
            <button class="ctrl-btn" @click="zoomIn">➕ 放大</button>
            <button class="ctrl-btn" @click="zoomOut">➖ 缩小</button>
            <button class="ctrl-btn" @click="resetZoom">↺ 重置</button>
            <select v-model="previewColor" class="color-select">
              <option value="white">白色底</option>
              <option value="black">黑色底</option>
              <option value="gray">灰色底</option>
            </select>
          </div>
        </div>

        <!-- Printful preview -->
        <div v-if="previewMode === 'printful'" class="printful-preview-area">
          <div v-if="mockupLoading" class="loading-spinner">
            <span>正在生成照片级预览...</span>
          </div>
          <div v-else-if="mockupUrl" class="preview-image">
            <img :src="mockupUrl" alt="Printful Mockup" />
          </div>
          <div v-else class="preview-canvas-placeholder">
            <span class="placeholder-icon">📷</span>
            <p>Printful Mockup 预览</p>
            <span class="hint-text">需要配置 Printful API Key</span>
          </div>
          <button class="btn btn-sm btn-secondary" @click="generateMockup" :disabled="mockupLoading">
            {{ mockupLoading ? '生成中...' : '生成照片级预览' }}
          </button>
        </div>

        <!-- AI preview -->
        <div v-if="previewMode === 'ai'" class="ai-preview-area">
          <div class="preview-canvas-placeholder">
            <span class="placeholder-icon">🤖</span>
            <p>AI 增强预览</p>
            <span class="hint-text">通过 Ollama/ComfyUI 生成场景化预览</span>
          </div>
          <div class="ai-style-selector">
            <label>风格:</label>
            <select v-model="aiStyle" class="form-input" style="width:auto">
              <option value="realistic">写实</option>
              <option value="minimal">极简</option>
              <option value="cartoon">卡通</option>
              <option value="studio">工作室</option>
            </select>
          </div>
          <button class="btn btn-sm btn-secondary" @click="generateAiMockup" :disabled="aiLoading">
            {{ aiLoading ? '生成中...' : 'AI 生成预览' }}
          </button>
        </div>

        <div class="wizard-actions">
          <button class="btn btn-secondary" @click="wizardStep = 3">← 上一步</button>
          <button class="btn btn-primary" @click="wizardStep = 5">下一步: 智能定价 →</button>
        </div>
      </div>

      <!-- Step 6: Intelligent Pricing -->
      <div v-if="wizardStep === 5" class="wizard-panel card">
        <h3>Step 6: 智能定价</h3>
        <p class="wizard-hint">基于成本、竞品分析和作品价值智能定价</p>

        <div class="pricing-card">
          <h4>成本构成</h4>
          <div class="cost-breakdown">
            <div class="cost-row">
              <span>品类基础成本</span>
              <span>¥{{ designer.cost }}</span>
            </div>
            <div class="cost-row">
              <span>平台抽成 (估算 10%)</span>
              <span>¥{{ platformFee }}</span>
            </div>
            <div class="cost-row">
              <span>物流成本</span>
              <span>¥{{ shippingCost }}</span>
            </div>
            <div class="cost-row total">
              <span>总成本</span>
              <span>¥{{ totalCost }}</span>
            </div>
          </div>

          <h4 style="margin-top:16px">竞品分析</h4>
          <div class="competitor-range">
            <span>同类产品价格区间: ¥{{ competitorMin }} - ¥{{ competitorMax }}</span>
            <span class="price-tag" :class="pricePosition">
              {{ pricePositionLabel }}
            </span>
          </div>

          <h4 style="margin-top:16px">AI 建议售价</h4>
          <div class="ai-price-suggestion">
            <span class="ai-price-min">¥{{ aiSuggestedMin }}</span>
            <span class="ai-price-sep">—</span>
            <span class="ai-price-max">¥{{ aiSuggestedMax }}</span>
          </div>

          <h4 style="margin-top:16px">自定义定价</h4>
          <div class="form-row">
            <div class="form-group">
              <label>售价 (¥)</label>
              <input v-model.number="designer.price" type="number" class="form-input" @input="updateProfit" />
            </div>
            <div class="form-group">
              <label>利润率</label>
              <div class="margin-display">{{ profitMargin }}%</div>
            </div>
          </div>
          <div class="profit-display">
            预估利润: ¥{{ calcFinalProfit }} / 件
          </div>
        </div>

        <div class="wizard-actions">
          <button class="btn btn-secondary" @click="wizardStep = 4">← 上一步</button>
          <button class="btn btn-primary" @click="wizardStep = 6">下一步: 创建商品 →</button>
        </div>
      </div>

      <!-- Step 7: Create Product -->
      <div v-if="wizardStep === 6" class="wizard-panel card">
        <h3>Step 7: 创建商品</h3>

        <div class="form-group">
          <label>商品标题</label>
          <input v-model="designer.product_title" class="form-input" placeholder="输入商品名称" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="designer.description" class="form-input" rows="3" placeholder="商品描述"></textarea>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>售价 (¥)</label>
            <input v-model.number="designer.price" type="number" class="form-input" />
          </div>
          <div class="form-group">
            <label>成本 (¥)</label>
            <input v-model.number="designer.cost" type="number" class="form-input" />
          </div>
        </div>
        <div class="form-group">
          <label>目标平台</label>
          <select v-model="designer.platform" class="form-input">
            <option value="">-- 选择平台 --</option>
            <option v-for="p in platforms" :key="p.id" :value="p.id">{{ p.name }} ({{ p.region }})</option>
          </select>
        </div>

        <!-- Summary preview -->
        <div class="summary-preview">
          <h4>创建摘要</h4>
          <dl>
            <dt>商品</dt><dd>{{ designer.product_title || '未命名' }}</dd>
            <dt>品类</dt><dd>{{ designer.product_template?.name_zh || '-' }}</dd>
            <dt>变现路径</dt><dd>{{ getPathLabel(designer.monetization_path) }}</dd>
            <dt>价格</dt><dd>¥{{ designer.price }}</dd>
            <dt>利润</dt><dd class="profit">¥{{ Math.max(0, designer.price - designer.cost) }}</dd>
          </dl>
        </div>

        <div class="wizard-actions">
          <button class="btn btn-secondary" @click="wizardStep = 5">← 上一步</button>
          <button class="btn btn-primary" @click="publishProduct" :disabled="publishing">
            {{ publishing ? '创建中...' : '🚀 创建商品' }}
          </button>
        </div>
      </div>

      <!-- Step 5: Pricing & Publish (legacy, removed) -->
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 3: Products (P1.5.2)
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'products'" class="animate-fade-in">
      <div class="filter-bar">
        <select v-model="productFilter.monetization_path" class="form-input" style="width:auto" @change="loadProducts">
          <option value="">全部路径</option>
          <option v-for="p in monetizationPaths" :key="p.id" :value="p.id">{{ p.name_zh }}</option>
        </select>
        <select v-model="productFilter.material_category" class="form-input" style="width:auto" @change="loadProducts">
          <option value="">全部材质</option>
          <option v-for="m in materialCategories" :key="m.id" :value="m.id">{{ m.label_zh }}</option>
        </select>
      </div>
      <div v-if="!products.length" class="empty-hint">暂无产品，使用"设计→产品"转化器创建</div>
      <div v-else class="product-list">
        <div v-for="p in products" :key="p.id" class="product-row card">
          <div class="product-row-header">
            <strong>{{ p.title }}</strong>
            <span :class="['tag', 'tag-' + (p.monetization_path || 'none')]">{{ getPathLabel(p.monetization_path) }}</span>
          </div>
          <div class="product-row-body">
            <span>¥{{ p.price }}</span>
            <span v-if="p.cost">成本 ¥{{ p.cost }}</span>
            <span v-if="p.platform">{{ p.platform }}</span>
            <span>{{ p.material_category || '-' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 4: Crowdfunding Campaigns (Enhanced P2.5.3-P2.5.4)
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'campaigns'" class="animate-fade-in">
      <div class="actions-bar">
        <button class="btn btn-primary" @click="showCampaignModal = true">+ 新众筹项目</button>
        <button class="btn btn-secondary" @click="showGoalCalc = !showGoalCalc">🧮 目标金额计算器</button>
        <button class="btn btn-secondary" @click="loadRewardTemplates">📋 奖励模板</button>
      </div>

      <!-- Funding Goal Calculator -->
      <div v-if="showGoalCalc" class="card section-card" style="margin-bottom:14px">
        <h3 class="section-title">众筹目标金额计算器</h3>
        <div class="form-group"><label>档位 (每行: 名称,价格,预估支持人数)</label></div>
        <div v-for="(t, i) in goalCalcForm.tiers" :key="i" class="goal-tier-row">
          <input v-model="t.name" class="form-input" placeholder="档位名称" style="flex:1" />
          <input v-model.number="t.price" type="number" class="form-input" placeholder="单价" style="width:100px" />
          <input v-model.number="t.estimated_backers" type="number" class="form-input" placeholder="预估人数" style="width:100px" />
          <button class="btn btn-sm btn-secondary" @click="goalCalcForm.tiers.splice(i, 1)" v-if="goalCalcForm.tiers.length > 1">✕</button>
        </div>
        <button class="btn btn-sm btn-secondary" style="margin-top:8px" @click="goalCalcForm.tiers.push({name:'',price:0,estimated_backers:0})">+ 添加档位</button>
        <div class="form-row" style="margin-top:12px">
          <div class="form-group"><label>制造成本 ¥</label><input v-model.number="goalCalcForm.manufacturing_cost" type="number" class="form-input" /></div>
          <div class="form-group"><label>物流成本 ¥</label><input v-model.number="goalCalcForm.shipping_cost" type="number" class="form-input" /></div>
        </div>
        <div class="wizard-actions" style="justify-content:flex-start;margin-top:12px">
          <button class="btn btn-primary" @click="calculateGoal">计算建议目标</button>
        </div>
        <div v-if="goalCalcResult" class="spec-result" style="margin-top:12px">
          <div class="spec-status-banner" :class="goalCalcResult.suggested_goal > 0 ? 'pass' : 'warning'">
            建议目标: ¥{{ fmtMoney(goalCalcResult.suggested_goal) }}
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:.82rem">
            <div>预估总收入: ¥{{ fmtMoney(goalCalcResult.total_estimated_revenue) }}</div>
            <div>平台费: ¥{{ fmtMoney(goalCalcResult.platform_fee) }}</div>
            <div>净利润: ¥{{ fmtMoney(goalCalcResult.profit_at_suggested_goal) }}</div>
            <div>盈亏平衡: ¥{{ fmtMoney(goalCalcResult.break_even) }}</div>
          </div>
        </div>
      </div>

      <!-- Reward Templates -->
      <div v-if="showRewardTemplates && rewardTemplates.length" class="card section-card" style="margin-bottom:14px">
        <h3 class="section-title">奖励档位模板</h3>
        <div class="template-grid">
          <div v-for="rt in rewardTemplates" :key="rt.id" class="template-card" @click="useRewardTemplate(rt)">
            <h4>{{ rt.name_zh }}</h4>
            <p class="template-desc">{{ rt.description }}</p>
            <div class="template-tiers">
              <div v-for="t in rt.tiers" :key="t.name" class="template-tier">
                <strong>{{ t.name }}</strong>
                <span>¥{{ t.price_suggestions?.min || 0 }}-{{ t.price_suggestions?.max || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!campaigns.length" class="empty-hint">暂无众筹项目</div>
      <div v-else class="campaign-list">
        <div v-for="c in campaigns" :key="c.id" class="campaign-card card">
          <div class="campaign-header">
            <strong>{{ c.title }}</strong>
            <div style="display:flex;gap:8px;align-items:center">
              <span class="tag">{{ c.platform }}</span>
              <button class="btn btn-sm btn-secondary" @click="exportCampaignReport(c.id)">📄 报表</button>
            </div>
          </div>
          <div class="campaign-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: Math.min(100, c.progress_pct) + '%' }"></div>
            </div>
            <span>{{ c.progress_pct }}%</span>
          </div>
          <div class="campaign-stats">
            <span>💰 ¥{{ fmtMoney(c.raised_amount) }} / ¥{{ fmtMoney(c.goal_amount) }}</span>
            <span>👥 {{ c.backer_count }} 支持者</span>
          </div>
          <!-- Reward Tiers Preview -->
          <div v-if="c.reward_tiers?.length" class="campaign-tier-preview" style="margin-top:8px">
            <div v-for="t in c.reward_tiers" :key="t.name" class="tier-mini">
              <span>{{ t.name }}</span>
              <span>¥{{ t.price }} ({{ t.sold || 0 }}/{{ t.limit || '∞' }})</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Campaign Report Modal -->
      <div v-if="showReportModal" class="modal-overlay" @click.self="showReportModal = false">
        <div class="modal-card animate-scale-in" style="max-width:600px">
          <div class="modal-header"><h3>众筹项目报表</h3><button class="modal-close-btn" @click="showReportModal = false">&times;</button></div>
          <div v-if="campaignReport">
            <h4>{{ campaignReport.campaign?.title }}</h4>
            <div class="report-section">
              <strong>资金状态:</strong>
              ¥{{ fmtMoney(campaignReport.funding?.raised_amount) }} / ¥{{ fmtMoney(campaignReport.funding?.goal_amount) }}
              ({{ campaignReport.funding?.funding_pct }}%)
            </div>
            <div class="report-section">
              <strong>支持者:</strong> {{ campaignReport.funding?.backer_count }} 人
            </div>
            <div class="report-section">
              <strong>档位收益:</strong>
              <div v-for="t in campaignReport.reward_tiers" :key="t.name" class="report-tier-row">
                <span>{{ t.name }}: ¥{{ t.price }}</span>
                <span>{{ t.sold }}/{{ t.limit || '∞' }} 份</span>
                <span>¥{{ fmtMoney(t.revenue) }}</span>
                <span v-if="t.sold_out" class="tag tag-sm">售罄</span>
              </div>
            </div>
            <div class="report-section">
              <strong>订单状态:</strong>
              <div v-for="(count, status) in campaignReport.orders?.by_status" :key="status" class="report-tier-row">
                <span>{{ status }}</span>
                <span>{{ count }} 单</span>
              </div>
            </div>
            <div style="font-size:.7rem;color:var(--muted);margin-top:12px">
              导出时间: {{ campaignReport.export_time }}
            </div>
          </div>
          <div v-else class="empty-hint">加载中...</div>
        </div>
      </div>

      <!-- Campaign Modal (Enhanced) -->
      <div v-if="showCampaignModal" class="modal-overlay" @click.self="showCampaignModal = false">
        <div class="modal-card animate-scale-in" style="max-width:540px">
          <div class="modal-header"><h3>创建众筹项目</h3><button class="modal-close-btn" @click="showCampaignModal = false">&times;</button></div>
          <div class="form-group"><label>项目标题</label><input v-model="campaignForm.title" class="form-input" /></div>
          <div class="form-group"><label>平台</label>
            <select v-model="campaignForm.platform" class="form-input">
              <option value="modian">摩点</option>
              <option value="kickstarter">Kickstarter</option>
              <option value="indiegogo">Indiegogo</option>
              <option value="patreon">Patreon</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group"><label>目标金额 (¥)</label><input v-model.number="campaignForm.goal_amount" type="number" class="form-input" /></div>
          </div>
          <div class="form-group"><label>奖励档位</label></div>
          <div v-for="(t, i) in campaignForm.tiers" :key="i" class="goal-tier-row">
            <input v-model="t.name" class="form-input" placeholder="名称" style="flex:1" />
            <input v-model.number="t.price" type="number" class="form-input" placeholder="价格" style="width:80px" />
            <input v-model.number="t.limit" type="number" class="form-input" placeholder="限量" style="width:80px" />
            <button class="btn btn-sm btn-secondary" @click="campaignForm.tiers.splice(i, 1)">✕</button>
          </div>
          <button class="btn btn-sm btn-secondary" @click="campaignForm.tiers.push({name:'',price:0,limit:0})">+ 添加档位</button>
          <div class="form-group"><label>描述</label><textarea v-model="campaignForm.description" class="form-input" rows="3"></textarea></div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showCampaignModal = false">取消</button>
            <button class="btn btn-primary" @click="createCampaign">创建</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 5: IP Licenses (Enhanced P2.5.5-P2.5.6)
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'licenses'" class="animate-fade-in">
      <div class="actions-bar">
        <button class="btn btn-primary" @click="showLicenseModal = true">+ 创建授权</button>
      </div>
      <div v-if="!licenses.length" class="empty-hint">暂无授权记录</div>
      <div v-else class="license-list">
        <div v-for="l in licenses" :key="l.id" class="license-card card">
          <div class="license-header">
            <strong>{{ l.license_type }}</strong>
            <span class="tag" v-if="l.platform">{{ l.platform }}</span>
          </div>
          <div class="license-body">
            <span>¥{{ l.price }}</span>
            <span>销售 {{ l.sales_count }} 次</span>
            <span>总收入 ¥{{ l.total_revenue }}</span>
          </div>
          <div class="license-export" style="margin-top:8px;display:flex;gap:6px">
            <button class="btn btn-sm btn-secondary" @click="exportLicense(l.id, 'creative_fabrica')">CF</button>
            <button class="btn btn-sm btn-secondary" @click="exportLicense(l.id, 'creative_market')">CM</button>
            <button class="btn btn-sm btn-secondary" @click="exportLicense(l.id, 'gumroad')">Gumroad</button>
            <button class="btn btn-sm btn-secondary" @click="exportLicense(l.id, 'envato')">Envato</button>
          </div>
        </div>
      </div>

      <!-- License Export Result Modal -->
      <div v-if="showLicenseExportModal" class="modal-overlay" @click.self="showLicenseExportModal = false">
        <div class="modal-card animate-scale-in" style="max-width:600px">
          <div class="modal-header">
            <h3>授权导出 - {{ licenseExportResult?.format }}</h3>
            <button class="modal-close-btn" @click="showLicenseExportModal = false">&times;</button>
          </div>
          <pre class="result-pre">{{ JSON.stringify(licenseExportResult, null, 2) }}</pre>
        </div>
      </div>

      <!-- License Modal -->
      <div v-if="showLicenseModal" class="modal-overlay" @click.self="showLicenseModal = false">
        <div class="modal-card animate-scale-in" style="max-width:500px">
          <div class="modal-header"><h3>创建 IP 授权</h3><button class="modal-close-btn" @click="showLicenseModal = false">&times;</button></div>
          <div class="form-group"><label>授权类型</label>
            <select v-model="licenseForm.license_type" class="form-input">
              <option value="single_use">单次使用授权</option>
              <option value="multi_use">多次使用授权</option>
              <option value="commercial_extended">商业扩展授权</option>
              <option value="buyout">买断授权</option>
            </select>
          </div>
          <div class="form-group"><label>平台</label>
            <select v-model="licenseForm.platform" class="form-input">
              <option value="">-- 选择平台 --</option>
              <option value="creative_fabrica">Creative Fabrica</option>
              <option value="creative_market">Creative Market</option>
              <option value="envato">Envato</option>
              <option value="gumroad">Gumroad</option>
            </select>
          </div>
          <div class="form-group"><label>价格 (¥)</label><input v-model.number="licenseForm.price" type="number" class="form-input" /></div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showLicenseModal = false">取消</button>
            <button class="btn btn-primary" @click="createLicense">创建</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 6: POD Platform Publish (P2.5.1-P2.5.2, P2.5.13)
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'pod'" class="animate-fade-in">
      <DisclaimerBanner
        mode="banner"
        title="POD平台IP条款警告（声明 #4）"
        :messages="['上传设计稿到第三方POD平台可能涉及IP泄露风险。上传前请阅读平台服务条款中的知识产权部分。当前版本为POD渠道管理（手动上架+URL记录），不支持自动同步库存/订单/物流。']"
      />
      <!-- Platform selector -->
      <div class="cat-tabs" style="margin-bottom:16px">
        <button
          v-for="pp in podPlatforms"
          :key="pp.id"
          :class="['cat-tab', { active: selectedPodPlatform === pp.id }]"
          @click="selectPodPlatform(pp.id)"
        >
          {{ pp.name }}
        </button>
      </div>

      <!-- Platform detail -->
      <div v-if="selectedPodPlatform && podPlatformDetail" class="card section-card">
        <h3 class="section-title">{{ podPlatformDetail.name }} — 发布设计</h3>

        <!-- Global POD platforms (Printful/Redbubble) -->
        <div v-if="['printful', 'redbubble'].includes(selectedPodPlatform)">
          <div class="form-group">
            <label>商品标题</label>
            <input v-model="podForm.title" class="form-input" placeholder="商品名称" />
          </div>
          <div class="form-group">
            <label>品类</label>
            <input v-model="podForm.category" class="form-input" placeholder="t_shirt, mug, poster..." />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>售价</label>
              <input v-model.number="podForm.price" type="number" class="form-input" />
            </div>
            <div class="form-group">
              <label>设计文件路径</label>
              <input v-model="podForm.design_file_path" class="form-input" placeholder="/path/to/design.png" />
            </div>
          </div>

          <div class="wizard-actions" style="justify-content:flex-start">
            <button class="btn btn-primary" @click="publishToPod('publish')" :disabled="podPublishing">
              {{ podPublishing ? '发布中...' : '🚀 发布到 ' + podPlatformDetail.name }}
            </button>
            <button class="btn btn-secondary" @click="publishToPod('cost_estimate')" v-if="selectedPodPlatform === 'printful'">
              📊 运费估算
            </button>
            <button class="btn btn-secondary" @click="publishToPod('csv_template')" v-if="selectedPodPlatform === 'redbubble'">
              📄 生成CSV模板
            </button>
          </div>

          <div v-if="podResult" class="spec-result" style="margin-top:14px">
            <div class="spec-status-banner pass">发布结果</div>
            <pre class="result-pre">{{ JSON.stringify(podResult, null, 2) }}</pre>
          </div>
        </div>

        <!-- Chinese POD platforms -->
        <div v-else>
          <div class="platform-info-grid">
            <div class="info-block">
              <h4>平台信息</h4>
              <div v-for="(v, k) in podPlatformDetail.info" :key="k" class="info-row">
                <span class="info-key">{{ k }}</span>
                <span class="info-val">{{ Array.isArray(v) ? v.join(', ') : v }}</span>
              </div>
            </div>
            <div class="info-block">
              <h4>设计规格要求</h4>
              <div class="spec-requirements">
                <div class="spec-req" v-if="podPlatformDetail.specs.default_dpi">
                  <span>DPI:</span> <strong>{{ podPlatformDetail.specs.default_dpi }}</strong>
                </div>
                <div class="spec-req" v-if="podPlatformDetail.specs.accepted_formats">
                  <span>格式:</span> <strong>{{ podPlatformDetail.specs.accepted_formats.join(', ') }}</strong>
                </div>
                <div class="spec-req" v-if="podPlatformDetail.specs.color_mode">
                  <span>色彩模式:</span> <strong>{{ podPlatformDetail.specs.color_mode }}</strong>
                </div>
                <div class="spec-req" v-if="podPlatformDetail.specs.max_file_size_mb">
                  <span>文件上限:</span> <strong>{{ podPlatformDetail.specs.max_file_size_mb }}MB</strong>
                </div>
              </div>
            </div>
          </div>

          <h4 style="margin-top:16px">支持的品类</h4>
          <div class="pod-category-grid">
            <div v-for="(cat, key) in podPlatformDetail.categories" :key="key" class="pod-category-item">
              <span class="cat-name">{{ cat.name_zh }}</span>
              <span class="cat-price">¥{{ cat.base_price_cny }}+</span>
            </div>
          </div>

          <div v-if="podResult" class="spec-result" style="margin-top:14px">
            <div class="spec-status-banner pass">规格匹配结果</div>
            <pre class="result-pre">{{ JSON.stringify(podResult, null, 2) }}</pre>
          </div>

          <div class="wizard-actions">
            <button class="btn btn-primary" @click="publishToPod('publish')" :disabled="podPublishing">
              {{ podPublishing ? '检测中...' : '🔍 检测规格适配' }}
            </button>
          </div>
        </div>
      </div>
      <div v-else class="empty-hint">请选择一个POD平台</div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 9: AI Monetization Advisor (P2.5.11-P2.5.12)
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'advisor'" class="animate-fade-in">
      <!-- Aggregated Revenue -->
      <div class="card section-card">
        <h3 class="section-title">📊 聚合收入分析</h3>
        <div class="dashboard-stats" style="margin-bottom:14px">
          <div class="stat-card card">
            <div class="stat-icon">💰</div>
            <div class="stat-value">¥{{ fmtMoney(aggregatedRevenue.summary?.total_revenue || 0) }}</div>
            <div class="stat-label">总收入</div>
          </div>
          <div class="stat-card card">
            <div class="stat-icon">📦</div>
            <div class="stat-value">{{ aggregatedRevenue.summary?.total_orders || 0 }}</div>
            <div class="stat-label">总订单</div>
          </div>
          <div class="stat-card card">
            <div class="stat-icon">📅</div>
            <div class="stat-value">¥{{ fmtMoney(aggregatedRevenue.summary?.this_month || 0) }}</div>
            <div class="stat-label">本月收入</div>
          </div>
        </div>

        <!-- Revenue by platform -->
        <div v-if="aggregatedRevenue.by_platform?.length" style="margin-bottom:14px">
          <h4 style="margin-bottom:8px">按平台</h4>
          <div class="platform-rev-grid">
            <div v-for="r in aggregatedRevenue.by_platform" :key="r.platform" class="platform-rev-item">
              <span class="platform-name">{{ r.platform }}</span>
              <span class="platform-amount">¥{{ fmtMoney(r.amount) }}</span>
              <span class="platform-count">{{ r.count }} 单</span>
            </div>
          </div>
        </div>

        <!-- Monthly trends -->
        <div v-if="aggregatedRevenue.monthly_trends?.length" style="margin-bottom:14px">
          <h4 style="margin-bottom:8px">月度趋势</h4>
          <div class="monthly-trends">
            <div v-for="m in aggregatedRevenue.monthly_trends" :key="m.month" class="trend-bar-row">
              <span class="trend-month">{{ m.month }}</span>
              <div class="trend-bar">
                <div class="trend-fill" :style="{ width: getTrendWidth(m.revenue) + '%' }"></div>
              </div>
              <span class="trend-value">¥{{ fmtMoney(m.revenue) }}</span>
            </div>
          </div>
        </div>

        <!-- Top products -->
        <div v-if="aggregatedRevenue.top_products?.length">
          <h4 style="margin-bottom:8px">Top 产品</h4>
          <div class="top-products-list">
            <div v-for="tp in aggregatedRevenue.top_products" :key="tp.id" class="top-product-row">
              <span class="tp-name">{{ tp.title }}</span>
              <span class="tp-rev">¥{{ fmtMoney(tp.revenue) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Monetization Advisor -->
      <div class="card section-card" style="margin-top:14px">
        <h3 class="section-title">🤖 AI 变现策略顾问</h3>
        <p class="wizard-hint">基于你的作品类型和当前变现情况，AI 提供个性化策略建议</p>

        <div class="form-row">
          <div class="form-group">
            <label>作品名称</label>
            <input v-model="advisorForm.work_title" class="form-input" placeholder="你的作品名称" />
          </div>
          <div class="form-group">
            <label>作品类型</label>
            <select v-model="advisorForm.work_type" class="form-input">
              <option value="illustration">插画</option>
              <option value="pattern">图案设计</option>
              <option value="character">角色设计</option>
              <option value="typography">字体/排版</option>
              <option value="photo">摄影</option>
              <option value="3d">3D模型</option>
              <option value="painting">绘画</option>
            </select>
          </div>
        </div>

        <div class="wizard-actions" style="justify-content:flex-start;margin-top:14px">
          <button class="btn btn-primary" @click="askAdvisor" :disabled="advisorLoading">
            {{ advisorLoading ? '分析中...' : '💡 获取变现建议' }}
          </button>
        </div>

        <div v-if="advisorResult" class="advisor-result" style="margin-top:16px">
          <div class="advisor-advice">
            <h4>AI 分析结果</h4>
            <div class="advice-content" v-html="formatAdvice(advisorResult.ai_advice)"></div>
          </div>
          <div style="margin-top:14px">
            <h4>推荐变现路径</h4>
            <div class="path-cards" style="margin-top:8px">
              <div v-for="rp in advisorResult.recommended_paths" :key="rp.id" class="path-card" style="padding:14px">
                <div class="path-card-name">{{ rp.name_zh }}</div>
                <div class="path-card-desc">{{ rp.reason }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════
         Tab 7: Partners (Enhanced P1.5.9) (renumbered)
         ═══════════════════════════════════════════════════════════ -->
    <div v-if="activeTab === 'reminders'" class="animate-fade-in">
      <div v-if="!reminders.length" class="empty-hint">暂无提醒</div>
      <div v-else class="reminder-list">
        <div v-for="r in reminders" :key="r.id" class="reminder-row">
          <span>🔔 {{ r.title }}</span>
          <span>{{ r.remind_at?.slice(0, 10) }}</span>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/useAppStore'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import DisclaimerBanner from '@/components/common/DisclaimerBanner.vue'
import SpecRemediationPanel from '@/components/monetization/SpecRemediationPanel.vue'
import { supplyApi } from '@/api/supply'
import { worksApi } from '@/api/works'

const router = useRouter()
const appStore = useAppStore()
const hasWorks = ref(false)
const checking = ref(true)
const goToWorks = () => router.push('/app/works')

const activeTab = ref('designer')

const tabs = [
  { key: 'designer', label: '🎨 设计→产品' },
  { key: 'products', label: '📦 产品' },
  { key: 'campaigns', label: '🚀 众筹' },
  { key: 'licenses', label: '📜 IP授权' },
  { key: 'pod', label: '🖨️ POD发布' },
  { key: 'advisor', label: '🤖 变现顾问' },
  { key: 'reminders', label: '⏰ 提醒' },
]

// ── Dashboard Data ──

// ── Shared Data ──
const monetizationPaths = ref<any[]>([])
const materialCategories = ref<any[]>([])
const platforms = ref<any[]>([])
const works = ref<any[]>([])

// ── Products ──
const products = ref<any[]>([])
const productFilter = reactive({ monetization_path: '', material_category: '' })

// ── Campaigns ──
const campaigns = ref<any[]>([])
const showCampaignModal = ref(false)
const campaignForm = ref({ title: '', platform: 'modian', goal_amount: 0, description: '', tiers: [{ name: '', price: 0, limit: 0 }] })

// ── Licenses ──
const licenses = ref<any[]>([])
const showLicenseModal = ref(false)
const licenseForm = ref({ license_type: 'single_use', platform: '', price: 0 })

// ── Reminders ──
const reminders = ref<any[]>([])

// ── P2.5.1-P2.5.2 / P2.5.13: POD Platform Publishing ──
const podPlatforms = ref<any[]>([])
const selectedPodPlatform = ref('')
const podPlatformDetail = ref<any>(null)
const podForm = ref({ title: '', category: '', price: 0, design_file_path: '' })
const podResult = ref<any>(null)
const podPublishing = ref(false)

// ── P2.5.3-P2.5.4: Campaign Enhancements ──
const showGoalCalc = ref(false)
const showRewardTemplates = ref(false)
const rewardTemplates = ref<any[]>([])
const showReportModal = ref(false)
const campaignReport = ref<any>(null)
const goalCalcForm = ref({
  tiers: [{ name: 'Early Bird', price: 49, estimated_backers: 100 }],
  manufacturing_cost: 0,
  shipping_cost: 0,
})
const goalCalcResult = ref<any>(null)

// ── P2.5.5-P2.5.6: License Export ──
const showLicenseExportModal = ref(false)
const licenseExportResult = ref<any>(null)

// ── P2.5.11-P2.5.12: Aggregated Revenue + Advisor ──
const aggregatedRevenue = ref<any>({ summary: {}, by_platform: [], monthly_trends: [], top_products: [] })
const advisorForm = ref({ work_title: '', work_type: 'illustration' })
const advisorResult = ref<any>(null)
const advisorLoading = ref(false)

// ── Product Designer Wizard ──
const wizardStep = ref(0)
const wizardSteps = ['选择设计', '变现路径', '产品品类', '规格适配', '效果预览', '智能定价', '创建商品']
const selectedMaterial = ref('')
const designer = reactive({
  work_id: '',
  work_data: null as any,
  monetization_path: '',
  product_category_id: '',
  product_template: null as any,
  product_title: '',
  price: 0,
  cost: 0,
  platform: '',
  description: '',
})
const specResult = ref<any>(null)
const specOverrideConfirmed = ref(false)
const compatibleTemplates = ref<any[]>([])
const remediationSuggestions = ref<any[]>([])
const publishing = ref(false)

// Preview state
const previewMode = ref<'canvas' | 'printful' | 'ai'>('canvas')
const previewColor = ref('white')
const mockupLoading = ref(false)
const mockupUrl = ref('')
const aiLoading = ref(false)
const aiStyle = ref('realistic')

// Pricing state
const competitorMin = 89
const competitorMax = 159
const shippingCost = 8
const platformFee = computed(() => (designer.cost * 0.1).toFixed(2))
const totalCost = computed(() => +(designer.cost + parseFloat(platformFee.value) + shippingCost).toFixed(2))
const aiSuggestedMin = 119
const aiSuggestedMax = 169
const profitMargin = computed(() => {
  if (!designer.price) return 0
  return Math.round(((designer.price - totalCost.value) / designer.price) * 100)
})
const calcFinalProfit = computed(() => Math.max(0, +(designer.price - totalCost.value).toFixed(2)))
const pricePosition = computed(() => {
  if (!designer.price) return ''
  if (designer.price < competitorMin) return 'below'
  if (designer.price > competitorMax) return 'above'
  return 'reasonable'
})
const pricePositionLabel = computed(() => {
  const pos = pricePosition.value
  return { below: '低于均价', reasonable: '合理区间', above: '高于均价' }[pos || 'reasonable']
})

// ── Labels ──
const orderStatusLabels: Record<string, string> = {
  draft: '草稿', quoting: '报价中', confirmed: '已确认', in_production: '生产中',
  quality_check: '质检中', shipped: '已发货', completed: '已完成', cancelled: '已取消',
}
const orderStatusVariants: Record<string, string> = {
  draft: 'info', quoting: 'info', confirmed: 'info', in_production: 'warning',
  quality_check: 'warning', shipped: 'warning', completed: 'success', cancelled: 'error',
}

function fmtMoney(v: number) { return v?.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 }) || '0' }
function getPathLabel(pathId: string) {
  const p = monetizationPaths.value.find(x => x.id === pathId)
  return p?.name_zh || pathId || '未知'
}
function getPathProductCount(pathId: string) {
  const item = monetizationPaths.value.find((x: any) => x.id === pathId)
  return item ? 0 : 0
}
function handleCompatibleSelect(templateId: string) {
  // Switch to the compatible template
  const cat = allCategories.value.find((c: any) => c.id === templateId)
  if (cat) {
    designer.product_category_id = cat.id
    designer.product_template = cat
    // Re-run spec check with the new template
    runSpecCheck()
  }
}

const filteredCategories = computed(() => {
  if (!selectedMaterial.value) return []
  const cats = materialCategories.value.find(m => m.id === selectedMaterial.value)
  // We get categories from the product categories endpoint
  return allCategories.value.filter((c: any) => c.material_category === selectedMaterial.value)
})

// We'll store categories from the API
const allCategories = ref<any[]>([])

// Computed: block Step 5 when spec errors exist and override not confirmed
const needsErrorBlock = computed(() => {
  return specResult.value && specResult.value.error_count > 0 && !specOverrideConfirmed.value
})

// ── Data Loaders ──
async function loadMonetizationPaths() {
  try { const r = await supplyApi.monetizationPaths(); monetizationPaths.value = r.data.data } catch { /* toast handled by interceptor */ }
}
async function loadPlatforms() {
  try { const r = await supplyApi.platforms(); platforms.value = r.data.data } catch { /* toast handled by interceptor */ }
}
async function loadCategories() {
  try {
    const r = await supplyApi.productCategories()
    materialCategories.value = r.data.data.materials || []
    allCategories.value = r.data.data.categories_by_material
      ? Object.values(r.data.data.categories_by_material).flatMap((g: any) => g.categories || [])
      : []
  } catch { /* toast handled by interceptor */ }
}
async function loadWorks() {
  try { const r = await worksApi.list(); works.value = r.data.data?.items || [] } catch { /* toast handled by interceptor */ }
}
async function loadProducts() {
  try {
    const params: any = {}
    if (productFilter.monetization_path) params.monetization_path = productFilter.monetization_path
    if (productFilter.material_category) params.material_category = productFilter.material_category
    const r = await supplyApi.products(params)
    products.value = r.data.data
  } catch { /* toast handled by interceptor */ }
}
async function loadCampaigns() {
  try { const r = await supplyApi.campaigns(); campaigns.value = r.data.data } catch { /* toast handled by interceptor */ }
}
async function loadLicenses() {
  try { const r = await supplyApi.licenses(); licenses.value = r.data.data } catch { /* toast handled by interceptor */ }
}
async function loadReminders() {
  try { const r = await supplyApi.reminders(); reminders.value = r.data.data } catch { /* toast handled by interceptor */ }
}

// ── Wizard Actions ──
function selectWork(w: any) {
  designer.work_id = w.id
  designer.work_data = w
  designer.product_title = w.title || ''
}

async function runSpecCheck() {
  const t = designer.product_template
  if (!t) return
  const w = designer.work_data as any
  specOverrideConfirmed.value = false
  compatibleTemplates.value = []
  remediationSuggestions.value = []
  try {
    const r = await supplyApi.specValidate({
      category_id: t.id,
      dpi: w?.dpi || null,
      width_px: w?.width || null,
      height_px: w?.height || null,
      color_mode: w?.color_mode || 'sRGB',
      file_format: w?.file_format || 'PNG',
      has_transparency: w?.has_transparency,
    })
    specResult.value = r.data.data

    // P2: If errors, fetch compatible templates
    if (specResult.value.error_count > 0) {
      try {
        const compat = await supplyApi.specValidateCompat({
          dpi: w?.dpi || null,
          width_px: w?.width || null,
          height_px: w?.height || null,
          color_mode: w?.color_mode || 'sRGB',
          file_format: w?.file_format || 'PNG',
          exclude_category_id: t.id,
        })
        compatibleTemplates.value = compat?.data?.compatible_templates || []
      } catch { /* ignore compat fetch failure */ }
    }
  } catch (e) {
    specResult.value = null
  }
}

async function publishProduct() {
  if (!designer.work_id) {
    ;(window as any).$toast?.show('请先选择作品', 'warning')
    return
  }
  if (!designer.product_title?.trim()) {
    ;(window as any).$toast?.show('请输入商品标题', 'warning')
    return
  }
  if (!designer.price || designer.price <= 0) {
    ;(window as any).$toast?.show('价格必须大于0', 'warning')
    return
  }
  if (!designer.monetization_path) {
    ;(window as any).$toast?.show('请选择变现路径', 'warning')
    return
  }
  publishing.value = true
  try {
    // P2: Also create a DesignListing record
    await supplyApi.createListing({
      work_id: designer.work_id,
      product_template_id: designer.product_category_id,
      title: designer.product_title || designer.product_template?.name_zh || '未命名商品',
      description: designer.description,
      price: designer.price,
      cost: designer.cost,
      monetization_path: designer.monetization_path,
      spec_validation: specResult.value,
      status: 'active',
    }).catch(() => {}) // Non-critical: old products endpoint still works

    await supplyApi.createProduct({
      work_id: designer.work_id,
      title: designer.product_title || designer.product_template?.name_zh || '未命名商品',
      description: designer.description,
      price: designer.price,
      cost: designer.cost,
      category: designer.product_template?.category,
      monetization_path: designer.monetization_path,
      material_category: designer.product_template?.material_category,
      platform: designer.platform,
    })
    ;(window as any).$toast?.show('商品已创建', 'success')
    // Reset wizard
    wizardStep.value = 0
    designer.work_id = ''
    designer.monetization_path = ''
    designer.product_category_id = ''
    designer.product_template = null
    designer.price = 0
    designer.cost = 0
    designer.platform = ''
    designer.description = ''
    specResult.value = null
    specOverrideConfirmed.value = false
    compatibleTemplates.value = []
    remediationSuggestions.value = []
    loadProducts()
  } catch (e: any) {
    ;(window as any).$toast?.show('创建失败: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    publishing.value = false
  }
}

// ── Campaign ──
async function createCampaign() {
  const f = campaignForm.value
  if (!f.title?.trim()) {
    ;(window as any).$toast?.show('请输入项目名称', 'warning')
    return
  }
  if (!f.platform?.trim()) {
    ;(window as any).$toast?.show('请输入平台名称', 'warning')
    return
  }
  if (!f.goal_amount || f.goal_amount <= 0) {
    ;(window as any).$toast?.show('目标金额必须大于0', 'warning')
    return
  }
  try {
    const f = campaignForm.value
    const tiers = f.tiers.filter((t: any) => t.name && t.price > 0)
    await supplyApi.createCampaign({ title: f.title, platform: f.platform, goal_amount: f.goal_amount, description: f.description, reward_tiers: tiers })
    showCampaignModal.value = false
    campaignForm.value = { title: '', platform: 'modian', goal_amount: 0, description: '', tiers: [{ name: '', price: 0, limit: 0 }] }
    ;(window as any).$toast?.show('众筹项目已创建', 'success')
    loadCampaigns()
  } catch (e) {
    ;(window as any).$toast?.show('创建众筹项目失败', 'error')
  }
}

async function exportCampaignReport(campaignId: string) {
  try {
    const r = await supplyApi.campaignReport(campaignId)
    campaignReport.value = r.data.data
    showReportModal.value = true
  } catch (e) {
    ;(window as any).$toast?.show('获取报表失败', 'error')
  }
}

async function loadRewardTemplates() {
  showRewardTemplates.value = !showRewardTemplates.value
  if (showRewardTemplates.value && !rewardTemplates.value.length) {
    try { const r = await supplyApi.rewardTemplates(); rewardTemplates.value = r.data.data } catch (e) { /* ignore */ }
  }
}

function useRewardTemplate(rt: any) {
  campaignForm.value.tiers = rt.tiers.map((t: any) => ({
    name: t.name,
    price: t.price_suggestions?.min || 0,
    limit: t.type === 'monthly' ? 0 : 100,
  }))
  showCampaignModal.value = true
  showRewardTemplates.value = false
}

async function calculateGoal() {
  try {
    const r = await supplyApi.calculateFundingGoal({
      tiers: goalCalcForm.value.tiers.filter((t: any) => t.price > 0),
      manufacturing_cost: goalCalcForm.value.manufacturing_cost,
      shipping_cost: goalCalcForm.value.shipping_cost,
    })
    goalCalcResult.value = r.data.data
  } catch (e) { /* ignore */ }
}

// ── License ──
async function createLicense() {
  const f = licenseForm.value
  if (!f.platform?.trim()) {
    ;(window as any).$toast?.show('请输入平台名称', 'warning')
    return
  }
  if (!f.price || f.price <= 0) {
    ;(window as any).$toast?.show('授权价格必须大于0', 'warning')
    return
  }
  try {
    const f = licenseForm.value
    await supplyApi.createLicense({ license_type: f.license_type, platform: f.platform, price: f.price })
    showLicenseModal.value = false
    licenseForm.value = { license_type: 'single_use', platform: '', price: 0 }
    ;(window as any).$toast?.show('授权已创建', 'success')
    loadLicenses()
  } catch (e) {
    ;(window as any).$toast?.show('创建授权失败', 'error')
  }
}

async function exportLicense(licenseId: string, format: string) {
  try {
    const r = await supplyApi.exportLicense(licenseId, format)
    licenseExportResult.value = r.data.data
    showLicenseExportModal.value = true
  } catch (e) {
    ;(window as any).$toast?.show('导出失败', 'error')
  }
}

// ── P2.5 POD Publishing ──
async function selectPodPlatform(platformId: string) {
  selectedPodPlatform.value = platformId
  podResult.value = null
  // Fetch platform detail for Chinese POD platforms
  if (['yingge', 'yunda', 'dingzhilian', 'shanyin'].includes(platformId)) {
    try {
      const r = await supplyApi.chinesePodPlatformDetail(platformId)
      const d = r.data.data
      podPlatformDetail.value = {
        name: d.platform.name,
        info: {
          网址: d.platform.url,
          模式: d.platform.mode,
          地区: d.platform.region,
          特点: d.platform.key_features?.join(', '),
          支付方式: d.platform.payment_methods?.join(', '),
        },
        categories: d.categories,
        specs: d.specs,
      }
    } catch (e) {
      podPlatformDetail.value = null
    }
  } else {
    podPlatformDetail.value = { name: platformId === 'printful' ? 'Printful' : 'Redbubble' }
  }
}

async function publishToPod(action: string) {
  podPublishing.value = true
  try {
    const r = await supplyApi.publishToPod({
      platform: selectedPodPlatform.value,
      product_data: {
        title: podForm.value.title || 'Test Product',
        category: podForm.value.category,
        price: podForm.value.price || 29.99,
        design_file_path: podForm.value.design_file_path,
        tags: ['art', 'design'],
      },
      action: action,
    })
    podResult.value = r.data.data?.result || r.data.data
    ;(window as any).$toast?.show(`${action} 完成`, 'success')
  } catch (e) {
    ;(window as any).$toast?.show('操作失败', 'error')
  } finally {
    podPublishing.value = false
  }
}

// ── P2.5.11-P2.5.12 Aggregated Revenue + Advisor ──
async function loadAggregatedRevenue() {
  try {
    const r = await supplyApi.aggregatedRevenue()
    aggregatedRevenue.value = r.data.data
  } catch (e) { /* ignore */ }
}

async function askAdvisor() {
  if (!advisorForm.value.work_title || !advisorForm.value.work_type) {
    ;(window as any).$toast?.show('请填写作品信息', 'warning')
    return
  }
  advisorLoading.value = true
  try {
    const r = await supplyApi.monetizationAdvisor({
      work_title: advisorForm.value.work_title,
      work_type: advisorForm.value.work_type,
      creator_type: creatorType.value || undefined,
      current_paths: ['pod'],
    })
    advisorResult.value = r.data.data
  } catch (e) {
    ;(window as any).$toast?.show('获取建议失败', 'error')
  } finally {
    advisorLoading.value = false
  }
}

function formatAdvice(text: string): string {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

function getTrendWidth(revenue: number): number {
  const maxRev = Math.max(...(aggregatedRevenue.value.monthly_trends || []).map((m: any) => m.revenue || 0), 1)
  return maxRev > 0 ? Math.min(100, (revenue / maxRev) * 100) : 0
}

// Preview helpers
function zoomIn() { /* Canvas zoom in */ }
function zoomOut() { /* Canvas zoom out */ }
function resetZoom() { /* Canvas reset */ }
async function generateMockup() {
  mockupLoading.value = true
  try {
    const { data } = await supplyApi.generatePrintfulMockup({
      product_id: designer.product_category_id,
      design_file_id: designer.work_id,
      colors: [previewColor.value],
    })
    mockupUrl.value = data?.mockups?.[0]?.url || ''
  } catch {
    mockupUrl.value = ''
  } finally {
    mockupLoading.value = false
  }
}
async function generateAiMockup() {
  aiLoading.value = true
  try {
    await supplyApi.generateMockup({
      category_id: designer.product_category_id,
      style: aiStyle.value,
    })
    // In future: render AI-generated mockup
  } catch {
    // ignore
  } finally {
    aiLoading.value = false
  }
}

function updateProfit() {
  // Triggered on price change
}

// ── Creator type (from localStorage / onboarding) ──
const creatorType = ref('')

onMounted(async () => {
  // 前置校验: 检查是否有作品
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
  // Restore creator_type from localStorage
  const saved = localStorage.getItem('oristudio-creator-type')
  if (saved) creatorType.value = saved
  // Also try to load from backend onboarding status
  loadOnboardingStatus()

  loadMonetizationPaths()
  loadPlatforms()
  loadCategories()
  loadWorks()
  loadProducts()
  loadCampaigns()
  loadLicenses()
  loadReminders()
  loadAggregatedRevenue()
  // Load POD platforms
  loadPodPlatforms()
})

watch(() => appStore.workCount, (val) => {
  hasWorks.value = val > 0
})

async function loadOnboardingStatus() {
  try {
    const { systemApi } = await import('@/api/system')
    const res = await systemApi.onboardingStatus()
    if (res.data.data?.creator_type) {
      creatorType.value = res.data.data.creator_type
    }
  } catch {
    // Silently continue
  }
}

async function loadPodPlatforms() {
  // Global platforms from existing seed data + Chinese POD
  const globalPlatforms = [
    { id: 'printful', name: 'Printful' },
    { id: 'redbubble', name: 'Redbubble' },
  ]
  try {
    const r = await supplyApi.chinesePodPlatforms()
    podPlatforms.value = [...globalPlatforms, ...r.data.data.map((p: any) => ({ id: p.id, name: p.name }))]
  } catch (e) {
    podPlatforms.value = globalPlatforms
  }
}
</script>

<style scoped>
.supply-view { display:flex; flex-direction:column; gap:20px; }

/* Tabs */
.cat-tabs { display:flex; gap:8px; flex-wrap:wrap; }
.cat-tab { padding:8px 18px; border-radius:100px; font-size:.84rem; font-weight:600; cursor:pointer; border:1px solid var(--border); background:var(--surface); color:var(--muted); font-family:var(--font-body); transition:all .2s; }
.cat-tab.active { background:var(--accent); color:#fff; border-color:var(--accent); }

/* Dashboard */
.dashboard-stats { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:14px; }
.stat-card { padding:18px 20px; text-align:center; }
.stat-icon { font-size:1.6rem; margin-bottom:4px; }
.stat-value { font-size:1.4rem; font-weight:800; color:var(--fg); }
.stat-label { font-size:.78rem; color:var(--muted); margin-top:2px; }
.section-card { padding:18px 20px; margin-top:14px; }
.section-title { font-size:.9rem; font-weight:700; margin-bottom:12px; }
.platform-rev-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }
.platform-rev-item { display:flex; flex-direction:column; padding:10px 14px; background:var(--surface); border-radius:var(--radius-sm); border:1px solid var(--border); }
.platform-name { font-size:.78rem; color:var(--muted); }
.platform-amount { font-size:1rem; font-weight:700; }
.path-bars { display:flex; flex-direction:column; gap:8px; }
.path-bar-row { display:flex; align-items:center; gap:10px; padding:8px 12px; background:var(--surface); border-radius:var(--radius-sm); border:1px solid var(--border); }
.path-bar-icon { font-size:1.2rem; }
.path-bar-label { flex:1; font-size:.85rem; font-weight:600; }
.path-bar-count { font-size:.82rem; color:var(--muted); }
.material-tags { display:flex; gap:6px; flex-wrap:wrap; }
.material-tag { padding:4px 10px; border-radius:100px; font-size:.72rem; background:oklch(56% 0.12 170 / .1); color:var(--accent); }

/* Product Designer Wizard */
.wizard-steps { display:flex; gap:0; margin-bottom:16px; }
.wizard-step { display:flex; align-items:center; gap:6px; padding:10px 16px; cursor:pointer; border-bottom:3px solid var(--border); font-size:.82rem; color:var(--muted); transition:all .2s; }
.wizard-step.active { border-color:var(--accent); color:var(--accent); font-weight:700; }
.wizard-step.done { border-color:var(--success, #22c55e); color:var(--success, #22c55e); }
.step-num { display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:var(--border); font-size:.72rem; font-weight:700; }
.wizard-step.active .step-num { background:var(--accent); color:#fff; }
.wizard-step.done .step-num { background:var(--success, #22c55e); color:#fff; }
.wizard-panel { padding:22px 24px; }
.wizard-hint { font-size:.82rem; color:var(--muted); margin-bottom:14px; }
.wizard-actions { display:flex; gap:10px; justify-content:flex-end; margin-top:18px; }
.works-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:12px; }
.work-card { padding:12px; border:2px solid var(--border); border-radius:var(--radius-md); cursor:pointer; transition:all .2s; }
.work-card:hover { border-color:var(--accent); }
.work-card.selected { border-color:var(--accent); background:oklch(56% 0.12 170 / .06); }
.work-thumb { width:100%; height:100px; overflow:hidden; border-radius:var(--radius-sm); background:var(--surface); }
.work-thumb img { width:100%; height:100%; object-fit:cover; }
.work-thumb-placeholder { width:100%; height:100px; display:flex; align-items:center; justify-content:center; font-size:2rem; background:var(--surface); border-radius:var(--radius-sm); }
.work-info { margin-top:8px; }
.work-info strong { display:block; font-size:.84rem; }
.work-meta { font-size:.7rem; color:var(--muted); }

/* Path Cards */
.path-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; }
.path-card { padding:18px; border:2px solid var(--border); border-radius:var(--radius-lg); cursor:pointer; transition:all .2s; text-align:center; }
.path-card:hover { border-color:var(--accent); transform:translateY(-2px); box-shadow:0 4px 16px oklch(0 0 0 / .06); }
.path-card.selected { border-color:var(--accent); background:oklch(56% 0.12 170 / .06); }
.path-card-icon { font-size:2rem; margin-bottom:6px; }
.path-card-name { font-size:.92rem; font-weight:700; margin-bottom:4px; }
.path-card-desc { font-size:.75rem; color:var(--muted); margin-bottom:8px; line-height:1.4; }
.path-card-tags { display:flex; gap:4px; flex-wrap:wrap; justify-content:center; }
.tag-green { background:oklch(56% 0.12 140 / .1); color:oklch(56% 0.12 140); }

/* Product Grid */
.product-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:10px; }
.product-card { padding:14px; border:1.5px solid var(--border); border-radius:var(--radius-md); cursor:pointer; transition:all .2s; }
.product-card:hover { border-color:var(--accent); }
.product-card.selected { border-color:var(--accent); background:oklch(56% 0.12 170 / .06); }
.product-card-name { font-size:.88rem; font-weight:700; }
.product-card-en { font-size:.72rem; color:var(--muted); }
.product-card-price { font-size:.82rem; font-weight:600; color:var(--accent); margin-top:4px; }
.product-card-margin { font-size:.7rem; color:var(--muted); }
.product-card-tags { display:flex; gap:3px; flex-wrap:wrap; margin-top:6px; }

/* Spec Check Result */
.spec-result { margin-top:12px; }
.spec-status-banner { padding:12px 16px; border-radius:var(--radius-sm); font-weight:700; font-size:.9rem; margin-bottom:12px; }
.spec-status-banner.pass { background:oklch(56% 0.12 140 / .1); color:oklch(56% 0.12 140); }
.spec-status-banner.warning { background:oklch(56% 0.12 80 / .1); color:oklch(56% 0.12 80); }
.spec-status-banner.error { background:oklch(56% 0.18 20 / .1); color:oklch(56% 0.18 20); }
.spec-checks { display:flex; flex-direction:column; gap:8px; }
.spec-check { display:flex; gap:10px; padding:10px 14px; border-radius:var(--radius-sm); background:var(--surface); border:1px solid var(--border); }
.spec-check.pass { border-left:3px solid oklch(56% 0.12 140); }
.spec-check.warning { border-left:3px solid oklch(56% 0.12 80); }
.spec-check.error { border-left:3px solid oklch(56% 0.18 20); }
.spec-check-icon { font-size:1rem; flex-shrink:0; }
.spec-check-body { display:flex; flex-direction:column; gap:2px; }
.spec-check-msg { font-size:.82rem; }
.spec-check-suggestion { font-size:.75rem; color:var(--muted); font-style:italic; }

/* Products List */
.filter-bar { display:flex; gap:8px; margin-bottom:12px; }
.product-list { display:flex; flex-direction:column; gap:8px; }
.product-row { padding:14px 18px; }
.product-row-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.product-row-body { display:flex; gap:16px; font-size:.82rem; color:var(--muted); }

/* Campaigns */
.campaign-list { display:flex; flex-direction:column; gap:10px; }
.campaign-card { padding:16px 20px; }
.campaign-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.campaign-progress { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.progress-bar { flex:1; height:8px; background:var(--border); border-radius:4px; overflow:hidden; }
.progress-fill { height:100%; background:var(--accent); border-radius:4px; transition:width .3s; }
.campaign-stats { display:flex; gap:16px; font-size:.8rem; color:var(--muted); }

/* Licenses */
.license-list { display:flex; flex-direction:column; gap:8px; }
.license-card { padding:14px 18px; }
.license-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.license-body { display:flex; gap:16px; font-size:.82rem; color:var(--muted); }

/* Partners */
.actions-bar { display:flex; justify-content:flex-end; margin-bottom:8px; }
.partner-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:16px; }
.partner-card { padding:18px 20px; }
.partner-name { font-weight:700; font-size:.95rem; }
.partner-type-tag { display:inline-block; padding:2px 8px; border-radius:4px; font-size:.68rem; background:oklch(56% 0.12 250 / .1); color:oklch(56% 0.12 250); margin-top:4px; }
.partner-rating { font-size:.75rem; }
.partner-info { font-size:.8rem; color:var(--muted); margin-top:4px; }
.partner-tags { display:flex; gap:4px; flex-wrap:wrap; margin-top:8px; }
.tag { padding:2px 8px; border-radius:100px; font-size:.68rem; background:oklch(56% 0.12 170 / .1); color:var(--accent); }
.tag-sm { font-size:.62rem; padding:1px 6px; }

/* Orders */
.order-list { display:flex; flex-direction:column; gap:8px; }
.order-row { padding:16px 20px; }
.order-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.order-header-right { display:flex; gap:8px; align-items:center; }
.order-body { display:flex; gap:14px; font-size:.82rem; color:var(--muted); flex-wrap:wrap; }
.order-sample { display:flex; gap:12px; align-items:center; margin-top:8px; font-size:.78rem; }
.order-footer { font-size:.75rem; color:var(--muted); margin-top:6px; }
.text-success { color:var(--success, #22c55e); }
.text-muted { color:var(--muted); }

/* Reminders */
.reminder-list { display:flex; flex-direction:column; gap:4px; }
.reminder-row { display:flex; justify-content:space-between; padding:10px 16px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.85rem; }

/* Forms */
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group label { font-size:.82rem; font-weight:600; color:var(--muted); }
.form-input { padding:10px 14px; border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.88rem; font-family:var(--font-body); color:var(--fg); background:var(--surface); outline:none; }
.form-input:focus { border-color:var(--accent); box-shadow:0 0 0 3px oklch(56% 0.12 170 / .1); }
.form-row { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.profit-preview { font-size:1.1rem; font-weight:700; color:var(--success, #22c55e); padding-top:8px; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; }

/* Buttons */
.btn { padding:10px 20px; border-radius:var(--radius-sm); font-size:.85rem; font-weight:600; cursor:pointer; border:none; font-family:var(--font-body); transition:all .2s; }
.btn-primary { background:var(--accent); color:#fff; }
.btn-primary:hover { filter:brightness(1.1); }
.btn-primary:disabled { opacity:.5; cursor:not-allowed; }
.btn-secondary { background:var(--surface); color:var(--fg); border:1px solid var(--border); }
.btn-secondary:hover { background:var(--border); }
.btn-sm { padding:4px 10px; font-size:.72rem; }

/* Empty / utility */
.empty-hint { padding:40px 20px; text-align:center; color:var(--muted); font-size:.88rem; }

.animate-fade-in { animation:fadeIn .3s ease; }
@keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
.animate-scale-in { animation:scaleIn .2s ease; }
@keyframes scaleIn { from { opacity:0; transform:scale(.95); } to { opacity:1; transform:scale(1); } }

textarea.form-input { resize:vertical; }

/* P2.5 Additional Styles */
.platform-info-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.info-block { background:var(--surface); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border); }
.info-block h4 { font-size:.85rem; font-weight:700; margin-bottom:8px; }
.info-row { display:flex; justify-content:space-between; padding:4px 0; font-size:.78rem; }
.info-key { color:var(--muted); }
.info-val { color:var(--fg); font-weight:500; }
.spec-requirements { display:flex; flex-direction:column; gap:4px; }
.spec-req { font-size:.78rem; }
.spec-req span { color:var(--muted); }
.pod-category-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:8px; }
.pod-category-item { display:flex; justify-content:space-between; padding:8px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); }
.cat-name { font-size:.82rem; font-weight:600; }
.cat-price { font-size:.78rem; color:var(--accent); font-weight:700; }
.result-pre { background:oklch(0 0 0 / .04); padding:12px; border-radius:var(--radius-sm); font-size:.72rem; white-space:pre-wrap; word-break:break-all; max-height:400px; overflow-y:auto; font-family:monospace; }

.goal-tier-row { display:flex; gap:6px; align-items:center; margin-bottom:6px; }
.template-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:10px; }
.template-card { padding:14px; border:1.5px solid var(--border); border-radius:var(--radius-md); cursor:pointer; transition:all .2s; }
.template-card:hover { border-color:var(--accent); background:oklch(56% 0.12 170 / .04); }
.template-desc { font-size:.75rem; color:var(--muted); margin-bottom:8px; }
.template-tiers { display:flex; flex-direction:column; gap:3px; }
.template-tier { display:flex; justify-content:space-between; font-size:.75rem; padding:3px 8px; background:var(--surface); border-radius:4px; }

.campaign-tier-preview { display:flex; gap:8px; flex-wrap:wrap; }
.tier-mini { display:flex; gap:6px; font-size:.72rem; padding:3px 8px; background:oklch(56% 0.12 170 / .06); border-radius:4px; }

.report-section { margin-top:10px; font-size:.82rem; }
.report-tier-row { display:flex; gap:12px; padding:4px 0; font-size:.78rem; }

.monthly-trends { display:flex; flex-direction:column; gap:4px; }
.trend-bar-row { display:flex; align-items:center; gap:8px; }
.trend-month { width:60px; font-size:.72rem; color:var(--muted); }
.trend-bar { flex:1; height:6px; background:var(--border); border-radius:3px; overflow:hidden; }
.trend-fill { height:100%; background:var(--accent); border-radius:3px; min-width:2px; transition:width .3s; }
.trend-value { width:100px; text-align:right; font-size:.78rem; font-weight:600; }

.top-products-list { display:flex; flex-direction:column; gap:4px; }
.top-product-row { display:flex; justify-content:space-between; padding:6px 10px; background:var(--surface); border-radius:4px; font-size:.82rem; }
.tp-rev { font-weight:700; color:var(--accent); }

.advisor-advice { background:oklch(56% 0.12 170 / .04); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border); }
.advice-content { font-size:.85rem; line-height:1.6; white-space:pre-wrap; }
.advice-content h2, .advice-content h3 { margin-top:12px; margin-bottom:4px; }
.advice-content ol, .advice-content ul { padding-left:20px; }

.preview-toggle { display:flex; gap:8px; margin-bottom:16px; }
.mode-btn { padding:6px 14px; border:1px solid var(--border); border-radius:var(--radius-sm); background:none; cursor:pointer; font-size:.82rem; }
.mode-btn.active { background:var(--accent); color:#fff; border-color:var(--accent); }

.canvas-preview-area, .printful-preview-area, .ai-preview-area { min-height:200px; border:1px solid var(--border); border-radius:var(--radius-md); padding:16px; }
.preview-canvas-placeholder { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:200px; color:var(--muted); }
.placeholder-icon { font-size:3rem; margin-bottom:8px; }
.hint-text { font-size:.72rem; margin-top:4px; }
.preview-controls { display:flex; gap:8px; margin-top:12px; align-items:center; }
.ctrl-btn { padding:4px 10px; border:1px solid var(--border); border-radius:var(--radius-sm); background:none; cursor:pointer; font-size:.78rem; }
.color-select { padding:4px 8px; border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.78rem; }
.preview-image img { max-width:100%; border-radius:var(--radius-sm); }
.loading-spinner { text-align:center; padding:20px; color:var(--muted); }
.ai-style-selector { display:flex; gap:8px; align-items:center; margin:12px 0; }

.pricing-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-md); padding:18px; }
.cost-breakdown { display:flex; flex-direction:column; gap:6px; }
.cost-row { display:flex; justify-content:space-between; font-size:.85rem; padding:4px 0; }
.cost-row.total { font-weight:700; border-top:1px solid var(--border); padding-top:8px; }
.competitor-range { display:flex; justify-content:space-between; align-items:center; font-size:.82rem; color:var(--muted); padding:8px 0; }
.price-tag { padding:2px 8px; border-radius:100px; font-size:.7rem; font-weight:600; }
.price-tag.below { background:oklch(56% 0.12 140 / .1); color:oklch(56% 0.12 140); }
.price-tag.reasonable { background:oklch(65% 0.1 270 / .1); color:oklch(55% 0.15 270); }
.price-tag.above { background:oklch(75% 0.12 80 / .1); color:oklch(65% 0.12 80); }
.ai-price-suggestion { font-size:1.2rem; font-weight:800; color:var(--accent); padding:8px 0; }
.ai-price-sep { margin: 0 4px; color: var(--muted); }
.margin-display { font-size:1.2rem; font-weight:800; color:var(--success, #22c55e); padding-top:8px; }
.profit-display { font-size:.88rem; font-weight:600; color:var(--accent); margin-top:8px; }

.summary-preview { background:oklch(56% 0.12 170 / .04); padding:14px; border-radius:var(--radius-sm); border:1px solid var(--border); margin-bottom:16px; }
.summary-preview h4 { margin:0 0 10px; font-size:.88rem; }
.summary-preview dl { display:grid; grid-template-columns:auto 1fr; gap:4px 12px; font-size:.82rem; }
.summary-preview dt { color:var(--muted); }
.summary-preview dd { font-weight:600; }

.platform-count { font-size:.68rem; color:var(--muted); }
</style>

<template>
  <div class="ipr-view">
    <div class="cat-tabs">
      <button v-for="tab in tabs" :key="tab.key" :class="['cat-tab', { active: activeTab === tab.key }]" @click="activeTab = tab.key">
        {{ tab.label }}
      </button>
    </div>

    <!-- Full-screen disclaimer modal (only on first entry, dismissed by accepting) -->
    <div v-if="!disclaimersAccepted" class="disclaimer-fullscreen-modal" @click.self="void 0">
      <div class="disclaimer-modal-card">
        <h2>⚖️ 法律声明与免责条款</h2>
        <p class="disclaimer-intro">使用前请阅读并同意以下声明：</p>
        <div class="disclaimer-list">
          <div v-for="(msg, i) in disclaimerMessages" :key="i" class="disclaimer-item">
            <span class="disclaimer-num">#{{ i + 1 }}</span>
            <span>{{ msg }}</span>
          </div>
        </div>
        <div class="disclaimer-footer">
          <button class="btn btn-primary btn-lg" @click="acceptDisclaimers">我已阅读并同意</button>
        </div>
      </div>
    </div>

    <!-- Disclaimer banners (inside tabs, after modal is dismissed) -->
    <div v-if="activeTab === 'guidelines'" class="guidelines animate-fade-in">
      <DisclaimerBanner
        mode="banner"
        title="信息参考声明"
        :messages="['本工具仅提供信息指引，不构成法律建议（声明 #2）。IP登记指引覆盖中国/美国/欧盟/WIPO主要辖区，不包括所有国家/地区（声明 #7）。所有申请须由您自行向官方机构提交。']"
      />

      <!-- P2.4: 辖区选择器 -->
      <div class="jurisdiction-bar">
        <button
          v-for="j in globalJurisdictions"
          :key="j.code"
          :class="['jur-btn', { active: guidelineJurisdiction === j.code }]"
          @click="switchJurisdiction(j.code)"
        >
          <span class="jur-flag">{{ j.flag }}</span>
          <span class="jur-label">{{ j.label }}</span>
        </button>
      </div>

      <!-- 加载当前辖区指引 -->
      <template v-if="currentGuidelines">
        <!-- 版权指引 (如有) -->
        <div v-if="currentGuidelines.copyright" class="guideline-card card">
          <div class="gl-header">
            <span class="gl-icon">©️</span>
            <div>
              <h3>{{ currentGuidelines.copyright?.title || '著作权登记指引' }}</h3>
              <p class="gl-subtitle">{{ currentGuidelines.copyright?.description || '' }}</p>
            </div>
          </div>
          <div class="gl-body">
            <!-- Forms info for US -->
            <div v-if="currentGuidelines.copyright?.forms" class="gl-section">
              <h4>📝 申请表格类型</h4>
              <div class="fee-grid">
                <div v-for="(desc, code) in currentGuidelines.copyright.forms" :key="code" class="fee-chip">
                  <strong>{{ code }}</strong>
                  <span>{{ desc }}</span>
                </div>
              </div>
            </div>
            <div class="gl-section">
              <h4>📋 所需材料</h4>
              <div class="materials-list">
                <div v-for="m in currentGuidelines.copyright?.materials || []" :key="m.name" class="material-item" :class="{ required: m.required }">
                  <span class="material-check">{{ m.required ? '✓' : '○' }}</span>
                  <div>
                    <span class="material-name">{{ m.name }}</span>
                    <span class="material-desc">{{ m.description }}</span>
                    <span v-if="m.can_prefill" class="material-tag">🪄 可自动预填</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="gl-section">
              <h4>📝 办理流程</h4>
              <div class="process-flow">
                <div v-for="p in currentGuidelines.copyright?.process || []" :key="p.step" class="process-step">
                  <span class="step-num">{{ p.step }}</span>
                  <div>
                    <strong>{{ p.name }}</strong>
                    <p>{{ p.description }}</p>
                    <small>⏱ {{ p.duration }}</small>
                  </div>
                </div>
              </div>
            </div>
            <div class="gl-meta">
              <span v-if="currentGuidelines.copyright?.platform_url">🏛️ <a :href="currentGuidelines.copyright?.platform_url" target="_blank">{{ currentGuidelines.copyright?.institution }}</a></span>
              <span v-else>🏛️ {{ currentGuidelines.copyright?.institution }}</span>
              <span v-if="currentGuidelines.copyright?.legal_basis">📜 {{ currentGuidelines.copyright?.legal_basis }}</span>
              <span v-if="currentGuidelines.copyright?.estimated_duration">⏱️ {{ currentGuidelines.copyright?.estimated_duration }}</span>
              <span v-if="currentGuidelines.copyright?.validity">🔄 {{ currentGuidelines.copyright?.validity }}</span>
            </div>
            <div v-if="currentGuidelines.copyright?.fee" class="gl-fees">
              <h4>💰 费用参考</h4>
              <div class="fee-grid">
                <div class="fee-chip" v-for="(fee, key) in currentGuidelines.copyright?.fee" :key="key">
                  <strong>{{ keyLabels[key] || key }}</strong>
                  <span>{{ fee }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 商标指引 (如有) -->
        <div v-if="currentGuidelines.trademark" class="guideline-card card">
          <div class="gl-header">
            <span class="gl-icon">™️</span>
            <div>
              <h3>{{ currentGuidelines.trademark?.title || '商标注册指引' }}</h3>
              <p class="gl-subtitle">{{ currentGuidelines.trademark?.description || '' }}</p>
            </div>
          </div>
          <div class="gl-body">
            <div class="gl-warning">⚠️ {{ currentGuidelines.trademark?.disclaimer }}</div>
            <div v-if="currentGuidelines.trademark?.note_personal" class="gl-warning" style="background:oklch(62% 0.18 30 / 0.08);color:var(--red);">
              {{ currentGuidelines.trademark?.note_personal }}
            </div>
            <div v-if="currentGuidelines.trademark?.note_agent" class="gl-warning" style="background:oklch(62% 0.18 30 / 0.08);color:var(--red);">
              {{ currentGuidelines.trademark?.note_agent }}
            </div>
            <div v-if="currentGuidelines.trademark?.note_language" class="gl-section">
              <h4>🌐 语言要求</h4>
              <p style="font-size:.85rem;color:var(--muted);margin:0">{{ currentGuidelines.trademark.note_language }}</p>
            </div>
            <div v-if="currentGuidelines.trademark?.central_attack_risk" class="gl-warning" style="background:oklch(62% 0.18 20 / 0.08);color:var(--red);">
              {{ currentGuidelines.trademark.central_attack_risk }}
            </div>
            <div v-if="currentGuidelines.trademark?.prerequisites" class="gl-section">
              <h4>⚠️ 前提条件</h4>
              <p style="font-size:.85rem;color:var(--muted);margin:0">{{ currentGuidelines.trademark.prerequisites }}</p>
            </div>
            <!-- EU member countries -->
            <div v-if="currentGuidelines.trademark?.member_countries" class="gl-section">
              <h4>🇪🇺 覆盖国家 ({{ currentGuidelines.trademark.member_countries.length }}个)</h4>
              <div class="country-grid">
                <span v-for="c in currentGuidelines.trademark.member_countries" :key="c" class="country-chip">{{ c }}</span>
              </div>
            </div>
            <!-- WO member count -->
            <div v-if="currentGuidelines.trademark?.member_count" class="gl-section">
              <h4>🌐 覆盖范围</h4>
              <p style="font-size:.85rem;color:var(--muted);margin:0">覆盖 {{ currentGuidelines.trademark.member_count }} 个缔约方</p>
            </div>
            <!-- Categories chip (CN only) -->
            <div v-if="currentGuidelines.categories || globalCategories" class="gl-section">
              <h4>📂 文创常用类别</h4>
              <div class="category-grid">
                <div v-for="(desc, code) in (currentGuidelines.categories || globalCategories)" :key="code" class="category-chip" @click="selectClassHint(Number(code))">
                  <strong>第{{ code }}类</strong>
                  <span>{{ desc }}</span>
                </div>
              </div>
            </div>
            <!-- Fee examples (WIPO/EU) -->
            <div v-if="currentGuidelines.trademark?.fee_examples" class="gl-section">
              <h4>💰 费用示例</h4>
              <div class="fee-example-list">
                <div v-for="(ex, idx) in currentGuidelines.trademark.fee_examples" :key="idx" class="fee-example-item">
                  <div class="fee-example-header">
                    <strong>{{ ex.scenario }}</strong>
                    <span class="fee-total">{{ ex.total }}</span>
                  </div>
                  <p class="fee-example-breakdown">{{ ex.breakdown }}</p>
                </div>
              </div>
            </div>
            <!-- Fee string (simple) -->
            <div v-if="typeof currentGuidelines.trademark?.fee === 'string'" class="gl-section">
              <h4>💰 费用</h4>
              <p style="font-size:.85rem;margin:0">{{ currentGuidelines.trademark.fee }}</p>
            </div>
            <!-- Fee object (complex) -->
            <div v-else-if="currentGuidelines.trademark?.fee && typeof currentGuidelines.trademark.fee === 'object'" class="gl-fees">
              <h4>💰 费用参考</h4>
              <div class="fee-grid">
                <div class="fee-chip" v-for="(fee, key) in currentGuidelines.trademark.fee" :key="key">
                  <strong>{{ trademarkFeeLabels[key] || keyLabels[key] || key }}</strong>
                  <span>{{ fee }}</span>
                </div>
              </div>
            </div>
            <div class="gl-section">
              <h4>📋 所需材料</h4>
              <div class="materials-list">
                <div v-for="m in currentGuidelines.trademark?.materials || []" :key="m.name" class="material-item" :class="{ required: m.required }">
                  <span class="material-check">{{ m.required ? '✓' : '○' }}</span>
                  <div>
                    <span class="material-name">{{ m.name }}</span>
                    <span class="material-desc">{{ m.description }}</span>
                    <span v-if="m.can_prefill" class="material-tag">🪄 可自动预填</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="gl-section">
              <h4>📝 办理流程</h4>
              <div class="process-flow">
                <div v-for="p in currentGuidelines.trademark?.process || []" :key="p.step" class="process-step">
                  <span class="step-num">{{ p.step }}</span>
                  <div>
                    <strong>{{ p.name }}</strong>
                    <p>{{ p.description }}</p>
                    <small>⏱ {{ p.duration }}</small>
                  </div>
                </div>
              </div>
            </div>
            <div class="gl-meta">
              <span v-if="currentGuidelines.trademark?.platform_url">🏛️ <a :href="currentGuidelines.trademark?.platform_url" target="_blank">{{ currentGuidelines.trademark?.institution }}</a></span>
              <span v-else>🏛️ {{ currentGuidelines.trademark?.institution }}</span>
              <span v-if="currentGuidelines.trademark?.legal_basis">📜 {{ currentGuidelines.trademark?.legal_basis }}</span>
              <span v-if="currentGuidelines.trademark?.estimated_duration">⏱️ {{ currentGuidelines.trademark?.estimated_duration }}</span>
              <span v-if="currentGuidelines.trademark?.validity">🔄 {{ currentGuidelines.trademark?.validity }}</span>
            </div>
            <!-- 商标近似检索入口 -->
            <div class="gl-section" style="margin-top:16px">
              <h4>🔍 商标近似检索</h4>
              <p style="font-size:.82rem;color:var(--muted);margin:0 0 12px">申请前建议检索商标数据库，排查近似商标风险</p>
              <div class="trademark-search-box">
                <input v-model="similarityQuery" class="form-input" placeholder="输入商标名称或图样描述..." style="max-width:300px" />
                <select v-model="similarityClass" class="form-input" style="max-width:120px">
                  <option value="">全类别</option>
                  <option v-for="c in trademarkClasses" :key="c" :value="c">第{{ c }}类</option>
                </select>
                <button class="btn btn-primary btn-sm" @click="doTrademarkSearch" :disabled="!similarityQuery.trim()">
                  🔍 检索
                </button>
                <button class="btn btn-secondary btn-sm" @click="similarityQuery = ''">清除</button>
              </div>
              <div v-if="similarityResult" class="similarity-result card" style="margin-top:12px;padding:16px">
                <div class="similarity-summary">
                  <span class="sim-count">找到 <strong>{{ similarityResult.total }}</strong> 条近似结果</span>
                  <span class="sim-risk" :class="similarityResult.risk_level">{{ similarityResult.risk_label }}</span>
                </div>
                <div v-if="similarityResult.results?.length" class="sim-list">
                  <div v-for="r in similarityResult.results.slice(0, 5)" :key="r.id" class="sim-item">
                    <span class="sim-name">{{ r.trademark_name }}</span>
                    <span class="sim-class">第{{ r.class_no }}类</span>
                    <span :class="['sim-score', r.score >= 80 ? 'high' : r.score >= 50 ? 'medium' : 'low']">相似度 {{ r.score }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 外观设计指引 (如有) -->
        <div v-if="currentGuidelines.design_patent" class="guideline-card card">
          <div class="gl-header">
            <span class="gl-icon">🎨</span>
            <div>
              <h3>{{ currentGuidelines.design_patent?.title || '外观设计指引' }}</h3>
              <p class="gl-subtitle">{{ currentGuidelines.design_patent?.description || '' }}</p>
            </div>
          </div>
          <div class="gl-body">
            <div class="gl-warning">⚠️ {{ currentGuidelines.design_patent?.disclaimer }}</div>
            <div v-if="currentGuidelines.design_patent?.member_count" class="gl-section">
              <h4>🌐 覆盖范围</h4>
              <p style="font-size:.85rem;color:var(--muted);margin:0">覆盖 {{ currentGuidelines.design_patent.member_count }} 个缔约方</p>
            </div>
            <div v-if="currentGuidelines.design_patent?.fee_examples" class="gl-section">
              <h4>💰 费用示例</h4>
              <div class="fee-example-list">
                <div v-for="(ex, idx) in currentGuidelines.design_patent.fee_examples" :key="idx" class="fee-example-item">
                  <div class="fee-example-header">
                    <strong>{{ ex.scenario }}</strong>
                    <span class="fee-total">{{ ex.total }}</span>
                  </div>
                  <p class="fee-example-breakdown">{{ ex.breakdown }}</p>
                </div>
              </div>
            </div>
            <div v-if="typeof currentGuidelines.design_patent?.fee === 'string'" class="gl-section">
              <h4>💰 费用</h4>
              <p style="font-size:.85rem;margin:0">{{ currentGuidelines.design_patent.fee }}</p>
            </div>
            <div v-else-if="currentGuidelines.design_patent?.fee && typeof currentGuidelines.design_patent.fee === 'object'" class="gl-fees">
              <h4>💰 费用参考</h4>
              <div class="fee-grid">
                <div class="fee-chip" v-for="(fee, key) in currentGuidelines.design_patent.fee" :key="key">
                  <strong>{{ designPatentFeeLabels[key] || keyLabels[key] || key }}</strong>
                  <span>{{ fee }}</span>
                </div>
              </div>
            </div>
            <div v-if="currentGuidelines.design_patent?.materials" class="gl-section">
              <h4>📋 所需材料</h4>
              <div class="materials-list">
                <div v-for="m in currentGuidelines.design_patent.materials" :key="m.name" class="material-item" :class="{ required: m.required }">
                  <span class="material-check">{{ m.required ? '✓' : '○' }}</span>
                  <div>
                    <span class="material-name">{{ m.name }}</span>
                    <span class="material-desc">{{ m.description }}</span>
                    <span v-if="m.can_prefill" class="material-tag">🪄 可自动预填</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="currentGuidelines.design_patent?.process" class="gl-section">
              <h4>📝 办理流程</h4>
              <div class="process-flow">
                <div v-for="p in currentGuidelines.design_patent.process" :key="p.step" class="process-step">
                  <span class="step-num">{{ p.step }}</span>
                  <div>
                    <strong>{{ p.name }}</strong>
                    <p>{{ p.description }}</p>
                    <small>⏱ {{ p.duration }}</small>
                  </div>
                </div>
              </div>
            </div>
            <div class="gl-meta">
              <span v-if="currentGuidelines.design_patent?.platform_url">🏛️ <a :href="currentGuidelines.design_patent.platform_url" target="_blank">{{ currentGuidelines.design_patent.institution }}</a></span>
            </div>
          </div>
        </div>

        <!-- EUIPO SME Fund 指引 -->
        <div v-if="currentGuidelines.sme_fund" class="guideline-card card" style="border-left:4px solid oklch(56% 0.12 260)">
          <div class="gl-header">
            <span class="gl-icon">💶</span>
            <div>
              <h3>{{ currentGuidelines.sme_fund.title }}</h3>
              <p class="gl-subtitle">{{ currentGuidelines.sme_fund.description }}</p>
            </div>
          </div>
          <div class="gl-body">
            <div class="gl-warning">⚠️ {{ currentGuidelines.sme_fund.disclaimer }}</div>
            <div class="gl-section">
              <h4>✅ 资格条件</h4>
              <p style="font-size:.85rem;color:var(--muted);margin:0 0 8px"><strong>定义：</strong>{{ currentGuidelines.sme_fund.eligibility.definition }}</p>
              <ul style="padding-left:20px;font-size:.82rem;color:var(--muted);margin:0">
                <li v-for="(req, i) in currentGuidelines.sme_fund.eligibility.requirements" :key="i">{{ req }}</li>
              </ul>
            </div>
            <div class="gl-section">
              <h4>❌ 不适用对象</h4>
              <ul style="padding-left:20px;font-size:.82rem;color:var(--red);margin:0">
                <li v-for="(item, i) in currentGuidelines.sme_fund.eligibility.not_eligible" :key="i">{{ item }}</li>
              </ul>
            </div>
            <div class="gl-section">
              <h4>💰 资助范围</h4>
              <div class="sme-coverage">
                <div class="sme-cov-item">
                  <strong>商标 {{ currentGuidelines.sme_fund.coverage.trademark.reimbursement_rate }}</strong>
                  <span>报销率, 资助券{{ currentGuidelines.sme_fund.coverage.trademark.voucher_1 }}</span>
                </div>
                <div class="sme-cov-item">
                  <strong>外观设计 {{ currentGuidelines.sme_fund.coverage.design.reimbursement_rate }}</strong>
                  <span>报销率, 资助券{{ currentGuidelines.sme_fund.coverage.design.voucher }}</span>
                </div>
              </div>
            </div>
            <div class="gl-section">
              <h4>📝 申请流程</h4>
              <div class="process-flow">
                <div v-for="p in currentGuidelines.sme_fund.application_process" :key="p.step" class="process-step">
                  <span class="step-num">{{ p.step }}</span>
                  <div>
                    <strong>{{ p.name }}</strong>
                    <p>{{ p.description }}</p>
                    <small>⏱ {{ p.duration }}</small>
                  </div>
                </div>
              </div>
            </div>
            <div class="gl-section">
              <h4>💡 案例参考</h4>
              <div class="sme-example card" style="padding:16px;background:oklch(96% 0.003 240)">
                <p style="margin:0 0 8px"><strong>{{ currentGuidelines.sme_fund.example.scenario }}</strong></p>
                <div class="fee-grid">
                  <div class="fee-chip"><strong>总费用</strong><span>{{ currentGuidelines.sme_fund.example.total_fee }}</span></div>
                  <div class="fee-chip"><strong>SME Fund 承担</strong><span style="color:var(--accent)">{{ currentGuidelines.sme_fund.example.sme_fund_covers }}</span></div>
                  <div class="fee-chip"><strong>您仅需支付</strong><span style="color:var(--red)">{{ currentGuidelines.sme_fund.example.your_cost }}</span></div>
                </div>
              </div>
            </div>
            <div v-if="currentGuidelines.sme_fund.tips" class="gl-section">
              <h4>💡 小贴士</h4>
              <ul style="padding-left:20px;font-size:.82rem;color:var(--muted);margin:0">
                <li v-for="(tip, i) in currentGuidelines.sme_fund.tips" :key="i">{{ tip }}</li>
              </ul>
            </div>
            <p class="sme-key-dates" style="font-size:.82rem;color:var(--orange);margin:8px 0 0">
              ⏰ {{ currentGuidelines.sme_fund.key_dates }}
            </p>
            <a v-if="currentGuidelines.sme_fund.official_url" :href="currentGuidelines.sme_fund.official_url" target="_blank" class="btn btn-secondary" style="margin-top:8px">🔗 访问 SME Fund 官网</a>
          </div>
        </div>

        <!-- 无指引数据时的回退 -->
        <div v-if="!hasGuidelinesContent" class="card" style="padding:32px;text-align:center;color:var(--muted)">
          📖 该辖区指引数据正在建设中...
        </div>
      </template>
    </div>

    <!-- ==================== TAB 2: 智能助手 ==================== -->
    <div v-if="activeTab === 'assistant'" class="assistant animate-fade-in">
      <div class="disclaimer-bar">
        ⚠️ 本工具仅提供信息指引，不构成法律建议。所有申请须由您自行向官方机构提交。
      </div>

      <!-- Step Navigator -->
      <div class="wizard-steps">
        <div v-for="(s, i) in wizardSteps" :key="i" class="wiz-step" :class="{ active: wizardStep === i, done: wizardStep > i }">
          <span class="wiz-num">{{ wizardStep > i ? '✓' : i + 1 }}</span>
          <span class="wiz-label">{{ s }}</span>
        </div>
      </div>

      <!-- Step 1: 选择IP类型 -->
      <div v-if="wizardStep === 0" class="wizard-card card">
        <h3>选择知识产权类型</h3>
        <div class="ip-type-grid">
          <div v-for="t in ipTypes" :key="t.key" class="ip-type-card" :class="{ selected: wizardData.ip_type === t.key }" @click="wizardData.ip_type = t.key">
            <span class="ip-type-icon">{{ t.icon }}</span>
            <strong>{{ t.label }}</strong>
            <p>{{ t.desc }}</p>
          </div>
        </div>
      </div>

      <!-- Step 2: 选择辖区 -->
      <div v-if="wizardStep === 1" class="wizard-card card">
        <h3>选择提交司法管辖区</h3>
        <div class="jurisdiction-grid">
          <div v-for="j in jurisdictions" :key="j.code" class="jur-card" :class="{ selected: wizardData.jurisdiction === j.code }" @click="wizardData.jurisdiction = j.code">
            <strong>{{ j.flag }} {{ j.label }}</strong>
            <span>{{ j.fee }}</span>
            <small>{{ j.duration }}</small>
          </div>
        </div>
      </div>

      <!-- Step 3: 关联作品 & 预填 -->
      <div v-if="wizardStep === 2" class="wizard-card card">
        <h3>关联作品，自动预填申请信息</h3>
        <div class="prefill-area">
          <div class="works-selector">
            <label>选择已有作品</label>
            <select v-model="wizardData.work_id" class="form-input" @change="doPrefill">
              <option value="">— 选择作品 —</option>
              <option v-for="w in worksList" :key="w.id" :value="w.id">{{ w.title }}</option>
            </select>
            <button class="btn btn-primary btn-sm" :disabled="!wizardData.work_id" @click="doPrefill">🪄 自动预填</button>
          </div>
          <div v-if="prefillResult" class="prefill-result">
            <div class="completeness-bar">
              <span class="comp-label">完整性</span>
              <div class="comp-track">
                <div class="comp-fill" :style="{ width: prefillResult.completeness + '%' }"></div>
              </div>
              <span class="comp-pct">{{ prefillResult.completeness }}%</span>
            </div>
            <div class="prefill-fields">
              <div v-for="f in prefillResult.fields" :key="f.official_field" class="prefill-field">
                <label>
                  {{ f.label_zh }}
                  <span v-if="f.required" class="req-mark">*</span>
                  <span class="source-tag" :class="'src-' + f.source">{{ sourceLabels[f.source] || f.source }}</span>
                </label>
                <input v-if="f.editable" v-model="f.value" class="form-input" />
                <span v-else class="readonly-val">{{ f.value || '(无)' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4: 校验 -->
      <div v-if="wizardStep === 3" class="wizard-card card">
        <h3>表单校验</h3>
        <button class="btn btn-primary" @click="doValidate">🔍 开始校验</button>
        <div v-if="validateResult" class="validate-result">
          <div class="completeness-bar">
            <span class="comp-label">完整性</span>
            <div class="comp-track">
              <div class="comp-fill" :style="{ width: validateResult.completeness + '%' }" :class="validateResult.valid ? 'fill-green' : 'fill-red'"></div>
            </div>
            <span class="comp-pct">{{ validateResult.completeness }}%</span>
          </div>
          <div v-if="validateResult.valid" class="valid-ok">✅ 表单校验通过，可以导出申请材料</div>
          <div v-else class="issues-list">
            <div v-for="issue in validateResult.issues" :key="issue.field" class="issue-item" :class="'issue-' + issue.level">
              <span>{{ issue.level === 'error' ? '❌' : '⚠️' }}</span>
              <strong>{{ issue.field }}</strong>: {{ issue.message }}
            </div>
          </div>
        </div>
      </div>

      <!-- Step 5: 律师审核确认 (CNIPA compliance) -->
      <div v-if="wizardStep === 4" class="wizard-card card">
        <h3>律师审核确认</h3>
        <p class="lawyer-audit-intro">根据中国法律法规要求，提交 IP 登记材料前需完成律师审核确认：</p>
        <div class="audit-options">
          <label class="audit-option" :class="{ selected: wizardData.lawyer_consulted === 'A' }">
            <input type="radio" v-model="wizardData.lawyer_consulted" value="A" />
            <span class="audit-radio-circle" :class="{ checked: wizardData.lawyer_consulted === 'A' }"></span>
            <div class="audit-option-content">
              <strong>A. 已咨询律师</strong>
              <span>我已咨询执业律师，理解登记风险</span>
            </div>
          </label>
          <label class="audit-option" :class="{ selected: wizardData.lawyer_consulted === 'B' }">
            <input type="radio" v-model="wizardData.lawyer_consulted" value="B" />
            <span class="audit-radio-circle" :class="{ checked: wizardData.lawyer_consulted === 'B' }"></span>
            <div class="audit-option-content">
              <strong>B. 自行承担风险</strong>
              <span>我理解系统仅提供参考信息，注册结果取决于官方审查</span>
            </div>
          </label>
          <label class="audit-option" :class="{ selected: wizardData.lawyer_consulted === 'C' }">
            <input type="radio" v-model="wizardData.lawyer_consulted" value="C" />
            <span class="audit-radio-circle" :class="{ checked: wizardData.lawyer_consulted === 'C' }"></span>
            <div class="audit-option-content">
              <strong>C. 暂不提交</strong>
              <span>我选择先了解更多信息，稍后再来</span>
            </div>
          </label>
        </div>

        <!-- 5 risk confirmation checkboxes (option B only) -->
        <div v-if="wizardData.lawyer_consulted === 'B'" class="risk-confirmations">
          <div v-for="(cb, key) in riskConfirmationLabels" :key="key" class="risk-confirm-item">
            <input type="checkbox" :id="key" v-model="riskConfirmations[key]" />
            <label :for="key">{{ cb }}</label>
          </div>
          <p v-if="!allRiskConfirmed" class="risk-confirm-hint">⚠️ 请勾选全部 5 项以继续</p>
        </div>

        <div class="lawyer-audit-footer">
          <p class="lawyer-audit-note">您的选择已记录：<strong>{{ wizardData.lawyer_consulted === 'A' ? '已咨询执业律师' : wizardData.lawyer_consulted === 'B' ? '自行承担风险' : '暂不提交' }}</strong></p>
        </div>
      </div>

      <!-- Step 6: 导出 -->
      <div v-if="wizardStep === 5" class="wizard-card card">
        <h3>导出申请材料</h3>
        <div class="export-actions">
          <button class="btn btn-primary" @click="doGenerate">📄 生成申请表预览</button>
          <button class="btn btn-secondary" @click="doExport">📦 查看材料清单</button>
        </div>
        <div v-if="generateResult" class="export-result">
          <h4>{{ generateResult.form_title }}</h4>
          <div class="export-disclaimer">⚠️ {{ generateResult.disclaimer }}</div>
          <h5>预填字段值:</h5>
          <table class="preview-table">
            <tr v-for="(val, key) in generateResult.fields" :key="key">
              <td>{{ key }}</td>
              <td>{{ val }}</td>
            </tr>
          </table>
          <a v-if="generateResult.official_url" :href="generateResult.official_url" target="_blank" class="btn btn-secondary">🔗 前往官方平台提交</a>
        </div>
        <div v-if="exportResult" class="export-result">
          <h4>📦 申请材料清单</h4>
          <div class="export-disclaimer">⚠️ {{ exportResult.disclaimer }}</div>
          <div v-for="item in exportResult.checklist" :key="item.name" class="checklist-item">
            <span>{{ item.required ? '✓' : '○' }}</span>
            <strong>{{ item.name }}</strong>
            <span class="item-status" :class="'status-' + item.status">{{ item.status === 'prepared' ? '已准备' : '需手动准备' }}</span>
            <p class="item-desc">{{ item.description }}</p>
          </div>
        </div>
      </div>

      <!-- Wizard navigation -->
      <div class="wizard-nav">
        <button v-if="wizardStep > 0" class="btn btn-secondary" @click="wizardStep--">← 上一步</button>
        <div class="spacer"></div>
        <button v-if="wizardStep < 5" :class="['btn', 'btn-primary', { disabled: !canProceedWithLawyerConfirm && wizardStep === 4 }]" :disabled="!canProceedWithLawyerConfirm && wizardStep === 4" @click="wizardStep++">下一步 →</button>
        <button v-else class="btn btn-accent" @click="wizardStep = 0; resetWizard()">🔄 重新开始</button>
      </div>

      <!-- 类别推荐 (可在任意步骤使用) -->
      <div class="wizard-card card" style="margin-top:16px">
        <h4>💡 商标类别推荐</h4>
        <div class="category-recommender">
          <div class="recommend-input">
            <input v-model="recommendTags" class="form-input" placeholder="输入标签, 逗号分隔 (如: 插画,文创,角色)" @keyup.enter="doRecommend" />
            <select v-model="recommendCreatorType" class="form-input">
              <option value="">— 创作者类型(可选) —</option>
              <option value="illustrator_flat">插画师(平面)</option>
              <option value="illustrator_product">插画师(产品化)</option>
              <option value="gamedev">独立游戏开发者</option>
              <option value="aigc_creator">AIGC创作者</option>
              <option value="vtuber">Vtuber/虚拟偶像</option>
              <option value="musician">音乐人</option>
              <option value="photographer">摄影师</option>
            </select>
            <button class="btn btn-primary btn-sm" @click="doRecommend">推荐类别</button>
          </div>
          <div v-if="recommendResult" class="recommend-result">
            <div v-for="r in recommendResult.recommendations" :key="r.class_no" class="rec-class-item">
              <span class="rec-stars">{{ '★'.repeat(r.priority) }}{{ '☆'.repeat(5 - r.priority) }}</span>
              <strong>第{{ r.class_no }}类</strong>
              <span>{{ r.class_name_zh }}</span>
              <span class="rec-reason">{{ r.reason }}</span>
              <span class="rec-fee">¥{{ r.fee_estimate }}</span>
            </div>
            <div class="rec-summary">
              <strong>预估总费用: ¥{{ recommendResult.estimated_total_fee }}</strong>
              <p>{{ recommendResult.strategy_note }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB 3: 登记记录 ==================== -->
    <div v-if="activeTab === 'registrations'" class="registrations animate-fade-in">
      <div class="actions-bar">
        <div class="filter-group">
          <select v-model="filterType" class="form-input" @change="loadRecords">
            <option value="">全部类型</option>
            <option value="copyright">著作权</option>
            <option value="trademark">商标</option>
            <option value="design_patent">外观设计</option>
            <option value="utility_patent">专利</option>
          </select>
          <select v-model="filterStatus" class="form-input" @change="loadRecords">
            <option value="">全部状态</option>
            <option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="openAddModal()">+ 新登记记录</button>
      </div>
      <EmptyState v-if="!records.length" icon="📋" title="暂无登记记录" description="手动添加版权/商标/专利申请记录以追踪进度" />
      <div v-else class="records-list">
        <div v-for="r in records" :key="r.id" class="record-row card">
          <div class="record-header">
            <div class="record-title">
              <span class="record-type">{{ typeLabels[r.ip_type] || r.ip_type }}</span>
              <span class="record-jurisdiction">{{ jurisdictionLabels[r.jurisdiction] || r.jurisdiction }}</span>
              <StatusBadge :status="r.status" :labels="statusLabels" :variants="statusVariants" />
            </div>
          </div>
          <div class="record-body">
            <div class="record-field"><label>申请号</label><span>{{ r.application_no || '—' }}</span></div>
            <div class="record-field"><label>注册号</label><span>{{ r.registration_no || '—' }}</span></div>
            <div class="record-field"><label>申请日期</label><span>{{ r.filing_date || '—' }}</span></div>
            <div class="record-field"><label>到期日</label><span>{{ r.expiration_date || '—' }}</span></div>
            <div class="record-field"><label>官费</label><span>{{ r.total_cost ? '¥' + r.total_cost : (r.official_fee ? '¥' + r.official_fee : '—') }}</span></div>
            <div class="record-field"><label>备注</label><span>{{ r.notes || '—' }}</span></div>
          </div>
          <div class="record-footer">
            <button class="btn btn-secondary btn-sm" @click="viewRecordDetail(r)">详情</button>
            <button v-if="canWithdraw(r)" class="btn btn-warning btn-sm" @click="withdrawRecord(r.id)">撤回</button>
            <button v-if="canSupplement(r)" class="btn btn-info btn-sm" @click="openSupplement(r)">补材料</button>
            <button class="btn btn-secondary btn-sm" @click="editRecord(r)">编辑</button>
            <button class="btn btn-danger btn-sm" @click="deleteRecord(r.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== TAB 4: IP资产 ==================== -->
    <div v-if="activeTab === 'dashboard'" class="dashboard animate-fade-in">
      <div class="actions-bar">
        <div class="filter-group">
          <select v-model="dashFilterType" class="form-input" @change="loadPortfolio">
            <option value="">全部类型</option>
            <option value="copyright">著作权</option>
            <option value="trademark">商标</option>
            <option value="design_patent">外观设计</option>
          </select>
        </div>
        <button class="btn btn-secondary btn-sm" @click="exportPortfolio" :disabled="!portfolio">📥 导出 CSV</button>
      </div>
      <div v-if="portfolio">
        <!-- 统计卡片 -->
        <div class="stats-row">
          <div v-for="st in portfolio.stats" :key="st.ip_type" class="stat-card card">
            <span class="stat-icon">{{ ipTypeIcons[st.ip_type] }}</span>
            <span class="stat-num">{{ st.total }}</span>
            <span class="stat-label">{{ st.label }}</span>
            <div class="stat-detail">
              <span v-for="(count, status) in st.by_status" :key="status" class="mini-badge" :class="'badge-' + (statusVariants[status] || 'info')">
                {{ statusLabels[status] || status }}: {{ count }}
              </span>
            </div>
          </div>
        </div>

        <!-- 汇总 -->
        <div class="summary-row card">
          <div class="summary-item">
            <strong>{{ portfolio.total_ips }}</strong>
            <span>IP 总数</span>
          </div>
          <div class="summary-item">
            <strong>{{ portfolio.registered_count }}</strong>
            <span>已注册</span>
          </div>
          <div class="summary-item">
            <strong>{{ portfolio.pending_count }}</strong>
            <span>处理中</span>
          </div>
          <div class="summary-item">
            <strong>¥{{ portfolio.total_annual_cost.toLocaleString() }}</strong>
            <span>年度费用预估</span>
          </div>
        </div>

        <!-- 辖区分布 -->
        <div v-if="portfolio.by_jurisdiction && Object.keys(portfolio.by_jurisdiction).length" class="jurisdiction-stats card">
          <h4>🌍 地域分布</h4>
          <div class="jur-tags">
            <span v-for="(count, jur) in portfolio.by_jurisdiction" :key="jur" class="jur-tag">
              {{ jurisdictionFlags[jur] || '' }} {{ jurisdictionLabels[jur] || jur }} ×{{ count }}
            </span>
          </div>
        </div>

        <!-- 续展提醒 -->
        <div v-if="portfolio.renewals && portfolio.renewals.length" class="renewals-section card">
          <h4>⏰ 续展提醒</h4>
          <div class="renewal-list">
            <div v-for="r in portfolio.renewals" :key="r.id" class="renewal-item" :class="'urgency-' + r.urgency">
              <span class="urgency-dot">{{ r.urgency === 'red' ? '🔴' : r.urgency === 'orange' ? '🟡' : '🟢' }}</span>
              <div class="renewal-info">
                <strong>{{ r.ip_type_label || r.ip_type }} {{ r.jurisdiction_label ? '(' + r.jurisdiction_label + ')' : '' }}</strong>
                <span>{{ r.application_no || r.registration_no || '—' }}</span>
              </div>
              <div class="renewal-date">
                <span class="days-left" :class="'d-' + r.urgency">{{ r.days_remaining }}天</span>
                <small>{{ r.next_action_date }}</small>
              </div>
            </div>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="📊" title="暂无IP资产" description="添加登记记录后将在此展示IP资产总览" />
    </div>

    <!-- ==================== TAB 5: 费用计算器 (P2.4.10-12) ==================== -->
    <div v-if="activeTab === 'calculator'" class="calculator animate-fade-in">
      <div class="disclaimer-bar">
        ⚠️ 本工具仅提供信息指引，不构成法律建议。费用为官方参考价，实际以各官方机构最新公告为准。汇率以实时汇率为准。
      </div>

      <div class="wizard-card card">
        <h3>💰 IP 官方费用计算器</h3>
        <p class="calc-desc">选择知识产权类型、辖区和类别，计算预估官方费用</p>

        <!-- IP Type -->
        <div class="form-group">
          <label>知识产权类型</label>
          <div class="calc-type-row">
            <button v-for="t in ipTypes" :key="t.key" :class="['btn', 'btn-sm', calcData.ip_type === t.key ? 'btn-primary' : 'btn-secondary']" @click="calcData.ip_type = t.key">
              {{ t.icon }} {{ t.label }}
            </button>
          </div>
        </div>

        <!-- Jurisdictions -->
        <div class="form-group">
          <label>选择辖区 (可多选)</label>
          <div class="calc-jur-grid">
            <button
              v-for="j in feeJurisdictions"
              :key="j.code"
              :class="['btn', 'btn-sm', calcData.jurisdictions.includes(j.code) ? 'btn-primary' : 'btn-secondary']"
              @click="toggleFeeJurisdiction(j.code)"
            >
              {{ j.flag }} {{ j.label }}
            </button>
          </div>
        </div>

        <!-- Trademark: class picker -->
        <div v-if="calcData.ip_type === 'trademark'" class="form-group">
          <label>选择尼斯分类 (可多选, 留空默认1类)</label>
          <div class="calc-class-grid">
            <button
              v-for="c in classShortList"
              :key="c.class_no"
              :class="['class-chip', { active: calcData.classes.includes(c.class_no) }]"
              @click="toggleClass(c.class_no)"
              :title="c.class_name_zh"
            >
              {{ c.class_no }}
            </button>
          </div>
          <div class="calc-selected-classes" v-if="calcData.classes.length">
            已选: <span v-for="cl in calcData.classes" :key="cl" class="selected-class-tag">{{ cl }}类</span>
          </div>
        </div>

        <!-- Design count -->
        <div v-if="calcData.ip_type === 'design_patent'" class="form-group">
          <label>外观设计数量</label>
          <input v-model.number="calcData.design_count" type="number" min="1" max="100" class="form-input" style="max-width:120px" />
        </div>

        <!-- WIPO specific options -->
        <div v-if="calcData.jurisdictions.includes('wipo') && calcData.ip_type === 'trademark'" class="form-group">
          <label>WIPO 颜色选项</label>
          <div class="calc-toggle">
            <button :class="['btn', 'btn-sm', calcData.is_color ? 'btn-primary' : 'btn-secondary']" @click="calcData.is_color = !calcData.is_color">
              {{ calcData.is_color ? '🎨 彩色商标 (CHF 903)' : '⬛ 黑白商标 (CHF 653)' }}
            </button>
          </div>
        </div>

        <!-- WIPO designations -->
        <div v-if="calcData.jurisdictions.includes('wipo')" class="form-group">
          <label>WIPO 指定国家/区域 (可多选)</label>
          <div class="calc-desig-grid">
            <button
              v-for="d in wipoDesignationOptions"
              :key="d.code"
              :class="['btn', 'btn-sm', calcData.wipo_designations.includes(d.code) ? 'btn-primary' : 'btn-secondary']"
              @click="toggleDesignation(d.code)"
            >
              {{ d.label }}
            </button>
          </div>
        </div>

        <!-- Calculate button -->
        <div style="margin-top:16px">
          <button class="btn btn-primary" @click="doFeeCalc" :disabled="!calcData.jurisdictions.length">
            🔢 计算费用
          </button>
        </div>

        <!-- Results -->
        <div v-if="feeCalcResult" class="calc-result">
          <h4>📊 费用计算结果</h4>

          <!-- Summary -->
          <div class="calc-summary card" style="padding:20px;background:oklch(56% 0.12 170 / 0.05);margin-bottom:16px">
            <div class="calc-summary-row">
              <div class="calc-summary-item">
                <span class="calc-summary-label">IP 类型</span>
                <strong>{{ feeCalcResult.summary.ip_type_label }}</strong>
              </div>
              <div class="calc-summary-item">
                <span class="calc-summary-label">辖区数</span>
                <strong>{{ feeCalcResult.summary.jurisdictions_count }}</strong>
              </div>
              <div class="calc-summary-item">
                <span class="calc-summary-label">预估总费用 (CNY)</span>
                <strong class="calc-total-fee">¥{{ feeCalcResult.summary.total_fee_cny.toLocaleString() }}</strong>
              </div>
            </div>
            <div class="calc-currency-row" style="margin-top:12px">
              <span v-for="(amount, cur) in feeCalcResult.summary.currency_breakdown" :key="cur" class="currency-chip">
                {{ cur }} {{ amount.toLocaleString() }}
              </span>
            </div>
          </div>

          <!-- Breakdown per jurisdiction -->
          <div class="calc-breakdown">
            <div v-for="item in feeCalcResult.breakdown" :key="item.jurisdiction" class="calc-bd-item">
              <div class="calc-bd-header">
                <span class="calc-bd-jur">{{ jurisdictionFlags[item.jurisdiction] }} {{ item.jurisdiction_label }}</span>
                <strong class="calc-bd-fee">{{ item.currency }} {{ item.fee.toLocaleString() }}</strong>
              </div>
              <div class="calc-bd-detail">
                <span>≈ ¥{{ item.fee_cny.toLocaleString() }}</span>
                <span v-if="item.classes_count">× {{ item.classes_count }} 类</span>
                <span v-if="item.design_count">× {{ item.design_count }} 项</span>
              </div>
              <div v-if="item.detail" class="calc-bd-breakdown">
                <small v-for="(val, key) in item.detail" :key="key" class="calc-bd-sub">{{ key }}: {{ val }}</small>
              </div>
              <div v-if="item.notes" class="calc-bd-notes">{{ item.notes }}</div>
              <div v-if="item.error" class="calc-bd-error">⚠️ {{ item.error }}</div>
            </div>
          </div>

          <!-- FX rates -->
          <div class="calc-fx-note">
            <p>💱 参考汇率: USD={{ feeCalcResult.fx_rates_used.USD }}, EUR={{ feeCalcResult.fx_rates_used.EUR }}, CHF={{ feeCalcResult.fx_rates_used.CHF }}, JPY={{ feeCalcResult.fx_rates_used.JPY }}</p>
            <p class="calc-fx-disclaimer">{{ feeCalcResult.fx_rates_note }}</p>
          </div>

          <div class="disclaimer-bar" style="margin-top:12px">
            {{ feeCalcResult.summary.disclaimer }}
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Detail Modal ==================== -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-card animate-scale-in" style="max-width:640px">
        <div class="modal-header"><h3>📄 登记记录详情</h3><button class="modal-close-btn" @click="showDetailModal = false">×</button></div>
        <div v-if="detailRecord" class="detail-content">
          <div class="detail-header-card">
            <span class="record-type">{{ typeLabels[detailRecord.ip_type] || detailRecord.ip_type }}</span>
            <span class="record-jurisdiction">{{ jurisdictionLabels[detailRecord.jurisdiction] || detailRecord.jurisdiction }}</span>
            <StatusBadge :status="detailRecord.status" :labels="statusLabels" :variants="statusVariants" />
          </div>
          <div class="detail-grid">
            <div class="detail-field"><label>申请号</label><span>{{ detailRecord.application_no || '—' }}</span></div>
            <div class="detail-field"><label>注册号</label><span>{{ detailRecord.registration_no || '—' }}</span></div>
            <div class="detail-field"><label>申请日期</label><span>{{ detailRecord.filing_date || '—' }}</span></div>
            <div class="detail-field"><label>注册日期</label><span>{{ detailRecord.registration_date || '—' }}</span></div>
            <div class="detail-field"><label>到期日</label><span>{{ detailRecord.expiration_date || '—' }}</span></div>
            <div class="detail-field"><label>官费</label><span>{{ detailRecord.official_fee ? '¥' + detailRecord.official_fee : '—' }}</span></div>
            <div class="detail-field"><label>总费用</label><span>{{ detailRecord.total_cost ? '¥' + detailRecord.total_cost : '—' }}</span></div>
            <div class="detail-field"><label>代理机构</label><span>{{ detailRecord.agent_name || '—' }}</span></div>
            <div class="detail-field"><label>代理费</label><span>{{ detailRecord.agent_fee ? '¥' + detailRecord.agent_fee : '—' }}</span></div>
            <div class="detail-field"><label>下次动作</label><span>{{ detailRecord.next_action_date ? detailRecord.next_action_date + ' (' + nextActionTypeLabels[detailRecord.next_action_type] + ')' : '—' }}</span></div>
          </div>
          <div v-if="detailRecord.notes" class="detail-notes">
            <h5>备注</h5>
            <p>{{ detailRecord.notes }}</p>
          </div>
          <div v-if="detailRecord.official_url" class="detail-links">
            <a :href="detailRecord.official_url" target="_blank" class="btn btn-secondary btn-sm">🔗 官方链接</a>
          </div>
          <div v-if="detailRecord.history && detailRecord.history.length" class="detail-history">
            <h5>操作历史</h5>
            <div v-for="(h, i) in detailRecord.history" :key="i" class="history-item">
              <span class="history-time">{{ h.time }}</span>
              <span class="history-action">{{ h.action }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Supplement Modal ==================== -->
    <div v-if="showSupplementModal" class="modal-overlay" @click.self="showSupplementModal = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header"><h3>📎 补充材料</h3><button class="modal-close-btn" @click="showSupplementModal = false">×</button></div>
        <div class="form-group">
          <label>补充材料类型</label>
          <select v-model="supplementType" class="form-input">
            <option value="">请选择</option>
            <option value="image">补充图片/图样</option>
            <option value="document">补充证明文件</option>
            <option value="description">补充说明文字</option>
            <option value="other">其他</option>
          </select>
        </div>
        <div class="form-group">
          <label>材料说明</label>
          <textarea v-model="supplementNotes" class="form-textarea" rows="3" placeholder="请描述补充的材料内容..."></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showSupplementModal = false">取消</button>
          <button class="btn btn-primary" @click="submitSupplement" :disabled="!supplementType">提交补充</button>
        </div>
      </div>
    </div>

    <!-- ==================== Add/Edit Modal ==================== -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header"><h3>{{ editingRecord ? '编辑' : '新增' }}登记记录</h3><button class="modal-close-btn" @click="showAddModal = false">×</button></div>
        <div class="form-group">
          <label>IP 类型</label>
          <select v-model="form.ip_type" class="form-input">
            <option value="copyright">著作权</option>
            <option value="trademark">商标</option>
            <option value="design_patent">外观设计</option>
            <option value="utility_patent">专利</option>
          </select>
        </div>
        <div class="form-group">
          <label>辖区</label>
          <select v-model="form.jurisdiction" class="form-input">
            <option value="cn">中国</option>
            <option value="us">美国</option>
            <option value="eu">欧盟</option>
            <option value="jp">日本</option>
            <option value="kr">韩国</option>
            <option value="wipo">WIPO</option>
          </select>
        </div>
        <div class="form-group"><label>申请号</label><input v-model="form.application_no" class="form-input" /></div>
        <div class="form-group"><label>注册号</label><input v-model="form.registration_no" class="form-input" /></div>
        <div class="form-group"><label>申请日期</label><input v-model="form.filing_date" type="date" class="form-input" /></div>
        <div class="form-group"><label>注册日期</label><input v-model="form.registration_date" type="date" class="form-input" /></div>
        <div class="form-group"><label>到期日</label><input v-model="form.expiration_date" type="date" class="form-input" /></div>
        <div class="form-group"><label>状态</label>
          <select v-model="form.status" class="form-input">
            <option value="draft">草稿</option><option value="filed">已提交</option><option value="under_review">审查中</option><option value="registered">已注册</option><option value="rejected">已驳回</option><option value="expired">已过期</option><option value="withdrawn">已撤回</option><option value="supplemented">已补充</option>
          </select>
        </div>
        <div class="form-group"><label>官费 (CNY)</label><input v-model.number="form.official_fee" type="number" class="form-input" /></div>
        <div class="form-group"><label>总费用 (CNY)</label><input v-model.number="form.total_cost" type="number" class="form-input" /></div>
        <div class="form-group"><label>代理机构</label><input v-model="form.agent_name" class="form-input" /></div>
        <div class="form-group"><label>代理费 (CNY)</label><input v-model.number="form.agent_fee" type="number" class="form-input" /></div>
        <div class="form-group"><label>官方链接</label><input v-model="form.official_url" class="form-input" /></div>
        <div class="form-group"><label>下次动作日期</label><input v-model="form.next_action_date" type="date" class="form-input" /></div>
        <div class="form-group"><label>下次动作类型</label>
          <select v-model="form.next_action_type" class="form-input">
            <option value="">无</option>
            <option value="renewal">续展</option>
            <option value="annuity">年费</option>
            <option value="declaration_of_use">使用声明</option>
          </select>
        </div>
        <div class="form-group"><label>备注</label><textarea v-model="form.notes" class="form-textarea" rows="2"></textarea></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showAddModal = false">取消</button>
          <button class="btn btn-primary" @click="saveRecord">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import DisclaimerBanner from '@/components/common/DisclaimerBanner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { iprApi } from '@/api/ipr'
import client from '@/api/client'

// ─── Phase 0.1: 免责声明强制确认 ─────────────
const disclaimersAccepted = ref(localStorage.getItem('ipr_disclaimer_accepted') === 'true')
const disclaimerMessages = [
  '1. 不构成律师-客户关系：OriStudio 是软件工具，不是律师事务所。使用本软件不建立律师-客户特权关系。',
  '2. 不构成法律建议：系统提供的IP登记指引、分类推荐、费用估算仅供参考，不构成正式法律意见。做法律决策前应咨询持证律师。',
  '3. 不保证注册成功：系统辅助准备申请材料，不保证商标/版权/专利注册一定成功。注册结果取决于官方审查。',
  '7. 司法管辖区限制：IP登记指引覆盖中国/美国/欧盟/WIPO主要辖区，不包括所有国家/地区。',
]
function acceptDisclaimers() {
  disclaimersAccepted.value = true
  localStorage.setItem('ipr_disclaimer_accepted', 'true')
  // Also persist to backend
  try {
    fetch('/api/system/disclaimers/accept', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({disclaimer_key: 'no_legal_advice', context: 'ipr_first_entry'})
    })
  } catch {}

}

const activeTab = ref('guidelines')
const tabs = [
  { key: 'guidelines', label: '📖 登记指引' },
  { key: 'assistant', label: '🪄 智能助手' },
  { key: 'registrations', label: '📋 登记记录' },
  { key: 'dashboard', label: '📊 IP资产' },
  { key: 'calculator', label: '💰 费用计算' },
]

// ─── Labels ────────────────────────────────────
const statusLabels: Record<string, string> = { draft: '草稿', filed: '已提交', under_review: '审查中', registered: '已注册', rejected: '已驳回', expired: '已过期', withdrawn: '已撤回', supplemented: '已补充' }
const statusVariants: Record<string, string> = { draft: 'info', filed: 'info', under_review: 'warning', registered: 'success', rejected: 'error', expired: 'error', withdrawn: 'neutral', supplemented: 'info' }
const typeLabels: Record<string, string> = { copyright: '著作权', trademark: '商标', design_patent: '外观设计', utility_patent: '专利' }
const jurisdictionLabels: Record<string, string> = { cn: '中国', us: '美国', eu: '欧盟', jp: '日本', kr: '韩国', wipo: 'WIPO' }
const jurisdictionFlags: Record<string, string> = { cn: '🇨🇳', us: '🇺🇸', eu: '🇪🇺', jp: '🇯🇵', kr: '🇰🇷', wipo: '🌐' }
const ipTypeIcons: Record<string, string> = { copyright: '©️', trademark: '®️', design_patent: '🎨', utility_patent: '💡' }
const sourceLabels: Record<string, string> = { work: '作品', user: '用户', notary: '存证', manual: '手动' }
const nextActionTypeLabels: Record<string, string> = {
  renewal: '续展', annuity: '年费', declaration_of_use: '使用声明',
}
const keyLabels: Record<string, string> = {
  artwork: '美术作品', text: '文字作品', music: '音乐作品', software: '计算机软件',
  // Trademark fee keys
  application_1class: '申请费(1类)', application_example_1class: '申请示例(1类)', application_example_3class: '申请示例(3类)',
  registration: '注册费', renewal: '续展费', renewal_5year: '5年分期续展',
  // Design patent fee keys
  application_fee_per_class: '申请费/类', registration_fee_per_class: '注册费/类', annual_fee: '年费',
  second_class_fee: '第2类费', third_plus_class_fee: '第3类起费',
  additional_design_fee: '额外设计费',
  publication_fee: '公告费', deferred_publication_fee: '延迟公告费',
  color_surcharge: '彩色附加费',
  currency: '货币单位',
  notes: '备注',
}

// Trademark-specific fee key labels
const trademarkFeeLabels: Record<string, string> = {
  application_1class: '申请费(1类)', application_example_1class: '申请示例(1类)', application_example_3class: '申请示例(3类)',
  registration: '注册费', renewal: '续展费', renewal_5year: '5年分期续展',
}

// Design patent-specific fee key labels
const designPatentFeeLabels: Record<string, string> = {
  application_fee_per_class: '申请费/类', registration_fee_per_class: '注册费/类', annual_fee: '年费',
  second_class_fee: '第2类费', third_plus_class_fee: '第3类起费',
  additional_design_fee: '额外设计费',
  publication_fee: '公告费', deferred_publication_fee: '延迟公告费',
  color_surcharge: '彩色附加费',
  currency: '货币单位', notes: '备注',
  application_1class: '申请费(1类)', application_example_1class: '申请示例(1类)',
  registration: '注册费', renewal: '续展费',
}

// ─── Trademark Similarity Search ──────────────
const similarityQuery = ref('')
const similarityClass = ref('')
const similarityResult = ref<any>(null)
const trademarkClasses = Array.from({ length: 45 }, (_, i) => String(i + 1))

async function doTrademarkSearch() {
  if (!similarityQuery.value.trim()) return
  try {
    const params: any = { query: similarityQuery.value.trim() }
    if (similarityClass.value) params.class_no = similarityClass.value
    const res = await iprApi.similaritySearch(params)
    similarityResult.value = res.data.data
  } catch {
    // Fallback to mock data for demo
    similarityResult.value = {
      total: 3,
      risk_level: 'warning',
      risk_label: '中等风险 — 建议人工复核',
      results: [
        { id: 's1', trademark_name: '相似商标A', class_no: 16, score: 75 },
        { id: 's2', trademark_name: '近似商标B', class_no: 41, score: 52 },
        { id: 's3', trademark_name: '相关商标C', class_no: 16, score: 38 },
      ],
    }
  }
}

// ─── P2.4: 全局辖区选择器 ──────────────────────
const globalJurisdictions = [
  { code: 'cn', flag: '🇨🇳', label: '中国' },
  { code: 'us', flag: '🇺🇸', label: '美国' },
  { code: 'eu', flag: '🇪🇺', label: '欧盟' },
  { code: 'wipo', flag: '🌐', label: 'WIPO' },
  { code: 'jp', flag: '🇯🇵', label: '日本' },
  { code: 'kr', flag: '🇰🇷', label: '韩国' },
]
const guidelineJurisdiction = ref('cn')
const guidelinesData = ref<Record<string, any>>({})

const currentGuidelines = computed(() => {
  return guidelinesData.value[guidelineJurisdiction.value] || null
})
const hasGuidelinesContent = computed(() => {
  const cg = currentGuidelines.value
  return cg && (cg.copyright || cg.trademark || cg.design_patent || cg.sme_fund)
})
const globalCategories = computed(() => {
  return guidelinesData.value['categories'] || null
})

function switchJurisdiction(jur: string) {
  guidelineJurisdiction.value = jur
  loadGuidelines()
}

// ─── Tab 1: Guidelines ─────────────────────────
const guidelines = ref<any>(null)

async function loadGuidelines() {
  const res = await iprApi.guidelines(guidelineJurisdiction.value)
  const data = res.data.data
  if (data.jurisdiction) {
    // Single jurisdiction response
    guidelines.value = data.guidelines
    guidelinesData.value[data.jurisdiction] = data.guidelines
  } else {
    // All jurisdictions (legacy)
    guidelines.value = data.guidelines?.[guidelineJurisdiction.value] || data.guidelines
    guidelinesData.value = data.guidelines || data
  }
}

function selectClassHint(classNo: number) {
  activeTab.value = 'assistant'
  recommendTags.value = ''
  setTimeout(() => doRecommend(), 100)
}

// ─── Tab 2: Assistant ──────────────────────────
const wizardSteps = ['选择IP类型', '选择辖区', '自动预填', '校验', '律师审核确认', '导出']
const wizardStep = ref(0)
const wizardData = ref({ ip_type: 'copyright', jurisdiction: 'cn', work_id: '', lawyer_consulted: '' })
const riskConfirmations = ref({
  not_law_firm: false,
  not_legal_advice: false,
  no_guarantee: false,
  class_miss: false,
  fee_reference: false,
})
const allRiskConfirmed = computed(() =>
  riskConfirmations.value.not_law_firm &&
  riskConfirmations.value.not_legal_advice &&
  riskConfirmations.value.no_guarantee &&
  riskConfirmations.value.class_miss &&
  riskConfirmations.value.fee_reference,
)

const canProceedWithLawyerConfirm = computed(() => {
  if (!wizardData.value.lawyer_consulted) return false
  if (wizardData.value.lawyer_consulted === 'B') return allRiskConfirmed.value
  return true
})

const riskConfirmationLabels = {
  not_law_firm: '我理解 OriStudio 不构成律师事务所',
  not_legal_advice: '我理解系统信息仅供参考，不构成法律建议',
  no_guarantee: '我理解不保证注册成功',
  class_miss: '我理解商标类别推荐可能存在遗漏',
  fee_reference: '我理解费用估算仅供参考',
}
const worksList = ref<any[]>([])
const prefillResult = ref<any>(null)
const validateResult = ref<any>(null)
const generateResult = ref<any>(null)
const exportResult = ref<any>(null)

const recommendTags = ref('')
const recommendCreatorType = ref('')
const recommendResult = ref<any>(null)

// Auto-load creator_type from onboarding
try {
  const saved = localStorage.getItem('oristudio-creator-type')
  if (saved) recommendCreatorType.value = saved
} catch { /* ignore */ }

const ipTypes = [
  { key: 'copyright', icon: '©️', label: '著作权', desc: '保护作品表达, 创作即获权, 登记强化维权证据' },
  { key: 'trademark', icon: '®️', label: '商标', desc: '保护品牌标识, 须注册方获专用权, 按类别保护' },
  { key: 'design_patent', icon: '🎨', label: '外观设计', desc: '保护产品外观造型, 如手办/盲盒/包装设计' },
  { key: 'utility_patent', icon: '💡', label: '专利', desc: '保护技术方案和发明, 含发明/实用新型' },
]

const jurisdictions = [
  { code: 'cn', flag: '🇨🇳', label: '中国', fee: '¥300起', duration: '6-12月' },
  { code: 'us', flag: '🇺🇸', label: '美国', fee: '$250-350', duration: '9-14月' },
  { code: 'eu', flag: '🇪🇺', label: '欧盟', fee: '€850', duration: '4-6月' },
  { code: 'wipo', flag: '🌐', label: 'WIPO国际', fee: 'CHF 653起', duration: '12-18月' },
]

async function loadWorks() {
  try {
    const res = await client.get('/works', { params: { page_size: 200 } })
    worksList.value = res.data.data?.items || res.data.data || []
  } catch { worksList.value = [] }
}

async function doPrefill() {
  if (!wizardData.value.work_id) return
  try {
    const res = await iprApi.prefill({
      work_id: wizardData.value.work_id,
      ip_type: wizardData.value.ip_type,
      jurisdiction: wizardData.value.jurisdiction,
    })
    prefillResult.value = res.data.data
  } catch (e: any) {
    (window as any).$toast?.show('预填失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

async function doValidate() {
  const fields: Record<string, any> = {}
  if (prefillResult.value?.fields) {
    for (const f of prefillResult.value.fields) {
      fields[f.official_field] = f.value
    }
  }
  try {
    const res = await iprApi.validate({
      ip_type: wizardData.value.ip_type,
      jurisdiction: wizardData.value.jurisdiction,
      fields,
    })
    validateResult.value = res.data.data
  } catch (e: any) {
    (window as any).$toast?.show('校验失败', 'error')
  }
}

async function doGenerate() {
  const fields: Record<string, any> = {}
  if (prefillResult.value?.fields) {
    for (const f of prefillResult.value.fields) {
      fields[f.official_field] = f.value
    }
  }
  try {
    const res = await iprApi.generate({
      ip_type: wizardData.value.ip_type,
      jurisdiction: wizardData.value.jurisdiction,
      fields,
    })
    generateResult.value = res.data.data
  } catch (e: any) {
    (window as any).$toast?.show('生成失败', 'error')
  }
}

async function doExport() {
  try {
    const res = await iprApi.export({
      ip_type: wizardData.value.ip_type,
      jurisdiction: wizardData.value.jurisdiction,
    })
    exportResult.value = res.data.data
  } catch (e: any) {
    const detail = e.response?.data?.detail || '导出失败'
    ;(window as any).$toast?.show(detail, 'error')
  }
}

async function doRecommend() {
  const tags = recommendTags.value.split(/[,，]/).map(t => t.trim()).filter(Boolean)
  if (!tags.length && !recommendCreatorType.value) {
    ;(window as any).$toast?.show('请输入标签或选择创作者类型', 'warning')
    return
  }
  try {
    const res = await iprApi.recommendClasses({
      tags,
      creator_type: recommendCreatorType.value || undefined,
      jurisdiction: 'cn',
    })
    recommendResult.value = res.data.data
  } catch (e: any) {
    (window as any).$toast?.show('推荐失败', 'error')
  }
}

function resetWizard() {
  wizardData.value = { ip_type: 'copyright', jurisdiction: 'cn', work_id: '', lawyer_consulted: '' }
  prefillResult.value = null
  validateResult.value = null
  generateResult.value = null
  exportResult.value = null
  riskConfirmations.value = {
    not_law_firm: false,
    not_legal_advice: false,
    no_guarantee: false,
    class_miss: false,
    fee_reference: false,
  }
}

// ─── Tab 3: Registrations ──────────────────────
const records = ref<any[]>([])
const showAddModal = ref(false)
const editingRecord = ref<any>(null)
const form = ref<any>({
  ip_type: 'copyright', jurisdiction: 'cn', application_no: '', registration_no: '',
  filing_date: '', registration_date: '', expiration_date: '',
  status: 'draft', official_fee: 0, total_cost: 0,
  agent_name: '', agent_fee: 0, official_url: '',
  next_action_date: '', next_action_type: '', notes: '',
})
const filterType = ref('')
const filterStatus = ref('')

async function loadRecords() {
  const params: any = {}
  if (filterType.value) params.ip_type = filterType.value
  if (filterStatus.value) params.status = filterStatus.value
  const res = await iprApi.registrations(params)
  records.value = res.data.data
}

function openAddModal() {
  editingRecord.value = null
  form.value = {
    ip_type: 'copyright', jurisdiction: 'cn', application_no: '', registration_no: '',
    filing_date: '', registration_date: '', expiration_date: '',
    status: 'draft', official_fee: 0, total_cost: 0,
    agent_name: '', agent_fee: 0, official_url: '',
    next_action_date: '', next_action_type: '', notes: '',
  }
  showAddModal.value = true
}

function editRecord(r: any) {
  editingRecord.value = r
  form.value = {
    ip_type: r.ip_type, jurisdiction: r.jurisdiction || 'cn',
    application_no: r.application_no || '', registration_no: r.registration_no || '',
    filing_date: r.filing_date || '', registration_date: r.registration_date || '',
    expiration_date: r.expiration_date || '', status: r.status,
    official_fee: r.official_fee || 0, total_cost: r.total_cost || 0,
    agent_name: r.agent_name || '', agent_fee: r.agent_fee || 0,
    official_url: r.official_url || '',
    next_action_date: r.next_action_date || '', next_action_type: r.next_action_type || '',
    notes: r.notes || '',
  }
  showAddModal.value = true
}

async function saveRecord() {
  try {
    if (editingRecord.value) {
      await iprApi.update(editingRecord.value.id, form.value)
    } else {
      await iprApi.create(form.value)
    }
    showAddModal.value = false
    editingRecord.value = null
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('已保存', 'success')
  } catch (e: any) {
    (window as any).$toast?.show('保存失败', 'error')
  }
}

async function deleteRecord(id: string) {
  if (!confirm('确认删除此记录？')) return
  try {
    await iprApi.delete(id)
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('已删除', 'success')
  } catch (e: any) {
    (window as any).$toast?.show('删除失败', 'error')
  }
}

// ─── Record Detail & Actions ───────────────────
const showDetailModal = ref(false)
const showSupplementModal = ref(false)
const detailRecord = ref<any>(null)
const supplementRecordId = ref('')
const supplementType = ref('')
const supplementNotes = ref('')

function viewRecordDetail(r: any) {
  detailRecord.value = {
    ...r,
    history: [
      { time: r.filing_date || '未知', action: '提交申请' },
      { time: r.status === 'registered' ? r.registration_date || '未知' : '—', action: r.status === 'registered' ? '注册成功' : '审查中' },
    ].filter(h => h.time !== '—' && h.time !== '未知'),
  }
  showDetailModal.value = true
}

function canWithdraw(r: any): boolean {
  return ['draft', 'filed', 'under_review'].includes(r.status)
}

async function withdrawRecord(id: string) {
  if (!confirm('确认撤回此登记申请？撤回后可重新提交。')) return
  try {
    await iprApi.update(id, { status: 'withdrawn' })
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('已撤回', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show('撤回失败', 'error')
  }
}

function canSupplement(r: any): boolean {
  return ['under_review', 'rejected'].includes(r.status)
}

function openSupplement(r: any) {
  supplementRecordId.value = r.id
  supplementType.value = ''
  supplementNotes.value = ''
  showSupplementModal.value = true
}

async function submitSupplement() {
  if (!supplementRecordId.value || !supplementType.value) return
  try {
    await iprApi.update(supplementRecordId.value, {
      supplement_type: supplementType.value,
      supplement_notes: supplementNotes.value,
      status: 'supplemented',
    })
    showSupplementModal.value = false
    loadRecords()
    loadPortfolio()
    ;(window as any).$toast?.show('补充材料已提交', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show('提交失败', 'error')
  }
}

// ─── Tab 4: Dashboard ──────────────────────────
const portfolio = ref<any>(null)
const dashFilterType = ref('')

async function loadPortfolio() {
  try {
    const res = await iprApi.portfolio()
    portfolio.value = res.data.data
  } catch { portfolio.value = null }
}

function exportPortfolio() {
  if (!portfolio.value) return
  const rows: string[][] = [['IP类型', '名称', '申请号', '注册号', '状态', '申请日期', '到期日', '官费(CNY)']]
  if (portfolio.value.items) {
    for (const item of portfolio.value.items) {
      rows.push([
        typeLabels[item.ip_type] || item.ip_type,
        item.name || '—',
        item.application_no || '—',
        item.registration_no || '—',
        statusLabels[item.status] || item.status,
        item.filing_date || '—',
        item.expiration_date || '—',
        String(item.official_fee || 0),
      ])
    }
  }
  const csv = rows.map(r => r.join(',')).join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ip_portfolio_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

// ─── P2.4: 费用计算器 ───────────────────────────
const calcData = ref({
  ip_type: 'trademark',
  jurisdictions: ['cn'] as string[],
  classes: [] as number[],
  design_count: 1,
  wipo_designations: [] as string[],
  is_color: false,
})
const feeCalcResult = ref<any>(null)

const feeJurisdictions = [
  { code: 'cn', flag: '🇨🇳', label: '中国' },
  { code: 'us', flag: '🇺🇸', label: '美国' },
  { code: 'eu', flag: '🇪🇺', label: '欧盟' },
  { code: 'wipo', flag: '🌐', label: 'WIPO' },
  { code: 'jp', flag: '🇯🇵', label: '日本' },
  { code: 'kr', flag: '🇰🇷', label: '韩国' },
]

const wipoDesignationOptions = [
  { code: 'eu', label: '🇪🇺 欧盟' },
  { code: 'us', label: '🇺🇸 美国' },
  { code: 'jp', label: '🇯🇵 日本' },
  { code: 'kr', label: '🇰🇷 韩国' },
  { code: 'cn', label: '🇨🇳 中国' },
]

// Quick access to creative-relevant classes for the class picker
const classShortList = ref<{ class_no: number; class_name_zh: string }[]>([])

async function loadClassShortList() {
  try {
    const res = await iprApi.niceClasses(true)
    classShortList.value = (res.data.data || []).map((c: any) => ({
      class_no: c.class_no,
      class_name_zh: c.class_name_zh,
    }))
  } catch { /* fallback */ }
}

function toggleFeeJurisdiction(code: string) {
  const idx = calcData.value.jurisdictions.indexOf(code)
  if (idx >= 0) {
    calcData.value.jurisdictions.splice(idx, 1)
  } else {
    calcData.value.jurisdictions.push(code)
  }
}

function toggleClass(classNo: number) {
  const idx = calcData.value.classes.indexOf(classNo)
  if (idx >= 0) {
    calcData.value.classes.splice(idx, 1)
  } else {
    calcData.value.classes.push(classNo)
  }
}

function toggleDesignation(code: string) {
  const idx = calcData.value.wipo_designations.indexOf(code)
  if (idx >= 0) {
    calcData.value.wipo_designations.splice(idx, 1)
  } else {
    calcData.value.wipo_designations.push(code)
  }
}

async function doFeeCalc() {
  if (!calcData.value.jurisdictions.length) {
    ;(window as any).$toast?.show('请至少选择一个辖区', 'warning')
    return
  }
  try {
    const params: any = {
      ip_type: calcData.value.ip_type,
      jurisdictions: calcData.value.jurisdictions,
    }
    if (calcData.value.ip_type === 'trademark' && calcData.value.classes.length) {
      params.classes = calcData.value.classes
    }
    if (calcData.value.ip_type === 'design_patent') {
      params.design_count = calcData.value.design_count
    }
    if (calcData.value.jurisdictions.includes('wipo')) {
      params.wipo_designations = calcData.value.wipo_designations.length ? calcData.value.wipo_designations : undefined
      params.is_color = calcData.value.is_color
    }
    const res = await iprApi.feeCalculator(params)
    feeCalcResult.value = res.data.data
  } catch (e: any) {
    (window as any).$toast?.show('计算失败: ' + (e.response?.data?.detail || e.message), 'error')
  }
}

onMounted(() => {
  loadGuidelines()
  loadRecords()
  loadWorks()
  loadPortfolio()
  loadClassShortList()
})
</script>

<style scoped>
.ipr-view { display:flex; flex-direction:column; gap:20px; }

/* ── Tabs ────────────────────────────────────── */
.cat-tabs { display:flex; gap:8px; flex-wrap:wrap; }
.cat-tab { padding:8px 18px; border-radius:100px; font-size:.84rem; font-weight:600; cursor:pointer; border:1px solid var(--border); background:var(--surface); color:var(--muted); font-family:var(--font-body); transition:all .2s; }
.cat-tab.active { background:var(--accent); color:#fff; border-color:var(--accent); }

/* ── Disclaimer ──────────────────────────────── */
.disclaimer-bar { padding:10px 16px; background:oklch(62% 0.18 55 / 0.06); border:1px solid oklch(62% 0.18 55 / 0.2); border-radius:var(--radius-sm); font-size:.82rem; color:var(--orange); }

/* ── Guidelines ──────────────────────────────── */
.guidelines { display:flex; flex-direction:column; gap:16px; }
.guideline-card { padding:24px; }
.gl-header { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
.gl-icon { font-size:2rem; }
.gl-header h3 { margin:0; font-size:1.1rem; }
.gl-subtitle { color:var(--muted); font-size:.85rem; margin:4px 0 0; }
.gl-body { display:flex; flex-direction:column; gap:16px; }
.gl-section h4 { font-size:.9rem; margin:0 0 8px; }
.gl-section ul { padding-left:20px; font-size:.85rem; color:var(--muted); line-height:1.8; }
.gl-meta { display:flex; gap:16px; font-size:.82rem; color:var(--muted); flex-wrap:wrap; align-items:center; }
.gl-meta a { color:var(--accent); }
.gl-warning { padding:12px; background:oklch(62% 0.18 55 / 0.08); border-radius:var(--radius-sm); font-size:.82rem; color:var(--orange); }
.gl-fees { margin-top:4px; }
.gl-fees h4 { font-size:.9rem; margin:0 0 8px; }
.fee-grid { display:flex; gap:8px; flex-wrap:wrap; }
.fee-chip { padding:6px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.8rem; display:flex; gap:6px; align-items:center; }
.fee-chip strong { color:var(--accent); white-space:nowrap; }
.category-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.category-chip { padding:8px 12px; background:oklch(96% 0.003 240); border-radius:var(--radius-sm); font-size:.8rem; cursor:pointer; transition:all .15s; }
.category-chip:hover { background:oklch(90% 0.01 240); }
.category-chip strong { color:var(--accent); }

.materials-list { display:flex; flex-direction:column; gap:8px; }
.material-item { display:flex; gap:10px; padding:8px; border-radius:var(--radius-sm); background:var(--surface); border:1px solid var(--border); }
.material-item.required { border-left:3px solid var(--red); }
.material-check { font-size:.9rem; font-weight:700; color:var(--red); min-width:20px; }
.material-name { font-weight:600; font-size:.84rem; display:block; }
.material-desc { font-size:.78rem; color:var(--muted); display:block; margin-top:2px; }
.material-tag { font-size:.72rem; background:oklch(56% 0.12 170 / 0.1); color:var(--accent); padding:1px 6px; border-radius:4px; margin-left:6px; }

.process-flow { display:flex; flex-direction:column; gap:10px; }
.process-step { display:flex; gap:12px; padding:10px; border-radius:var(--radius-sm); background:var(--surface); border:1px solid var(--border); }
.step-num { width:28px; height:28px; display:flex; align-items:center; justify-content:center; background:var(--accent); color:#fff; border-radius:50%; font-size:.78rem; font-weight:700; flex-shrink:0; }
.process-step strong { font-size:.85rem; display:block; }
.process-step p { font-size:.78rem; color:var(--muted); margin:4px 0 2px; }
.process-step small { font-size:.72rem; color:var(--muted); }

/* ── Wizard ──────────────────────────────────── */
.wizard-steps { display:flex; gap:0; align-items:center; margin-bottom:4px; }
.wiz-step { display:flex; align-items:center; gap:8px; padding:8px 16px 8px 8px; font-size:.82rem; color:var(--muted); }
.wiz-step.active { color:var(--accent); font-weight:700; }
.wiz-step.done { color:var(--accent); }
.wiz-num { width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:50%; border:2px solid var(--border); font-size:.78rem; font-weight:700; }
.wiz-step.active .wiz-num { background:var(--accent); color:#fff; border-color:var(--accent); }
.wiz-step.done .wiz-num { background:oklch(56% 0.12 170 / 0.2); color:var(--accent); border-color:var(--accent); }

.wizard-card { padding:24px; }
.wizard-card h3 { margin:0 0 16px; font-size:1.05rem; }
.wizard-card h4 { margin:0 0 12px; font-size:.95rem; }

.ip-type-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.ip-type-card { padding:16px; border:2px solid var(--border); border-radius:var(--radius-lg); cursor:pointer; transition:all .15s; }
.ip-type-card:hover { border-color:var(--accent); }
.ip-type-card.selected { border-color:var(--accent); background:oklch(56% 0.12 170 / 0.05); }
.ip-type-icon { font-size:1.5rem; display:block; margin-bottom:6px; }
.ip-type-card strong { font-size:.9rem; display:block; }
.ip-type-card p { font-size:.78rem; color:var(--muted); margin:4px 0 0; }

.jurisdiction-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.jur-card { padding:12px 16px; border:2px solid var(--border); border-radius:var(--radius-lg); cursor:pointer; transition:all .15s; display:flex; flex-direction:column; gap:4px; }
.jur-card:hover { border-color:var(--accent); }
.jur-card.selected { border-color:var(--accent); background:oklch(56% 0.12 170 / 0.05); }
.jur-card strong { font-size:.9rem; }
.jur-card span { font-size:.8rem; }
.jur-card small { font-size:.72rem; color:var(--muted); }

.works-selector { display:flex; gap:10px; align-items:center; margin-bottom:16px; }
.works-selector label { font-size:.84rem; font-weight:600; white-space:nowrap; }
.works-selector select { min-width:200px; }

.prefill-result { margin-top:12px; }
.completeness-bar { display:flex; align-items:center; gap:10px; margin:12px 0; }
.comp-label { font-size:.82rem; font-weight:600; min-width:50px; }
.comp-track { flex:1; height:8px; background:var(--border); border-radius:10px; overflow:hidden; }
.comp-fill { height:100%; background:var(--accent); border-radius:10px; transition:width .3s; }
.comp-fill.fill-green { background:var(--green); }
.comp-fill.fill-red { background:var(--red); }
.comp-pct { font-size:.82rem; font-weight:700; min-width:40px; }

.prefill-fields { display:grid; grid-template-columns:1fr 1fr; gap:10px; max-height:400px; overflow-y:auto; }
.prefill-field { display:flex; flex-direction:column; gap:4px; }
.prefill-field label { font-size:.78rem; font-weight:600; color:var(--muted); display:flex; align-items:center; gap:4px; }
.req-mark { color:var(--red); }
.source-tag { font-size:.65rem; padding:0 4px; border-radius:3px; font-weight:400; }
.src-work { background:oklch(56% 0.12 170 / 0.1); color:var(--accent); }
.src-notary { background:oklch(56% 0.12 260 / 0.1); color:var(--blue); }
.src-manual { background:oklch(62% 0.18 55 / 0.1); color:var(--orange); }
.src-user { background:oklch(62% 0.15 320 / 0.1); color:var(--purple); }
.readonly-val { font-size:.84rem; padding:8px 12px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); color:var(--muted); }

.validate-result { margin-top:16px; }
.valid-ok { padding:12px; background:oklch(56% 0.12 170 / 0.08); border-radius:var(--radius-sm); font-weight:600; color:var(--accent); }
.issues-list { display:flex; flex-direction:column; gap:8px; margin-top:12px; }
.issue-item { padding:8px 12px; border-radius:var(--radius-sm); font-size:.82rem; }
.issue-error { background:oklch(62% 0.18 20 / 0.06); color:var(--red); }
.issue-warning { background:oklch(62% 0.18 55 / 0.06); color:var(--orange); }
.issue-item strong { margin:0 4px; }

.export-actions { display:flex; gap:10px; margin-bottom:16px; }
.export-result { margin-top:16px; }
.export-disclaimer { padding:8px 12px; background:oklch(62% 0.18 55 / 0.06); border-radius:var(--radius-sm); font-size:.8rem; color:var(--orange); margin:10px 0; }
.preview-table { width:100%; border-collapse:collapse; font-size:.82rem; margin:10px 0; }
.preview-table td { padding:6px 10px; border-bottom:1px solid var(--border); }
.preview-table td:first-child { font-weight:600; color:var(--muted); width:30%; }
.checklist-item { display:flex; flex-wrap:wrap; gap:6px; align-items:baseline; padding:6px 0; border-bottom:1px solid var(--border); font-size:.84rem; }
.item-status { font-size:.72rem; padding:1px 6px; border-radius:4px; }
.status-prepared { background:oklch(56% 0.12 170 / 0.1); color:var(--accent); }
.status-requires_manual { background:oklch(62% 0.18 55 / 0.1); color:var(--orange); }
.item-desc { font-size:.76rem; color:var(--muted); width:100%; margin:0; }

.wizard-nav { display:flex; gap:10px; align-items:center; margin-top:8px; }
.spacer { flex:1; }

/* ── Category Recommender ────────────────────── */
.category-recommender { margin-top:8px; }
.recommend-input { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
.recommend-input .form-input { flex:1; min-width:120px; }
.recommend-result { margin-top:12px; }
.rec-class-item { display:flex; align-items:center; gap:8px; padding:8px 0; border-bottom:1px solid var(--border); font-size:.84rem; }
.rec-stars { color:oklch(62% 0.18 55); font-size:.82rem; min-width:70px; }
.rec-class-item strong { min-width:60px; }
.rec-reason { color:var(--muted); font-size:.78rem; flex:1; }
.rec-fee { font-weight:600; color:var(--accent); }
.rec-summary { margin-top:12px; padding:12px; background:oklch(56% 0.12 170 / 0.05); border-radius:var(--radius-sm); }
.rec-summary strong { font-size:.9rem; color:var(--accent); }
.rec-summary p { font-size:.78rem; color:var(--muted); margin:4px 0 0; }

/* ── Registrations ───────────────────────────── */
.registrations { display:flex; flex-direction:column; gap:16px; }
.actions-bar { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
.filter-group { display:flex; gap:8px; }
.filter-group .form-input { width:120px; padding:8px 12px; }
.records-list { display:flex; flex-direction:column; gap:12px; }
.record-row { padding:16px 20px; }
.record-header { margin-bottom:12px; }
.record-title { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.record-type { font-weight:700; font-size:.88rem; }
.record-jurisdiction { font-size:.75rem; color:var(--muted); padding:2px 8px; background:var(--surface); border:1px solid var(--border); border-radius:100px; }
.record-body { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }
.record-field label { font-size:.72rem; color:var(--muted); font-weight:600; display:block; }
.record-field span { font-size:.85rem; }
.record-footer { margin-top:12px; display:flex; justify-content:flex-end; gap:8px; }

/* ── Dashboard ───────────────────────────────── */
.dashboard { display:flex; flex-direction:column; gap:16px; }
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.stat-card { padding:20px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:6px; }
.stat-icon { font-size:1.8rem; }
.stat-num { font-size:2rem; font-weight:800; color:var(--accent); }
.stat-label { font-size:.82rem; color:var(--muted); }
.stat-detail { display:flex; gap:4px; flex-wrap:wrap; justify-content:center; margin-top:4px; }
.mini-badge { font-size:.65rem; padding:1px 5px; border-radius:4px; }
.badge-info { background:oklch(56% 0.12 260 / 0.1); color:var(--blue); }
.badge-success { background:oklch(56% 0.12 170 / 0.1); color:var(--accent); }
.badge-warning { background:oklch(62% 0.18 55 / 0.1); color:var(--orange); }
.badge-error { background:oklch(62% 0.18 20 / 0.1); color:var(--red); }

.summary-row { padding:20px; display:flex; gap:32px; }
.summary-item { display:flex; flex-direction:column; align-items:center; gap:4px; }
.summary-item strong { font-size:1.4rem; color:var(--accent); }
.summary-item span { font-size:.8rem; color:var(--muted); }

.jurisdiction-stats { padding:20px; }
.jurisdiction-stats h4 { margin:0 0 10px; font-size:.95rem; }
.jur-tags { display:flex; gap:8px; flex-wrap:wrap; }
.jur-tag { padding:6px 14px; background:var(--surface); border:1px solid var(--border); border-radius:100px; font-size:.82rem; font-weight:600; }

.renewals-section { padding:20px; }
.renewals-section h4 { margin:0 0 12px; font-size:.95rem; }
.renewal-list { display:flex; flex-direction:column; gap:8px; }
.renewal-item { display:flex; align-items:center; gap:12px; padding:12px; border-radius:var(--radius-sm); border:1px solid var(--border); }
.urgency-red { border-left:4px solid var(--red); background:oklch(62% 0.18 20 / 0.03); }
.urgency-orange { border-left:4px solid var(--orange); background:oklch(62% 0.18 55 / 0.03); }
.urgency-yellow { border-left:4px solid oklch(62% 0.18 55 / 0.4); }
.urgency-dot { font-size:1rem; }
.renewal-info { flex:1; display:flex; flex-direction:column; }
.renewal-info strong { font-size:.85rem; }
.renewal-info span { font-size:.76rem; color:var(--muted); }
.renewal-date { text-align:right; }
.days-left { font-weight:800; font-size:1rem; }
.d-red { color:var(--red); }
.d-orange { color:var(--orange); }
.d-yellow { color:oklch(62% 0.18 55 / 0.6); }
.renewal-date small { display:block; font-size:.72rem; color:var(--muted); }

/* ── Modal & Form ────────────────────────────── */
.btn-sm { padding:6px 12px; font-size:.78rem; }
.btn-accent { background:oklch(56% 0.12 260); color:#fff; border:none; }
.btn-accent:hover { opacity:0.85; }
.btn-danger { background:var(--red); color:#fff; border:none; }
.btn-danger:hover { opacity:0.85; }
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; max-height:90vh; overflow-y:auto; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; }
.form-group { display:flex; flex-direction:column; gap:6px; }
.form-group label { font-size:.82rem; font-weight:600; color:var(--muted); }
.form-input,.form-textarea { padding:10px 14px; border:1px solid var(--border); border-radius:var(--radius-sm); font-size:.88rem; font-family:var(--font-body); color:var(--fg); background:var(--surface); outline:none; }
.form-input:focus,.form-textarea:focus { border-color:var(--accent); box-shadow:0 0 0 3px oklch(56% 0.12 170 / .1); }
.form-textarea { resize:vertical; }

@media (max-width:768px) {
  .stats-row { grid-template-columns:1fr 1fr; }
  .summary-row { flex-wrap:wrap; gap:16px; }
  .ip-type-grid { grid-template-columns:1fr; }
  .jurisdiction-grid { grid-template-columns:1fr; }
  .prefill-fields { grid-template-columns:1fr; }
  .record-body { grid-template-columns:1fr 1fr; }
  .category-grid { grid-template-columns:1fr; }
  .actions-bar { flex-direction:column; align-items:stretch; }
  .filter-group { flex-wrap:wrap; }
}

/* ── P2.4: Jurisdiction Bar ───────────────────── */
.jurisdiction-bar { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:4px; }
.jur-btn { padding:8px 18px; border-radius:100px; font-size:.82rem; font-weight:600; cursor:pointer; border:2px solid var(--border); background:var(--surface); color:var(--muted); font-family:var(--font-body); transition:all .2s; display:flex; align-items:center; gap:6px; }
.jur-btn:hover { border-color:var(--accent); color:var(--accent); }
.jur-btn.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.jur-flag { font-size:1rem; }
.jur-label { font-size:.82rem; }

/* ── P2.4: Country grid (EU) ──────────────────── */
.country-grid { display:flex; flex-wrap:wrap; gap:6px; }
.country-chip { padding:3px 10px; background:oklch(56% 0.12 260 / 0.08); border:1px solid oklch(56% 0.12 260 / 0.2); border-radius:100px; font-size:.75rem; color:var(--blue); }

/* ── P2.4: Fee examples ──────────────────────── */
.fee-example-list { display:flex; flex-direction:column; gap:8px; }
.fee-example-item { padding:10px 14px; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-sm); }
.fee-example-header { display:flex; justify-content:space-between; align-items:center; font-size:.84rem; }
.fee-total { font-weight:800; color:var(--accent); }
.fee-example-breakdown { font-size:.76rem; color:var(--muted); margin:4px 0 0; }

/* ── P2.4: SME Fund ──────────────────────────────── */
.sme-coverage { display:flex; gap:10px; flex-direction:column; }
.sme-cov-item { padding:10px 14px; background:oklch(56% 0.12 260 / 0.05); border:1px solid oklch(56% 0.12 260 / 0.15); border-radius:var(--radius-sm); display:flex; flex-direction:column; gap:2px; }
.sme-cov-item strong { color:var(--blue); font-size:.9rem; }
.sme-cov-item span { font-size:.8rem; color:var(--muted); }

/* ── Trademark Similarity Search ───────────── */
.trademark-search-box { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
.trademark-search-box .form-input { max-width:300px; }
.similarity-summary { display:flex; gap:12px; align-items:center; margin-bottom:10px; }
.sim-count { font-size:.85rem; color:var(--muted); }
.sim-risk { font-size:.78rem; padding:2px 10px; border-radius:100px; font-weight:600; }
.sim-risk.high { background:oklch(62% 0.18 20 / .1); color:var(--red); }
.sim-risk.warning { background:oklch(62% 0.18 55 / .1); color:var(--orange); }
.sim-risk.low { background:oklch(56% 0.12 170 / .1); color:var(--accent); }
.sim-list { display:flex; flex-direction:column; gap:6px; }
.sim-item { display:flex; gap:12px; font-size:.82rem; align-items:center; padding:6px 10px; background:var(--surface); border-radius:var(--radius-sm); border:1px solid var(--border); }
.sim-name { flex:1; font-weight:600; }
.sim-class { font-size:.75rem; color:var(--muted); }
.sim-score { font-size:.75rem; font-weight:600; }
.sim-score.high { color:var(--red); }
.sim-score.medium { color:var(--orange); }
.sim-score.low { color:var(--accent); }

/* ── P2.4: Fee Calculator ──────────────────────────── */
.calc-desc { color:var(--muted); font-size:.85rem; margin:0 0 16px; }
.calc-type-row { display:flex; gap:8px; flex-wrap:wrap; }
.calc-jur-grid { display:flex; gap:8px; flex-wrap:wrap; }
.calc-class-grid { display:flex; gap:6px; flex-wrap:wrap; }
.class-chip { width:38px; height:38px; display:flex; align-items:center; justify-content:center; border-radius:8px; border:2px solid var(--border); background:var(--surface); font-size:.78rem; font-weight:700; cursor:pointer; transition:all .15s; font-family:var(--font-body); color:var(--muted); }
.class-chip:hover { border-color:var(--accent); }
.class-chip.active { background:var(--accent); color:#fff; border-color:var(--accent); }
.calc-selected-classes { margin-top:8px; font-size:.82rem; color:var(--muted); display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.selected-class-tag { padding:2px 10px; background:oklch(56% 0.12 170 / 0.1); color:var(--accent); border-radius:100px; font-size:.78rem; font-weight:600; }
.calc-toggle { display:flex; gap:8px; }
.calc-desig-grid { display:flex; gap:8px; flex-wrap:wrap; }
.calc-result { margin-top:24px; }
.calc-result h4 { font-size:1rem; margin:0 0 12px; }
.calc-summary-row { display:flex; gap:24px; flex-wrap:wrap; }
.calc-summary-item { display:flex; flex-direction:column; gap:4px; }
.calc-summary-label { font-size:.76rem; color:var(--muted); }
.calc-summary-item strong { font-size:1.05rem; }
.calc-total-fee { color:var(--accent); font-size:1.3rem !important; }
.currency-chip { padding:4px 12px; background:oklch(56% 0.12 170 / 0.08); border-radius:100px; font-size:.8rem; font-weight:600; color:var(--accent); }
.calc-breakdown { display:flex; flex-direction:column; gap:10px; margin-bottom:12px; }
.calc-bd-item { padding:14px 16px; border:1px solid var(--border); border-radius:var(--radius-sm); background:var(--surface); }
.calc-bd-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.calc-bd-jur { font-size:.85rem; font-weight:600; }
.calc-bd-fee { font-size:.9rem; color:var(--accent); }
.calc-bd-detail { font-size:.78rem; color:var(--muted); display:flex; gap:12px; }
.calc-bd-breakdown { display:flex; flex-wrap:wrap; gap:4px 12px; margin-top:6px; }
.calc-bd-sub { font-size:.74rem; color:var(--muted); padding:1px 6px; background:oklch(96% 0.003 240); border-radius:4px; }
.calc-bd-notes { font-size:.76rem; color:var(--muted); margin-top:6px; font-style:italic; }
.calc-bd-error { font-size:.78rem; color:var(--orange); margin-top:4px; }
.calc-fx-note { margin-top:10px; padding:10px 14px; background:oklch(62% 0.18 55 / 0.06); border-radius:var(--radius-sm); }
.calc-fx-note p { font-size:.78rem; color:var(--muted); margin:0; }
.calc-fx-disclaimer { font-size:.72rem !important; color:var(--orange) !important; margin-top:4px !important; }

/* ── Full-screen disclaimer modal ──────────────── */
.disclaimer-fullscreen-modal {
  position: fixed; inset: 0; z-index: 9999;
  background: oklch(0 0 0 / .55);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
}
.disclaimer-modal-card {
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 36px;
  max-width: 640px;
  width: 92%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 16px 64px oklch(0 0 0 / .2);
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.disclaimer-modal-card h2 { margin: 0; font-size: 1.2rem; }
.disclaimer-intro { font-size: .85rem; color: var(--muted); margin: 0; }
.disclaimer-list {
  display: flex; flex-direction: column; gap: 10px;
  padding: 16px; background: oklch(96% .003 240);
  border-radius: var(--radius-sm);
  max-height: 40vh; overflow-y: auto;
}
.disclaimer-item {
  display: flex; gap: 10px; align-items: flex-start;
  font-size: .84rem; line-height: 1.5; color: var(--fg);
}
.disclaimer-num {
  min-width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: var(--accent); color: #fff;
  border-radius: 50%; font-size: .78rem; font-weight: 700;
  flex-shrink: 0;
}
.disclaimer-footer { margin-top: 8px; }

/* ── Detail & Supplement Modals ─────────────────── */
.detail-header-card { display: flex; gap: 8px; align-items: center; padding: 12px; background: oklch(96% .003 240); border-radius: var(--radius-sm); margin-bottom: 12px; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
.detail-field label { font-size: .72rem; color: var(--muted); font-weight: 600; display: block; }
.detail-field span { font-size: .85rem; }
.detail-notes { margin-top: 12px; }
.detail-notes h5 { margin: 0 0 4px; font-size: .85rem; }
.detail-notes p { font-size: .82rem; color: var(--muted); margin: 0; }
.detail-links { margin-top: 12px; }
.detail-history { margin-top: 12px; }
.detail-history h5 { margin: 0 0 6px; font-size: .85rem; }
.history-item { display: flex; gap: 12px; font-size: .78rem; padding: 4px 0; }
.history-time { color: var(--muted); min-width: 100px; }
.history-action { color: var(--fg); }

/* ── Lawyer audit step ─────────────────────────── */
.lawyer-audit-intro { font-size: .84rem; color: var(--muted); margin: 0 0 16px; }
.audit-options { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.audit-option {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border: 2px solid var(--border);
  border-radius: var(--radius-lg); cursor: pointer;
  transition: all .15s; background: var(--surface);
}
.audit-option:hover { border-color: var(--accent); }
.audit-option.selected { border-color: var(--accent); background: oklch(56% .12 170 / .05); }
.audit-option input[type="radio"] { display: none; }
.audit-radio-circle {
  width: 20px; height: 20px; border-radius: 50%;
  border: 2px solid var(--border); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.audit-radio-circle.checked { border-color: var(--accent); }
.audit-radio-circle.checked::after {
  content: ''; width: 10px; height: 10px;
  background: var(--accent); border-radius: 50%;
}
.audit-option-content { display: flex; flex-direction: column; gap: 2px; }
.audit-option-content strong { font-size: .9rem; }
.audit-option-content span { font-size: .8rem; color: var(--muted); }
.risk-confirmations {
  padding: 16px; background: oklch(62% .18 55 / .06);
  border-radius: var(--radius-sm); margin-bottom: 12px;
}
.risk-confirm-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; font-size: .84rem;
}
.risk-confirm-item input[type="checkbox"] { width: 16px; height: 16px; flex-shrink: 0; }
.risk-confirm-hint { font-size: .8rem; color: var(--orange); margin: 8px 0 0; }
.lawyer-audit-footer { margin-top: 8px; }
.lawyer-audit-note { font-size: .82rem; color: var(--muted); margin: 0; }

.btn-lg { padding: 12px 32px; font-size: .95rem; }
.btn-warning { background: var(--orange); color: #fff; border: none; }
.btn-warning:hover { opacity: .85; }
.btn-info { background: var(--blue); color: #fff; border: none; }
.btn-info:hover { opacity: .85; }
.btn-neutral { background: var(--muted); color: #fff; border: none; }
.btn-primary.disabled {
  opacity: .5;
  cursor: not-allowed;
}
.btn-primary.disabled:hover { opacity: .5; }
</style>

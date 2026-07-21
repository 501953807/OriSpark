<template>
  <div class="settings-view">
    <div class="settings-sidebar">
      <div
        v-for="s in sections"
        :key="s.key"
        class="settings-nav-item"
        :class="{ active: activeSection === s.key }"
        @click="activeSection = s.key"
      >
        <span>{{ s.icon }}</span>
        <span>{{ s.label }}</span>
      </div>
    </div>

    <div class="settings-content">
      <!-- Profile -->
      <div v-if="activeSection === 'profile'" class="settings-section card animate-fade-in">
        <h2>个人资料</h2>
        <div class="form-group">
          <label>显示名称</label>
          <input v-model="profile.name" class="form-input" placeholder="创作者" />
        </div>
        <div class="form-group">
          <label>简介</label>
          <textarea v-model="profile.bio" class="form-textarea" rows="3" placeholder="介绍一下你自己..."></textarea>
        </div>

        <!-- P2.7.14: Avatar Upload -->
        <div class="form-group">
          <label>头像</label>
          <div class="avatar-upload-row">
            <div class="avatar-preview" v-if="profile.avatar_url">
              <img :src="profile.avatar_url" alt="avatar" />
            </div>
            <div class="avatar-placeholder" v-else>👤</div>
            <label class="btn btn-secondary btn-sm avatar-upload-btn">
              上传头像
              <input type="file" accept="image/*" @change="onAvatarSelected" hidden />
            </label>
          </div>
        </div>

        <!-- P2.7.11: Email Verification -->
        <div class="form-group">
          <label>邮箱验证</label>
          <div class="email-verify-row">
            <span v-if="profile.email_verified" class="verified-badge">已验证</span>
            <span v-else class="unverified-badge">未验证</span>
            <button v-if="!profile.email_verified" class="btn btn-sm btn-secondary" @click="showEmailVerifyInput = !showEmailVerifyInput">
              {{ showEmailVerifyInput ? '取消' : '验证邮箱' }}
            </button>
          </div>
          <div v-if="showEmailVerifyInput" class="email-verify-form">
            <input v-model="verifyEmailAddr" class="form-input" placeholder="输入邮箱" style="width:200px" />
            <button class="btn btn-sm btn-primary" @click="sendVerifyCode" :disabled="verifySending">
              {{ verifySending ? '发送中...' : '发送验证码' }}
            </button>
            <div v-if="verifyCodeSent" class="verify-code-row">
              <input v-model="verifyCode" class="form-input" placeholder="验证码" style="width:120px" />
              <button class="btn btn-sm btn-primary" @click="confirmVerifyCode">确认</button>
            </div>
          </div>
        </div>

        <button class="btn btn-primary" @click="saveProfile" :disabled="profileSaving">
          {{ profileSaving ? '保存中...' : '保存' }}
        </button>
      </div>

      <!-- Appearance -->
      <div v-if="activeSection === 'appearance'" class="settings-section card animate-fade-in">
        <h2>外观设置</h2>
        <div class="setting-row">
          <div>
            <div class="setting-label">暗色模式</div>
            <div class="setting-desc">切换深色/浅色主题</div>
          </div>
          <label class="toggle">
            <input type="checkbox" :checked="isDark" @change="toggleTheme" aria-label="切换暗色模式" />
            <span class="toggle-slider"></span>
          </label>
        </div>
        <!-- P3.3.5: Language Switcher -->
        <div class="setting-row">
          <div>
            <div class="setting-label">界面语言</div>
            <div class="setting-desc">选择显示语言 / Display language</div>
          </div>
          <select v-model="currentLang" @change="changeLang" class="form-select" style="width:140px" aria-label="选择界面语言">
            <option value="zh-CN">中文</option>
            <option value="en-US">English</option>
          </select>
        </div>
      </div>

      <!-- Linked Accounts -->
      <div v-if="activeSection === 'linked'" class="settings-section card animate-fade-in">
        <h2>关联账号</h2>
        <div class="linked-card" v-for="provider in providers" :key="provider.key">
          <div class="linked-info">
            <span class="linked-icon">{{ provider.icon }}</span>
            <div>
              <div class="linked-name">{{ provider.name }}</div>
              <div class="linked-status" :class="{ bound: provider.bound }">
                {{ provider.bound ? (provider.account || '已绑定') : '未绑定' }}
              </div>
            </div>
          </div>
          <button
            class="btn btn-sm"
            :class="provider.bound ? 'btn-secondary' : 'btn-primary'"
            @click="provider.bound ? unbindProvider(provider.key) : bindProvider(provider.key)"
          >
            {{ provider.bound ? '解绑' : '绑定' }}
          </button>
        </div>
      </div>

      <!-- P2.7.1-P2.7.2: System Health -->
      <div v-if="activeSection === 'health'" class="settings-section card animate-fade-in">
        <h2>系统健康监控</h2>
        <div class="health-grid" v-if="healthData">
          <div class="health-card" :class="{ warning: healthData.cpu?.percent > 80, danger: healthData.cpu?.percent > 90 }">
            <div class="health-label">CPU</div>
            <div class="health-value">{{ healthData.cpu?.percent || 0 }}%</div>
            <div class="health-sub">核心数: {{ healthData.cpu?.cores || 1 }}</div>
            <div class="health-bar"><div class="health-fill" :style="{ width: (healthData.cpu?.percent || 0) + '%', background: healthData.cpu?.percent > 80 ? '#ef4444' : healthData.cpu?.percent > 60 ? '#f59e0b' : '#16a34a' }"></div></div>
          </div>
          <div class="health-card" :class="{ warning: healthData.memory?.percent > 80, danger: healthData.memory?.percent > 90 }">
            <div class="health-label">内存</div>
            <div class="health-value">{{ healthData.memory?.percent || 0 }}%</div>
            <div class="health-sub">{{ formatMB(healthData.memory?.used_mb) }} / {{ formatMB(healthData.memory?.total_mb) }}</div>
            <div class="health-bar"><div class="health-fill" :style="{ width: (healthData.memory?.percent || 0) + '%', background: healthData.memory?.percent > 80 ? '#ef4444' : healthData.memory?.percent > 60 ? '#f59e0b' : '#16a34a' }"></div></div>
          </div>
          <div class="health-card" :class="{ warning: healthData.disk?.percent > 80, danger: healthData.disk?.percent > 90 }">
            <div class="health-label">磁盘</div>
            <div class="health-value">{{ healthData.disk?.percent || 0 }}%</div>
            <div class="health-sub">{{ formatGB(healthData.disk?.free_gb) }} 可用</div>
            <div class="health-bar"><div class="health-fill" :style="{ width: (healthData.disk?.percent || 0) + '%', background: healthData.disk?.percent > 80 ? '#ef4444' : healthData.disk?.percent > 60 ? '#f59e0b' : '#16a34a' }"></div></div>
          </div>
        </div>
        <div class="service-status-row" v-if="serviceStatus">
          <h3 style="margin:0 0 12px;font-size:0.95rem">服务状态</h3>
          <div v-for="(status, name) in serviceStatus" :key="name" class="service-item">
            <span class="service-name">{{ name }}</span>
            <span class="service-dot" :class="{ online: status.status === 'healthy', offline: status.status !== 'healthy' }"></span>
            <span class="service-status-text">{{ status.status === 'healthy' ? '正常' : (status.note || '异常') }}</span>
          </div>
        </div>
        <div class="actions-row">
          <button class="btn btn-sm btn-secondary" @click="refreshHealth">刷新</button>
        </div>
      </div>

      <!-- Data / Backup (P2.7.3-P2.7.4 enhanced) -->
      <div v-if="activeSection === 'data'" class="settings-section card animate-fade-in">
        <h2>数据管理</h2>

        <!-- Storage -->
        <div class="storage-info" v-if="storageInfo">
          <div class="storage-bar">
            <div class="storage-fill" :style="{ width: storagePercent + '%' }"></div>
          </div>
          <div class="storage-text">
            已用 {{ formatBytes((storageInfo.breakdown?.workspace ?? 0) + (storageInfo.breakdown?.database ?? 0)) }} / 可用 {{ formatBytes(storageInfo.free_space ?? 0) }}
          </div>
        </div>

        <!-- Backup Actions -->
        <div class="setting-row">
          <div>
            <div class="setting-label">创建备份</div>
            <div class="setting-desc">备份数据库到本地</div>
          </div>
          <div class="btn-row">
            <button class="btn btn-sm btn-primary" @click="createBackup">标准备份</button>
            <button class="btn btn-sm btn-secondary" @click="createEncryptedBackup">加密备份</button>
          </div>
        </div>

        <!-- Backup Schedule -->
        <div class="setting-row">
          <div>
            <div class="setting-label">定时备份</div>
            <div class="setting-desc">自动定时备份 (cron 表达式)</div>
          </div>
          <div class="schedule-row">
            <select v-model="backupScheduleCron" class="form-select" style="width:140px;font-size:0.82rem">
              <option value="0 2 * * *">每日 02:00</option>
              <option value="0 4 * * *">每日 04:00</option>
              <option value="0 2 * * 0">每周日 02:00</option>
              <option value="0 0 1 * *">每月1日 00:00</option>
            </select>
            <button class="btn btn-sm btn-secondary" @click="saveBackupSchedule">保存</button>
          </div>
        </div>

        <!-- Backup List -->
        <div v-if="backupList.length" class="backup-list">
          <h3 style="margin:0 0 8px;font-size:0.9rem">备份历史</h3>
          <div v-for="b in backupList" :key="b.id" class="backup-row">
            <div class="backup-info">
              <span class="backup-date">{{ b.created_at?.slice(0, 16).replace('T', ' ') }}</span>
              <span class="backup-type">{{ b.type === 'auto' ? '自动' : '手动' }}{{ b.encrypted ? ' 加密' : '' }}</span>
            </div>
            <div class="backup-size">{{ formatBytes(b.size) }}</div>
            <div class="backup-actions">
              <button class="btn btn-sm btn-secondary" @click="restoreBackup(b.id)">恢复</button>
              <button class="btn btn-sm btn-danger" @click="deleteBackupRecord(b.id)">删除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- P2.7.5-P2.7.6: Notification Channels -->
      <div v-if="activeSection === 'notifications'" class="settings-section card animate-fade-in">
        <h2>通知渠道</h2>

        <!-- Email SMTP -->
        <div class="notif-channel">
          <h3>邮件通知 (SMTP)</h3>
          <div class="form-group">
            <label>SMTP 服务器</label>
            <input v-model="smtpConfig.host" class="form-input" placeholder="smtp.example.com" />
          </div>
          <div class="form-row-2">
            <div class="form-group">
              <label>端口</label>
              <input v-model="smtpConfig.port" class="form-input" placeholder="587" />
            </div>
            <div class="form-group">
              <label>使用TLS</label>
              <select v-model="smtpConfig.tls" class="form-select">
                <option value="true">是</option>
                <option value="false">否</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>发件邮箱</label>
            <input v-model="smtpConfig.user" class="form-input" placeholder="user@example.com" />
          </div>
          <div class="form-group">
            <label>密码/授权码</label>
            <input v-model="smtpConfig.password" type="password" class="form-input" placeholder="••••••••" />
          </div>
          <div class="form-group">
            <label>测试收件地址</label>
            <div class="test-row">
              <input v-model="testEmailAddr" class="form-input" placeholder="test@example.com" style="width:220px" />
              <button class="btn btn-sm btn-primary" @click="testEmailSend" :disabled="emailTesting">
                {{ emailTesting ? '发送中...' : '发送测试邮件' }}
              </button>
            </div>
          </div>
          <button class="btn btn-secondary btn-sm" @click="saveSmtpConfig">保存 SMTP 配置</button>
        </div>

        <!-- WeChat Template -->
        <div class="notif-channel">
          <h3>微信模板消息</h3>
          <div class="form-group">
            <label>AppID</label>
            <input v-model="wechatConfig.appid" class="form-input" placeholder="wx..." />
          </div>
          <div class="form-group">
            <label>AppSecret</label>
            <input v-model="wechatConfig.appsecret" type="password" class="form-input" placeholder="••••••••" />
          </div>
          <div class="form-group">
            <label>模板ID</label>
            <input v-model="wechatConfig.templateId" class="form-input" placeholder="消息模板ID" />
          </div>
          <div class="btn-row">
            <button class="btn btn-secondary btn-sm" @click="saveWechatConfig">保存配置</button>
            <button class="btn btn-sm btn-primary" @click="testWechatSend" :disabled="wechatTesting">
              {{ wechatTesting ? '测试中...' : '测试连接' }}
            </button>
          </div>
        </div>
      </div>

      <!-- P2.7.8: Plugin Framework -->
      <div v-if="activeSection === 'plugins'" class="settings-section card animate-fade-in">
        <h2>插件管理</h2>
        <div class="actions-bar">
          <button class="btn btn-sm btn-primary" @click="showPluginModal = true">+ 注册插件</button>
        </div>
        <div v-if="plugins.length" class="plugin-list">
          <div v-for="p in plugins" :key="p.id" class="plugin-card" :class="{ disabled: !p.enabled }">
            <div class="plugin-info">
              <div class="plugin-name">{{ p.display_name }}</div>
              <div class="plugin-version">v{{ p.version }}</div>
              <div class="plugin-desc" v-if="p.description">{{ p.description }}</div>
              <div class="plugin-hooks" v-if="p.hooks?.length">
                <span v-for="h in p.hooks" :key="h" class="plugin-hook-tag">{{ h }}</span>
              </div>
            </div>
            <div class="plugin-actions">
              <label class="toggle">
                <input type="checkbox" :checked="p.enabled" @change="togglePlugin(p)" />
                <span class="toggle-slider"></span>
              </label>
              <button class="btn btn-sm btn-secondary" @click="deletePluginRecord(p.id)">删除</button>
            </div>
          </div>
        </div>
        <div v-else class="empty-hint">暂无注册插件</div>
      </div>

      <!-- P2.7.13: Password -->
      <div v-if="activeSection === 'password'" class="settings-section card animate-fade-in">
        <h2>密码管理</h2>
        <div class="form-group">
          <label>当前密码</label>
          <input v-model="currentPassword" type="password" class="form-input" placeholder="输入当前密码" />
        </div>
        <div class="form-group">
          <label>新密码</label>
          <input v-model="newPassword" type="password" class="form-input" placeholder="输入新密码" @input="checkStrength" />
          <div v-if="passwordStrength" class="strength-bar-row">
            <div class="strength-bar">
              <div class="strength-fill" :style="{ width: passwordStrength.score + '%', background: strengthColor }"></div>
            </div>
            <span class="strength-text" :style="{ color: strengthColor }">{{ strengthLabel }}</span>
          </div>
        </div>
        <div class="form-group">
          <label>确认新密码</label>
          <input v-model="newPasswordConfirm" type="password" class="form-input" placeholder="再次输入新密码" />
        </div>
        <button class="btn btn-primary" @click="changePassword" :disabled="!currentPassword || !newPassword || newPassword !== newPasswordConfirm">
          修改密码
        </button>
      </div>

      <!-- P2-8: Account Security -->
      <div v-if="activeSection === 'security'" class="settings-section card animate-fade-in">
        <h2>账户安全</h2>

        <!-- 2FA / TOTP -->
        <div class="security-card">
          <h3 style="margin:0 0 8px;font-size:0.95rem">两步验证 (2FA)</h3>
          <p style="margin:0 0 12px;font-size:0.84rem;color:var(--muted)">启用 TOTP 双因素认证增强账户安全</p>
          <div v-if="totpEnabled" class="totp-active">
            <span style="color:#16a34a;font-weight:600;font-size:0.88rem">已启用</span>
            <div class="form-group" style="max-width:240px;margin-top:12px">
              <label>输入验证码以禁用</label>
              <div class="form-row-2" style="grid-template-columns:1fr auto">
                <input v-model="totpVerifyCode" type="text" class="form-input" placeholder="输入 TOTP 验证码" maxlength="6" style="width:100%;max-width:240px" />
                <button class="btn btn-sm btn-danger" @click="disableTOTP" :disabled="!totpVerifyCode">禁用 2FA</button>
              </div>
            </div>
          </div>
          <template v-else>
            <div v-if="!totpSetupSecret" class="totp-setup-stub">
              <div class="qr-placeholder">📱</div>
              <p style="font-size:0.84rem;color:var(--muted)">使用 Authenticator App 扫描下方二维码</p>
            </div>
            <div v-if="totpSetupSecret" class="form-group">
              <label>设置密钥: {{ totpSetupSecret }}</label>
            </div>
            <div class="form-group" style="max-width:240px">
              <label>输入验证码完成设置</label>
              <div class="form-row-2" style="grid-template-columns:1fr auto">
                <input v-model="totpSetupCode" type="text" class="form-input" placeholder="输入 TOTP 验证码" maxlength="6" style="width:100%;max-width:240px" />
                <button class="btn btn-sm btn-primary" @click="enableTOTP" :disabled="!totpSetupCode">启用 2FA</button>
              </div>
            </div>
            <button v-if="!totpSetupSecret" class="btn btn-sm btn-secondary" @click="generateTOTPSeed">生成密钥</button>
          </template>
        </div>

        <!-- Connected Sessions -->
        <div class="security-card">
          <h3 style="margin:0 0 8px;font-size:0.95rem">活跃会话</h3>
          <p style="margin:0 0 12px;font-size:0.84rem;color:var(--muted)">管理已登录你账户的设备</p>
          <div v-if="sessions.length === 0" class="empty-hint">暂无活跃会话</div>
          <div v-for="sess in sessions" :key="sess.id" class="session-row">
            <div class="session-info">
              <span class="session-device">{{ sess.device }}</span>
              <span class="session-meta">{{ sess.ip }} · {{ sess.last_active }}</span>
            </div>
            <span v-if="sess.current" class="current-badge">当前</span>
            <button v-else class="btn btn-sm btn-danger" @click="revokeSession(sess.id)">吊销</button>
          </div>
        </div>
      </div>

      <!-- P2-8: Notification Preferences -->
      <div v-if="activeSection === 'notif-prefs'" class="settings-section card animate-fade-in">
        <h2>通知偏好</h2>
        <p style="color:var(--muted);font-size:0.85rem;margin-bottom:16px">自定义系统通知方式和频率</p>

        <!-- Email Notifications -->
        <div class="security-card">
          <h3 style="margin:0 0 12px;font-size:0.95rem">📧 邮件通知</h3>
          <div class="setting-row" v-for="pref in emailNotifPrefs" :key="pref.key">
            <div>
              <div class="setting-label">{{ pref.label }}</div>
              <div class="setting-desc">{{ pref.desc }}</div>
            </div>
            <label class="toggle">
              <input type="checkbox" :checked="pref.enabled" @change="pref.enabled = !pref.enabled" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <!-- In-App Notifications -->
        <div class="security-card">
          <h3 style="margin:0 0 12px;font-size:0.95rem">🔔 站内通知</h3>
          <div class="setting-row" v-for="pref in inAppNotifPrefs" :key="pref.key">
            <div>
              <div class="setting-label">{{ pref.label }}</div>
              <div class="setting-desc">{{ pref.desc }}</div>
            </div>
            <label class="toggle">
              <input type="checkbox" :checked="pref.enabled" @change="pref.enabled = !pref.enabled" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <!-- Notification Frequency -->
        <div class="security-card">
          <h3 style="margin:0 0 12px;font-size:0.95rem">⏰ 通知频率</h3>
          <div class="form-group">
            <label>汇总频率</label>
            <select v-model="notifFrequency" class="form-select" style="width:200px">
              <option value="realtime">实时推送</option>
              <option value="hourly">每小时汇总</option>
              <option value="daily">每日摘要</option>
              <option value="weekly">每周摘要</option>
            </select>
          </div>
          <button class="btn btn-primary btn-sm" @click="saveNotifPrefs">保存偏好</button>
        </div>
      </div>

      <!-- P2.6.7: MCP Config Panel -->
      <div v-if="activeSection === 'mcp'" class="settings-section card animate-fade-in">
        <h2>MCP Server 配置</h2>
        <div class="mcp-info" v-if="mcpInfo">
          <div class="mcp-status-row">
            <span class="mcp-status-label">服务状态</span>
            <span class="service-dot online"></span>
            <span>运行中</span>
          </div>
          <div class="mcp-detail">
            <div><span class="detail-label">协议版本:</span> {{ mcpInfo.version }}</div>
            <div><span class="detail-label">服务名称:</span> {{ mcpInfo.server }} v{{ mcpInfo.server_version }}</div>
            <div><span class="detail-label">传输方式:</span> {{ mcpInfo.transport }}</div>
            <div><span class="detail-label">认证方式:</span> {{ mcpInfo.authentication }}</div>
            <div><span class="detail-label">端点:</span> <code>POST /api/mcp</code></div>
          </div>
          <div class="mcp-tools">
            <h3 style="margin:16px 0 8px;font-size:0.9rem">可用 Tools ({{ mcpInfo.tools_count || 0 }})</h3>
            <div v-for="t in mcpInfo.tools" :key="t.name" class="mcp-tool-item">
              <span class="tool-name">{{ t.name }}</span>
              <span class="tool-desc">{{ t.description }}</span>
            </div>
          </div>
          <div class="mcp-api-keys">
            <h3 style="margin:16px 0 8px;font-size:0.9rem">API Keys</h3>
            <div class="api-key-row">
              <code>mcp-dev-key-001</code>
              <span class="key-rate">100 req/min</span>
            </div>
            <div class="api-key-row">
              <code>mcp-local-default</code>
              <span class="key-rate">60 req/min</span>
            </div>
          </div>
        </div>
        <button class="btn btn-sm btn-secondary" @click="refreshMcpInfo">刷新</button>
      </div>

      <!-- P2.7.14: Export Data -->
      <div v-if="activeSection === 'export'" class="settings-section card animate-fade-in">
        <h2>数据导出</h2>
        <p style="color:var(--muted);font-size:0.85rem">导出所有作品、产品、收入数据</p>
        <div class="btn-row">
          <button class="btn btn-primary" @click="exportData('json')">导出 JSON</button>
          <button class="btn btn-secondary" @click="exportData('csv')">导出 CSV</button>
        </div>
      </div>

      <!-- P2.7.15: Danger Zone -->
      <div v-if="activeSection === 'danger'" class="settings-section card animate-fade-in danger-zone">
        <h2 style="color:#ef4444">危险区</h2>

        <div class="danger-item">
          <div>
            <div class="setting-label">注销账号</div>
            <div class="setting-desc">清除个人数据，标记账号为已删除</div>
          </div>
          <button class="btn btn-sm btn-danger" @click="showDeleteAccountModal = true">注销账号</button>
        </div>

        <div class="danger-item">
          <div>
            <div class="setting-label">清除所有数据</div>
            <div class="setting-desc">永久删除所有本地数据，不可恢复</div>
          </div>
          <button class="btn btn-sm btn-danger" @click="showClearDataModal = true">清除数据</button>
        </div>
      </div>

      <!-- Dictionary Admin -->
      <div v-if="activeSection === 'dictionary'" class="settings-section card animate-fade-in">
        <h2>字典管理</h2>
        <div class="dict-controls">
          <select v-model="selectedDictGroup" class="form-input" style="flex:1" @change="loadDictGroupItems">
            <option value="">-- 选择字典分组 --</option>
            <option v-for="g in dictGroups" :key="g.group_key" :value="g.group_key">
              {{ g.group_name }} ({{ g.module }})
            </option>
          </select>
          <button class="btn btn-sm btn-secondary" @click="loadDictGroups" :disabled="dictLoading">
            刷新
          </button>
        </div>
        <div v-if="selectedDictGroup && dictGroupItems.length > 0" class="dict-items">
          <table class="dict-table">
            <thead>
              <tr>
                <th>Key</th>
                <th>中文</th>
                <th>English</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in dictGroupItems" :key="item.id" :class="{ inactive: !item.is_active }">
                <td class="dict-key">{{ item.item_key }}</td>
                <td>{{ item.item_value }}</td>
                <td class="dict-en">{{ item.item_value_en || '-' }}</td>
                <td>
                  <span class="dict-status" :class="{ active: item.is_active }">
                    {{ item.is_active ? '启用' : '禁用' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="selectedDictGroup && dictGroupItems.length === 0 && !dictLoading" class="dict-empty">
          该分组暂无条目
        </div>
      </div>

      <!-- About -->
      <div v-if="activeSection === 'about'" class="settings-section card animate-fade-in">
        <h2>关于 OriStudio</h2>
        <p style="color: var(--muted); font-size: 0.9rem">
          OriStudio v0.2.0<br />
          个人创作者全链路助手工具<br />
          数据主权归你所有，一切数据存储在本地
        </p>
      </div>
    </div>

    <!-- Plugin Modal -->
    <div v-if="showPluginModal" class="modal-overlay" @click.self="showPluginModal = false">
      <div class="modal-card animate-scale-in" style="max-width:480px">
        <div class="modal-header"><h3>注册插件</h3><button class="modal-close-btn" @click="showPluginModal = false">×</button></div>
        <div class="form-group"><label>插件名 (ID)</label><input v-model="pluginForm.name" class="form-input" placeholder="my-plugin" /></div>
        <div class="form-group"><label>显示名称</label><input v-model="pluginForm.display_name" class="form-input" placeholder="我的插件" /></div>
        <div class="form-group"><label>版本</label><input v-model="pluginForm.version" class="form-input" placeholder="1.0.0" /></div>
        <div class="form-group"><label>描述</label><input v-model="pluginForm.description" class="form-input" placeholder="插件描述" /></div>
        <div class="form-group"><label>Hook 列表 (逗号分隔)</label><input v-model="pluginForm.hooks_str" class="form-input" placeholder="on_startup, on_product_create" /></div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showPluginModal = false">取消</button>
          <button class="btn btn-primary" @click="registerPlugin">注册</button>
        </div>
      </div>
    </div>

    <!-- Delete Account Modal -->
    <div v-if="showDeleteAccountModal" class="modal-overlay" @click.self="showDeleteAccountModal = false">
      <div class="modal-card animate-scale-in" style="max-width:400px">
        <div class="modal-header"><h3 style="color:#ef4444">注销账号</h3><button class="modal-close-btn" @click="showDeleteAccountModal = false">×</button></div>
        <p style="font-size:0.85rem;color:var(--muted)">此操作将清除您的个人数据并标记账号为已删除。请输入 DELETE 确认。</p>
        <div class="form-group">
          <input v-model="deleteAccountConfirm" class="form-input" placeholder="输入 DELETE 确认" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDeleteAccountModal = false">取消</button>
          <button class="btn btn-danger" @click="doDeleteAccount" :disabled="deleteAccountConfirm !== 'DELETE'">确认注销</button>
        </div>
      </div>
    </div>

    <!-- Clear Data Modal -->
    <div v-if="showClearDataModal" class="modal-overlay" @click.self="showClearDataModal = false">
      <div class="modal-card animate-scale-in" style="max-width:400px">
        <div class="modal-header"><h3 style="color:#ef4444">清除所有数据</h3><button class="modal-close-btn" @click="showClearDataModal = false">×</button></div>
        <p style="font-size:0.85rem;color:#ef4444">永久删除所有本地数据，此操作不可恢复！请输入 CLEAR ALL 确认。</p>
        <div class="form-group">
          <input v-model="clearDataConfirm" class="form-input" placeholder="输入 CLEAR ALL 确认" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showClearDataModal = false">取消</button>
          <button class="btn btn-danger" @click="doClearData" :disabled="clearDataConfirm !== 'CLEAR ALL'">确认清除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { useSettingsStore } from '@/stores/useSettingsStore'
import { useI18n, type Locale } from '@/composables/useI18n'
import { systemApi } from '@/api/system'
import client from '@/api/client'

const appStore = useAppStore()
const settingsStore = useSettingsStore()
const isDark = computed(() => appStore.isDark)
const storageInfo = computed(() => settingsStore.storageInfo)
const { locale, setLocale } = useI18n()
const currentLang = ref<Locale>(locale.value)

const activeSection = ref('profile')

const sections = [
  { key: 'profile', icon: '👤', label: '个人资料' },
  { key: 'appearance', icon: '🎨', label: '外观设置' },
  { key: 'linked', icon: '🔗', label: '关联账号' },
  { key: 'health', icon: '📊', label: '系统健康' },
  { key: 'data', icon: '💾', label: '数据管理' },
  { key: 'notifications', icon: '🔔', label: '通知渠道' },
  { key: 'plugins', icon: '🧩', label: '插件管理' },
  { key: 'password', icon: '🔑', label: '密码管理' },
  { key: 'security', icon: '🛡️', label: '账户安全' },
  { key: 'notif-prefs', icon: '📢', label: '通知偏好' },
  { key: 'mcp', icon: '🔌', label: 'MCP 服务' },
  { key: 'export', icon: '📤', label: '数据导出' },
  { key: 'dictionary', icon: '📚', label: '字典管理' },
  { key: 'danger', icon: '⚠️', label: '危险区' },
  { key: 'about', icon: 'ℹ️', label: '关于' },
]

// Profile
const profile = ref({ name: '创作者', bio: '', avatar_url: '', email_verified: false })
const profileSaving = ref(false)

async function fetchProfile() {
  try {
    const res = await client.get('/auth/me')
    const data = res.data.data
    if (data) {
      profile.value.name = data.username || '创作者'
      profile.value.bio = data.bio || ''
      profile.value.avatar_url = data.avatar_url || ''
      profile.value.email_verified = data.email_verified || false
    }
  } catch { /* use defaults */ }
}

async function saveProfile() {
  profileSaving.value = true
  try {
    await client.patch('/auth/me', {
      username: profile.value.name,
      bio: profile.value.bio,
    })
    ;(window as any).$toast?.show('个人资料已保存', 'success')
  } catch {
    ;(window as any).$toast?.show('保存失败', 'error')
  } finally {
    profileSaving.value = false
  }
}

// Avatar upload
async function onAvatarSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  try {
    const res = await systemApi.uploadAvatar(file)
    profile.value.avatar_url = res.data.data.avatar_url
    ;(window as any).$toast?.show('头像已上传', 'success')
  } catch {
    ;(window as any).$toast?.show('头像上传失败', 'error')
  }
}

// Email verification
const showEmailVerifyInput = ref(false)
const verifyEmailAddr = ref('')
const verifyCode = ref('')
const verifyCodeSent = ref(false)
const verifySending = ref(false)

async function sendVerifyCode() {
  if (!verifyEmailAddr.value) return
  verifySending.value = true
  try {
    const res = await systemApi.sendVerificationCode(verifyEmailAddr.value)
    verifyCodeSent.value = true
    if (!res.data.data.email_sent) {
      ;(window as any).$toast?.show(`验证码: ${res.data.message}`, 'info', 10000)
    } else {
      ;(window as any).$toast?.show('验证码已发送', 'success')
    }
  } catch {
    ;(window as any).$toast?.show('发送失败', 'error')
  } finally {
    verifySending.value = false
  }
}

async function confirmVerifyCode() {
  try {
    await systemApi.confirmVerificationCode(verifyEmailAddr.value, verifyCode.value)
    profile.value.email_verified = true
    showEmailVerifyInput.value = false
    ;(window as any).$toast?.show('邮箱验证成功', 'success')
  } catch {
    ;(window as any).$toast?.show('验证码错误', 'error')
  }
}

// Storage
const storagePercent = computed(() => {
  if (!storageInfo.value) return 0
  const used = (storageInfo.value.breakdown?.workspace || 0) + (storageInfo.value.breakdown?.database || 0)
  return Math.min((used / (storageInfo.value.total_space || 1)) * 100, 100)
})

function formatBytes(bytes: number): string {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function formatMB(mb: number): string {
  if (!mb || mb === 0) return '0 MB'
  if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB'
  return mb.toFixed(0) + ' MB'
}

function formatGB(gb: number): string {
  if (!gb) return '0 GB'
  return gb.toFixed(1) + ' GB'
}

// P2.7.1-P2.7.2: Health
const healthData = ref<any>(null)
const serviceStatus = ref<any>(null)

async function refreshHealth() {
  try {
    const [hRes, sRes] = await Promise.all([
      systemApi.healthDashboard(),
      systemApi.serviceStatus(),
    ])
    healthData.value = hRes.data.data
    serviceStatus.value = sRes.data.data
  } catch { /* toast handled by interceptor */ }
}

// Backup
const backupList = ref<any[]>([])
const backupScheduleCron = ref('0 2 * * *')

async function loadBackups() {
  try {
    const res = await systemApi.backups()
    backupList.value = res.data.data || []
  } catch { /* ignore */ }
}

async function loadBackupSchedule() {
  try {
    const res = await systemApi.backupSchedule()
    backupScheduleCron.value = res.data.data.cron
  } catch { /* ignore */ }
}

async function createBackup() {
  try {
    await systemApi.backup(false, false, false)
    ;(window as any).$toast?.show('备份已创建', 'success')
    loadBackups()
  } catch {
    ;(window as any).$toast?.show('备份失败', 'error')
  }
}

async function createEncryptedBackup() {
  try {
    await systemApi.backup(true, false, false)
    ;(window as any).$toast?.show('加密备份已创建', 'success')
    loadBackups()
  } catch {
    ;(window as any).$toast?.show('备份失败', 'error')
  }
}

async function saveBackupSchedule() {
  try {
    await systemApi.createBackupSchedule(backupScheduleCron.value, true)
    ;(window as any).$toast?.show('定时备份已配置', 'success')
  } catch {
    ;(window as any).$toast?.show('配置失败', 'error')
  }
}

async function restoreBackup(id: string) {
  try {
    await systemApi.restore(id)
    ;(window as any).$toast?.show('数据已恢复，请重启服务', 'success')
  } catch {
    ;(window as any).$toast?.show('恢复失败', 'error')
  }
}

async function deleteBackupRecord(id: string) {
  try {
    await systemApi.deleteBackup(id)
    ;(window as any).$toast?.show('备份已删除', 'success')
    loadBackups()
  } catch {
    ;(window as any).$toast?.show('删除失败', 'error')
  }
}

// P2.7.5-P2.7.6: Notifications
const smtpConfig = ref({ host: '', port: '587', tls: 'true', user: '', password: '' })
const testEmailAddr = ref('')
const emailTesting = ref(false)
const wechatConfig = ref({ appid: '', appsecret: '', templateId: '' })
const wechatTesting = ref(false)

async function saveSmtpConfig() {
  try {
    await settingsStore.updateSettings({
      smtp_host: smtpConfig.value.host,
      smtp_port: smtpConfig.value.port,
      smtp_user: smtpConfig.value.user,
      smtp_password: smtpConfig.value.password,
      smtp_tls: smtpConfig.value.tls,
    })
    ;(window as any).$toast?.show('SMTP 配置已保存', 'success')
  } catch {
    ;(window as any).$toast?.show('保存失败', 'error')
  }
}

async function testEmailSend() {
  if (!testEmailAddr.value) return
  emailTesting.value = true
  try {
    await systemApi.testEmail(testEmailAddr.value)
    ;(window as any).$toast?.show('测试邮件已发送', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '发送失败', 'error')
  } finally {
    emailTesting.value = false
  }
}

async function saveWechatConfig() {
  try {
    await settingsStore.updateSettings({
      wechat_appid: wechatConfig.value.appid,
      wechat_appsecret: wechatConfig.value.appsecret,
      wechat_template_id: wechatConfig.value.templateId,
    })
    ;(window as any).$toast?.show('微信配置已保存', 'success')
  } catch {
    ;(window as any).$toast?.show('保存失败', 'error')
  }
}

async function testWechatSend() {
  wechatTesting.value = true
  try {
    await systemApi.testWechat()
    ;(window as any).$toast?.show('微信连接测试成功', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '测试失败', 'error')
  } finally {
    wechatTesting.value = false
  }
}

// P2.7.8: Plugins
const plugins = ref<any[]>([])
const showPluginModal = ref(false)
const pluginForm = ref({ name: '', display_name: '', version: '1.0.0', description: '', hooks_str: '' })

async function loadPlugins() {
  try {
    const res = await systemApi.plugins()
    plugins.value = res.data.data || []
  } catch { /* ignore */ }
}

async function registerPlugin() {
  if (!pluginForm.value.name.trim()) {
    ;(window as any).$toast?.show('请输入插件名称', 'error')
    return
  }
  if (!/^[a-z0-9_-]+$/.test(pluginForm.value.name.trim())) {
    ;(window as any).$toast?.show('插件名称只能包含小写字母、数字、下划线和连字符', 'error')
    return
  }
  try {
    const hooks = pluginForm.value.hooks_str.split(',').map(h => h.trim()).filter(Boolean)
    await systemApi.registerPlugin({
      name: pluginForm.value.name,
      display_name: pluginForm.value.display_name,
      version: pluginForm.value.version,
      description: pluginForm.value.description,
      hooks,
    })
    showPluginModal.value = false
    pluginForm.value = { name: '', display_name: '', version: '1.0.0', description: '', hooks_str: '' }
    ;(window as any).$toast?.show('插件已注册', 'success')
    loadPlugins()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '注册失败', 'error')
  }
}

async function togglePlugin(plugin: any) {
  try {
    await systemApi.updatePlugin(plugin.id, { enabled: !plugin.enabled })
    plugin.enabled = !plugin.enabled
    ;(window as any).$toast?.show(plugin.enabled ? '插件已启用' : '插件已禁用', 'success')
  } catch {
    ;(window as any).$toast?.show('操作失败', 'error')
  }
}

async function deletePluginRecord(id: string) {
  try {
    await systemApi.deletePlugin(id)
    ;(window as any).$toast?.show('插件已删除', 'success')
    loadPlugins()
  } catch {
    ;(window as any).$toast?.show('删除失败', 'error')
  }
}

// P2.7.13: Password
const currentPassword = ref('')
const newPassword = ref('')
const newPasswordConfirm = ref('')
const passwordStrength = ref<any>(null)

const strengthColor = computed(() => {
  if (!passwordStrength.value) return 'var(--border)'
  const s = passwordStrength.value.score
  if (s >= 80) return '#16a34a'
  if (s >= 50) return '#f59e0b'
  return '#ef4444'
})

const strengthLabel = computed(() => {
  if (!passwordStrength.value) return ''
  const map: Record<string, string> = { strong: '强', medium: '中等', weak: '弱' }
  return map[passwordStrength.value.level] || ''
})

async function checkStrength() {
  if (newPassword.value.length === 0) {
    passwordStrength.value = null
    return
  }
  try {
    const res = await systemApi.checkPasswordStrength(newPassword.value)
    passwordStrength.value = res.data.data
  } catch { /* ignore */ }
}

async function changePassword() {
  if (newPassword.value !== newPasswordConfirm.value) {
    ;(window as any).$toast?.show('两次密码不一致', 'error')
    return
  }
  try {
    await client.post('/auth/change-password', {
      current_password: currentPassword.value,
      new_password: newPassword.value,
    })
    ;(window as any).$toast?.show('密码已修改', 'success')
    currentPassword.value = ''
    newPassword.value = ''
    newPasswordConfirm.value = ''
    passwordStrength.value = null
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '修改失败', 'error')
  }
}

// P2.6.7: MCP Config
const mcpInfo = ref<any>(null)

async function refreshMcpInfo() {
  try {
    const res = await systemApi.mcpInfo()
    mcpInfo.value = res.data
  } catch { /* ignore */ }
}

// P2.7.14: Export
async function exportData(format: string) {
  try {
    const res = await systemApi.exportAllData(format)
    const content = format === 'json'
      ? JSON.stringify(res.data.data, null, 2)
      : res.data.data.csv_content
    const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `oristudio-export-${new Date().toISOString().slice(0, 10)}.${format}`
    a.click()
    URL.revokeObjectURL(url)
    ;(window as any).$toast?.show('数据已导出', 'success')
  } catch {
    ;(window as any).$toast?.show('导出失败', 'error')
  }
}

// P2.7.15: Danger Zone
const showDeleteAccountModal = ref(false)
const showClearDataModal = ref(false)
const deleteAccountConfirm = ref('')
const clearDataConfirm = ref('')

async function doDeleteAccount() {
  try {
    await systemApi.deleteAccount(deleteAccountConfirm.value)
    ;(window as any).$toast?.show('账号已注销', 'success')
    showDeleteAccountModal.value = false
    localStorage.removeItem('oristudio-token')
    window.location.href = '/'
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '操作失败', 'error')
  }
}

async function doClearData() {
  try {
    await systemApi.clearAllData(clearDataConfirm.value)
    ;(window as any).$toast?.show('所有数据已清除', 'success')
    showClearDataModal.value = false
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '操作失败', 'error')
  }
}

// Linked accounts
const providers = ref([
  { key: 'google', icon: 'G', name: 'Google', bound: false, account: '' },
  { key: 'wechat', icon: '💬', name: '微信', bound: false, account: '' },
  { key: 'douyin', icon: '🎵', name: '抖音', bound: false, account: '' },
])

async function loadLinkedAccounts() {
  try {
    const res = await systemApi.authMe()
    const data = res.data.data
    if (data) {
      providers.value.forEach(p => {
        const oauthField = `oauth_${p.key}_id`
        const acctField = `oauth_${p.key}_account`
        if (data[oauthField]) {
          p.bound = true
          p.account = data[acctField] || '已绑定'
        }
      })
    }
  } catch {
    // Silently keep defaults
  }
}

// P2-8: Account Security (TOTP 2FA)
const totpEnabled = ref(false)
const totpSetupSecret = ref('')
const totpSetupCode = ref('')
const totpVerifyCode = ref('')

async function generateTOTPSeed() {
  try {
    const res = await systemApi.setupTOTP()
    totpSetupSecret.value = res.data.data?.secret || ''
    totpEnabled.value = false
    ;(window as any).$toast?.show('密钥已生成，请扫描二维码并输入验证码', 'success')
  } catch {
    ;(window as any).$toast?.show('生成密钥失败', 'error')
  }
}

async function enableTOTP() {
  if (!totpSetupCode.value) {
    ;(window as any).$toast?.show('请输入验证码', 'warning')
    return
  }
  try {
    await systemApi.verifyTOTP(totpSetupCode.value)
    totpEnabled.value = true
    totpSetupSecret.value = ''
    totpSetupCode.value = ''
    ;(window as any).$toast?.show('2FA 已启用', 'success')
  } catch {
    ;(window as any).$toast?.show('验证码无效', 'error')
  }
}

async function disableTOTP() {
  if (!totpVerifyCode.value) {
    ;(window as any).$toast?.show('请输入验证码以确认禁用', 'warning')
    return
  }
  try {
    await systemApi.disableTOTP()
    totpEnabled.value = false
    totpVerifyCode.value = ''
    ;(window as any).$toast?.show('2FA 已禁用', 'success')
  } catch {
    ;(window as any).$toast?.show('禁用失败', 'error')
  }
}

async function revokeSession(id: string) {
  try {
    await systemApi.revokeSession(id)
    sessions.value = sessions.value.filter(s => s.id !== id)
    ;(window as any).$toast?.show('会话已吊销', 'success')
  } catch {
    ;(window as any).$toast?.show('吊销失败', 'error')
  }
}

// Active sessions
const sessions = ref<any[]>([])

async function loadSessions() {
  try {
    const res = await systemApi.getSessions()
    sessions.value = res.data.data || []
  } catch {
    sessions.value = []
  }
}

// Notification preferences
const emailNotifPrefs = ref([
  { key: 'monitor_alert', label: '侵权监测告警', desc: '发现疑似侵权时发送邮件通知', enabled: true },
  { key: 'notary_complete', label: '存证完成通知', desc: '区块链存证完成后发送邮件', enabled: true },
  { key: 'order_update', label: '订单状态变更', desc: '委托订单状态更新时通知', enabled: true },
  { key: 'system_announce', label: '系统公告', desc: '重要系统维护和公告', enabled: false },
])

const inAppNotifPrefs = ref([
  { key: 'monitor_alert', label: '侵权监测告警', desc: '在站内显示侵权通知', enabled: true },
  { key: 'notary_complete', label: '存证完成通知', desc: '在站内显示存证完成通知', enabled: true },
  { key: 'order_update', label: '订单状态变更', desc: '在站内显示订单更新通知', enabled: true },
  { key: 'message', label: '委托消息', desc: '委托沟通消息通知', enabled: true },
])

const notifFrequency = ref('realtime')

// Load saved notification preferences from server
async function loadNotifPrefs() {
  try {
    const resp = await client.get('/system/notification/prefs')
    const prefs = resp.data.data
    if (prefs) {
      // Apply saved preferences to the UI arrays
      ;(prefs.email || []).forEach((p: { key: string; enabled: boolean }) => {
        const item = emailNotifPrefs.value.find(e => e.key === p.key)
        if (item) item.enabled = p.enabled
      })
      ;(prefs.in_app || []).forEach((p: { key: string; enabled: boolean }) => {
        const item = inAppNotifPrefs.value.find(e => e.key === p.key)
        if (item) item.enabled = p.enabled
      })
      if (prefs.frequency) notifFrequency.value = prefs.frequency
    }
  } catch {
    // Use defaults if loading fails
  }
}

async function saveNotifPrefs() {
  try {
    await systemApi.updateNotifPrefs({
      email: emailNotifPrefs.value.map(p => ({ key: p.key, enabled: p.enabled })),
      in_app: inAppNotifPrefs.value.map(p => ({ key: p.key, enabled: p.enabled })),
      frequency: notifFrequency.value,
    })
    ;(window as any).$toast?.show('通知偏好已保存', 'success')
  } catch {
    ;(window as any).$toast?.show('保存失败', 'error')
  }
}

async function bindProvider(provider: string) {
  try {
    let url = ''
    if (provider === 'google') {
      const res = await systemApi.googleLoginUrl()
      url = res.data.data?.url
    } else if (provider === 'wechat') {
      const res = await systemApi.wechatQrcode()
      url = res.data.data?.qr_url
    } else if (provider === 'douyin') {
      const res = await systemApi.douyinLoginUrl()
      url = res.data.data?.url
    }
    if (url) {
      window.open(url, '_blank')
      ;(window as any).$toast?.show('请在弹出窗口中完成授权', 'info')
    } else {
      // Fallback: show config hint
      ;(window as any).$toast?.show(`${provider} OAuth 尚未配置，请联系管理员`, 'warning')
    }
  } catch {
    ;(window as any).$toast?.show('绑定失败', 'error')
  }
}

async function unbindProvider(provider: string) {
  try {
    await systemApi.unbindProvider(provider)
    const p = providers.value.find(x => x.key === provider)
    if (p) { p.bound = false; p.account = '' }
    ;(window as any).$toast?.show('已解绑', 'success')
  } catch {
    ;(window as any).$toast?.show('解绑失败', 'error')
  }
}

// Dictionary admin
const dictGroups = ref<any[]>([])
const selectedDictGroup = ref('')
const dictGroupItems = ref<any[]>([])
const dictLoading = ref(false)

async function loadDictGroups() {
  dictLoading.value = true
  try {
    const res = await systemApi.dictGroups()
    dictGroups.value = res.data.data || []
  } catch { /* toast handled by interceptor */ } finally {
    dictLoading.value = false
  }
}

async function loadDictGroupItems() {
  if (!selectedDictGroup.value) {
    dictGroupItems.value = []
    return
  }
  dictLoading.value = true
  try {
    const res = await systemApi.dictGroupItems(selectedDictGroup.value)
    dictGroupItems.value = res.data.data?.items || []
  } catch { /* toast handled by interceptor */ } finally {
    dictLoading.value = false
  }
}

// Theme
function toggleTheme() {
  appStore.toggleTheme()
}

// P3.3.5: Language switcher
function changeLang() {
  setLocale(currentLang.value)
  ;(window as any).$toast?.show(
    currentLang.value === 'zh-CN' ? '已切换为中文' : 'Switched to English',
    'success'
  )
}

onMounted(() => {
  settingsStore.fetchStorage()
  fetchProfile()
  loadDictGroups()
  loadBackups()
  loadBackupSchedule()
  loadPlugins()
  refreshHealth()
  refreshMcpInfo()
  loadLinkedAccounts()
  loadSessions()
  loadNotifPrefs()
})
</script>

<style scoped>
.settings-view { display: flex; gap: 24px; }
@media (max-width: 768px) {
  .settings-view { flex-direction: column; }
  .settings-sidebar { width: 100%; flex-direction: row; flex-wrap: wrap; gap: 2px; overflow-x: auto; padding-bottom: 8px; }
  .settings-nav-item { font-size: 0.78rem; padding: 6px 10px; white-space: nowrap; }
  .settings-nav-item span:first-child { display: none; }
  .settings-section { padding: 16px; }
  .form-input, .form-textarea { max-width: 100%; }
  .health-grid { grid-template-columns: 1fr; }
  .form-row-2 { grid-template-columns: 1fr; }
  .modal-card { padding: 16px; }
}
.settings-sidebar {
  width: 200px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: 4px;
}
.settings-nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px; border-radius: var(--radius-sm);
  cursor: pointer; font-size: 0.9rem; font-weight: 500;
  color: var(--muted); transition: all 0.2s;
}
.settings-nav-item:hover { background: oklch(0 0 0 / 0.04); color: var(--fg); }
.settings-nav-item.active { background: var(--surface); color: var(--accent); font-weight: 600; box-shadow: 0 1px 4px oklch(0 0 0 / 0.04); }
.settings-content { flex: 1; min-width: 0; }
.settings-section { padding: 24px; display: flex; flex-direction: column; gap: 16px; }
.settings-section h2 { font-size: 1.1rem; margin: 0; }
.setting-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; }
.setting-label { font-weight: 600; font-size: 0.9rem; }
.setting-desc { font-size: 0.8rem; color: var(--muted); margin-top: 2px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input, .form-textarea {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none; max-width: 400px;
}
.form-input:focus, .form-textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1); }
.form-textarea { resize: vertical; }
.form-select { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.88rem; background: var(--surface); color: var(--fg); }

/* Toggle switch */
.toggle { position: relative; display: inline-block; width: 48px; height: 26px; cursor: pointer; }
.toggle input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute; inset: 0;
  background: var(--border); border-radius: 13px; transition: 0.3s;
}
.toggle-slider::before {
  content: ''; position: absolute; top: 3px; left: 3px;
  width: 20px; height: 20px; border-radius: 50%;
  background: #fff; transition: 0.3s; box-shadow: 0 1px 3px oklch(0 0 0 / 0.15);
}
.toggle input:checked + .toggle-slider { background: var(--accent); }
.toggle input:checked + .toggle-slider::before { transform: translateX(22px); }

/* Storage */
.storage-info { margin-top: 8px; }
.storage-bar { height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.storage-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.5s; }
.storage-text { font-size: 0.78rem; color: var(--muted); margin-top: 6px; }

/* Linked accounts */
.linked-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 0; border-bottom: 1px solid var(--border);
}
.linked-card:last-child { border-bottom: none; }
.linked-info { display: flex; align-items: center; gap: 12px; }
.linked-icon {
  width: 36px; height: 36px; border-radius: 50%;
  background: oklch(96% 0.004 240); display: flex;
  align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.9rem;
}
.linked-name { font-weight: 600; font-size: 0.9rem; }
.linked-status { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }
.linked-status.bound { color: var(--accent); }

/* Dictionary admin */
.dict-controls { display: flex; gap: 8px; align-items: center; }
.dict-items { margin-top: 8px; }
.dict-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.dict-table th {
  text-align: left; padding: 8px 12px; border-bottom: 2px solid var(--border);
  font-weight: 600; color: var(--muted); font-size: 0.8rem;
}
.dict-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); }
.dict-table tr.inactive td { opacity: 0.5; }
.dict-key { font-family: monospace; font-size: 0.82rem; }
.dict-en { color: var(--muted); font-size: 0.82rem; }
.dict-status {
  font-size: 0.78rem; padding: 2px 8px; border-radius: 10px;
  background: oklch(95% 0.01 240); color: var(--muted);
}
.dict-status.active { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
.dict-empty { text-align: center; padding: 32px; color: var(--muted); font-size: 0.9rem; }

/* Health Dashboard (P2.7.1) */
.health-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
@media (max-width: 600px) { .health-grid { grid-template-columns: 1fr; } }
.health-card {
  padding: 16px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  text-align: center; transition: border-color 0.3s;
}
.health-card.warning { border-color: #f59e0b; }
.health-card.danger { border-color: #ef4444; }
.health-label { font-size: 0.78rem; color: var(--muted); font-weight: 600; margin-bottom: 4px; }
.health-value { font-size: 1.8rem; font-weight: 700; font-family: var(--font-display); }
.health-sub { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }
.health-bar { height: 6px; background: var(--border); border-radius: 3px; margin-top: 8px; overflow: hidden; }
.health-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
.service-status-row { margin-top: 16px; }
.service-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; font-size: 0.84rem; }
.service-name { flex: 0 0 100px; font-weight: 600; }
.service-dot { width: 8px; height: 8px; border-radius: 50%; }
.service-dot.online { background: #16a34a; }
.service-dot.offline { background: #ef4444; }
.service-status-text { color: var(--muted); font-size: 0.8rem; }
.actions-row { margin-top: 8px; }
.actions-bar { display: flex; justify-content: flex-end; gap: 8px; }

/* Backup (P2.7.3-P2.7.4) */
.btn-row { display: flex; gap: 8px; }
.schedule-row { display: flex; gap: 8px; align-items: center; }
.backup-list { margin-top: 16px; }
.backup-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  margin-bottom: 4px; font-size: 0.82rem;
}
.backup-info { display: flex; flex-direction: column; gap: 2px; }
.backup-date { font-weight: 600; }
.backup-type { font-size: 0.72rem; color: var(--muted); }
.backup-size { color: var(--muted); font-size: 0.78rem; }
.backup-actions { display: flex; gap: 4px; }

/* Notification Channels (P2.7.5-P2.7.6) */
.notif-channel { padding: 16px 0; border-bottom: 1px solid var(--border); }
.notif-channel:last-child { border-bottom: none; }
.notif-channel h3 { margin: 0 0 12px; font-size: 0.95rem; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.test-row { display: flex; gap: 8px; align-items: flex-end; }

/* Plugin Framework (P2.7.8) */
.plugin-list { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.plugin-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  transition: opacity 0.2s;
}
.plugin-card.disabled { opacity: 0.5; }
.plugin-info { flex: 1; }
.plugin-name { font-weight: 600; font-size: 0.9rem; }
.plugin-version { font-size: 0.75rem; color: var(--muted); }
.plugin-desc { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }
.plugin-hooks { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px; }
.plugin-hook-tag {
  font-size: 0.68rem; padding: 1px 6px; border-radius: 10px;
  background: oklch(56% 0.12 170 / 0.1); color: oklch(56% 0.12 170);
  font-family: monospace;
}
.plugin-actions { display: flex; align-items: center; gap: 8px; }
.empty-hint { text-align: center; padding: 32px; color: var(--muted); font-size: 0.85rem; }

/* Password Strength (P2.7.13) */
.strength-bar-row { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.strength-bar { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.strength-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
.strength-text { font-size: 0.78rem; font-weight: 600; }

/* MCP Config (P2.6.7) */
.mcp-status-row { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; }
.mcp-status-label { font-weight: 600; }
.mcp-detail { margin-top: 12px; font-size: 0.84rem; line-height: 1.8; }
.detail-label { font-weight: 600; color: var(--muted); }
.mcp-tool-item {
  display: flex; align-items: baseline; gap: 12px;
  padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 0.82rem;
}
.tool-name { font-family: monospace; font-weight: 600; color: var(--accent); min-width: 200px; }
.tool-desc { color: var(--muted); }
.api-key-row { display: flex; align-items: baseline; gap: 12px; padding: 4px 0; font-size: 0.82rem; }
.api-key-row code { background: var(--surface); padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; }
.key-rate { color: var(--muted); font-size: 0.75rem; }

/* Email verification */
.avatar-upload-row { display: flex; align-items: center; gap: 12px; }
.avatar-preview img { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; border: 2px solid var(--border); }
.avatar-placeholder { width: 48px; height: 48px; border-radius: 50%; background: var(--surface); display: flex; align-items: center; justify-content: center; font-size: 1.5rem; border: 2px dashed var(--border); }
.avatar-upload-btn { cursor: pointer; position: relative; overflow: hidden; }
.avatar-upload-btn input { position: absolute; left: -9999px; }
.email-verify-row { display: flex; align-items: center; gap: 8px; }
.verified-badge { color: #16a34a; font-weight: 600; font-size: 0.82rem; }
.unverified-badge { color: var(--muted); font-size: 0.82rem; }
.email-verify-form { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.verify-code-row { display: flex; gap: 8px; align-items: center; }

/* Danger Zone */
.danger-zone { border: 1px solid #ef4444; }
.danger-item { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--border); }
.danger-item:last-child { border-bottom: none; }
.btn-danger { background: #ef4444; color: #fff; border: none; }
.btn-danger:hover { background: #dc2626; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; max-height:90vh; overflow-y:auto; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; }

/* Buttons */
.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
</style>

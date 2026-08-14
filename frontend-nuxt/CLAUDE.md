# OriSpark (frontend-nuxt) - 交易后台

## 系统定位

**OriSpark 是非创作者专属交易后台**，面向8种市场参与角色提供作品衍生品交易服务。

### 目标用户（8种角色）
1. **运营方 (operator)** - 作品包装、授权、分润
2. **贸易商/采购方 (trader)** - 合约认购、采购
3. **法务代表 (legal_rep)** - 合同审核、争议处理
4. **税务代理 (tax_agent)** - 税费计算、申报
5. **物流方 (logistics)** - 发货、跟踪、签收
6. **保险方 (insurer)** - 承保、理赔
7. **支付托管方 (payment_provider)** - 资金托管、结算
8. **平台方 (platform)** - 运营管理、数据监控

### 核心功能
- 合约行情：金融化展示、价格趋势
- 合约交易：认购、成交、第三方托管
- 运营合作：包装、授权、分润锁定
- 工厂对接：POD、生产、质检、物流
- 数据看板：创作者排行、品类趋势、行业报告
- 订单履约：支付、结算、发票管理

### 登录入口
- 地址：http://localhost:3000/auth/login
- 账号：local@oristudio / local

### 按钮文案
- ✅ 正确：**"进入 OriSpark"**
- ❌ 错误：不要写"进入 OriStudio"

### 技术栈
- Nuxt 3 SSR + TypeScript
- Nitro 服务器端渲染
- Pinia 状态管理

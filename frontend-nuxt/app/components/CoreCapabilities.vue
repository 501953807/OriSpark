<template>
  <div class="capability-grid">
    <div
      v-for="(cap, i) in capabilities"
      :key="i"
      class="capability-card"
    >
      <div class="capability-icon">{{ cap.icon }}</div>
      <h3 class="capability-title">{{ cap.title }}</h3>
      <p class="capability-desc">{{ cap.description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const capabilities = [
  { icon: '🔍', title: '侵权风险预警', description: '提示词检测、LoRA 权属检查、商标/Logo 碰撞、参考图相似度' },
  { icon: '📝', title: 'AIGC 痕迹审计', description: '三层证据体系、MCP 事件流、自声明系统、贡献度评分' },
  { icon: '🔏', title: '自动存证 + 监测', description: 'C2PA Manifest、TSA 时间戳、区块链存证、全网扫描' },
  { icon: '🛡️', title: '四级版权防御', description: 'L1 基础标记 → L2 平台工具 → L3 法律注册 → L4 技术保护' },
  { icon: '🤝', title: '合约撮合', description: '合约挂牌、主动撮合引擎、第三方支付托管、保险承保' },
  { icon: '🔄', title: 'Fork-Merge 协同创作', description: '半成品仓库、Merge Request、联合确权、分润锁定' },
  { icon: '📡', title: '媒体分发与回流', description: '多平台发布、隐形水印、Reverse Traceback Router' },
  { icon: '💰', title: '全球税收分润清算', description: '市场化分润、第三方托管、多币种结算、税务代理' },
  { icon: '⭐', title: 'SCR 分布式信誉', description: '链上履约记录、信誉评分、信用等级、奖惩机制' },
]
</script>

<style scoped>
.capability-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.capability-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.capability-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.capability-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px;
}

.capability-desc {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  margin: 0;
}

@media (max-width: 768px) {
  .capability-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .capability-grid {
    grid-template-columns: 1fr;
  }
}
</style>

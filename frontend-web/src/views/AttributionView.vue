<template>
  <div class="attribution-view">
    <n-page title="归因分析">
      <n-card v-if="summary">
        <n-descriptions label-placement="left" :column="2" bordered>
          <n-descriptions-item label="总点击量">{{ summary.total_clicks }}</n-descriptions-item>
          <n-descriptions-item label="独立访客">{{ summary.unique_visitors }}</n-descriptions-item>
          <n-descriptions-item label="转化率">
            {{ (summary.conversion_rate * 100).toFixed(2) }}%
          </n-descriptions-item>
          <n-descriptions-item label="总转化额">
            ${{ summary.total_conversion_value.toFixed(2) }}
          </n-descriptions-item>
        </n-descriptions>

        <!-- 事件分布 -->
        <h3 style="margin: 16px 0 8px">事件分布</h3>
        <n-space wrap>
          <n-tag v-for="(count, type) in summary.event_breakdown" :key="type" size="large">
            {{ eventTypeLabel(type) }}: {{ count }}
          </n-tag>
        </n-space>

        <!-- 国家 TOP10 -->
        <h3 style="margin: 16px 0 8px">来源国家 TOP10</h3>
        <n-table>
          <template #header-columns>
            <n-th>排名</n-th>
            <n-th>国家</n-th>
            <n-th>次数</n-th>
          </template>
          <template #row-columns="{ row, index }">
            <n-td>{{ index + 1 }}</n-td>
            <n-td>{{ row.country }}</n-td>
            <n-td>{{ row.count }}</n-td>
          </template>
        </n-table>
      </n-card>

      <n-result v-else status="info" title="请选择一个链接查看分析" description="从分发 Hub 跳转到此页面并传入 linkId 参数" />
    </n-page>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { NPage, NCard, NDescriptions, NDescriptionsItem, NSpace, NTag, NTable, NTh, NTd, NResult } from 'naive-ui'
import api from '@/api/reverseTrace'

const route = useRoute()
const summary = ref<any>(null)

function eventTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    click: '点击',
    view: '浏览',
    share: '分享',
    purchase: '购买',
    signup: '注册',
  }
  return labels[type] || type
}

onMounted(async () => {
  const linkId = route.query.linkId as string
  if (!linkId) return

  try {
    const res = await api.getAnalytics(linkId)
    summary.value = res.data
  } catch {
    // ignore
  }
})
</script>

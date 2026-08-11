<template>
  <div class="attribution-view">
    <div class="card" v-if="summary">
        <div class="descriptions">
          <div class="desc-row">
            <span class="desc-label">总点击量</span>
            <span class="desc-value">{{ summary.total_clicks }}</span>
          </div>
          <div class="desc-row">
            <span class="desc-label">独立访客</span>
            <span class="desc-value">{{ summary.unique_visitors }}</span>
          </div>
          <div class="desc-row">
            <span class="desc-label">转化率</span>
            <span class="desc-value">{{ (summary.conversion_rate * 100).toFixed(2) }}%</span>
          </div>
          <div class="desc-row">
            <span class="desc-label">总转化额</span>
            <span class="desc-value">${{ summary.total_conversion_value.toFixed(2) }}</span>
          </div>
        </div>

        <!-- 事件分布 -->
        <h3 style="margin: 16px 0 8px">事件分布</h3>
        <div class="tag-wrap">
          <span v-for="(count, type) in summary.event_breakdown" :key="String(type)" class="badge badge-large">
            {{ eventTypeLabel(String(type)) }}: {{ count }}
          </span>
        </div>

        <!-- 国家 TOP10 -->
        <h3 style="margin: 16px 0 8px">来源国家 TOP10</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>排名</th>
              <th>国家</th>
              <th>次数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in summary.country_breakdown" :key="index">
              <td>{{ index + 1 }}</td>
              <td>{{ row.country }}</td>
              <td>{{ row.count }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    <div class="status-msg status-msg-info" v-else>请选择一个链接查看分析<br><small>从分发 Hub 跳转到此页面并传入 linkId 参数</small></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
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

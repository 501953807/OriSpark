<script setup lang="ts">
import { ref, computed } from 'vue'

interface Material {
  id: string
  material_name: string
  material_category: string
  quantity_on_hand: number
  reorder_level: number
  unit?: string
  supplier?: string
  unit_cost?: number
  location?: string
}

const props = defineProps<{ materials?: Material[] }>()
const lowStock = computed(() => props.materials?.filter(m => m.quantity_on_hand < m.reorder_level) || [])

const onReceive = (name: string) => window.alert(`入库: ${name}`)
const onIssue = (name: string) => window.alert(`出库: ${name}`)
</script>

<template>
  <div class="material-inventory-panel">
    <div class="panel-header">
      <h3>原材料库存</h3>
      <button class="btn btn-primary btn-sm">+ 入库登记</button>
    </div>
    <div v-if="lowStock.length > 0" class="warning-banner">⚠️ {{ lowStock.length }} 种材料低于最低库存线</div>
    <table v-if="materials?.length" class="inventory-table">
      <thead><tr><th>材料名</th><th>分类</th><th>当前数量</th><th>单位</th><th>最低库存线</th><th>供应商</th><th>位置</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="mat in materials" :key="mat.id" :class="{ 'low-stock': mat.quantity_on_hand < mat.reorder_level }">
          <td>{{ mat.material_name }}</td><td>{{ mat.material_category }}</td>
          <td>{{ mat.quantity_on_hand }}</td><td>{{ mat.unit || '个' }}</td>
          <td>{{ mat.reorder_level }}</td><td>{{ mat.supplier || '-' }}</td><td>{{ mat.location || '-' }}</td>
          <td class="actions"><button class="btn-link" @click="onReceive(mat.material_name)">入库</button><button class="btn-link" @click="onIssue(mat.material_name)">出库</button></td>
        </tr>
      </tbody>
    </table>
    <div v-if="!materials?.length" class="empty-state">暂无材料记录</div>
  </div>
</template>

<style scoped>
.material-inventory-panel { padding: 16px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.warning-banner { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 13px; }
.inventory-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.inventory-table th, .inventory-table td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; text-align: left; }
.inventory-table th { background: #f9fafb; font-weight: 600; }
.low-stock { background: #fef2f2; }
.actions { display: flex; gap: 8px; }
.empty-state { padding: 32px; text-align: center; color: #9ca3af; }
.btn-sm { padding: 4px 12px; font-size: 13px; }
</style>

<template>
  <div class="card">
    <div class="modal-header">
      <h3>税务代理管理</h3>
      <button class="btn btn-sm btn-primary" @click="showCreate = true">新增代理</button>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>名称</th>
          <th>许可证</th>
          <th>服务区域</th>
          <th>费率</th>
          <th>状态</th>
        </tr>
      </thead>
      <tbody v-if="!loading">
        <tr v-for="row in agents" :key="row.id">
          <td>{{ row.id }}</td>
          <td>{{ row.name }}</td>
          <td>{{ row.license_no }}</td>
          <td>{{ (row.service_areas as unknown[])?.join(', ') || '' }}</td>
          <td>{{ ((row.fee_rate as number) * 100).toFixed(1) }}%</td>
          <td>{{ row.status }}</td>
        </tr>
      </tbody>
      <tbody v-else>
        <tr><td colspan="6" class="text-center">加载中...</td></tr>
      </tbody>
    </table>

    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-card modal-card-lg">
        <div class="modal-header"><h3>新增税务代理</h3></div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">参与者 ID</label>
            <input class="form-input" v-model="newAgent.participant_id" />
          </div>
          <div class="form-group">
            <label class="form-label">名称</label>
            <input class="form-input" v-model="newAgent.name" />
          </div>
          <div class="form-group">
            <label class="form-label">许可证号</label>
            <input class="form-input" v-model="newAgent.license_no" />
          </div>
          <div class="form-group">
            <label class="form-label">服务区域 (逗号分隔)</label>
            <input class="form-input" v-model="newAgent.service_areas_str" placeholder="CN,US,EU" />
          </div>
          <div class="form-group">
            <label class="form-label">费率 (%)</label>
            <input class="form-input" type="number" v-model.number="newAgent.fee_rate" :min="0" :max="100" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="handleCreate">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { taxApi } from '@/api/tax'

const loading = ref(false)
const agents = ref<any[]>([])
const showCreate = ref(false)

const newAgent = reactive({
  participant_id: '',
  name: '',
  license_no: '',
  service_areas_str: '',
  fee_rate: 5,
})

async function fetchAgents() {
  loading.value = true
  try {
    const res = await taxApi.taxAgentApi.list()
    agents.value = res.data || []
  } catch {
    // ignore
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  try {
    await taxApi.taxAgentApi.create({
      ...newAgent,
      service_areas: newAgent.service_areas_str.split(',').map((s: string) => s.trim()).filter(Boolean),
    })
    console.warn('创建成功')
    showCreate.value = false
    fetchAgents()
  } catch {
    console.warn('创建失败')
  }
}

fetchAgents()
</script>

<template>
  <n-card title="税务代理管理">
    <template #header-extra>
      <n-button type="primary" size="small" @click="showCreate = true">新增代理</n-button>
    </template>

    <n-data-table :columns="columns" :data="agents" :loading="loading" />

    <n-modal v-model:show="showCreate" preset="dialog" title="新增税务代理">
      <n-form :model="newAgent" label-placement="left" label-width="100">
        <n-form-item label="参与者 ID">
          <n-input v-model:value="newAgent.participant_id" />
        </n-form-item>
        <n-form-item label="名称">
          <n-input v-model:value="newAgent.name" />
        </n-form-item>
        <n-form-item label="许可证号">
          <n-input v-model:value="newAgent.license_no" />
        </n-form-item>
        <n-form-item label="服务区域 (逗号分隔)">
          <n-input v-model:value="newAgent.service_areas_str" placeholder="CN,US,EU" />
        </n-form-item>
        <n-form-item label="费率 (%)">
          <n-input-number v-model:value="newAgent.fee_rate" :min="0" :max="100" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" @click="handleCreate">创建</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { NCard, NButton, NDataTable, NModal, NForm, NFormItem, NInput, NInputNumber, NSpace } from 'naive-ui'
import { useMessage } from 'naive-ui'
import { taxApi } from '@/api/tax'

const message = useMessage()
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

const columns = [
  { title: 'ID', key: 'id' },
  { title: '名称', key: 'name' },
  { title: '许可证', key: 'license_no' },
  { title: '服务区域', key: 'service_areas', render(row) { return (row.service_areas || []).join(', ') } },
  { title: '费率', key: 'fee_rate', render(row) { return `${(row.fee_rate * 100).toFixed(1)}%` } },
  { title: '状态', key: 'status' },
]

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
    message.success('创建成功')
    showCreate.value = false
    fetchAgents()
  } catch {
    message.error('创建失败')
  }
}

fetchAgents()
</script>

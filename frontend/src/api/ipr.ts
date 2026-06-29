import client from './client'

export const iprApi = {
  // IP 登记 CRUD
  registrations: (params?: any) =>
    client.get('/ipr/registrations', { params }),

  getRegistration: (id: string) =>
    client.get(`/ipr/registrations/${id}`),

  create: (data: any) =>
    client.post('/ipr/registrations', data),

  update: (id: string, data: any) =>
    client.patch(`/ipr/registrations/${id}`, data),

  delete: (id: string) =>
    client.delete(`/ipr/registrations/${id}`),

  // 指引
  guidelines: (jurisdiction?: string) =>
    client.get('/ipr/guidelines', { params: { jurisdiction } }),

  guidelinesByType: (ipType: string, jurisdiction: string = 'cn') =>
    client.get(`/ipr/guidelines/${ipType}`, { params: { jurisdiction } }),

  // 类别推荐
  recommendClasses: (data: { tags: string[]; description?: string; creator_type?: string; jurisdiction?: string }) =>
    client.post('/ipr/recommend/classes', data),

  niceClasses: (creativeOnly: boolean = false) =>
    client.get('/ipr/nice-classes', { params: { creative_only: creativeOnly } }),

  classGoods: (classNo: number) =>
    client.get(`/ipr/nice-classes/${classNo}/goods`),

  recommendStrategies: () =>
    client.get('/ipr/recommend/strategies'),

  // 智能申请助手
  prefill: (data: { work_id: string; ip_type: string; jurisdiction?: string }) =>
    client.post('/ipr/assistant/prefill', data),

  validate: (data: { ip_type: string; jurisdiction: string; fields: Record<string, any> }) =>
    client.post('/ipr/assistant/validate', data),

  generate: (data: { ip_type: string; jurisdiction: string; fields: Record<string, any> }) =>
    client.post('/ipr/assistant/generate', data),

  export: (data: { ip_type: string; jurisdiction: string; lawyer_consulted?: string }) =>
    client.post('/ipr/assistant/export', data),

  // 资产仪表盘
  portfolio: () =>
    client.get('/ipr/portfolio'),

  reminders: () =>
    client.get('/ipr/reminders'),

  dashboard: () =>
    client.get('/ipr/dashboard'),

  // 路径信息
  paths: () =>
    client.get('/ipr/paths'),

  // P2.4: 费用计算器
  feeCalculator: (data: {
    ip_type: string;
    jurisdictions: string[];
    classes?: number[];
    design_count?: number;
    wipo_designations?: string[];
    is_color?: boolean;
  }) => client.post('/ipr/fee-calculator', data),

  // P2.4: 申请表模板
  templates: (params?: { ip_type?: string; jurisdiction?: string }) =>
    client.get('/ipr/templates', { params }),

  templateDetail: (id: string) =>
    client.get(`/ipr/templates/${id}`),

  // P2.4: 商标近似检索
  similaritySearch: (params: { query: string; class_no?: string }) =>
    client.get('/ipr/similarity-search', { params }),
}

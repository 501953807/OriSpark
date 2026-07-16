/** 案例知识库类型定义 */

export interface CaseStudy {
  id: string
  title: string
  category: string
  case_type: 'success' | 'lesson'
  description?: string
  key_metrics?: Record<string, unknown>
  tags: string[]
  takeaways: string[]
  source_url?: string
  created_at: string
  updated_at: string
}

export interface CaseStats {
  total: number
  by_category: Record<string, number>
  by_type: Record<string, number>
  top_tags: Array<{name: string; count: number}>
}

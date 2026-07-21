export interface CommissionProject {
  id: string
  user_id: string
  title: string
  description?: string
  client_name?: string
  status: string
  // Legacy / order-derived fields (may be populated from orders or payment_terms)
  amount?: number
  currency?: string
  due_date?: string
  priority?: string
  work_title?: string
  milestones?: Milestone[]
  payment_terms?: Record<string, unknown>[]
  orders?: CommissionOrder[]
  messages?: CommissionMessage[]
  order_count?: number
  message_count?: number
  created_at?: string
  updated_at?: string
}

export interface CommissionOrder {
  id: string
  project_id: string
  order_type: string
  amount: number
  status: string
  created_at?: string
}

export interface CommissionMessage {
  id: string
  project_id: string
  sender_id: string
  content: string
  created_at?: string
}

export interface Milestone {
  id: string
  commission_id: string
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'overdue'
  due_date?: string
  description?: string
  order_index: number
  created_at?: string
  updated_at?: string
}

export interface Payment {
  id: string
  commission_id: string
  milestone_id?: string
  amount: number
  method: string
  status: 'pending' | 'received' | 'partial' | 'overdue'
  paid_at?: string
  notes?: string
  created_at?: string
}

export interface Revision {
  id: string
  commission_id: string
  description: string
  client_feedback?: string
  files?: string[]
  created_by: string
  created_at?: string
}

export interface TimelineEvent {
  type: 'milestone' | 'payment' | 'revision'
  id: string
  title: string
  description?: string
  date?: string
  status?: string
}

export interface DashboardStats {
  active_count: number
  pending_payment: number
  monthly_revenue: number
  avg_ticket: number
}

export interface CalendarEvent {
  id: string
  title: string
  date: string
  type: 'milestone_due' | 'payment_received'
}

export interface CommissionFilters {
  user_id?: string
  status?: string
}

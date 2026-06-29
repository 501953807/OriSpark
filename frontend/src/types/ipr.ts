export interface IPRegistration {
  id: string
  work_id: string | null
  ip_type: 'copyright' | 'trademark' | 'patent'
  application_no: string | null
  filing_date: string | null
  status: string
  category_info: Record<string, any> | null
  official_fee: number
  agent_name: string | null
  notes: string | null
  created_at: string
}

export interface IPRGuidelines {
  copyright: {
    title: string
    description: string
    materials: string[]
    platform_url: string
    fee_range: string
    estimated_duration: string
  }
  trademark: {
    title: string
    description: string
    common_categories: Record<string, string>
    platform_url: string
    fee_range: string
    estimated_duration: string
    disclaimer: string
  }
  categories: Record<string, string>
}

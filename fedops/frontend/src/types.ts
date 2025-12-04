export interface Opportunity {
  id: number
  notice_id: string
  title: string
  solicitation_number: string
  department: string
  sub_tier: string
  office: string
  posted_date: string
  type: string
  base_type: string
  archive_type: string
  archive_date: string
  type_of_set_aside_description: string
  type_of_set_aside: string
  response_deadline: string
  naics_code: string
  classification_code: string
  active: string
  award: any
  point_of_contact: any[]
  description: string
  organization_type: string
  office_address: any
  place_of_performance: any
  additional_info_link: string
  ui_link: string
  links: any[]
  resource_links: string[]
  full_response: any
  source?: string  // SAM.gov, Manual, eBuy, eFast, SeaPort, etc.
}

export interface UnifiedOpportunity {
  source: 'SAM.gov' | 'USASpending'
  id: string
  title: string
  description: string
  status: string
  date: string
  amount?: number
  recipient?: string
  agency: string
  type: string
  raw: any
}

export interface OpportunityComment {
  id: number
  opportunity_id: number
  text: string
  created_at: string
}

export interface Entity {
  uei: string
  legal_business_name: string
  cage_code?: string
  entity_type?: string
  is_primary?: boolean
  notes?: string
  logo_url?: string
  last_synced_at?: string
  similarity_score?: number
  full_response?: any
  
  // Partner Search Fields
  revenue?: number
  capabilities?: {
    type: string
    code?: string
    description?: string
  }[]
  locations?: {
    type: string
    address: any
  }[]
  web_addresses?: any[]
  personnel_count?: number
  business_types?: {
    code: string
    description: string
  }[]
}

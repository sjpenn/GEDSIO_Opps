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
  entity_type?: 'PARTNER' | 'COMPETITOR' | 'OBSERVING' | 'OTHER'
  is_primary?: boolean
  notes?: string
  logo_url?: string
  last_synced_at?: string
  similarity_score?: number
  last_active_at?: string
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

export interface EntitySearchTerm {
  term: string
  searched_at: string
  result_count?: number
}

export interface EntityProfileSummary {
  uei: string;
  legal_business_name: string;
  is_primary: boolean;
  logo_url?: string;
  cage_code?: string;
  entity_type?: string;
  document_count: number;
  document_types: Record<string, number>;
  last_active_at?: string;
}

export interface PastPerformance {
  id: number;
  title: string;
  status: string;
  questionnaire_data: Record<string, any>;
  created_at: string;
  updated_at?: string;
  entity_uei?: string;
  source_document_id?: number;
}

export interface EntityAward {
  award_id: string;
  recipient_uei: string;
  total_obligation?: number;
  description?: string;
  award_date?: string;
  awarding_agency?: string;
  award_type?: string;
  solicitation_id?: string;
}

export interface CompanyProfile {
  uei: string;
  company_name: string;
  entity_uei?: string;
  target_naics: string[];
  target_keywords: string[];
  target_set_asides: string[];
  logo_url?: string;
  awards?: EntityAward[];
  past_performances?: PastPerformance[];
}

export interface CompanyProfileDocument {
  id: number;
  company_uei: string;
  document_type: string;
  title: string;
  description?: string;
  file_path: string;
  file_size?: number;
  created_at: string;
  parsed_content?: string;
  status?: string;
}

export interface CompanyProfileLink {
  id: number;
  company_uei: string;
  link_type: string;
  title: string;
  url: string;
  description?: string;
  created_at: string;
}

export interface ContractDocument {
  award_id: string;
  solicitation_id: string;
  opportunity_title: string;
  document_url: string;
  document_filename: string;
  document_type: string;
  award_description?: string;
}

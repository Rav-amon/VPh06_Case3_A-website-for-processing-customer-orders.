export type TLeadTemperature = 'hot' | 'warm' | 'cold';

export interface ILeadIntelligence {
  score: number;
  temperature: TLeadTemperature;
  temperature_label: string;
  worth_time: boolean;
  needs_personal_manager: boolean;
  recommended_department: string;
  department_hint: string;
  priority_advice: string;
  reasons: string[];
  budget_value: number;
}

export interface IApplicationItem {
  id: number;
  first_name: string;
  last_name: string;
  middle_name: string;
  phone: string;
  email: string;
  business_info: string;
  niche: string;
  company_size: string;
  business_size: string;
  company_volume: string;
  demand_volume: string;
  tasks: string;
  client_role: string;
  deadline: string;
  task_type: string;
  product_interest: string;
  budget: string;
  contact_method: string;
  convenient_time: string;
  comment: string;
  created_at: string;
  updated_at: string;
  intelligence: ILeadIntelligence;
}

export interface IApplicationsSummary {
  total: number;
  hot: number;
  warm: number;
  cold: number;
  needs_personal_manager: number;
  worth_time: number;
  average_score: number;
}

export interface IApplicationsPage {
  items: IApplicationItem[];
  total: number;
  limit: number;
  offset: number;
  skip: number;
  summary: IApplicationsSummary;
}

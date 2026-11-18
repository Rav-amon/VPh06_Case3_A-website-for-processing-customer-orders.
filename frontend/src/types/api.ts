/** Общий конверт ответа backend. */
export interface IApiErrorBody {
  code: string;
  message: string;
  details: unknown;
}

export interface IApiResponse<T> {
  data: T;
  error: IApiErrorBody | null;
  message: string;
}

export interface IServiceItem {
  code: string;
  title: string;
  description: string;
  price_min: number;
  price_max: number;
  is_active: boolean;
}

export interface IAdminSettings {
  id: number;
  services: IServiceItem[];
  budget_min: number;
  budget_max: number;
  budget_step: number;
  updated_at: string;
}

export interface ILeadPayload {
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
}

export interface ILeadCreated {
  id: number;
}

export interface IButtonClickMetric {
  name: string;
  count: number;
}

export interface ICursorHotspotMetric {
  x: number;
  y: number;
  duration_ms: number;
  selector: string;
}

export interface IBehaviorPayload {
  lead_id: number;
  time_on_page_ms: number;
  button_clicks: IButtonClickMetric[];
  cursor_hotspots: ICursorHotspotMetric[];
  return_count: number;
  user_agent: string;
  language: string;
  timezone: string;
  screen: string;
  referrer: string;
}

export interface IAdminUser {
  id: number;
  login: string;
  created_at: string;
  updated_at: string;
}

export interface IAuthTokenResponse {
  access_token: string;
  token_type: string;
  admin: IAdminUser;
}

export interface IBootstrapStatus {
  registration_open: boolean;
}

export interface INamedCount {
  name: string;
  count: number;
}

export interface IDayCount {
  day: string;
  count: number;
}

export interface IRecentLead {
  id: number;
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  product_interest: string;
  budget: string;
  client_role: string;
  created_at: string;
}

export interface IAdminStats {
  total_leads: number;
  total_with_behavior: number;
  avg_time_on_page_ms: number;
  avg_return_count: number;
  by_role: INamedCount[];
  by_product: INamedCount[];
  by_day: IDayCount[];
  recent_leads: IRecentLead[];
  days_window: number;
}

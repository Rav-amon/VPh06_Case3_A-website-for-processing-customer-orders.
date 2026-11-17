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

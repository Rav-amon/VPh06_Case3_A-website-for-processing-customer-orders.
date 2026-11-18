/** Снимок живых метрик с POST /api/behavior-metrics/. */
export interface IBehaviorMetricsItem {
  id: number;
  application_id: number;
  time_on_page: number;
  buttons_clicked: string;
  cursor_positions: string;
  return_frequency: number;
  created_at: string;
}

export interface IBehaviorMetricsPage {
  items: IBehaviorMetricsItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ICursorPoint {
  x: number;
  y: number;
  t?: number;
}

export interface IPeriodTimeStats {
  label: string;
  sampleCount: number;
  averageSeconds: number;
  maxSeconds: number;
}

export interface IHeatmapCell {
  x: number;
  y: number;
  count: number;
}

import type {
  IBehaviorMetricsItem,
  ICursorPoint,
  IHeatmapCell,
  IPeriodTimeStats,
} from '@/types/behavior-metrics';

const DAY_MS = 24 * 60 * 60 * 1000;
const WEEK_MS = 7 * DAY_MS;
const MONTH_MS = 30 * DAY_MS;
const GRID_SIZE = 48;
const MAX_POINTS_PER_ITEM = 90;
const MAX_TOTAL_POINTS = 1200;

interface IVisitSession {
  endedAt: number;
  durationSeconds: number;
}

function parseCursorPositions(raw: string): ICursorPoint[] {
  if (!raw || raw.trim() === '') {
    return [];
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    const points: ICursorPoint[] = [];
    const start = Math.max(0, parsed.length - MAX_POINTS_PER_ITEM);
    for (let index = start; index < parsed.length; index += 1) {
      const item = parsed[index];
      if (!item || typeof item !== 'object') {
        continue;
      }
      const record = item as Record<string, unknown>;
      const x = Number(record.x);
      const y = Number(record.y);
      if (!Number.isFinite(x) || !Number.isFinite(y)) {
        continue;
      }
      const t = Number(record.t);
      points.push({
        x: Math.round(x),
        y: Math.round(y),
        t: Number.isFinite(t) ? t : undefined,
      });
    }
    return points;
  } catch {
    return [];
  }
}

/**
 * Восстанавливает визиты: новый визит, когда time_on_page резко падает.
 */
export function extractVisitSessions(
  items: IBehaviorMetricsItem[],
): IVisitSession[] {
  const ordered = [...items].sort(
    (left, right) =>
      new Date(left.created_at).getTime() - new Date(right.created_at).getTime(),
  );
  const sessions: IVisitSession[] = [];
  let peak = 0;
  let endedAt = 0;

  const flush = () => {
    if (peak <= 0 || endedAt <= 0) {
      return;
    }
    sessions.push({ endedAt, durationSeconds: peak });
    peak = 0;
    endedAt = 0;
  };

  for (const item of ordered) {
    const createdAt = new Date(item.created_at).getTime();
    if (!Number.isFinite(createdAt)) {
      continue;
    }
    if (item.time_on_page < peak - 2) {
      flush();
    }
    if (item.time_on_page >= peak) {
      peak = item.time_on_page;
      endedAt = createdAt;
    }
  }
  flush();
  return sessions;
}

function periodStats(
  label: string,
  sessions: IVisitSession[],
  windowMs: number,
  nowMs: number,
): IPeriodTimeStats {
  const filtered = sessions.filter(
    (session) => session.endedAt >= nowMs - windowMs,
  );
  if (filtered.length === 0) {
    return {
      label,
      sampleCount: 0,
      averageSeconds: 0,
      maxSeconds: 0,
    };
  }
  const total = filtered.reduce(
    (sum, session) => sum + session.durationSeconds,
    0,
  );
  const maxSeconds = filtered.reduce(
    (current, session) => Math.max(current, session.durationSeconds),
    0,
  );
  return {
    label,
    sampleCount: filtered.length,
    averageSeconds: Math.round(total / filtered.length),
    maxSeconds,
  };
}

/** Среднее и максимум времени визита за день, неделю и месяц. */
export function buildPeriodTimeStats(
  items: IBehaviorMetricsItem[],
  nowMs: number = Date.now(),
): IPeriodTimeStats[] {
  const sessions = extractVisitSessions(items);
  return [
    periodStats('День', sessions, DAY_MS, nowMs),
    periodStats('Неделя', sessions, WEEK_MS, nowMs),
    periodStats('Месяц', sessions, MONTH_MS, nowMs),
  ];
}

/** Собирает точки курсора: свежие снимки, с лимитом на объём. */
export function collectCursorPoints(
  items: IBehaviorMetricsItem[],
): ICursorPoint[] {
  const newestFirst = [...items].sort(
    (left, right) =>
      new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
  );
  const points: ICursorPoint[] = [];
  for (const item of newestFirst) {
    const parsed = parseCursorPositions(item.cursor_positions).filter(
      (point) => point.x > 0 || point.y > 0,
    );
    points.push(...parsed);
    if (points.length >= MAX_TOTAL_POINTS) {
      break;
    }
  }
  return points.slice(0, MAX_TOTAL_POINTS);
}

/**
 * Агрегирует точки в сетку для хитмапа: чем больше count, тем плотнее зона.
 */
export function buildHeatmapCells(points: ICursorPoint[]): IHeatmapCell[] {
  const buckets = new Map<string, IHeatmapCell>();
  for (const point of points) {
    const cellX = Math.floor(point.x / GRID_SIZE) * GRID_SIZE + GRID_SIZE / 2;
    const cellY = Math.floor(point.y / GRID_SIZE) * GRID_SIZE + GRID_SIZE / 2;
    const key = `${cellX}:${cellY}`;
    const existing = buckets.get(key);
    if (existing) {
      buckets.set(key, { ...existing, count: existing.count + 1 });
    } else {
      buckets.set(key, { x: cellX, y: cellY, count: 1 });
    }
  }
  return [...buckets.values()].sort((left, right) => left.count - right.count);
}

export interface IHeatmapBounds {
  width: number;
  height: number;
}

/** Границы области хитмапа по фактическим точкам. */
export function computeHeatmapBounds(cells: IHeatmapCell[]): IHeatmapBounds {
  if (cells.length === 0) {
    return { width: 960, height: 540 };
  }
  const maxX = cells.reduce((current, cell) => Math.max(current, cell.x), 0);
  const maxY = cells.reduce((current, cell) => Math.max(current, cell.y), 0);
  return {
    width: Math.max(480, Math.min(1400, maxX + GRID_SIZE * 2)),
    height: Math.max(320, Math.min(900, maxY + GRID_SIZE * 2)),
  };
}

export function formatSeconds(totalSeconds: number): string {
  if (totalSeconds < 60) {
    return `${totalSeconds} с`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes < 60) {
    return `${minutes} м ${seconds} с`;
  }
  const hours = Math.floor(minutes / 60);
  const restMinutes = minutes % 60;
  return `${hours} ч ${restMinutes} м`;
}

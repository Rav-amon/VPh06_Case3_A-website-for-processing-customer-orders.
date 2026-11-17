import { useEffect, useRef } from 'react';
import type {
  IBehaviorPayload,
  IButtonClickMetric,
  ICursorHotspotMetric,
} from '@/types/api';

const RETURN_KEY = 'autello_return_count';
const MAX_HOTSPOTS = 40;
const HOVER_THRESHOLD_MS = 450;

interface ITrackerApi {
  trackClick: (name: string) => void;
  buildPayload: (leadId: number) => IBehaviorPayload;
}

/**
 * Собирает время на странице, клики и точки зависания курсора.
 */
export function useBehaviorTracker(): ITrackerApi {
  const startedAt = useRef(Date.now());
  const clicks = useRef<Map<string, number>>(new Map());
  const hotspots = useRef<ICursorHotspotMetric[]>([]);
  const hoverStarted = useRef<{ x: number; y: number; at: number } | null>(null);

  useEffect(() => {
    const raw = window.sessionStorage.getItem(RETURN_KEY);
    const next = Number.parseInt(raw ?? '0', 10);
    const safe = Number.isFinite(next) ? next + 1 : 1;
    window.sessionStorage.setItem(RETURN_KEY, String(safe));

    const onMove = (event: MouseEvent) => {
      const now = Date.now();
      const previous = hoverStarted.current;
      if (previous && now - previous.at >= HOVER_THRESHOLD_MS) {
        if (hotspots.current.length < MAX_HOTSPOTS) {
          const target = event.target;
          const selector =
            target instanceof HTMLElement
              ? target.dataset.track || target.tagName.toLowerCase()
              : '';
          hotspots.current = [
            ...hotspots.current,
            {
              x: Math.round(previous.x),
              y: Math.round(previous.y),
              duration_ms: now - previous.at,
              selector,
            },
          ];
        }
      }
      hoverStarted.current = { x: event.clientX, y: event.clientY, at: now };
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    return () => {
      window.removeEventListener('mousemove', onMove);
    };
  }, []);

  const trackClick = (name: string) => {
    const current = clicks.current.get(name) ?? 0;
    clicks.current.set(name, current + 1);
  };

  const buildPayload = (leadId: number): IBehaviorPayload => {
    const buttonClicks: IButtonClickMetric[] = [...clicks.current.entries()].map(
      ([name, count]) => ({ name, count }),
    );
    const returns = Number.parseInt(
      window.sessionStorage.getItem(RETURN_KEY) ?? '1',
      10,
    );
    return {
      lead_id: leadId,
      time_on_page_ms: Math.max(0, Date.now() - startedAt.current),
      button_clicks: buttonClicks,
      cursor_hotspots: hotspots.current,
      return_count: Number.isFinite(returns) ? returns : 1,
      user_agent: window.navigator.userAgent.slice(0, 512),
      language: window.navigator.language.slice(0, 32),
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone.slice(0, 64),
      screen: `${window.screen.width}x${window.screen.height}`,
      referrer: document.referrer.slice(0, 1000),
    };
  };

  return { trackClick, buildPayload };
}

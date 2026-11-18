import { useEffect, useRef } from 'react';
import { postBehaviorMetrics } from '@/api/behavior-metrics';

const TICK_MS = 1000;
const MAX_CURSOR_POINTS = 180;
const APPLICATION_ID = 0;
const RETURN_FREQUENCY = 0;

interface ICursorPoint {
  x: number;
  y: number;
  t: number;
}

/**
 * На главной: каждую секунду пишет позицию курсора и шлёт метрики на сервер.
 */
export function useLiveMetrics(): void {
  const startedAt = useRef(Date.now());
  const cursor = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const positions = useRef<ICursorPoint[]>([]);
  const clicks = useRef<Map<string, number>>(new Map());
  const inFlight = useRef(false);

  useEffect(() => {
    const onMove = (event: MouseEvent) => {
      // pageX/pageY учитывают прокрутку длинной формы заявки.
      cursor.current = {
        x: Math.round(event.pageX),
        y: Math.round(event.pageY),
      };
    };

    const onClick = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      const clickable = target.closest(
        'button, a, [role="button"], input[type="submit"], [data-track]',
      );
      if (!(clickable instanceof HTMLElement)) {
        return;
      }
      const name =
        clickable.dataset.track ||
        clickable.getAttribute('aria-label') ||
        clickable.id ||
        clickable.tagName.toLowerCase();
      const key = name.trim().slice(0, 100) || 'unknown';
      clicks.current.set(key, (clicks.current.get(key) ?? 0) + 1);
    };

    const sendSnapshot = async () => {
      if (inFlight.current) {
        return;
      }
      const timeOnPage = Math.max(
        0,
        Math.floor((Date.now() - startedAt.current) / TICK_MS),
      );
      const point: ICursorPoint = {
        x: cursor.current.x,
        y: cursor.current.y,
        t: timeOnPage,
      };
      const nextPositions = [...positions.current, point];
      positions.current =
        nextPositions.length > MAX_CURSOR_POINTS
          ? nextPositions.slice(nextPositions.length - MAX_CURSOR_POINTS)
          : nextPositions;

      const buttonsObject: Record<string, number> = {};
      for (const [name, count] of clicks.current.entries()) {
        buttonsObject[name] = count;
      }

      inFlight.current = true;
      try {
        await postBehaviorMetrics({
          application_id: APPLICATION_ID,
          time_on_page: timeOnPage,
          buttons_clicked: JSON.stringify(buttonsObject),
          cursor_positions: JSON.stringify(positions.current),
          return_frequency: RETURN_FREQUENCY,
        });
      } catch (error) {
        console.error('Не удалось отправить живые метрики', error);
      } finally {
        inFlight.current = false;
      }
    };

    window.addEventListener('mousemove', onMove, { passive: true });
    window.addEventListener('click', onClick, true);
    const timer = window.setInterval(() => {
      void sendSnapshot();
    }, TICK_MS);

    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('click', onClick, true);
      window.clearInterval(timer);
    };
  }, []);
}

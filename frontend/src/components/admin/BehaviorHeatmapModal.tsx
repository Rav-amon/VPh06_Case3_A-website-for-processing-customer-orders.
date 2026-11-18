import { useCallback, useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { fetchBehaviorMetrics } from '@/api/behavior-metrics';
import { ApiClientError } from '@/api/client';
import type {
  IBehaviorMetricsItem,
  IHeatmapCell,
  IPeriodTimeStats,
} from '@/types/behavior-metrics';
import {
  buildHeatmapCells,
  buildPeriodTimeStats,
  collectCursorPoints,
  computeHeatmapBounds,
  formatSeconds,
} from '@/utils/behavior-metrics-stats';

const METRICS_LIMIT = 30;
const REFRESH_MS = 5000;

interface IBehaviorHeatmapModalProps {
  open: boolean;
  onClose: () => void;
}

/** Компактная модалка через portal: не ломается от transform родителя. */
export function BehaviorHeatmapModal({
  open,
  onClose,
}: IBehaviorHeatmapModalProps) {
  const [items, setItems] = useState<IBehaviorMetricsItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  const load = useCallback(async (silent: boolean) => {
    if (!silent) {
      setLoading(true);
    }
    setError(null);
    try {
      const page = await fetchBehaviorMetrics(0, METRICS_LIMIT);
      setItems(page.items ?? []);
      setUpdatedAt(new Date().toLocaleTimeString('ru-RU'));
    } catch (loadError) {
      setError(
        loadError instanceof ApiClientError
          ? loadError.message
          : 'Не удалось загрузить метрики поведения',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) {
      return;
    }
    void load(false);
    const timer = window.setInterval(() => {
      void load(true);
    }, REFRESH_MS);
    return () => {
      window.clearInterval(timer);
    };
  }, [open, load]);

  useEffect(() => {
    if (!open) {
      return;
    }
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [open, onClose]);

  const periods: IPeriodTimeStats[] = useMemo(
    () => buildPeriodTimeStats(items),
    [items],
  );
  const cells: IHeatmapCell[] = useMemo(() => {
    const points = collectCursorPoints(items);
    return buildHeatmapCells(points);
  }, [items]);
  const bounds = useMemo(() => computeHeatmapBounds(cells), [cells]);
  const maxCount = cells.reduce(
    (current, cell) => Math.max(current, cell.count),
    0,
  );
  const pointsTotal = cells.reduce((sum, cell) => sum + cell.count, 0);

  if (!open) {
    return null;
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 p-3
        sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-label="Статистика поведения на странице заказа"
      onClick={onClose}
    >
      <div
        className="flex max-h-[88vh] w-full max-w-4xl flex-col overflow-hidden
          rounded-sm border border-gold-400/40 bg-[#16120e]"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex shrink-0 items-center justify-between gap-3
          border-b border-gold-400/25 px-4 py-3">
          <div className="min-w-0">
            <h2 className="font-display text-xl text-gold-100 sm:text-2xl">
              Поведение на странице
            </h2>
            <p className="mt-0.5 text-xs text-gold-200/70">
              автообновление · {updatedAt ?? '—'}
              {loading ? ' · загрузка…' : ''}
            </p>
          </div>
          <div className="flex shrink-0 gap-2">
            <button
              type="button"
              onClick={() => {
                void load(false);
              }}
              className="border border-gold-400/40 bg-gold-400/10 px-3 py-1.5 text-xs
                uppercase tracking-[0.12em] text-gold-100 hover:bg-gold-400/20"
            >
              Обновить
            </button>
            <button
              type="button"
              onClick={onClose}
              className="border border-gold-300/50 bg-gold-400/15 px-3 py-1.5 text-xs
                uppercase tracking-[0.12em] text-gold-100 hover:bg-gold-400/25"
              aria-label="Закрыть модальное окно"
            >
              Закрыть
            </button>
          </div>
        </header>

        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-3">
          {error ? (
            <p className="field-error" role="alert">
              {error}
            </p>
          ) : null}

          <section className="grid grid-cols-3 gap-2">
            {periods.map((period) => (
              <article
                key={period.label}
                className="border border-gold-400/30 bg-[#1c1712] px-3 py-2"
              >
                <p className="text-[0.65rem] uppercase tracking-[0.14em] text-gold-200">
                  {period.label}
                </p>
                <p className="mt-1 font-display text-2xl leading-none text-gold-100">
                  {formatSeconds(period.averageSeconds)}
                </p>
                <p className="mt-1 text-[0.72rem] text-mist">
                  макс. {formatSeconds(period.maxSeconds)} · визитов{' '}
                  {period.sampleCount}
                </p>
              </article>
            ))}
          </section>

          <section>
            <div className="mb-1.5 flex items-baseline justify-between gap-2">
              <h3 className="text-[0.7rem] uppercase tracking-[0.14em] text-gold-200">
                Хитмап курсора
              </h3>
              <p className="text-[0.72rem] text-mist">
                зон {cells.length} · точек {pointsTotal}
              </p>
            </div>

            {cells.length === 0 ? (
              <p className="border border-gold-400/25 bg-[#1c1712] px-3 py-5
                text-center text-sm text-mist">
                Нет координат курсора. Откройте главную и подвигайте мышью.
              </p>
            ) : (
              <div className="border border-gold-400/30 bg-[#0d0b09] p-2">
                <svg
                  viewBox={`0 0 ${bounds.width} ${bounds.height}`}
                  className="mx-auto block h-[38vh] w-full max-h-[320px]"
                  role="img"
                  aria-label="Хитмап позиций курсора"
                >
                  <rect
                    x={0}
                    y={0}
                    width={bounds.width}
                    height={bounds.height}
                    fill="#12100d"
                  />
                  <g opacity={0.28} stroke="#d4b56a" strokeWidth={1}>
                    {Array.from({ length: 7 }, (_, index) => (
                      <line
                        key={`v-${index}`}
                        x1={(index * bounds.width) / 6}
                        y1={0}
                        x2={(index * bounds.width) / 6}
                        y2={bounds.height}
                      />
                    ))}
                    {Array.from({ length: 5 }, (_, index) => (
                      <line
                        key={`h-${index}`}
                        x1={0}
                        y1={(index * bounds.height) / 4}
                        x2={bounds.width}
                        y2={(index * bounds.height) / 4}
                      />
                    ))}
                  </g>
                  {cells.map((cell) => {
                    const intensity = maxCount > 0 ? cell.count / maxCount : 0;
                    const radius = 6 + intensity * 20;
                    const opacity = 0.35 + intensity * 0.6;
                    return (
                      <circle
                        key={`${cell.x}-${cell.y}`}
                        cx={Math.min(Math.max(cell.x, 0), bounds.width)}
                        cy={Math.min(Math.max(cell.y, 0), bounds.height)}
                        r={radius}
                        fill={`rgba(232, 213, 163, ${opacity.toFixed(3)})`}
                        stroke="rgba(244, 234, 208, 0.55)"
                        strokeWidth={1}
                      >
                        <title>
                          x={cell.x}, y={cell.y}, точек={cell.count}
                        </title>
                      </circle>
                    );
                  })}
                </svg>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>,
    document.body,
  );
}

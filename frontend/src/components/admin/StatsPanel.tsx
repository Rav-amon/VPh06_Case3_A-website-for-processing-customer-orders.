import { useEffect, useState } from 'react';
import { fetchAdminStats } from '@/api/admin';
import { ApiClientError } from '@/api/client';
import { BehaviorHeatmapModal } from '@/components/admin/BehaviorHeatmapModal';
import type { IAdminStats } from '@/types/api';

const MS_IN_SECOND = 1000;

function formatDuration(ms: number): string {
  const totalSeconds = Math.round(ms / MS_IN_SECOND);
  if (totalSeconds < 60) {
    return `${totalSeconds} с`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes} м ${seconds} с`;
}

/** Компактная сводка по заявкам и поведению. */
export function StatsPanel() {
  const [stats, setStats] = useState<IAdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [heatmapOpen, setHeatmapOpen] = useState(false);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await fetchAdminStats();
        if (!active) {
          return;
        }
        setStats(data);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setError(
          loadError instanceof ApiClientError
            ? loadError.message
            : 'Не удалось загрузить статистику',
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <p className="text-sm text-mist">Загрузка статистики…</p>;
  }

  if (error) {
    return (
      <p className="field-error" role="alert">
        {error}
      </p>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <section className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-2xl text-gold-100">Статистика</h2>
          <p className="mt-1 text-sm text-mist">
            Сводка за всё время · динамика {stats.days_window} дн.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setHeatmapOpen(true)}
          className="border border-gold-400/50 bg-gold-400/15 px-4 py-2.5 text-sm
            uppercase tracking-[0.14em] text-gold-100 transition hover:bg-gold-400/25"
        >
          Хитмап и время
        </button>
      </div>

      <BehaviorHeatmapModal
        open={heatmapOpen}
        onClose={() => setHeatmapOpen(false)}
      />

      <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
        <StatTile label="Заявок" value={String(stats.total_leads)} />
        <StatTile
          label="С метриками"
          value={String(stats.total_with_behavior)}
        />
        <StatTile
          label="Среднее время"
          value={formatDuration(stats.avg_time_on_page_ms)}
        />
        <StatTile
          label="Возвраты"
          value={stats.avg_return_count.toFixed(1)}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <NamedList title="По роли" items={stats.by_role} />
        <NamedList title="По продукту" items={stats.by_product} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="text-[0.7rem] uppercase tracking-[0.16em] text-gold-200">
            По дням
          </h3>
          {stats.by_day.length === 0 ? (
            <p className="mt-2 text-sm text-mist">Пока нет данных.</p>
          ) : (
            <ul className="mt-2 max-h-48 space-y-1 overflow-y-auto pr-1">
              {stats.by_day.map((item) => (
                <li
                  key={item.day}
                  className="flex justify-between border-b border-gold-400/15 py-1.5
                    text-sm text-mist"
                >
                  <span>{item.day}</span>
                  <span className="text-gold-100">{item.count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="text-[0.7rem] uppercase tracking-[0.16em] text-gold-200">
            Последние заявки
          </h3>
          {stats.recent_leads.length === 0 ? (
            <p className="mt-2 text-sm text-mist">Заявок ещё нет.</p>
          ) : (
            <div className="mt-2 max-h-48 overflow-auto">
              <table className="min-w-full text-left text-sm text-mist">
                <thead className="text-gold-200">
                  <tr>
                    <th className="py-1.5 pr-3 font-normal">ID</th>
                    <th className="py-1.5 pr-3 font-normal">Клиент</th>
                    <th className="py-1.5 pr-3 font-normal">Продукт</th>
                    <th className="py-1.5 font-normal">Бюджет</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_leads.map((lead) => (
                    <tr key={lead.id} className="border-t border-gold-400/15">
                      <td className="py-1.5 pr-3 text-gold-100">{lead.id}</td>
                      <td className="py-1.5 pr-3">
                        {lead.last_name} {lead.first_name}
                      </td>
                      <td className="py-1.5 pr-3">{lead.product_interest}</td>
                      <td className="py-1.5">{lead.budget}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

interface IStatTileProps {
  label: string;
  value: string;
}

function StatTile({ label, value }: IStatTileProps) {
  return (
    <div className="border border-gold-400/30 bg-[#1c1712] px-3 py-3">
      <p className="text-[0.65rem] uppercase tracking-[0.16em] text-gold-200">
        {label}
      </p>
      <p className="mt-1.5 font-display text-2xl text-gold-100">{value}</p>
    </div>
  );
}

interface INamedListProps {
  title: string;
  items: Array<{ name: string; count: number }>;
}

function NamedList({ title, items }: INamedListProps) {
  return (
    <div className="border border-gold-400/25 bg-[#1c1712]/60 px-3 py-3">
      <h3 className="text-[0.7rem] uppercase tracking-[0.16em] text-gold-200">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-mist">Пока нет данных.</p>
      ) : (
        <ul className="mt-2 space-y-1">
          {items.map((item) => (
            <li
              key={item.name}
              className="flex justify-between border-b border-gold-400/15 py-1.5
                text-sm text-mist"
            >
              <span>{item.name}</span>
              <span className="text-gold-100">{item.count}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

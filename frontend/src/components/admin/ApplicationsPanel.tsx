import { useEffect, useState } from 'react';
import { fetchApplications } from '@/api/applications';
import { ApiClientError } from '@/api/client';
import { ApplicationDetailModal } from '@/components/admin/ApplicationDetailModal';
import type {
  IApplicationItem,
  IApplicationsSummary,
  TLeadTemperature,
} from '@/types/applications';

const LIST_LIMIT = 100;

const TEMPERATURE_CLASS: Record<TLeadTemperature, string> = {
  hot: 'text-red-300',
  warm: 'text-amber-200',
  cold: 'text-sky-300/80',
};

/** Очередь заявок: горячие сверху, детали и контакты. */
export function ApplicationsPanel() {
  const [items, setItems] = useState<IApplicationItem[]>([]);
  const [summary, setSummary] = useState<IApplicationsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<IApplicationItem | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const page = await fetchApplications(0, LIST_LIMIT);
        if (!active) {
          return;
        }
        setItems(page.items ?? []);
        setSummary(page.summary);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setError(
          loadError instanceof ApiClientError
            ? loadError.message
            : 'Не удалось загрузить заявки',
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
    return <p className="text-sm text-mist/60">Загрузка очереди заявок…</p>;
  }

  if (error) {
    return (
      <p className="field-error" role="alert">
        {error}
      </p>
    );
  }

  return (
    <section className="space-y-8">
      <div>
        <h2 className="font-display text-2xl text-gold-100">Заявки</h2>
        <p className="mt-2 text-sm text-mist/60">
          Интеллектуальная очередь: срочные («горячие») лиды сверху, холодные ниже.
        </p>
      </div>

      {summary ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryTile label="Всего" value={String(summary.total)} />
          <SummaryTile label="Горячие" value={String(summary.hot)} accent="hot" />
          <SummaryTile label="Тёплые" value={String(summary.warm)} accent="warm" />
          <SummaryTile label="Холодные" value={String(summary.cold)} accent="cold" />
          <SummaryTile
            label="Нужен менеджер"
            value={String(summary.needs_personal_manager)}
          />
          <SummaryTile label="Стоит времени" value={String(summary.worth_time)} />
          <SummaryTile
            label="Средний score"
            value={String(summary.average_score)}
          />
        </div>
      ) : null}

      <div className="overflow-x-auto border border-gold-400/15">
        <table className="min-w-full text-left text-sm text-mist/80">
          <thead className="bg-ink-900/50 text-[0.68rem] uppercase tracking-[0.14em]
            text-gold-200/65">
            <tr>
              <th className="px-3 py-3 font-normal">Темп.</th>
              <th className="px-3 py-3 font-normal">Score</th>
              <th className="px-3 py-3 font-normal">Клиент</th>
              <th className="px-3 py-3 font-normal">Ниша</th>
              <th className="px-3 py-3 font-normal">Бюджет</th>
              <th className="px-3 py-3 font-normal">Срок</th>
              <th className="px-3 py-3 font-normal">Отдел</th>
              <th className="px-3 py-3 font-normal">Менеджер</th>
              <th className="px-3 py-3 font-normal" />
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-3 py-8 text-center text-mist/50">
                  Заявок пока нет.
                </td>
              </tr>
            ) : (
              items.map((item) => {
                const intel = item.intelligence;
                return (
                  <tr
                    key={item.id}
                    className="border-t border-gold-400/10 hover:bg-ink-800/40"
                  >
                    <td
                      className={`px-3 py-3 font-medium ${TEMPERATURE_CLASS[intel.temperature]}`}
                    >
                      {intel.temperature_label}
                    </td>
                    <td className="px-3 py-3 text-gold-100">{intel.score}</td>
                    <td className="px-3 py-3">
                      {item.last_name} {item.first_name}
                      <div className="text-xs text-mist/45">{item.client_role}</div>
                    </td>
                    <td className="px-3 py-3">{item.niche}</td>
                    <td className="px-3 py-3">{item.budget}</td>
                    <td className="px-3 py-3">{item.deadline}</td>
                    <td className="px-3 py-3">{intel.recommended_department}</td>
                    <td className="px-3 py-3">
                      {intel.needs_personal_manager ? 'Да' : 'Нет'}
                    </td>
                    <td className="px-3 py-3">
                      <button
                        type="button"
                        className="text-gold-300 hover:underline"
                        onClick={() => setSelected(item)}
                      >
                        Открыть
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <ApplicationDetailModal
        application={selected}
        onClose={() => setSelected(null)}
      />
    </section>
  );
}

interface ISummaryTileProps {
  label: string;
  value: string;
  accent?: TLeadTemperature;
}

function SummaryTile({ label, value, accent }: ISummaryTileProps) {
  const valueClass = accent ? TEMPERATURE_CLASS[accent] : 'text-gold-100';
  return (
    <div className="border border-gold-400/15 bg-ink-900/30 px-4 py-5">
      <p className="text-[0.68rem] uppercase tracking-[0.2em] text-gold-200/60">
        {label}
      </p>
      <p className={`mt-3 font-display text-3xl ${valueClass}`}>{value}</p>
    </div>
  );
}

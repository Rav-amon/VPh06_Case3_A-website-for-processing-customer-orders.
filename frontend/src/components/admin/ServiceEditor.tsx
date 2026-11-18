import { useEffect, useState } from 'react';
import {
  fetchAdminSettings,
  updateAdminSettings,
} from '@/api/admin';
import { ApiClientError } from '@/api/client';
import { Field } from '@/components/Field';
import type { IServiceItem } from '@/types/api';

const DEFAULT_PRICE_MIN = 0;
const DEFAULT_PRICE_MAX = 100_000;
const NUMERIC_ID_PATTERN = /^\d+$/;

interface IServiceForm {
  id: string;
  title: string;
}

/** Следующий свободный числовой id: 1, 2, 3… */
function nextServiceId(services: IServiceItem[]): string {
  let maxId = 0;
  for (const item of services) {
    if (!NUMERIC_ID_PATTERN.test(item.code)) {
      continue;
    }
    const value = Number.parseInt(item.code, 10);
    if (Number.isFinite(value) && value > maxId) {
      maxId = value;
    }
  }
  return String(maxId + 1);
}

function toForm(item: IServiceItem): IServiceForm {
  return { id: item.code, title: item.title };
}

function emptyFormFor(services: IServiceItem[]): IServiceForm {
  return { id: nextServiceId(services), title: '' };
}

function buildServicePayload(
  form: IServiceForm,
  previous: IServiceItem | null,
): IServiceItem {
  return {
    code: form.id.trim(),
    title: form.title.trim(),
    description: previous?.description ?? '',
    price_min: previous?.price_min ?? DEFAULT_PRICE_MIN,
    price_max:
      previous && previous.price_max > previous.price_min
        ? previous.price_max
        : DEFAULT_PRICE_MAX,
    is_active: previous?.is_active ?? true,
  };
}

function validateForm(form: IServiceForm): string | null {
  const id = form.id.trim();
  const title = form.title.trim();
  if (id === '' || !NUMERIC_ID_PATTERN.test(id)) {
    return 'Id должен быть положительным числом';
  }
  if (Number.parseInt(id, 10) < 1) {
    return 'Id должен быть не меньше 1';
  }
  if (title === '') {
    return 'Укажите название услуги';
  }
  return null;
}

/** CRUD услуг: авто-id по порядку и название. */
export function ServiceEditor() {
  const [services, setServices] = useState<IServiceItem[]>([]);
  const [budgetMin, setBudgetMin] = useState(0);
  const [budgetMax, setBudgetMax] = useState(1_000_000);
  const [budgetStep, setBudgetStep] = useState(10_000);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [form, setForm] = useState<IServiceForm>({ id: '1', title: '' });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const persist = async (nextServices: IServiceItem[], okMessage: string) => {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const saved = await updateAdminSettings({
        services: nextServices,
        budget_min: budgetMin,
        budget_max: budgetMax,
        budget_step: budgetStep,
      });
      const list = saved.services ?? [];
      setServices(list);
      setBudgetMin(saved.budget_min);
      setBudgetMax(saved.budget_max);
      setBudgetStep(saved.budget_step);
      setMessage(okMessage);
      return list;
    } catch (saveError) {
      setError(
        saveError instanceof ApiClientError
          ? saveError.message
          : 'Не удалось сохранить услуги',
      );
      return null;
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const settings = await fetchAdminSettings();
        if (!active) {
          return;
        }
        const list = settings.services ?? [];
        setServices(list);
        setBudgetMin(settings.budget_min);
        setBudgetMax(settings.budget_max);
        setBudgetStep(settings.budget_step);
        setForm(emptyFormFor(list));
      } catch (loadError) {
        if (!active) {
          return;
        }
        setError(
          loadError instanceof ApiClientError
            ? loadError.message
            : 'Не удалось загрузить услуги',
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

  const handleSelect = (item: IServiceItem) => {
    setSelectedCode(item.code);
    setForm(toForm(item));
    setError(null);
    setMessage(null);
  };

  const handleAdd = async () => {
    const prepared: IServiceForm = {
      id: nextServiceId(services),
      title: form.title,
    };
    setForm(prepared);
    const validationError = validateForm(prepared);
    if (validationError) {
      setError(validationError);
      return;
    }
    const code = prepared.id;
    if (services.some((item) => item.code === code)) {
      setError('Услуга с таким id уже есть');
      return;
    }
    const next = [...services, buildServicePayload(prepared, null)];
    const saved = await persist(next, 'Услуга добавлена');
    if (saved) {
      setSelectedCode(null);
      setForm(emptyFormFor(saved));
    }
  };

  const handleEdit = async () => {
    if (!selectedCode) {
      setError('Выберите услугу в таблице');
      return;
    }
    // При редактировании id не меняем — только название.
    const prepared: IServiceForm = {
      id: selectedCode,
      title: form.title,
    };
    setForm(prepared);
    const validationError = validateForm(prepared);
    if (validationError) {
      setError(validationError);
      return;
    }
    const previous = services.find((item) => item.code === selectedCode) ?? null;
    const next = services.map((item) =>
      item.code === selectedCode ? buildServicePayload(prepared, previous) : item,
    );
    const saved = await persist(next, 'Услуга изменена');
    if (saved) {
      setSelectedCode(selectedCode);
      setForm({ id: selectedCode, title: prepared.title.trim() });
    }
  };

  const handleDelete = async () => {
    if (!selectedCode) {
      setError('Выберите услугу в таблице');
      return;
    }
    const next = services.filter((item) => item.code !== selectedCode);
    const saved = await persist(next, 'Услуга удалена');
    if (saved) {
      setSelectedCode(null);
      setForm(emptyFormFor(saved));
    }
  };

  if (loading) {
    return <p className="text-sm text-mist">Загрузка услуг…</p>;
  }

  return (
    <section className="space-y-5">
      <div>
        <h2 className="font-display text-2xl text-gold-100">Услуги</h2>
        <p className="mt-1 text-sm text-mist">
          Введите только название. Id назначается автоматически: 1, 2, 3…
        </p>
      </div>

      <div className="overflow-x-auto border border-gold-400/30">
        <table className="min-w-full text-left text-sm text-mist">
          <thead className="bg-[#1c1712] text-[0.68rem] uppercase tracking-[0.14em]
            text-gold-200">
            <tr>
              <th className="px-3 py-3 font-normal">Id</th>
              <th className="px-3 py-3 font-normal">Название услуги</th>
            </tr>
          </thead>
          <tbody>
            {services.length === 0 ? (
              <tr>
                <td colSpan={2} className="px-3 py-6 text-center text-mist">
                  Услуг пока нет. Введите название и нажмите «Добавить».
                </td>
              </tr>
            ) : (
              services.map((item) => {
                const selected = item.code === selectedCode;
                return (
                  <tr
                    key={item.code}
                    onClick={() => handleSelect(item)}
                    className={
                      selected
                        ? 'cursor-pointer border-t border-gold-400/15 bg-gold-400/15'
                        : 'cursor-pointer border-t border-gold-400/15 hover:bg-[#1c1712]'
                    }
                  >
                    <td className="px-3 py-3 text-gold-100">{item.code}</td>
                    <td className="px-3 py-3">{item.title}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <Field
        id="service-title"
        label="Название услуги"
        value={form.title}
        required
        placeholder="Сайт под ключ"
        onChange={(value) => setForm({ ...form, title: value })}
        onBlur={() => undefined}
      />

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            void handleAdd();
          }}
          className="border border-gold-400/50 bg-gold-400/15 px-4 py-2.5 text-sm
            uppercase tracking-[0.14em] text-gold-100 hover:bg-gold-400/25
            disabled:opacity-40"
        >
          Добавить
        </button>
        <button
          type="button"
          disabled={busy || !selectedCode}
          onClick={() => {
            void handleEdit();
          }}
          className="border border-gold-400/40 px-4 py-2.5 text-sm uppercase
            tracking-[0.14em] text-gold-100 hover:bg-gold-400/10 disabled:opacity-40"
        >
          Редактировать
        </button>
        <button
          type="button"
          disabled={busy || !selectedCode}
          onClick={() => {
            void handleDelete();
          }}
          className="border border-red-400/40 px-4 py-2.5 text-sm uppercase
            tracking-[0.14em] text-red-300 hover:bg-red-400/10 disabled:opacity-40"
        >
          Удалить
        </button>
      </div>

      {error ? (
        <p className="field-error" role="alert">
          {error}
        </p>
      ) : null}
      {message ? <p className="text-sm text-gold-200">{message}</p> : null}
    </section>
  );
}

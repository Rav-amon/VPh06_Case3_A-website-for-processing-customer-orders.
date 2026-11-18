import { createPortal } from 'react-dom';
import type { IApplicationItem } from '@/types/applications';

interface IApplicationDetailModalProps {
  application: IApplicationItem | null;
  onClose: () => void;
}

/** Карточка заявки: интеллект, контакты и поля анкеты. */
export function ApplicationDetailModal({
  application,
  onClose,
}: IApplicationDetailModalProps) {
  if (!application) {
    return null;
  }

  const intel = application.intelligence;
  const phoneHref = application.phone
    ? `tel:${application.phone.replace(/\s+/g, '')}`
    : null;
  const emailHref = application.email ? `mailto:${application.email}` : null;
  const fullName = [
    application.last_name,
    application.first_name,
    application.middle_name,
  ]
    .filter(Boolean)
    .join(' ');

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center overflow-y-auto
        bg-black/80 px-4 py-8"
      role="dialog"
      aria-modal="true"
      aria-label={`Заявка ${application.id}`}
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl border border-gold-400/35 bg-[#16120e] p-6 sm:p-8"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-[0.68rem] uppercase tracking-[0.2em] text-gold-200/60">
              Заявка #{application.id}
            </p>
            <h2 className="mt-2 font-display text-3xl text-gold-100">{fullName}</h2>
            <p className="mt-2 text-sm text-mist/60">
              {new Date(application.created_at).toLocaleString('ru-RU')}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="border border-gold-400/30 px-4 py-2 text-sm uppercase
              tracking-[0.16em] text-gold-200 hover:bg-gold-400/10"
          >
            Закрыть
          </button>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <InfoBlock title="Температура" value={`${intel.temperature_label} · ${intel.score}`} />
          <InfoBlock title="Отдел" value={intel.recommended_department} />
          <InfoBlock
            title="Персональный менеджер"
            value={intel.needs_personal_manager ? 'Да, нужен' : 'Не обязателен'}
          />
          <InfoBlock
            title="Тратить время"
            value={intel.worth_time ? 'Да, стоит' : 'Низкий приоритет'}
          />
        </div>

        <p className="mt-4 text-sm text-gold-200/90">{intel.priority_advice}</p>
        <p className="mt-2 text-sm text-mist/60">{intel.department_hint}</p>

        <ul className="mt-4 space-y-1 text-sm text-mist/70">
          {intel.reasons.map((reason) => (
            <li key={reason}>• {reason}</li>
          ))}
        </ul>

        <div className="mt-6 flex flex-wrap gap-3">
          {phoneHref ? (
            <a
              href={phoneHref}
              className="border border-gold-400/40 bg-gold-400/10 px-4 py-2 text-sm
                text-gold-100 hover:bg-gold-400/20"
            >
              Позвонить · {application.phone}
            </a>
          ) : null}
          {emailHref ? (
            <a
              href={emailHref}
              className="border border-gold-400/30 px-4 py-2 text-sm text-gold-200
                hover:bg-gold-400/10"
            >
              Написать · {application.email}
            </a>
          ) : null}
        </div>

        <dl className="mt-8 grid gap-4 sm:grid-cols-2">
          <Field label="Ниша" value={application.niche} />
          <Field label="Роль" value={application.client_role} />
          <Field label="Размер компании" value={application.company_size} />
          <Field label="Размер бизнеса" value={application.business_size} />
          <Field label="Объём" value={application.company_volume} />
          <Field label="Объём потребности" value={application.demand_volume} />
          <Field label="Срок" value={application.deadline} />
          <Field label="Тип задачи" value={application.task_type} />
          <Field label="Продукт" value={application.product_interest} />
          <Field label="Бюджет" value={application.budget} />
          <Field label="Связь" value={application.contact_method} />
          <Field label="Удобное время" value={application.convenient_time} />
          <Field label="О бизнесе" value={application.business_info} wide />
          <Field label="Задачи" value={application.tasks} wide />
          <Field label="Комментарий" value={application.comment || '—'} wide />
        </dl>
      </div>
    </div>,
    document.body,
  );
}

interface IInfoBlockProps {
  title: string;
  value: string;
}

function InfoBlock({ title, value }: IInfoBlockProps) {
  return (
    <div className="border border-gold-400/15 bg-ink-950/40 px-4 py-3">
      <p className="text-[0.68rem] uppercase tracking-[0.18em] text-gold-200/55">
        {title}
      </p>
      <p className="mt-2 text-gold-100">{value}</p>
    </div>
  );
}

interface IFieldProps {
  label: string;
  value: string;
  wide?: boolean;
}

function Field({ label, value, wide = false }: IFieldProps) {
  return (
    <div className={wide ? 'sm:col-span-2' : undefined}>
      <dt className="text-[0.68rem] uppercase tracking-[0.16em] text-gold-200/55">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-mist/80 whitespace-pre-wrap">{value}</dd>
    </div>
  );
}

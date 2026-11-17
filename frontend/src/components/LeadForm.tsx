import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import { createBehavior, createLead, fetchAdminSettings } from '@/api/leads';
import { ApiClientError } from '@/api/client';
import { BudgetSlider } from '@/components/BudgetSlider';
import { Field } from '@/components/Field';
import { useBehaviorTracker } from '@/hooks/use-behavior-tracker';
import type { IAdminSettings, IServiceItem } from '@/types/api';
import type {
  TClientRole,
  TFieldErrors,
  TLeadFormValues,
  TSubmitState,
} from '@/types/form';
import { leadSchema, validateField } from '@/utils/lead-schema';

const DEFAULT_BUDGET_MIN = 5000;
const DEFAULT_BUDGET_MAX = 120000;
const DEFAULT_BUDGET_STEP = 1000;

const EMPTY_FORM: TLeadFormValues = {
  first_name: '',
  last_name: '',
  middle_name: '',
  phone: '',
  email: '',
  business_info: '',
  niche: '',
  company_size: '',
  business_size: '',
  company_volume: '',
  demand_volume: '',
  tasks: '',
  client_role: 'руководитель',
  deadline: '',
  task_type: '',
  product_interest: '',
  budget: String(DEFAULT_BUDGET_MIN),
  contact_method: 'телефон',
  convenient_time: '',
  comment: '',
};

/**
 * Анкета тёплого клиента: настройки с API, заявка и метрики.
 */
export function LeadForm() {
  const tracker = useBehaviorTracker();
  const [values, setValues] = useState<TLeadFormValues>(EMPTY_FORM);
  const [errors, setErrors] = useState<TFieldErrors>({});
  const [settings, setSettings] = useState<IAdminSettings | null>(null);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [submitState, setSubmitState] = useState<TSubmitState>('idle');
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await fetchAdminSettings();
        if (cancelled) {
          return;
        }
        setSettings(data);
        setValues((current) => ({
          ...current,
          budget: String(data.budget_min),
        }));
        setSettingsError(null);
      } catch (error) {
        if (cancelled) {
          return;
        }
        const message =
          error instanceof ApiClientError
            ? error.message
            : 'Не удалось загрузить настройки формы';
        setSettingsError(message);
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeServices = useMemo(
    () => (settings?.services ?? []).filter((item) => item.is_active),
    [settings],
  );

  const selectedService = useMemo(
    () =>
      activeServices.find((item) => item.title === values.product_interest) ?? null,
    [activeServices, values.product_interest],
  );

  const budgetBounds = useMemo(() => {
    if (selectedService) {
      return {
        min: selectedService.price_min,
        max: selectedService.price_max,
        step: settings?.budget_step ?? DEFAULT_BUDGET_STEP,
      };
    }
    return {
      min: settings?.budget_min ?? DEFAULT_BUDGET_MIN,
      max: settings?.budget_max ?? DEFAULT_BUDGET_MAX,
      step: settings?.budget_step ?? DEFAULT_BUDGET_STEP,
    };
  }, [selectedService, settings]);

  const budgetValue = Number.parseInt(values.budget, 10) || budgetBounds.min;

  const updateField = <K extends keyof TLeadFormValues>(
    key: K,
    value: TLeadFormValues[K],
  ) => {
    setValues((current) => ({ ...current, [key]: value }));
  };

  const handleBlur = (key: keyof TLeadFormValues) => {
    const message = validateField(key, values);
    setErrors((current) => ({ ...current, [key]: message }));
  };

  const handleServiceChange = (service: IServiceItem | null) => {
    if (!service) {
      updateField('product_interest', '');
      return;
    }
    setValues((current) => ({
      ...current,
      product_interest: service.title,
      budget: String(service.price_min),
    }));
    setErrors((current) => ({
      ...current,
      product_interest: undefined,
      budget: undefined,
    }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    tracker.trackClick('submit');

    const parsed = leadSchema.safeParse(values);
    if (!parsed.success) {
      const nextErrors: TFieldErrors = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0];
        if (typeof key === 'string') {
          nextErrors[key as keyof TLeadFormValues] = issue.message;
        }
      }
      setErrors(nextErrors);
      setSubmitState('error');
      setSubmitMessage('Проверьте поля формы');
      return;
    }

    setSubmitState('loading');
    setSubmitMessage(null);

    try {
      const lead = await createLead(parsed.data);
      try {
        await createBehavior(tracker.buildPayload(lead.id));
      } catch (behaviorError) {
        console.error('Не удалось сохранить метрики', behaviorError);
      }
      setSubmitState('success');
      setSubmitMessage('Заявка принята. Мы свяжемся в удобное время.');
      setValues({
        ...EMPTY_FORM,
        budget: String(settings?.budget_min ?? DEFAULT_BUDGET_MIN),
      });
      setErrors({});
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : 'Не удалось отправить заявку';
      setSubmitState('error');
      setSubmitMessage(message);
    }
  };

  return (
    <form
      className="relative z-10 mx-auto w-full max-w-5xl animate-rise"
      onSubmit={handleSubmit}
      noValidate
    >
      {settingsError ? (
        <p className="mb-8 border-l border-red-300/50 pl-4 text-red-200" role="alert">
          {settingsError}
        </p>
      ) : null}

      <section className="grid gap-8 md:grid-cols-3">
        <Field
          id="last_name"
          label="Фамилия"
          required
          value={values.last_name}
          error={errors.last_name}
          onChange={(value) => updateField('last_name', value)}
          onBlur={() => handleBlur('last_name')}
        />
        <Field
          id="first_name"
          label="Имя"
          required
          value={values.first_name}
          error={errors.first_name}
          onChange={(value) => updateField('first_name', value)}
          onBlur={() => handleBlur('first_name')}
        />
        <Field
          id="middle_name"
          label="Отчество"
          value={values.middle_name}
          error={errors.middle_name}
          onChange={(value) => updateField('middle_name', value)}
          onBlur={() => handleBlur('middle_name')}
        />
      </section>

      <section className="mt-10 grid gap-8 md:grid-cols-2">
        <Field
          id="phone"
          label="Телефон"
          type="tel"
          placeholder="+7 ..."
          value={values.phone}
          error={errors.phone}
          onChange={(value) => updateField('phone', value)}
          onBlur={() => handleBlur('phone')}
        />
        <Field
          id="email"
          label="Почта"
          type="email"
          placeholder="name@company.ru"
          value={values.email}
          error={errors.email}
          onChange={(value) => updateField('email', value)}
          onBlur={() => handleBlur('email')}
        />
      </section>

      <section className="mt-10 grid gap-8 md:grid-cols-2">
        <Field
          id="niche"
          label="Ниша бизнеса"
          required
          value={values.niche}
          error={errors.niche}
          onChange={(value) => updateField('niche', value)}
          onBlur={() => handleBlur('niche')}
        />
        <Field
          id="client_role"
          label="Кто вы"
          required
          value={values.client_role}
          error={errors.client_role}
          onChange={(value) => updateField('client_role', value as TClientRole)}
          onBlur={() => handleBlur('client_role')}
        >
          <select
            id="client_role"
            name="client_role"
            value={values.client_role}
            className="field-control"
            aria-invalid={Boolean(errors.client_role)}
            onChange={(event) => {
              updateField('client_role', event.target.value as TClientRole);
            }}
            onBlur={() => handleBlur('client_role')}
          >
            <option value="руководитель">Руководитель</option>
            <option value="сотрудник">Сотрудник</option>
          </select>
        </Field>
      </section>

      <section className="mt-10">
        <Field
          id="business_info"
          label="Информация о бизнесе"
          required
          multiline
          rows={4}
          value={values.business_info}
          error={errors.business_info}
          onChange={(value) => updateField('business_info', value)}
          onBlur={() => handleBlur('business_info')}
        />
      </section>

      <section className="mt-10 grid gap-8 md:grid-cols-2">
        <Field
          id="company_size"
          label="Размер компании"
          required
          value={values.company_size}
          error={errors.company_size}
          onChange={(value) => updateField('company_size', value)}
          onBlur={() => handleBlur('company_size')}
        />
        <Field
          id="business_size"
          label="Размер бизнеса"
          required
          value={values.business_size}
          error={errors.business_size}
          onChange={(value) => updateField('business_size', value)}
          onBlur={() => handleBlur('business_size')}
        />
        <Field
          id="company_volume"
          label="Объём"
          required
          value={values.company_volume}
          error={errors.company_volume}
          onChange={(value) => updateField('company_volume', value)}
          onBlur={() => handleBlur('company_volume')}
        />
        <Field
          id="demand_volume"
          label="Объём потребности"
          required
          value={values.demand_volume}
          error={errors.demand_volume}
          onChange={(value) => updateField('demand_volume', value)}
          onBlur={() => handleBlur('demand_volume')}
        />
      </section>

      <section className="mt-10">
        <Field
          id="tasks"
          label="Задачи"
          required
          multiline
          rows={4}
          value={values.tasks}
          error={errors.tasks}
          onChange={(value) => updateField('tasks', value)}
          onBlur={() => handleBlur('tasks')}
        />
      </section>

      <section className="mt-10 grid gap-8 md:grid-cols-2">
        <Field
          id="task_type"
          label="Тип задачи"
          required
          value={values.task_type}
          error={errors.task_type}
          onChange={(value) => updateField('task_type', value)}
          onBlur={() => handleBlur('task_type')}
        />
        <Field
          id="deadline"
          label="Срок результата"
          required
          value={values.deadline}
          error={errors.deadline}
          onChange={(value) => updateField('deadline', value)}
          onBlur={() => handleBlur('deadline')}
        />
      </section>

      <section className="mt-10">
        <div className="field-shell animate-rise">
          <label htmlFor="product_interest" className="field-label">
            Интересующий продукт
            <span className="text-gold-300"> *</span>
          </label>
          <select
            id="product_interest"
            name="product_interest"
            data-track="product_interest"
            value={values.product_interest}
            className="field-control"
            aria-invalid={Boolean(errors.product_interest)}
            onChange={(event) => {
              const next = activeServices.find(
                (item) => item.title === event.target.value,
              );
              handleServiceChange(next ?? null);
              if (!next && event.target.value !== '') {
                updateField('product_interest', event.target.value);
              }
            }}
            onBlur={() => handleBlur('product_interest')}
          >
            <option value="">Выберите услугу</option>
            {activeServices.map((service) => (
              <option key={service.code} value={service.title}>
                {service.title}
              </option>
            ))}
          </select>
          {selectedService?.description ? (
            <p className="text-sm text-mist/70">{selectedService.description}</p>
          ) : null}
          {errors.product_interest ? (
            <p className="field-error" role="alert">
              {errors.product_interest}
            </p>
          ) : null}
        </div>
      </section>

      <section className="mt-10">
        <BudgetSlider
          id="budget"
          label="Бюджет"
          value={budgetValue}
          min={budgetBounds.min}
          max={budgetBounds.max}
          step={budgetBounds.step}
          error={errors.budget}
          onChange={(value) => updateField('budget', String(value))}
          onBlur={() => handleBlur('budget')}
        />
      </section>

      <section className="mt-10 grid gap-8 md:grid-cols-2">
        <Field
          id="contact_method"
          label="Способ связи"
          required
          value={values.contact_method}
          error={errors.contact_method}
          onChange={(value) => updateField('contact_method', value)}
          onBlur={() => handleBlur('contact_method')}
        >
          <select
            id="contact_method"
            name="contact_method"
            value={values.contact_method}
            className="field-control"
            onChange={(event) => updateField('contact_method', event.target.value)}
            onBlur={() => handleBlur('contact_method')}
          >
            <option value="телефон">Телефон</option>
            <option value="почта">Почта</option>
            <option value="мессенджер">Мессенджер</option>
          </select>
        </Field>
        <Field
          id="convenient_time"
          label="Удобное время"
          required
          placeholder="Будни после 16:00"
          value={values.convenient_time}
          error={errors.convenient_time}
          onChange={(value) => updateField('convenient_time', value)}
          onBlur={() => handleBlur('convenient_time')}
        />
      </section>

      <section className="mt-10">
        <Field
          id="comment"
          label="Комментарий"
          multiline
          rows={3}
          value={values.comment}
          error={errors.comment}
          onChange={(value) => updateField('comment', value)}
          onBlur={() => handleBlur('comment')}
        />
      </section>

      <div className="mt-12 flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="submit"
          data-track="submit"
          disabled={submitState === 'loading'}
          aria-label="Отправить заявку"
          className="border border-gold-300/70 bg-gold-400/10 px-10 py-4 font-display text-xl
            tracking-[0.08em] text-gold-100 transition hover:bg-gold-400/20
            disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitState === 'loading' ? 'Отправляем…' : 'Отправить заявку'}
        </button>
        {submitMessage ? (
          <p
            className={
              submitState === 'success'
                ? 'text-gold-200'
                : 'text-red-200'
            }
            role="status"
          >
            {submitMessage}
          </p>
        ) : (
          <p className="max-w-sm text-sm text-mist/55">
            Телефон или почта обязательны. Метрики страницы уходят вместе с заявкой.
          </p>
        )}
      </div>
    </form>
  );
}

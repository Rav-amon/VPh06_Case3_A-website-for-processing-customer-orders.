import { formatBudget } from '@/utils/format';

interface IBudgetSliderProps {
  id: string;
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  error?: string;
  onChange: (value: number) => void;
  onBlur: () => void;
}

/** Ползунок бюджета в границах, пришедших с backend. */
export function BudgetSlider({
  id,
  label,
  value,
  min,
  max,
  step,
  error,
  onChange,
  onBlur,
}: IBudgetSliderProps) {
  const safeMax = max > min ? max : min + step;
  const safeValue = Math.min(Math.max(value, min), safeMax);

  return (
    <div className="field-shell animate-rise">
      <div className="flex items-end justify-between gap-4">
        <label htmlFor={id} className="field-label">
          {label}
          <span className="text-gold-300"> *</span>
        </label>
        <span className="font-display text-2xl text-gold-200">{formatBudget(safeValue)}</span>
      </div>
      <input
        id={id}
        name={id}
        type="range"
        min={min}
        max={safeMax}
        step={step}
        value={safeValue}
        aria-valuemin={min}
        aria-valuemax={safeMax}
        aria-valuenow={safeValue}
        aria-invalid={Boolean(error)}
        className="mt-4"
        onChange={(event) => onChange(Number(event.target.value))}
        onBlur={onBlur}
      />
      <div className="mt-2 flex justify-between text-xs tracking-wide text-mist/50">
        <span>{formatBudget(min)}</span>
        <span>{formatBudget(safeMax)}</span>
      </div>
      {error ? (
        <p className="field-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

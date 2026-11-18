import type { ChangeEvent, FocusEvent, ReactNode } from 'react';

interface IFieldProps {
  id: string;
  label: string;
  value: string;
  error?: string;
  required?: boolean;
  type?: 'text' | 'email' | 'tel' | 'password' | 'number';
  placeholder?: string;
  multiline?: boolean;
  rows?: number;
  children?: ReactNode;
  onChange: (value: string) => void;
  onBlur: () => void;
}

/** Поле формы с подписью и ошибкой после blur. */
export function Field({
  id,
  label,
  value,
  error,
  required = false,
  type = 'text',
  placeholder,
  multiline = false,
  rows = 4,
  children,
  onChange,
  onBlur,
}: IFieldProps) {
  const describedBy = error ? `${id}-error` : undefined;

  const handleChange = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    onChange(event.target.value);
  };

  const handleBlur = (
    _event: FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    onBlur();
  };

  return (
    <div className="field-shell animate-rise">
      <label htmlFor={id} className="field-label">
        {label}
        {required ? <span className="text-gold-300"> *</span> : null}
      </label>
      {children ? (
        children
      ) : multiline ? (
        <textarea
          id={id}
          name={id}
          value={value}
          rows={rows}
          placeholder={placeholder}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy}
          className="field-control-area"
          onChange={handleChange}
          onBlur={handleBlur}
        />
      ) : (
        <input
          id={id}
          name={id}
          type={type}
          value={value}
          placeholder={placeholder}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy}
          className="field-control"
          onChange={handleChange}
          onBlur={handleBlur}
        />
      )}
      {error ? (
        <p id={`${id}-error`} className="field-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

import type { ReactNode } from 'react';

interface LabeledFieldProps {
  label: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}

export function LabeledField({ label, hint, children, className = '' }: LabeledFieldProps) {
  return (
    <label className={`field ${className}`.trim()}>
      <span className="field__label">{label}</span>
      {hint && <span className="field__hint">{hint}</span>}
      {children}
    </label>
  );
}

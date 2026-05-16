interface StatCardProps {
  value: string | number;
  label: string;
  unit?: string;
}

export function StatCard({ value, label, unit }: StatCardProps) {
  return (
    <div className="stat-card">
      <span className="stat-card__value">{value}</span>
      <span className="stat-card__label">{label}</span>
      {unit && <span className="stat-card__unit">{unit}</span>}
    </div>
  );
}

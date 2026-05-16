interface PlaceholderCardProps {
  title: string;
  children?: React.ReactNode;
}

export function PlaceholderCard({ title, children }: PlaceholderCardProps) {
  return (
    <section className="card">
      <h2 className="card__title">{title}</h2>
      <div className="card__body">
        {children ?? <p className="muted">Раздел в разработке — подключите API бэкенда.</p>}
      </div>
    </section>
  );
}

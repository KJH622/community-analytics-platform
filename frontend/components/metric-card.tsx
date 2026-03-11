type MetricCardProps = {
  label: string;
  value: string;
  caption: string;
};

export function MetricCard({ label, value, caption }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className="metric-caption">{caption}</div>
    </div>
  );
}

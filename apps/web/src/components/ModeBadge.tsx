interface ModeBadgeProps {
  mode: string;
  showLabel?: boolean;
}

const MODE_STYLES: Record<string, string> = {
  real: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  mock: 'bg-amber-100 text-amber-800 border-amber-200',
  fixture: 'bg-blue-100 text-blue-800 border-blue-200',
  rule_based: 'bg-purple-100 text-purple-800 border-purple-200',
  unavailable: 'bg-slate-100 text-slate-600 border-slate-200',
  degraded: 'bg-rose-100 text-rose-800 border-rose-200',
};

const MODE_LABELS: Record<string, string> = {
  real: 'REAL',
  mock: 'MOCK',
  fixture: 'FIXTURE',
  rule_based: 'RULE',
  unavailable: 'N/A',
  degraded: 'DEGRADED',
};

export default function ModeBadge({ mode, showLabel = true }: ModeBadgeProps) {
  const style = MODE_STYLES[mode] || MODE_STYLES.unavailable;
  const label = MODE_LABELS[mode] || mode.toUpperCase();

  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${style}`}
      title={`Module mode: ${mode}`}
    >
      {showLabel && label}
    </span>
  );
}

export default function StatCard({ icon: Icon, label, value, description }) {
  return (
    <div className="paper p-5">
      <div className="mb-4 flex items-center justify-between">
        <span className="grid h-9 w-9 place-items-center rounded-lg bg-slate-50 text-slate2"><Icon size={18} aria-hidden="true" /></span>
      </div>
      <p className="text-3xl font-semibold text-ink">{value}</p>
      <p className="mt-1 text-sm font-semibold text-ink">{label}</p>
      {description && <p className="mt-1 text-xs leading-5 text-slate2">{description}</p>}
    </div>
  );
}

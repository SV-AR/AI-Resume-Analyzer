export default function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center gap-3 py-10 justify-center text-slate2" role="status">
      <span className="h-5 w-5 rounded-full border-2 border-rule border-t-margin animate-spin" aria-hidden="true" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

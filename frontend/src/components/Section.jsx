export default function Section({ title, hint, children, className = "" }) {
  return (
    <section className={`paper p-5 sm:p-6 ${className}`}>
      <div className="mb-5 border-b border-rule/70 pb-4">
        <h2 className="text-lg font-semibold leading-tight">{title}</h2>
        {hint && <p className="mt-1 text-xs leading-5 text-slate2">{hint}</p>}
      </div>
      {children}
    </section>
  );
}

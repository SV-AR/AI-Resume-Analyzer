export default function PageHeader({ eyebrow, title, children, actions }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-5">
      <div>
        {eyebrow && <p className="mb-2 text-xs font-semibold uppercase text-slate2">{eyebrow}</p>}
        <h1 className="page-heading">{title}</h1>
        {children && <p className="page-subtitle">{children}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

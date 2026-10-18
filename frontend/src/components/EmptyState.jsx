export default function EmptyState({ title, children, action }) {
  return (
    <div className="paper p-8 text-center">
      <h3 className="text-lg font-medium">{title}</h3>
      {children && <p className="text-sm text-slate2 mt-2 max-w-md mx-auto">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

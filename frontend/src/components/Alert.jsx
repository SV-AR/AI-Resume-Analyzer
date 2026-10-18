const TONES = {
  error: "border-redpen bg-red-50 text-redpen",
  success: "border-pass bg-green-50 text-pass",
  info: "border-margin bg-blue-50 text-margin",
};

export default function Alert({ tone = "info", children, onClose }) {
  if (!children) return null;
  return (
    <div role={tone === "error" ? "alert" : "status"} className={`border-l-4 rounded px-4 py-3 text-sm flex justify-between gap-4 ${TONES[tone]}`}>
      <div>{children}</div>
      {onClose && (
        <button onClick={onClose} aria-label="Dismiss" className="font-bold">×</button>
      )}
    </div>
  );
}

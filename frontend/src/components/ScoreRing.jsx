/** Circular gauge for a 0-100 score. */
export default function ScoreRing({ value, label, sublabel, size = 132 }) {
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(100, value || 0));
  const color = "#2563eb";
  return (
    <figure className="flex flex-col items-center text-center" aria-label={`${label}: ${Math.round(v)} out of 100`}>
      <svg width={size} height={size} role="img" aria-hidden="true">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#e4e9ee" strokeWidth={stroke} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - v / 100)} transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central" fontSize={size * 0.28} fill="#1e293b" fontWeight="700">
          {Math.round(v)}
        </text>
      </svg>
      <figcaption className="mt-2 text-sm font-medium">{label}</figcaption>
      {sublabel && <span className="text-xs text-slate2 max-w-[11rem]">{sublabel}</span>}
    </figure>
  );
}

const TONE = { high: "border-redpen", medium: "border-[#b7791f]", low: "border-rule", info: "border-pass" };

export default function RecommendationList({ items = [], limit }) {
  const list = limit ? items.slice(0, limit) : items;
  if (!list.length) return <p className="text-sm text-slate2">No recommendations for this analysis.</p>;
  return (
    <ol className="space-y-3">
      {list.map((r, idx) => (
        <li key={idx} className={`rounded-lg border border-rule/80 border-l-4 bg-[#fbfcfe] p-4 ${TONE[r.priority] || "border-rule"}`}>
          <h3 className="font-semibold text-[15px]">{r.title}</h3>
          <p className="mt-2 text-sm leading-6 whitespace-pre-line">{r.message}</p>
          <p className="mt-3 border-t border-rule/70 pt-2 text-xs leading-5 text-slate2"><span className="font-semibold text-ink">Why this matters: </span>{r.reason}</p>
        </li>
      ))}
    </ol>
  );
}

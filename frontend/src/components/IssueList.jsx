import { AlertCircle, AlertTriangle, Info } from "lucide-react";
const SEV = { high: ["High", "bg-red-50 text-redpen border-redpen/20", AlertCircle], medium: ["Medium", "bg-amber-50 text-amber-700 border-amber-200", AlertTriangle], low: ["Low", "bg-slate-50 text-slate2 border-rule", Info] };

export default function IssueList({ issues = [] }) {
  if (!issues.length) return <p className="text-sm text-pass">No issues found by the quality checklist.</p>;
  return (
    <ul className="space-y-3">
      {issues.map((i, idx) => (
        <li key={idx} className="flex gap-3 rounded-lg border border-rule/80 bg-[#fbfcfe] p-3 text-sm">
          {(() => { const [label, tone, Icon] = SEV[i.severity] || SEV.low; return <><span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border ${tone}`}><Icon size={16} aria-hidden="true" /></span><div><p className="font-semibold text-ink">{label} priority</p><p className="mt-0.5 leading-5 text-slate2">{i.message}</p></div></>; })()}
        </li>
      ))}
    </ul>
  );
}

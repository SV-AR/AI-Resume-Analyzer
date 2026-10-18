import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, PolarAngleAxis, PolarGrid,
  PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { COMPONENT_LABELS } from "../utils/format";

const COLORS = ["#2563eb", "#64748b", "#94a3b8", "#cbd5e1"];

export function ComponentRadar({ scores }) {
  const data = Object.entries(scores || {}).map(([k, v]) => ({ name: COMPONENT_LABELS[k] || k, value: v }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis dataKey="name" tick={{ fontSize: 11, fill: "#1e293b" }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
        <Radar dataKey="value" stroke="#2563eb" fill="#2563eb" fillOpacity={0.16} />
        <Tooltip formatter={(v) => `${Math.round(v)} / 100`} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

export function HistoryChart({ history = [] }) {
  const data = history.map((h, i) => ({
    name: `#${h.id}`, match: h.overall_score, similarity: Math.round((h.semantic_similarity || 0) * 100), label: h.job_title, i,
  }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ left: -10, right: 10, top: 5 }}>
        <CartesianGrid stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
        <Tooltip labelFormatter={(_, p) => p?.[0]?.payload?.label || ""} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="match" name="Match score" stroke="#2563eb" strokeWidth={2} dot />
        <Line type="monotone" dataKey="similarity" name="Semantic similarity ×100" stroke="#64748b" strokeDasharray="4 3" dot />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function CategoryChart({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie data={data} dataKey="count" nameKey="category" innerRadius={48} outerRadius={85} paddingAngle={2}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function HorizontalBars({ data = [], xKey, yKey, color = "#3b6ea5", domain }) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(120, data.length * 34 + 30)}>
      <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
        <CartesianGrid stroke="#e2e8f0" horizontal={false} />
        <XAxis type="number" domain={domain} tick={{ fontSize: 11 }} allowDecimals={false} />
        <YAxis type="category" dataKey={yKey} width={110} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey={xKey} fill={color} radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

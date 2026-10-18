export const pct = (v) => `${Math.round(v)}%`;
export const sim = (v) => (v ?? 0).toFixed(2);
export const date = (iso) => new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });

export const COMPONENT_LABELS = {
  skills: "Skills match",
  semantic: "Semantic similarity",
  experience: "Experience relevance",
  education: "Education relevance",
  structure: "Resume structure",
};

/** Colour band for a 0-100 score. */
export function scoreTone(score) {
  if (score >= 70) return "#2f7d5b";
  if (score >= 45) return "#b7791f";
  return "#c8434a";
}

export function groupBy(items, key) {
  return items.reduce((acc, it) => {
    (acc[it[key]] = acc[it[key]] || []).push(it);
    return acc;
  }, {});
}

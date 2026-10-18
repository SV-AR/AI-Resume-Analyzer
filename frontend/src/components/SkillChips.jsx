const CLASS = { match: "chip-match", miss: "chip-miss", extra: "chip-extra", plain: "chip-plain" };

export default function SkillChips({ skills = [], variant = "plain", empty = "None" }) {
  if (!skills.length) return <p className="text-sm text-slate2">{empty}</p>;
  return (
    <ul className="flex flex-wrap gap-x-2 gap-y-2">
      {skills.map((s) => {
        const name = typeof s === "string" ? s : s.name;
        const title = typeof s === "string" ? undefined : `Heuristic confidence ${s.confidence} (not a model probability)`;
        return (
          <li key={name} className={CLASS[variant]} title={title}>
            {name}
          </li>
        );
      })}
    </ul>
  );
}

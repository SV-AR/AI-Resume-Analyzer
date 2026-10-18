import { Link, useParams } from "react-router-dom";
import Alert from "../components/Alert";
import { ComponentRadar, HorizontalBars } from "../components/Charts";
import Disclaimer from "../components/Disclaimer";
import IssueList from "../components/IssueList";
import RecommendationList from "../components/RecommendationList";
import ScoreRing from "../components/ScoreRing";
import Section from "../components/Section";
import SkillChips from "../components/SkillChips";
import Spinner from "../components/Spinner";
import { useAsync } from "../hooks/useAsync";
import { matchApi } from "../services/api";
import { COMPONENT_LABELS, scoreTone, sim } from "../utils/format";
import PageHeader from "../components/PageHeader";

export default function MatchResult() {
  const { id } = useParams();
  const { data: a, loading, error } = useAsync(() => matchApi.get(id), [id]);
  if (loading) return <Spinner label="Loading analysis…" />;
  if (error) return <Alert tone="error">{error}</Alert>;

  const { skills, semantic, experience, education, quality } = a.details;
  const sections = Object.entries(semantic.section_similarity).map(([name, v]) => ({ name, similarity: Math.round(v * 100) / 100 }));
  const coverage = semantic.requirement_coverage || [];

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Match report" title={a.job_title}>
        Resume: <Link to={`/resume/${a.resume_id}`} className="font-medium text-margin hover:underline">{a.resume_name}</Link> · {new Date(a.created_at).toLocaleString()}
      </PageHeader>
      <Disclaimer>{a.disclaimer}</Disclaimer>

      <Section title="Scores">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <ScoreRing value={a.overall_score} label="Resume-job match score" sublabel="Weighted total of the five parts" />
          <ScoreRing value={a.semantic_similarity * 100} label="Semantic similarity" sublabel={`cosine similarity ${sim(a.semantic_similarity)}`} />
          <ScoreRing value={a.quality_score} label="Resume quality" sublabel="Includes job-specific skills check" />
        </div>
      </Section>

      <div className="grid md:grid-cols-2 gap-6">
        <Section title="How the match score is built" hint={a.details.score_explanation}>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-slate2 border-b border-rule"><th className="py-1.5">Component</th><th>Score</th><th>Weight</th><th className="text-right">Contribution</th></tr></thead>
            <tbody>
              {Object.keys(a.weights).map((k) => (
                <tr key={k} className="border-b border-rule last:border-0">
                  <td className="py-1.5">{COMPONENT_LABELS[k]}</td>
                  <td style={{ color: scoreTone(a.component_scores[k]) }} className="font-medium">{a.component_scores[k].toFixed(1)}</td>
                  <td>{Math.round(a.weights[k] * 100)}%</td>
                  <td className="text-right">{(a.component_scores[k] * a.weights[k]).toFixed(1)}</td>
                </tr>
              ))}
              <tr className="font-bold"><td className="pt-2" colSpan={3}>Total</td><td className="pt-2 text-right">{a.overall_score.toFixed(1)}</td></tr>
            </tbody>
          </table>
          <div className="mt-3 space-y-1 text-xs text-slate2">
            <p><span className="font-medium">Experience: </span>{experience.note}</p>
            <p><span className="font-medium">Education: </span>{education.note}</p>
          </div>
        </Section>
        <Section title="Component profile"><ComponentRadar scores={a.component_scores} /></Section>
      </div>

      <Section title="Skill comparison" hint="Skills are normalised first (for example JS → JavaScript), then compared.">
        <div className="grid md:grid-cols-3 gap-6">
          <div><h3 className="text-sm font-medium mb-1.5">Matched ({skills.matched_skills.length})</h3><SkillChips variant="match" skills={skills.matched_skills} empty="None matched" /></div>
          <div><h3 className="text-sm font-medium mb-1.5">Missing ({skills.missing_skills.length})</h3><SkillChips variant="miss" skills={skills.missing_skills} empty="Nothing missing" /></div>
          <div><h3 className="text-sm font-medium mb-1.5">Additional ({skills.additional_skills.length})</h3><SkillChips variant="extra" skills={skills.additional_skills} /></div>
        </div>
      </Section>

      <Section title="Skill gap analysis" hint="Priority comes only from how the job description words each skill.">
        <div className="grid md:grid-cols-3 gap-6">
          {[["critical", "Critical", "Explicitly required"], ["important", "Important", "Preferred or part of the duties"], ["optional", "Optional", "Mentioned only elsewhere"]].map(([k, t, h]) => (
            <div key={k}><h3 className="text-sm font-medium">{t}</h3><p className="text-xs text-slate2 mb-1.5">{h}</p><SkillChips variant="miss" skills={skills.skill_gaps[k]} empty="None" /></div>
          ))}
        </div>
      </Section>

      <div className="grid md:grid-cols-2 gap-6">
        <Section title="Similarity by resume section" hint="Cosine similarity of each section's embedding with the job description">
          <HorizontalBars data={sections} xKey="similarity" yKey="name" domain={[0, 1]} />
        </Section>
        <Section title="Requirement coverage" hint={coverage.length ? `${semantic.coverage_ratio !== null ? Math.round(semantic.coverage_ratio * 100) : 0}% of requirement lines have a close resume line (threshold ${semantic.coverage_threshold}, a tunable heuristic)` : "No requirement lines were extracted"}>
          <ul className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {coverage.map((c, i) => (
              <li key={i} className="text-sm border-l-4 pl-3" style={{ borderColor: c.covered ? "#2f7d5b" : "#c8434a" }}>
                <p>{c.requirement}</p>
                <p className="text-xs text-slate2">{c.kind} · best match {sim(c.best_similarity)}{c.covered ? ` — “${c.best_match}”` : " — no close line"}</p>
              </li>
            ))}
          </ul>
        </Section>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <Section title="Resume issues" hint="Resume Quality Analysis (rule-based, not an ATS prediction)"><IssueList issues={quality.issues} /></Section>
        <Section title="Recommendations" hint="Based only on what was found in your resume and this job description">
          <RecommendationList items={a.recommendations} />
        </Section>
      </div>
    </div>
  );
}

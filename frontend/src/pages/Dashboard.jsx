import { Link } from "react-router-dom";
import Alert from "../components/Alert";
import { CategoryChart, ComponentRadar, HistoryChart, HorizontalBars } from "../components/Charts";
import Disclaimer from "../components/Disclaimer";
import EmptyState from "../components/EmptyState";
import IssueList from "../components/IssueList";
import ScoreRing from "../components/ScoreRing";
import Section from "../components/Section";
import SkillChips from "../components/SkillChips";
import Spinner from "../components/Spinner";
import { useAsync } from "../hooks/useAsync";
import { dashboardApi, matchApi } from "../services/api";
import RecommendationList from "../components/RecommendationList";
import { sim } from "../utils/format";
import { BriefcaseBusiness, FileText, Gauge, Sparkles } from "lucide-react";
import PageHeader from "../components/PageHeader";
import StatCard from "../components/StatCard";

export default function Dashboard() {
  const { data: d, loading, error } = useAsync(() => dashboardApi.get(), []);
  const latestId = d?.latest_analysis?.id;
  const { data: latestFull } = useAsync(() => (latestId ? matchApi.get(latestId) : Promise.resolve(null)), [latestId]);

  if (loading) return <Spinner label="Loading dashboard…" />;
  if (error) return <Alert tone="error">{error}</Alert>;

  const la = d.latest_analysis;
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Dashboard" title={`Good ${new Date().getHours() < 12 ? "morning" : new Date().getHours() < 18 ? "afternoon" : "evening"}, ${d.user?.full_name?.trim() || "User"}`} actions={<div className="flex flex-wrap gap-2">
        <Link to="/job-analysis" className="btn-ghost">New job match</Link>
        <Link to="/upload" className="btn-primary">Upload resume</Link>
      </div>}>
        Here&apos;s an overview of your resume performance.
      </PageHeader>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={FileText} value={d.counts.resumes} label="Resumes" description="Documents uploaded to your workspace" />
        <StatCard icon={BriefcaseBusiness} value={d.counts.jobs} label="Job descriptions" description="Roles analysed for requirements" />
        <StatCard icon={Sparkles} value={d.counts.analyses} label="Analyses" description="Resume-to-job comparisons completed" />
        <StatCard icon={Gauge} value={la ? `${Math.round(la.quality_score)}/100` : "—"} label="Resume quality" description={la ? "Latest available quality score" : "Upload a resume to see your score"} />
      </div>

      {!d.counts.resumes && (
        <EmptyState title="Start by uploading a resume" action={<Link to="/upload" className="btn-primary">Upload resume</Link>}>
          We extract your skills, education, experience and projects, then check the resume quality.
        </EmptyState>
      )}
      {d.counts.resumes > 0 && !la && (
        <EmptyState title="Match your resume to a job" action={<Link to="/job-analysis" className="btn-primary">Paste a job description</Link>}>
          You will see matched and missing skills, a semantic similarity score and recommendations.
        </EmptyState>
      )}

      {la && (
        <>
          <Section title="Latest analysis" hint={`${la.resume_name} vs ${la.job_title}`} className="overflow-hidden">
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4 md:gap-8 items-start">
              <ScoreRing value={la.overall_score} label="Job match score" sublabel="Weighted resume-job match" />
              <ScoreRing value={(la.semantic_similarity || 0) * 100} label="Semantic similarity" sublabel={`cosine ${sim(la.semantic_similarity)}`} />
              <ScoreRing value={la.quality_score} label="Resume quality" sublabel="Rule-based checklist" />
              <div className="p-2 text-sm">
                <p className="font-semibold">{la.recommendation_count} recommendations</p>
                <p className="mt-1 text-xs leading-5 text-slate2">Prioritised suggestions based on your resume and this role.</p>
                <Link className="mt-3 inline-block font-semibold text-margin hover:underline" to={`/match/${la.id}`}>View full analysis →</Link>
              </div>
            </div>
            <div className="mt-4"><Disclaimer /></div>
          </Section>

          <div className="grid md:grid-cols-2 gap-6">
            <Section title="Score components" hint="Skills 40% · Semantic 30% · Experience 15% · Education 10% · Structure 5%">
              <ComponentRadar scores={la.component_scores} />
            </Section>
            <Section title="Skills against this job">
              <div className="space-y-4">
                <div><h3 className="text-sm font-medium mb-1.5">Matched</h3><SkillChips variant="match" skills={la.matched_skills} empty="No matched skills" /></div>
                <div><h3 className="text-sm font-medium mb-1.5">Missing</h3><SkillChips variant="miss" skills={la.missing_skills} empty="Nothing missing" /></div>
                <div><h3 className="text-sm font-medium mb-1.5">Additional (not asked for)</h3><SkillChips variant="extra" skills={la.additional_skills} /></div>
              </div>
            </Section>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {["critical", "important", "optional"].map((k) => (
              <Section key={k} title={`${k[0].toUpperCase()}${k.slice(1)} gaps`}
                hint={{ critical: "Explicitly required", important: "Preferred or part of the duties", optional: "Mentioned elsewhere" }[k]}>
                <SkillChips variant="miss" skills={la.skill_gaps?.[k] || []} />
              </Section>
            ))}
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <Section title="Resume issues"><IssueList issues={la.issues} /></Section>
            <Section title="Top recommendations" hint="Each one explains why it was generated">
              <RecommendationList items={latestFull?.recommendations || []} limit={3} />
            </Section>
          </div>
        </>
      )}

      {d.history.length > 1 && (
        <Section title="Analysis history"><HistoryChart history={d.history} /></Section>
      )}
      <div className="grid md:grid-cols-2 gap-6">
        {d.skills_by_category.length > 0 && (
          <Section title="Detected skills by category" hint="Latest resume"><CategoryChart data={d.skills_by_category} /></Section>
        )}
        {d.top_missing_skills.length > 0 && (
          <Section title="Most frequently missing skills" hint="Across all analyses">
            <HorizontalBars data={d.top_missing_skills} xKey="count" yKey="skill" color="#64748b" />
          </Section>
        )}
      </div>
    </div>
  );
}

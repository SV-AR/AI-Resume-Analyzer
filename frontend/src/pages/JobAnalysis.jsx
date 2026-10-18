import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Alert from "../components/Alert";
import Section from "../components/Section";
import SkillChips from "../components/SkillChips";
import Spinner from "../components/Spinner";
import { useAsync } from "../hooks/useAsync";
import { errorMessage, jobApi, matchApi, resumeApi } from "../services/api";
import PageHeader from "../components/PageHeader";

export default function JobAnalysis() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { data: resumes, loading } = useAsync(() => resumeApi.list(), []);
  const { data: savedJobs } = useAsync(() => jobApi.list(), []);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [job, setJob] = useState(null);
  const [resumeId, setResumeId] = useState(params.get("resume") || "");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!resumeId && resumes?.length) setResumeId(String(resumes[0].id));
  }, [resumes, resumeId]);

  const analyze = async (e) => {
    e.preventDefault();
    setError("");
    setBusy("analyze");
    try {
      setJob(await jobApi.analyze({ title: title.trim() || null, description: text }));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy("");
    }
  };

  const loadSaved = async (id) => {
    if (!id) return;
    setError("");
    try {
      const j = await jobApi.get(id);
      setJob(j); setTitle(j.title); setText(j.raw_text);
    } catch (err) {
      setError(errorMessage(err));
    }
  };

  const match = async () => {
    setError("");
    setBusy("match");
    try {
      const a = await matchApi.analyze({ resume_id: Number(resumeId), job_id: job.id });
      navigate(`/match/${a.id}`);
    } catch (err) {
      setError(errorMessage(err));
      setBusy("");
    }
  };

  if (loading) return <Spinner />;
  const a = job?.analysis;
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Analysis" title="Job matching">
        Compare your resume against a job description.
      </PageHeader>
      <Alert tone="error" onClose={() => setError("")}>{error}</Alert>

      <Section title="1. Paste a job description" hint="Only skills and requirements that appear in the text are extracted.">
        <form onSubmit={analyze} className="space-y-3">
          {savedJobs?.length > 0 && (
            <div>
              <label htmlFor="saved" className="label">Or reuse a saved job</label>
              <select id="saved" className="input" defaultValue="" onChange={(e) => loadSaved(e.target.value)}>
                <option value="">Select…</option>
                {savedJobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
              </select>
            </div>
          )}
          <div>
            <label htmlFor="title" className="label">Job title (optional)</label>
            <input id="title" className="input" maxLength={255} value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div>
            <label htmlFor="jd" className="label">Job description</label>
            <textarea id="jd" required minLength={50} rows={12} className="input resize-y leading-6" value={text} onChange={(e) => setText(e.target.value)}
              placeholder={"Requirements\n- Python and SQL\n\nNice to have\n- Docker"} />
            <p className="text-xs text-slate2 mt-1">{text.length} / 20000 characters</p>
          </div>
          <button className="btn-primary" disabled={busy === "analyze" || text.length < 50}>{busy === "analyze" ? "Analysing…" : "Analyse job description"}</button>
        </form>
      </Section>

      {a && (
        <>
          <Section title="Extracted requirements" hint={a.structure_detected ? "Section headings were detected." : "No headings detected: skills count as required unless marked preferred."}>
            {a.warnings.map((w) => <Alert key={w} tone="info">{w}</Alert>)}
            <div className="grid md:grid-cols-2 gap-5 mt-3">
              <div><h3 className="text-sm font-medium mb-1.5">Required skills</h3><SkillChips variant="match" skills={a.required_skills} /></div>
              <div><h3 className="text-sm font-medium mb-1.5">Preferred skills</h3><SkillChips variant="plain" skills={a.preferred_skills} /></div>
              <div><h3 className="text-sm font-medium mb-1.5">Mentioned in responsibilities</h3><SkillChips variant="plain" skills={a.responsibility_skills} /></div>
              <div><h3 className="text-sm font-medium mb-1.5">Mentioned elsewhere</h3><SkillChips variant="plain" skills={a.other_skills} /></div>
              <div>
                <h3 className="text-sm font-medium mb-1.5">Experience</h3>
                {a.experience_requirements.length ? <ul className="text-sm list-disc pl-5">{a.experience_requirements.map((x, i) => <li key={i}>{x.text}</li>)}</ul> : <p className="text-sm text-slate2">None stated</p>}
              </div>
              <div>
                <h3 className="text-sm font-medium mb-1.5">Education</h3>
                {a.education_requirements.length ? <ul className="text-sm list-disc pl-5">{a.education_requirements.map((x, i) => <li key={i}>{x}</li>)}</ul> : <p className="text-sm text-slate2">None stated</p>}
              </div>
              <div className="md:col-span-2">
                <h3 className="text-sm font-medium mb-1.5">Responsibilities</h3>
                {a.responsibilities.length ? <ul className="text-sm list-disc pl-5 space-y-0.5">{a.responsibilities.map((x, i) => <li key={i}>{x}</li>)}</ul> : <p className="text-sm text-slate2">None detected</p>}
              </div>
              <div className="md:col-span-2">
                <h3 className="text-sm font-medium mb-1.5">Important keywords <span className="font-normal text-slate2">(frequency based)</span></h3>
                <SkillChips variant="plain" skills={a.keywords} />
              </div>
            </div>
          </Section>

          <Section title="2. Match a resume against this job">
            {!resumes?.length ? <Alert tone="info">Upload a resume first on the Resumes page.</Alert> : (
              <div className="flex flex-wrap items-end gap-3">
                <div className="min-w-[16rem]">
                  <label htmlFor="resume" className="label">Resume</label>
                  <select id="resume" className="input" value={resumeId} onChange={(e) => setResumeId(e.target.value)}>
                    {resumes.map((r) => <option key={r.id} value={r.id}>{r.original_filename}{r.candidate_name ? ` (${r.candidate_name})` : ""}</option>)}
                  </select>
                </div>
                <button className="btn-primary" onClick={match} disabled={busy === "match" || !resumeId}>{busy === "match" ? "Computing embeddings…" : "Run match analysis"}</button>
              </div>
            )}
            {busy === "match" && <p className="text-xs text-slate2 mt-3">The first run may take a while because the transformer model is loaded once.</p>}
          </Section>
        </>
      )}
    </div>
  );
}

import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Alert from "../components/Alert";
import EmptyState from "../components/EmptyState";
import Section from "../components/Section";
import Spinner from "../components/Spinner";
import { useAsync } from "../hooks/useAsync";
import { errorMessage, resumeApi } from "../services/api";
import { date } from "../utils/format";
import PageHeader from "../components/PageHeader";

const MAX_MB = 5;

export default function Upload() {
  const navigate = useNavigate();
  const input = useRef(null);
  const { data: resumes, loading, error: listError, reload } = useAsync(() => resumeApi.list(), []);
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [drag, setDrag] = useState(false);

  const pick = (f) => {
    setError("");
    if (!f) return;
    const ext = f.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx"].includes(ext)) return setError("Unsupported file format. Please upload PDF or DOCX.");
    if (f.size === 0) return setError("The selected file is empty.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`File is too large. Maximum size is ${MAX_MB} MB.`);
    setFile(f);
  };

  const submit = async () => {
    setBusy(true);
    setError("");
    setProgress(0);
    try {
      const resume = await resumeApi.upload(file, setProgress);
      navigate(`/resume/${resume.id}`);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Delete this resume and its analyses?")) return;
    try {
      await resumeApi.remove(id);
      setMessage("Resume deleted.");
      reload();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader eyebrow="Resumes" title="My resumes">
        Manage your uploaded resumes and review their analysis.
      </PageHeader>
      <Section title="Upload a resume" hint="PDF or DOCX, up to 5 MB. Scanned (image-only) PDFs are not supported yet.">
        <div
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files[0]); }}
          className={`rounded-xl border-2 border-dashed p-8 text-center transition-colors sm:p-12 ${drag ? "border-margin bg-blue-50" : "border-rule bg-slate-50 hover:border-margin/60"}`}
        >
          <p className="text-sm">{file ? <><span className="font-medium">{file.name}</span> ({Math.round(file.size / 1024)} KB)</> : "Drag a file here, or"}</p>
          <input ref={input} type="file" accept=".pdf,.docx" className="sr-only" id="file" onChange={(e) => pick(e.target.files[0])} />
          <label htmlFor="file" className="btn-ghost mt-3 cursor-pointer">Choose file</label>
        </div>
        <div className="mt-4 space-y-3">
          <Alert tone="error" onClose={() => setError("")}>{error}</Alert>
          <Alert tone="success" onClose={() => setMessage("")}>{message}</Alert>
          {busy && (
            <div aria-live="polite">
              <div className="h-2 overflow-hidden rounded-full bg-desk"><div className="h-full rounded-full bg-margin transition-all duration-300" style={{ width: `${progress}%` }} /></div>
              <p className="text-xs text-slate2 mt-1">{progress < 100 ? `Uploading… ${progress}%` : "Analysing resume (NLP extraction)…"}</p>
            </div>
          )}
          <button className="btn-primary" disabled={!file || busy} onClick={submit}>{busy ? "Working…" : "Upload and analyse"}</button>
        </div>
      </Section>

      <Section title="Your resumes">
        {loading ? <Spinner /> : listError ? <Alert tone="error">{listError}</Alert> : !resumes.length ? (
          <EmptyState title="No resumes yet">Upload your first resume above.</EmptyState>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead><tr><th>Resume</th><th>Candidate</th><th>Skills</th><th>Quality</th><th>Uploaded</th><th><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>
                {resumes.map((r) => (
                  <tr key={r.id} className="border-b border-rule last:border-0">
                    <td><Link className="font-medium text-margin hover:underline" to={`/resume/${r.id}`}>{r.original_filename}</Link></td>
                    <td>{r.candidate_name || "—"}</td><td>{r.skill_count}</td><td>{Math.round(r.quality_score)}</td><td>{date(r.created_at)}</td>
                    <td className="text-right"><div className="flex justify-end gap-2"><Link className="btn-ghost min-h-8 px-3 py-1" to={`/resume/${r.id}`}>View</Link><Link className="btn-ghost min-h-8 px-3 py-1" to={`/job-analysis?resume=${r.id}`}>Analyze</Link><button className="btn-danger min-h-8 py-1" onClick={() => remove(r.id)}>Delete</button></div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  );
}

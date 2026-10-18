import { Link } from "react-router-dom";
import Alert from "../components/Alert";
import { HistoryChart } from "../components/Charts";
import EmptyState from "../components/EmptyState";
import Section from "../components/Section";
import Spinner from "../components/Spinner";
import { useAsync } from "../hooks/useAsync";
import { matchApi } from "../services/api";
import { sim } from "../utils/format";
import PageHeader from "../components/PageHeader";

export default function History() {
  const { data, loading, error } = useAsync(() => matchApi.list(), []);
  if (loading) return <Spinner />;
  if (error) return <Alert tone="error">{error}</Alert>;
  return (
    <div className="space-y-6">
      <PageHeader eyebrow="History" title="Analysis history">
        Review your previous resume and job comparisons.
      </PageHeader>
      {!data.length ? <EmptyState title="No analyses yet" action={<Link className="btn-primary" to="/job-analysis">Run your first match</Link>}>Each match you run is saved here.</EmptyState> : null}
      {data.length > 1 && <Section title="Scores over time"><HistoryChart history={[...data].reverse().map((a) => ({ ...a }))} /></Section>}
      {data.length > 0 && <Section title="All analyses">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead><tr><th>Date</th><th>Job</th><th>Resume</th><th>Match</th><th>Similarity</th><th>Quality</th><th><span className="sr-only">Action</span></th></tr></thead>
            <tbody>
              {data.map((a) => (
                <tr key={a.id}>
                  <td className="whitespace-nowrap">{new Date(a.created_at).toLocaleString()}</td><td className="font-medium">{a.job_title}</td><td>{a.resume_name}</td>
                  <td className="font-medium">{a.overall_score.toFixed(1)}</td><td>{sim(a.semantic_similarity)}</td><td>{Math.round(a.quality_score)}</td>
                  <td><Link className="font-medium text-margin hover:underline" to={`/match/${a.id}`}>Open</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>}
    </div>
  );
}

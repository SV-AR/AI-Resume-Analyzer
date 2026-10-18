import Section from "../components/Section";
import { useAsync } from "../hooks/useAsync";
import { useAuth } from "../hooks/useAuth";
import { dashboardApi } from "../services/api";
import { date } from "../utils/format";
import PageHeader from "../components/PageHeader";

export default function Profile() {
  const { user } = useAuth();
  const { data } = useAsync(() => dashboardApi.get(), []);
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader eyebrow="Account" title="Profile" />
      <Section title="Account">
        <dl className="text-sm space-y-2">
          <div className="flex gap-3"><dt className="w-28 text-slate2">Name</dt><dd>{user?.full_name?.trim() || "User"}</dd></div>
          <div className="flex gap-3"><dt className="w-28 text-slate2">Email</dt><dd>{user.email}</dd></div>
          <div className="flex gap-3"><dt className="w-28 text-slate2">Member since</dt><dd>{date(user.created_at)}</dd></div>
        </dl>
      </Section>
      {data && (
        <Section title="Your activity">
          <div className="grid gap-4 sm:grid-cols-3">
            <p className="text-sm"><strong className="block text-2xl">{data.counts.resumes}</strong><span className="text-slate2">Resumes</span></p>
            <p className="text-sm"><strong className="block text-2xl">{data.counts.jobs}</strong><span className="text-slate2">Job descriptions</span></p>
            <p className="text-sm"><strong className="block text-2xl">{data.counts.analyses}</strong><span className="text-slate2">Analyses</span></p>
          </div>
        </Section>
      )}
      <Section title="Responsible use">
        <p className="text-sm">Match scores measure similarity between texts. They do not predict hiring decisions. Review all extracted details and recommendations yourself, and only add skills or experience you actually have.</p>
      </Section>
    </div>
  );
}

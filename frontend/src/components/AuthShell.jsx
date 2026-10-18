export default function AuthShell({ title, subtitle, children }) {
  return (
    <div className="min-h-screen bg-desk md:grid md:grid-cols-2">
      <div className="hidden bg-ink px-10 py-14 text-white md:flex md:flex-col md:justify-center lg:px-16 xl:px-24">
        <div className="max-w-xl">
        <p className="mb-6 text-sm font-semibold text-blue-200">RESUME ANALYZER</p>
        <h1 className="text-4xl font-bold leading-tight lg:text-[44px]">Know how your resume reads against the job.</h1>
        <p className="mt-5 max-w-md text-[15px] leading-7 text-slate-300">
          Upload your resume, compare it against real job requirements, discover skill gaps, and get actionable recommendations.
        </p>
        <ul className="mt-9 space-y-4 text-sm text-slate-100">
          <li className="flex items-center gap-3"><span className="text-blue-300">✓</span>Resume analysis</li>
          <li className="flex items-center gap-3"><span className="text-blue-300">✓</span>Job matching</li>
          <li className="flex items-center gap-3"><span className="text-blue-300">✓</span>Skill gap detection</li>
        </ul>
        </div>
      </div>
      <div className="flex min-h-screen items-center justify-center p-5 sm:p-10">
        <div className="w-full max-w-[420px] rounded-xl border border-rule bg-white p-7 shadow-[0_2px_8px_rgba(15,23,42,0.04)] sm:p-10">
          <p className="mb-8 text-base font-semibold text-ink md:hidden">Resume Analyzer</p>
          <h2 className="text-2xl font-bold">{title}</h2>
          <p className="mb-7 mt-2 text-[15px] leading-6 text-slate2">{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  );
}

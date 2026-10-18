import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { BarChart3, BriefcaseBusiness, FileText, History, LogOut, Menu, UserRound, X } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

const LINKS = [
  ["/dashboard", "Dashboard", BarChart3],
  ["/upload", "Resumes", FileText],
  ["/job-analysis", "Job matching", BriefcaseBusiness],
  ["/history", "History", History],
  ["/profile", "Profile", UserRound],
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const displayName = user?.full_name?.trim() || "User";
  const initials = displayName.split(/\s+/).map((part) => part[0]).slice(0, 2).join("").toUpperCase();
  const link = ({ isActive }) =>
    `flex h-full items-center border-b-2 px-1 py-2 text-sm font-medium transition-colors ${isActive ? "border-margin text-ink" : "border-transparent text-slate2 hover:text-ink"}`;

  return (
    <header className="sticky top-0 z-20 border-b border-rule bg-white">
      <nav className="relative mx-auto flex h-[72px] max-w-7xl items-center justify-between gap-4 px-4 sm:px-6" aria-label="Main">
        <NavLink to="/dashboard" className="flex shrink-0 items-center gap-3 text-base font-semibold text-ink">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-ink text-sm font-bold text-white">R</span>
          Resume Analyzer
        </NavLink>
        <button className="btn-ghost h-10 w-10 p-0 lg:hidden" onClick={() => setOpen(!open)} aria-expanded={open} aria-label={open ? "Close navigation menu" : "Open navigation menu"}>
          {open ? <X size={19} /> : <Menu size={19} />}
        </button>
        <div className={`${open ? "flex" : "hidden"} absolute left-0 right-0 top-[72px] flex-col gap-3 border-b border-rule bg-white p-4 shadow-sm lg:static lg:flex lg:flex-1 lg:flex-row lg:items-center lg:justify-between lg:border-0 lg:p-0 lg:shadow-none`}>
          <div className="flex flex-col gap-1 lg:h-[72px] lg:flex-row lg:items-center lg:gap-4 xl:gap-7">
            {LINKS.map(([to, label]) => (
              <NavLink key={to} to={to} className={link} onClick={() => setOpen(false)}>{label}</NavLink>
            ))}
          </div>
          <div className="flex items-center gap-3 border-t border-rule pt-3 lg:border-0 lg:pt-0">
            <NavLink to="/profile" onClick={() => setOpen(false)} className="flex min-w-0 items-center gap-2 text-sm font-medium text-ink">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-semibold text-slate2">{initials || "U"}</span>
              <span className="max-w-32 truncate">{displayName}</span>
            </NavLink>
            <button className="btn-ghost min-h-9 px-3 py-1.5" onClick={() => { logout(); navigate("/login"); }}><LogOut size={15} aria-hidden="true" />Log out</button>
          </div>
        </div>
      </nav>
    </header>
  );
}

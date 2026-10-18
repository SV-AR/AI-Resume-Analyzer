import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";

export default function Layout() {
  return (
    <div className="min-h-screen bg-desk">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
        <Outlet />
      </main>
      <footer className="mx-auto max-w-7xl px-4 pb-8 text-xs leading-5 text-slate2 sm:px-6">
        Portfolio project. Analysis uses spaCy and sentence-transformers/all-MiniLM-L6-v2 and may contain extraction errors.
      </footer>
    </div>
  );
}

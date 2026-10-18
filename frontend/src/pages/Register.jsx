import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Alert from "../components/Alert";
import AuthShell from "../components/AuthShell";
import { authApi, errorMessage } from "../services/api";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await authApi.register({ ...form, email: form.email.trim() });
      navigate("/login", { state: { registered: true } });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell title="Create your account" subtitle="Your resumes and analyses are private to your account.">
      <form onSubmit={submit} className="space-y-4">
        <Alert tone="error">{error}</Alert>
        <div>
          <label className="label" htmlFor="name">Full name</label>
          <input id="name" required minLength={2} className="input" value={form.full_name} onChange={set("full_name")} autoComplete="name" />
        </div>
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input id="email" type="email" required className="input" value={form.email} onChange={set("email")} autoComplete="email" />
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input id="password" type="password" required minLength={8} className="input" value={form.password} onChange={set("password")} autoComplete="new-password" aria-describedby="pw-hint" />
          <p id="pw-hint" className="text-xs text-slate2 mt-1">At least 8 characters, with a letter and a number.</p>
        </div>
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Creating account…" : "Create account"}</button>
        <p className="text-sm text-slate2">Already registered? <Link className="text-margin underline" to="/login">Log in</Link></p>
      </form>
    </AuthShell>
  );
}

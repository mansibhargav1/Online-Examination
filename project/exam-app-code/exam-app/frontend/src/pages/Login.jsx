import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, auth } from "../lib/api";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      const data = await api.post("/auth/login", { email, password });
      auth.save(data);
      nav(data.role === "admin" ? "/admin" : "/dashboard", { replace: true });
    } catch (e2) {
      setErr(e2.message);
      setBusy(false);
    }
  };

  return (
    <div className="center-wrap">
      <div style={{ width: "100%", maxWidth: 400 }}>
        <Link to="/" className="brand" style={{ display: "block", marginBottom: 26 }}>
          Examination<span>.</span>
        </Link>

        <form className="card" onSubmit={submit}>
          <div className="card-head">
            <h2>Sign in</h2>
            <p className="sub" style={{ fontSize: 14, marginTop: 4 }}>
              Use the credentials your administrator issued.
            </p>
          </div>

          {err && <div className="alert alert-error">{err}</div>}

          <div className="field">
            <label htmlFor="e">Email</label>
            <input id="e" type="email" required autoFocus
                   value={email} onChange={(x) => setEmail(x.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="p">Password</label>
            <input id="p" type="password" required
                   value={password} onChange={(x) => setPassword(x.target.value)} />
          </div>

          <button className="btn btn-primary btn-wide" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="sub" style={{ textAlign: "center", marginTop: 18, fontSize: 14 }}>
          No account yet? <Link to="/apply">Apply for a seat</Link>
        </p>
      </div>
    </div>
  );
}

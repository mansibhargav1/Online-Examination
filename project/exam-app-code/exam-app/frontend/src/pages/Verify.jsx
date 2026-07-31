import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import { api, auth } from "../lib/api";

export default function Verify() {
  const { examId } = useParams();
  const [code, setCode] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();
  const user = auth.user();

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await api.post(`/exam/${examId}/verify`, {
        verification_code: code.trim(),
        declaration_accepted: accepted,
      });
      nav(`/exam/${examId}`, { replace: true });
    } catch (e2) {
      setErr(e2.message);
      setBusy(false);
    }
  };

  return (
    <Layout narrow>
      <p className="eyebrow">Step 3 of 4 · Verification</p>
      <h1 style={{ margin: "10px 0 8px" }}>Confirm it's you</h1>
      <p className="sub" style={{ marginBottom: 24 }}>
        Enter the six-digit code your administrator issued with your password.
      </p>

      <form className="card" onSubmit={submit}>
        {err && <div className="alert alert-error">{err}</div>}

        <div className="alert alert-info" style={{ marginBottom: 20 }}>
          Signing in as <b>{user?.full_name}</b>. If this isn't you, sign out now.
        </div>

        <div className="field">
          <label htmlFor="c">Verification code</label>
          <input id="c" className="code-input" required autoFocus inputMode="numeric"
                 maxLength={6} placeholder="000000" value={code}
                 onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} />
        </div>

        <div className="declare">
          <input id="dec" type="checkbox" checked={accepted}
                 onChange={(e) => setAccepted(e.target.checked)} />
          <label htmlFor="dec">
            I am the candidate named above. I am sitting this exam without help from any
            person, notes, or software, and I understand that the attempt is final and
            recorded against my name.
          </label>
        </div>

        <div className="alert alert-info">
          The clock starts on the next screen. You get one attempt.
        </div>

        <button className="btn btn-primary btn-wide" disabled={busy || !accepted || code.length !== 6}>
          {busy ? "Verifying…" : "Verify and begin"}
        </button>
      </form>

      <p style={{ textAlign: "center", marginTop: 16 }}>
        <Link to="/dashboard" className="sub" style={{ fontSize: 14 }}>Back to my exams</Link>
      </p>
    </Layout>
  );
}

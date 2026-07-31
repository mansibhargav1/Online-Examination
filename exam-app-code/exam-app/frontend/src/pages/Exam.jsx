import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../lib/api";

const KEYS = ["A", "B", "C", "D", "E", "F"];

function mmss(s) {
  const m = Math.floor(Math.max(0, s) / 60);
  const r = Math.max(0, s) % 60;
  return `${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
}

export default function Exam() {
  const { examId } = useParams();
  const nav = useNavigate();

  const [q, setQ] = useState(null);
  const [picked, setPicked] = useState(null);
  const [left, setLeft] = useState(0);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  // Guards against double-submits from a timeout racing a click.
  const sending = useRef(false);

  const load = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const data = await api.get(`/exam/${examId}/question`);
      setQ(data);
      setLeft(data.seconds_remaining);
      setPicked(null);
      sending.current = false;
    } catch (e) {
      // 409 means every question is done.
      if (e.status === 409) return nav(`/result/${examId}`, { replace: true });
      if (e.status === 400 || e.status === 403) {
        setErr(e.message);
        setTimeout(() => nav("/dashboard", { replace: true }), 2200);
        return;
      }
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }, [examId, nav]);

  useEffect(() => { load(); }, [load]);

  const send = useCallback(async (optionId) => {
    if (sending.current || !q) return;
    sending.current = true;
    setBusy(true);
    try {
      const res = await api.post(`/exam/${examId}/answer`, {
        question_id: q.question_id,
        selected_option_id: optionId,
      });
      if (res.finished) nav(`/result/${examId}`, { replace: true });
      else await load();
    } catch (e) {
      if (e.status === 400) await load();  // already locked — resync with server
      else { setErr(e.message); sending.current = false; }
    } finally {
      setBusy(false);
    }
  }, [examId, q, load, nav]);

  // Countdown. Purely cosmetic — the server is the source of truth.
  useEffect(() => {
    if (!q || loading) return;
    if (left <= 0) { send(null); return; }
    const t = setTimeout(() => setLeft((s) => s - 1), 1000);
    return () => clearTimeout(t);
  }, [left, q, loading, send]);

  // Re-sync the clock when the tab regains focus; the server kept counting.
  useEffect(() => {
    const onVis = () => { if (!document.hidden && !sending.current) load(); };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, [load]);

  // Keyboard: A–D to pick, Enter to lock in.
  useEffect(() => {
    const onKey = (e) => {
      if (!q || busy) return;
      const i = KEYS.indexOf(e.key.toUpperCase());
      if (i >= 0 && i < q.options.length) setPicked(q.options[i].id);
      if (e.key === "Enter" && picked) send(picked);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [q, picked, busy, send]);

  useEffect(() => {
    const warn = (e) => { e.preventDefault(); e.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, []);

  if (loading && !q) {
    return <div className="center-wrap"><div className="spinner" /></div>;
  }
  if (err && !q) {
    return (
      <div className="center-wrap">
        <div style={{ maxWidth: 440 }}>
          <div className="alert alert-error">{err}</div>
          <button className="btn btn-ghost btn-wide" onClick={() => nav("/dashboard")}>
            Back to my exams
          </button>
        </div>
      </div>
    );
  }
  if (!q) return null;

  const pct = Math.max(0, Math.min(100, (left / q.seconds_per_question) * 100));
  const tone = left <= 15 ? "crit" : left <= 45 ? "warn" : "ok";

  return (
    <div className="shell">
      <header className="exam-bar">
        <div>
          <span className="counter">QUESTION {q.index} / {q.total}</span>
        </div>
        <div className={`clock ${tone}`} role="timer" aria-live="off">{mmss(left)}</div>
      </header>

      {/* Signature: time as a physical, depleting rule */}
      <div className="depleting">
        <div className={`depleting-fill ${tone === "ok" ? "" : tone}`} style={{ width: `${pct}%` }} />
      </div>

      <main className="page page-narrow">
        {err && <div className="alert alert-error">{err}</div>}

        <p className="qtext">{q.text}</p>

        <div className="opts" role="radiogroup" aria-label="Answer options">
          {q.options.map((o, i) => (
            <button
              key={o.id}
              type="button"
              role="radio"
              aria-checked={picked === o.id}
              className={`opt${picked === o.id ? " sel" : ""}`}
              onClick={() => setPicked(o.id)}
              disabled={busy}
            >
              <span className="opt-key">{KEYS[i]}</span>
              <span>{o.text}</span>
            </button>
          ))}
        </div>

        <div className="btn-row" style={{ marginTop: 26, justifyContent: "space-between" }}>
          <button className="btn btn-ghost" onClick={() => send(null)} disabled={busy}>
            Skip — score 0
          </button>
          <button className="btn btn-primary" onClick={() => send(picked)} disabled={busy || !picked}>
            {busy ? "Saving…" : q.index === q.total ? "Lock in and finish" : "Lock in and continue"}
          </button>
        </div>

        <p className="sub" style={{ fontSize: 13, marginTop: 18, textAlign: "center" }}>
          Press A–{KEYS[q.options.length - 1]} to choose, Enter to lock in. Answers are final.
        </p>
      </main>
    </div>
  );
}

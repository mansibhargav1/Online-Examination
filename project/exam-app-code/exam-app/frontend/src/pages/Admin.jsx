import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import { api } from "../lib/api";

const BLANK_Q = { text: "", options: [{ text: "" }, { text: "" }, { text: "" }, { text: "" }], correct: 0 };

export default function Admin() {
  const [tab, setTab] = useState("applications");
  const [stats, setStats] = useState(null);
  const [apps, setApps] = useState([]);
  const [users, setUsers] = useState([]);
  const [exams, setExams] = useState([]);
  const [creds, setCreds] = useState(null);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const refresh = async () => {
    try {
      const [s, a, u, e] = await Promise.all([
        api.get("/admin/stats"),
        api.get("/admin/applications"),
        api.get("/admin/users"),
        api.get("/admin/exams"),
      ]);
      setStats(s); setApps(a); setUsers(u); setExams(e);
    } catch (e2) { setErr(e2.message); }
  };

  useEffect(() => { refresh(); }, []);

  const approve = async (id) => {
    setErr(""); setOk(""); setCreds(null);
    try {
      setCreds(await api.post(`/admin/applications/${id}/approve`, {}));
      refresh();
    } catch (e) { setErr(e.message); }
  };

  const reject = async (id) => {
    setErr(""); setOk("");
    const note = prompt("Reason for rejection (optional):") ?? "";
    try {
      await api.post(`/admin/applications/${id}/reject`, { admin_note: note });
      setOk("Application rejected.");
      refresh();
    } catch (e) { setErr(e.message); }
  };

  return (
    <Layout>
      <p className="eyebrow">Administrator</p>
      <h1 style={{ margin: "10px 0 22px" }}>Console</h1>

      {err && <div className="alert alert-error">{err}</div>}
      {ok && <div className="alert alert-ok">{ok}</div>}

      {creds && (
        <div className="alert alert-ok">
          <b>Account created — copy these now, the password won't be shown again.</b>
          <div className="creds">
            Email: {creds.email}<br />
            Password: {creds.password}<br />
            Verification code: {creds.verification_code}
          </div>

          {creds.email_sent ? (
            <p style={{ fontSize: 13, marginTop: 10 }}>
              Emailed to {creds.email}.
            </p>
          ) : (
            <p style={{ fontSize: 13, marginTop: 10, color: "var(--warn)" }}>
              <b>Not emailed</b> — {creds.email_detail || "email is off"}. Pass these on yourself.
            </p>
          )}

          <button className="btn btn-ghost btn-sm" style={{ marginTop: 10 }} onClick={() => setCreds(null)}>
            Dismiss
          </button>
        </div>
      )}

      {stats && (
        <div className="stats">
          <div className="stat"><div className="n">{stats.pending_applications}</div><div className="l">Pending applications</div></div>
          <div className="stat"><div className="n">{stats.candidates}</div><div className="l">Candidates</div></div>
          <div className="stat"><div className="n">{stats.exams}</div><div className="l">Exams</div></div>
          <div className="stat"><div className="n">{stats.attempts_in_progress}</div><div className="l">In progress</div></div>
          <div className="stat"><div className="n">{stats.attempts_submitted}</div><div className="l">Submitted</div></div>
        </div>
      )}

      <div className="tabs">
        {["applications", "candidates", "exams", "results", "new exam"].map((t) => (
          <button key={t} className={`tab${tab === t ? " on" : ""}`} onClick={() => setTab(t)}>
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === "applications" && <Applications apps={apps} approve={approve} reject={reject} />}
      {tab === "candidates" && <Candidates users={users} refresh={refresh} setErr={setErr} setCreds={setCreds} />}
      {tab === "exams" && <Exams exams={exams} refresh={refresh} setErr={setErr} setOk={setOk} />}
      {tab === "results" && <Results exams={exams} setErr={setErr} />}
      {tab === "new exam" && <NewExam refresh={refresh} setErr={setErr} setOk={setOk} setTab={setTab} />}
    </Layout>
  );
}

function Applications({ apps, approve, reject }) {
  if (!apps.length) return <div className="card"><div className="empty">No applications yet.</div></div>;
  return (
    <div className="card">
      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr><th>Name</th><th>Email</th><th>Phone</th><th>Qualification</th><th>ID proof</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {apps.map((a) => (
              <tr key={a.id}>
                <td>{a.full_name}</td>
                <td>{a.email}</td>
                <td>{a.phone}</td>
                <td>{a.qualification || "—"}</td>
                <td>{a.id_proof_type ? `${a.id_proof_type} ${a.id_proof_number || ""}` : "—"}</td>
                <td><span className={`pill pill-${a.status}`}>{a.status}</span></td>
                <td>
                  {a.status === "pending" && (
                    <div className="btn-row">
                      <button className="btn btn-primary btn-sm" onClick={() => approve(a.id)}>Approve</button>
                      <button className="btn btn-danger btn-sm" onClick={() => reject(a.id)}>Reject</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Candidates({ users, refresh, setErr, setCreds }) {
  const act = async (path, id) => {
    setErr("");
    try {
      const r = await api.post(`/admin/users/${id}/${path}`, {});
      if (r.password || r.verification_code) {
        setCreds({
          email: r.email,
          password: r.password || "(unchanged)",
          verification_code: r.verification_code || "(unchanged)",
          email_sent: r.email_sent ?? false,
          email_detail: r.email_detail ?? "email is off",
        });
      }
      refresh();
    } catch (e) { setErr(e.message); }
  };

  return (
    <div className="card">
      <div className="table-wrap">
        <table className="table">
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td><span className="pill pill-neutral">{u.role}</span></td>
                <td>
                  <span className={`pill pill-${u.is_active ? "approved" : "rejected"}`}>
                    {u.is_active ? "active" : "disabled"}
                  </span>
                </td>
                <td>
                  {u.role !== "admin" && (
                    <div className="btn-row">
                      <button className="btn btn-ghost btn-sm" onClick={() => act("reset-password", u.id)}>New password</button>
                      <button className="btn btn-ghost btn-sm" onClick={() => act("reset-verification", u.id)}>New code</button>
                      <button className="btn btn-danger btn-sm" onClick={() => act("toggle-active", u.id)}>
                        {u.is_active ? "Disable" : "Enable"}
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Exams({ exams, refresh, setErr, setOk }) {
  const toggle = async (id) => {
    setErr("");
    try { await api.post(`/admin/exams/${id}/toggle-active`, {}); refresh(); }
    catch (e) { setErr(e.message); }
  };
  const remove = async (id) => {
    setErr(""); setOk("");
    if (!confirm("Delete this exam and all its questions?")) return;
    try { await api.del(`/admin/exams/${id}`); setOk("Exam deleted."); refresh(); }
    catch (e) { setErr(e.message); }
  };

  if (!exams.length) return <div className="card"><div className="empty">No exams yet. Create one from the "New exam" tab.</div></div>;
  return (
    <div className="card">
      <div className="table-wrap">
        <table className="table">
          <thead><tr><th>Title</th><th>Questions</th><th>Per question</th><th>Marking</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {exams.map((e) => (
              <tr key={e.id}>
                <td>{e.title}</td>
                <td>{e.question_count}</td>
                <td>{Math.round(e.seconds_per_question / 60)} min</td>
                <td style={{ fontFamily: "var(--mono)", fontSize: 12 }}>
                  +{e.marks_correct} / {e.marks_wrong} / {e.marks_unattempted}
                </td>
                <td>
                  <span className={`pill pill-${e.is_active ? "approved" : "rejected"}`}>
                    {e.is_active ? "live" : "closed"}
                  </span>
                </td>
                <td>
                  <div className="btn-row">
                    <button className="btn btn-ghost btn-sm" onClick={() => toggle(e.id)}>
                      {e.is_active ? "Close" : "Open"}
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => remove(e.id)}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Results({ exams, setErr }) {
  const [examId, setExamId] = useState("");
  const [rows, setRows] = useState([]);

  const load = async (id) => {
    setExamId(id);
    setRows([]);
    if (!id) return;
    try { setRows(await api.get(`/admin/exams/${id}/results`)); }
    catch (e) { setErr(e.message); }
  };

  return (
    <div className="card">
      <div className="field" style={{ maxWidth: 380 }}>
        <label htmlFor="pick">Choose an exam</label>
        <select id="pick" value={examId} onChange={(e) => load(e.target.value)}>
          <option value="">Select…</option>
          {exams.map((e) => <option key={e.id} value={e.id}>{e.title}</option>)}
        </select>
      </div>

      {examId && (rows.length === 0 ? (
        <div className="empty">Nobody has submitted this exam yet.</div>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>#</th><th>Candidate</th><th>Email</th><th>Score</th><th>C</th><th>W</th><th>U</th><th>Submitted</th></tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.email}>
                  <td style={{ fontFamily: "var(--mono)", color: "var(--slate)" }}>{i + 1}</td>
                  <td>{r.user_name}</td>
                  <td>{r.email}</td>
                  <td style={{ fontFamily: "var(--mono)", fontWeight: 600 }}>{r.total_score}</td>
                  <td style={{ color: "var(--pass)" }}>{r.correct}</td>
                  <td style={{ color: "var(--fail)" }}>{r.wrong}</td>
                  <td style={{ color: "var(--slate)" }}>{r.unattempted}</td>
                  <td style={{ fontSize: 13, color: "var(--slate)" }}>
                    {r.finished_at ? new Date(r.finished_at).toLocaleString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}

function NewExam({ refresh, setErr, setOk, setTab }) {
  const [meta, setMeta] = useState({
    title: "", description: "", instructions: "",
    seconds_per_question: 120, marks_correct: 4, marks_wrong: -1, marks_unattempted: 0,
  });
  const [qs, setQs] = useState([structuredClone(BLANK_Q)]);
  const [busy, setBusy] = useState(false);

  const setM = (k) => (e) => {
    const v = e.target.type === "number" ? Number(e.target.value) : e.target.value;
    setMeta({ ...meta, [k]: v });
  };

  const setQText = (i, v) => { const c = [...qs]; c[i].text = v; setQs(c); };
  const setOText = (i, j, v) => { const c = [...qs]; c[i].options[j].text = v; setQs(c); };
  const setCorrect = (i, j) => { const c = [...qs]; c[i].correct = j; setQs(c); };
  const addQ = () => setQs([...qs, structuredClone(BLANK_Q)]);
  const delQ = (i) => setQs(qs.filter((_, x) => x !== i));

  const save = async () => {
    setErr(""); setOk("");
    setBusy(true);
    try {
      const payload = {
        ...meta,
        questions: qs.map((q) => ({
          text: q.text,
          options: q.options.map((o, j) => ({ text: o.text, is_correct: j === q.correct })),
        })),
      };
      await api.post("/admin/exams", payload);
      setOk("Exam created.");
      setMeta({ title: "", description: "", instructions: "", seconds_per_question: 120, marks_correct: 4, marks_wrong: -1, marks_unattempted: 0 });
      setQs([structuredClone(BLANK_Q)]);
      refresh();
      setTab("exams");
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  };

  const valid = meta.title.trim() && qs.every((q) => q.text.trim() && q.options.every((o) => o.text.trim()));

  return (
    <>
      <div className="card">
        <div className="card-head"><h2>Paper details</h2></div>
        <div className="field">
          <label htmlFor="t">Title</label>
          <input id="t" value={meta.title} onChange={setM("title")} placeholder="Computer Science Fundamentals" />
        </div>
        <div className="field">
          <label htmlFor="d">Description</label>
          <input id="d" value={meta.description} onChange={setM("description")} />
        </div>
        <div className="field">
          <label htmlFor="i">Instructions shown before the exam</label>
          <textarea id="i" rows={6} value={meta.instructions} onChange={setM("instructions")}
                    placeholder="One rule per line." />
        </div>
        <div className="grid2">
          <div className="field">
            <label htmlFor="s">Seconds per question</label>
            <input id="s" type="number" min={10} value={meta.seconds_per_question} onChange={setM("seconds_per_question")} />
          </div>
          <div className="field">
            <label htmlFor="mc">Marks for correct</label>
            <input id="mc" type="number" value={meta.marks_correct} onChange={setM("marks_correct")} />
          </div>
        </div>
        <div className="grid2">
          <div className="field">
            <label htmlFor="mw">Marks for wrong (negative)</label>
            <input id="mw" type="number" value={meta.marks_wrong} onChange={setM("marks_wrong")} />
          </div>
          <div className="field">
            <label htmlFor="mu">Marks for unattempted</label>
            <input id="mu" type="number" value={meta.marks_unattempted} onChange={setM("marks_unattempted")} />
          </div>
        </div>
      </div>

      {qs.map((q, i) => (
        <div className="card" key={i}>
          <div className="card-head" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontFamily: "var(--mono)", fontSize: 12, letterSpacing: "0.08em" }}>QUESTION {i + 1}</h3>
            {qs.length > 1 && (
              <button className="btn btn-danger btn-sm" onClick={() => delQ(i)}>Remove</button>
            )}
          </div>
          <div className="field">
            <label>Question text</label>
            <textarea rows={2} value={q.text} onChange={(e) => setQText(i, e.target.value)} />
          </div>
          <p className="sub" style={{ fontSize: 13, marginBottom: 8 }}>
            Select the radio button next to the correct option.
          </p>
          {q.options.map((o, j) => (
            <div key={j} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <input type="radio" name={`c${i}`} checked={q.correct === j}
                     onChange={() => setCorrect(i, j)} style={{ accentColor: "var(--seal)", width: 16, height: 16 }} />
              <input style={{
                flex: 1, padding: "9px 12px", fontSize: 14, fontFamily: "var(--sans)",
                border: "1px solid var(--line)", borderRadius: "var(--r)",
              }} value={o.text} placeholder={`Option ${["A", "B", "C", "D"][j]}`}
                     onChange={(e) => setOText(i, j, e.target.value)} />
            </div>
          ))}
        </div>
      ))}

      <div className="btn-row" style={{ marginTop: 16 }}>
        <button className="btn btn-ghost" onClick={addQ}>Add another question</button>
        <button className="btn btn-primary" onClick={save} disabled={busy || !valid}>
          {busy ? "Saving…" : "Create exam"}
        </button>
      </div>
      {!valid && <p className="sub" style={{ fontSize: 13, marginTop: 10 }}>Fill in the title, every question, and all four options.</p>}
    </>
  );
}

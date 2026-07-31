import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import { api, auth } from "../lib/api";

export default function Dashboard() {
  const [exams, setExams] = useState(null);
  const [err, setErr] = useState("");
  const user = auth.user();

  useEffect(() => {
    api.get("/exam/available").then(setExams).catch((e) => {
      setErr(e.message);
      setExams([]);
    });
  }, []);

  return (
    <Layout>
      <p className="eyebrow">Candidate</p>
      <h1 style={{ margin: "10px 0 6px" }}>{user?.full_name}</h1>
      <p className="sub" style={{ marginBottom: 28 }}>
        Exams assigned to you. Once you begin, the clock does not stop.
      </p>

      {err && <div className="alert alert-error">{err}</div>}

      <div className="card">
        {exams === null ? (
          <div className="spinner" />
        ) : exams.length === 0 ? (
          <div className="empty">No exams are open for you right now.</div>
        ) : (
          exams.map((ex) => (
            <div className="exam-row" key={ex.id}>
              <div>
                <h3>{ex.title}</h3>
                {ex.description && (
                  <p className="sub" style={{ fontSize: 14, margin: "4px 0", maxWidth: "60ch" }}>
                    {ex.description}
                  </p>
                )}
                <p className="meta">
                  {ex.question_count} questions · {Math.round(ex.seconds_per_question / 60)} min each ·
                  {" "}+{ex.marks_correct} / {ex.marks_wrong} / {ex.marks_unattempted}
                </p>
              </div>
              <div>
                {ex.attempt_status === "submitted" ? (
                  <Link to={`/result/${ex.id}`} className="btn btn-ghost btn-sm">View result</Link>
                ) : ex.attempt_status === "in_progress" ? (
                  <Link to={`/exam/${ex.id}`} className="btn btn-primary btn-sm">Resume</Link>
                ) : (
                  <Link to={`/instructions/${ex.id}`} className="btn btn-primary btn-sm">Start</Link>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </Layout>
  );
}

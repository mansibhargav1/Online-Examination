import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import { api } from "../lib/api";

export default function Instructions() {
  const { examId } = useParams();
  const [exam, setExam] = useState(null);
  const [err, setErr] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    api.get(`/exam/${examId}/instructions`).then(setExam).catch((e) => setErr(e.message));
  }, [examId]);

  if (err) {
    return (
      <Layout narrow>
        <div className="alert alert-error">{err}</div>
        <Link to="/dashboard" className="btn btn-ghost">Back to my exams</Link>
      </Layout>
    );
  }
  if (!exam) return <Layout narrow><div className="spinner" /></Layout>;

  return (
    <Layout narrow>
      <p className="eyebrow">Step 2 of 4 · Instructions</p>
      <h1 style={{ margin: "10px 0 8px" }}>{exam.title}</h1>
      {exam.description && <p className="sub" style={{ marginBottom: 24 }}>{exam.description}</p>}

      <div className="rules" style={{ marginBottom: 20 }}>
        <div className="rule">
          <div className="val pos">+{exam.marks_correct}</div>
          <div className="lbl">Correct</div>
        </div>
        <div className="rule">
          <div className="val neg">{exam.marks_wrong}</div>
          <div className="lbl">Wrong</div>
        </div>
        <div className="rule">
          <div className="val zero">{exam.marks_unattempted}</div>
          <div className="lbl">Blank or timed out</div>
        </div>
      </div>

      <div className="card">
        <div className="card-head"><h2>Read before you begin</h2></div>
        <div className="instr">
          {exam.instructions || "No specific instructions were provided for this paper."}
        </div>
      </div>

      <div className="btn-row" style={{ marginTop: 22 }}>
        <Link to="/dashboard" className="btn btn-ghost">Not yet</Link>
        <button className="btn btn-primary" onClick={() => nav(`/verify/${examId}`)}>
          I've read this — continue
        </button>
      </div>
    </Layout>
  );
}

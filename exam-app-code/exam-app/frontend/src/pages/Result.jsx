import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import { api } from "../lib/api";

export default function Result() {
  const { examId } = useParams();
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get(`/exam/${examId}/result`).then(setRes).catch((e) => setErr(e.message));
  }, [examId]);

  if (err) {
    return (
      <Layout narrow>
        <div className="alert alert-error">{err}</div>
        <Link to="/dashboard" className="btn btn-ghost">Back to my exams</Link>
      </Layout>
    );
  }
  if (!res) return <Layout narrow><div className="spinner" /></Layout>;

  const tone = res.total_score > 0 ? "var(--pass)" : res.total_score < 0 ? "var(--fail)" : "var(--slate)";

  return (
    <Layout narrow>
      <div className="score-head">
        <p className="eyebrow">Step 4 of 4 · Result</p>
        <h2 style={{ margin: "10px 0 18px" }}>{res.exam_title}</h2>
        <div className="score-val" style={{ color: tone }}>
          {res.total_score}
          <span className="score-max"> / {res.max_score}</span>
        </div>
        <p className="sub" style={{ marginTop: 12 }}>
          {res.user_name}
          {res.finished_at && ` · submitted ${new Date(res.finished_at).toLocaleString()}`}
        </p>
      </div>

      <div className="tally">
        <div className="tally-cell">
          <div className="n" style={{ color: "var(--pass)" }}>{res.correct}</div>
          <div className="l">Correct</div>
        </div>
        <div className="tally-cell">
          <div className="n" style={{ color: "var(--fail)" }}>{res.wrong}</div>
          <div className="l">Wrong</div>
        </div>
        <div className="tally-cell">
          <div className="n" style={{ color: "var(--slate)" }}>{res.unattempted}</div>
          <div className="l">Unattempted</div>
        </div>
      </div>

      <div className="card">
        <div className="card-head"><h2>Question by question</h2></div>
        {res.review.map((r, i) => (
          <div className="review-item" key={i}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
              <p className="review-q">{i + 1}. {r.question_text}</p>
              <span className={`mk ${r.marks_awarded > 0 ? "pos" : r.marks_awarded < 0 ? "neg" : "zero"}`}>
                {r.marks_awarded > 0 ? `+${r.marks_awarded}` : r.marks_awarded}
              </span>
            </div>
            <p className="review-line">
              <b>You answered:</b>{" "}
              {r.selected_option_text || <i>left blank</i>}
            </p>
            {!r.is_correct && (
              <p className="review-line"><b>Correct answer:</b> {r.correct_option_text}</p>
            )}
            {r.time_taken_seconds != null && (
              <p className="review-line">Took {r.time_taken_seconds}s</p>
            )}
          </div>
        ))}
      </div>

      <div className="btn-row" style={{ marginTop: 22 }}>
        <Link to="/dashboard" className="btn btn-ghost">Back to my exams</Link>
        <button className="btn btn-primary" onClick={() => window.print()}>Print result</button>
      </div>
    </Layout>
  );
}

import { Link } from "react-router-dom";
import Layout from "../components/Layout";

export default function Home() {
  return (
    <Layout>
      <section className="hero">
        <p className="eyebrow">Invigilated · Server-timed</p>
        <h1>Two minutes. One question. No going back.</h1>
        <p>
          Every question is timed by the server, not your browser. The clock keeps running
          if you refresh, switch tabs, or close the laptop. Answer, and the question locks.
        </p>
        <div className="btn-row">
          <Link to="/apply" className="btn btn-primary">Apply for a seat</Link>
          <Link to="/login" className="btn btn-ghost">I have credentials</Link>
        </div>
      </section>

      <p className="eyebrow" style={{ marginBottom: 12 }}>How marks are awarded</p>
      <div className="rules">
        <div className="rule">
          <div className="val pos">+4</div>
          <div className="lbl">Correct answer</div>
        </div>
        <div className="rule">
          <div className="val neg">&minus;1</div>
          <div className="lbl">Wrong answer</div>
        </div>
        <div className="rule">
          <div className="val zero">0</div>
          <div className="lbl">Left blank or timed out</div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 32 }}>
        <div className="card-head">
          <h2>Getting an account</h2>
        </div>
        <p className="sub" style={{ marginBottom: 18 }}>
          You cannot register yourself. Accounts are issued by an administrator only.
        </p>
        <ol style={{ paddingLeft: 18, fontSize: 15, lineHeight: 2, color: "var(--ink-soft)" }}>
          <li>Submit the application form with your details and ID proof.</li>
          <li>An administrator reviews it and creates your account.</li>
          <li>You receive a password and a six-digit verification code.</li>
          <li>Sign in, read the instructions, verify your identity, and begin.</li>
        </ol>
      </div>
    </Layout>
  );
}

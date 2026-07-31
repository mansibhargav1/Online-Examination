import { Link, useNavigate } from "react-router-dom";
import { auth } from "../lib/api";

export default function Layout({ children, narrow = false }) {
  const nav = useNavigate();
  const user = auth.user();

  const signOut = () => {
    auth.clear();
    nav("/");
  };

  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">Examination<span>.</span></Link>
        <nav>
          {user ? (
            <>
              <Link to={user.role === "admin" ? "/admin" : "/dashboard"}>
                {user.role === "admin" ? "Console" : "My exams"}
              </Link>
              <button className="linkbtn" onClick={signOut}>Sign out</button>
            </>
          ) : (
            <>
              <Link to="/apply">Apply</Link>
              <Link to="/login">Sign in</Link>
            </>
          )}
        </nav>
      </header>
      <main className={`page${narrow ? " page-narrow" : ""}`}>{children}</main>
      <footer className="foot">Invigilated online examination system</footer>
    </div>
  );
}

import { Navigate } from "react-router-dom";
import { auth } from "../lib/api";

export default function Protected({ role, children }) {
  const user = auth.user();
  if (!user || !auth.token()) return <Navigate to="/login" replace />;
  if (role && user.role !== role) {
    return <Navigate to={user.role === "admin" ? "/admin" : "/dashboard"} replace />;
  }
  return children;
}

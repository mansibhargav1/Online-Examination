import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Protected from "./components/Protected";
import Home from "./pages/Home";
import Apply from "./pages/Apply";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Instructions from "./pages/Instructions";
import Verify from "./pages/Verify";
import Exam from "./pages/Exam";
import Result from "./pages/Result";
import Admin from "./pages/Admin";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/apply" element={<Apply />} />
        <Route path="/login" element={<Login />} />

        <Route path="/dashboard" element={<Protected role="candidate"><Dashboard /></Protected>} />
        <Route path="/instructions/:examId" element={<Protected role="candidate"><Instructions /></Protected>} />
        <Route path="/verify/:examId" element={<Protected role="candidate"><Verify /></Protected>} />
        <Route path="/exam/:examId" element={<Protected role="candidate"><Exam /></Protected>} />
        <Route path="/result/:examId" element={<Protected role="candidate"><Result /></Protected>} />

        <Route path="/admin" element={<Protected role="admin"><Admin /></Protected>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

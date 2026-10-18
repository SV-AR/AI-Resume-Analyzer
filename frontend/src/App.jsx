import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import JobAnalysis from "./pages/JobAnalysis";
import Login from "./pages/Login";
import MatchResult from "./pages/MatchResult";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import ResumeDetail from "./pages/ResumeDetail";
import Upload from "./pages/Upload";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/resume/:id" element={<ResumeDetail />} />
        <Route path="/job-analysis" element={<JobAnalysis />} />
        <Route path="/match/:id" element={<MatchResult />} />
        <Route path="/history" element={<History />} />
        <Route path="/profile" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

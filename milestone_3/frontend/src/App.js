import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import Layout from "./components/Layout";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import Candidates from "./components/Candidates";
import CandidateDetail from "./components/CandidateDetail";
import Analysis from "./components/Analysis";
import Reports from "./components/Reports";
import Settings from "./components/Settings";

function RequireAuth({ children }) {
  const { auth } = useAuth();
  if (auth.loading) {
    return <div className="boot-screen">Loading TALASH...</div>;
  }
  if (!auth.authenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="candidates" element={<Candidates />} />
        <Route path="candidates/:candidateId" element={<CandidateDetail />} />
        <Route path="analysis" element={<Analysis />} />
        <Route path="analysis/:candidateId" element={<Analysis />} />
        <Route path="profile/:candidateId" element={<CandidateDetail />} />
        <Route path="reports" element={<Reports />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

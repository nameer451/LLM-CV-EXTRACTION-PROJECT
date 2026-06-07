import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiDelete } from "../api";
import { useAuth } from "../contexts/AuthContext";

export default function Candidates() {
  const { auth = {} } = useAuth();
  const [rows, setRows] = useState([]);
  const [query, setQuery] = useState("");
  const [band, setBand] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (auth.loading) return;

    setLoading(true);
    apiGet("/api/candidates")
      .then((payload) => {
        const allRows = payload.candidates || [];
        const visibleRows = auth.role === "admin"
          ? allRows
          : allRows.filter((row) => row.uploaded_by === auth.user);
        setRows(visibleRows);
      })
      .catch((err) => {
        alert(`Could not load candidates: ${err.message}`);
      })
      .finally(() => setLoading(false));
  }, [auth.role, auth.user, auth.loading]);

  const filtered = useMemo(() => {
    return rows.filter((row) => {
      const matchesQuery = `${row.name} ${row.email}`.toLowerCase().includes(query.toLowerCase());
      const matchesBand = band === "all" || row.ranking_band === band;
      return matchesQuery && matchesBand;
    });
  }, [rows, query, band]);

  const bands = ["all", ...Array.from(new Set(rows.map((row) => row.ranking_band)))];

  async function handleDelete(candidateId) {
    if (!confirm("Are you sure you want to delete this candidate?")) return;
    try {
      await apiDelete(`/api/candidate/${candidateId}`);
      setRows(rows.filter(row => row.id !== candidateId));
    } catch (err) {
      alert(`Failed to delete candidate: ${err.message}`);
    }
  }

  if (auth.loading || loading) {
    return <div className="boot-screen">Querying Database...</div>;
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Candidate-wise tabular output</p>
          <h2>Candidate Ledger</h2>
        </div>
        <div className="toolbar">
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search candidates" />
          <select value={band} onChange={(event) => setBand(event.target.value)}>
            {bands.map((item) => <option key={item} value={item}>{item === "all" ? "All bands" : item}</option>)}
          </select>
        </div>
      </header>

      <section className="panel">
        {filtered.length === 0 && (
          <div className="empty-state">
            <h3>No candidates yet</h3>
            <p>Upload a CV from the dashboard or run folder ingestion to populate this user's ledger.</p>
          </div>
        )}
        <table>
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Education</th>
              <th>Experience</th>
              <th>Research</th>
              <th>Missing</th>
              <th>Ranking</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((candidate) => (
              <tr key={candidate.id} className="clickable-row">
                <td>
                  <Link to={`/candidates/${candidate.id}`}>{candidate.name}</Link>
                  <small>{candidate.email || "Email missing"}</small>
                </td>
                <td>{candidate.education_count}</td>
                <td>{candidate.experience_count}</td>
                <td>{candidate.research_count}</td>
                <td>{candidate.missing_count}</td>
                <td>
                  <span className="score-pill">{candidate.ranking_score}</span>
                  <small>{candidate.ranking_band}</small>
                </td>
                <td className="action-cell">
                  <Link className="table-button" to={`/profile/${candidate.id}`}>Profile</Link>
                  <Link className="table-button" to={`/analysis/${candidate.id}`}>Analysis</Link>
                  <button className="table-button delete" onClick={() => handleDelete(candidate.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

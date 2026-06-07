import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, apiPost, apiUpload, apiDelete } from "../api";
import { useAuth } from "../contexts/AuthContext";

function StatCard({ label, value, tone }) {
  return (
    <div className={`stat-card ${tone || ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MiniBars({ labels = [], values = [] }) {
  const max = Math.max(1, ...values);
  return (
    <div className="mini-bars">
      {labels.map((label, index) => (
        <div className="mini-bar-row" key={label}>
          <span>{label}</span>
          <div className="bar-track">
            <div style={{ width: `${(values[index] / max) * 100}%` }} />
          </div>
          <b>{values[index]}</b>
        </div>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { auth = {} } = useAuth();
  const [stats, setStats] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [reports, setReports] = useState(null);
  const [uploadState, setUploadState] = useState("");
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    const [statsPayload, candidatesPayload, reportsPayload, uploadsPayload] = await Promise.all([
      apiGet("/api/dashboard-stats"),
      apiGet("/api/candidates"),
      apiGet("/api/reports-data"),
      apiGet("/api/uploads"),
    ]);

    const allCandidates = candidatesPayload.candidates || [];
    const visibleCandidates = auth.role === "admin"
      ? allCandidates
      : allCandidates.filter((candidate) => candidate.uploaded_by === auth.user);

    setCandidates(visibleCandidates);
    setStats(
      auth.role === "admin"
        ? statsPayload
        : {
            total_candidates: visibleCandidates.length,
            analysis_complete: visibleCandidates.filter((candidate) => candidate.status === "complete").length,
            flagged: visibleCandidates.filter((candidate) => candidate.is_flagged || candidate.flagged || candidate.status?.toLowerCase() === "review").length,
            average_ranking_score: visibleCandidates.length > 0
              ? Number(
                  (
                    visibleCandidates.reduce(
                      (sum, candidate) => sum + Number(candidate.ranking_score || 0),
                      0
                    ) / visibleCandidates.length
                  ).toFixed(1)
                )
              : 0,
          }
    );
    setReports(reportsPayload);
    setUploads(uploadsPayload.uploads || []);
    setLoading(false);
  }

  useEffect(() => {
    if (auth.loading) return;
    refresh().catch((err) => {
      setUploadState(err.message);
      setLoading(false);
    });
  }, [auth.role, auth.user, auth.loading]);

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploadState("Uploading and extracting CV...");
    try {
      const payload = await apiUpload("/api/upload", file);
      setUploadState(`Added ${payload.candidate.name} with score ${payload.candidate.ranking_score}`);
      await refresh();
    } catch (err) {
      setUploadState(err.message);
    } finally {
      event.target.value = "";
    }
  }

  async function ingestFolder() {
    setUploadState("Processing PDFs from milestone_3/uploads...");
    try {
      const payload = await apiPost("/api/ingest-folder");
      setUploadState(`Folder ingest complete: ${payload.added_candidates.length} candidate records added.`);
      await refresh();
    } catch (err) {
      setUploadState(err.message);
    }
  }

  async function deleteUpload(filename) {
    if (!confirm(`Delete ${filename}?`)) return;
    try {
      await apiDelete(`/api/upload/${filename}`);
      setUploadState(`Deleted ${filename}`);
      await refresh();
    } catch (err) {
      setUploadState(err.message);
    }
  }

  const topCandidates = useMemo(() => candidates.slice(0, 6), [candidates]);

  if (auth.loading || loading) {
    return <div className="boot-screen">Updating your dashboard...</div>;
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">End-to-end recruitment pipeline</p>
          <h2>Integrated Dashboard</h2>
        </div>
        <div className="header-actions">
          <label className="primary-button">
            Upload CV
            <input type="file" accept="application/pdf" hidden onChange={handleUpload} />
          </label>
          <button className="secondary-button" onClick={ingestFolder}>Ingest Folder</button>
        </div>
      </header>

      {uploadState && <div className="notice">{uploadState}</div>}

      <section className="stats-grid">
        <StatCard label="Candidates" value={stats?.total_candidates ?? "..."} />
        <StatCard label="Complete" value={stats?.analysis_complete ?? "..."} tone="green" />
        <StatCard label="Review" value={stats?.flagged ?? "..."} tone="amber" />
        <StatCard label="Average Score" value={stats?.average_ranking_score ?? "..."} tone="blue" />
      </section>

      <section className="panel">
        <h3>Uploaded CVs</h3>
        {uploads.length === 0 ? (
          <p>No uploads yet.</p>
        ) : (
          <ul className="uploads-list">
            {uploads.map((upload) => (
              <li key={upload.filename} className="upload-item">
                <span>{upload.filename} ({(upload.size / 1024).toFixed(1)} KB)</span>
                <button className="delete-button" onClick={() => deleteUpload(upload.filename)}>
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="two-column">
        <div className="panel">
          <div className="panel-header">
            <h3>Top Ranked Candidates</h3>
            <Link to="/candidates">View all</Link>
          </div>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Research</th>
                <th>Score</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {topCandidates.map((candidate) => (
                <tr key={candidate.id}>
                  <td>
                    <Link to={`/candidates/${candidate.id}`}>{candidate.name}</Link>
                    <small>{candidate.email || "No email"}</small>
                  </td>
                  <td>{candidate.research_count}</td>
                  <td><span className="score-pill">{candidate.ranking_score}</span></td>
                  <td><span className={`status ${candidate.status?.toLowerCase() === 'complete' ? 'complete' : 'review'}`}>{candidate.status || "In Progress"}</span></td>
                </tr>
              ))}
              {topCandidates.length === 0 && (
                <tr>
                  <td colSpan="4">
                    No candidates yet. Upload a CV or run folder ingestion to start this user's dashboard.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3>Score Distribution</h3>
          </div>
          <MiniBars labels={reports?.score_distribution?.labels} values={reports?.score_distribution?.values} />
        </div>
      </section>
    </div>
  );
}

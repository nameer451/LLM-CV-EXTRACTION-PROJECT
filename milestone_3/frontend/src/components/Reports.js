import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api";

function Bars({ title, labels = [], values = [] }) {
  const max = Math.max(1, ...values);
  return (
    <div className="panel chart-panel">
      <h3>{title}</h3>
      <div className="mini-bars tall">
        {labels.map((label, index) => (
          <div className="mini-bar-row" key={`${title}-${label}`}>
            <span>{label || "Unlabeled"}</span>
            <div className="bar-track"><div style={{ width: `${(values[index] / max) * 100}%` }} /></div>
            <b>{values[index]}</b>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Reports() {
  const [reports, setReports] = useState(null);
  const [tracking, setTracking] = useState([]);
  const [message, setMessage] = useState("");

  async function refresh() {
    const [reportPayload, trackingPayload] = await Promise.all([
      apiGet("/api/reports-data"),
      apiGet("/api/email-tracking"),
    ]);
    setReports(reportPayload);
    setTracking(trackingPayload.tracking_data || []);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function markResponded(trackingId) {
    setMessage("Updating response tracking...");
    try {
      await apiPost(`/api/email-response/${trackingId}`, { response_notes: "Candidate replied with requested information." });
      setMessage("Response recorded.");
      await refresh();
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Graphical dashboard and comparative views</p>
          <h2>Reports</h2>
        </div>
      </header>

      <section className="stats-grid">
        <div className="stat-card"><span>Average Ranking</span><strong>{reports?.average_score ?? "..."}</strong></div>
        <div className="stat-card amber"><span>Flagged Profiles</span><strong>{reports?.flagged_profiles ?? "..."}</strong></div>
        <div className="stat-card green"><span>Complete Profiles</span><strong>{reports?.complete_profiles ?? "..."}</strong></div>
      </section>

      <section className="chart-grid">
        <Bars title="Ranking Distribution" labels={reports?.score_distribution?.labels} values={reports?.score_distribution?.values} />
        <Bars title="Research Mix" labels={reports?.research_mix?.labels} values={reports?.research_mix?.values} />
        <Bars title="Top Skills" labels={reports?.top_skills?.labels} values={reports?.top_skills?.values} />
        <Bars title="Top Topics" labels={reports?.top_topics?.labels} values={reports?.top_topics?.values} />
      </section>

      <section className="panel">
        <h3>Comparative Ranking Table</h3>
        <table>
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Score</th>
              <th>Journals</th>
              <th>Conferences</th>
              <th>Skill Alignment</th>
            </tr>
          </thead>
          <tbody>
            {(reports?.ranked_candidates || []).map((row) => (
              <tr key={row.candidate_id}>
                <td>{row.candidate_name}</td>
                <td><span className="score-pill">{row.ranking_score}</span></td>
                <td>{row.journals}</td>
                <td>{row.conferences}</td>
                <td>{row.skill_alignment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Email Tracking and Candidate Responses</h3>
          {message && <span className="muted">{message}</span>}
        </div>
        <table>
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Email</th>
              <th>Delivery</th>
              <th>Opened</th>
              <th>Responded</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {tracking.map((row) => (
              <tr key={row.tracking_id}>
                <td>{row.candidate_name}</td>
                <td>{row.to_email}</td>
                <td>{row.delivery_status}</td>
                <td>{row.opened ? "Yes" : "No"}</td>
                <td>{row.responded ? "Yes" : "No"}</td>
                <td>
                  {!row.responded && <button className="ghost-button" onClick={() => markResponded(row.tracking_id)}>Mark response</button>}
                </td>
              </tr>
            ))}
            {tracking.length === 0 && (
              <tr><td colSpan="6">No follow-up emails have been queued yet.</td></tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}

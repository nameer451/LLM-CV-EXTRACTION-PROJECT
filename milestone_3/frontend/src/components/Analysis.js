import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { apiGet, apiPost } from "../api";
import { useAuth } from "../contexts/AuthContext";

function BulletList({ items }) {
  if (!items || items.length === 0) {
    return <p className="muted">No records available.</p>;
  }
  return (
    <ul className="plain-list">
      {items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
    </ul>
  );
}

function AnalysisTabs({ analysis, candidateId, candidate }) {
  const [tab, setTab] = useState("education");
  const [emailState, setEmailState] = useState("");

  async function sendEmail() {
    setEmailState("Queueing follow-up email...");
    try {
      const missing = await apiGet(`/api/missing-info-email/${candidateId}`);
      const response = await apiPost(`/api/send-missing-info-email/${candidateId}`, {
        to_email: missing.to_email || candidate.email,
        body: missing.draft_email,
      });
      setEmailState(`${response.status}: ${response.tracking_id}`);
    } catch (err) {
      setEmailState(err.message);
    }
  }

  const tabs = [
    ["education", "Educational Profile"],
    ["experience", "Professional Experience"],
    ["research", "Research Profile"],
    ["skills", "Skill Alignment"],
    ["missing", "Missing Information"],
    ["ranking", "Candidate Score"],
  ];

  return (
    <section className="panel">
      <div className="analysis-tabs">
        {tabs.map(([key, label]) => (
          <button key={key} className={tab === key ? "active" : ""} onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>

      {tab === "education" && (
        <div className="tab-panel">
          <h3>Educational Profile Analysis</h3>
          <p><b>Highest qualification:</b> {analysis.education_analysis?.highest_qualification}</p>
          <p><b>Institution quality:</b> {analysis.education_analysis?.institutional_quality}</p>
          <p><b>Grade coverage:</b> {analysis.education_analysis?.grade_coverage}</p>
          <BulletList items={analysis.education_analysis?.educational_gaps} />
        </div>
      )}

      {tab === "experience" && (
        <div className="tab-panel">
          <h3>Professional Experience and Employment History</h3>
          <p>{analysis.experience_analysis?.career_progression}</p>
          <p><b>Roles:</b> {analysis.experience_analysis?.employment_history_count}</p>
          <p><b>Estimated years:</b> {analysis.experience_analysis?.estimated_years}</p>
          <BulletList items={analysis.experience_analysis?.professional_gaps} />
          <BulletList items={analysis.experience_analysis?.timeline_overlaps} />
        </div>
      )}

      {tab === "research" && (
        <div className="tab-panel">
          <h3>Research Profile Analysis</h3>
          <p><b>Journals:</b> {analysis.research_profile?.journal_count}</p>
          <p><b>Conferences:</b> {analysis.research_profile?.conference_count}</p>
          <p><b>Average impact factor:</b> {analysis.research_profile?.average_impact_factor}</p>
          <p><b>Topic diversity:</b> {analysis.research_profile?.topic_variability?.diversity_index}</p>
          <p><b>Unique co-authors:</b> {analysis.research_profile?.coauthor_analysis?.unique_coauthors}</p>
          <BulletList items={(analysis.research_profile?.topic_variability?.top_topics || []).map(([topic, count]) => `${topic}: ${count}`)} />
        </div>
      )}

      {tab === "skills" && (
        <div className="tab-panel">
          <h3>Skill Alignment</h3>
          <p><b>Alignment ratio:</b> {analysis.skill_alignment?.alignment_ratio}</p>
          <p><b>Claimed skills:</b> {analysis.skill_alignment?.claimed_skills}</p>
          <BulletList items={analysis.skill_alignment?.matched_required_skills} />
          <p className="muted">Missing target skills</p>
          <BulletList items={analysis.skill_alignment?.missing_required_skills} />
        </div>
      )}

      {tab === "missing" && (
        <div className="tab-panel">
          <div className="panel-header">
            <h3>Personalized Missing-Information Email</h3>
            <button className="secondary-button" onClick={sendEmail}>Send or Queue Email</button>
          </div>
          <BulletList items={analysis.missing_information?.missing_fields} />
          <pre className="email-draft">{analysis.missing_information?.draft_email}</pre>
          {emailState && <div className="notice">{emailState}</div>}
        </div>
      )}

      {tab === "ranking" && (
        <div className="tab-panel">
          <h3>Quantifiable Candidate Score</h3>
          <p><b>Overall:</b> {analysis.ranking_analysis?.overall_score} — <span className="status review">{analysis.ranking_analysis?.band}</span></p>
          <div className="breakdown-list">
            {Object.entries(analysis.ranking_analysis?.breakdown || {}).map(([key, value]) => (
              <div key={key}>
                <span>{key.replaceAll("_", " ")}</span>
                <div className="bar-track">
                  {/* Logic fix: Safe width calculation */}
                  <div style={{ width: `${value.weight > 0 ? Math.min(100, (value.score / value.weight) * 100) : 0}%` }} />
                </div>
                <b>{value.score}/{value.weight}</b>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default function Analysis() {
  const { auth = {} } = useAuth();
  const { candidateId } = useParams();
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const selectedId = candidateId || candidates[0]?.id;

  useEffect(() => {
    if (auth.loading) return;

    setLoading(true);
    apiGet("/api/candidates")
      .then((payload) => {
        const allCandidates = payload.candidates || [];
        const visibleCandidates = auth.role === "admin"
          ? allCandidates
          : allCandidates.filter((candidate) => candidate.uploaded_by === auth.user);
        setCandidates(visibleCandidates);
      })
      .catch((err) => {
        console.error(err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [auth.role, auth.user, auth.loading]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    apiGet(`/api/candidate/${selectedId}`).then(setDetail);
  }, [selectedId]);

  const candidate = detail?.candidates || {};
  const analysis = detail?.analysis || {};
  const candidateOptions = useMemo(() => candidates.slice().sort((a, b) => a.name.localeCompare(b.name)), [candidates]);

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Detailed validation insights</p>
          <h2>Analysis Results</h2>
        </div>
        <div className="toolbar">
          <select
            value={selectedId || ""}
            onChange={(event) => navigate(`/analysis/${event.target.value}`)}
            disabled={candidateOptions.length === 0}
          >
            {candidateOptions.length === 0 && <option value="">No candidates available</option>}
            {candidateOptions.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </div>
      </header>

      {candidateOptions.length === 0 && (
        <section className="panel empty-state">
          <h3>No candidate analysis yet</h3>
          <p>This user has no candidates. Upload a CV from the dashboard or sign in as admin to view seeded demo candidates.</p>
        </section>
      )}

      {detail && (
        <>
          <section className="panel">
            <div className="detail-grid">
              <span>Name</span><b>{candidate.full_name}</b>
              <span>Email</span><b>{candidate.email || "Missing"}</b>
              <span>Phone</span><b>{candidate.phone_number || "Missing"}</b>
              <span>Profile</span><b><Link to={`/profile/${selectedId}`}>Open candidate profile</Link></b>
            </div>
          </section>
          <AnalysisTabs analysis={analysis} candidateId={selectedId} candidate={candidate} />
        </>
      )}
    </div>
  );
}

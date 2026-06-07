import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { apiGet, apiPost } from "../api";

function ListBlock({ items }) {
  if (!items || items.length === 0) return <p className="muted">No records available.</p>;
  return (
    <ul className="plain-list">
      {items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}
    </ul>
  );
}

export default function CandidateDetail() {
  const { candidateId } = useParams();
  const [payload, setPayload] = useState(null);
  const [emailState, setEmailState] = useState("");

  useEffect(() => {
    apiGet(`/api/candidate/${candidateId}`).then(setPayload);
  }, [candidateId]);

  const candidate = payload?.candidates || {};
  const analysis = payload?.analysis || {};
  const ranking = analysis.ranking_analysis || {};
  const rankingBreakdown = useMemo(() => Object.entries(ranking.breakdown || {}), [ranking]);

  async function sendEmail() {
    setEmailState("Recording follow-up email...");
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

  if (!payload) {
    return <div className="boot-screen">Loading candidate...</div>;
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Candidate assessment report</p>
          <h2>{candidate.full_name}</h2>
        </div>
        <div className="score-card">
          <span>Ranking Score</span>
          <strong>{ranking.overall_score}</strong>
          <em>{ranking.band}</em>
        </div>
      </header>

      <section className="two-column">
        <div className="panel">
          <h3>Candidate Summary</h3>
          <p>{analysis.candidate_summary?.quick_summary}</p>
          <div className="detail-grid">
            <span>Email</span><b>{candidate.email || "Missing"}</b>
            <span>Phone</span><b>{candidate.phone_number || "Missing"}</b>
            <span>Source</span><b>{payload.source_filename || "N/A"}</b>
          </div>
        </div>
        <div className="panel">
          <h3>Ranking Breakdown</h3>
          <div className="breakdown-list">
            {rankingBreakdown.map(([key, value]) => (
              <div key={key}>
                <span>{key.replaceAll("_", " ")}</span>
                <div className="bar-track"><div style={{ width: `${value.weight > 0 ? Math.min(100, (value.score / value.weight) * 100) : 0}%` }} /></div>
                <b>{value.score}/{value.weight}</b>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="analysis-grid">
        <div className="panel">
          <h3>Educational Profile</h3>
          <p><b>Highest:</b> {analysis.education_analysis?.highest_qualification}</p>
          <p><b>Institution quality:</b> {analysis.education_analysis?.institutional_quality}</p>
          <ListBlock items={analysis.education_analysis?.educational_gaps} />
        </div>
        <div className="panel">
          <h3>Research Profile</h3>
          <p><b>Journals:</b> {analysis.research_profile?.journal_count} | <b>Conferences:</b> {analysis.research_profile?.conference_count}</p>
          <p><b>Average impact:</b> {analysis.research_profile?.average_impact_factor}</p>
          <p><b>Unique co-authors:</b> {analysis.research_profile?.coauthor_analysis?.unique_coauthors}</p>
          <ListBlock items={analysis.research_profile?.sample_titles} />
        </div>
        <div className="panel">
          <h3>Topic and Co-author Analysis</h3>
          <p><b>Diversity index:</b> {analysis.research_profile?.topic_variability?.diversity_index}</p>
          <ListBlock items={(analysis.research_profile?.topic_variability?.top_topics || []).map(([topic, count]) => `${topic}: ${count}`)} />
        </div>
        <div className="panel">
          <h3>Skill Alignment</h3>
          <p><b>Alignment:</b> {analysis.skill_alignment?.alignment_ratio}</p>
          <ListBlock items={analysis.skill_alignment?.matched_required_skills} />
        </div>
        <div className="panel">
          <h3>Experience History</h3>
          <p>{analysis.experience_analysis?.career_progression}</p>
          <p><b>Estimated years:</b> {analysis.experience_analysis?.estimated_years}</p>
          <ListBlock items={analysis.experience_analysis?.professional_gaps} />
        </div>
        <div className="panel">
          <h3>Supervision, Patents, Books</h3>
          <p><b>Supervision:</b> {analysis.supervision_patents_books?.supervision_count}</p>
          <p><b>Patents:</b> {analysis.supervision_patents_books?.patent_count}</p>
          <p><b>Books:</b> {analysis.supervision_patents_books?.book_count}</p>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Missing Information Email</h3>
          <button className="secondary-button" onClick={sendEmail}>Send or Queue Follow-up</button>
        </div>
        <ListBlock items={analysis.missing_information?.missing_fields} />
        <pre className="email-draft">{analysis.missing_information?.draft_email}</pre>
        {emailState && <div className="notice">{emailState}</div>}
      </section>
    </div>
  );
}

"""
TALASH Milestone 3 analysis engine.

This module keeps the Milestone 2 class name for compatibility, but expands the
analysis to cover the complete Milestone 3 rubric and the extra-credit ranking
module.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from dateutil import parser as date_parser
except Exception:  # pragma: no cover - dateutil is listed in requirements
    date_parser = None


CURRENT_YEAR = datetime.now().year


def _clean(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if text.lower() in {"", "none", "null", "unknown", "n/a", "nan"}:
        return default
    return text


def _as_number(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else default


def _as_year(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value
    text = str(value)
    match = re.search(r"(19\d{2}|20\d{2})", text)
    return int(match.group(1)) if match else None


def _parse_date(value: Any, assume_current: bool = True) -> Optional[datetime]:
    text = _clean(value)
    if not text:
        return datetime.now() if assume_current else None
    if text.lower() in {"present", "current", "now", "ongoing"}:
        return datetime.now()
    if isinstance(value, datetime):
        return value
    if date_parser is not None:
        try:
            return date_parser.parse(text, fuzzy=True, default=datetime(1900, 1, 1))
        except Exception:
            pass
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y", "%m/%d/%Y", "%d/%m/%Y", "%b-%Y", "%B-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    year = _as_year(text)
    return datetime(year, 1, 1) if year else (datetime.now() if assume_current else None)


def _degree_rank(record: Dict[str, Any]) -> int:
    text = f"{record.get('degree_name', '')} {record.get('degree', '')}".lower()
    if any(token in text for token in ("postdoc", "post doctoral", "post-doctoral")):
        return 6
    if any(token in text for token in ("phd", "ph.d", "doctor", "doctoral", "doctorate")):
        return 5
    if any(token in text for token in ("ms", "m.sc", "msc", "master", "mphil", "m.eng", "meng", "mba")):
        return 4
    if any(token in text for token in ("bs", "b.sc", "bsc", "bachelor", "be", "beng", "bba")):
        return 3
    if any(token in text for token in ("hssc", "fsc", "intermediate", "a-level", "alevel")):
        return 2
    if any(token in text for token in ("ssc", "matric", "o-level", "olevel")):
        return 1
    return 0


def _extract_topics(outputs: Iterable[Dict[str, Any]]) -> List[str]:
    topics: List[str] = []
    stop_words = {
        "using", "based", "with", "from", "into", "through", "towards", "for",
        "and", "the", "a", "an", "study", "analysis", "system", "systems",
        "journal", "conference", "international", "novel", "approach",
    }
    for output in outputs:
        raw_topics = output.get("research_topics") or []
        if isinstance(raw_topics, list) and raw_topics:
            # Use multi-word phrases as-is from Gemini extraction
            topics.extend(_clean(topic).lower() for topic in raw_topics if _clean(topic))
        else:
            # Only fall back to title word extraction when no explicit topics provided
            title = _clean(output.get("title")).lower()
            words = re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", title)
            topics.extend(word.strip("-") for word in words if word not in stop_words)

    return [topic for topic in topics if topic]


def _authors(output: Dict[str, Any]) -> List[str]:
    text = _clean(output.get("author_names") or output.get("authors"))
    if not text:
        return []
    parts = re.split(r",|;|\band\b", text)
    return [re.sub(r"\s+", " ", part).strip() for part in parts if part.strip()]


class CandidateRanking:
    """Quantifiable 100-point ranking model for extra credit."""

    WEIGHTS = {
        "education": 20,
        "research": 25,
        "topic_and_collaboration": 10,
        "supervision_books_patents": 10,
        "experience": 15,
        "skill_alignment": 10,
        "completeness": 10,
    }

    def __init__(self, candidate_data: Dict[str, Any], analysis: Optional[Dict[str, Any]] = None):
        self.data = candidate_data
        self.analysis = analysis or {}

    def _education_score(self) -> Tuple[float, List[str]]:
        education = self.data.get("education", [])
        if not education:
            return 0, ["No education records found"]

        highest_rank = max((_degree_rank(record) for record in education), default=0)
        base_by_rank = {6: 20, 5: 19, 4: 15, 3: 10, 2: 4, 1: 2, 0: 1}
        score = base_by_rank.get(highest_rank, 0)

        grades = [_as_number(record.get("grade_value"), -1) for record in education]
        strong_grades = [grade for grade in grades if 3.5 <= grade <= 4.0 or grade >= 80]
        if strong_grades:
            score += 1

        return min(self.WEIGHTS["education"], score), [f"Highest degree rank {highest_rank}"]

    def _research_score(self) -> Tuple[float, List[str]]:
        outputs = self.data.get("research_outputs", [])
        journals = [item for item in outputs if _clean(item.get("output_type")).lower() == "journal"]
        conferences = [item for item in outputs if _clean(item.get("output_type")).lower() == "conference"]
        impact_sum = sum(_as_number(item.get("impact_factor"), 0) for item in outputs)
        recent = sum(1 for item in outputs if (_as_year(item.get("publication_year")) or 0) >= CURRENT_YEAR - 5)

        score = min(10, len(journals) * 1.4) + min(6, len(conferences) * 1.0)
        score += min(5, impact_sum / 6)
        score += min(4, recent * 0.8)
        reasons = [f"{len(journals)} journals", f"{len(conferences)} conferences", f"{recent} recent outputs"]
        return min(self.WEIGHTS["research"], score), reasons

    def _topic_collaboration_score(self) -> Tuple[float, List[str]]:
        outputs = self.data.get("research_outputs", [])
        topics = _extract_topics(outputs)
        topic_count = len(set(topics))
        coauthors = Counter()
        for output in outputs:
            coauthors.update(_authors(output))

        score = min(5, topic_count * 0.35) + min(5, len(coauthors) * 0.18)
        return min(self.WEIGHTS["topic_and_collaboration"], score), [
            f"{topic_count} distinct topic signals",
            f"{len(coauthors)} unique co-authors",
        ]

    def _supervision_books_patents_score(self) -> Tuple[float, List[str]]:
        outputs = self.data.get("research_outputs", [])
        supervision = self.data.get("supervision", [])
        patents = [item for item in outputs if _clean(item.get("output_type")).lower() == "patent"]
        books = [item for item in outputs if _clean(item.get("output_type")).lower() == "book"]
        completed_supervision = [
            item for item in supervision
            if _clean(item.get("status")).lower() == "completed"
        ]

        score = min(4, len(completed_supervision) * 1.5 + max(0, len(supervision) - len(completed_supervision)) * 0.75)
        score += min(3, len(patents) * 1.5)
        score += min(3, len(books) * 1.5)
        return min(self.WEIGHTS["supervision_books_patents"], score), [
            f"{len(supervision)} supervision records",
            f"{len(patents)} patents",
            f"{len(books)} books",
        ]

    def _experience_score(self) -> Tuple[float, List[str]]:
        experience = self.data.get("experience", [])
        months = 0
        for record in experience:
            duration = _as_number(record.get("duration_months"), 0)
            if duration <= 0:
                start = _parse_date(record.get("start_date"), assume_current=False)
                end = _parse_date(record.get("end_date"), assume_current=True)
                if start and end and end >= start:
                    duration = max(0, (end.year - start.year) * 12 + (end.month - start.month))
            months += duration

        academic_titles = sum(
            1 for record in experience
            if re.search(r"professor|lecturer|research|faculty|postdoc", _clean(record.get("job_title")), re.I)
        )
        years = months / 12
        score = min(11, years * 1.2) + min(4, academic_titles * 0.8)
        return min(self.WEIGHTS["experience"], score), [f"{years:.1f} estimated years", f"{academic_titles} academic/research roles"]

    def _skill_score(self) -> Tuple[float, List[str]]:
        alignment = self.analysis.get("skill_alignment", {})
        if isinstance(alignment, dict):
            ratio_text = _clean(alignment.get("alignment_ratio"), "0").replace("%", "")
            ratio = _as_number(ratio_text, 0)
            claimed = _as_number(alignment.get("claimed_skills"), 0)
            score = min(10, ratio / 10 + min(2, claimed * 0.2))
            return score, [f"{ratio:.1f}% evidence alignment"]
        skills = self.data.get("skills", [])
        return min(10, len(skills) * 1.2), [f"{len(skills)} listed skills"]

    def _completeness_score(self) -> Tuple[float, List[str]]:
        missing = self.analysis.get("missing_information", {})
        missing_count = len(missing.get("missing_fields", [])) if isinstance(missing, dict) else 0
        score = max(0, self.WEIGHTS["completeness"] - missing_count * 1.5)
        return score, [f"{missing_count} missing-information flags"]

    def score(self) -> Dict[str, Any]:
        components = {
            "education": self._education_score(),
            "research": self._research_score(),
            "topic_and_collaboration": self._topic_collaboration_score(),
            "supervision_books_patents": self._supervision_books_patents_score(),
            "experience": self._experience_score(),
            "skill_alignment": self._skill_score(),
            "completeness": self._completeness_score(),
        }
        breakdown = {
            name: {
                "score": round(value, 2),
                "weight": self.WEIGHTS[name],
                "reasons": reasons,
            }
            for name, (value, reasons) in components.items()
        }
        total = round(sum(item["score"] for item in breakdown.values()), 2)
        if total >= 85:
            band = "Highly Recommended"
        elif total >= 70:
            band = "Recommended"
        elif total >= 55:
            band = "Review"
        else:
            band = "Needs More Evidence"
        return {
            "overall_score": min(100, total),
            "band": band,
            "breakdown": breakdown,
            "model": "TALASH weighted academic hiring score v3",
        }


class Milestone2Analysis:
    """Compatibility class expanded for Milestone 3."""

    def __init__(self, candidate_data: Dict[str, Any]):
        self.data = candidate_data
        self.analysis_summary: Dict[str, Any] = {}

    def run_all_analyses(self) -> Dict[str, Any]:
        self.analyze_educational_profile()
        self.analyze_professional_experience()
        self.analyze_skill_alignment()
        self.analyze_research_profile()
        self.analyze_supervision_patents_books()
        self.detect_missing_information()
        self.generate_initial_candidate_summary()
        self.analysis_summary["ranking_analysis"] = CandidateRanking(self.data, self.analysis_summary).score()
        return self.analysis_summary

    def analyze_educational_profile(self) -> None:
        education = list(self.data.get("education", []))
        if not education:
            self.analysis_summary["education_analysis"] = {
                "status": "No education data found.",
                "educational_gaps": ["Education records are missing."],
                "institutional_quality": "0 out of 0 degrees are from ranked institutions.",
                "highest_qualification": "N/A",
                "grade_coverage": "0%",
            }
            return

        education_sorted = sorted(education, key=lambda record: (_as_year(record.get("passing_year")) is None, _as_year(record.get("passing_year")) or 0))
        experience = list(self.data.get("experience", []))
        gaps = []
        for previous, current in zip(education_sorted, education_sorted[1:]):
            previous_year = _as_year(previous.get("passing_year"))
            current_year = _as_year(current.get("passing_year"))
            if previous_year and current_year and current_year - previous_year > 3:
                # Don't flag gap if work experience covers the period (candidate was working)
                gap_covered = False
                for exp in experience:
                    exp_start = _as_year(exp.get("start_date"))
                    exp_end_raw = _clean(exp.get("end_date", ""))
                    exp_end = CURRENT_YEAR if exp_end_raw.lower() in {"present", "current", "now"} else _as_year(exp.get("end_date"))
                    if exp_start and exp_end and exp_start <= previous_year and exp_end >= previous_year:
                        gap_covered = True
                        break
                if not gap_covered:
                    gaps.append(
                        f"{current_year - previous_year}-year gap between {_clean(previous.get('degree_name'), 'previous degree')} and {_clean(current.get('degree_name'), 'current degree')}."
                    )

        ranked_names = {
            "national university of sciences and technology",
            "lahore university of management sciences",
            "ghulam ishaq khan institute",
            "national university of computer and emerging sciences",
            "comsats university",
            "quaid-i-azam university",
            "university of engineering and technology",
            # International ranked institutions
            "kingston university",
            "kingston university london",
            "university of warwick",
            "university of birmingham",
            "imperial college london",
            "university college london",
            "university of oxford",
            "university of cambridge",
            "mit",
            "stanford university",
            "harvard university",
            "carnegie mellon university",
            "georgia institute of technology",
            "university of toronto",
            "eth zurich",
        }
        ranked = [
            record for record in education
            if record.get("qs_ranking") or record.get("the_ranking") or _clean(record.get("institution_name")).lower() in ranked_names
        ]
        highest = max(education, key=lambda record: (_degree_rank(record), _as_year(record.get("passing_year")) or -1))
        grade_count = sum(1 for record in education if record.get("grade_value") not in (None, ""))

        self.analysis_summary["education_analysis"] = {
            "educational_gaps": gaps or ["No significant educational gaps detected."],
            "institutional_quality": f"{len(ranked)} out of {len(education)} degrees are from ranked institutions.",
            "highest_qualification": _clean(highest.get("degree_name"), "N/A"),
            "grade_coverage": f"{(grade_count / len(education) * 100):.1f}%",
            "records": education_sorted,
        }

    def analyze_professional_experience(self) -> None:
        experience = list(self.data.get("experience", []))
        if not experience:
            self.analysis_summary["experience_analysis"] = {
                "status": "No professional experience data found.",
                "timeline_overlaps": ["No experience timeline available."],
                "professional_gaps": ["No experience timeline available."],
                "career_progression": "No clear progression pattern identified.",
                "employment_history_count": 0,
                "estimated_years": 0,
            }
            return

        sorted_records = sorted(experience, key=lambda record: _parse_date(record.get("start_date"), assume_current=False) or datetime.max)
        overlaps = []
        gaps = []
        total_months = 0
        previous_end = None
        previous_title = ""

        for record in sorted_records:
            start = _parse_date(record.get("start_date"), assume_current=False)
            end = _parse_date(record.get("end_date"), assume_current=True)
            if start and end and end >= start:
                total_months += max(0, (end.year - start.year) * 12 + (end.month - start.month))
                if previous_end:
                    gap_days = (start - previous_end).days
                    if gap_days < -31:
                        overlaps.append(f"Overlap between {previous_title or 'previous role'} and {_clean(record.get('job_title'), 'current role')}.")
                    elif gap_days > 120:
                        gaps.append(f"Gap of about {round(gap_days / 30)} months before {_clean(record.get('job_title'), 'current role')}.")
                previous_end = max(previous_end, end) if previous_end else end
                previous_title = _clean(record.get("job_title"))

        titles = " ".join(_clean(record.get("job_title")).lower() for record in sorted_records)
        if "professor" in titles and "lecturer" in titles:
            progression = "Academic progression from lecturer/research roles toward professor track detected."
        elif re.search(r"senior|lead|head|principal|associate", titles):
            progression = "Progression into senior or leadership roles detected."
        elif len(sorted_records) > 1:
            progression = "Multiple role transitions detected."
        else:
            progression = "Single role history available."

        self.analysis_summary["experience_analysis"] = {
            "timeline_overlaps": overlaps or ["No job overlaps detected."],
            "professional_gaps": gaps or ["No significant professional gaps detected."],
            "career_progression": progression,
            "employment_history_count": len(sorted_records),
            "estimated_years": round(total_months / 12, 1),
            "records": sorted_records,
        }

    def analyze_skill_alignment(self, required_skills: Optional[List[str]] = None) -> None:
        skills = [
            _clean(skill.get("skill_name") if isinstance(skill, dict) else skill).lower()
            for skill in self.data.get("skills", [])
        ]
        skills = [skill for skill in skills if skill]
        required = [skill.lower() for skill in (required_skills or [
            "machine learning", "artificial intelligence", "signal processing",
            "research", "python", "data analysis", "teaching", "communication",
        ])]

        evidence_parts = []
        for record in self.data.get("experience", []):
            evidence_parts.extend([record.get("job_title"), record.get("job_description"), record.get("industry")])
        for output in self.data.get("research_outputs", []):
            evidence_parts.extend([output.get("title"), output.get("venue_name"), " ".join(output.get("research_topics", []) if isinstance(output.get("research_topics"), list) else [])])
        evidence = " ".join(_clean(part).lower() for part in evidence_parts)

        matched_required = []
        for required_skill in required:
            if any(required_skill in skill or skill in required_skill for skill in skills) or required_skill in evidence:
                matched_required.append(required_skill)

        evidence_backed = []
        for skill in skills:
            tokens = [skill, skill.replace("-", " ")]
            if any(token and token in evidence for token in tokens):
                evidence_backed.append(skill)

        self.analysis_summary["skill_alignment"] = {
            "claimed_skills": len(skills),
            "required_skills": required,
            "matched_required_skills": matched_required,
            "missing_required_skills": [skill for skill in required if skill not in matched_required],
            "aligned_skills_count": len(set(evidence_backed)),
            "aligned_skills_list": sorted(set(evidence_backed)),
            "alignment_ratio": f"{(len(matched_required) / len(required) * 100):.1f}%" if required else "0%",
        }

    def analyze_research_profile(self) -> None:
        outputs = list(self.data.get("research_outputs", []))
        journals = [item for item in outputs if _clean(item.get("output_type")).lower() == "journal"]
        conferences = [item for item in outputs if _clean(item.get("output_type")).lower() == "conference"]
        years = [_as_year(item.get("publication_year")) for item in outputs]
        years = [year for year in years if year]
        topics = _extract_topics(outputs)
        topic_counts = Counter(topics)
        author_counts = Counter()
        for item in outputs:
            author_counts.update(_authors(item))

        self.analysis_summary["research_profile"] = {
            "status": "Full research profile processed." if outputs else "No research outputs available.",
            "output_count": len(outputs),
            "journal_count": len(journals),
            "conference_count": len(conferences),
            "recent_publication_year": max(years) if years else None,
            "average_impact_factor": round(sum(_as_number(item.get("impact_factor"), 0) for item in outputs) / len(outputs), 2) if outputs else 0,
            "topic_variability": {
                "distinct_topics": len(topic_counts),
                "top_topics": topic_counts.most_common(8),
                "diversity_index": round(len(topic_counts) / max(1, len(outputs)), 2),
            },
            "coauthor_analysis": {
                "unique_coauthors": len(author_counts),
                "frequent_coauthors": author_counts.most_common(8),
                "average_authors_per_output": round(sum(len(_authors(item)) for item in outputs) / len(outputs), 2) if outputs else 0,
            },
            "sample_titles": [_clean(item.get("title"), "Untitled") for item in outputs[:5]],
        }

    def analyze_supervision_patents_books(self) -> None:
        outputs = list(self.data.get("research_outputs", []))
        supervision = list(self.data.get("supervision", []))
        patents = [item for item in outputs if _clean(item.get("output_type")).lower() == "patent"]
        books = [item for item in outputs if _clean(item.get("output_type")).lower() == "book"]

        self.analysis_summary["supervision_patents_books"] = {
            "supervision_count": len(supervision),
            "completed_supervision": sum(1 for item in supervision if _clean(item.get("status")).lower() == "completed"),
            "ongoing_supervision": sum(1 for item in supervision if _clean(item.get("status")).lower() == "ongoing"),
            "patent_count": len(patents),
            "book_count": len(books),
            "records": {
                "supervision": supervision,
                "patents": patents,
                "books": books,
            },
        }

    def detect_missing_information(self) -> None:
        missing_fields = []
        candidate = self.data.get("candidates", {})
        if not _clean(candidate.get("email")):
            missing_fields.append("Candidate email")
        if not _clean(candidate.get("phone_number")):
            missing_fields.append("Candidate phone number")
        if not self.data.get("education"):
            missing_fields.append("Education details")
        elif any(record.get("grade_value") in (None, "") for record in self.data.get("education", [])):
            missing_fields.append("Grade/CGPA for one or more degrees")
        if not self.data.get("experience"):
            missing_fields.append("Professional experience records")
        elif any(not _clean(record.get("job_description")) for record in self.data.get("experience", [])):
            missing_fields.append("Job description for one or more experience records")
        if self.data.get("research_outputs") and any(not _clean(item.get("doi")) for item in self.data.get("research_outputs", [])):
            missing_fields.append("DOI for one or more research outputs")

        candidate_name = _clean(candidate.get("full_name"), "Candidate")
        if missing_fields:
            email_body = (
                f"Dear {candidate_name},\n\n"
                "Thank you for your interest in the faculty recruitment process. "
                "During TALASH profile review, we noticed that the following information is missing or incomplete:\n\n"
                + "\n".join(f"- {field}" for field in missing_fields)
                + "\n\nPlease reply to this email with the missing details or upload an updated CV.\n\nBest regards,\nTALASH Recruitment Team"
            )
            status = "Missing information detected."
        else:
            email_body = "No missing information detected. No follow-up email is required."
            status = "No critical information missing."

        self.analysis_summary["missing_information"] = {
            "status": status,
            "missing_fields": missing_fields,
            "draft_email": email_body,
        }

    def generate_initial_candidate_summary(self) -> None:
        candidate = self.data.get("candidates", {})
        name = _clean(candidate.get("full_name"), "Candidate")
        education = self.analysis_summary.get("education_analysis", {})
        research = self.analysis_summary.get("research_profile", {})
        experience = self.analysis_summary.get("experience_analysis", {})
        missing = self.analysis_summary.get("missing_information", {})

        quick_summary = (
            f"{name} has {education.get('highest_qualification', 'N/A')} as the highest qualification, "
            f"{experience.get('estimated_years', 0)} estimated years of experience, "
            f"{research.get('journal_count', 0)} journal outputs, "
            f"{research.get('conference_count', 0)} conference outputs, and "
            f"{len(missing.get('missing_fields', [])) if isinstance(missing, dict) else 0} missing-information flags."
        )

        self.analysis_summary["candidate_summary"] = {
            "quick_summary": quick_summary,
            "education_entries": len(self.data.get("education", [])),
            "experience_entries": len(self.data.get("experience", [])),
            "skills_entries": len(self.data.get("skills", [])),
            "research_entries": len(self.data.get("research_outputs", [])),
            "missing_items": len(missing.get("missing_fields", [])) if isinstance(missing, dict) else 0,
        }

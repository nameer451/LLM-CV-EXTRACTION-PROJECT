from datetime import datetime

class Milestone2Analysis:
    def __init__(self, candidate_data):
        """
        Initializes the analysis module with data for a single candidate.
        :param candidate_data: A dictionary containing all data for one candidate 
                               (personal info, education, experience, etc.).
        """
        self.data = candidate_data
        self.analysis_summary = {}

    def run_all_analyses(self):
        """Runs all analysis modules and returns a consolidated summary."""
        self.analyze_educational_profile()
        self.analyze_professional_experience()
        self.analyze_skill_alignment()
        self.analyze_research_profile_partial()
        self.detect_missing_information()
        self.generate_initial_candidate_summary()
        return self.analysis_summary

    def analyze_educational_profile(self):
        """
        Analyzes the candidate's educational background for consistency, gaps, 
        and institutional quality.
        """
        education = list(self.data.get('education', []))
        if not education:
            self.analysis_summary['education_analysis'] = "No education data found."
            return

        def parse_year(record):
            try:
                return int(record.get('passing_year'))
            except (TypeError, ValueError):
                return None

        def degree_rank(name):
            text = str(name or '').lower()
            if any(token in text for token in ('phd', 'doctorate', 'doctoral')):
                return 5
            if any(token in text for token in ('ms', 'msc', 'master', 'mphil', 'mba')):
                return 4
            if any(token in text for token in ('bs', 'bsc', 'bachelor', 'bba', 'be', 'beng')):
                return 3
            if any(token in text for token in ('hssc', 'fsc', 'intermediate', 'a-level')):
                return 2
            if any(token in text for token in ('ssc', 'matric', 'o-level')):
                return 1
            return 0

        education_sorted = sorted(
            education,
            key=lambda record: (parse_year(record) is None, parse_year(record) or 0)
        )

        gaps = []
        for i in range(1, len(education_sorted)):
            current_year = parse_year(education_sorted[i])
            previous_year = parse_year(education_sorted[i - 1])
            if current_year is None or previous_year is None:
                continue

            gap = current_year - previous_year
            if gap > 2:
                gaps.append(
                    f"A {gap}-year gap found between "
                    f"{education_sorted[i - 1].get('degree_name', 'previous degree')} and "
                    f"{education_sorted[i].get('degree_name', 'current degree')}."
                )

        # Institutional Quality
        known_ranked_institutions = {
            'national university of sciences and technology',
            'lahore university of management sciences',
            'ghulam ishaq khan institute',
            'national university of computer and emerging sciences',
            'quaid-i-azam university',
            'comsats university',
        }

        ranked_institutions = [
            record for record in education_sorted
            if (
                record.get('qs_ranking') is not None
                or record.get('the_ranking') is not None
                or str(record.get('institution_name', '')).strip().lower() in known_ranked_institutions
            )
        ]

        reliable_records = [
            record for record in education_sorted
            if record.get('institution_name') or parse_year(record) is not None or record.get('grade_value') is not None
        ]

        if reliable_records:
            highest_record = max(
                reliable_records,
                key=lambda record: (degree_rank(record.get('degree_name')), parse_year(record) or -1),
                default=None
            )
        else:
            # Conservative fallback: avoid overstating qualification when extraction confidence is low.
            non_unknown = [r for r in education_sorted if degree_rank(r.get('degree_name')) > 0]
            highest_record = min(non_unknown, key=lambda record: degree_rank(record.get('degree_name')), default=None)
        
        summary = {
            "educational_gaps": gaps if gaps else ["No significant educational gaps detected."],
            "institutional_quality": f"{len(ranked_institutions)} out of {len(education_sorted)} "
                                     f"degrees are from ranked institutions.",
            "highest_qualification": highest_record.get('degree_name', 'N/A') if highest_record else "N/A"
        }
        self.analysis_summary['education_analysis'] = summary

    def analyze_professional_experience(self):
        """
        Analyzes professional experience for timeline consistency and career progression.
        """
        experience = list(self.data.get('experience', []))
        if not experience:
            self.analysis_summary['experience_analysis'] = "No professional experience data found."
            return

        def parse_date(value):
            if not value:
                return datetime.now()
            if isinstance(value, datetime):
                return value
            for fmt in ('%Y-%m-%d', '%Y-%m', '%Y'):
                try:
                    return datetime.strptime(str(value), fmt)
                except ValueError:
                    continue
            return datetime.now()

        experience_sorted = sorted(experience, key=lambda record: parse_date(record.get('start_date')))

        overlaps = []
        gaps = []
        for i in range(1, len(experience_sorted)):
            previous = experience_sorted[i - 1]
            current = experience_sorted[i]
            previous_end = parse_date(previous.get('end_date'))
            current_start = parse_date(current.get('start_date'))

            # Check for overlap
            if current_start < previous_end:
                overlaps.append(
                    f"Overlap detected between "
                    f"{previous.get('job_title', 'previous role')} and "
                    f"{current.get('job_title', 'current role')}."
                )
            # Check for gaps
            gap_days = (current_start - previous_end).days
            if gap_days > 90: # More than 3 months
                gaps.append(
                    f"A gap of ~{round(gap_days/30)} months found between "
                    f"{previous.get('job_title', 'previous role')} and "
                    f"{current.get('job_title', 'current role')}."
                )

        progression = "No clear progression pattern identified."
        titles = [str(record.get('job_title', '')).lower() for record in experience_sorted]
        if any("senior" in t for t in titles):
            progression = "Progression to senior role detected."
        elif len(titles) > 1:
            progression = "Role transitions detected across the timeline."

        summary = {
            "timeline_overlaps": overlaps if overlaps else ["No job overlaps detected."],
            "professional_gaps": gaps if gaps else ["No significant professional gaps detected."],
            "career_progression": progression,
            "employment_history_count": len(experience_sorted)
        }
        self.analysis_summary['experience_analysis'] = summary

    def analyze_research_profile_partial(self):
        """Partial research-profile processing required for milestone demo."""
        outputs = self.data.get('research_outputs', [])
        if not outputs:
            self.analysis_summary['research_profile'] = {
                "status": "No research outputs available.",
                "output_count": 0,
                "recent_publication_year": None
            }
            return

        years = [o.get('year') for o in outputs if o.get('year') is not None]
        self.analysis_summary['research_profile'] = {
            "status": "Partial research profile processed.",
            "output_count": len(outputs),
            "recent_publication_year": max(years) if years else None,
            "sample_titles": [o.get('title', 'Untitled') for o in outputs[:2]]
        }

    def analyze_skill_alignment(self):
        """
        Analyzes alignment between claimed skills and evidence from experience/publications.
        """
        skills = [str(skill.get('skill_name', '')).lower() for skill in self.data.get('skills', []) if skill.get('skill_name')]
        if not skills:
            self.analysis_summary['skill_alignment'] = "No skills data found."
            return

        evidence_text = ""
        for exp in self.data.get('experience', []):
            evidence_text += exp.get('job_title', '').lower() + " "
            evidence_text += exp.get('job_description', '').lower() + " "
            evidence_text += exp.get('industry', '').lower() + " "
        for pub in self.data.get('research_outputs', []):
            evidence_text += pub.get('title', '').lower() + " "
            evidence_text += pub.get('publication', '').lower() + " "

        skill_aliases = {
            'aws': ['cloud', 'infrastructure', 'amazon web services'],
            'docker': ['container', 'containers', 'orchestration'],
            'machine learning': ['machine learning', 'ml', 'predictive model', 'predictive models'],
            'research': ['research', 'publication', 'publications', 'paper', 'papers'],
            'system design': ['system design', 'architecture', 'architected', 'architectural'],
            'python': ['python', 'django', 'flask'],
            'sql': ['sql', 'database', 'databases'],
            'statistics': ['statistics', 'statistical', 'analytics', 'analysis'],
            'tableau': ['tableau', 'dashboard', 'dashboards'],
            'r': [' r ', 'r programming', 'statistics']
        }

        aligned_skills = []
        for skill in skills:
            aliases = skill_aliases.get(skill, [skill])
            if any(alias in evidence_text for alias in aliases):
                aligned_skills.append(skill)
        
        summary = {
            "claimed_skills": len(skills),
            "aligned_skills_count": len(aligned_skills),
            "alignment_ratio": f"{(len(aligned_skills) / len(skills) * 100):.2f}%" if skills else "0%",
            "aligned_skills_list": aligned_skills
        }
        self.analysis_summary['skill_alignment'] = summary

    def detect_missing_information(self):
        """
        Detects missing information in the candidate's profile and generates a draft email.
        """
        missing_fields = []
        candidate = self.data.get('candidates', {})
        if not candidate.get('email'):
            missing_fields.append("Candidate Email")
        if not candidate.get('phone_number'):
            missing_fields.append("Candidate Phone Number")
        
        education = list(self.data.get('education', []))
        if not education:
            missing_fields.append("Education details (degree/institution/year)")
        elif any(record.get('grade_value') in (None, '') for record in education):
            missing_fields.append("Grade/CGPA for one or more degrees")

        experience = list(self.data.get('experience', []))
        if not experience:
            missing_fields.append("Professional experience records")
        elif any(not record.get('job_description') for record in experience):
            missing_fields.append("Job description for one or more experience records")

        research_outputs = self.data.get('research_outputs', [])
        for output in research_outputs:
            if not output.get('doi'):
                missing_fields.append("Research DOI for one or more publications")
                break

        if not missing_fields:
            self.analysis_summary['missing_information'] = {"status": "No critical information missing."}
            return

        candidate_name = candidate.get('full_name', 'Candidate')
        email_body = f"Dear {candidate_name},\n\n" \
                     f"Thank you for your interest. We are reviewing your application and noticed " \
                     f"that the following information is missing or incomplete in your CV:\n\n"
        for field in missing_fields:
            email_body += f"- {field}\n"
        email_body += "\nCould you please provide the missing details or upload an updated CV at your earliest convenience?" \
                      "\n\nBest regards,\nHR Team"

        summary = {
            "status": "Missing information detected.",
            "missing_fields": missing_fields,
            "draft_email": email_body
        }
        self.analysis_summary['missing_information'] = summary

    def generate_initial_candidate_summary(self):
        """Generate initial candidate summary for recruiter quick view."""
        candidate = self.data.get('candidates', {})
        education_count = len(self.data.get('education', []))
        experience_count = len(self.data.get('experience', []))
        skills_count = len(self.data.get('skills', []))
        missing = self.analysis_summary.get('missing_information', {})
        missing_count = len(missing.get('missing_fields', [])) if isinstance(missing, dict) else 0

        summary_text = (
            f"{candidate.get('full_name', 'Candidate')} has {education_count} education entries, "
            f"{experience_count} experience roles, and {skills_count} listed skills. "
            f"Missing-information flags: {missing_count}."
        )

        self.analysis_summary['candidate_summary'] = {
            "quick_summary": summary_text,
            "education_entries": education_count,
            "experience_entries": experience_count,
            "skills_entries": skills_count,
            "missing_items": missing_count
        }

if __name__ == '__main__':
    # This is a placeholder for where you would load your candidate data
    # For a real run, you would loop through your candidates from the database
    # and run the analysis on each one.
    
    # Example of how to use the class:
    # candidate_json = load_candidate_from_db(candidate_id) 
    # analyzer = Milestone2Analysis(candidate_json)
    # analysis_results = analyzer.run_all_analyses()
    # print(analysis_results)
    pass

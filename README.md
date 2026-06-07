# TALASH: Talent Acquisition & Learning Automation for Smart Hiring

An intelligent CV parsing and candidate assessment system powered by Google Gemini.

**Course:** CS-417 Large Language Models — Spring 2026  
**University:** NUST Islamabad  
**Instructor:** Prof. Dr. Muhammad Moazam Fraz  
**Team:** Nameer Ahmed (454029), Rimsha Mahmood (455080), Muhammad Ahmad (461348)  
**Repository:** https://github.com/mahmadr10/Talash-LLM_Project

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Milestone 1 — Database & Extraction Foundation](#milestone-1--database--extraction-foundation)
4. [Milestone 2 — Analysis Pipeline & Intermediate Web App](#milestone-2--analysis-pipeline--intermediate-web-app)
5. [Milestone 3 — Full-Stack Application](#milestone-3--full-stack-application)
6. [Scoring & Ranking Model](#scoring--ranking-model)
7. [Setup & Installation](#setup--installation)
8. [API Reference](#api-reference)
9. [Configuration](#configuration)

---

## Project Overview

TALASH is a recruitment pipeline built for academic hiring workflows. It replaces manual CV review with an automated system that extracts structured data from PDF CVs, performs multi-dimensional candidate analysis, ranks candidates against each other, and drafts personalised follow-up emails for incomplete profiles.

The system handles multi-candidate PDFs where each candidate section is delimited by the phrase "Candidate for the post of", extracts structured JSON via Google Gemini, analyzes education and experience timelines, scores candidates on a 100-point weighted rubric, and presents everything through a React frontend backed by a Flask API.

---

## System Architecture

```
PDF Upload
  -> pdfplumber text extraction
  -> split on "Candidate for the post of" delimiter
  -> Google Gemini structured JSON extraction (with rule-based fallback)
  -> normalization (university names, durations, enums)
  -> candidate_database (in-memory, persisted to cv_extraction_results.json)
  -> Milestone2Analysis engine
  -> analysis_results.json cache
  -> Flask REST API
  -> React frontend
```

---

## Milestone 1 — Database & Extraction Foundation

Milestone 1 established the extraction pipeline and relational database schema.

**Deliverables:**
- PDF ingestion via pdfplumber
- Google Gemini prompt engineering for structured JSON output
- 9-table PostgreSQL schema on Supabase (Hub-and-Spoke model)
- JSONB extensibility, row-level security, indexed foreign keys

**Schema covers:** personal info, education, experience, skills, research outputs, supervision, certifications, awards, references.

**Running on Kaggle:**
1. Open the notebook in `milestone_1/`
2. Add secrets: `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
3. Upload CVs to `/kaggle/input/`
4. Run all cells

**Running locally:**
```bash
cd milestone_1
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
# create .env with GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
python main.py
```

---

## Milestone 2 — Analysis Pipeline & Intermediate Web App

Milestone 2 built the core analysis engine and an HTML/Flask intermediate web interface.

### CV Parsing and Structured Extraction

Implemented in `milestone_2/cv_batch_processor.py`.

- Scans an uploads folder for PDF files
- Extracts text via pdfplumber
- Splits multi-candidate PDFs on the "Candidate for the post of" delimiter (max 50 candidates per PDF)
- Sends each chunk to Google Gemini with a structured schema prompt
- Falls back to rule-based extraction if Gemini is unavailable
- Runs a second dedicated Gemini call for publications if fewer than 5 are detected
- Saves all results to `outputs/cv_extraction_results.json`

```bash
python cv_batch_processor.py
```

**Fields extracted:** full name, email, phone, DOB, education (degree, institution, grade, year, QS/THE ranking), experience (title, organisation, dates, duration), skills (with category), research outputs (title, venue, type, impact factor, topics, co-authors), supervision, patents, books, certifications, awards, references.

### Educational Profile Analysis

Implemented in `milestone_2/milestone2.py` — `analyze_educational_profile()`.

- Validates degree progression (SSC → HSSC → BS → MS → PhD)
- Flags educational gaps greater than 3 years
- Assesses institutional quality using a ranked list of Pakistani and international universities
- Identifies highest qualification
- Detects missing grades/CGPA

### Professional Experience Analysis

Implemented in `milestone_2/milestone2.py` — `analyze_professional_experience()`.

- Detects overlapping employment periods (tolerance: 31 days)
- Flags gaps greater than 120 days
- Tracks career progression (junior to senior role detection)
- Calculates total estimated experience in years

### Missing Information Detection and Email Drafting

Implemented in `milestone_2/milestone2.py` — `detect_missing_information()`.

Detects: missing email, missing phone, missing grades, missing job descriptions, missing DOIs on research outputs.

Generates a personalised draft email listing the specific missing fields, addressed to the candidate by name, ready for SMTP delivery.

### Intermediate Web Application

Flask backend with HTML/CSS frontend and Chart.js visualisations.

Pages: Login, Dashboard, Candidates, Analysis Results, Reports, Profile, Settings.

```bash
# Backend
python app.py
# Open http://localhost:5000
```

---

## Milestone 3 — Full-Stack Application

Milestone 3 delivers the complete production-ready system with a React frontend, session-based authentication, email tracking, and the extra-credit quantifiable ranking module.

### Demo Login

| Username | Password | Access |
|----------|----------|--------|
| admin | admin123 | All candidates including seeded 43-candidate demo dataset |
| recruiter | recruiter123 | Only candidates uploaded during the session |
| user | user123 | Only candidates uploaded during the session |

Passwords can be overridden via environment variables: `TALASH_ADMIN_PASSWORD`, `TALASH_RECRUITER_PASSWORD`, `TALASH_USER_PASSWORD`.

### Running Milestone 3

**Backend:**
```bash
cd milestone_3
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Runs on http://127.0.0.1:5000
```

**Frontend:**
```bash
cd milestone_3/frontend
npm install
npm start
# Runs on http://localhost:3000
```

The backend loads `milestone_3/outputs/cv_extraction_results.json` when present. If not found, it falls back to the Milestone 2 extraction file and normalised CSV exports.

### Frontend Components

| Component | Purpose |
|-----------|---------|
| Dashboard | Stats cards, top candidates, CV upload, folder ingest |
| Candidates | Searchable and filterable candidate ledger |
| CandidateDetail | Full profile, score breakdown by component, email trigger |
| Analysis | Tabbed view: Education / Experience / Research / Skills / Missing Info / Score |
| Reports | Score distribution chart, research mix, top skills and topics, email tracking table |
| Settings | User preferences (display name, timezone, notifications) |

### Email Tracking

By default email sending runs in dry-run mode so tracking works without SMTP credentials:

```text
TALASH_EMAIL_DRY_RUN=true
```

Each sent email gets a 16-character URL-safe tracking ID. A 1x1 pixel in the email footer records opens via `/api/email-track/<tracking_id>`. Opened/responded status is stored in `email_tracking.json`.

To send real email:
```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_address@gmail.com
SMTP_APP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_address@gmail.com
TALASH_EMAIL_DRY_RUN=false
```

---

## Scoring & Ranking Model

The ranking engine produces a score out of 100 across seven components.

| Component | Weight | Details |
|-----------|-------:|---------|
| Education | 20 | Degree rank (SSC=2 to Postdoc=20), +1 bonus for GPA 3.5+ or 80%+ |
| Research output | 25 | 1.4 pts/journal (max 10), 1.0 pts/conference (max 6), impact factor contribution (max 5), recent outputs within 5 years (max 4) |
| Topic variability and co-author network | 10 | 0.35 pts per unique research topic, 0.18 pts per unique co-author |
| Supervision, patents, books | 10 | 1.5 pts per completed supervision, 0.75 ongoing, 1.5 per patent, 1.5 per book |
| Professional experience | 15 | 1.2 pts/year (max 11), 0.8 pts per academic/research role (max 4) |
| Skill alignment | 10 | Based on match ratio against a required skills list |
| Completeness | 10 | Starts at 10, minus 1.5 per missing field |

**Ranking bands:**

| Score | Band |
|-------|------|
| 85 - 100 | Highly Recommended |
| 70 - 84 | Recommended |
| 55 - 69 | Review |
| 0 - 54 | Needs More Evidence |

The score and band appear in the dashboard, candidate ledger, candidate detail report, comparative reports, and `/api/rankings`.

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/login` | POST | Session-based authentication |
| `/api/logout` | POST | Clear session |
| `/api/auth-status` | GET | Current auth state |
| `/api/candidates` | GET | List all visible candidates (role-filtered) |
| `/api/candidate/<id>` | GET | Full profile and analysis |
| `/api/candidate/<id>` | DELETE | Remove candidate |
| `/api/analyze/<id>` | POST | Force re-analysis |
| `/api/analysis-output/<id>` | GET | Analysis JSON only |
| `/api/rankings` | GET | All candidates sorted by score |
| `/api/skill-alignment/<id>` | GET | Skill alignment breakdown |
| `/api/upload` | POST | Single PDF upload and extraction |
| `/api/ingest-folder` | POST | Batch process a folder |
| `/api/uploads` | GET | List uploaded files |
| `/api/upload/<filename>` | DELETE | Delete uploaded file |
| `/api/dashboard-stats` | GET | Totals, average score, flagged count |
| `/api/tabular-output` | GET | Candidate row data for tables |
| `/api/reports-data` | GET | Score distribution, research mix, top skills and topics |
| `/api/missing-info-email/<id>` | GET | Draft missing info email |
| `/api/send-missing-info-email/<id>` | POST | Queue or send missing info email |
| `/api/email-track/<tracking_id>` | GET | Pixel open-tracking endpoint |
| `/api/email-tracking` | GET | List all tracked emails |
| `/api/email-response/<tracking_id>` | POST | Mark email as responded |
| `/api/rubric-status` | GET | Feature completion status |
| `/health` | GET | Health check |

---

## Configuration

All configuration is via environment variables, typically stored in a `.env` file in `milestone_3/`.

```text
# Gemini
GEMINI_API_KEY=
GEMINI_MODEL_NAME=gemini-3.1-flash-lite-preview
TALASH_GEMINI_MODELS=          # comma-separated fallback models
TALASH_DISABLE_GEMINI=false
TALASH_GEMINI_COOLDOWN_SECONDS=2.0

# Auth
SECRET_KEY=                    # auto-generated if not set
TALASH_ADMIN_PASSWORD=admin123
TALASH_RECRUITER_PASSWORD=recruiter123
TALASH_USER_PASSWORD=user123

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_APP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_USE_TLS=true
TALASH_EMAIL_DRY_RUN=true

# Server
PORT=5000
```

---

## File Structure

```text
Talash-LLM_Project/
├── README.md
├── milestone_1/
│   ├── cv_extraction_pipeline.ipynb
│   ├── schema.sql
│   └── requirements.txt
├── milestone_2/
│   ├── cv_batch_processor.py
│   ├── milestone2.py
│   ├── app.py
│   ├── sample_cv_generator.py
│   ├── frontend/                  # HTML/CSS intermediate web app
│   ├── uploads/
│   ├── outputs/
│   └── requirements.txt
└── milestone_3/
    ├── app.py                     # Flask API server
    ├── milestone2.py              # Analysis and ranking engine
    ├── cv_batch_processor.py      # Batch PDF processor
    ├── frontend/                  # React + Vite application
    │   └── src/
    │       └── components/
    ├── uploads/
    ├── outputs/
    │   ├── cv_extraction_results.json
    │   ├── analysis_results.json
    │   └── email_tracking.json
    └── requirements.txt
```

---

## References

- Google Generative AI: https://ai.google.dev/
- pdfplumber: https://github.com/jsvine/pdfplumber
- Flask: https://flask.palletsprojects.com/
- React: https://react.dev/
- Chart.js: https://www.chartjs.org/
- Supabase: https://supabase.com/docs

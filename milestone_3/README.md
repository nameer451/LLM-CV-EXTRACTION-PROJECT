# TALASH Milestone 3

Full integrated system for the CS 417 LLM TALASH project.

## What Is Included

- Flask backend with session authentication
- React frontend for recruiter workflows
- Folder-based PDF CV processing
- Candidate-wise tabular output
- Full educational, professional, research, topic, co-author, supervision, patent, and book analysis
- Skill alignment against role requirements
- Personalized missing-information email drafting
- Email open and response tracking
- Extra-credit quantifiable candidate ranking module

## Demo Login

```text
admin / admin123
recruiter / recruiter123
user / user123
```

Passwords can be overridden with:

```text
TALASH_ADMIN_PASSWORD
TALASH_RECRUITER_PASSWORD
TALASH_USER_PASSWORD
```

`admin` can see the seeded 43-candidate demo data. `recruiter` and `user` start with an empty workspace and only see candidates they upload or ingest during their session.

## Backend

```bash
cd milestone_3
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend URL:

```text
http://127.0.0.1:5000
```

The backend loads `milestone_3/outputs/cv_extraction_results.json` when present. If it is not present, it falls back to the completed Milestone 2 extraction file and normalized CSV exports.

## Frontend

```bash
cd milestone_3/frontend
npm install
npm start
```

Frontend URL:

```text
http://localhost:3000
```

## Email Tracking

By default email sending runs in dry-run mode, so demo tracking works without SMTP credentials:

```text
TALASH_EMAIL_DRY_RUN=true
```

To send real email, set:

```text
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_APP_PASSWORD
SMTP_FROM_EMAIL
TALASH_EMAIL_DRY_RUN=false
```

## Key API Endpoints

```text
POST /api/login
GET  /api/candidates
GET  /api/candidate/<id>
GET  /api/analysis-output/<id>
GET  /api/rankings
POST /api/upload
POST /api/ingest-folder
GET  /api/reports-data
GET  /api/tabular-output
GET  /api/missing-info-email/<id>
POST /api/send-missing-info-email/<id>
GET  /api/email-tracking
POST /api/email-response/<tracking_id>
GET  /api/rubric-status
GET  /health
```

## Extra-Credit Ranking Model

The ranking engine produces a 100-point score:

| Component | Weight |
| --- | ---: |
| Education | 20 |
| Research output | 25 |
| Topic variability and co-author network | 10 |
| Supervision, patents, books | 10 |
| Professional experience | 15 |
| Skill alignment | 10 |
| Completeness | 10 |

The score is shown in the dashboard, candidate ledger, candidate detail report, comparative reports, and `/api/rankings`.

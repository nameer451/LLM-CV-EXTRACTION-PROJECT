# Environment Setup

## Python

Use Python 3.9 or newer.

```bash
cd milestone_3
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Node

Use Node 18 or newer.

```bash
cd milestone_3/frontend
npm install
```

## Optional Gemini

Milestone 3 reuses the Milestone 2 parser. Gemini extraction activates when these variables are configured:

```text
GEMINI_API_KEY
GEMINI_MODEL_NAME
TALASH_GEMINI_MODELS
```

Set this to force rule-based parsing:

```text
TALASH_DISABLE_GEMINI=true
```

## Optional SMTP

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_APP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email
SMTP_USE_TLS=true
TALASH_EMAIL_DRY_RUN=false
```

Keep `TALASH_EMAIL_DRY_RUN=true` for classroom demos without real email sending.

## Demo Users

```text
admin / admin123       Shows seeded Milestone 2 candidates
recruiter / recruiter123 Starts with an empty workspace
user / user123         Starts with an empty workspace
```

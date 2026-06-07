# TALASH: Talent Acquisition & Learning Automation for Smart Hiring

## Course Information
**Course:** CS-417 Large Language Models  
**Semester:** Spring 2026  
**University:** NUST Islamabad  

**Team Members**
- Nameer Ahmed (454029)
- Rimsha Mahmood (455080)
- Muhammad Ahmad (461348)

---

# Milestone 2

## Objective
Milestone 2 focuses on building the core extraction and analysis pipeline with an intermediate web application for viewing candidate data and analysis results.

The system performs:

- CV parsing from PDF files  
- Educational profile analysis  
- Professional experience analysis  
- Missing information detection  
- Draft email generation for missing details  
- Intermediate web dashboard for displaying results  

---

# Implemented Components

## 1. CV Parsing and Structured Extraction

Implemented in:

- `cv_batch_processor.py`

Features:

- Reads CVs from uploads folder  
- Extracts text from PDF files using pdfplumber  
- Converts extracted content into structured JSON  
- Stores outputs in output files  

Run:

```bash
python cv_batch_processor.py
```

Example output:

```json
{
 "candidate_name":"Ahmed Khan",
 "education":[...],
 "experience":[...],
 "skills":[...]
}
```

---

## 2. Educational Profile Analysis

Implemented in:

- `milestone2.py`

Checks:

- Degree progression validation  
- Educational gaps  
- Highest qualification identification  
- Missing CGPA detection  
- Institution quality checks  

Example:

```python
education_analysis = {
 "highest_qualification":"MS Computer Science",
 "educational_gaps":"None detected"
}
```

---

## 3. Professional Experience Analysis

Implemented in:

- `milestone2.py`

Checks:

- Timeline overlap detection  
- Employment gap analysis  
- Career progression tracking  
- Current employment status  

Example:

```python
experience_analysis = {
 "timeline_overlaps":"None",
 "professional_gaps":"No major gaps",
 "career_progression":"Junior to Senior progression"
}
```

---

## 4. Missing Information Detection and Email Drafting

Implemented in:

- `milestone2.py`

Detects:

- Missing email  
- Missing phone number  
- Missing grades  
- Incomplete candidate fields  

Generates draft email:

```text
Dear Candidate,

Some information is missing from your submitted CV.

Please provide the missing details and resubmit.

Regards,
HR Team
```

---

## 5. Intermediate Web Application

Implemented using:

- Flask backend  
- HTML/CSS frontend  
- Chart.js visualizations  

Pages created:

- Login  
- Dashboard  
- Candidates  
- Analysis Results  
- Reports  
- Profile  
- Settings  

Features:

- Candidate search  
- Analysis viewing  
- Charts and reports  
- Candidate profile pages  
- Upload interface  

Run backend:

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

---

# File Structure

```text
Talash-LLM_Project/

app.py
cv_batch_processor.py
milestone2.py
sample_cv_generator.py

frontend/
 ├── login.html
 ├── index.html
 ├── candidates.html
 ├── analysis.html
 ├── reports.html
 ├── profile.html
 └── settings.html

uploads/
outputs/
```

---

# Running the Demo

Generate sample data:

```bash
python sample_cv_generator.py
```

Start backend:

```bash
python app.py
```

Process CV folder:

```bash
python cv_batch_processor.py
```

---

# Rubric Coverage

## CV Parsing (5 Marks)
- Folder-based reading implemented  
- Structured extraction implemented  
- JSON output generated  

## Educational Analysis (5 Marks)
- Degree progression checks  
- Qualification analysis  
- Gap detection implemented  

## Professional Analysis (6 Marks)
- Timeline validation  
- Gap detection  
- Career progression analysis  

## Missing Information (4 Marks)
- Missing fields detected  
- Draft emails generated  

## Intermediate Web App (6 Marks)
- Multi-page interface  
- Charts and analysis display  
- Candidate data visualization  

---

# Future Work (Milestone 3)

Planned additions:

- Full Gemini integration  
- Supabase database connection  
- Candidate ranking engine  
- Job matching module  
- Email sending integration  

---

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Repository

GitHub:

https://github.com/mahmadr10/Talash-LLM_Project

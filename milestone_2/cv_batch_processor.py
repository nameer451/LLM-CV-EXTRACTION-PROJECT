"""
TALASH - CV Batch Processing Pipeline
Processes CVs from a folder and stores results
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import pdfplumber

try:
    import google.generativeai as genai
except ImportError:
    genai = None


GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-3.1-flash-lite-preview')
GEMINI_MODEL_FALLBACKS = [
    model.strip()
    for model in os.getenv('TALASH_GEMINI_MODELS', '').split(',')
    if model.strip()
]
GEMINI_ENABLED = os.getenv('TALASH_DISABLE_GEMINI', '').strip().lower() not in {'1', 'true', 'yes'}
_GEMINI_CONFIGURED = False
MAX_CANDIDATES_PER_PDF = 50  # Limit batch processing to first N candidates per PDF to avoid rate limits
GEMINI_COOLDOWN_SECONDS = float(os.getenv('TALASH_GEMINI_COOLDOWN_SECONDS', '2.0'))

SECTION_HEADERS = {
    'skills': [
        'skills', 'technical skills', 'core competencies', 'competencies', 'tools',
        'technologies', 'technology stack', 'programming languages'
    ],
    'education': ['education', 'academic background', 'academics', 'qualification', 'qualifications'],
    'experience': ['experience', 'work experience', 'employment history', 'professional experience']
}

SECTION_STOP_HEADERS = {
    'skills': ['education', 'experience', 'projects', 'publications', 'certifications', 'references'],
    'education': ['experience', 'skills', 'projects', 'publications', 'certifications', 'references'],
    'experience': ['education', 'skills', 'projects', 'publications', 'certifications', 'references']
}

SKILL_CATEGORY_HINTS = {
    'Research': ['research', 'publication', 'methodology', 'academic', 'thesis'],
    'Soft': ['leadership', 'communication', 'teamwork', 'collaboration', 'mentoring', 'management'],
    'Tool': ['excel', 'tableau', 'power bi', 'jira', 'confluence', 'git', 'github', 'linux', 'windows'],
    'Technical': ['python', 'java', 'sql', 'javascript', 'machine learning', 'ai', 'data', 'cloud', 'docker'],
}

UNIVERSITY_MAP = {
    'nust': 'National University of Sciences and Technology',
    'lums': 'Lahore University of Management Sciences',
    'giki': 'Ghulam Ishaq Khan Institute',
    'fast': 'National University of Computer and Emerging Sciences',
    'pu': 'University of the Punjab',
    'uet': 'University of Engineering and Technology',
    'qau': 'Quaid-i-Azam University',
    'comsats': 'COMSATS University',
}

SYSTEM_PROMPT = """
You are an expert HR AI for the TALASH academic recruitment system.
Extract CV information into STRICT JSON only.

CRITICAL RULES:
1. grade_metric must be exactly one of: GPA, CGPA, Percentage, Unknown.
2. is_sse_hssc must be true only for Matric/O-Levels/FSc/HSSC/SSC.
3. output_type must be exactly one of: Journal, Conference, Book, Patent, Unknown.
4. degree_level must be exactly one of: BS, MS, PhD, Unknown.
5. supervision status must be exactly one of: Completed, Ongoing, Unknown.
6. skill_category must be exactly one of: Technical, Research, Soft, Tool, Unknown.
7. If unsure about numeric fields, use null.
8. Use empty arrays for missing sections.
9. Return valid JSON only. No markdown and no code fences.
10. For duration_months: calculate the integer number of months between start_date and end_date. Use the current date for "Present"/"Current". Never leave null if both dates are present.
11. For skills: extract ALL skills mentioned anywhere in the CV — including technical tools, programming languages, research methodologies, domain expertise areas (e.g. Computer Vision, NLP, Medical Imaging), soft skills, and leadership competencies. Do not limit to a dedicated Skills section.
12. For research_outputs: extract EVERY publication listed — journals, conference papers, book chapters, and patents. Include all entries even if there are dozens.

OUTPUT SCHEMA:
{
  "personal_info": {
    "full_name": "string",
    "email": "string",
    "phone_number": "string",
    "research_summary": "string",
    "dob": "string",
    "marital_status": "string",
    "fathers_name": "string"
  },
  "education": [{
    "degree_name": "string",
    "specialization": "string",
    "institution_name": "string",
    "grade_value": null,
    "grade_metric": "Unknown",
    "passing_year": null,
    "is_sse_hssc": false,
    "qs_ranking": null,
    "the_ranking": null
  }],
  "experience": [{
    "job_title": "string",
    "organization": "string",
    "location": "string",
    "start_date": "string",
    "end_date": "string",
    "is_current": false,
    "job_description": "string",
    "industry": "string",
    "duration_months": null
  }],
  "certifications": [{
    "qualification_name": "string",
    "institution_name": "string",
    "passing_year": null
  }],
  "awards": [{
    "award_type": "string",
    "detail": "string"
  }],
  "references": [{
    "reference_name": "string",
    "designation": "string",
    "address": "string",
    "phone": "string",
    "email": "string"
  }],
  "research_outputs": [{
    "title": "string",
    "venue_name": "string",
    "output_type": "Unknown",
    "publication_year": null,
    "impact_factor": null,
    "author_names": "string",
    "research_topics": []
  }],
  "supervision": [{
    "student_name": "string",
    "degree_level": "Unknown",
    "status": "Unknown"
  }],
  "skills": [{
    "skill_name": "string",
    "skill_category": "Unknown"
  }]
}
"""


def _calculate_duration_months(start_str, end_str):
    """Return integer month count between two date strings; None on parse failure."""
    try:
        from dateutil import parser as _dp
        start = _dp.parse(start_str, fuzzy=True)
        if not end_str or end_str.strip().lower() in {'present', 'current', 'now', 'till date', 'to date'}:
            end = datetime.now()
        else:
            end = _dp.parse(end_str, fuzzy=True)
        months = (end.year - start.year) * 12 + (end.month - start.month)
        return max(0, months)
    except Exception:
        return None


def extract_float(value):
    if value is None or str(value).strip() == '':
        return None
    match = re.search(r'\d+(\.\d+)?', str(value))
    return float(match.group()) if match else None


def extract_int(value):
    if value is None or str(value).strip() == '':
        return None
    match = re.search(r'\d+', str(value))
    return int(match.group()) if match else None


def clean_string(value):
    if not value:
        return None
    cleaned = str(value).strip()
    if cleaned.lower() in {'null', 'none', 'unknown', 'n/a', ''}:
        return None
    return cleaned


def validate_enum(value, valid_options, default='Unknown'):
    cleaned = clean_string(value)
    if not cleaned:
        return default

    for option in valid_options:
        if cleaned.lower() == option.lower():
            return option
    return default


def normalize_university(raw_name):
    cleaned = clean_string(raw_name)
    if not cleaned:
        return None

    key = cleaned.lower()
    if key in UNIVERSITY_MAP:
        return UNIVERSITY_MAP[key]

    words = set(key.replace('(', ' ').replace(')', ' ').split())
    for short_name, full_name in UNIVERSITY_MAP.items():
        if short_name in words:
            return full_name

    return cleaned.title()


def _as_list(payload, key):
    value = payload.get(key, []) if isinstance(payload, dict) else []
    return value if isinstance(value, list) else []


def _normalize_education(items):
    output = []
    for e in items:
        if not isinstance(e, dict):
            continue
        degree_name = clean_string(e.get('degree_name'))
        institution_name = normalize_university(e.get('institution_name'))
        if not degree_name and not institution_name:
            continue

        output.append({
            'degree_name': degree_name or '',
            'specialization': clean_string(e.get('specialization')) or '',
            'institution_name': institution_name or '',
            'grade_value': extract_float(e.get('grade_value')),
            'grade_metric': validate_enum(e.get('grade_metric'), ['GPA', 'CGPA', 'Percentage'], 'Unknown'),
            'passing_year': extract_int(e.get('passing_year')),
            'is_sse_hssc': bool(e.get('is_sse_hssc')),
            'qs_ranking': extract_int(e.get('qs_ranking')),
            'the_ranking': extract_int(e.get('the_ranking')),
        })
    return output


def _normalize_experience(items):
    output = []
    for ex in items:
        if not isinstance(ex, dict):
            continue

        start_date = clean_string(ex.get('start_date')) or ''
        end_date = clean_string(ex.get('end_date')) or ''
        duration_months = extract_int(ex.get('duration_months'))
        if duration_months is None and start_date:
            duration_months = _calculate_duration_months(start_date, end_date)

        output.append({
            'job_title': clean_string(ex.get('job_title')) or '',
            'organization': clean_string(ex.get('organization')) or '',
            'location': clean_string(ex.get('location')) or '',
            'start_date': start_date,
            'end_date': end_date,
            'is_current': bool(ex.get('is_current')),
            'job_description': clean_string(ex.get('job_description')) or '',
            'industry': clean_string(ex.get('industry')) or '',
            'duration_months': duration_months,
        })
    return output


def _normalize_research_outputs(items):
    output = []
    for r in items:
        if not isinstance(r, dict):
            continue
        output.append({
            'title': clean_string(r.get('title')) or '',
            'venue_name': clean_string(r.get('venue_name')) or '',
            'output_type': validate_enum(r.get('output_type'), ['Journal', 'Conference', 'Book', 'Patent'], 'Unknown'),
            'publication_year': extract_int(r.get('publication_year')),
            'impact_factor': extract_float(r.get('impact_factor')),
            'author_names': clean_string(r.get('author_names')) or '',
            'research_topics': r.get('research_topics', []) if isinstance(r.get('research_topics'), list) else [],
        })
    return output


def _normalize_supervision(items):
    output = []
    for s in items:
        if not isinstance(s, dict):
            continue
        output.append({
            'student_name': clean_string(s.get('student_name')) or '',
            'degree_level': validate_enum(s.get('degree_level'), ['BS', 'MS', 'PhD'], 'Unknown'),
            'status': validate_enum(s.get('status'), ['Completed', 'Ongoing'], 'Unknown'),
        })
    return output


def _normalize_skills(items):
    output = []
    seen = set()
    for sk in items:
        if not isinstance(sk, dict):
            continue
        skill_name = clean_string(sk.get('skill_name'))
        if not skill_name:
            continue

        key = skill_name.lower()
        if key in seen:
            continue
        seen.add(key)

        output.append({
            'skill_name': skill_name,
            'skill_category': validate_enum(sk.get('skill_category'), ['Technical', 'Research', 'Soft', 'Tool'], 'Unknown'),
        })
    return output


def _normalize_certifications(items):
    output = []
    for c in items:
        if not isinstance(c, dict):
            continue
        qualification_name = clean_string(c.get('qualification_name'))
        if not qualification_name:
            continue
        output.append({
            'qualification_name': qualification_name,
            'institution_name': clean_string(c.get('institution_name')) or '',
            'passing_year': extract_int(c.get('passing_year')),
        })
    return output


def _normalize_awards(items):
    output = []
    for a in items:
        if not isinstance(a, dict):
            continue
        detail = clean_string(a.get('detail'))
        if not detail and not clean_string(a.get('award_type')):
            continue
        output.append({
            'award_type': clean_string(a.get('award_type')) or '',
            'detail': detail or '',
        })
    return output


def _normalize_references(items):
    output = []
    for r in items:
        if not isinstance(r, dict):
            continue
        output.append({
            'reference_name': clean_string(r.get('reference_name')) or '',
            'designation': clean_string(r.get('designation')) or '',
            'address': clean_string(r.get('address')) or '',
            'phone': clean_string(r.get('phone')) or '',
            'email': clean_string(r.get('email')) or '',
        })
    return output


def _configure_gemini():
    """Configure Gemini once if the package and API key are available."""
    global _GEMINI_CONFIGURED

    if not GEMINI_ENABLED:
        print(f"[GEMINI] ✗ Gemini is disabled (TALASH_DISABLE_GEMINI env var set)")
        return False
    
    if genai is None:
        print(f"[GEMINI] ✗ google.generativeai package not imported")
        return False

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print(f"[GEMINI] ✗ GEMINI_API_KEY environment variable not set")
        return False
    
    print(f"[GEMINI] ✓ API key found (length: {len(api_key)})")

    if not _GEMINI_CONFIGURED:
        try:
            genai.configure(api_key=api_key)
            _GEMINI_CONFIGURED = True
            print(f"[GEMINI] ✓ Configured with model: {GEMINI_MODEL_NAME}")
        except Exception as e:
            print(f"[GEMINI] ✗ Configuration failed: {str(e)}")
            return False

    return True


def _parse_json_payload(raw_text):
    """Extract JSON from a Gemini response that may contain code fences or extra text."""
    cleaned = (raw_text or '').strip()

    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```$', '', cleaned)

    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]

    return json.loads(cleaned)


def _iter_gemini_models():
    """Return configured models in priority order with duplicates removed."""
    models = [GEMINI_MODEL_NAME] + GEMINI_MODEL_FALLBACKS
    deduped = []
    seen = set()
    for model_name in models:
        key = model_name.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(model_name.strip())
    return deduped


def _cooldown_sleep(seconds, reason):
    """Throttle Gemini requests to reduce token/rate-limit failures."""
    delay = max(0.0, float(seconds))
    if delay <= 0:
        return
    print(f"[GEMINI] Waiting {delay:.1f}s ({reason})")
    time.sleep(delay)


def _is_token_or_rate_limit_error(error):
    """Detect token/quota/rate errors using provider message text."""
    message = str(error).lower()
    keywords = ['token', 'rate', 'quota', '429', 'resource exhausted', 'too many requests']
    return any(word in message for word in keywords)


def _normalize_structured_extraction(payload, fallback_name):
    """Fill the schema expected by the Milestone 2 app."""
    payload = payload if isinstance(payload, dict) else {}
    personal_info = payload.get('personal_info', {}) if isinstance(payload.get('personal_info', {}), dict) else {}

    name = clean_string(payload.get('name')) or clean_string(personal_info.get('full_name')) or fallback_name
    email = clean_string(payload.get('email')) or clean_string(personal_info.get('email')) or ''
    phone = clean_string(payload.get('phone_number')) or clean_string(personal_info.get('phone_number')) or ''

    return {
        'name': name,
        'email': email,
        'phone_number': phone,
        'research_summary': clean_string(personal_info.get('research_summary')) or '',
        'dob': clean_string(personal_info.get('dob')) or '',
        'marital_status': clean_string(personal_info.get('marital_status')) or '',
        'fathers_name': clean_string(personal_info.get('fathers_name')) or '',
        'education': _normalize_education(_as_list(payload, 'education')),
        'experience': _normalize_experience(_as_list(payload, 'experience')),
        'skills': _normalize_skills(_as_list(payload, 'skills')),
        'research_outputs': _normalize_research_outputs(_as_list(payload, 'research_outputs')),
        'certifications': _normalize_certifications(_as_list(payload, 'certifications')),
        'awards': _normalize_awards(_as_list(payload, 'awards')),
        'references': _normalize_references(_as_list(payload, 'references') or _as_list(payload, 'references_table')),
        'supervision': _normalize_supervision(_as_list(payload, 'supervision')),
        'extraction_method': payload.get('extraction_method', 'gemini' if payload.get('gemini_used') else 'rule-based')
    }


def _extract_all_candidate_chunks(raw_text):
    """Extract candidate chunks from a multi-candidate PDF (limited to first MAX_CANDIDATES_PER_PDF).
    
    Returns a list of (chunk_text, index) tuples, one per candidate.
    If no delimiter found, returns entire text as single chunk.
    Limited to MAX_CANDIDATES_PER_PDF to avoid rate limit issues.
    """
    text = (raw_text or '').replace('\x00', ' ')
    text = re.sub(r'\s+', ' ', text).strip()

    # Split by "Candidate for the post of" delimiter (case-insensitive)
    raw_chunks = re.split(r'(?i)candidate for the post of', text)
    
    # Filter and format chunks - keep those with at least 500 chars
    chunks = []
    for i, c in enumerate(raw_chunks):
        # Stop if we've reached the max candidates
        if len(chunks) >= MAX_CANDIDATES_PER_PDF:
            print(f"[EXTRACTION] Limiting to {MAX_CANDIDATES_PER_PDF} candidates per PDF. Total found: {len(raw_chunks) - 1}")
            break
        
        chunk_text = c.strip()
        if len(chunk_text) > 500:
            # Add delimiter back to all except first (which had no delimiter originally)
            if i > 0:
                chunk_text = 'Candidate for the post of ' + chunk_text
            chunks.append((chunk_text[:50000], i))  # Cap at 50k chars per chunk
    
    # If no chunks found via delimiter, return entire text as single chunk
    if not chunks:
        return [(text[:10000], 0)]
    
    return chunks


def _candidate_text_chunk(raw_text):
    """Mirror notebook behavior for noisy PDFs while still supporting single-CV files.
    
    DEPRECATED: Use _extract_all_candidate_chunks() for multi-candidate support.
    Returns only the first chunk for backward compatibility.
    """
    chunks = _extract_all_candidate_chunks(raw_text)
    return chunks[0][0] if chunks else raw_text[:10000]


def _extract_with_gemini(raw_text, fallback_name):
    """Use Gemini to convert CV text into structured JSON."""
    if not _configure_gemini():
        print(f"[GEMINI] ✗ Gemini not configured (API key missing?)")
        return None

    cv_chunk = raw_text[:50000] if raw_text else ''
    prompt = f"{SYSTEM_PROMPT}\n\nPreferred candidate name: {fallback_name}\n\nCV TEXT:\n{cv_chunk}"

    max_attempts = 4
    model_names = _iter_gemini_models()
    for model_name in model_names:
        model = genai.GenerativeModel(model_name)
        print(f"[GEMINI] -> Calling {model_name} for: {fallback_name}")

        for attempt in range(max_attempts):
            try:
                # Space out requests to avoid burst failures and token/quota throttling.
                _cooldown_sleep(GEMINI_COOLDOWN_SECONDS, f"pre-request cooldown for {fallback_name}")

                response = model.generate_content(
                    prompt,
                    generation_config={'response_mime_type': 'application/json'}
                )
                response_text = getattr(response, 'text', '') or ''
                if not response_text and getattr(response, 'candidates', None):
                    response_text = str(response.candidates[0])

                parsed = _parse_json_payload(response_text)
                if isinstance(parsed, dict):
                    parsed['gemini_used'] = True
                    parsed['gemini_model'] = model_name
                    print(f"[GEMINI] + Successfully extracted via Gemini ({model_name})")
                    return _normalize_structured_extraction(parsed, fallback_name)
            except json.JSONDecodeError as e:
                print(f"[GEMINI] x Model {model_name} attempt {attempt + 1}/{max_attempts} - JSON decode error: {str(e)[:100]}")
                _cooldown_sleep(2 + attempt, "retry after JSON decode error")
                continue
            except Exception as e:
                print(f"[GEMINI] x Model {model_name} attempt {attempt + 1}/{max_attempts} - {type(e).__name__}: {str(e)[:100]}")
                if _is_token_or_rate_limit_error(e):
                    # Longer backoff when provider indicates token/rate pressure.
                    _cooldown_sleep(GEMINI_COOLDOWN_SECONDS + 4 + attempt * 2, "token/rate limit backoff")
                else:
                    _cooldown_sleep(2 + attempt, "generic retry backoff")
                continue

        print(f"[GEMINI] x Model {model_name} exhausted retries")

    print(f"[GEMINI] ✗ Failed after {max_attempts} attempts, falling back to rule-based")
    return None


def _extract_candidate_name(text, fallback_name):
    """Heuristic candidate-name extractor when LLM extraction is unavailable."""
    lines = (text or '').splitlines()[:50]  # Look in first 50 lines
    
    # First, try to find lines starting with "Name" or similar
    for line in lines:
        cleaned = re.sub(r'\s+', ' ', line).strip(' -:\t')
        lower = cleaned.lower()
        if lower.startswith('name') and ':' in lower:
            # Extract after "Name:"
            parts = cleaned.split(':', 1)
            if len(parts) > 1:
                name_part = parts[1].strip()
                if name_part and len(name_part) > 3:
                    return ' '.join(word.capitalize() for word in name_part.split())
    
    # Fallback to original logic
    for line in lines:
        cleaned = re.sub(r'\s+', ' ', line).strip(' -:\t')
        if len(cleaned) < 3 or len(cleaned) > 80:
            continue
        lower = cleaned.lower()
        if any(token in lower for token in ['email', 'phone', 'mobile', 'address', 'objective', 'summary', 'qualification']):
            continue
        if re.search(r'[^A-Za-z\s\.-]', cleaned):
            continue
        words = cleaned.replace('.', ' ').split()
        if 2 <= len(words) <= 5:
            return ' '.join(word.capitalize() for word in words)
    return fallback_name


def _extract_section_lines(text, section_key):
    """Extract probable lines under a CV section header."""
    headers = SECTION_HEADERS.get(section_key, [])
    stop_headers = SECTION_STOP_HEADERS.get(section_key, [])
    lines = (text or '').splitlines()
    collected = []
    collecting = False

    for raw_line in lines:
        line = re.sub(r'\s+', ' ', raw_line).strip()
        if not line:
            if collecting and collected:
                break
            continue

        normalized = line.lower().strip(':-')
        if any(normalized.startswith(h) for h in headers):
            collecting = True
            continue

        if collecting and any(normalized.startswith(h) for h in stop_headers):
            break

        if collecting:
            collected.append(line)

    return collected


def _guess_skill_category(skill_name):
    skill = (skill_name or '').lower()
    for category, hints in SKILL_CATEGORY_HINTS.items():
        if any(hint in skill for hint in hints):
            return category
    return 'Technical'


def _normalize_degree_name(line):
    """Map free-text education line to a canonical degree label."""
    text = (line or '').lower()

    if re.search(r'\b(ph\.?d|doctorate|doctoral)\b', text):
        return 'PhD'
    if re.search(r'\b(m\.?\s?s\.?c?|master\'?s|masters|master|mphil|mba)\b', text):
        return 'MS'
    if re.search(r'\b(b\.?\s?s\.?c?|bachelor\'?s|bachelors|bachelor|bba|be|beng)\b', text):
        return 'BS'
    if re.search(r'\b(fsc|hssc|intermediate|a-?levels)\b', text):
        return 'HSSC'
    if re.search(r'\b(ssc|matric|o-?levels)\b', text):
        return 'SSC'
    return None


def _extract_institution_from_line(line):
    """Infer institution name from one education line."""
    text = str(line or '')
    lowered = text.lower()

    for short_name, full_name in UNIVERSITY_MAP.items():
        if re.search(rf'\b{re.escape(short_name)}\b', lowered):
            return full_name

    # Generic fallback: capture phrases ending with institution keywords.
    match = re.search(
        r'([A-Za-z][A-Za-z\s\-\.&]{3,}?(?:university|institute|college|school))',
        text,
        re.IGNORECASE
    )
    if match:
        return normalize_university(match.group(1))

    return ''


def _extract_skills_rule_based(text):
    """Extract skills without hardcoded fixed-skill lists."""
    candidates = []
    section_lines = _extract_section_lines(text, 'skills')

    if section_lines:
        merged = ' | '.join(section_lines)
        parts = re.split(r'[|,;/\\]|\s+-\s+|\s{2,}', merged)
        candidates.extend(parts)
    else:
        # Fallback: parse generic "proficient/experienced/familiar" expressions.
        phrase_matches = re.findall(
            r'(?:proficient in|experienced with|experience in|familiar with|tools?:)\s*([^\n\.]+)',
            text or '',
            flags=re.IGNORECASE
        )
        for phrase in phrase_matches:
            candidates.extend(re.split(r'[,;/]|\band\b', phrase, flags=re.IGNORECASE))

    seen = set()
    structured = []
    for token in candidates:
        cleaned = re.sub(r'^[\-•*\d\.)\s]+', '', token or '').strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)
        if not cleaned or len(cleaned) < 2:
            continue
        if len(cleaned) > 40:
            continue
        if cleaned.lower() in {'skills', 'technical', 'core', 'competencies', 'others'}:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        structured.append({
            'skill_name': cleaned,
            'skill_category': _guess_skill_category(cleaned)
        })

    return structured


def _extract_education_rule_based(text):
    records = []
    # Keep degree matching strict to avoid false positives such as "MS Office" from skills text.
    degree_pattern = re.compile(
        r'\b(ph\.?d|doctorate|doctoral|m\.?\s?s\.?c?|master\'?s|masters|master|mphil|mba|b\.?\s?s\.?c?|bachelor\'?s|bachelors|bachelor|bba|be|beng|fsc|hssc|intermediate|a-?levels|ssc|matric|o-?levels)\b',
        re.IGNORECASE
    )
    year_pattern = re.compile(r'(19\d{2}|20\d{2})')
    non_degree_markers = {'office', 'excel', 'word', 'powerpoint', 'outlook'}
    degree_context_markers = {
        'degree', 'university', 'college', 'institute', 'school', 'cgpa', 'gpa',
        'bachelor', 'master', 'phd', 'matric', 'intermediate', 'hssc', 'ssc', 'fsc'
    }

    section_lines = _extract_section_lines(text, 'education')

    for idx, line in enumerate(section_lines):
        if not degree_pattern.search(line):
            continue

        lower_line = line.lower()
        # Skip common software-skill lines unless explicit education context is present.
        if any(marker in lower_line for marker in non_degree_markers) and not any(ctx in lower_line for ctx in degree_context_markers):
            continue

        degree_name = _normalize_degree_name(line)
        if not degree_name:
            continue

        year_match = year_pattern.search(line)
        metric = 'Unknown'
        grade = None
        if re.search(r'cgpa|gpa', line, re.IGNORECASE):
            metric = 'CGPA' if re.search(r'cgpa', line, re.IGNORECASE) else 'GPA'
            grade_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:/\s*4(?:\.0+)?)?', line)
            if grade_match:
                grade = extract_float(grade_match.group(1))

        institution_name = _extract_institution_from_line(line)
        if not institution_name:
            # Many CVs place the institution on the line above/below the degree title.
            nearby = []
            if idx - 1 >= 0:
                nearby.append(section_lines[idx - 1])
            if idx - 2 >= 0:
                nearby.append(section_lines[idx - 2])
            nearby.extend(section_lines[idx + 1: idx + 3])

            for neighbor in nearby:
                institution_name = _extract_institution_from_line(neighbor)
                if institution_name:
                    break

        records.append({
            'degree_name': degree_name,
            'specialization': '',
            'institution_name': institution_name,
            'grade_value': grade,
            'grade_metric': metric,
            'passing_year': int(year_match.group(1)) if year_match else None,
            'is_sse_hssc': bool(re.search(r'fsc|hssc|ssc|matric|o-?levels', line, re.IGNORECASE)),
            'qs_ranking': None,
            'the_ranking': None,
        })
    return records


def _extract_experience_rule_based(text):
    records = []
    year_span = re.compile(r'(19\d{2}|20\d{2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).{0,20}(19\d{2}|20\d{2}|present|current)', re.IGNORECASE)
    section_lines = _extract_section_lines(text, 'experience')
    
    for line in section_lines:
        if len(line) < 4:
            continue
        parts = [p.strip() for p in line.split(',') if p.strip()]
        if len(parts) < 2:
            continue
        job_title = parts[0]
        organization = parts[1] if len(parts) > 1 else ''
        location = parts[2] if len(parts) > 2 else ''
        duration = parts[3] if len(parts) > 3 else ''
        
        match = year_span.search(line)
        start_date = ''
        end_date = ''
        if match:
            start_date = match.group(1)
            end_date = match.group(2)
        
        records.append({
            'job_title': job_title[:120],
            'organization': organization[:120],
            'location': location[:120],
            'start_date': start_date,
            'end_date': end_date,
            'is_current': end_date.lower() in ['present', 'current'],
            'job_description': line[:300],
            'industry': '',
            'duration_months': None,
        })
    return records


def _extract_personal_info_rule_based(text):
    info = {}
    lines = text.splitlines()[:100]
    for line in lines:
        line = line.strip()
        lower = line.lower()
        if 'father' in lower and 'name' in lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                info['fathers_name'] = parts[1].strip()
        elif 'date' in lower and 'birth' in lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                info['dob'] = parts[1].strip()
        elif 'marital' in lower and 'status' in lower:
            parts = line.split(':', 1)
            if len(parts) > 1:
                info['marital_status'] = parts[1].strip()
    return info


def _extract_research_rule_based(text):
    records = []
    # Look for publication-like lines
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if len(line) < 10:
            continue
        lower = line.lower()
        if any(keyword in lower for keyword in ['journal', 'conference', 'paper', 'publication', 'published']):
            # Assume it's a publication
            records.append({
                'title': line[:200],
                'authors': '',
                'publication_name': '',
                'publication_year': None,
                'output_type': 'Journal' if 'journal' in lower else 'Conference',
                'doi': '',
                'impact_factor': None,
                'citations': None,
                'co_authors': [],
            })
    return records


PUBLICATIONS_PROMPT = """Extract ALL publications from this CV as a JSON array.
Return ONLY a raw JSON array (no markdown, no code fences, no explanation).
Each element must be: {"title": "string", "venue_name": "string", "output_type": "Journal|Conference|Book|Patent", "publication_year": null, "author_names": "string", "research_topics": [], "impact_factor": null}
Extract every single entry: journal articles, conference papers, book chapters, patents.
Do not summarise or truncate — list them all."""


def _extract_publications_second_pass(raw_text, candidate_name):
    """Second dedicated Gemini call to extract the full publications list."""
    if not _configure_gemini():
        return None
    prompt = f"{PUBLICATIONS_PROMPT}\n\nCV TEXT:\n{raw_text[:50000]}"
    for model_name in _iter_gemini_models():
        model = genai.GenerativeModel(model_name)
        for attempt in range(3):
            try:
                _cooldown_sleep(GEMINI_COOLDOWN_SECONDS, f"publications pass for {candidate_name}")
                response = model.generate_content(prompt, generation_config={'response_mime_type': 'application/json'})
                text = getattr(response, 'text', '') or ''
                cleaned = text.strip()
                if cleaned.startswith('```'):
                    cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r'\s*```$', '', cleaned)
                start = cleaned.find('[')
                end = cleaned.rfind(']')
                if start != -1 and end != -1:
                    parsed = json.loads(cleaned[start:end + 1])
                    if isinstance(parsed, list) and len(parsed) > 0:
                        print(f"[GEMINI] + Publications second pass: {len(parsed)} items extracted")
                        return _normalize_research_outputs(parsed)
            except Exception as e:
                print(f"[GEMINI] x Publications pass attempt {attempt + 1}: {str(e)[:80]}")
                _cooldown_sleep(2 + attempt, "retry")
    return None


def parse_cv_text_to_structured(raw_text, fallback_name):
    """Parse CV text into structured data using Gemini first, then fallback rules."""
    gemini_result = _extract_with_gemini(raw_text, fallback_name)
    if gemini_result is not None:
        # If very few publications came back, do a targeted second pass
        if len(gemini_result.get('research_outputs', [])) < 5:
            print(f"[GEMINI] Only {len(gemini_result.get('research_outputs', []))} publications found — running second pass")
            pubs = _extract_publications_second_pass(raw_text, fallback_name)
            if pubs:
                gemini_result['research_outputs'] = pubs
        return gemini_result

    text = raw_text or ''
    email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
    phone_match = re.search(r'(\+?\d[\d\s\-]{8,}\d)', text)

    found_skills = _extract_skills_rule_based(text)
    parsed_name = _extract_candidate_name(text, fallback_name)
    parsed_education = _extract_education_rule_based(text)
    parsed_experience = _extract_experience_rule_based(text)
    parsed_research = _extract_research_rule_based(text)
    parsed_personal = _extract_personal_info_rule_based(text)

    return {
        'personal_info': parsed_personal,
        'name': parsed_name,
        'email': email_match.group(0) if email_match else '',
        'phone_number': phone_match.group(0).strip() if phone_match else '',
        'skills': found_skills,
        'education': parsed_education,
        'experience': parsed_experience,
        'research_outputs': parsed_research,
        'certifications': [],
        'awards': [],
        'references': [],
        'supervision': [],
        'extraction_method': 'rule-based'
    }


class CVBatchProcessor:
    """Process multiple CVs from a folder"""

    def __init__(self, input_folder='uploads', output_folder='outputs'):
        self.input_folder = input_folder
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        self.results = []

    def extract_text_from_pdf(self, filepath):
        """Extract text from PDF"""
        try:
            text = ''
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or '') + '\n'
            return text
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"

    def process_folder(self):
        """Process all PDFs in input folder"""
        pdf_files = list(Path(self.input_folder).glob('*.pdf'))
        print(f"Found {len(pdf_files)} PDF files to process")

        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file.name}")
            self.process_single_cv(pdf_file)

        return self.results

    def process_single_cv(self, filepath):
        """Process a single CV file (may contain multiple candidates).
        
        If PDF contains multiple candidates (separated by 'Candidate for the post of'),
        each is processed separately and added as individual results.
        """
        try:
            extracted_text = self.extract_text_from_pdf(str(filepath))
            chunks = _extract_all_candidate_chunks(extracted_text)
            
            file_stem = filepath.stem
            total_chunks = len(chunks)
            
            # Process each candidate chunk
            for chunk_text, chunk_index in chunks:
                try:
                    # Generate candidate name: if multiple chunks, suffix with _01, _02, etc.
                    if total_chunks > 1:
                        candidate_name = f"{file_stem}_candidate_{chunk_index + 1:02d}"
                    else:
                        candidate_name = file_stem
                    
                    structured = parse_cv_text_to_structured(chunk_text, candidate_name)
                    
                    result = {
                        'filename': filepath.name if total_chunks == 1 else f"{file_stem}_candidate_{chunk_index + 1:02d}.pdf",
                        'extraction_date': datetime.now().isoformat(),
                        'raw_text': chunk_text[:1000],
                        'status': 'extracted',
                        'structured_extraction': structured
                    }
                    
                    self.results.append(result)
                    print(f'  ✓ Candidate {chunk_index + 1}/{total_chunks} extracted successfully')
                    
                except Exception as e:
                    print(f'  ✗ Candidate {chunk_index + 1}/{total_chunks} error: {str(e)}')
                    continue
            
            return self.results if total_chunks > 0 else None

        except Exception as e:
            print(f'  ✗ Error processing file: {str(e)}')
            return None

    def save_results(self, filename='cv_extraction_results.json'):
        """Save extraction results"""
        output_path = os.path.join(self.output_folder, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {output_path}")
        return output_path

    def generate_report(self):
        """Generate processing report"""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get('status') == 'extracted')

        report = {
            'processing_date': datetime.now().isoformat(),
            'total_files': total,
            'successful': successful,
            'failed': total - successful,
            'success_rate': f"{(successful / total * 100):.1f}%" if total > 0 else '0%'
        }

        print('\n' + '=' * 50)
        print('PROCESSING REPORT')
        print('=' * 50)
        print(f"Total CVs: {report['total_files']}")
        print(f"Successful: {report['successful']}")
        print(f"Failed: {report['failed']}")
        print(f"Success Rate: {report['success_rate']}")
        print('=' * 50)

        return report


if __name__ == '__main__':
    processor = CVBatchProcessor('uploads', 'outputs')
    processor.process_folder()
    processor.save_results()
    report = processor.generate_report()

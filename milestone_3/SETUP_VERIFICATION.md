# Setup Verification

## Backend Health

```bash
curl http://127.0.0.1:5000/health
```

Expected:

```json
{
  "status": "healthy",
  "service": "TALASH Milestone 3"
}
```

## Login

```bash
curl -c cookies.txt -X POST http://127.0.0.1:5000/api/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

## Candidate List

```bash
curl -b cookies.txt http://127.0.0.1:5000/api/candidates
```

Expected:

- 43 candidates loaded from Milestone 2 data fallback
- Each candidate has a `ranking_score`

## Rubric Status

```bash
curl http://127.0.0.1:5000/api/rubric-status
```

Every item should be `true`.

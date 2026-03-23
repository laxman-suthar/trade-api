# Trade Opportunities API

A FastAPI service that analyzes Indian market sectors using live web data and Google Gemini AI. Returns structured markdown trade opportunity reports.

---

## Features

- JWT authentication
- Rate limiting (5 requests/hour per user)
- Live market data via DuckDuckGo search
- AI-powered analysis via Google Gemini
- Auto-generated Swagger docs

---

## Project Structure

```
trade_api/
├── main.py             # FastAPI app + all endpoints
├── auth.py             # JWT logic
├── rate_limiter.py     # In-memory rate limiting
├── data_collector.py   # DuckDuckGo search
├── analyzer.py         # Gemini AI integration
├── config.py           # Settings from .env
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd trade_api
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
JWT_SECRET_KEY=your-long-random-secret-key
GEMINI_API_KEY=your-gemini-api-key-here
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 5. Run the server

```bash
uvicorn main:app --reload
```

Server runs at: `http://localhost:8000`

---

## API Usage

### Step 1 — Get a JWT token

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in_minutes": 60
}
```

### Step 2 — Analyze a sector

```bash
curl http://localhost:8000/analyze/pharmaceuticals \
  -H "Authorization: Bearer eyJ..."
```

Returns a markdown report.

### Other endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/login` | No | Get JWT token |
| GET | `/analyze/{sector}` | Yes | Get trade report |
| GET | `/usage` | Yes | Check rate limit usage |

---

## Supported Sectors

`agriculture`, `automobile`, `banking`, `chemicals`, `energy`,
`finance`, `fmcg`, `healthcare`, `infrastructure`, `metals`,
`pharmaceuticals`, `real estate`, `technology`, `telecom`, `textiles`

---

## Demo Credentials

| Username | Password |
|----------|----------|
| demo | demo123 |
| admin | admin123 |

---

## Swagger Docs

Visit `http://localhost:8000/docs` after starting the server.

Click the **Authorize** button (lock icon), enter `Bearer <your_token>` to test protected endpoints directly from the browser.

---

## Rate Limits

- 5 requests per hour per user
- Response headers include `X-Requests-Used` and `X-Requests-Remaining`
- Exceeding the limit returns `429 Too Many Requests`
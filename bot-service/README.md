# Bot Service

Python 3.11 · FastAPI · LangChain · PostgreSQL

The Bot Service is the core of the Darwin AI expense tracker. It receives messages from the Connector Service, uses a LangChain + OpenAI agent to classify and extract expense data, and persists the results to PostgreSQL.

---

## Architecture

```
POST /process-message
        │
        ├─ 1. Verify JWT Bearer token
        ├─ 2. Check telegram_id against users whitelist
        ├─ 3. LangChain agent: classify + extract expense
        ├─ 4. Insert into expenses table
        └─ 5. Return reply text
```

---

## Requirements

- Python 3.11+
- PostgreSQL 14+ (or SQLite for local tests)
- An OpenAI API key

---

## Setup

### 1. Clone and enter the directory

```bash
cd bot-service
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in DATABASE_URL, OPENAI_API_KEY, JWT_SECRET
```

### 5. Run the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Documentation

With the server running, open:

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/openapi.json | Raw OpenAPI schema |

---

## Endpoints

### `GET /health`
No authentication required. Returns service status and UTC timestamp.

### `POST /process-message`
Requires `Authorization: Bearer <JWT>` header.

**Request body:**
```json
{
  "telegram_id": "123456789",
  "text": "Pizza 20 bucks"
}
```

**Response:**
```json
{
  "reply": "Food expense added ✅",
  "processed": true
}
```

---

## Running Tests

Tests use an in-memory SQLite database and a FakeLLM — no external services needed.

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Verbose
pytest -v
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `OPENAI_API_KEY` | ✅ | — | OpenAI key (`test` activates FakeLLM) |
| `JWT_SECRET` | ✅ | — | Shared secret with Connector Service |
| `OPENAI_MODEL` | ❌ | `gpt-4o-mini` | OpenAI model to use |
| `JWT_ALGORITHM` | ❌ | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | ❌ | `5` | Token lifetime in minutes |
| `ENVIRONMENT` | ❌ | `production` | `development` enables SQL echo logs |
| `HOST` | ❌ | `0.0.0.0` | Bind host |
| `PORT` | ❌ | `8000` | Bind port |

---

## Docker

```bash
docker build -t darwin-bot-service .
docker run -p 8000:8000 --env-file .env darwin-bot-service
```

---

## Seeding the Whitelist

Add a user directly via SQL:

```sql
INSERT INTO users (telegram_id) VALUES ('your-telegram-id');
```

Get your Telegram ID by messaging [@userinfobot](https://t.me/userinfobot).

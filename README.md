# Darwin AI Test  - Expense Tracker Bot

A Telegram chatbot that lets whitelisted users log expenses by sending short messages like _"Pizza 20 bucks"_. The bot classifies the expense, stores it in PostgreSQL, and replies with a confirmation.

---

## Architecture

```
User (Telegram)
      │  "Pizza 20 bucks"
      ▼
┌─────────────────────────┐
│   Connector Service     │  Node.js LTS · ESM
│   (node-telegram-bot)   │
│                         │
│  1. Receive message     │
│  2. Sign JWT            │
│  3. POST /process-msg   │
└────────────┬────────────┘
             │  Bearer <JWT>
             ▼
┌─────────────────────────┐
│     Bot Service         │  Python 3.11 · FastAPI · LangChain
│                         │
│  1. Verify JWT          │
│  2. Check whitelist     │
│  3. LLM classify+extract│
│  4. Insert to DB        │
│  5. Return reply        │
└────────────┬────────────┘
             │
             ▼
      PostgreSQL DB
  (users + expenses tables)
```

---

## Services

| Service             | Language              | Port | Description                    |
|---------------------|-----------------------|------|--------------------------------|
| `bot-service`.      | Python 3.11 / FastAPI | 8000 | LLM classification + DB writes  |
| `connector-service` | Node.js LTS / ESM     | —    | Telegram polling + HTTP bridge |

---

## Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- An API key (OpenAI, Google Gemini or Anthropic)

### 1. Configure environment files

```bash
# Bot Service
cp bot-service/.env.example bot-service/.env
# Fill in: OPENAI_API_KEY, JWT_SECRET

# Connector Service
cp connector-service/.env.example connector-service/.env
# Fill in: TELEGRAM_BOT_TOKEN, JWT_SECRET (same value as above)
```

> ⚠️ `JWT_SECRET` **must be identical** in both `.env` files.

### 2. Start all services

```bash
docker-compose up --build
```

This starts:
- PostgreSQL on port 5432
- Bot Service on port 8000 (Swagger at http://localhost:8000/docs)
- Connector Service (Telegram)

### 3. Add yourself to the whitelist

```bash
# Get your Telegram ID from @userinfobot, then:
docker-compose exec postgres psql -U darwin darwin_db \
  -c "INSERT INTO users (telegram_id) VALUES ('YOUR_TELEGRAM_ID');"
```

### 4. Send a message

Open Telegram, message your bot: `Pizza 20 bucks`

Expected reply: `Food expense added ✅`

---

## Running Tests

### Bot Service

```bash
cd bot-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

### Connector Service

```bash
cd connector-service
npm install
npm test
```

### Both (via Docker)

```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## API Documentation

With the Bot Service running, visit:

- **Swagger UI** → http://localhost:8000/docs
- **ReDoc** → http://localhost:8000/redoc

---

## Security

- All requests from the Connector to the Bot Service are authenticated with a **short-lived JWT** (HS256, 5 min TTL by default).
- The `service: "connector"` claim is verified server-side to prevent token reuse from other sources.
- Unknown Telegram users are silently ignored (no reply sent), preventing user enumeration.
- `.env` files are excluded from version control via `.gitignore`.

---

## Database Schema

```sql
CREATE TABLE users (
  "id"          SERIAL PRIMARY KEY,
  "telegram_id" text UNIQUE NOT NULL
);

CREATE TABLE expenses (
  "id"          SERIAL PRIMARY KEY,
  "user_id"     integer NOT NULL REFERENCES users("id"),
  "description" text NOT NULL,
  "amount"      money NOT NULL,
  "category"    text NOT NULL,
  "added_at"    timestamp NOT NULL
);
```

---

## Expense Categories

`Housing` · `Transportation` · `Food` · `Utilities` · `Insurance` · `Medical/Healthcare` · `Savings` · `Debt` · `Education` · `Entertainment` · `Other`

---

## Project Structure

```
darwin_ai_test/
├── bot-service/
│   ├── app/
│   │   ├── main.py          # FastAPI app + Swagger config
│   │   ├── routes.py        # Endpoints (/health, /process-message)
│   │   ├── agent.py         # LangChain expense classifier
│   │   ├── auth.py          # JWT verification dependency
│   │   ├── database.py      # Async SQLAlchemy engine + session
│   │   ├── models.py        # ORM models (User, Expense)
│   │   └── schemas.py       # Pydantic request/response schemas
│   └── tests/
│       ├── conftest.py      # Shared fixtures (FakeLLM, test DB, JWT)
│       ├── test_routes.py   # Endpoint integration tests
│       └── test_agent.py    # LangChain agent unit tests
├── connector-service/
│   ├── src/
│   │   ├── index.js         # Entry point + message handler
│   │   ├── telegram.js      # Telegram polling wrapper
│   │   ├── botService.js    # HTTP client to Bot Service
│   │   └── auth.js          # JWT token generator
│   └── tests/
│       ├── auth.test.js     # JWT generation tests
│       └── botService.test.js # HTTP client tests (fetch mocked)
├── docker-compose.yml       # Dev: all services + PostgreSQL
├── docker-compose.test.yml  # CI: ephemeral DB + test runners
└── .gitignore
```

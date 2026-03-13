# Connector Service

Node.js LTS · ESM · node-telegram-bot-api

The Connector Service is the bridge between Telegram and the Bot Service. It polls the Telegram API for new messages, forwards them to the Bot Service over HTTP (with a JWT Bearer token), and sends the reply back to the user.

---

## Architecture

```
Telegram API  (long-polling)
      │
      ▼
 src/index.js  (message handler)
      │
      ├─ src/auth.js       → generates short-lived JWT
      ├─ src/botService.js → POST /process-message to Bot Service
      └─ src/telegram.js   → sendMessage back to Telegram
```

---

## Requirements

- Node.js 20+ (LTS)
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- The Bot Service running and accessible

---

## Setup

### 1. Install dependencies

```bash
cd connector-service
npm install
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Fill in TELEGRAM_BOT_TOKEN, BOT_SERVICE_URL, and JWT_SECRET
```

> ⚠️ `JWT_SECRET` must be identical in both services.

### 3. Start the service

```bash
npm start        # Production
npm run dev      # Development (auto-restarts on file changes)
```

---

## Running Tests

No external services needed – fetch is mocked.

```bash
npm test
npm run test:coverage
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Token from @BotFather |
| `BOT_SERVICE_URL` | ✅ | — | Base URL of the Bot Service |
| `JWT_SECRET` | ✅ | — | Shared secret with Bot Service |
| `JWT_ALGORITHM` | ❌ | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | ❌ | `5` | Token lifetime in minutes |
| `ENVIRONMENT` | ❌ | `production` | Runtime environment |

---

## Docker

```bash
docker build -t darwin-connector-service .
docker run --env-file .env darwin-connector-service
```

# How to use Darwin AI Expense Tracker

This guide explains step-by-step how to configure, run, and interact with Darwin_AI_Test bot.

## 1. Prepare the Environment Files

You need to provide configuration variables to both the Python backend and the Node.js connector.

1. Go into the `bot-service` directory, open `.env.example`, and save it as `.env`.
   - Update `OPENAI_API_KEY` to your valid OpenAI key or update `GEMINI_API_KEY` to your valid Google Gemini key or update `ANTHROPIC_API_KEY` to your valid Anthropic key.
   - Set `JWT_SECRET` to a random, secure string (e.g. `my-super-duper-secret-key-12345`).

2. Go into the `connector-service` directory, open `.env.example`, and save it as `.env`.
   - Set `TELEGRAM_BOT_TOKEN` this token was sent in a separate email and is required.
   - Set `JWT_SECRET` to the **exact same string** you used in the `bot-service` (this is how they communicate securely!).

## 2. Run the Application with Docker

Make sure you have Docker Desktop running.
1. Open your terminal in the root folder of the project.
2. Build and start the cluster by running:
   ```bash
   docker-compose up --build -d
   ```
3. This will spin up three containers:
   - A PostgreSQL database (`postgres`).
   - The Python API Backend (`bot-service`).
   - The Node.js Telegram Bridge (`connector-service`).

*Wait a moment for them to initialize.*

## 3. Whitelist your Telegram Account

For security, the bot ignores messages from random users. You must register your Telegram ID in the database so the bot will reply to you.

1. Find your personal Telegram ID. (You can message a bot like [@userinfobot](https://t.me/userinfobot) on Telegram to get your ID - it's a long number like `123456789`).
2. Open your terminal in the project root and insert your user into the database manually:
   ```bash
   docker-compose exec postgres psql -U darwin darwin_db -c "INSERT INTO users (telegram_id) VALUES ('YOUR_TELEGRAM_ID_HERE');"
   ```
   *(Replace `YOUR_TELEGRAM_ID_HERE` with your actual numeric ID).*

## 4. Test the Bot

1. Open Telegram and find the bot call [@darwinbot_test_bot](https://t.me/darwinbot_test_bot).
2. Send a natural language message describing an expense. For example:
   > _"I just spent $25 on a Taxi in New York."_
3. In a matter of seconds, the Telegram bot should reply confirming that the expense was categorized and added to the database:
   > _"Transportation expense added ✅"_

## 5. Managing the Cluster

- **To view logs in real-time**: 
  ```bash
  docker-compose logs -f
  ```
- **To shut down the app**: 
  ```bash
  docker-compose down
  ```
- **To run tests**: 
  ```bash
  docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  ```

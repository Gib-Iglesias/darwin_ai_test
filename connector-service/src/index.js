/**
 * index.js – Connector Service entry point.
 *
 * Bootstraps the application:
 *  1. Loads environment variables from .env (dotenv).
 *  2. Starts Telegram polling.
 *  3. On each incoming message:
 *       a. Forward to Bot Service via HTTP (botService.js).
 *       b. If a reply is returned, send it back to the user on Telegram.
 *
 * No message is sent to Telegram if the Bot Service returns processed=false
 * (i.e. unknown user or non-expense text). This keeps the bot silent for
 * unrecognized users, preventing enumeration.
 */

import 'dotenv/config';

import { processMessage } from './botService.js';
import { sendMessage, startPolling } from './telegram.js';

/**
 * Message handler called by the Telegram polling loop.
 *
 * @param {string} telegramId - Sender's Telegram user ID.
 * @param {string} text       - Raw message text.
 * @param {number} chatId     - Chat ID to reply to.
 */
async function handleMessage(telegramId, text, chatId) {
  console.log(`[Connector] Received message from ${telegramId}: "${text}"`);

  let reply;
  try {
    // Forward to Bot Service – gets null back if the message was ignored
    reply = await processMessage(telegramId, text);
  } catch (err) {
    // Don't surface internal errors to the user; log them instead
    console.error('[Connector] Bot Service error:', err.message);
    return;
  }

  // Only reply if the Bot Service actually processed an expense
  if (reply) {
    await sendMessage(chatId, reply);
    console.log(`[Connector] Sent reply to ${telegramId}: "${reply}"`);
  } else {
    console.log(`[Connector] Message from ${telegramId} was ignored (no reply sent).`);
  }
}

// ── Start ──────────────────────────────────────────────────────────────────

console.log('[Connector] Starting Darwin AI Connector Service...');
startPolling(handleMessage);

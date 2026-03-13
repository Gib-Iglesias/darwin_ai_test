/**
 * telegram.js
 *
 * Thin wrapper around `node-telegram-bot-api` that exposes two functions:
 *  - `startPolling(onMessage)` – begins long-polling and invokes the callback
 *     for every text message received.
 *  - `sendMessage(chatId, text)` – sends a reply to a specific chat.
 *
 * Keeping Telegram logic isolated here makes it easy to swap the transport
 * (e.g. webhooks) without touching the rest of the codebase.
 */

import TelegramBot from 'node-telegram-bot-api';

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;

if (!TELEGRAM_BOT_TOKEN) {
  throw new Error('TELEGRAM_BOT_TOKEN environment variable is required.');
}

const bot = new TelegramBot(TELEGRAM_BOT_TOKEN);

/**
 * Registers a callback that fires on every incoming text message.
 *
 * @param {(telegramId: string, text: string, chatId: number) => Promise<void>} onMessage
 *   Async function called with the sender's Telegram ID, the message text,
 *   and the chat ID (used to reply).
 */
export function startPolling(onMessage) {
  bot.on('message', async (msg) => {
    console.log('[Telegram] Raw incoming message:', JSON.stringify(msg, null, 2));
    // Ignore non-text messages (photos, stickers, etc.)
    if (!msg.text) return;

    const telegramId = String(msg.from.id);
    const chatId = msg.chat.id;
    const text = msg.text;

    try {
      await onMessage(telegramId, text, chatId);
    } catch (err) {
      // Log but don't crash the polling loop
      console.error('[Telegram] Error handling message:', err.message);
    }
  });

  // Surface polling errors (network issues, invalid token, etc.)
  bot.on('polling_error', (err) => {
    console.error('[Telegram] Polling error:', err.message);
  });

  bot.startPolling();
  console.log('[Telegram] Polling started. Waiting for messages...');
}

/**
 * Sends a text message to a Telegram chat.
 *
 * @param {number} chatId  - Telegram chat ID to reply to.
 * @param {string} text    - Message text to send.
 * @returns {Promise<void>}
 */
export async function sendMessage(chatId, text) {
  await bot.sendMessage(chatId, text);
}

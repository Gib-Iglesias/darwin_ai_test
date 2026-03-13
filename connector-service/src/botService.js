/**
 * botService.js
 *
 * HTTP client that forwards Telegram messages to the Bot Service REST API.
 *
 * Responsibilities:
 *  - Generate a fresh JWT for every request (auth.js).
 *  - POST the message payload to /process-message.
 *  - Return the reply text, or null if the message was ignored.
 *  - Surface meaningful errors without crashing the polling loop.
 */

import { generateToken } from './auth.js';

const BOT_SERVICE_URL = process.env.BOT_SERVICE_URL;

if (!BOT_SERVICE_URL) {
  throw new Error('BOT_SERVICE_URL environment variable is required.');
}

/**
 * Sends a message to the Bot Service for processing.
 *
 * @param {string} telegramId  - Telegram user ID as a string.
 * @param {string} text        - Raw message text from the user.
 * @returns {Promise<string|null>} Reply text to forward to the user,
 *                                 or null if the message was silently ignored.
 * @throws {Error} If the Bot Service returns a non-200 status.
 */
export async function processMessage(telegramId, text) {
  const token = generateToken();

  const response = await fetch(`${BOT_SERVICE_URL}/process-message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // Short-lived JWT authorizes this request
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ telegram_id: telegramId, text }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(
      `Bot Service responded with ${response.status}: ${errorBody}`
    );
  }

  /** @type {{ reply: string, processed: boolean }} */
  const data = await response.json();

  // `processed: false` means the message was intentionally ignored
  // (non-whitelisted user or non-expense text). Return null so the
  // caller knows not to send any reply to Telegram.
  return data.processed ? data.reply : null;
}

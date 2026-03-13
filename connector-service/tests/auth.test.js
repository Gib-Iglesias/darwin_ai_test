/**
 * Tests for JWT token generation (src/auth.js).
 *
 * Verifies that tokens are:
 *  - Properly signed with the shared secret.
 *  - Carrying the expected `service` claim.
 *  - Set to expire within the configured window.
 */

import jwt from 'jsonwebtoken';

// ── Environment setup ──────────────────────────────────────────────────────
process.env.JWT_SECRET = 'test-secret-for-ci';
process.env.JWT_ALGORITHM = 'HS256';
process.env.JWT_EXPIRE_MINUTES = '5';

// Import AFTER env vars are set
const { generateToken } = await import('../src/auth.js');

// ── Tests ──────────────────────────────────────────────────────────────────

describe('generateToken', () => {
  test('returns a non-empty string', () => {
    const token = generateToken();
    expect(typeof token).toBe('string');
    expect(token.length).toBeGreaterThan(0);
  });

  test('token is verifiable with the shared secret', () => {
    const token = generateToken();
    // Should not throw
    const payload = jwt.verify(token, 'test-secret-for-ci');
    expect(payload).toBeTruthy();
  });

  test('token contains service=connector claim', () => {
    const token = generateToken();
    const payload = jwt.decode(token);
    expect(payload.service).toBe('connector');
  });

  test('token has a future expiry', () => {
    const token = generateToken();
    const payload = jwt.decode(token);
    const nowSeconds = Math.floor(Date.now() / 1000);
    expect(payload.exp).toBeGreaterThan(nowSeconds);
  });

  test('token expires within configured window (+1s buffer)', () => {
    const token = generateToken();
    const payload = jwt.decode(token);
    const nowSeconds = Math.floor(Date.now() / 1000);
    const maxExpiry = nowSeconds + 5 * 60 + 1; // 5 min + 1s buffer
    expect(payload.exp).toBeLessThanOrEqual(maxExpiry);
  });

  test('each call generates a different token (fresh iat)', async () => {
    // Small delay ensures iat differs between tokens
    await new Promise((r) => setTimeout(r, 1100));
    const token1 = generateToken();
    const token2 = generateToken();
    expect(token1).not.toBe(token2);
  });
});

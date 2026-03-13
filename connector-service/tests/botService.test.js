/**
 * Tests for the Bot Service HTTP client (src/botService.js).
 *
 * Uses Jest's global fetch mock to avoid real HTTP calls. Verifies:
 *  - Correct URL and method are used.
 *  - JWT Bearer token is attached to every request.
 *  - Reply text is returned when processed=true.
 *  - null is returned when processed=false.
 *  - Errors are thrown on non-200 responses.
 */

import { jest } from '@jest/globals';

// ── Environment setup ──────────────────────────────────────────────────────
process.env.JWT_SECRET = 'test-secret-for-ci';
process.env.JWT_ALGORITHM = 'HS256';
process.env.JWT_EXPIRE_MINUTES = '5';
process.env.BOT_SERVICE_URL = 'http://bot-service:8000';

// ── Mock global fetch ──────────────────────────────────────────────────────
const mockFetch = jest.fn();
global.fetch = mockFetch;

const { processMessage } = await import('../src/botService.js');

// ── Helpers ────────────────────────────────────────────────────────────────

/**
 * Creates a minimal Response-like mock.
 */
function mockResponse(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

// ── Tests ──────────────────────────────────────────────────────────────────

beforeEach(() => {
  mockFetch.mockClear();
});

describe('processMessage', () => {
  test('POSTs to the correct URL', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ reply: 'Food expense added ✅', processed: true })
    );

    await processMessage('123456789', 'Pizza 20 bucks');

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url] = mockFetch.mock.calls[0];
    expect(url).toBe('http://bot-service:8000/process-message');
  });

  test('includes Authorization Bearer header', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ reply: 'Food expense added ✅', processed: true })
    );

    await processMessage('123456789', 'Pizza 20 bucks');

    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers['Authorization']).toMatch(/^Bearer .+/);
  });

  test('sends correct JSON body', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ reply: 'Food expense added ✅', processed: true })
    );

    await processMessage('123456789', 'Pizza 20 bucks');

    const [, options] = mockFetch.mock.calls[0];
    const body = JSON.parse(options.body);
    expect(body).toEqual({ telegram_id: '123456789', text: 'Pizza 20 bucks' });
  });

  test('returns reply text when processed=true', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ reply: 'Food expense added ✅', processed: true })
    );

    const result = await processMessage('123456789', 'Pizza 20 bucks');
    expect(result).toBe('Food expense added ✅');
  });

  test('returns null when processed=false', async () => {
    mockFetch.mockResolvedValueOnce(
      mockResponse({ reply: '', processed: false })
    );

    const result = await processMessage('123456789', 'Hey how are you?');
    expect(result).toBeNull();
  });

  test('throws on non-200 response', async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ detail: 'Unauthorized' }, 401));

    await expect(processMessage('123456789', 'Pizza 20')).rejects.toThrow(
      /Bot Service responded with 401/
    );
  });
});

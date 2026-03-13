/**
 * auth.js
 *
 * Generates short-lived JWT tokens used to authenticate requests
 * from the Connector Service to the Bot Service.
 *
 * The shared secret (`JWT_SECRET`) must match the value configured
 * in the Bot Service environment. Both services use HS256 signing.
 *
 * Token payload:
 *   { service: "connector", iat: <now>, exp: <now + JWT_EXPIRE_MINUTES> }
 *
 * The `service` claim lets the Bot Service verify the token comes
 * specifically from this connector, not from any other service.
 */

import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_ALGORITHM = process.env.JWT_ALGORITHM ?? 'HS256';
const JWT_EXPIRE_MINUTES = parseInt(process.env.JWT_EXPIRE_MINUTES ?? '5', 10);

if (!JWT_SECRET) {
  throw new Error('JWT_SECRET environment variable is required.');
}

/**
 * Generates a signed JWT valid for JWT_EXPIRE_MINUTES minutes.
 *
 * A new token is created per request to ensure the `exp` claim is always
 * fresh. Token generation is cheap (pure CPU), so this adds negligible latency.
 *
 * @returns {string} Signed JWT string to use as Bearer token.
 */
export function generateToken() {
  const payload = {
    service: 'connector',
  };

  return jwt.sign(payload, JWT_SECRET, {
    algorithm: JWT_ALGORITHM,
    expiresIn: `${JWT_EXPIRE_MINUTES}m`,
  });
}

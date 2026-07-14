import { createHmac } from "crypto";

/**
 * Generates a signed token: timestamp.signature
 * The signature is HMAC-SHA256 of the timestamp using the password as the secret key.
 */
export function generateToken(password: string): string {
  const timestamp = Date.now().toString();
  const hmac = createHmac("sha256", password);
  hmac.update(timestamp);
  const signature = hmac.digest("hex");
  return `${timestamp}.${signature}`;
}

/**
 * Constant-time string comparison to prevent timing attacks.
 */
function safeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

/**
 * Verifies a signed token timestamp and signature against the site password.
 * Tokens are valid for up to 90 days.
 */
export function verifyToken(token: string | undefined, password: string): boolean {
  if (!token) return false;
  const parts = token.split(".");
  if (parts.length !== 2) return false;
  
  const [timestampStr, signature] = parts;
  const timestamp = parseInt(timestampStr, 10);
  if (isNaN(timestamp)) return false;
  
  // 7 days expiry rule
  const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
  const now = Date.now();
  if (now - timestamp > sevenDaysMs || now - timestamp < 0) {
    return false;
  }
  
  // Re-calculate signature
  const hmac = createHmac("sha256", password);
  hmac.update(timestampStr);
  const expectedSignature = hmac.digest("hex");
  
  return safeCompare(signature, expectedSignature);
}

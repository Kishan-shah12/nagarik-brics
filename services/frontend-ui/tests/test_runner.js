/**
 * Automated Test Runner - Security & Contracts
 * Validates XSS sanitization, schema constraints, and payload logic.
 * Designed to be run in Node.js or via browser console.
 */

// We simulate ES6 module imports for a standalone script execution environment.
import { sanitizeHTML, sanitizeURL, deepFreeze, CONFIG } from '../js/security.js';

let passed = 0;
let failed = 0;

/**
 * Assertion utility.
 * @param {string} desc Test description
 * @param {boolean} condition Truthy condition
 */
const assert = (desc, condition) => {
    if (condition) {
        console.log(`[PASS] ${desc}`);
        passed++;
    } else {
        console.error(`[FAIL] ${desc}`);
        failed++;
    }
};

console.log("=========================================");
console.log("STARTING AUTOMATED SECURITY & E2E TESTS");
console.log("=========================================\n");

// 1. XSS Entity Sanitization
console.log("--- Testing XSS Sanitization ---");
const maliciousPayload = `<script>alert("XSS")</script>&'`;
const sanitized = sanitizeHTML(maliciousPayload);
assert("sanitizeHTML escapes < > \" ' &", !sanitized.includes('<') && !sanitized.includes('>'));
assert("sanitizeHTML output matches entity map", sanitized === '&lt;script&gt;alert(&quot;XSS&quot;)&lt;&#x2F;script&gt;&amp;&#39;');

// 2. URL Protocol Sanitization
const maliciousUrl = "javascript:alert(document.cookie)";
const safeUrl = sanitizeURL(maliciousUrl);
assert("sanitizeURL strips javascript: protocol", safeUrl === '#');
assert("sanitizeURL preserves https: protocol", sanitizeURL("https://api.nagarikbrics.org") === "https://api.nagarikbrics.org");

// 3. Object Freezing (Prototype Pollution Defense)
console.log("\n--- Testing Prototype Defenses ---");
try {
    CONFIG.JAVA_API_URL = "http://malicious.com";
} catch (e) {} // Strict mode throws, non-strict ignores
assert("CONFIG object is deeply frozen", CONFIG.JAVA_API_URL === '/api/v1/feedback');

// 4. Schema Constraints Simulation
console.log("\n--- Testing Schema Logic (Client Side) ---");
const testTextBoundary = (text) => text.length >= CONFIG.MIN_TEXT_LENGTH && text.length <= CONFIG.MAX_TEXT_LENGTH;
assert("Rejects feedback text < 10 chars", testTextBoundary("Too short") === false);
assert("Accepts feedback text 10+ chars", testTextBoundary("This is a valid feedback text.") === true);

// 5. Payload Contract Mocking (Java -> Python Simulation)
console.log("\n--- Testing Inter-Service Contracts ---");
const mockJavaPayload = {
    feedback_id: "123e4567-e89b-12d3-a456-426614174000",
    raw_text: "पानी नहीं है",
    language: "hi",
    location_coords: { lat: 26.84, lng: 80.94 },
    country_code: "IN"
};

const validateJavaPayload = (p) => {
    return p.feedback_id.length === 36 &&
           p.location_coords.lat >= -90 && p.location_coords.lat <= 90 &&
           p.language.length >= 2;
};
assert("InternalProcessRequest payload meets Python schema validation", validateJavaPayload(mockJavaPayload) === true);

console.log("\n=========================================");
console.log(`TEST SUMMARY: ${passed} Passed, ${failed} Failed`);
console.log("=========================================");

if (typeof process !== 'undefined' && failed > 0) {
    process.exit(1);
}

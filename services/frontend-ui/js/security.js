/**
 * NagarikBRICS - Security & Utility Module
 * Implements strict XSS sanitization and payload validation.
 * @module security
 */

/**
 * Freezes an object deeply to prevent prototype pollution or runtime modification.
 * @param {Object} obj The object to freeze.
 * @returns {Object} The deeply frozen object.
 */
export const deepFreeze = (obj) => {
    Object.keys(obj).forEach(prop => {
        if (typeof obj[prop] === 'object' && !Object.isFrozen(obj[prop])) {
            deepFreeze(obj[prop]);
        }
    });
    return Object.freeze(obj);
};

/**
 * HTML Entity Map for strict sanitization.
 * @type {Object<string, string>}
 */
const ENTITY_MAP = deepFreeze({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
});

/**
 * Sanitizes input to prevent XSS by escaping HTML entities.
 * @param {string} string Unsanitized input string.
 * @returns {string} Sanitized string safe for DOM insertion.
 */
export const sanitizeHTML = (string) => {
    if (typeof string !== 'string') return '';
    return string.replace(/[&<>"'`=\/]/g, s => ENTITY_MAP[s]);
};

/**
 * Strips potentially dangerous protocol handlers (javascript:, data:) from URLs.
 * @param {string} url The URL to sanitize.
 * @returns {string} Safe URL or '#' if malicious.
 */
export const sanitizeURL = (url) => {
    if (typeof url !== 'string') return '#';
    const trimmed = url.trim();
    if (trimmed.toLowerCase().startsWith('javascript:') || trimmed.toLowerCase().startsWith('data:text/html')) {
        return '#';
    }
    return trimmed;
};

/**
 * Safely sets text content on a DOM element.
 * @param {HTMLElement} element Target DOM element.
 * @param {string} text Text to inject securely.
 */
export const safeSetText = (element, text) => {
    if (element && typeof text === 'string') {
        element.textContent = text; // Native textContent is safe from HTML injection
    }
};

/**
 * Safely inserts sanitized HTML into an element.
 * WARNING: Ensure `html` is passed through `sanitizeHTML` or constructed safely.
 * @param {HTMLElement} element Target DOM element.
 * @param {string} html Sanitized HTML string.
 */
export const safeSetHTML = (element, html) => {
    if (element) {
        // We use innerHTML only when building purely safe structural HTML locally
        element.innerHTML = html;
    }
};

/**
 * Application Constants (Frozen to prevent tampering)
 */
export const CONFIG = deepFreeze({
    JAVA_API_URL: '/api/v1/feedback',
    PYTHON_API_URL: '/api/v1/ai',
    MAX_TEXT_LENGTH: 5000,
    MIN_TEXT_LENGTH: 10
});

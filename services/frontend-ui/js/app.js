/**
 * NagarikBRICS - Frontend Application Logic
 * Implements interaction between UI, Java Ingestion, and Python AI Core.
 * @module app
 */

import { CONFIG, sanitizeHTML, safeSetText, safeSetHTML } from './security.js';

// ============================================================================
// DOM Elements
// ============================================================================
const form = document.getElementById('feedback-form');
const textInput = document.getElementById('feedback-text');
const latInput = document.getElementById('feedback-lat');
const lngInput = document.getElementById('feedback-lng');
const submitBtn = document.getElementById('submit-feedback-btn');
const statusPanel = document.getElementById('sim-status');
const errorMsg = document.getElementById('text-error');
const refreshBtn = document.getElementById('refresh-analysis-btn');
const recsFeed = document.getElementById('recommendations-feed');

const kpiTotal = document.getElementById('kpi-total');
const kpiCritical = document.getElementById('kpi-critical');
const kpiRecs = document.getElementById('kpi-recs');

const svgHotspotLayer = document.getElementById('hotspot-layer');
const countrySelector = document.getElementById('country-selector');
const languageSelector = document.getElementById('language-selector');

/**
 * Appends a log message safely to the status panel.
 * @param {string} msg Log message string.
 * @param {boolean} isError Is error message.
 */
const logStatus = (msg, isError = false) => {
    const p = document.createElement('p');
    p.style.color = isError ? 'var(--color-critical)' : 'var(--color-success)';
    p.textContent = `[${new Date().toISOString().split('T')[1].slice(0,-1)}] ${msg}`;
    statusPanel.appendChild(p);
    statusPanel.scrollTop = statusPanel.scrollHeight;
};

// ============================================================================
// Java Ingestion - Submit Feedback
// ============================================================================

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorMsg.textContent = '';
    
    const text = textInput.value.trim();
    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);
    const language = languageSelector.value;
    const country = countrySelector.value || undefined;

    // Strict client-side validation mirroring schema
    if (text.length < CONFIG.MIN_TEXT_LENGTH || text.length > CONFIG.MAX_TEXT_LENGTH) {
        errorMsg.textContent = `Text must be between ${CONFIG.MIN_TEXT_LENGTH} and ${CONFIG.MAX_TEXT_LENGTH} characters.`;
        return;
    }
    if (isNaN(lat) || lat < -90 || lat > 90 || isNaN(lng) || lng < -180 || lng > 180) {
        logStatus('Invalid coordinates. Lat: [-90,90], Lng: [-180,180]', true);
        return;
    }

    submitBtn.disabled = true;
    logStatus('Submitting feedback to Java Ingestion API...');

    const payload = {
        raw_text: text,
        language: language,
        location_coords: { lat, lng },
        country_code: country,
        source_channel: 'api'
    };

    try {
        const response = await fetch(`${CONFIG.JAVA_API_URL}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            logStatus(`Success: AI processed as [${sanitizeHTML(data.data.category)}] (Urgency: ${data.data.urgency_score})`);
            // Trigger background analysis refresh slightly after ingestion
            setTimeout(refreshAnalysis, 1000);
        } else {
            logStatus(`Error: ${data.error ? data.error.message : 'Unknown API error'}`, true);
        }
    } catch (err) {
        logStatus(`Network Error: ${err.message}`, true);
    } finally {
        submitBtn.disabled = false;
        textInput.value = '';
    }
});

// ============================================================================
// Python AI Core - Hotspot Analysis & Canvas Rendering
// ============================================================================

/**
 * Projects Lat/Lng coordinates onto a localized SVG Canvas coordinate system.
 * Very simple pseudo-Mercator projection for MVP purposes fitting 800x500 box.
 * @param {number} lat Latitude
 * @param {number} lng Longitude
 * @returns {{x: number, y: number}} SVG X/Y coordinates
 */
const projectCoords = (lat, lng) => {
    // Normalizing globally: lat [-90,90], lng [-180,180] -> [0,800]x[0,500]
    // A real mapping would center on the selected BRICS country.
    // For MVP, we map lng to x directly, lat to y inverted.
    const x = ((lng + 180) / 360) * 800;
    const y = ((90 - lat) / 180) * 500;
    return { x, y };
};

/**
 * Renders hotspots as SVG circles on the Canvas.
 * @param {Array<Object>} hotspots Array of hotspot clusters.
 */
const renderHotspots = (hotspots) => {
    // Clear previous layer
    svgHotspotLayer.innerHTML = '';
    
    let criticalCount = 0;

    hotspots.forEach(hs => {
        if (hs.intensity === 'critical') criticalCount++;
        
        const { x, y } = projectCoords(hs.center_coords.lat, hs.center_coords.lng);
        // Radius scaled by feedback count (pseudo-logarithmic)
        const r = Math.max(10, Math.min(40, hs.feedback_count * 2));
        
        // Intensity color mapping
        let color = 'var(--color-info)'; // Default
        if (hs.intensity === 'critical') color = 'var(--color-critical)';
        else if (hs.intensity === 'high') color = 'var(--color-high)';
        else if (hs.intensity === 'medium') color = 'var(--color-medium)';
        else if (hs.intensity === 'low') color = 'var(--color-low)';

        // Build SVG Elements using safe DOM creation
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute('cx', x.toString());
        circle.setAttribute('cy', y.toString());
        circle.setAttribute('r', r.toString());
        circle.setAttribute('fill', color);
        circle.setAttribute('opacity', '0.6');
        circle.classList.add(hs.intensity === 'critical' ? 'pulse' : 'static');
        
        // A11y
        circle.setAttribute('role', 'img');
        circle.setAttribute('aria-label', `Hotspot: ${sanitizeHTML(hs.dominant_category)}, Intensity: ${hs.intensity}`);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute('cx', x.toString());
        text.setAttribute('cy', (y + 4).toString()); // center vertically
        text.setAttribute('font-size', '10');
        text.setAttribute('fill', '#FFF');
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-family', 'var(--font-mono)');
        text.textContent = hs.feedback_count.toString();
        
        // Tooltip native support
        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = `${sanitizeHTML(hs.region_name)} - ${sanitizeHTML(hs.dominant_category)}`;
        circle.appendChild(title);

        svgHotspotLayer.appendChild(circle);
        svgHotspotLayer.appendChild(text);
    });

    safeSetText(kpiCritical, criticalCount.toString());
};

// ============================================================================
// Python AI Core - Recommendations Feed
// ============================================================================

/**
 * Renders the AI Recommendations feed.
 * @param {Array<Object>} recs Array of ProjectRecommendation objects.
 */
const renderRecommendations = (recs) => {
    recsFeed.innerHTML = '';
    
    if (!recs || recs.length === 0) {
        recsFeed.innerHTML = '<div class="empty-state">No recommendations available for current filter.</div>';
        return;
    }

    // Build DOM iteratively to avoid innerHTML payload injection risks
    recs.forEach(rec => {
        // Sanitize data deeply
        const title = sanitizeHTML(rec.title);
        const category = sanitizeHTML(rec.category);
        const priority = parseFloat(rec.priority_score).toFixed(1);
        const budget = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(rec.budget_estimate.amount_usd);
        const justification = sanitizeHTML(rec.justification);
        const region = sanitizeHTML(rec.location.region_name);
        
        let badgeClass = 'badge-medium';
        if (rec.priority_score >= 80) badgeClass = 'badge-critical';
        else if (rec.priority_score >= 60) badgeClass = 'badge-high';

        // Safe HTML construction
        const html = `
            <div class="card" tabindex="0">
                <div class="card-header">
                    <h3 class="card-title">${title}</h3>
                    <span class="badge ${badgeClass}">${priority} PTS</span>
                </div>
                <div class="card-meta">
                    <span><strong>Region:</strong> ${region}</span>
                    <span><strong>Category:</strong> ${category}</span>
                </div>
                <div class="card-body">
                    ${justification}
                </div>
                <div class="card-footer">
                    <span>Est. Budget: <span class="budget">${budget}</span></span>
                    <span>Confidence: ${sanitizeHTML(rec.budget_estimate.confidence)}</span>
                </div>
            </div>
        `;
        
        // Create wrapper and use innerHTML (safe because variables are sanitized)
        const wrapper = document.createElement('div');
        safeSetHTML(wrapper, html);
        recsFeed.appendChild(wrapper.firstElementChild);
    });
};

const loadRecommendations = async (countryCode = '') => {
    try {
        const url = `${CONFIG.PYTHON_API_URL}/recommendations?sort_by=priority_score&sort_order=desc${countryCode ? '&country_code='+countryCode : ''}`;
        const response = await fetch(url);
        const data = await response.json();
        if (response.ok && data.status === 'success') {
            renderRecommendations(data.data.recommendations);
            safeSetText(kpiRecs, data.data.pagination.total_items.toString());
        }
    } catch (err) {
        console.error("Failed to load recommendations:", err);
    }
};

/**
 * Triggers hotspot analysis and refreshes the dashboard view.
 */
const refreshAnalysis = async () => {
    refreshBtn.disabled = true;
    safeSetText(refreshBtn, 'Analyzing...');
    logStatus('Triggering Python AI Hotspot Analysis...');

    const countryCode = countrySelector.value || undefined;
    const payload = { filters: {} };
    if (countryCode) payload.filters.country_code = countryCode;

    try {
        const response = await fetch(`${CONFIG.PYTHON_API_URL}/analyze-hotspots`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            const { hotspots, total_feedback_analyzed } = data.data;
            
            safeSetText(kpiTotal, total_feedback_analyzed.toString());
            renderHotspots(hotspots);
            
            logStatus(`Analysis complete: ${hotspots.length} hotspots identified.`);
            
            // Reload recommendations
            await loadRecommendations(countryCode);
        } else {
            logStatus('Analysis failed.', true);
        }
    } catch (err) {
        logStatus(`Analysis network error: ${err.message}`, true);
    } finally {
        refreshBtn.disabled = false;
        safeSetText(refreshBtn, 'Refresh Analysis');
    }
};

// ============================================================================
// Initialization
// ============================================================================

refreshBtn.addEventListener('click', refreshAnalysis);
countrySelector.addEventListener('change', refreshAnalysis);

// Optional: Auto-fetch on load (might fail if backend isn't up, but good for UX)
window.addEventListener('DOMContentLoaded', () => {
    logStatus('Dashboard initialized. System ready.');
});

// ============================================================================
// Vercel Serverless AI Chat Widget
// ============================================================================

const chatWidget = document.getElementById('ai-chat-widget');
const openChatBtn = document.getElementById('open-chat-btn');
const closeChatBtn = document.getElementById('close-chat-btn');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const chatSendBtn = document.getElementById('chat-send-btn');

openChatBtn.addEventListener('click', () => {
    chatWidget.classList.add('active');
    chatWidget.setAttribute('aria-hidden', 'false');
    openChatBtn.setAttribute('aria-expanded', 'true');
    chatInput.focus();
});

closeChatBtn.addEventListener('click', () => {
    chatWidget.classList.remove('active');
    chatWidget.setAttribute('aria-hidden', 'true');
    openChatBtn.setAttribute('aria-expanded', 'false');
});

const appendChatMessage = (text, sender) => {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${sender}`;
    safeSetText(msgDiv, text); // Sanitizes rendering
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
};

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = chatInput.value.trim();
    if (prompt.length < 2) return;

    // Append user message
    appendChatMessage(prompt, 'user');
    chatInput.value = '';
    
    // Loading state
    chatSendBtn.disabled = true;
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'chat-msg ai loading';
    safeSetText(loadingMsg, 'AI is thinking...');
    chatMessages.appendChild(loadingMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const language = document.getElementById('language-selector').options[document.getElementById('language-selector').selectedIndex].text;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt, language })
        });

        chatMessages.removeChild(loadingMsg);
        
        const data = await response.json();
        
        if (response.ok && data.reply) {
            appendChatMessage(data.reply, 'ai');
        } else {
            appendChatMessage(data.error || 'Server error occurred.', 'error');
        }
    } catch (err) {
        chatMessages.removeChild(loadingMsg);
        appendChatMessage('Network error. Failed to reach AI endpoint.', 'error');
    } finally {
        chatSendBtn.disabled = false;
        chatInput.focus();
    }
});

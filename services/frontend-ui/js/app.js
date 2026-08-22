/**
 * Civic Connect - Frontend Application Logic
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
const refreshBtn = document.getElementById('refresh-analysis-btn');

const kpiTotal = document.getElementById('kpi-total');
const kpiCritical = document.getElementById('kpi-critical');
const kpiRecs = document.getElementById('kpi-recs');

const svgHotspotLayer = document.getElementById('hotspot-layer');
const feedbackTableBody = document.getElementById('feedback-table-body');
const recommendationsTableBody = document.getElementById('recommendations-table-body');

/**
 * Appends a log message safely to the status panel.
 * @param {string} msg Log message string.
 * @param {boolean} isError Is error message.
 */
const logStatus = (msg, isError = false) => {
    const p = document.createElement('div');
    p.style.color = isError ? 'var(--color-critical)' : 'var(--color-low)';
    p.style.fontSize = '0.75rem';
    p.textContent = `[${new Date().toISOString().split('T')[1].slice(0,-1)}] ${msg}`;
    statusPanel.appendChild(p);
    statusPanel.scrollTop = statusPanel.scrollHeight;
};

// ============================================================================
// Java Ingestion - Submit Feedback
// ============================================================================

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const text = textInput.value.trim();
    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);
    
    // Grab the active language from the toggles
    const activeLangBtn = document.querySelector('.lang-btn.active');
    const language = activeLangBtn ? activeLangBtn.textContent.toLowerCase() : 'en';
    
    const country = 'IN'; // Hardcoded to India for this demo

    if (text.length < CONFIG.MIN_TEXT_LENGTH || text.length > CONFIG.MAX_TEXT_LENGTH) {
        logStatus(`Text must be between ${CONFIG.MIN_TEXT_LENGTH} and ${CONFIG.MAX_TEXT_LENGTH} chars.`, true);
        return;
    }

    submitBtn.disabled = true;
    logStatus('Submitting feedback...');

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
            logStatus(`Success: [${sanitizeHTML(data.data.category)}] (Urgency: ${data.data.urgency_score})`);
            // Trigger background analysis refresh slightly after ingestion
            setTimeout(refreshAnalysis, 1000);
        } else {
            logStatus(`API Error: ${JSON.stringify(data)}`, true);
        }
    } catch (err) {
        logStatus(`Network Error: ${err.message}`, true);
    } finally {
        submitBtn.disabled = false;
        textInput.value = '';
    }
});

// ============================================================================
// Map rendering
// ============================================================================
const projectCoords = (lat, lng) => {
    const x = ((lng + 180) / 360) * 800;
    const y = ((90 - lat) / 180) * 400; // SVG height is 400
    return { x, y };
};

const renderHotspots = (hotspots) => {
    svgHotspotLayer.innerHTML = '';
    let criticalCount = 0;

    hotspots.forEach(hs => {
        if (hs.intensity === 'critical') criticalCount++;
        const { x, y } = projectCoords(hs.center_coords.lat, hs.center_coords.lng);
        const r = Math.max(10, Math.min(40, hs.feedback_count * 2));
        
        let color = 'var(--color-info)'; 
        if (hs.intensity === 'critical') color = 'var(--color-critical)';
        else if (hs.intensity === 'high') color = 'var(--color-high)';
        else if (hs.intensity === 'medium') color = 'var(--color-medium)';
        else if (hs.intensity === 'low') color = 'var(--color-low)';

        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute('cx', x.toString());
        circle.setAttribute('cy', y.toString());
        circle.setAttribute('r', r.toString());
        circle.setAttribute('fill', color);
        circle.setAttribute('opacity', '0.6');
        
        const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
        title.textContent = `${sanitizeHTML(hs.region_name)} - ${sanitizeHTML(hs.dominant_category)}`;
        circle.appendChild(title);

        svgHotspotLayer.appendChild(circle);
    });

    safeSetText(kpiCritical, criticalCount.toString());
};

// ============================================================================
// Tables rendering
// ============================================================================
const renderRecommendations = (recs) => {
    recommendationsTableBody.innerHTML = '';
    if (!recs || recs.length === 0) {
        recommendationsTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:#999">No projects generated yet.</td></tr>';
        return;
    }

    recs.forEach(rec => {
        const title = sanitizeHTML(rec.title);
        const status = sanitizeHTML(rec.status);
        const score = rec.priority_score.toFixed(1);
        
        let statusClass = 'status-planned';
        if (status.toLowerCase().includes('progress')) statusClass = 'status-progress';
        if (status.toLowerCase().includes('complete')) statusClass = 'status-complete';

        const tr = document.createElement('tr');
        
        const tdTitle = document.createElement('td');
        tdTitle.textContent = title;
        
        const tdStatus = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = `status-badge ${statusClass}`;
        badge.textContent = status;
        tdStatus.appendChild(badge);
        
        const tdScore = document.createElement('td');
        tdScore.innerHTML = `<strong>${score}</strong>
            <div class="progress-track"><div class="progress-fill" style="width:${Math.min(100, score)}%"></div></div>`;
            
        tr.appendChild(tdTitle);
        tr.appendChild(tdStatus);
        tr.appendChild(tdScore);
        
        recommendationsTableBody.appendChild(tr);
    });
};

const fetchAndRenderFeedback = async () => {
    // For MVP, we will simulate the Recent Feedback table with mock data or just leave it empty 
    // unless we implement a GET endpoint for raw feedback.
    feedbackTableBody.innerHTML = `
        <tr>
            <td>WhatsApp</td>
            <td>Better Roads needed in our village immediately.</td>
            <td><span class="tag">Roads</span></td>
            <td><span class="urgency-indicator high">!</span></td>
        </tr>
        <tr>
            <td>SMS</td>
            <td>Water supply is highly irregular.</td>
            <td><span class="tag">Water</span></td>
            <td><span class="urgency-indicator medium">!</span></td>
        </tr>
    `;
};

// ============================================================================
// Orchestration
// ============================================================================

const refreshAnalysis = async () => {
    const country = 'IN';
    logStatus('Triggering Python AI Hotspot Analysis...');
    refreshBtn.disabled = true;

    try {
        const hsRes = await fetch(`${CONFIG.PYTHON_API_URL}/analyze-hotspots`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filters: { country_code: country } })
        });
        const hsData = await hsRes.json();

        if (hsRes.ok && hsData.data) {
            safeSetText(kpiTotal, hsData.data.total_feedback_analyzed.toString());
            renderHotspots(hsData.data.hotspots || []);
            logStatus(`Analysis complete: ${hsData.data.hotspots.length} hotspots identified.`);
        } else {
            logStatus(`Hotspot Analysis failed.`, true);
        }

        const recRes = await fetch(`${CONFIG.PYTHON_API_URL}/recommendations?country_code=${country}`);
        const recData = await recRes.json();

        if (recRes.ok && recData.data) {
            const totalRecs = recData.data.pagination ? recData.data.pagination.total_items : (recData.data.total_count || 0);
            safeSetText(kpiRecs, totalRecs.toString());
            renderRecommendations(recData.data.recommendations || []);
        } else {
            logStatus(`Recommendations failed.`, true);
        }

        fetchAndRenderFeedback();

    } catch (err) {
        logStatus(`Analysis failed: ${err.message}`, true);
    } finally {
        refreshBtn.disabled = false;
    }
};

refreshBtn.addEventListener('click', refreshAnalysis);

// ============================================================================
// AI Chat Widget
// ============================================================================
const chatWidget = document.getElementById('ai-chat-widget');
const openChatBtn = document.getElementById('open-chat-btn');
const closeChatBtn = document.getElementById('close-chat-btn');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');

openChatBtn.addEventListener('click', () => chatWidget.style.display = 'flex');
closeChatBtn.addEventListener('click', () => chatWidget.style.display = 'none');

const appendChatMessage = (text, sender) => {
    const div = document.createElement('div');
    div.className = `chat-msg ${sender}`;
    div.style.padding = '0.75rem';
    div.style.borderRadius = '8px';
    div.style.background = sender === 'user' ? 'var(--color-brand-light)' : '#f1f1f1';
    div.style.color = sender === 'user' ? 'var(--color-brand-blue)' : '#333';
    div.style.alignSelf = sender === 'user' ? 'flex-end' : 'flex-start';
    div.style.maxWidth = '85%';
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
};

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = chatInput.value.trim();
    if (!prompt) return;

    appendChatMessage(prompt, 'user');
    chatInput.value = '';

    const activeLangBtn = document.querySelector('.lang-btn.active');
    const language = activeLangBtn ? activeLangBtn.textContent.toLowerCase() : 'en';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, language })
        });
        
        const data = await response.json();
        
        if (response.ok && data.reply) {
            appendChatMessage(data.reply, 'ai');
        } else {
            appendChatMessage('Server error occurred.', 'error');
        }
    } catch (err) {
        appendChatMessage('Network error. Failed to reach AI endpoint.', 'error');
    }
});

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    logStatus('Dashboard initialized. System ready.');
    refreshAnalysis();
    
    // Lang toggles logic
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
        });
    });
});

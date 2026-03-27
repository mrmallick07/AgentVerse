/**
 * AgentVerse — Frontend Application Logic
 * Handles chat, SSE streaming, agent activity visualization, and results panel.
 */

// ============ State ============
let sessionId = null;
let isProcessing = false;

// ============ DOM References ============
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const activityFeed = document.getElementById('activity-feed');
const activeAgentCount = document.getElementById('active-agent-count');

// Results
const docsSection = document.getElementById('docs-section');
const docsList = document.getElementById('docs-list');
const eventsSection = document.getElementById('events-section');
const eventsList = document.getElementById('events-list');
const researchSection = document.getElementById('research-section');
const researchList = document.getElementById('research-list');
const resultsEmpty = document.getElementById('results-empty');

// ============ Auto-resize textarea ============
chatInput.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

chatInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ============ Use Example Prompt ============
function useExample(btn) {
    const textEl = btn.querySelector('.example-text');
    const text = textEl ? textEl.textContent : btn.textContent;
    chatInput.value = text.trim();
    chatInput.focus();
    chatInput.dispatchEvent(new Event('input'));

    // Hide welcome and examples on first use
    const hero = document.querySelector('.welcome-hero');
    const grid = document.querySelector('.examples-grid');
    if (hero) hero.style.display = 'none';
    if (grid) grid.style.display = 'none';
}

// ============ Send Message ============
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message || isProcessing) return;

    isProcessing = true;
    sendBtn.disabled = true;
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Add user message to chat
    addMessage(message, 'user');

    // Add typing indicator
    const typingEl = addTypingIndicator();

    // Clear previous agent states
    resetAgentCards();
    addFeedItem('User sent a request', 'info');

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
            }),
        });

        // Get session ID from response header
        const newSessionId = response.headers.get('X-Session-Id');
        if (newSessionId) sessionId = newSessionId;

        // Read SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let currentAgentMessage = null;
        let currentAgentText = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const jsonStr = line.slice(6).trim();
                if (!jsonStr) continue;

                try {
                    const event = JSON.parse(jsonStr);
                    handleStreamEvent(event, typingEl, () => {
                        if (!currentAgentMessage) {
                            // Remove typing indicator and create agent message
                            if (typingEl.parentNode) typingEl.remove();
                            currentAgentMessage = addMessage('', 'agent', true);
                        }
                        return currentAgentMessage;
                    });

                    if (event.type === 'text') {
                        if (!currentAgentMessage) {
                            if (typingEl.parentNode) typingEl.remove();
                            currentAgentMessage = addMessage('', 'agent', true);
                        }
                        currentAgentText += event.content;
                        const contentEl = currentAgentMessage.querySelector('.message-text');
                        if (contentEl) {
                            contentEl.innerHTML = formatMarkdown(currentAgentText);
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }
                    }

                    if (event.type === 'done') {
                        if (typingEl.parentNode) typingEl.remove();
                        resetAgentCards();
                        addFeedItem('✅ Request completed', 'success');
                    }

                    if (event.type === 'error') {
                        if (typingEl.parentNode) typingEl.remove();
                        if (!currentAgentMessage) {
                            currentAgentMessage = addMessage('', 'agent', true);
                        }
                        const contentEl = currentAgentMessage.querySelector('.message-text');
                        if (contentEl) {
                            contentEl.innerHTML = `<span style="color: var(--red);">Error: ${event.content}</span>`;
                        }
                        addFeedItem(`❌ Error: ${event.content}`, 'error');
                    }
                } catch (e) {
                    // Skip unparseable lines
                }
            }
        }
    } catch (error) {
        if (typingEl.parentNode) typingEl.remove();
        addMessage(`Connection error: ${error.message}. Make sure the server is running.`, 'agent');
        addFeedItem(`❌ Connection error`, 'error');
    }

    isProcessing = false;
    sendBtn.disabled = false;
    chatInput.focus();
}

// ============ Handle Stream Events ============
function handleStreamEvent(event, typingEl, getMessageEl) {
    switch (event.type) {
        case 'agent_activity':
            activateAgent(event.agent);
            addFeedItem(`🤖 ${event.agent} activated`, 'agent');
            break;

        case 'tool_call':
            activateAgent(event.agent);
            setAgentStatus(event.agent, `Calling ${event.tool}...`);
            addFeedItem(`🔧 ${event.agent} → ${event.tool}`, 'tool');

            // Extract results for the right panel
            extractResultFromToolCall(event);
            break;

        case 'tool_response':
            const statusIcon = event.status === 'success' ? '✅' : '⚠️';
            addFeedItem(`${statusIcon} ${event.tool} → ${event.status}`, event.status === 'success' ? 'success' : 'error');
            break;
    }
}

// ============ Extract Results from Tool Calls ============
function extractResultFromToolCall(event) {
    const tool = event.tool;
    const args = event.args || '';

    if (tool === 'create_document') {
        // Will populate from the text response (URL extraction)
    }

    if (tool === 'create_calendar_event') {
        // Will populate from the text response
    }
}

// ============ Agent Card Management ============
function activateAgent(agentName) {
    // Map agent names to card IDs
    const agentMap = {
        'OrchestratorAgent': 'agent-orchestrator',
        'ResearchAgent': 'agent-research',
        'AnalystAgent': 'agent-analyst',
        'PlannerAgent': 'agent-planner',
        'WriterAgent': 'agent-writer',
    };

    const cardId = agentMap[agentName];
    if (!cardId) return;

    const card = document.getElementById(cardId);
    if (card) {
        card.classList.add('active');
        setAgentStatus(agentName, 'Working...');
    }

    updateActiveCount();
}

function setAgentStatus(agentName, status) {
    const agentMap = {
        'OrchestratorAgent': 'agent-orchestrator',
        'ResearchAgent': 'agent-research',
        'AnalystAgent': 'agent-analyst',
        'PlannerAgent': 'agent-planner',
        'WriterAgent': 'agent-writer',
    };

    const cardId = agentMap[agentName];
    if (!cardId) return;

    const card = document.getElementById(cardId);
    if (card) {
        const statusEl = card.querySelector('.agent-status');
        if (statusEl) statusEl.textContent = status;
    }
}

function resetAgentCards() {
    document.querySelectorAll('.agent-card').forEach(card => {
        card.classList.remove('active');
        card.querySelector('.agent-status').textContent = 'Idle';
    });
    updateActiveCount();
}

function updateActiveCount() {
    const count = document.querySelectorAll('.agent-card.active').length;
    activeAgentCount.textContent = `${count} active`;
}

// ============ Activity Feed ============
function addFeedItem(text, type = 'info') {
    const now = new Date();
    const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });

    const item = document.createElement('div');
    item.className = `feed-item feed-${type}`;
    item.innerHTML = `
        <span class="feed-time">${time}</span>
        <span class="feed-text">${text}</span>
    `;

    activityFeed.insertBefore(item, activityFeed.firstChild);

    // Limit feed items
    while (activityFeed.children.length > 50) {
        activityFeed.removeChild(activityFeed.lastChild);
    }
}

// ============ Chat Messages ============
function addMessage(text, type, streaming = false) {
    const msg = document.createElement('div');
    msg.className = `message ${type}-message`;

    let avatar = '🌌';
    if (type === 'user') avatar = '👤';
    if (type === 'agent') avatar = '🧠';

    msg.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-text">${streaming ? '' : formatMarkdown(text)}</div>
        </div>
    `;

    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msg;
}

function addTypingIndicator() {
    const msg = document.createElement('div');
    msg.className = 'message agent-message typing-msg';
    msg.innerHTML = `
        <div class="message-avatar">🧠</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msg;
}

// ============ Markdown Formatting ============
function formatMarkdown(text) {
    if (!text) return '';

    let html = text
        // Headers
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        // Bold and Italic
        .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // Links
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
        // Raw URLs
        .replace(/(https?:\/\/[^\s<]+)/g, (match, url) => {
            // Don't double-wrap already linked URLs
            if (text.indexOf(`(${url})`) !== -1 || text.indexOf(`"${url}"`) !== -1) return match;
            return `<a href="${url}" target="_blank" rel="noopener">${url}</a>`;
        })
        // Unordered lists
        .replace(/^[\-\*] (.+)$/gm, '<li>$1</li>')
        // Numbered lists
        .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');

    // Wrap in paragraph
    html = '<p>' + html + '</p>';

    // Wrap consecutive <li> in <ul>
    html = html.replace(/(<li>.*?<\/li>(?:<br>)?)+/g, (match) => {
        return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
    });

    // Extract any Google Docs or Calendar links for the results panel
    extractLinksForResults(text);

    return html;
}

// ============ Extract Links for Results Panel ============
function extractLinksForResults(text) {
    // Google Docs links
    const docsRegex = /https:\/\/docs\.google\.com\/document\/d\/[^\s)<]+/g;
    const docsMatches = text.match(docsRegex);
    if (docsMatches) {
        resultsEmpty.style.display = 'none';
        docsSection.style.display = 'block';
        docsMatches.forEach(url => {
            if (!docsList.querySelector(`[href="${url}"]`)) {
                const card = document.createElement('a');
                card.className = 'result-card';
                card.href = url;
                card.target = '_blank';
                card.innerHTML = `
                    <div class="result-type doc">Google Doc</div>
                    <h4>📄 Created Document</h4>
                    <p>Click to open in Google Docs</p>
                `;
                docsList.appendChild(card);
            }
        });
    }

    // Google Calendar links
    const calRegex = /https:\/\/www\.google\.com\/calendar\/event\?[^\s)<]+/g;
    const calMatches = text.match(calRegex);
    if (calMatches) {
        resultsEmpty.style.display = 'none';
        eventsSection.style.display = 'block';
        calMatches.forEach(url => {
            if (!eventsList.querySelector(`[href="${url}"]`)) {
                const card = document.createElement('a');
                card.className = 'result-card';
                card.href = url;
                card.target = '_blank';
                card.innerHTML = `
                    <div class="result-type event">Calendar Event</div>
                    <h4>📅 Scheduled Event</h4>
                    <p>Click to view in Google Calendar</p>
                `;
                eventsList.appendChild(card);
            }
        });
    }

    // YouTube links
    const ytRegex = /https:\/\/www\.youtube\.com\/watch\?v=[^\s)<]+/g;
    const ytMatches = text.match(ytRegex);
    if (ytMatches) {
        resultsEmpty.style.display = 'none';
        researchSection.style.display = 'block';
        ytMatches.forEach(url => {
            if (!researchList.querySelector(`[href="${url}"]`)) {
                const card = document.createElement('a');
                card.className = 'result-card';
                card.href = url;
                card.target = '_blank';
                card.innerHTML = `
                    <div class="result-type source">YouTube</div>
                    <h4>🎬 Video Source</h4>
                    <p>${url}</p>
                `;
                researchList.appendChild(card);
            }
        });
    }
}

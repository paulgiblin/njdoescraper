const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000';
let ws;

// UI Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const pauseBtn = document.getElementById('pauseBtn');
const rateLimitInput = document.getElementById('rateLimit');
const setRateBtn = document.getElementById('setRateBtn');
const pagesCrawledSpan = document.getElementById('pagesCrawled');
const pagesQueuedSpan = document.getElementById('pagesQueued');
const currentUrlSpan = document.getElementById('currentUrl');
const startTimeSpan = document.getElementById('startTime');
const errorLogDiv = document.getElementById('errorLog');

// WebSocket Connection
function connectWebSocket() {
    const wsUrl = API_BASE_URL.replace('http', 'ws');
    ws = new WebSocket(`${wsUrl}/ws`);
    
    ws.onmessage = (event) => {
        const stats = JSON.parse(event.data);
        updateStats(stats);
    };

    ws.onclose = () => {
        setTimeout(connectWebSocket, 1000); // Reconnect after 1 second
    };
}

// Update Statistics
function updateStats(stats) {
    pagesCrawledSpan.textContent = stats.pages_crawled;
    pagesQueuedSpan.textContent = stats.pages_queued;
    currentUrlSpan.textContent = stats.current_url || '-';
    
    if (stats.start_time) {
        const startTime = new Date(stats.start_time);
        startTimeSpan.textContent = startTime.toLocaleString();
    }

    // Update error log
    if (stats.errors && stats.errors.length > 0) {
        const newErrors = stats.errors.filter(error => {
            const errorElement = document.querySelector(`[data-error="${error}"]`);
            return !errorElement;
        });

        newErrors.forEach(error => {
            const errorDiv = document.createElement('div');
            errorDiv.textContent = `[${new Date().toLocaleTimeString()}] ${error}`;
            errorDiv.setAttribute('data-error', error);
            errorDiv.className = 'text-red-600 mb-1';
            errorLogDiv.appendChild(errorDiv);
        });

        // Auto-scroll to bottom
        errorLogDiv.scrollTop = errorLogDiv.scrollHeight;
    }
}

// API Calls
async function makeRequest(endpoint, method = 'POST', body = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        const errorDiv = document.createElement('div');
        errorDiv.textContent = `[${new Date().toLocaleTimeString()}] API Error: ${error.message}`;
        errorDiv.className = 'text-red-600 mb-1';
        errorLogDiv.appendChild(errorDiv);
    }
}

// Event Listeners
startBtn.addEventListener('click', () => makeRequest('/start'));
stopBtn.addEventListener('click', () => makeRequest('/stop'));
pauseBtn.addEventListener('click', async () => {
    const result = await makeRequest('/pause');
    pauseBtn.textContent = result.status === 'paused' ? 'Resume' : 'Pause';
});

setRateBtn.addEventListener('click', () => {
    const rate = parseFloat(rateLimitInput.value);
    if (rate >= 0.1) {
        makeRequest('/rate-limit', 'POST', { rate });
    }
});

// Initialize WebSocket connection
connectWebSocket();

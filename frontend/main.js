// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const rateLimitInput = document.getElementById('rateLimit');
    const statusDisplay = document.getElementById('status');
    const pagesCrawledDisplay = document.getElementById('pagesCrawled');
    const pdfsFoundDisplay = document.getElementById('pdfsFound');
    const pdfsDownloadedDisplay = document.getElementById('pdfsDownloaded');
    const currentUrlDisplay = document.getElementById('currentUrl');
    const logContainer = document.getElementById('logContainer');
    const logEntries = document.getElementById('logEntries');

    // API Configuration
    const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000';
    const WS_URL = API_BASE_URL.replace('http', 'ws') + '/ws';

    let ws = null;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 5;

    // Maximum number of log entries to keep
    const MAX_LOG_ENTRIES = 1000;

    // WebSocket Connection
    function connectWebSocket() {
        if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            console.error('Max reconnection attempts reached');
            return;
        }

        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'log') {
                addLogEntry(data.data);
            } else {
                updateStats(data);
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setTimeout(() => {
                reconnectAttempts++;
                connectWebSocket();
            }, 2000);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    // Update UI with crawler stats
    function updateStats(data) {
        pagesCrawledDisplay.textContent = data.pages_crawled;
        pdfsFoundDisplay.textContent = data.pdfs_found;
        pdfsDownloadedDisplay.textContent = data.pdfs_downloaded || 0;
        currentUrlDisplay.textContent = data.current_url || 'Not crawling';
        statusDisplay.textContent = data.status;

        // Update button states
        updateButtonStates(data.status);
    }

    // Update button states based on crawler status
    function updateButtonStates(status) {
        startBtn.disabled = status === 'running';
        stopBtn.disabled = status === 'stopped';
        pauseBtn.disabled = status === 'stopped';
        
        // Update pause button text
        if (status === 'paused') {
            pauseBtn.textContent = 'Resume';
        } else {
            pauseBtn.textContent = 'Pause';
        }
    }

    function addLogEntry(logMessage) {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.textContent = logMessage;
        
        logEntries.appendChild(entry);
        
        // Remove old entries if we exceed the maximum
        while (logEntries.children.length > MAX_LOG_ENTRIES) {
            logEntries.removeChild(logEntries.firstChild);
        }
        
        // Auto-scroll to bottom
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    // API Calls
    async function startCrawler() {
        try {
            const response = await fetch(`${API_BASE_URL}/start`, {
                method: 'POST'
            });
            const data = await response.json();
            console.log('Crawler started:', data);
        } catch (error) {
            console.error('Error starting crawler:', error);
        }
    }

    async function stopCrawler() {
        try {
            const response = await fetch(`${API_BASE_URL}/stop`, {
                method: 'POST'
            });
            const data = await response.json();
            console.log('Crawler stopped:', data);
        } catch (error) {
            console.error('Error stopping crawler:', error);
        }
    }

    async function togglePause() {
        try {
            const response = await fetch(`${API_BASE_URL}/pause`, {
                method: 'POST'
            });
            const data = await response.json();
            console.log('Crawler pause toggled:', data);
        } catch (error) {
            console.error('Error toggling pause:', error);
        }
    }

    async function updateRateLimit() {
        const rate = parseFloat(rateLimitInput.value);
        if (isNaN(rate) || rate < 0) {
            alert('Please enter a valid rate limit (seconds)');
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/rate-limit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ rate_limit: rate })
            });
            const data = await response.json();
            console.log('Rate limit updated:', data);
        } catch (error) {
            console.error('Error updating rate limit:', error);
        }
    }

    // Event Listeners
    startBtn.addEventListener('click', startCrawler);
    stopBtn.addEventListener('click', stopCrawler);
    pauseBtn.addEventListener('click', togglePause);
    rateLimitInput.addEventListener('change', updateRateLimit);

    // Initialize WebSocket connection
    connectWebSocket();
});

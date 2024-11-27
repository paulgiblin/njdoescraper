let ws;
let isRunning = false;
let isPaused = false;

// Tree visualization state
let treeData = { nodes: [], links: [] };
let root = null;

function processDataForTree(data) {
    // Create a map of all nodes
    const nodesMap = new Map(data.nodes.map(node => [node.id, { ...node, children: [] }]));
    
    // Build parent-child relationships
    data.links.forEach(link => {
        const source = nodesMap.get(link.source);
        const target = nodesMap.get(link.target);
        if (source && target) {
            source.children.push(target);
        }
    });
    
    // Find the root node (the one with no incoming links)
    const targetIds = new Set(data.links.map(link => link.target));
    const rootNode = Array.from(nodesMap.values()).find(node => !targetIds.has(node.id));
    
    return rootNode || { id: "No Data", name: "No Data", children: [] };
}

function initVisualization() {
    // Clear existing visualization
    d3.select("#tree-container").selectAll("*").remove();
}

function createNode(d, isRoot = false, level = 0) {
    const node = document.createElement("div");
    node.className = "node";
    if (isRoot) {
        node.classList.add("root");
    }
    
    const content = document.createElement("div");
    content.className = "node-content";
    
    if (d.children?.length) {
        const toggle = document.createElement("span");
        toggle.className = "node-toggle";
        toggle.textContent = "+";
        toggle.onclick = (e) => {
            e.stopPropagation();
            const nodeElement = e.target.closest(".node");
            const childrenContainer = nodeElement.querySelector(".node-children");
            if (childrenContainer) {
                const isExpanded = nodeElement.classList.toggle("expanded");
                e.target.textContent = isExpanded ? "−" : "+";
            }
        };
        content.appendChild(toggle);
    } else {
        // Add empty toggle space for alignment
        const spacer = document.createElement("span");
        spacer.className = "node-toggle";
        spacer.style.visibility = "hidden";
        content.appendChild(spacer);
    }
    
    const label = document.createElement("span");
    label.className = "node-label";
    if (isRoot) {
        label.textContent = d.id;
        label.classList.add("root-label");
    } else {
        try {
            const url = new URL(d.id);
            let displayName = url.pathname;
            displayName = displayName.replace(/\/$/, "");
            displayName = displayName.split('/').pop();
            displayName = decodeURIComponent(displayName);
            if (!displayName) {
                displayName = url.hostname;
            }
            label.textContent = displayName;
            label.title = d.id;
        } catch (e) {
            label.textContent = d.name || d.id;
        }
    }
    
    const type = document.createElement("span");
    type.className = `node-type ${d.type}`;
    if (d.type === 'pdf') {
        type.textContent = 'PDF';
    }
    
    content.appendChild(label);
    content.appendChild(type);
    node.appendChild(content);
    
    if (d.children?.length) {
        const childrenContainer = document.createElement("div");
        childrenContainer.className = "node-children";
        d.children.forEach(child => {
            childrenContainer.appendChild(createNode(child, false));
        });
        node.appendChild(childrenContainer);
    }
    
    return node;
}

function updateVisualization(data) {
    if (!data.nodes.length) return;
    
    // Process the data into a hierarchical structure
    root = processDataForTree(data);
    
    // Clear and initialize the container
    const container = d3.select("#tree-container");
    container.selectAll("*").remove();
    
    // Create a wrapper for the tree content
    const wrapper = container.append("div")
        .attr("class", "tree-wrapper");
    
    // Create and append the tree structure, passing isRoot=true for the root node
    wrapper.node().appendChild(createNode(root, true));
}

function connectWebSocket() {
    try {
        const wsUrl = window.APP_CONFIG.WS_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
        console.log('Connecting to WebSocket:', wsUrl);
        ws = new WebSocket(wsUrl);
        
        ws.onopen = function() {
            console.log('WebSocket connection established');
            addLogEntry('Connected to server');
        };

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.type === 'stats') {
                updateStats(data.stats);
                if (data.stats.link_tree) {
                    updateVisualization(data.stats.link_tree);
                }
            } else if (data.type === 'log') {
                addLogEntry(data.message);
            }
        };

        ws.onclose = function(event) {
            console.log('WebSocket connection closed:', event.code, event.reason);
            addLogEntry(`Disconnected from server (code: ${event.code})`);
            // Attempt to reconnect after a delay
            setTimeout(connectWebSocket, 5000);
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
            addLogEntry(`WebSocket error: ${error.message || 'Connection failed'}`);
        };
    } catch (error) {
        console.error('Error connecting to WebSocket:', error);
        addLogEntry(`Error connecting to WebSocket: ${error.message}`);
        // Attempt to reconnect after a delay
        setTimeout(connectWebSocket, 5000);
    }
}

function updateStats(stats) {
    document.getElementById('status').textContent = stats.status;
    document.getElementById('pagesCrawled').textContent = stats.pages_crawled;
    document.getElementById('pdfsFound').textContent = stats.pdfs_found;
    document.getElementById('pdfsDownloaded').textContent = stats.pdfs_downloaded;
    document.getElementById('currentUrl').textContent = stats.current_url || 'None';
}

function updateButtonStates(status) {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const pauseBtn = document.getElementById('pauseBtn');

    startBtn.disabled = status === 'running' || status === 'paused';
    stopBtn.disabled = status === 'stopped';
    pauseBtn.disabled = status === 'stopped';

    // Update pause button text
    if (status === 'paused') {
        pauseBtn.textContent = 'Resume';
        isPaused = true;
    } else {
        pauseBtn.textContent = 'Pause';
        isPaused = false;
    }
}

function addLogEntry(message) {
    const logContainer = document.getElementById('logEntries');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    // If the message doesn't already have a timestamp (from backend),
    // add one in Eastern Time
    if (!message.match(/^\d{4}-\d{2}-\d{2}/)) {
        const now = new Date();
        const eastern = new Intl.DateTimeFormat('en-US', {
            timeZone: 'America/New_York',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZoneName: 'short'
        }).format(now);
        message = `${eastern} [INFO] ${message}`;
    }
    
    entry.textContent = message;
    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Start button
    document.getElementById('startBtn').onclick = async function() {
        try {
            const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                mode: 'cors',
                credentials: 'include'
            });
            const data = await response.json();
            if (data.status === 'started') {
                isRunning = true;
                this.disabled = true;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('pauseBtn').disabled = false;
            }
        } catch (error) {
            console.error('Error starting crawler:', error);
            addLogEntry(`Error starting crawler: ${error.message}`);
        }
    };

    // Stop button
    document.getElementById('stopBtn').onclick = async function() {
        try {
            const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                mode: 'cors',
                credentials: 'include'
            });
            const data = await response.json();
            if (data.status === 'stopped') {
                isRunning = false;
                isPaused = false;
                this.disabled = true;
                document.getElementById('startBtn').disabled = false;
                document.getElementById('pauseBtn').disabled = true;
                document.getElementById('pauseBtn').textContent = 'Pause';
            }
        } catch (error) {
            console.error('Error stopping crawler:', error);
            addLogEntry(`Error stopping crawler: ${error.message}`);
        }
    };

    // Pause button
    document.getElementById('pauseBtn').onclick = async function() {
        try {
            const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/pause`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                mode: 'cors',
                credentials: 'include'
            });
            const data = await response.json();
            if (data.status === 'paused' || data.status === 'resumed') {
                isPaused = data.status === 'paused';
                this.textContent = isPaused ? 'Resume' : 'Pause';
            }
        } catch (error) {
            console.error('Error toggling pause:', error);
            addLogEntry(`Error toggling pause: ${error.message}`);
        }
    };

    // Reset button
    document.getElementById('resetBtn').onclick = function() {
        fetch(`${window.APP_CONFIG.API_BASE_URL}/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            mode: 'cors',
            credentials: 'include'
        });
        // Clear visualization
        initVisualization();
        // Clear logs
        document.getElementById('logEntries').innerHTML = '';
    };

    // Initialize
    connectWebSocket();
    initVisualization();
});

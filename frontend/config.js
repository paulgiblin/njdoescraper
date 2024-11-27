// Initialize configuration using environment or window location
const getBaseUrl = () => {
    // Use API_URL from environment if available
    if (window.APP_CONFIG?.API_BASE_URL) {
        return window.APP_CONFIG.API_BASE_URL;
    }
    // Fallback to window location
    return `${window.location.protocol}//${window.location.hostname}:8000`;
};

// Export configuration
window.APP_CONFIG = {
    API_BASE_URL: getBaseUrl(),
    WS_BASE_URL: process.env.API_URL ? process.env.API_URL.replace(/^http/, 'ws') : getBaseUrl().replace(/^http/, 'ws')
};

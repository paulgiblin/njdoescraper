// Initialize configuration using environment or window location
const getBaseUrl = () => {
    // API_BASE_URL will be injected by the container's environment
    return '/api';  // Always return /api since that's our nginx configuration
};

const getWsUrl = () => {
    // WS_BASE_URL will be injected by the container's environment
    return '/ws';  // Always return /ws since that's our nginx configuration
};

// Export configuration
window.APP_CONFIG = {
    API_BASE_URL: getBaseUrl(),
    WS_BASE_URL: getWsUrl()
};

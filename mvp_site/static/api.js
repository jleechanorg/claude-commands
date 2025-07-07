async function fetchApi(path, options = {}, retryCount = 0) {
    const startTime = performance.now();
    
    // Check for test mode bypass
    let defaultHeaders;
    if (window.testAuthBypass && window.testAuthBypass.enabled) {
        // Use test bypass headers
        defaultHeaders = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': window.testAuthBypass.userId,
            'Content-Type': 'application/json'
        };
    } else {
        // Normal authentication flow
        const user = firebase.auth().currentUser;
        if (!user) throw new Error('User not authenticated');

        // Get fresh token, forcing refresh on retries to handle clock skew
        const forceRefresh = retryCount > 0;
        const token = await user.getIdToken(forceRefresh);
        defaultHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
    }
    
    const config = { ...options, headers: { ...defaultHeaders, ...options.headers } };

    const response = await fetch(path, config);
    const duration = ((performance.now() - startTime) / 1000).toFixed(2);

    if (!response.ok) {
        let errorPayload = {
            message: `HTTP Error: ${response.status} ${response.statusText}`,
            traceback: `Status code ${response.status} indicates a server-side problem. Check the Cloud Run logs for details.`
        };
        try {
            // Attempt to parse the body as JSON, it might contain our detailed error
            const jsonError = await response.json();
            errorPayload.message = jsonError.error || errorPayload.message;
            errorPayload.traceback = jsonError.traceback || errorPayload.traceback;
        } catch (e) {
            // The response was not JSON. The server likely sent a plain HTML error page.
            console.error("Failed to parse error response as JSON.", e);
        }

        // RESILIENCE: Auto-retry auth failures that might be clock-related
        if (response.status === 401 && retryCount < 2) {
            const isClockSkewError = errorPayload.message.includes('Token used too early') || 
                                   errorPayload.message.includes('clock') ||
                                   errorPayload.message.includes('time');
            
            if (isClockSkewError) {
                console.log(`🔄 Clock skew detected, retrying with fresh token (attempt ${retryCount + 1}/2)`);
                // Wait a moment before retry to let any timing issues settle
                await new Promise(resolve => setTimeout(resolve, 1000));
                return fetchApi(path, options, retryCount + 1);
            }
        }

        // Throw an object that our UI knows how to render.
        const error = new Error(errorPayload.message);
        error.traceback = errorPayload.traceback;
        throw error;
    }

    const data = await response.json();
    return { data, duration };
}

// RESILIENCE: Health check function to detect backend issues
async function checkBackendHealth() {
    try {
        const response = await fetch('/api/health', { 
            method: 'GET',
            timeout: 5000 // 5 second timeout
        });
        return response.ok;
    } catch (error) {
        console.warn('Backend health check failed:', error);
        return false;
    }
}

// RESILIENCE: Connection status monitoring
let connectionStatus = {
    online: navigator.onLine,
    backendHealthy: true,
    lastCheck: Date.now()
};

// Monitor network status
window.addEventListener('online', () => {
    connectionStatus.online = true;
    console.log('🌐 Network connection restored');
});

window.addEventListener('offline', () => {
    connectionStatus.online = false;
    console.log('📡 Network connection lost - switching to offline mode');
});

// RESILIENCE: Get connection status for UI decisions
function getConnectionStatus() {
    return {
        ...connectionStatus,
        canCreateCampaigns: connectionStatus.online && connectionStatus.backendHealthy,
        canViewCachedCampaigns: true // Always true - we can show cached data
    };
}

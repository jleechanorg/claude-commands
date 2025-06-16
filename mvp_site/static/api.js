async function fetchApi(path, options = {}) {
    const startTime = performance.now();
    const user = firebase.auth().currentUser;
    if (!user) throw new Error('User not authenticated');
    
    const token = await user.getIdToken();
    const defaultHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
    const config = { ...options, headers: { ...defaultHeaders, ...options.headers } };
    const response = await fetch(path, config);
    
    const data = await response.json();
    const duration = ((performance.now() - startTime) / 1000).toFixed(2);

    if (!response.ok) {
        throw new Error(data.message || 'API request failed');
    }
    
    // Return both data and duration
    return { data, duration };
}

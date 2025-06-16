async function fetchApi(path, options = {}) {
    const startTime = performance.now();
    const user = firebase.auth().currentUser;
    if (!user) throw new Error('User not authenticated');

    const token = await user.getIdToken();
    const defaultHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
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
        // Throw an object that our UI knows how to render.
        const error = new Error(errorPayload.message);
        error.traceback = errorPayload.traceback;
        throw error;
    }

    const data = await response.json();
    return { data, duration };
}

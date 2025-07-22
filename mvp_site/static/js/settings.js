/**
 * Settings page JavaScript functionality
 * Handles model selection with auto-save, debouncing, and error handling
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Settings page loaded');
    
    // Load current settings
    loadSettings();
    
    // Add change listeners to radio buttons
    const radioButtons = document.querySelectorAll('input[name="geminiModel"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', saveSettings);
    });
});

let saveTimeout = null;

/**
 * Load user settings from the API and update the UI
 */
async function loadSettings() {
    try {
        console.log('Loading user settings...');
        const response = await fetch('/api/settings', {
            headers: getAuthHeaders()
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const settings = await response.json();
        console.log('Loaded settings:', settings);
        
        // Validate the model value before using it
        if (settings.gemini_model && 
            ['pro-2.5', 'flash-2.5'].includes(settings.gemini_model)) {
            const radio = document.querySelector(`input[value="${settings.gemini_model}"]`);
            if (radio) {
                radio.checked = true;
                console.log(`Set model to: ${settings.gemini_model}`);
            }
        } else {
            console.log('No saved model preference or invalid value, using default (pro-2.5)');
        }
        
    } catch (error) {
        console.error('Failed to load settings:', error);
        showErrorMessage('Failed to load settings. Please refresh the page.');
    }
}

/**
 * Save settings with debouncing and visual feedback
 */
async function saveSettings() {
    // Debounce rapid changes
    if (saveTimeout) {
        clearTimeout(saveTimeout);
    }
    
    saveTimeout = setTimeout(async () => {
        const selectedModel = document.querySelector('input[name="geminiModel"]:checked').value;
        const radioButtons = document.querySelectorAll('input[name="geminiModel"]');
        
        console.log(`Saving model selection: ${selectedModel}`);
        
        // Show loading indicator
        showLoadingIndicator(true);
        
        // Disable inputs during save
        radioButtons.forEach(radio => radio.disabled = true);
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    ...getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ gemini_model: selectedModel })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                console.log('Settings saved successfully');
                showSaveMessage();
            } else {
                console.error('Failed to save settings:', result.error);
                showErrorMessage(result.error || 'Failed to save settings. Please try again.');
            }
            
        } catch (error) {
            console.error('Failed to save settings:', error);
            showErrorMessage('An error occurred while saving settings. Please try again.');
        } finally {
            // Re-enable inputs and hide loading
            radioButtons.forEach(radio => radio.disabled = false);
            showLoadingIndicator(false);
        }
    }, 300); // 300ms debounce
}

/**
 * Get authentication headers for API requests
 */
function getAuthHeaders() {
    const headers = {};
    
    // Check for test mode parameters in URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('test_mode') === 'true') {
        headers['X-Test-Bypass-Auth'] = 'true';
        headers['X-Test-User-ID'] = urlParams.get('test_user_id') || 'test-user-123';
    }
    
    return headers;
}

/**
 * Show success message with auto-hide
 */
function showSaveMessage() {
    const messageDiv = document.getElementById('save-message');
    const errorDiv = document.getElementById('error-message');
    
    // Hide error message
    errorDiv.style.display = 'none';
    
    // Show success message
    messageDiv.style.display = 'block';
    messageDiv.style.opacity = '1';
    
    // Fade out after 3 seconds
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        messageDiv.style.transition = 'opacity 0.5s';
        
        setTimeout(() => {
            messageDiv.style.display = 'none';
            messageDiv.style.opacity = '1';
        }, 500);
    }, 3000);
}

/**
 * Show error message with auto-hide
 */
function showErrorMessage(message) {
    const errorDiv = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const messageDiv = document.getElementById('save-message');
    
    // Hide success message
    messageDiv.style.display = 'none';
    
    // Show error message
    if (errorText) {
        errorText.textContent = message;
    } else {
        errorDiv.innerHTML = `<i class="bi bi-exclamation-triangle me-2"></i>${message}`;
    }
    
    errorDiv.style.display = 'block';
    errorDiv.style.opacity = '1';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.opacity = '0';
        errorDiv.style.transition = 'opacity 0.5s';
        
        setTimeout(() => {
            errorDiv.style.display = 'none';
            errorDiv.style.opacity = '1';
        }, 500);
    }, 5000);
}

/**
 * Show/hide loading indicator
 */
function showLoadingIndicator(show) {
    const loadingDiv = document.getElementById('loading-indicator');
    
    if (show) {
        loadingDiv.style.display = 'block';
    } else {
        loadingDiv.style.display = 'none';
    }
}
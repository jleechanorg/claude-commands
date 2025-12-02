/**
 * Settings page JavaScript functionality
 * Handles model selection with auto-save, debouncing, and error handling
 */
/* global firebase */

document.addEventListener('DOMContentLoaded', function () {
  console.log('Settings page loaded');

  // Load current settings
  loadSettings();

  const geminiModelSelect = document.getElementById('geminiModel');
  if (geminiModelSelect) {
    geminiModelSelect.addEventListener('change', saveSettings);
  }

  const providerRadios = document.querySelectorAll('input[name="llmProvider"]');
  providerRadios.forEach((radio) => {
    radio.addEventListener('change', () => {
      toggleProviderSections(radio.value);
      saveSettings();
    });
  });

  const openrouterModelSelect = document.getElementById('openrouterModel');
  if (openrouterModelSelect) {
    openrouterModelSelect.addEventListener('change', saveSettings);
  }

  const cerebrasModelSelect = document.getElementById('cerebrasModel');
  if (cerebrasModelSelect) {
    cerebrasModelSelect.addEventListener('change', saveSettings);
  }

  // Add change listener to debug mode switch
  const debugSwitch = document.getElementById('debugModeSwitch');
  if (debugSwitch) {
    debugSwitch.addEventListener('change', saveSettings);
  }
});

let saveTimeout = null;
const DEFAULT_OPENROUTER_MODEL = 'meta-llama/llama-3.1-70b-instruct';
const DEFAULT_CEREBRAS_MODEL = 'qwen-3-235b-a22b-instruct-2507'; // 131K context - best for RPG
const DEFAULT_GEMINI_MODEL = 'gemini-2.0-flash';

// Users allowed to see Gemini 3 Pro option (expensive model)
const GEMINI_3_ALLOWED_USERS = ['jleechan@gmail.com', 'jleechantest@gmail.com'];
const GEMINI_MODEL_MAPPING = {
  'gemini-3-pro-preview': 'gemini-3-pro-preview',
  'gemini-2.0-flash': 'gemini-2.0-flash',
  'gemini-2.5-flash': 'gemini-2.0-flash',
  'gemini-2.5-pro': 'gemini-2.0-flash',
  'pro-2.5': 'gemini-2.0-flash',
  'flash-2.5': 'gemini-2.0-flash'
};
let pendingAuthReload = false;

/**
 * Load user settings from the API and update the UI
 */
async function loadSettings() {
  try {
    console.log('Loading user settings...');
    const response = await fetch('/api/settings', {
      headers: await getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const settings = await response.json();
    console.log('Loaded settings:', settings);

    // Get current user email from Firebase Auth
    const allowedEmails = GEMINI_3_ALLOWED_USERS.map((email) => email.toLowerCase());
    const userEmail = window.firebase?.auth()?.currentUser?.email || '';
    if (!userEmail && window.firebase?.auth && !pendingAuthReload) {
      pendingAuthReload = true;
      window.firebase.auth().onAuthStateChanged((user) => {
        if (user?.email) {
          pendingAuthReload = false;
          loadSettings();
        }
      });
    }

    const canUseGemini3 =
      userEmail && allowedEmails.includes(userEmail.toLowerCase());

    // Dynamically add Gemini 3 option for allowed users
    const geminiSelect = document.getElementById('geminiModel');
    if (geminiSelect && canUseGemini3) {
      const hasGemini3 = Array.from(geminiSelect.options).some(
        (opt) => opt.value === 'gemini-3-pro-preview',
      );
      if (!hasGemini3) {
        const option = document.createElement('option');
        option.value = 'gemini-3-pro-preview';
        option.textContent = 'Gemini 3 Pro Preview (premium)';
        geminiSelect.insertBefore(option, geminiSelect.firstChild);
      }
    }

    const allowedProviders = ['gemini', 'openrouter', 'cerebras'];
    const selectedProvider = allowedProviders.includes(settings.llm_provider)
      ? settings.llm_provider
      : 'gemini';

    const providerRadio = document.querySelector(
      `input[name="llmProvider"][value="${selectedProvider}"]`,
    );
    if (providerRadio) {
      providerRadio.checked = true;
    }
    toggleProviderSections(selectedProvider);

    const mappedGeminiModel = GEMINI_MODEL_MAPPING[settings.gemini_model] || DEFAULT_GEMINI_MODEL;
    // Only downgrade premium selection if we know the user isn't allowlisted
    const geminiModel =
      mappedGeminiModel === 'gemini-3-pro-preview' && !canUseGemini3
        ? DEFAULT_GEMINI_MODEL
        : mappedGeminiModel;
    if (geminiSelect) {
      const hasOption = Array.from(geminiSelect.options).some(
        (opt) => opt.value === geminiModel,
      );
      geminiSelect.value = hasOption ? geminiModel : DEFAULT_GEMINI_MODEL;
    }

    const openrouterModel = settings.openrouter_model || DEFAULT_OPENROUTER_MODEL;
    const openrouterSelect = document.getElementById('openrouterModel');
    if (openrouterSelect) {
      openrouterSelect.value = openrouterModel;
    }

    const cerebrasModel = settings.cerebras_model || DEFAULT_CEREBRAS_MODEL;
    const cerebrasSelect = document.getElementById('cerebrasModel');
    if (cerebrasSelect) {
      cerebrasSelect.value = cerebrasModel;
    }

    // Set debug mode switch
    const debugSwitch = document.getElementById('debugModeSwitch');
    if (debugSwitch) {
      debugSwitch.checked = settings.debug_mode === true;
      console.log(`Set debug mode to: ${settings.debug_mode}`);
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
    const geminiSelect = document.getElementById('geminiModel');
    const providerRadio = document.querySelector(
      'input[name="llmProvider"]:checked',
    );
    const openrouterSelect = document.getElementById('openrouterModel');
    const cerebrasSelect = document.getElementById('cerebrasModel');

    if (!providerRadio) {
      console.warn('No provider is selected. Aborting save operation.');
      return;
    }

    const provider = providerRadio.value;
    const selectedModel = geminiSelect ? geminiSelect.value : DEFAULT_GEMINI_MODEL;
    const openrouterModel = openrouterSelect
      ? openrouterSelect.value
      : DEFAULT_OPENROUTER_MODEL;
    const cerebrasModel = cerebrasSelect
      ? cerebrasSelect.value
      : DEFAULT_CEREBRAS_MODEL;
    const debugSwitch = document.getElementById('debugModeSwitch');
    const providerRadios = document.querySelectorAll('input[name="llmProvider"]');

    // Collect all settings to save
    const settingsToSave = {
      llm_provider: provider,
      gemini_model: selectedModel,
      openrouter_model: openrouterModel,
      cerebras_model: cerebrasModel,
      debug_mode: debugSwitch ? debugSwitch.checked : false,
    };

    console.log('Saving settings:', settingsToSave);

    // Show loading indicator
    showLoadingIndicator(true);

    // Disable inputs during save
    if (geminiSelect) geminiSelect.disabled = true;
    providerRadios.forEach((radio) => (radio.disabled = true));
    if (openrouterSelect) openrouterSelect.disabled = true;
    if (cerebrasSelect) cerebrasSelect.disabled = true;
    if (debugSwitch) debugSwitch.disabled = true;

    try {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          ...(await getAuthHeaders()),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settingsToSave),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        console.log('Settings saved successfully');
        showSaveMessage();
      } else {
        console.error('Failed to save settings:', result.error);
        showErrorMessage(
          result.error || 'Failed to save settings. Please try again.',
        );
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      showErrorMessage(
        'An error occurred while saving settings. Please try again.',
      );
    } finally {
      // Re-enable inputs and hide loading
      if (geminiSelect) geminiSelect.disabled = false;
      providerRadios.forEach((radio) => (radio.disabled = false));
      if (openrouterSelect) openrouterSelect.disabled = false;
      if (cerebrasSelect) cerebrasSelect.disabled = false;
      if (debugSwitch) debugSwitch.disabled = false;
      showLoadingIndicator(false);
    }
  }, 300); // 300ms debounce
}

function toggleProviderSections(provider) {
  const geminiSection = document.getElementById('gemini-model-selection');
  const openrouterSection = document.getElementById('openrouter-model-selection');
  const cerebrasSection = document.getElementById('cerebras-model-selection');

  if (!geminiSection || !openrouterSection || !cerebrasSection) {
    return;
  }

  geminiSection.classList.toggle('d-none', provider !== 'gemini');
  openrouterSection.classList.toggle('d-none', provider !== 'openrouter');
  cerebrasSection.classList.toggle('d-none', provider !== 'cerebras');
}

/**
 * Get authentication headers for API requests
 */
async function getAuthHeaders() {
  if (window.authTokenManager) {
    return window.authTokenManager.getAuthHeaders();
  }

  const headers = {};

  // Check for test mode parameters in URL
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('test_mode') === 'true') {
    headers['X-Test-Bypass-Auth'] = 'true';
    headers['X-Test-User-ID'] =
      urlParams.get('test_user_id') || 'test-user-123';
  } else {
    // Production mode - include Firebase auth token
    try {
      const user = firebase.auth().currentUser;
      if (user) {
        const token = await user.getIdToken();
        headers['Authorization'] = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Failed to get auth token:', error);
    }
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

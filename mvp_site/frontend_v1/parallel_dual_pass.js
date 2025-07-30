/**
 * Parallel Dual-Pass Frontend Implementation - TASK-019
 *
 * This module handles the parallel processing of entity enhancement
 * while users read the initial response.
 */

// Track pending enhancements
const pendingEnhancements = new Map();

/**
 * Handle interaction with parallel dual-pass optimization
 */
async function handleInteractionParallel(userInput, mode, currentCampaignId) {
  try {
    // Get initial response (Pass 1)
    const response = await fetch(
      `/api/campaigns/${currentCampaignId}/interaction`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: userInput, mode: mode }),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // Display initial response immediately
    appendToStory(
      'gemini',
      data.response,
      null,
      data.debug_mode,
      data.sequence_id,
    );

    // Check if enhancement is needed
    if (
      data.enhancement_needed &&
      data.missing_entities &&
      data.missing_entities.length > 0
    ) {
      // Start background enhancement
      console.log(
        `Starting background enhancement for ${data.missing_entities.length} missing entities`,
      );
      enhanceStoryInBackground(
        data.response,
        data.missing_entities,
        data.sequence_id,
        currentCampaignId,
      );
    }

    return data;
  } catch (error) {
    console.error('Error in parallel interaction:', error);
    throw error;
  }
}

/**
 * Enhance story in background (Pass 2)
 */
async function enhanceStoryInBackground(
  originalResponse,
  missingEntities,
  sequenceId,
  campaignId,
) {
  // Store pending enhancement
  pendingEnhancements.set(sequenceId, {
    status: 'pending',
    startTime: Date.now(),
  });

  try {
    // Show subtle enhancement indicator
    showEnhancementIndicator(sequenceId);

    // Call enhancement endpoint
    const response = await fetch(
      `/api/campaigns/${campaignId}/enhance-entities`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          original_response: originalResponse,
          missing_entities: missingEntities,
          sequence_id: sequenceId,
        }),
      },
    );

    if (!response.ok) {
      throw new Error(`Enhancement failed: ${response.status}`);
    }

    const data = await response.json();

    if (data.success && data.enhanced_response) {
      // Replace the narrative smoothly
      replaceStoryEntry(sequenceId, data.enhanced_response);

      // Show success notification
      showEnhancementSuccess(sequenceId, data.entities_injected);

      // Update pending status
      pendingEnhancements.set(sequenceId, {
        status: 'complete',
        completedTime: Date.now(),
        entitiesInjected: data.entities_injected,
      });
    }
  } catch (error) {
    console.warn('Background enhancement failed:', error);
    // Silent failure - user keeps original response
    hideEnhancementIndicator(sequenceId);

    pendingEnhancements.set(sequenceId, {
      status: 'failed',
      error: error.message,
    });
  }
}

/**
 * Replace story entry with enhanced version
 */
function replaceStoryEntry(sequenceId, enhancedNarrative) {
  const storyEntry = document.querySelector(
    `[data-sequence-id="${sequenceId}"]`,
  );
  if (!storyEntry) {
    console.warn(`Story entry not found for sequence ${sequenceId}`);
    return;
  }

  // Find the narrative content within the entry
  const narrativeElement =
    storyEntry.querySelector('.narrative-content') || storyEntry;

  // Smooth transition
  narrativeElement.style.transition = 'opacity 0.3s ease';
  narrativeElement.style.opacity = '0.7';

  setTimeout(() => {
    narrativeElement.innerHTML = enhancedNarrative;
    narrativeElement.style.opacity = '1';
  }, 300);
}

/**
 * Show enhancement indicator
 */
function showEnhancementIndicator(sequenceId) {
  const storyEntry = document.querySelector(
    `[data-sequence-id="${sequenceId}"]`,
  );
  if (!storyEntry) return;

  const indicator = document.createElement('div');
  indicator.className = 'enhancement-indicator';
  indicator.innerHTML =
    '<span class="spinner-border spinner-border-sm"></span> Enhancing story...';
  indicator.id = `enhance-${sequenceId}`;

  storyEntry.appendChild(indicator);
}

/**
 * Hide enhancement indicator
 */
function hideEnhancementIndicator(sequenceId) {
  const indicator = document.getElementById(`enhance-${sequenceId}`);
  if (indicator) {
    indicator.remove();
  }
}

/**
 * Show enhancement success notification
 */
function showEnhancementSuccess(sequenceId, entitiesInjected) {
  hideEnhancementIndicator(sequenceId);

  const storyEntry = document.querySelector(
    `[data-sequence-id="${sequenceId}"]`,
  );
  if (!storyEntry) return;

  const notification = document.createElement('div');
  notification.className = 'enhancement-success';
  notification.innerHTML = `✨ Story enhanced with ${entitiesInjected} character${entitiesInjected > 1 ? 's' : ''}`;
  notification.id = `success-${sequenceId}`;

  storyEntry.appendChild(notification);

  // Fade out after 3 seconds
  setTimeout(() => {
    notification.style.transition = 'opacity 1s ease';
    notification.style.opacity = '0';
    setTimeout(() => notification.remove(), 1000);
  }, 3000);
}

// Export for use in main app.js
window.parallelDualPass = {
  handleInteractionParallel,
  pendingEnhancements,
};

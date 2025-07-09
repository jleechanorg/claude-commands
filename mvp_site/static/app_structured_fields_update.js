// Update for app.js to handle structured response fields properly

// 1. Update appendToStory signature to accept fullData
const appendToStory = (actor, text, mode = null, debugMode = false, sequenceId = null, fullData = null) => {
    const storyContainer = document.getElementById('story-content');
    const entryEl = document.createElement('div');
    entryEl.className = 'story-entry';
    
    let label = '';
    if (actor === 'gemini') {
        label = sequenceId ? `Scene #${sequenceId}` : 'Story';
    } else { // actor is 'user'
        label = mode === 'character' ? 'Main Character' : (mode === 'god' ? 'God' : 'You');
    }
    
    // Process debug content - backend now handles stripping based on debug_mode
    // Frontend only needs to style debug content when present
    let processedText = text;
    if (actor === 'gemini') {
        // Style STATE_UPDATES_PROPOSED blocks when present (only in debug mode)
        processedText = text
            .replace(/\[STATE_UPDATES_PROPOSED\]/g, '<div class="debug-content"><strong>🔧 STATE UPDATES PROPOSED:</strong><br><pre>')
            .replace(/\[END_STATE_UPDATES_PROPOSED\]/g, '</pre></div>');
        
        // Then style other debug content that is present
        processedText = processedText
            .replace(/\[DEBUG_START\]/g, '<div class="debug-content"><strong>🔍 DM Notes:</strong> ')
            .replace(/\[DEBUG_END\]/g, '</div>')
            .replace(/\[DEBUG_STATE_START\]/g, '<div class="debug-content"><strong>⚙️ State Changes:</strong> ')
            .replace(/\[DEBUG_STATE_END\]/g, '</div>')
            .replace(/\[DEBUG_ROLL_START\]/g, '<div class="debug-rolls"><strong>🎲 Dice Roll:</strong> ')
            .replace(/\[DEBUG_ROLL_END\]/g, '</div>');
        
        // Parse and convert planning block choices to buttons
        processedText = parsePlanningBlocks(processedText);
    }
    
    // Build the HTML with narrative
    let html = `<p><strong>${label}:</strong> ${processedText}</p>`;
    
    // Add structured fields for AI responses
    if (actor === 'gemini' && fullData) {
        html += generateStructuredFieldsHTML(fullData, debugMode);
    }
    
    entryEl.innerHTML = html;
    storyContainer.appendChild(entryEl);
    
    // Add click handlers to any choice buttons we just added
    if (actor === 'gemini') {
        const choiceButtons = entryEl.querySelectorAll('.choice-button');
        choiceButtons.forEach(button => {
            button.addEventListener('click', handleChoiceClick);
        });
    }
};

// 2. Add helper function to generate HTML for structured fields
const generateStructuredFieldsHTML = (fullData, debugMode) => {
    let html = '';
    
    // Handle god_mode_response if present
    if (fullData.god_mode_response) {
        html += `<div class="god-mode-response" style="background-color: #f0e6ff; padding: 10px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #9b59b6;">`;
        html += `<strong>🔮 God Mode:</strong> ${fullData.god_mode_response}`;
        html += `</div>`;
    }
    
    // Extract dice rolls from debug_info when in debug mode
    if (debugMode && fullData.debug_info && fullData.debug_info.dice_rolls && fullData.debug_info.dice_rolls.length > 0) {
        html += '<div class="dice-rolls" style="background-color: #e8f4e8; padding: 8px; margin: 10px 0; border-radius: 5px;">';
        html += '<strong>🎲 Dice Rolls:</strong><ul style="margin: 5px 0; padding-left: 20px;">';
        fullData.debug_info.dice_rolls.forEach(roll => {
            html += `<li>${roll}</li>`;
        });
        html += '</ul></div>';
    }
    
    // Extract resources from debug_info when in debug mode
    if (debugMode && fullData.debug_info && fullData.debug_info.resources) {
        html += `<div class="resources" style="background-color: #fff3cd; padding: 8px; margin: 10px 0; border-radius: 5px;"><strong>📊 Resources:</strong> ${fullData.debug_info.resources}</div>`;
    }
    
    // Add entities mentioned
    if (fullData.entities_mentioned && fullData.entities_mentioned.length > 0) {
        html += `<div class="entities" style="background-color: #e7f3ff; padding: 8px; margin: 10px 0; border-radius: 5px;"><strong>👥 Entities:</strong> ${fullData.entities_mentioned.join(', ')}</div>`;
    }
    
    // Add location confirmed
    if (fullData.location_confirmed && fullData.location_confirmed !== 'Unknown') {
        html += `<div class="location" style="background-color: #f0f8ff; padding: 8px; margin: 10px 0; border-radius: 5px;"><strong>📍 Location:</strong> ${fullData.location_confirmed}</div>`;
    }
    
    // Add state updates in debug mode
    if (debugMode && fullData.state_updates && Object.keys(fullData.state_updates).length > 0) {
        html += '<div class="state-updates" style="background-color: #f5f5f5; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 0.9em;">';
        html += '<strong>🔧 State Updates:</strong><br>';
        html += '<pre style="margin: 5px 0; font-size: 0.85em;">' + JSON.stringify(fullData.state_updates, null, 2) + '</pre>';
        html += '</div>';
    }
    
    // Add full debug info details in debug mode
    if (debugMode && fullData.debug_info) {
        // Add DM notes if present
        if (fullData.debug_info.dm_notes && fullData.debug_info.dm_notes.length > 0) {
            html += '<div class="dm-notes" style="background-color: #f8f4ff; padding: 10px; margin-top: 10px; border-radius: 5px; font-style: italic;">';
            html += '<strong>📝 DM Notes:</strong><ul style="margin: 5px 0; padding-left: 20px;">';
            fullData.debug_info.dm_notes.forEach(note => {
                html += `<li>${note}</li>`;
            });
            html += '</ul></div>';
        }
        
        // Add state rationale if present
        if (fullData.debug_info.state_rationale) {
            html += `<div class="state-rationale" style="background-color: #fff8e7; padding: 8px; margin: 10px 0; border-radius: 5px;"><strong>💭 State Rationale:</strong> ${fullData.debug_info.state_rationale}</div>`;
        }
    }
    
    return html;
};

// 3. Update the interaction handler to pass full data
// In the user input submission handler, change this line:
// appendToStory('gemini', data.response, null, data.debug_mode || false, data.user_scene_number);
// To this:
// appendToStory('gemini', data.response, null, data.debug_mode || false, data.user_scene_number, data);

// 4. Also update the loadCampaign function where it renders existing story entries
// Change from:
// data.story.forEach(entry => appendToStory(entry.actor, entry.text, entry.mode, debugMode, entry.user_scene_number));
// To:
// data.story.forEach(entry => appendToStory(entry.actor, entry.text, entry.mode, debugMode, entry.user_scene_number, entry));
document.addEventListener('DOMContentLoaded', () => {
    // --- State and Constants ---
    const views = { 
        auth: document.getElementById('auth-view'), 
        dashboard: document.getElementById('dashboard-view'), 
        newCampaign: document.getElementById('new-campaign-view'), 
        game: document.getElementById('game-view') 
    };
    const loadingOverlay = document.getElementById('loading-overlay');
    let currentCampaignId = null;
    let campaignToEdit = null; 
    let isNavigatingToNewCampaignDirectly = false;

    // Helper function for scrolling
    const scrollToBottom = (element) => { 
        console.log(`Scrolling element: ${element.id}, current scrollHeight: ${element.scrollHeight}, clientHeight: ${element.clientHeight}`);
        element.scrollTop = element.scrollHeight; 
    };

    // --- Core UI & Navigation Logic ---
    const showSpinner = (context = 'loading') => {
        loadingOverlay.style.display = 'flex';
        if (window.loadingMessages) {
            window.loadingMessages.start(context);
        }
    };
    const hideSpinner = () => {
        loadingOverlay.style.display = 'none';
        if (window.loadingMessages) {
            window.loadingMessages.stop();
        }
    };
    
    const showView = (viewName) => {
        Object.values(views).forEach(v => v.classList.remove('active-view'));
        if(views[viewName]) {
            views[viewName].classList.add('active-view');
        }
    };

    function resetNewCampaignForm() {
        // CRITICAL: Don't reset form if wizard is active - this destroys the wizard state
        if (window.campaignWizard && window.campaignWizard.isEnabled) {
            console.log("Skipping form reset - wizard is active");
            return;
        }

        const campaignTitleInput = document.getElementById('campaign-title');
        const campaignPromptTextarea = document.getElementById('campaign-prompt');
        const narrativeCheckbox = document.getElementById('prompt-narrative');
        const mechanicsCheckbox = document.getElementById('prompt-mechanics');

        if (campaignTitleInput) {
            campaignTitleInput.value = "My Epic Adventure"; // Your default title
        }
        if (campaignPromptTextarea) {
            campaignPromptTextarea.value = "A brave knight in a land of dragons."; // Your default prompt
        }
        if (narrativeCheckbox) {
            narrativeCheckbox.checked = true; // Default checked
        }
        if (mechanicsCheckbox) {
            mechanicsCheckbox.checked = true; // Default checked
        }
        console.log("New campaign form reset to defaults.");
    }

    let handleRouteChange = () => {
        if (!firebase.auth().currentUser) { showView('auth'); return; }
        const path = window.location.pathname;
        const campaignIdMatch = path.match(/^\/game\/([a-zA-Z0-9]+)/);
        if (campaignIdMatch) {
            currentCampaignId = campaignIdMatch[1];
            resumeCampaign(currentCampaignId);
        } else if (path === '/new-campaign') {
            if (isNavigatingToNewCampaignDirectly) { 
                resetNewCampaignForm();
                isNavigatingToNewCampaignDirectly = false; // Reset the flag after use
            }
            showView('newCampaign');
        } else {
            currentCampaignId = null;
            renderCampaignList();
            showView('dashboard');
        }
    };
    
    const appendToStory = (actor, text, mode = null, debugMode = false, sequenceId = null) => {
        const storyContainer = document.getElementById('story-content');
        const entryEl = document.createElement('p');
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
        }
        
        entryEl.innerHTML = `<strong>${label}:</strong> ${processedText}`;
        storyContainer.appendChild(entryEl);
    };

    // --- Data Fetching and Rendering ---
    let renderCampaignList = async () => {
        showSpinner('loading');
        try {
            const { data: campaigns } = await fetchApi('/api/campaigns');
            
            // RESILIENCE: Cache successful campaign data for offline viewing
            localStorage.setItem('cachedCampaigns', JSON.stringify(campaigns));
            localStorage.setItem('lastCampaignUpdate', new Date().toISOString());
            
            renderCampaignListUI(campaigns, false);
        } catch (error) { 
            console.error("Error fetching campaigns:", error);
            
            // RESILIENCE: Try to load from cache if network fails
            const cachedCampaigns = localStorage.getItem('cachedCampaigns');
            const lastUpdate = localStorage.getItem('lastCampaignUpdate');
            
            if (cachedCampaigns) {
                const campaigns = JSON.parse(cachedCampaigns);
                const lastUpdateDate = lastUpdate ? new Date(lastUpdate).toLocaleDateString() : 'unknown';
                renderCampaignListUI(campaigns, true, lastUpdateDate);
                
                // Show user that we're offline but they can still view campaigns
                const listEl = document.getElementById('campaign-list');
                const offlineNotice = document.createElement('div');
                offlineNotice.className = 'alert alert-warning mb-3';
                offlineNotice.innerHTML = `
                    📡 <strong>Offline Mode:</strong> Showing cached campaigns from ${lastUpdateDate}. 
                    Campaign creation and editing require internet connection.
                `;
                listEl.insertBefore(offlineNotice, listEl.firstChild);
            } else {
                const listEl = document.getElementById('campaign-list');
                listEl.innerHTML = `
                    <div class="alert alert-danger">
                        🌐 <strong>Connection Error:</strong> Could not load campaigns. 
                        Please check your internet connection and try again.
                    </div>
                `;
            }
        }
        finally { hideSpinner(); }
    };
    
    // RESILIENCE: Separate UI rendering for reuse with cached data
    function renderCampaignListUI(campaigns, isOffline = false, lastUpdate = null) {
        const listEl = document.getElementById('campaign-list');
        listEl.innerHTML = '';
        
        if (campaigns.length === 0) { 
            listEl.innerHTML = '<p>You have no campaigns. Start a new one!</p>'; 
            return;
        }
        
        campaigns.forEach(campaign => {
            const campaignEl = document.createElement('div');
            campaignEl.className = 'list-group-item list-group-item-action';
            
            const lastPlayed = campaign.last_played ? new Date(campaign.last_played).toLocaleString() : 'N/A';
            const initialPrompt = campaign.initial_prompt ? campaign.initial_prompt.substring(0, 100) + '...' : '[No prompt]';

            campaignEl.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1 campaign-title-link">${campaign.title}</h5>
                    <div>
                        ${!isOffline ? '<button class="btn btn-sm btn-outline-primary edit-campaign-btn me-2">Edit</button>' : ''}
                        <small class="text-muted">Last played: ${lastPlayed}</small>
                    </div>
                </div>
                <p class="mb-1 campaign-title-link">${initialPrompt}</p>`;
            
            campaignEl.dataset.campaignId = campaign.id;
            campaignEl.dataset.campaignTitle = campaign.title;

            listEl.appendChild(campaignEl);
        });
    }

    let resumeCampaign = async (campaignId) => {
        showSpinner('loading');
        try {
            const { data } = await fetchApi(`/api/campaigns/${campaignId}`);
            document.getElementById('game-title').innerText = data.campaign.title;
            const storyContainer = document.getElementById('story-content');
            storyContainer.innerHTML = '';
            
            // Check if we have game state with debug mode
            const debugMode = data.game_state?.debug_mode || false;
            
            // Update debug indicator
            const debugIndicator = document.getElementById('debug-indicator');
            if (debugIndicator) {
                debugIndicator.style.display = debugMode ? 'block' : 'none';
            }
            
            // Render story with debug mode awareness
            data.story.forEach(entry => appendToStory(entry.actor, entry.text, entry.mode, debugMode, entry.user_scene_number));
            
            // Add a slight delay to allow rendering before scrolling
            console.log("Attempting to scroll after content append, with a slight delay."); // RESTORED console.log
            setTimeout(() => scrollToBottom(storyContainer), 100); // 100ms delay
            
            showView('game');
            document.getElementById('shareStoryBtn').style.display = 'block';
            document.getElementById('downloadStoryBtn').style.display = 'block';
        } catch (error) {
            console.error('Failed to resume campaign:', error);
            history.pushState({}, '', '/');
            handleRouteChange();
        } finally {
            hideSpinner();
        }
    };
    
    // --- Event Listeners ---
    document.getElementById('new-campaign-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        showSpinner('newCampaign');
        const prompt = document.getElementById('campaign-prompt').value;
        const title = document.getElementById('campaign-title').value;
        const selectedPrompts = Array.from(document.querySelectorAll('input[name="selectedPrompts"]:checked')).map(checkbox => checkbox.value);
        const customOptions = Array.from(document.querySelectorAll('input[name="customOptions"]:checked')).map(checkbox => checkbox.value);
        try {
            const { data } = await fetchApi('/api/campaigns', { 
                method: 'POST', 
                body: JSON.stringify({ prompt, title, selected_prompts: selectedPrompts, custom_options: customOptions }) 
            });
            
            // Complete progress bar if wizard is active
            if (window.campaignWizard && typeof window.campaignWizard.completeProgress === 'function') {
                window.campaignWizard.completeProgress();
            }
            
            history.pushState({ campaignId: data.campaign_id }, '', `/game/${data.campaign_id}`);
            handleRouteChange();
            
        } catch (error) {
            console.error("Error creating campaign:", error);
            hideSpinner();
            
            // RESILIENCE: Better error messaging and recovery options
            let userMessage = 'Failed to start a new campaign.';
            let showRetryOption = false;
            
            if (error.message.includes('Token used too early') || error.message.includes('clock')) {
                userMessage = '⏰ Authentication timing issue detected. This usually resolves automatically.';
                showRetryOption = true;
            } else if (error.message.includes('401') || error.message.includes('Auth failed')) {
                userMessage = '🔐 Authentication issue. Please try signing out and back in.';
            } else if (error.message.includes('Network') || error.message.includes('fetch')) {
                userMessage = '🌐 Network connection issue. Please check your internet connection.';
                showRetryOption = true;
            }
            
            if (showRetryOption) {
                const retry = confirm(`${userMessage}\n\nWould you like to try again?`);
                if (retry) {
                    // Retry after a short delay
                    setTimeout(() => {
                        document.getElementById('new-campaign-form').dispatchEvent(new Event('submit'));
                    }, 2000);
                    return;
                }
            }
            
            alert(userMessage);
        }
    });

    const interactionForm = document.getElementById('interaction-form');
    const userInputEl = document.getElementById('user-input');

    if (userInputEl) {
        userInputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                if (interactionForm) {
                    interactionForm.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            }
        });
    }

    if (interactionForm) {
        interactionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            let userInput = userInputEl.value.trim();
            if (!userInput || !currentCampaignId) return;
            const mode = document.querySelector('input[name="interactionMode"]:checked').value;
            const localSpinner = document.getElementById('loading-spinner');
            const timerInfo = document.getElementById('timer-info');
            localSpinner.style.display = 'block';
            
            // Start loading messages for interactions
            if (window.loadingMessages) {
                const messageEl = localSpinner.querySelector('.loading-message');
                window.loadingMessages.start('interaction', messageEl);
            }
            
            userInputEl.disabled = true;
            timerInfo.textContent = '';
            appendToStory('user', userInput, mode);
            userInputEl.value = '';
            try {
                const { data, duration } = await fetchApi(`/api/campaigns/${currentCampaignId}/interaction`, {
                    method: 'POST', body: JSON.stringify({ input: userInput, mode }),
                });
                // Use user_scene_number from backend response
                appendToStory('gemini', data.response, null, data.debug_mode || false, data.user_scene_number);
                timerInfo.textContent = `Response time: ${duration}s`;
                
                // Update debug mode indicator if present
                const debugIndicator = document.getElementById('debug-indicator');
                if (debugIndicator) {
                    debugIndicator.style.display = data.debug_mode ? 'block' : 'none';
                }
            } catch (error) {
                console.error("Interaction failed:", error);
                appendToStory('system', 'Sorry, an error occurred. Please try again.');
            } finally {
                localSpinner.style.display = 'none';
                if (window.loadingMessages) {
                    window.loadingMessages.stop();
                }
                userInputEl.disabled = false;
                userInputEl.focus();
            }
        });
    }
    
    // --- NEW EVENT LISTENERS FOR EDIT FUNCTIONALITY ---
    document.getElementById('campaign-list').addEventListener('click', (e) => {
        const target = e.target;
        const campaignItem = target.closest('.list-group-item');

        if (!campaignItem) return;

        // Check if we clicked on a button (edit button, etc)
        if (target.closest('.btn')) {
            if (target.classList.contains('edit-campaign-btn')) {
                e.stopPropagation(); // Prevent campaign navigation
                campaignToEdit = {
                    id: campaignItem.dataset.campaignId,
                    title: campaignItem.dataset.campaignTitle
                };
                const editModalEl = document.getElementById('editCampaignModal');
                const editModal = new bootstrap.Modal(editModalEl);
                document.getElementById('edit-campaign-title').value = campaignToEdit.title;
                editModal.show();
            }
            return; // Don't navigate if any button was clicked
        }
        
        // Make the entire campaign item clickable (except buttons)
        const campaignId = campaignItem.dataset.campaignId;
        if (campaignId) {
            // Add visual feedback
            campaignItem.style.opacity = '0.8';
            setTimeout(() => {
                campaignItem.style.opacity = '';
            }, 100);
            
            // Navigate to campaign
            history.pushState({ campaignId }, '', `/game/${campaignId}`);
            handleRouteChange();
        }
    });

    const saveCampaignTitle = async () => {
        const newTitleInput = document.getElementById('edit-campaign-title');
        const newTitle = newTitleInput.value.trim();
        
        if (!newTitle || !campaignToEdit) {
            alert("Campaign title cannot be empty.");
            return;
        }
        
        showSpinner('saving');
        try {
            await fetchApi(`/api/campaigns/${campaignToEdit.id}`, {
                method: 'PATCH',
                body: JSON.stringify({ title: newTitle })
            });
            
            const editModalEl = document.getElementById('editCampaignModal');
            const modal = bootstrap.Modal.getInstance(editModalEl);
            if (modal) {
                modal.hide();
            }

            await renderCampaignList();
            alert('Campaign title updated successfully!');
        } catch (error) {
            console.error('Failed to update campaign title:', error);
            alert('Could not save the new title. Please try again.');
        } finally {
            hideSpinner();
            campaignToEdit = null;
        }
    };

    document.getElementById('save-campaign-title-btn').addEventListener('click', saveCampaignTitle);
    
    // Add form submit handler for Enter key support
    document.getElementById('edit-campaign-form').addEventListener('submit', (e) => {
        e.preventDefault();
        saveCampaignTitle();
    });

    // --- Share & Download Functionality ---
    function getFormattedStoryText() {
        const storyContent = document.getElementById('story-content');
        if (!storyContent) return '';
        const paragraphs = storyContent.querySelectorAll('p');
        return Array.from(paragraphs).map(p => p.innerText.trim()).join('\\n\\n');
    }

    async function downloadFile(format) {
        if (!currentCampaignId) return;
        showSpinner('saving');
        try {
            const user = firebase.auth().currentUser;
            if (!user) throw new Error('User not authenticated for download.');
            const token = await user.getIdToken();

            const response = await fetch(`/api/campaigns/${currentCampaignId}/export?format=${format}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Could not download story.' }));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const disposition = response.headers.get('Content-Disposition');
            let filename = `story_export.${format}`;
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            console.error('Download failed:', error);
            alert(`Download failed: ${error.message}`);
        } finally {
            hideSpinner();
        }
    }

    async function handleShareStory() {
        if (!navigator.share) {
            alert("Share feature is only available on supported devices, like mobile phones.");
            return;
        }
        const storyText = getFormattedStoryText();
        const storyTitle = document.getElementById('game-title').innerText || "My WorldArchitect.AI Story";
        if (!storyText) {
            alert('The story is empty. Nothing to share.');
            return;
        }
        
        // Check story size and handle large stories
        const maxShareSize = 30000; // 30KB limit for better compatibility
        let shareText = storyText;
        
        if (storyText.length > maxShareSize) {
            console.log('Share too large');
            // Truncate and add continuation message
            shareText = storyText.substring(0, maxShareSize) + 
                "...\n\n[Story continues - full version available at WorldArchitect.AI]";
            
            // Ask user if they want to share truncated version
            const userChoice = confirm(
                `Your story is very long (${Math.round(storyText.length/1000)}KB). ` +
                "Would you like to share a shortened preview, or cancel and use Download instead?"
            );
            
            if (!userChoice) {
                alert("Consider using the Download button to save your full story instead.");
                return;
            }
        }
        
        try {
            await navigator.share({ title: storyTitle, text: shareText });
        } catch (error) {
            console.error('Error sharing story:', error);
            // Fallback suggestion for share failures
            alert("Share failed. Try using the Download button to save your story, or copy the text manually from the story area.");
        }
    }

    function handleDownloadClick() {
        const downloadModal = new bootstrap.Modal(document.getElementById('downloadOptionsModal'));
        downloadModal.show();
    }

    // Attach all action event listeners
    document.getElementById('shareStoryBtn')?.addEventListener('click', handleShareStory);
    document.getElementById('downloadStoryBtn')?.addEventListener('click', handleDownloadClick);
    document.getElementById('download-txt-btn')?.addEventListener('click', () => downloadFile('txt'));
    document.getElementById('download-pdf-btn')?.addEventListener('click', () => downloadFile('pdf'));
    document.getElementById('download-docx-btn')?.addEventListener('click', () => downloadFile('docx'));
    
    // Theme integration
    window.addEventListener('themeChanged', (e) => {
        console.log(`Theme changed to: ${e.detail.theme}`);
    });

    // Show user email in navbar when authenticated
    firebase.auth().onAuthStateChanged(user => {
        const userEmailElement = document.getElementById('user-email');
        if (user && userEmailElement) {
            userEmailElement.textContent = user.email;
            userEmailElement.style.display = 'block';
        } else if (userEmailElement) {
            userEmailElement.style.display = 'none';
        }
        handleRouteChange();
    });

    // Main navigation listeners (these must remain at the end of DOMContentLoaded)
    document.getElementById('go-to-new-campaign').onclick = () => {
        isNavigatingToNewCampaignDirectly = true;
        history.pushState({}, '', '/new-campaign'); 
        handleRouteChange(); 
        
        // CRITICAL FIX: Enable wizard after navigation completes
        if (window.campaignWizard) {
            window.campaignWizard.enable();
        }
    };
    document.getElementById('back-to-dashboard').onclick = () => { history.pushState({}, '', '/'); handleRouteChange(); };
    window.addEventListener('popstate', handleRouteChange);
});

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

    // Helper function for scrolling
    const scrollToBottom = (element) => { 
        console.log(`Scrolling element: ${element.id}, current scrollHeight: ${element.scrollHeight}, clientHeight: ${element.clientHeight}`);
        element.scrollTop = element.scrollHeight; 
    };

    // --- Core UI & Navigation Logic ---
    const showSpinner = () => loadingOverlay.style.display = 'flex';
    const hideSpinner = () => loadingOverlay.style.display = 'none';
    
    // MODIFIED: Use CSS classes to control view visibility
    const showView = (viewName) => {
        Object.values(views).forEach(v => v.classList.remove('active-view')); // Remove from all views
        if(views[viewName]) {
            views[viewName].classList.add('active-view'); // Add to the target view
        }
    };

    let handleRouteChange = () => {
        if (!firebase.auth().currentUser) { showView('auth'); return; }
        const path = window.location.pathname;
        const campaignIdMatch = path.match(/^\/game\/([a-zA-Z0-9]+)/);
        if (campaignIdMatch) {
            currentCampaignId = campaignIdMatch[1];
            resumeCampaign(currentCampaignId);
        } else if (path === '/new-campaign') {
            showView('newCampaign');
        } else {
            currentCampaignId = null;
            renderCampaignList();
            showView('dashboard');
        }
    };
    
    const appendToStory = (actor, text, mode = null) => {
        const storyContainer = document.getElementById('story-content');
        const entryEl = document.createElement('p');
        let label = '';
        if (actor === 'gemini') {
            label = 'Story';
        } else { // actor is 'user'
            label = mode === 'character' ? 'Main Character' : (mode === 'god' ? 'God' : 'You');
        }
        
        entryEl.innerHTML = `<strong>${label}:</strong> ${text}`;
        storyContainer.appendChild(entryEl);
    };

    // --- Data Fetching and Rendering ---
    let renderCampaignList = async () => {
        showSpinner();
        try {
            const { data: campaigns } = await fetchApi('/api/campaigns');
            const listEl = document.getElementById('campaign-list');
            listEl.innerHTML = '';
            if (campaigns.length === 0) { listEl.innerHTML = '<p>You have no campaigns. Start a new one!</p>'; }
            campaigns.forEach(campaign => {
                const campaignEl = document.createElement('div');
                campaignEl.className = 'list-group-item list-group-item-action';
                campaignEl.innerHTML = `<div class="d-flex w-100 justify-content-between"><h5 class="mb-1">${campaign.title}</h5><small>Last played: ${new Date(campaign.last_played).toLocaleString()}</small></div><p class="mb-1">${campaign.initial_prompt.substring(0, 100)}...</p>`;
                campaignEl.onclick = () => {
                    history.pushState({ campaignId: campaign.id }, '', `/game/${campaign.id}`);
                    handleRouteChange();
                };
                listEl.appendChild(campaignEl);
            });
        } catch (error) { console.error("Error fetching campaigns:", error); }
        finally { hideSpinner(); }
    };

    let resumeCampaign = async (campaignId) => {
        showSpinner();
        try {
            const { data } = await fetchApi(`/api/campaigns/${campaignId}`);
            document.getElementById('game-title').innerText = data.campaign.title;
            const storyContainer = document.getElementById('story-content');
            storyContainer.innerHTML = '';
            data.story.forEach(entry => appendToStory(entry.actor, entry.text, entry.mode)); // Pass existing mode if available
            
            // Add a slight delay to allow rendering before scrolling
            console.log("Attempting to scroll after content append, with a slight delay.");
            setTimeout(() => scrollToBottom(storyContainer), 100); // 100ms delay
            
            showView('game');
        } catch (error) {
            console.error('Failed to resume campaign:', error);
            history.pushState({}, '', '/');
            handleRouteChange();
        } finally {
            hideSpinner();
        }
    };
    
    // --- Event Listeners ---
    // RE-ADDED: New Campaign Form Submission Listener
    document.getElementById('new-campaign-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        showSpinner();
        const prompt = document.getElementById('campaign-prompt').value;
        const title = document.getElementById('campaign-title').value;
        try {
            const { data } = await fetchApi('/api/campaigns', { method: 'POST', body: JSON.stringify({ prompt, title }) });
            history.pushState({ campaignId: data.campaign_id }, '', `/game/${data.campaign_id}`);
            handleRouteChange();
        } catch (error) {
            console.error("Error creating campaign:", error);
            alert('Failed to start a new campaign.');
            hideSpinner();
        }
    });


    const interactionForm = document.getElementById('interaction-form');
    const userInputEl = document.getElementById('user-input');

    // NEW: Listen for Enter key press on the textarea
    if (userInputEl) {
        userInputEl.addEventListener('keydown', (e) => {
            // Check for Enter key (keyCode 13 or key property 'Enter')
            // And ensure Shift or Ctrl/Cmd are NOT pressed (to allow multiline input with Shift+Enter)
            if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey) {
                e.preventDefault(); // Prevent default newline behavior
                if (interactionForm) {
                    interactionForm.dispatchEvent(new Event('submit', { cancelable: true })); // Trigger form submission
                }
            }
        });
    }

    if (interactionForm) { // Ensure the form exists before adding listener
        interactionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            let userInput = userInputEl.value.trim();
            if (!userInput || !currentCampaignId) return;
            const mode = document.querySelector('input[name="interactionMode"]:checked').value;
            const localSpinner = document.getElementById('loading-spinner');
            const timerInfo = document.getElementById('timer-info');
            localSpinner.style.display = 'block';
            userInputEl.disabled = true;
            timerInfo.textContent = '';
            appendToStory('user', userInput, mode); // Pass the selected mode here
            userInputEl.value = ''; // Clear input after appending
            try {
                const { data, duration } = await fetchApi(`/api/campaigns/${currentCampaignId}/interaction`, {
                    method: 'POST', body: JSON.stringify({ input: userInput, mode }),
                });
                appendToStory('gemini', data.response);
                timerInfo.textContent = `Response time: ${duration}s`;
            } catch (error) {
                console.error("Interaction failed:", error);
                appendToStory('system', 'Sorry, an error occurred. Please try again.');
            } finally {
                localSpinner.style.display = 'none';
                userInputEl.disabled = false;
                userInputEl.focus();
            }
        });
    }
    
    document.getElementById('go-to-new-campaign').onclick = () => { history.pushState({}, '', '/new-campaign'); handleRouteChange(); };
    document.getElementById('back-to-dashboard').onclick = () => { history.pushState({}, '', '/'); handleRouteChange(); };
    window.addEventListener('popstate', handleRouteChange);
    firebase.auth().onAuthStateChanged(user => handleRouteChange());
});

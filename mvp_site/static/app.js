document.addEventListener('DOMContentLoaded', () => {
    // --- State and Constants ---
    const views = { auth: document.getElementById('auth-view'), dashboard: document.getElementById('dashboard-view'), newCampaign: document.getElementById('new-campaign-view'), game: document.getElementById('game-view') };
    const loadingOverlay = document.getElementById('loading-overlay');
    let currentCampaignId = null;

    // --- Core UI & Navigation Logic ---
    const showSpinner = () => loadingOverlay.style.display = 'flex';
    const hideSpinner = () => loadingOverlay.style.display = 'none';
    const showView = (viewName) => { Object.values(views).forEach(v => v.style.display = 'none'); if(views[viewName]) views[viewName].style.display = 'block'; };
    const scrollToBottom = (element) => { element.scrollTop = element.scrollHeight; };

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
            showView('game');
            scrollToBottom(storyContainer);
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

    document.getElementById('interaction-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const userInputEl = document.getElementById('user-input');
        let userInput = userInputEl.value.trim();
        if (!userInput || !currentCampaignId) return;
        const mode = document.querySelector('input[name="interactionMode"]:checked').value;
        const localSpinner = document.getElementById('loading-spinner');
        const timerInfo = document.getElementById('timer-info');
        localSpinner.style.display = 'block';
        userInputEl.disabled = true;
        timerInfo.textContent = '';
        appendToStory('user', userInput, mode); // Pass the selected mode here
        userInputEl.value = '';
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
    
    document.getElementById('go-to-new-campaign').onclick = () => { history.pushState({}, '', '/new-campaign'); handleRouteChange(); };
    document.getElementById('back-to-dashboard').onclick = () => { history.pushState({}, '', '/'); handleRouteChange(); };
    window.addEventListener('popstate', handleRouteChange);
    firebase.auth().onAuthStateChanged(user => handleRouteChange());
});

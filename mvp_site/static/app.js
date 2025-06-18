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
    
    const showView = (viewName) => {
        Object.values(views).forEach(v => v.classList.remove('active-view'));
        if(views[viewName]) {
            views[viewName].classList.add('active-view');
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
            // Show the Share and Download buttons
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
        showSpinner();
        const prompt = document.getElementById('campaign-prompt').value;
        const title = document.getElementById('campaign-title').value;
        const selectedPrompts = Array.from(document.querySelectorAll('input[name="selectedPrompts"]:checked')).map(checkbox => checkbox.value);
        try {
            const { data } = await fetchApi('/api/campaigns', { 
                method: 'POST', 
                body: JSON.stringify({ prompt, title, selected_prompts: selectedPrompts }) 
            });
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
            userInputEl.disabled = true;
            timerInfo.textContent = '';
            appendToStory('user', userInput, mode);
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
    }
    
    document.getElementById('go-to-new-campaign').onclick = () => { history.pushState({}, '', '/new-campaign'); handleRouteChange(); };
    document.getElementById('back-to-dashboard').onclick = () => { history.pushState({}, '', '/'); handleRouteChange(); };
    window.addEventListener('popstate', handleRouteChange);
    firebase.auth().onAuthStateChanged(user => handleRouteChange());
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
    document.getElementById('loading-overlay').style.display = 'flex';
    try {
        const user = firebase.auth().currentUser;
        if (!user) throw new Error('User not authenticated');
        const token = await user.getIdToken();

        const response = await fetch(`/api/campaigns/${currentCampaignId}/export?format=${format}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error(`Download failed: ${response.statusText}`);

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        
        const disposition = response.headers.get('content-disposition');
        let filename = `story.${format}`;
        if (disposition && disposition.indexOf('attachment') !== -1) {
            const filenameRegex = /filename[^;=\\n]*=((['"]).*?\\2|[^;\\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error("Download failed:", error);
        alert("Could not download the story.");
    } finally {
        document.getElementById('loading-overlay').style.display = 'none';
        const modalElement = document.getElementById('downloadOptionsModal');
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) modal.hide();
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
    try {
        await navigator.share({ title: storyTitle, text: storyText });
    } catch (error) {
        console.error('Error sharing story:', error);
    }
}

function handleDownloadClick() {
    const downloadModal = new bootstrap.Modal(document.getElementById('downloadOptionsModal'));
    downloadModal.show();
}

// Attach all event listeners
function addActionListeners() {
    document.getElementById('shareStoryBtn')?.addEventListener('click', handleShareStory);
    document.getElementById('downloadStoryBtn')?.addEventListener('click', handleDownloadClick);
    document.getElementById('download-txt-btn')?.addEventListener('click', () => downloadFile('txt'));
    document.getElementById('download-pdf-btn')?.addEventListener('click', () => downloadFile('pdf'));
    document.getElementById('download-docx-btn')?.addEventListener('click', () => downloadFile('docx'));
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addActionListeners);
} else {
    addActionListeners();
}

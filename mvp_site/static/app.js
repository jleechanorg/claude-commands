document.addEventListener('DOMContentLoaded', () => {
    // --- State and Constants ---
    const views = {
        auth: document.getElementById('auth-view'),
        dashboard: document.getElementById('dashboard-view'),
        newCampaign: document.getElementById('new-campaign-view'),
        game: document.getElementById('game-view'),
    };
    const loggedInUser = () => firebase.auth().currentUser;

    // --- Core Navigation Logic ---
    const showView = (viewName) => {
        Object.values(views).forEach(view => view.style.display = 'none');
        if (views[viewName]) views[viewName].style.display = 'block';
    };

    const handleRouteChange = () => {
        if (!loggedInUser()) {
            showView('auth');
            return;
        }

        const path = window.location.pathname;
        const campaignIdMatch = path.match(/^\/game\/([a-zA-Z0-9]+)/);

        if (campaignIdMatch) {
            const campaignId = campaignIdMatch[1];
            resumeCampaign(campaignId);
        } else if (path === '/new-campaign') {
            showView('newCampaign');
        } else {
            // Default to dashboard
            renderCampaignList();
            showView('dashboard');
        }
    };
    
    // --- Data Fetching and Rendering ---
    const renderCampaignList = async () => {
        try {
            const { data: campaigns } = await fetchApi('/api/campaigns');
            const listEl = document.getElementById('campaign-list');
            listEl.innerHTML = '';
            if (campaigns.length === 0) {
                listEl.innerHTML = '<p>You have no campaigns. Start a new one!</p>';
                return;
            }
            campaigns.forEach(campaign => {
                const campaignEl = document.createElement('div');
                campaignEl.className = 'list-group-item list-group-item-action';
                campaignEl.innerHTML = `
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">${campaign.title}</h5>
                        <small>Last played: ${new Date(campaign.last_played).toLocaleString()}</small>
                    </div>
                    <p class="mb-1">${campaign.initial_prompt.substring(0, 100)}...</p>
                `;
                campaignEl.onclick = () => {
                    history.pushState({ campaignId: campaign.id }, '', `/game/${campaign.id}`);
                    handleRouteChange();
                };
                listEl.appendChild(campaignEl);
            });
        } catch (error) {
            console.error("Error fetching campaigns:", error);
        }
    };

    const resumeCampaign = async (campaignId) => {
        try {
            const { data } = await fetchApi(`/api/campaigns/${campaignId}`);
            document.getElementById('game-title').innerText = data.campaign.title;
            const storyText = data.story.map(entry => `<p><strong>${entry.actor}:</strong> ${entry.text}</p>`).join('');
            document.getElementById('story-content').innerHTML = storyText;
            showView('game');
        } catch (error) {
            console.error('Failed to resume campaign:', error);
            history.pushState({}, '', '/');
            handleRouteChange();
        }
    };
    
    // --- Event Listeners ---
    document.getElementById('go-to-new-campaign').addEventListener('click', () => {
        history.pushState({}, '', '/new-campaign');
        handleRouteChange();
    });

    document.getElementById('back-to-dashboard').addEventListener('click', () => {
        history.pushState({}, '', '/');
        handleRouteChange();
    });

    document.getElementById('new-campaign-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const prompt = document.getElementById('campaign-prompt').value;
        const title = document.getElementById('campaign-title').value;
        try {
            await fetchApi('/api/campaigns', {
                method: 'POST',
                body: JSON.stringify({ prompt, title }),
            });
            history.pushState({}, '', '/');
            handleRouteChange();
        } catch (error) {
            console.error("Error creating campaign:", error);
            alert('Failed to start a new campaign.');
        }
    });

    // Listen for browser back/forward button clicks
    window.addEventListener('popstate', handleRouteChange);

    // Initial route handling
    firebase.auth().onAuthStateChanged(user => {
        handleRouteChange(); // Let the router decide which view to show
    });
});

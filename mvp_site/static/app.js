document.addEventListener('DOMContentLoaded', () => {
    const views = {
        auth: document.getElementById('auth-view'),
        dashboard: document.getElementById('dashboard-view'),
        newCampaign: document.getElementById('new-campaign-view'),
        game: document.getElementById('game-view'),
    };

    let currentStory = [];
    let currentPage = 0;
    const WORDS_PER_PAGE = 300;

    const showView = (viewName) => {
        Object.values(views).forEach(view => view.style.display = 'none');
        if (views[viewName]) views[viewName].style.display = 'block';
    };

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
                campaignEl.onclick = () => resumeCampaign(campaign.id);
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
            const storyContainer = document.getElementById('story-content');
            storyContainer.innerHTML = storyText;
            showView('game');
        } catch (error) {
            console.error('Failed to resume campaign:', error);
        }
    };
    
    document.getElementById('go-to-new-campaign').addEventListener('click', () => showView('newCampaign'));
    document.getElementById('back-to-dashboard').addEventListener('click', () => {
        renderCampaignList();
        showView('dashboard');
    });

    document.getElementById('new-campaign-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const prompt = document.getElementById('campaign-prompt').value;
        const title = document.getElementById('campaign-title').value;
        try {
            const { data } = await fetchApi('/api/campaigns', {
                method: 'POST',
                body: JSON.stringify({ prompt, title }),
            });
            await renderCampaignList();
            showView('dashboard');
        } catch (error) {
            console.error("Error creating campaign:", error);
            alert('Failed to start a new campaign.');
        }
    });

    firebase.auth().onAuthStateChanged(user => {
        if (user) {
            renderCampaignList();
            showView('dashboard');
        } else {
            showView('auth');
        }
    });
});

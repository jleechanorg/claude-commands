document.addEventListener('DOMContentLoaded', () => {
    const views = {
        auth: document.getElementById('auth-view'),
        newCampaign: document.getElementById('new-campaign-view'),
        game: document.getElementById('game-view'),
    };

    const showView = (viewName) => {
        Object.values(views).forEach(view => view.style.display = 'none');
        if (views[viewName]) {
            views[viewName].style.display = 'block';
        }
    };

    // Form handling
    const newCampaignForm = document.getElementById('new-campaign-form');
    newCampaignForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const prompt = document.getElementById('campaign-prompt').value;
        const title = document.getElementById('campaign-title').value;

        try {
            const result = await fetchApi('/api/campaigns', {
                method: 'POST',
                body: JSON.stringify({ prompt, title }),
            });
            
            // For now, just log the result and show the game view
            console.log("Campaign created:", result);
            document.getElementById('story-content').innerHTML = `<p>${result.opening_story}</p>`;
            showView('game');

        } catch (error) {
            console.error("Error creating campaign:", error);
            alert('Failed to start a new campaign. Check the console.');
        }
    });


    // Listen for auth changes to control view
    firebase.auth().onAuthStateChanged(user => {
        if (user) {
            showView('newCampaign');
        } else {
            showView('auth');
        }
    });
});

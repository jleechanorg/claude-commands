/**
 * Example integration of mock service with Frontend v2 components
 *
 * This file demonstrates how to use the mock service for development
 * and testing purposes.
 */

import React, { useState, useEffect } from 'react';
import { mockApiService } from './mock.service';
import { Campaign, StoryEntry, InteractionResponse } from './api.types';

// Example: Mock-enabled Campaign List Component
export function MockEnabledCampaignList() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      setError(null);

      // Use mock service
      const data = await mockApiService.getCampaigns();
      setCampaigns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading campaigns...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Your Campaigns ({campaigns.length})</h2>
      {campaigns.map(campaign => (
        <div key={campaign.id}>
          <h3>{campaign.title}</h3>
          <p>{campaign.prompt}</p>
          <small>Last played: {new Date(campaign.last_played).toLocaleDateString()}</small>
        </div>
      ))}
    </div>
  );
}

// Example: Mock-enabled Game Play Component
export function MockEnabledGamePlay({ campaignId }: { campaignId: string }) {
  const [story, setStory] = useState<StoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState('');

  useEffect(() => {
    loadCampaignDetails();
  }, [campaignId]);

  const loadCampaignDetails = async () => {
    try {
      const details = await mockApiService.getCampaign(campaignId);
      setStory(details.story);
    } catch (err) {
      console.error('Failed to load campaign:', err);
    }
  };

  const sendAction = async () => {
    if (!input.trim()) return;

    try {
      setLoading(true);

      // Send interaction
      const response = await mockApiService.sendInteraction(campaignId, {
        input,
        mode: 'character'
      });

      // Reload story to see the update
      await loadCampaignDetails();
      setInput('');
    } catch (err) {
      console.error('Failed to send action:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="story-area">
        {story.map((entry, idx) => (
          <div key={idx} className={`story-entry ${entry.actor}`}>
            <strong>{entry.actor}:</strong> {entry.text}
            {entry.narrative && <p className="narrative">{entry.narrative}</p>}
            {entry.dice_rolls && (
              <div className="dice-rolls">
                {entry.dice_rolls.map((roll, i) => (
                  <span key={i}>
                    {roll.type}: {roll.result} + {roll.modifier} = {roll.total}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="What do you do?"
          disabled={loading}
        />
        <button onClick={sendAction} disabled={loading}>
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </div>
    </div>
  );
}

// Example: Error Testing Component
export function ErrorTestingPanel() {
  const [errorRate, setErrorRate] = useState(5);

  const testScenarios = [
    { type: 'timeout', label: 'Network Timeout' },
    { type: 'validation', label: 'Validation Error' },
    { type: 'auth_failed', label: 'Auth Failure' },
    { type: 'server_error', label: 'Server Error (500)' },
    { type: 'rate_limit', label: 'Rate Limit' },
    { type: 'service_unavailable', label: 'Service Unavailable (503)' }
  ];

  const updateErrorRate = (rate: number) => {
    setErrorRate(rate);
    mockApiService.setErrorRate(rate / 100);
  };

  const triggerError = async (errorType: string) => {
    try {
      await mockApiService.simulateError(errorType as any);
    } catch (err) {
      alert(`Error triggered: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="error-testing-panel">
      <h3>Error Testing Panel</h3>

      <div>
        <label>Random Error Rate: {errorRate}%</label>
        <input
          type="range"
          min="0"
          max="100"
          value={errorRate}
          onChange={(e) => updateErrorRate(Number(e.target.value))}
        />
      </div>

      <div>
        <h4>Trigger Specific Errors:</h4>
        {testScenarios.map(scenario => (
          <button
            key={scenario.type}
            onClick={() => triggerError(scenario.type)}
          >
            {scenario.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// Example: Mock Data Explorer
export function MockDataExplorer() {
  const [activeTab, setActiveTab] = useState<'campaigns' | 'users' | 'achievements'>('campaigns');

  return (
    <div className="mock-data-explorer">
      <h3>Mock Data Explorer</h3>

      <div className="tabs">
        <button
          className={activeTab === 'campaigns' ? 'active' : ''}
          onClick={() => setActiveTab('campaigns')}
        >
          Campaigns
        </button>
        <button
          className={activeTab === 'users' ? 'active' : ''}
          onClick={() => setActiveTab('users')}
        >
          Users
        </button>
        <button
          className={activeTab === 'achievements' ? 'active' : ''}
          onClick={() => setActiveTab('achievements')}
        >
          Achievements
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'campaigns' && <CampaignExplorer />}
        {activeTab === 'users' && <UserExplorer />}
        {activeTab === 'achievements' && <AchievementExplorer />}
      </div>
    </div>
  );
}

// Sub-components for Mock Data Explorer
function CampaignExplorer() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);

  useEffect(() => {
    // Switch to different test users to see their campaigns
    mockApiService.setTestMode(true, 'user-pro');
    mockApiService.getCampaigns().then(setCampaigns);
  }, []);

  return (
    <div>
      <h4>Available Mock Campaigns</h4>
      <pre>{JSON.stringify(campaigns, null, 2)}</pre>
    </div>
  );
}

function UserExplorer() {
  const users = ['user-basic', 'user-pro', 'user-gm'];

  const switchUser = async (userId: string) => {
    mockApiService.setTestMode(true, userId);
    const user = await mockApiService.getCurrentUser();
    alert(`Switched to: ${user?.displayName} (${user?.email})`);
  };

  return (
    <div>
      <h4>Test Users</h4>
      {users.map(userId => (
        <button key={userId} onClick={() => switchUser(userId)}>
          Switch to {userId}
        </button>
      ))}
    </div>
  );
}

function AchievementExplorer() {
  const [achievements, setAchievements] = useState<any[]>([]);

  useEffect(() => {
    mockApiService.getAchievements().then(setAchievements);
  }, []);

  return (
    <div>
      <h4>Mock Achievements</h4>
      {achievements.map(achievement => (
        <div key={achievement.id}>
          <span>{achievement.icon}</span>
          <strong>{achievement.name}</strong>
          {achievement.unlocked ? ' ✓' : ` (${achievement.progress}/${achievement.total})`}
        </div>
      ))}
    </div>
  );
}

// Example: Development Mode Toggle
export function DevelopmentModeToggle() {
  const [mockMode, setMockMode] = useState(true);
  const [testUserId, setTestUserId] = useState('user-pro');

  const toggleMode = () => {
    if (!mockMode) {
      // Enable mock mode
      mockApiService.setTestMode(true, testUserId);
      setMockMode(true);
    } else {
      // Disable mock mode (would use real API)
      mockApiService.setTestMode(false);
      setMockMode(false);
    }
  };

  return (
    <div className="dev-mode-toggle">
      <label>
        <input
          type="checkbox"
          checked={mockMode}
          onChange={toggleMode}
        />
        Use Mock Data
      </label>

      {mockMode && (
        <select
          value={testUserId}
          onChange={(e) => {
            setTestUserId(e.target.value);
            mockApiService.setTestMode(true, e.target.value);
          }}
        >
          <option value="user-basic">Basic User</option>
          <option value="user-pro">Pro User</option>
          <option value="user-gm">Game Master</option>
        </select>
      )}
    </div>
  );
}

// Example: How to integrate with existing components
export function IntegrationExample() {
  // In your main App component or wherever you initialize:
  useEffect(() => {
    // Enable mock mode for development
    if (process.env.NODE_ENV === 'development') {
      mockApiService.setTestMode(true, 'user-pro');
      console.log('Mock mode enabled for development');
    }

    // Listen to auth state changes
    const unsubscribe = mockApiService.onAuthStateChanged((user) => {
      console.log('Auth state changed:', user);
      // Update your app's auth state here
    });

    return unsubscribe;
  }, []);

  return (
    <div>
      <h1>WorldArchitect.AI - Development Mode</h1>
      <DevelopmentModeToggle />
      <ErrorTestingPanel />
      <MockDataExplorer />
    </div>
  );
}

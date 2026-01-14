/* global bootstrap, fetchApi, UIUtils, firebase, loadSettings, saveSettings, toggleProviderSections, InlineEditor */

document.addEventListener('DOMContentLoaded', () => {
  // Check for test mode
  const urlParams = new URLSearchParams(window.location.search);
  const isTestMode = urlParams.get('test_mode') === 'true';

  // Initialize test mode if enabled
  if (isTestMode) {
    const testUserId = urlParams.get('test_user_id') || 'test-user-123';
    window.testAuthBypass = { enabled: true, userId: testUserId };
    console.log(`Test mode initialized for user: ${testUserId}`);
    // Dispatch event after a short delay to ensure listeners are registered
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('testModeReady', { detail: { userId: testUserId } }));
    }, 100);
  }

  // --- State and Constants ---
  const views = {
    auth: document.getElementById('auth-view'),
    dashboard: document.getElementById('dashboard-view'),
    newCampaign: document.getElementById('new-campaign-view'),
    game: document.getElementById('game-view'),
  };
  const loadingOverlay = document.getElementById('loading-overlay');
  let currentCampaignId = null;
  let campaignToEdit = null;
  let isNavigatingToNewCampaignDirectly = false;

  // Initialize Bootstrap tooltips for mode selection buttons
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggerList.forEach((tooltipTriggerEl) => {
    bootstrap.Tooltip.getOrCreateInstance(tooltipTriggerEl);
  });

  // Helper function for scrolling
  const scrollToBottom = (element) => {
    console.log(
      `Scrolling element: ${element.id}, current scrollHeight: ${element.scrollHeight}, clientHeight: ${element.clientHeight}`,
    );
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

  // Shared helper for character info queries (equipment, stats, spells)
  // Uses dedicated API endpoints for fast, deterministic responses
  const handleInfoQuery = async ({ endpoint, builder, summaryKey, errorMsg }) => {
    if (!currentCampaignId) {
      console.warn(`No campaign loaded - cannot fetch ${endpoint}`);
      return;
    }

    const userInputEl = document.getElementById('user-input');
    const localSpinner = document.getElementById('loading-spinner');
    const timerInfo = document.getElementById('timer-info');

    // Show spinner and disable input
    if (localSpinner) localSpinner.style.display = 'block';
    if (window.loadingMessages) {
      const messageEl = localSpinner?.querySelector('.loading-message');
      if (messageEl) window.loadingMessages.start('interaction', messageEl);
    }
    if (userInputEl) userInputEl.disabled = true;
    if (timerInfo) timerInfo.textContent = '';

    try {
      const { data, duration } = await fetchApi(
        `/api/campaigns/${currentCampaignId}/${endpoint}`,
        { method: 'GET' },
      );

      const html = builder ? builder(data) : null;
      const fallbackText = data?.[summaryKey] || `No ${endpoint} information available.`;
      appendToStory('system', html || fallbackText, null, false, null, null, {
        isHtml: Boolean(html),
      });
      if (timerInfo) timerInfo.textContent = `Response time: ${duration}s`;
    } catch (error) {
      console.error(`${endpoint} query failed:`, error);
      appendToStory('system', errorMsg);
    } finally {
      if (localSpinner) localSpinner.style.display = 'none';
      if (window.loadingMessages) window.loadingMessages.stop();
      if (userInputEl) {
        userInputEl.disabled = false;
        userInputEl.focus();
      }
    }
  };

  // Global functions for quick action buttons - use dedicated API endpoints
  window.sendEquipmentQuery = () =>
    handleInfoQuery({
      endpoint: 'equipment',
      builder: buildEquipmentHTML,
      summaryKey: 'equipment_summary',
      errorMsg: 'Sorry, an error occurred fetching equipment.',
    });

  // Stats display with BG3-style HTML tables
  window.sendStatsQuery = () =>
    handleInfoQuery({
      endpoint: 'stats',
      builder: buildStatsHTML,
      summaryKey: 'stats_summary',
      errorMsg: 'Sorry, an error occurred fetching stats.',
    });

  window.sendSpellsQuery = () =>
    handleInfoQuery({
      endpoint: 'spells',
      builder: buildSpellsHTML,
      summaryKey: 'spells_summary',
      errorMsg: 'Sorry, an error occurred fetching spells.',
    });

  const renderInfoTable = ({ headers = [], rows = [], compact = false, extraClass = '' }) => {
    const tableClass = `info-table ${compact ? 'compact-table' : ''} ${extraClass}`.trim();
    let table = `<table class="${tableClass}">`;
    if (headers.length) {
      table += `<thead><tr>${headers.map((h) => `<th>${sanitizeHtml(h)}</th>`).join('')}</tr></thead>`;
    }
    table += '<tbody>';
    rows.forEach((row) => {
      table += `<tr>${row.map((cell) => {
        const safe = sanitizeHtml(String(cell ?? '—'));
        return `<td>${safe}</td>`;
      }).join('')}</tr>`;
    });
    table += '</tbody></table>';
    return table;
  };

  // Build neutral, game-chat friendly stats UI using structured JSON
  const buildStatsHTML = (data) => {
    if (!data || !data.success) {
      return data?.stats_summary || 'No stats available.';
    }

    const combat = data.combat_stats || {};
    const effective = data.effective_stats || {};
    const naked = data.naked_stats || {};
    const features = data.features || [];
    const spellStats = combat.spell_stats;
    const savingThrows = combat.saving_throws || [];

    const fmtMod = (mod) => {
      const n = parseInt(mod, 10);
      if (Number.isNaN(n)) return '+0';
      return n >= 0 ? `+${n}` : `${n}`;
    };

    const getStat = (stats, key) => {
      const s = stats[key];
      if (!s) return { score: 10, modifier: '+0' };
      return { score: s.score ?? 10, modifier: s.modifier ?? '+0' };
    };

    let html = '<div class="stats-panel info-card">';
    html += '<div class="stats-header info-header">';
    html += `<span class="stat-badge info-badge">Level ${combat.level || '?'}</span>`;
    html += `<span class="stat-badge info-badge">HP ${combat.hp_current || 0}/${combat.hp_max || 0}</span>`;
    html += `<span class="stat-badge info-badge">AC ${combat.ac || 10}${combat.effective_ac && combat.effective_ac !== combat.ac ? ` → ${combat.effective_ac}` : ''}</span>`;
    html += `<span class="stat-badge info-badge">Initiative ${fmtMod(combat.initiative)}</span>`;
    if (combat.speed) {
      const speedText = /\bft\b/i.test(String(combat.speed))
        ? String(combat.speed)
        : `${combat.speed} ft`;
      html += `<span class="stat-badge info-badge">Speed ${speedText}</span>`;
    }
    html += `<span class="stat-badge info-badge">Prof ${fmtMod(combat.proficiency_bonus)}</span>`;

    // Hit Dice
    if (combat.hit_dice) {
      const hitDiceText = combat.hit_dice_current !== null && combat.hit_dice_current !== undefined
        ? `${combat.hit_dice_current}/${combat.hit_dice_max} ${combat.hit_dice}`
        : combat.hit_dice;
      html += `<span class="stat-badge info-badge">Hit Dice ${hitDiceText}</span>`;
    }
    html += '</div>';

    if (spellStats) {
      html += '<div class="stats-spellcasting info-subrow">';
      html += `<span class="stat-badge spell info-badge">Spell DC ${spellStats.spell_save_dc}</span>`;
      html += `<span class="stat-badge spell info-badge">Spell Attack ${fmtMod(spellStats.spell_attack_bonus)}</span>`;
      html += `<span class="stat-badge spell info-badge">${spellStats.spellcasting_ability}</span>`;
      html += '</div>';
    }

    html += '<div class="info-section-title">Ability Scores</div>';
    const abilityRows = ['str', 'dex', 'con', 'int', 'wis', 'cha'].map((stat) => {
      const eff = getStat(effective, stat);
      const base = getStat(naked, stat);
      const bonus = data.equipment_bonuses?.[stat];
      return [
        stat.toUpperCase(),
        base.score,
        bonus ? `${base.score} → ${eff.score}` : eff.score,
        fmtMod(eff.modifier),
        bonus ? fmtMod(bonus) : '—',
      ];
    });
    html += renderInfoTable({
      headers: ['Stat', 'Base', 'Effective', 'Mod', 'Bonus'],
      rows: abilityRows,
      compact: true,
    });

    if (savingThrows.length) {
      html += '<div class="info-section-title">Saving Throws</div>';
      const saveRows = savingThrows.map((save) => {
        const label = save?.stat?.toUpperCase?.() || '';
        const proficient = save?.proficient ? '●' : '○';
        return [label, fmtMod(save?.bonus || 0), proficient];
      });
      html += renderInfoTable({ headers: ['Save', 'Bonus', 'Prof'], rows: saveRows, compact: true });
    }

    if (features.length > 0) {
      const safeFeatures = features.filter(f => f).map(f => sanitizeHtml(f)).join(', ');
      html += `<div class="features-section info-block"><strong>Features:</strong> ${safeFeatures}</div>`;
    }

    if (data.stats_summary) {
      const summary = data.stats_summary;
      const sections = ['▸ Skills:', '▸ Passives:', '▸ Weapons:'];
      let extraContent = '';
      // Fallback: parse summary sections by markers until backend provides structured JSON.
      sections.forEach((section) => {
        const idx = summary.indexOf(section);
        if (idx >= 0) {
          const nextIdx = summary.indexOf('▸', idx + 1);
          const sectionContent = nextIdx > 0 ? summary.slice(idx, nextIdx) : summary.slice(idx);
          extraContent += `<pre class="stats-section">${sanitizeHtml(sectionContent.trim())}</pre>`;
        }
      });
      if (extraContent) html += extraContent;
    }

    html += '</div>';
    return html;
  };

  const buildEquipmentHTML = (data) => {
    if (!data || !data.success) {
      return data?.equipment_summary || 'No equipment available.';
    }

    const equipmentList = Array.isArray(data.equipment_list) ? data.equipment_list : [];
    let html = '<div class="stats-panel info-card">';
    html += '<div class="stats-header info-header">';
    html += '<span class="stat-badge info-badge">Equipment</span>';
    html += `<span class="info-subtext">${equipmentList.length || 0} items</span>`;
    html += '</div>';

    if (equipmentList.length) {
      const equipmentRows = equipmentList.map((item) => {
        if (!item || typeof item !== 'object') {
          return ['—', 'Unknown item', '—'];
        }
        const slot = item.slot || item.category || '—';
        const name = item.name || item.item || 'Unknown item';
        const details = item.stats || item.description || item.effects || '';
        return [slot, name, details || '—'];
      });
      html += renderInfoTable({ headers: ['Slot', 'Item', 'Details'], rows: equipmentRows, compact: true });
    } else {
      html += '<div class="info-subtext">No equipment found.</div>';
    }

    if (data.equipment_summary) {
      html += `<pre class="stats-section">${sanitizeHtml(data.equipment_summary)}</pre>`;
    }

    html += '</div>';
    return html;
  };

  const buildSpellsHTML = (data) => {
    if (!data || !data.success) {
      return data?.spells_summary || 'No spells available.';
    }

    const spellSlots = data.spell_slots || {};
    const cantrips = Array.isArray(data.cantrips) ? data.cantrips : [];
    const spellsPrepared = Array.isArray(data.spells_prepared) ? data.spells_prepared : [];
    const spellsKnown = Array.isArray(data.spells_known) ? data.spells_known : [];
    const classResources = data.class_resources || {};
    const spellStats = data.spell_stats;

    const normalizeSpell = (spell) => {
      if (typeof spell === 'string') {
        return { name: spell, level: null };
      }
      if (spell && typeof spell === 'object') {
        return { name: spell.name || 'Unknown Spell', level: spell.level ?? null };
      }
      return { name: 'Unknown Spell', level: null };
    };

    const groupSpells = (spells) => {
      return spells.reduce((acc, raw) => {
        const { name, level } = normalizeSpell(raw);
        const key = level === null || level === undefined || level === '' ? '?' : level;
        if (!acc[key]) acc[key] = [];
        acc[key].push(name);
        return acc;
      }, {});
    };

    const renderSpellGroup = (label, spells) => {
      if (!spells.length) return '';
      const grouped = groupSpells(spells);
      let section = `<div class="info-section-title">${label}</div>`;
      const rows = Object.keys(grouped)
        .sort((a, b) => {
          const toNum = (val) => (String(val).match(/^\d+$/) ? parseInt(val, 10) : 99);
          return toNum(a) - toNum(b);
        })
        .map((level) => {
          const names = grouped[level].sort();
          const labelText = level === '0' ? 'Cantrip' : level === '?' ? '—' : `Level ${level}`;
          return [labelText, names.join(', ')];
        });
      section += renderInfoTable({ headers: ['Level', 'Spells'], rows, compact: true });
      return section;
    };

    const fmtMod = (mod) => {
      const n = parseInt(mod, 10);
      if (Number.isNaN(n)) return '+0';
      return n >= 0 ? `+${n}` : `${n}`;
    };

    let html = '<div class="stats-panel info-card">';
    html += '<div class="stats-header info-header">';
    html += '<span class="stat-badge info-badge">Spells & Resources</span>';
    if (Object.keys(spellSlots).length) {
      html += `<span class="info-subtext">Slots: ${Object.keys(spellSlots).length}</span>`;
    }
    html += '</div>';

    // Display spell DC and spell attack for spellcasters
    if (spellStats) {
      html += '<div class="stats-spellcasting info-subrow">';
      html += `<span class="stat-badge spell info-badge">Spell DC ${spellStats.spell_save_dc}</span>`;
      html += `<span class="stat-badge spell info-badge">Spell Attack ${fmtMod(spellStats.spell_attack_bonus)}</span>`;
      html += `<span class="stat-badge spell info-badge">${spellStats.spellcasting_ability}</span>`;
      html += '</div>';
    }

    if (Object.keys(spellSlots).length) {
      html += '<div class="info-section-title">Spell Slots</div>';
      const slotRows = Object.keys(spellSlots)
        .sort((a, b) => {
          const toNum = (val) => (String(val).match(/^\d+$/) ? parseInt(val, 10) : 99);
          return toNum(a) - toNum(b);
        })
        .map((level) => {
          const slot = spellSlots[level] || {};
          return [level, slot.current ?? '?', slot.max ?? '?'];
        });
      html += renderInfoTable({ headers: ['Level', 'Available', 'Max'], rows: slotRows, compact: true });
    }

    if (cantrips.length) {
      html += '<div class="info-section-title">Cantrips</div>';
      html += `<div class="info-block">${cantrips.map((c) => sanitizeHtml(normalizeSpell(c).name)).join(', ')}</div>`;
    }

    html += renderSpellGroup('Spells Prepared', spellsPrepared);
    if (spellsKnown.length && spellsPrepared.length) {
      html += renderSpellGroup('Spells Known', spellsKnown);
    } else if (spellsKnown.length && !spellsPrepared.length) {
      html += renderSpellGroup('Spells', spellsKnown);
    }

    if (classResources && Object.keys(classResources).length) {
      html += '<div class="info-section-title">Class Resources</div>';
      const resourceRows = Object.entries(classResources).map(([name, value]) => {
        if (value && typeof value === 'object') {
          const current = value.current ?? value.remaining ?? '?';
          const max = value.max ?? value.total ?? '?';
          return [name.replace(/_/g, ' '), `${current}/${max}`];
        }
        return [name.replace(/_/g, ' '), value ?? '—'];
      });
      html += renderInfoTable({ headers: ['Resource', 'Value'], rows: resourceRows, compact: true });
    }

    if (data.spells_summary) {
      html += `<pre class="stats-section">${sanitizeHtml(data.spells_summary)}</pre>`;
    }

    html += '</div>';
    return html;
  };

  const showView = (viewName) => {
    Object.values(views).forEach((v) => v && v.classList.remove('active-view'));
    if (views[viewName]) {
      views[viewName].classList.add('active-view');

      // Setup campaign type handlers when showing new campaign view
      if (viewName === 'newCampaign') {
        setupCampaignTypeHandlers();
        UIUtils.setupCollapsibleDescription(
          'toggle-description',
          'description-container',
        );
      }
    }
  };

  function resetNewCampaignForm() {
    // CRITICAL: Don't reset form if wizard is active - this destroys the wizard state
    if (window.campaignWizard && window.campaignWizard.isEnabled) {
      console.log('Skipping form reset - wizard is active');
      return;
    }

    const campaignTitleInput = document.getElementById('campaign-title');
    const campaignPromptTextarea = document.getElementById('campaign-prompt');
    const narrativeCheckbox = document.getElementById('prompt-narrative');
    const mechanicsCheckbox = document.getElementById('prompt-mechanics');

    if (campaignTitleInput) {
      campaignTitleInput.value = 'My Epic Adventure'; // Your default title
    }
    if (campaignPromptTextarea) {
      campaignPromptTextarea.value = window.DRAGON_KNIGHT_CAMPAIGN; // Default Dragon Knight prompt
    }
    if (narrativeCheckbox) {
      narrativeCheckbox.checked = true; // Default checked
    }
    if (mechanicsCheckbox) {
      mechanicsCheckbox.checked = true; // Default checked
    }
    console.log('New campaign form reset to defaults.');
  }

  // Dragon Knight campaign narrative
  const DRAGON_KNIGHT_NARRATIVE = `You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium. For decades, the Empire has been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her methods are terrifying, her reign has brought undeniable benefits: the roads are safe, commerce thrives, and the Imperium has never been stronger. But dark whispers speak of the Dragon Knights - an ancient order that once served the realm before mysteriously vanishing. As you journey through this morally complex world, you must decide: will you serve the tyrant who brings order, or seek a different path?`;

  // Handle campaign type radio button changes
  function setupCampaignTypeHandlers() {
    const dragonKnightRadio = document.getElementById('dragonKnightCampaign');
    const customRadio = document.getElementById('customCampaign');
    const descriptionTextarea = document.getElementById('description-input');

    if (!dragonKnightRadio || !customRadio || !descriptionTextarea) return;

    // Load Dragon Knight content on page load if it's checked
    if (dragonKnightRadio.checked) {
      descriptionTextarea.value = DRAGON_KNIGHT_NARRATIVE;

      // Also ensure default world is checked when Dragon Knight is selected
      const defaultWorldCheckbox = document.getElementById('use-default-world');
      if (defaultWorldCheckbox) {
        defaultWorldCheckbox.checked = true;
        defaultWorldCheckbox.disabled = true; // Disable to prevent unchecking
      }
    }

    dragonKnightRadio.addEventListener('change', async (e) => {
      if (e.target.checked) {
        // Pre-fill the description with Dragon Knight narrative
        descriptionTextarea.value = DRAGON_KNIGHT_NARRATIVE;

        // Force default world checkbox to be checked when Dragon Knight is selected
        const defaultWorldCheckbox =
          document.getElementById('use-default-world');
        if (defaultWorldCheckbox) {
          defaultWorldCheckbox.checked = true;
          defaultWorldCheckbox.disabled = true; // Disable to prevent unchecking
        }
      }
    });

    customRadio.addEventListener('change', (e) => {
      if (e.target.checked) {
        // Clear the description for custom campaigns
        descriptionTextarea.value = '';
        descriptionTextarea.focus();

        // Re-enable default world checkbox when custom campaign is selected
        const defaultWorldCheckbox =
          document.getElementById('use-default-world');
        if (defaultWorldCheckbox) {
          defaultWorldCheckbox.disabled = false; // Re-enable checkbox
        }
      }
    });
  }

  let handleRouteChange = () => {
    // In test mode, skip auth check
    if (!isTestMode) {
      // Only check Firebase auth if not in test mode
      if (!firebase.auth().currentUser) {
        showView('auth');
        return;
      }
    } else {
      console.log('📍 handleRouteChange called in test mode');
    }
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
    } else if (path === '/settings') {
      // Load settings within the SPA
      loadSettingsPage();
    } else {
      currentCampaignId = null;
      renderCampaignList();
      showView('dashboard');
    }
  };

  // Load settings page dynamically
  const loadSettingsPage = async () => {
    try {
      showSpinner('Loading settings...');

      // Fetch settings content from server
      const authHeaders = window.authTokenManager
        ? await window.authTokenManager.getAuthHeaders()
        : { Authorization: `Bearer ${await firebase.auth().currentUser.getIdToken()}` };

      const response = await fetch('/settings', {
        headers: authHeaders,
      });

      if (!response.ok) {
        throw new Error(`Failed to load settings: ${response.status}`);
      }

      const settingsHtml = await response.text();

      // Create settings view if it doesn't exist
      let settingsView = document.getElementById('settings-view');
      if (!settingsView) {
        settingsView = document.createElement('div');
        settingsView.id = 'settings-view';
        settingsView.className = 'content-view';
        document.body.appendChild(settingsView);

        // Update views object
        views.settings = settingsView;
      }

      // Hide all other views
      Object.values(views).forEach(
        (v) => v && v.classList.remove('active-view'),
      );

      // Load settings content
      settingsView.innerHTML = settingsHtml;

      // Initialize settings functionality manually
      initializeSettings();

      // Show settings view
      settingsView.classList.add('active-view');
    } catch (error) {
      console.error('Failed to load settings:', error);
      alert('Failed to load settings page. Please try again.');

      // Fall back to dashboard
      history.pushState({}, '', '/');
      handleRouteChange();
    } finally {
      hideSpinner();
    }
  };

  // Initialize settings functionality when dynamically loaded
  const initializeSettings = async () => {
    console.log('Initializing settings functionality...');

    // Load settings.js if not already loaded
    if (!window.settingsScriptLoaded) {
      const script = document.createElement('script');
      script.src = '/frontend_v1/js/settings.js';
      script.onload = () => {
        window.settingsScriptLoaded = true;
        console.log('Settings JavaScript loaded');
        setupSettingsEventListeners();
      };
      document.head.appendChild(script);
    } else {
      // First visit already loaded the bundle – just show the UI once.
      if (!window.settingsListenersAttached) {
        setupSettingsEventListeners();
      }
    }
  };

  const setupSettingsEventListeners = () => {
    // Prevent re-attachment
    if (window.settingsListenersAttached) {
      return;
    }
    window.settingsListenersAttached = true;

    // Load current settings
    if (typeof loadSettings === 'function') {
      loadSettings();
    }

    // Gemini dropdown listener
    const geminiModelSelect = document.getElementById('geminiModel');
    if (geminiModelSelect) {
      geminiModelSelect.addEventListener('change', saveSettings);
    }

    const providerRadios = document.querySelectorAll('input[name="llmProvider"]');
    providerRadios.forEach((radio) => {
      radio.addEventListener('change', () => {
        if (typeof toggleProviderSections === 'function') {
          toggleProviderSections(radio.value);
        }
        saveSettings();
      });
    });

    const openrouterModelSelect = document.getElementById('openrouterModel');
    if (openrouterModelSelect) {
      openrouterModelSelect.addEventListener('change', saveSettings);
    }

    const cerebrasModelSelect = document.getElementById('cerebrasModel');
    if (cerebrasModelSelect) {
      cerebrasModelSelect.addEventListener('change', saveSettings);
    }
    // Add change listener to debug mode switch
    const debugSwitch = document.getElementById('debugModeSwitch');
    if (debugSwitch) {
      debugSwitch.addEventListener('change', saveSettings);
    }

    console.log('Settings event listeners attached');
  };

  // Helper function for elements 2-4: location, resources, dice rolls
  const generateStructuredFieldsPreNarrative = (fullData, debugMode) => {
    let html = '';

    // 2. Location confirmed
    if (
      fullData.location_confirmed &&
      fullData.location_confirmed !== 'Unknown'
    ) {
      html += '<div class="location-confirmed">';
      html += `<strong>📍 Location:</strong> ${sanitizeHtml(fullData.location_confirmed)}`;
      html += '</div>';
    }

    // 3. Resources (always show)
    // Handle both string and object types (object should be converted to string)
    let resourceText = '<em>None</em>';
    if (fullData.resources !== undefined && fullData.resources !== null && fullData.resources !== 'undefined' && fullData.resources !== '') {
      if (typeof fullData.resources === 'string') {
        resourceText = sanitizeHtml(fullData.resources);
      } else if (typeof fullData.resources === 'object') {
        // Convert object to string representation (e.g., world_resources.last_note)
        if (fullData.resources.last_note) {
          resourceText = sanitizeHtml(fullData.resources.last_note);
        } else {
          // Fallback: stringify the object (shouldn't happen in normal flow)
          resourceText = sanitizeHtml(JSON.stringify(fullData.resources));
        }
      }
    }
    html += `<div class="resources" style="background-color: #fff3cd; padding: 8px; margin: 10px 0; border-radius: 5px;"><strong>📊 Resources:</strong> ${resourceText}</div>`;

    // 4. Dice rolls (only show in debug mode)
    if (debugMode) {
      if (
        fullData.dice_rolls &&
        Array.isArray(fullData.dice_rolls) &&
        fullData.dice_rolls.length > 0
      ) {
        html +=
          '<div class="dice-rolls" style="background-color: #e8f4e8; padding: 8px; margin: 10px 0; border-radius: 5px;">';
        html += '<strong>🎲 Dice Rolls:</strong><ul>';
        fullData.dice_rolls.forEach((roll) => {
          html += `<li>${sanitizeHtml(roll)}</li>`;
        });
        html += '</ul></div>';
      }
    }

    // 4b. Rewards box (if XP was awarded)
    if (fullData.rewards_box && fullData.rewards_box.xp_gained > 0) {
      const rb = fullData.rewards_box;
      const source = sanitizeHtml(rb.source || 'earned');
      const xpGained = rb.xp_gained || 0;
      const currentXp = rb.current_xp;
      const nextLevelXp = rb.next_level_xp;
      const progressPercent = rb.progress_percent;
      const levelUpAvailable = rb.level_up_available;
      const loot = rb.loot || [];
      const gold = rb.gold || 0;

      html += '<div class="rewards-box" style="background-color: #d4edda; border: 2px solid #28a745; padding: 12px; margin: 10px 0; border-radius: 8px;">';
      html += `<strong style="color: #155724;">✨ REWARDS (${source}):</strong>`;
      html += `<div style="margin-top: 8px; color: #155724;"><strong>+${xpGained} XP</strong>`;

      if (currentXp !== undefined && nextLevelXp !== undefined) {
        html += ` | XP: ${currentXp}/${nextLevelXp}`;
        if (progressPercent !== undefined) {
          html += ` (${Math.round(progressPercent)}%)`;
        }
      }
      html += '</div>';

      // Loot display
      const validLoot = loot.filter(item => item && item !== 'None');
      if (gold > 0 || validLoot.length > 0) {
        html += '<div style="margin-top: 6px; color: #155724;"><strong>Loot:</strong> ';
        const lootParts = [];
        if (gold > 0) lootParts.push(`${gold} gold`);
        if (validLoot.length > 0) lootParts.push(...validLoot.map(item => sanitizeHtml(item)));
        html += lootParts.join(', ');
        html += '</div>';
      }

      // Level up notification
      if (levelUpAvailable) {
        html += '<div style="margin-top: 8px; font-weight: bold; color: #856404; background-color: #fff3cd; padding: 6px; border-radius: 4px;">🎉 LEVEL UP AVAILABLE!</div>';
      }

      html += '</div>';
    }

    // 4.5 Living World Updates (debug mode only)
    const stateUpdates = fullData.state_updates || {};
    const worldEvents = stateUpdates.world_events || fullData.world_events;
    const factionUpdates = stateUpdates.faction_updates || fullData.faction_updates;
    const timeEvents = stateUpdates.time_events || fullData.time_events;
    const rumors = stateUpdates.rumors || fullData.rumors;
    const sceneEvent = stateUpdates.scene_event || fullData.scene_event;
    const complications = stateUpdates.complications || fullData.complications;

    const hasBackgroundEvents =
      Array.isArray(worldEvents?.background_events) &&
      worldEvents.background_events.some((event) => event && typeof event === 'object');
    const hasFactionUpdates =
      factionUpdates &&
      Object.keys(factionUpdates).length > 0 &&
      Object.values(factionUpdates).some((update) => update && typeof update === 'object');
    const hasTimeEvents =
      timeEvents &&
      Object.keys(timeEvents).length > 0 &&
      Object.values(timeEvents).some((event) => event && typeof event === 'object');
    const hasRumors =
      Array.isArray(rumors) && rumors.some((rumor) => rumor && typeof rumor === 'object');
    const hasSceneEvent =
      sceneEvent &&
      typeof sceneEvent === 'object' &&
      (sceneEvent.type || sceneEvent.description || sceneEvent.actor);
    // Check for boolean true or string "true" to handle LLM type inconsistency
    const hasComplications =
      complications &&
      typeof complications === 'object' &&
      (complications.triggered === true || complications.triggered === 'true');

    const hasLivingWorldData =
      debugMode &&
      (hasBackgroundEvents ||
        hasFactionUpdates ||
        hasTimeEvents ||
        hasRumors ||
        hasSceneEvent ||
        hasComplications);

    if (hasLivingWorldData) {
      html += '<div class="living-world-updates">';
      html += '<strong>🌍 Living World Updates (Debug):</strong>';

      // Background events
      if (hasBackgroundEvents) {
        html +=
          '<div class="living-world-section"><strong>📜 Background Events:</strong><ul class="living-world-list">';
        worldEvents.background_events.forEach((event) => {
          if (!event || typeof event !== 'object') return;
          const actor = event.actor || 'Unknown';
          const action = event.action || 'Unknown action';
          const eventType = event.event_type || 'unknown';
          const status = event.status || 'pending';
          const statusEmoji =
            status === 'discovered'
              ? '👁️'
              : status === 'resolved'
                ? '✅'
                : '⏳';
          html += `<li>${statusEmoji} <strong>${sanitizeHtml(actor)}</strong>: ${sanitizeHtml(action)} <em>[${sanitizeHtml(eventType)}, ${sanitizeHtml(status)}]</em></li>`;
        });
        html += '</ul></div>';
      }

      // Scene event (immediate player-facing)
      if (hasSceneEvent) {
        html +=
          '<div class="living-world-section living-world-scene"><strong>⚡ Scene Event:</strong> ';
        html += `<strong>${sanitizeHtml(sceneEvent.type || 'event')}</strong> - ${sanitizeHtml(sceneEvent.description || 'No description')}`;
        if (sceneEvent.actor) {
          html += ` (Actor: ${sanitizeHtml(sceneEvent.actor)})`;
        }
        html += '</div>';
      }

      // Faction updates
      if (hasFactionUpdates) {
        html +=
          '<div class="living-world-section"><strong>⚔️ Faction Updates:</strong><ul class="living-world-list">';
        Object.entries(factionUpdates).forEach(([faction, update]) => {
          if (!update || typeof update !== 'object') return;
          const objective = update.current_objective || 'Unknown objective';
          html += `<li><strong>${sanitizeHtml(faction)}</strong>: ${sanitizeHtml(objective)}</li>`;
        });
        html += '</ul></div>';
      }

      // Time events
      if (hasTimeEvents) {
        html +=
          '<div class="living-world-section"><strong>⏰ Time Events:</strong><ul class="living-world-list">';
        Object.entries(timeEvents).forEach(([eventName, event]) => {
          if (!event || typeof event !== 'object') return;
          const timeRemaining = event.time_remaining || 'Unknown';
          const status = event.status || 'ongoing';
          html += `<li><strong>${sanitizeHtml(eventName)}</strong>: ${sanitizeHtml(timeRemaining)} [${sanitizeHtml(status)}]</li>`;
        });
        html += '</ul></div>';
      }

      // Rumors
      if (hasRumors) {
        html +=
          '<div class="living-world-section"><strong>💬 Rumors:</strong><ul class="living-world-list">';
        rumors.forEach((rumor) => {
          if (!rumor || typeof rumor !== 'object') return;
          const content = rumor.content || 'Unknown rumor';
          const accuracy = rumor.accuracy || 'unknown';
          const accuracyEmoji =
            accuracy === 'true'
              ? '✓'
              : accuracy === 'false'
                ? '✗'
                : accuracy === 'partial'
                  ? '≈'
                  : '?';
          html += `<li>${accuracyEmoji} ${sanitizeHtml(content)} <em>[${sanitizeHtml(rumor.source_type || 'unknown source')}]</em></li>`;
        });
        html += '</ul></div>';
      }

      // Complications
      if (hasComplications) {
        html +=
          '<div class="living-world-section living-world-complication"><strong>⚠️ Complication:</strong> ';
        html += `<strong>${sanitizeHtml(complications.type || 'unknown')}</strong> - ${sanitizeHtml(complications.description || 'No description')}`;
        html += ` [Severity: ${sanitizeHtml(complications.severity || 'unknown')}]`;
        html += '</div>';
      }

      html += '</div>';
    }

    // 5. God mode response (if present, before narrative)
    if (
      fullData.god_mode_response &&
      fullData.god_mode_response !== 'undefined' &&
      fullData.god_mode_response !== ''
    ) {
      const escapedResponse = sanitizeHtml(fullData.god_mode_response);
      html += '<div class="god-mode-response">';
      html += '<strong>🔮 God Mode Response:</strong>';
      html += `<pre>${escapedResponse}</pre>`;
      html += '</div>';
    }

    // 6. Equipment display (deterministic backend data, not LLM-generated)
    if (
      fullData.equipment_display &&
      Array.isArray(fullData.equipment_display) &&
      fullData.equipment_display.length > 0
    ) {
      // Filter out items without valid names
      const validItems = fullData.equipment_display.filter((item) => {
        const name = item.name || item.item || '';
        return name && name.trim() !== '';
      });

      if (validItems.length > 0) {
        html +=
          '<div class="equipment-display" style="background-color: #e6f3ff; padding: 8px; margin: 10px 0; border-radius: 5px;">';
        html += '<strong>⚔️ Equipment:</strong><ul style="margin: 5px 0; padding-left: 20px;">';
        validItems.forEach((item) => {
          const slot = sanitizeHtml(item.slot || 'unknown');
          const itemName = sanitizeHtml(item.name || item.item || '');
          const stats = item.stats ? ` - ${sanitizeHtml(item.stats)}` : '';
          html += `<li><strong>${slot}:</strong> ${itemName}${stats}</li>`;
        });
        html += '</ul></div>';
      }
    }

    return html;
  };

  // Helper function for elements 7-10: planning block, entities, state updates, debug info
  const generateStructuredFieldsPostNarrative = (fullData, debugMode) => {
    let html = '';

    // 7. Planning block (always at the bottom if present)
    if (fullData.planning_block) {
      try {
        const parsedPlanningBlock = parsePlanningBlocks(
          fullData.planning_block,
        );
        if (parsedPlanningBlock) {
          html += `<div class="planning-block" style="background-color: #e7f3ff; padding: 10px; margin: 10px 0; border-radius: 5px;">${parsedPlanningBlock}</div>`;
        }
      } catch (e) {
        console.error('Error parsing planning block:', e);
        const escapedText = String(fullData.planning_block)
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;');
        html += `<div class="planning-block planning-block-error" style="background-color: #e7f3ff; padding: 10px; margin: 10px 0; border-radius: 5px;">Error parsing planning block. Raw content:<br><pre>${escapedText}</pre></div>`;
      }
    }

    // 8. Entities
    if (
      fullData.entities_mentioned &&
      Array.isArray(fullData.entities_mentioned) &&
      fullData.entities_mentioned.length > 0
    ) {
      html += '<div class="entities-mentioned">';
      html += '<strong>👥 Entities:</strong>';
      html += '<ul>';
      fullData.entities_mentioned.forEach((entity) => {
        html += `<li>${sanitizeHtml(entity)}</li>`;
      });
      html += '</ul>';
      html += '</div>';
    }

    // 9. State updates - DISABLED: too verbose, not useful for gameplay
    // State updates are still returned by the backend for data integrity
    // but no longer displayed in the UI even in debug mode

    // 10. Debug info (still gate UI strictly on debugMode)
    const debugInfo = fullData.debug_info;
    if (debugMode && debugInfo && typeof debugInfo === 'object' && Object.keys(debugInfo).length > 0) {
      html += '<div class="debug-info">';
      html += '<strong>🔍 Debug Info:</strong>';

      // Show agent name if present
      const agentName = debugInfo?.agent_name;
      if (agentName) {
        html += `<div class="agent-name"><strong>🤖 Agent:</strong> ${sanitizeHtml(agentName)}</div>`;
      }

      // Show DM notes if present
      if (
        debugInfo.dm_notes &&
        Array.isArray(debugInfo.dm_notes) &&
        debugInfo.dm_notes.length > 0
      ) {
        html += '<div class="dm-notes"><strong>📝 DM Notes:</strong><ul>';
        debugInfo.dm_notes.forEach((note) => {
          html += `<li>${sanitizeHtml(note)}</li>`;
        });
        html += '</ul></div>';
      }

      // Show state rationale if present
      if (debugInfo.state_rationale) {
        html += `<div class="state-rationale"><strong>💭 State Rationale:</strong> ${sanitizeHtml(debugInfo.state_rationale)}</div>`;
      }

      // Raw debug info JSON - DISABLED: too verbose (code_contains_rng, stdout, etc.)

      html += '</div>';
    }

    return html;
  };

  // Unified function to generate all structured fields (pre and post narrative)
  const generateStructuredFieldsHTML = (fullData, debugMode) => {
    return (
      generateStructuredFieldsPreNarrative(fullData, debugMode) +
      generateStructuredFieldsPostNarrative(fullData, debugMode)
    );
  };

  const appendToStory = (
    actor,
    text,
    mode = null,
    debugMode = false,
    sequenceId = null,
    fullData = null,
    options = {},
  ) => {
    const storyContainer = document.getElementById('story-content');
    const entryEl = document.createElement('div');
    entryEl.className = 'story-entry';

    let label = '';
    if (actor === 'gemini') {
      label = sequenceId ? `Scene #${sequenceId}` : 'Story';
    } else if (actor === 'system') {
      label = 'System';
    } else {
      // actor is 'user'
      label =
        mode === 'character'
          ? 'Main Character'
          : mode === 'god'
            ? 'God'
            : 'You';
    }

    // Build the full response HTML in the correct order
    let html = '';

    // 1. Session header (always at the top, with escaping)
    if (
      actor === 'gemini' &&
      fullData &&
      fullData.session_header &&
      fullData.session_header !== 'undefined'
    ) {
      const escapedHeader = sanitizeHtml(fullData.session_header);
      html += `<div class="session-header">${escapedHeader}</div>`;
      // Quick action buttons for equipment, stats, and spells
      html += `<div class="quick-actions d-flex gap-2" style="margin: 5px 0;">
        <button class="btn btn-sm btn-outline-secondary equipment-btn"
                title="List all equipped items">
          <i class="bi bi-backpack2"></i> Equipment
        </button>
        <button class="btn btn-sm btn-outline-info stats-btn"
                title="View character stats">
          <i class="bi bi-bar-chart"></i> Stats
        </button>
        <button class="btn btn-sm btn-outline-primary spells-btn"
                title="View spells and spell slots">
          <i class="bi bi-magic"></i> Spells
        </button>
      </div>`;
    }

    // Process debug content - backend now handles stripping based on debug_mode
    // Defensive check: ensure text is not null/undefined
    if (!text) {
      console.error('appendToStory called with null/undefined text:', { actor, text, mode, debugMode, sequenceId });
      text = '[Error: Empty response from server]';
    }

    let processedText = text;
    if (actor === 'gemini') {
      processedText = text
        .replace(
          /\[STATE_UPDATES_PROPOSED\]/g,
          '<div class="debug-content"><strong>🔧 STATE UPDATES PROPOSED:</strong><br><pre>',
        )
        .replace(/\[END_STATE_UPDATES_PROPOSED\]/g, '</pre></div>')
        .replace(
          /\[DEBUG_START\]/g,
          '<div class="debug-content"><strong>🔍 DM Notes:</strong> ',
        )
        .replace(/\[DEBUG_END\]/g, '</div>')
        .replace(
          /\[DEBUG_STATE_START\]/g,
          '<div class="debug-content"><strong>⚙️ State Changes:</strong> ',
        )
        .replace(/\[DEBUG_STATE_END\]/g, '</div>')
        .replace(
          /\[DEBUG_ROLL_START\]/g,
          '<div class="debug-rolls"><strong>🎲 Dice Roll:</strong> ',
        )
        .replace(/\[DEBUG_ROLL_END\]/g, '</div>');
    }

    // 2-5. Structured fields before narrative (location, resources, dice rolls, god_mode_response)
    if (actor === 'gemini' && fullData) {
      html += generateStructuredFieldsPreNarrative(fullData, debugMode);
    }

    // 6. Main narrative
    const renderAsHtml = actor === 'system' && options?.isHtml;
    if (renderAsHtml) {
      html += `<div><strong>${label}:</strong></div>`;
      html += `<div>${processedText}</div>`;
    } else {
      html += `<p><strong>${label}:</strong> ${processedText}</p>`;
    }

    // 7-10. Structured fields after narrative (planning block, entities, state updates, debug info)
    if (actor === 'gemini' && fullData) {
      html += generateStructuredFieldsPostNarrative(fullData, debugMode);
    }

    entryEl.innerHTML = html;

    const beforeNode = options.prepend
      ? storyContainer.querySelector('.story-entry')
      : null;
    if (beforeNode) {
      storyContainer.insertBefore(entryEl, beforeNode);
    } else {
      storyContainer.appendChild(entryEl);
    }

    // Add click handlers to any choice buttons we just added
    if (actor === 'gemini') {
      const choiceButtons = entryEl.querySelectorAll('.choice-button');
      choiceButtons.forEach((button) => {
        button.addEventListener('click', handleChoiceClick);
      });

      // Add click handlers for quick action buttons (CSP blocks inline onclick)
      const equipmentBtn = entryEl.querySelector('.equipment-btn');
      if (equipmentBtn) {
        equipmentBtn.addEventListener('click', window.sendEquipmentQuery);
      }
      const statsBtn = entryEl.querySelector('.stats-btn');
      if (statsBtn) {
        statsBtn.addEventListener('click', window.sendStatsQuery);
      }
      const spellsBtn = entryEl.querySelector('.spells-btn');
      if (spellsBtn) {
        spellsBtn.addEventListener('click', window.sendSpellsQuery);
      }
    }
  };

  // Handler for choice button clicks
  const handleChoiceClick = async (e) => {
    const button = e.currentTarget;
    const choiceText = button.getAttribute('data-choice-text');
    const choiceId = button.getAttribute('data-choice-id');
    const switchToStory = button.getAttribute('data-switch-to-story') === 'true';
    const userInputEl = document.getElementById('user-input');
    const interactionForm = document.getElementById('interaction-form');

    if (!userInputEl || !interactionForm) return;

    // For predefined choices, disable all buttons
    document.querySelectorAll('.choice-button').forEach((btn) => {
      btn.disabled = true;
    });

    // If switch_to_story_mode is true, change the interaction mode radio to character mode (story/narrative)
    if (switchToStory) {
      const charModeRadio = document.getElementById('char-mode');
      if (charModeRadio) {
        charModeRadio.checked = true;
        // Trigger change event in case other code listens for it
        charModeRadio.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('Switched to character/story mode via switch_to_story_mode flag');
      }
    }

    // Set the choice text in the input field
    userInputEl.value = choiceText;

    // Submit the form programmatically
    const submitEvent = new Event('submit', {
      cancelable: true,
      bubbles: true,
    });
    interactionForm.dispatchEvent(submitEvent);
  };

  // Helper function to parse planning blocks and create buttons - JSON ONLY
  const parsePlanningBlocks = (input) => {
    // Robust error handling for edge cases
    if (!input) {
      console.log('parsePlanningBlocks: Empty or null planning block');
      return '';
    }

    // JSON format - ONLY supported format
    if (typeof input === 'object' && input !== null) {
      return parsePlanningBlocksJson(input);
    }

    // String format - NO LONGER SUPPORTED, but try to parse as malformed text
    if (typeof input === 'string') {
      console.error(
        '❌ STRING PLANNING BLOCKS NO LONGER SUPPORTED: String planning blocks are deprecated. Only JSON format is allowed. Received:',
        input.substring(0, 100) + '...',
      );

      // Try to extract readable content from malformed string for user experience
      const decodedText = decodeHtmlEntities(input);
      const cleanText = decodedText.replace(/[\r\n\t]+/g, ' ').trim();

      if (cleanText.length > 0) {
        return `<div class="planning-block-error">
                    <p><strong>⚠️ Malformed Planning Block Detected</strong></p>
                    <p>The AI generated an invalid planning block format. Here's the readable content:</p>
                    <div class="malformed-content">${sanitizeHtml(cleanText)}</div>
                    <p><em>Please try again - this will be fixed in future responses.</em></p>
                </div>`;
      }

      return `<div class="planning-block-error">❌ Error: Planning block must be JSON object, not string. System needs to be updated to use JSON format.</div>`;
    }

    // Invalid type - reject
    console.error(
      '❌ INVALID PLANNING BLOCK TYPE: Expected JSON object, got:',
      typeof input,
    );
    return `<div class="planning-block-error">❌ Error: Invalid planning block type. Expected JSON object with 'thinking' and 'choices' fields.</div>`;
  };

  // New function to handle JSON planning blocks
  const parsePlanningBlocksJson = (planningBlock) => {
    console.log('parsePlanningBlocks: Processing JSON format planning block');

    // Validate structure
    if (!planningBlock.choices || typeof planningBlock.choices !== 'object') {
      console.warn(
        'parsePlanningBlocks: Invalid JSON structure - missing or invalid choices',
      );
      return planningBlock.thinking || '';
    }

    const choices = planningBlock.choices;
    const choiceKeys = Object.keys(choices);

    // If no choices, just return thinking text
    if (choiceKeys.length === 0) {
      console.log('parsePlanningBlocks: No choices in planning block');
      return planningBlock.thinking || '';
    }

    // Build HTML output
    let html = '';

    // Add thinking text if present
    if (planningBlock.thinking) {
      const sanitizedThinking = sanitizeHtml(planningBlock.thinking);
      html += `<div class="planning-block-thinking">${sanitizedThinking}</div>`;
    }

    // Add context if present
    if (planningBlock.context) {
      const sanitizedContext = sanitizeHtml(planningBlock.context);
      html += `<div class="planning-block-context">${sanitizedContext}</div>`;
    }

    // Create choice buttons
    html += '<div class="planning-block-choices">';

    choiceKeys.forEach((choiceKey) => {
      const choice = choices[choiceKey];

      // Validate choice structure
      if (!choice || typeof choice !== 'object') {
        console.warn(
          `parsePlanningBlocks: Invalid choice object for key: ${choiceKey}`,
        );
        return;
      }

      if (!choice.text || !choice.description) {
        console.warn(
          `parsePlanningBlocks: Choice missing required fields: ${choiceKey}`,
        );
        return;
      }

      // Sanitize choice data
      const safeKey = sanitizeIdentifier(choiceKey);
      const safeText = sanitizeHtml(choice.text);
      const safeDescription = sanitizeHtml(choice.description);
      const riskLevel = choice.risk_level || 'low';
      const switchToStory = choice.switch_to_story_mode === true;

      // Expanded rendering when pros/cons/confidence are present.
      //
      // Canonical schema (narrative_response_schema.py / CHOICE_SCHEMA):
      // - pros/cons/confidence live at the choice level (choice.pros, choice.cons, choice.confidence)
      // - choice.analysis is reserved for non-display metadata (e.g., parallel execution coordination details)
      const hasExpandedDetails =
        (Array.isArray(choice.pros) && choice.pros.length > 0) ||
        (Array.isArray(choice.cons) && choice.cons.length > 0) ||
        (typeof choice.confidence === 'string' && choice.confidence.trim());

      if (hasExpandedDetails) {
        const safePros = Array.isArray(choice.pros)
          ? choice.pros.map((p) => sanitizeHtml(p))
          : [];
        const safeCons = Array.isArray(choice.cons)
          ? choice.cons.map((c) => sanitizeHtml(c))
          : [];
        const safeConfidence =
          typeof choice.confidence === 'string'
            ? sanitizeHtml(choice.confidence)
            : '';

        // Build multi-line button text
        let buttonText = `${safeText}: ${safeDescription}`;
        if (safePros.length > 0) {
          buttonText += `\nPros: ${safePros.join(', ')}`;
        }
        if (safeCons.length > 0) {
          buttonText += `\nCons: ${safeCons.join(', ')}`;
        }
        if (safeConfidence) {
          buttonText += `\nAssessment: ${safeConfidence}`;
        }

        const choiceData = `${safeText} - ${safeDescription}`;
        const escapedChoiceData = escapeHtmlAttribute(choiceData);
        const escapedTitle = escapeHtmlAttribute(safeDescription);
        const riskClass = `risk-${riskLevel}`;

        html +=
          `<button class="choice-button ${riskClass}" ` +
          `data-choice-id="${safeKey}" ` +
          `data-choice-text="${escapedChoiceData}" ` +
          `data-switch-to-story="${switchToStory}" ` +
          `title="${escapedTitle}" ` +
          `style="white-space: pre-wrap; text-align: left;">${buttonText}</button>`;
      } else {
        // Standard mode - render simple button format
        const buttonText = `${safeText}: ${safeDescription}`;
        const choiceData = `${safeText} - ${safeDescription}`;
        const escapedChoiceData = escapeHtmlAttribute(choiceData);
        const escapedTitle = escapeHtmlAttribute(safeDescription);
        const riskClass = `risk-${riskLevel}`;

        html +=
          `<button class="choice-button ${riskClass}" ` +
          `data-choice-id="${safeKey}" ` +
          `data-choice-text="${escapedChoiceData}" ` +
          `data-switch-to-story="${switchToStory}" ` +
          `title="${escapedTitle}">${buttonText}</button>`;
      }
    });

    html += '</div>';

    return html;
  };

  // Utility functions for sanitization and validation
  const decodeHtmlEntities = (text) => {
    if (!text) return '';
    return text
      .toString()
      .replace(/&#x27;/g, "'")
      .replace(/&quot;/g, '"')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&');
  };

  const sanitizeHtml = (text) => {
    if (!text) return '';
    // First decode any existing entities, then encode for safety
    const decoded = decodeHtmlEntities(text);
    return decoded
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  };

  const escapeHtmlAttribute = (text) => {
    if (!text) return '';
    return text
      .toString()
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  };

  const sanitizeIdentifier = (text) => {
    if (!text) return 'unknown';
    // Keep only alphanumeric, underscore, and hyphen characters
    return text.toString().replace(/[^a-zA-Z0-9_-]/g, '');
  };

  /**
   * Show a generic error toast notification
   */
  function showErrorToast(message, title = 'Error') {
    // Remove any existing error toast
    const existingToast = document.getElementById('error-toast');
    if (existingToast) {
      existingToast.remove();
    }

    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
      toastContainer.style.zIndex = '1100';
      document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.id = 'error-toast';
    toast.className = 'toast show';
    toast.setAttribute('role', 'alert');

    // Header
    const header = document.createElement('div');
    header.className = 'toast-header bg-danger text-white';

    const titleEl = document.createElement('strong');
    titleEl.className = 'me-auto';
    titleEl.textContent = title;

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'btn-close btn-close-white';
    closeBtn.setAttribute('data-bs-dismiss', 'toast');
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.addEventListener('click', () => toast.remove());

    header.appendChild(titleEl);
    header.appendChild(closeBtn);

    // Body
    const body = document.createElement('div');
    body.className = 'toast-body';
    body.textContent = message;

    toast.appendChild(header);
    toast.appendChild(body);

    toastContainer.appendChild(toast);

    // Auto-hide after 5 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
      }
    }, 5000);
  }

  // --- Data Fetching and Rendering ---
  // Pagination state for campaigns
  let campaignPagination = {
    limit: 50, // Default page size
    loadedCampaigns: [],
    hasMore: false,
    isLoading: false,
    totalCount: 0, // Total campaigns loaded so far
    estimatedTotal: null, // Estimated total if available from API
    nextCursor: null, // Cursor for next page {timestamp, id}
  };

  let renderCampaignList = async (loadMore = false) => {
    if (campaignPagination.isLoading) return;

    showSpinner('loading');
    campaignPagination.isLoading = true;

    // Update button state
    const loadMoreBtn = document.getElementById('load-more-campaigns-btn');
    if (loadMoreBtn) {
      loadMoreBtn.disabled = true;
      loadMoreBtn.textContent = 'Loading...';
    }

    try {
      // Build query with limit
      const limit = campaignPagination.limit;
      const params = new URLSearchParams({
        limit: limit.toString(),
        paginate: 'true'
      });

      // Use cursor-based pagination if loading more
      if (loadMore && campaignPagination.nextCursor) {
        params.set('start_after_timestamp', campaignPagination.nextCursor.timestamp);
        params.set('start_after_id', campaignPagination.nextCursor.id);
      }

      const { data } = await fetchApi(`/api/campaigns?${params}`);

      // Handle both legacy array response and new paginated object response
      const campaigns = Array.isArray(data) ? data : (data.campaigns || []);

      // Update pagination state
      if (loadMore) {
        // Append to existing campaigns
        campaignPagination.loadedCampaigns = [...campaignPagination.loadedCampaigns, ...campaigns];
      } else {
        // Replace campaigns (first load)
        campaignPagination.loadedCampaigns = campaigns;
      }

      // Update pagination metadata from response
      campaignPagination.hasMore = data.has_more || false;
      campaignPagination.nextCursor = data.next_cursor || null;
      campaignPagination.totalCount = campaignPagination.loadedCampaigns.length;

      // Update estimated total if provided by API
      if (data.total_count !== undefined) {
        campaignPagination.estimatedTotal = data.total_count;
      }

      // Update button state
      const updatedLoadMoreBtn = document.getElementById('load-more-campaigns-btn');
      if (updatedLoadMoreBtn) {
        updatedLoadMoreBtn.disabled = false;
        updatedLoadMoreBtn.textContent = 'Load More';
      }

      // RESILIENCE: Cache successful campaign data for offline viewing
      localStorage.setItem('cachedCampaigns', JSON.stringify(campaignPagination.loadedCampaigns));
      localStorage.setItem('cachedPaginationState', JSON.stringify({
        hasMore: campaignPagination.hasMore,
        nextCursor: campaignPagination.nextCursor,
        estimatedTotal: campaignPagination.estimatedTotal,
        totalCount: campaignPagination.loadedCampaigns.length
      }));
      localStorage.setItem('lastCampaignUpdate', new Date().toISOString());

      campaignPagination.isLoading = false;
      renderCampaignListUI(campaignPagination.loadedCampaigns, loadMore);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
      showErrorToast(`Failed to load campaigns: ${error.message || 'Unknown error'}`, 'Connection Error');

      // Reset button state on error
      const errorLoadMoreBtn = document.getElementById('load-more-campaigns-btn');
      if (errorLoadMoreBtn) {
        errorLoadMoreBtn.disabled = false;
        errorLoadMoreBtn.textContent = 'Load More';
      }

      // RESILIENCE: Try to load from cache if network fails
      const cachedCampaigns = localStorage.getItem('cachedCampaigns');
      const lastUpdate = localStorage.getItem('lastCampaignUpdate');

      if (cachedCampaigns) {
        const campaigns = JSON.parse(cachedCampaigns);
        const cachedState = localStorage.getItem('cachedPaginationState');
        if (cachedState) {
          try {
            const paginationState = JSON.parse(cachedState);
            campaignPagination.hasMore = paginationState.hasMore || false;
            campaignPagination.nextCursor = paginationState.nextCursor || null;
            campaignPagination.estimatedTotal = paginationState.estimatedTotal || null;
          } catch (e) {
            console.warn('Failed to parse cached pagination state', e);
          }
        }
        const lastUpdateDate = lastUpdate
          ? new Date(lastUpdate).toLocaleDateString()
          : 'unknown';

        campaignPagination.isLoading = false;
        renderCampaignListUI(campaigns, false, lastUpdateDate);

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
    } finally {
      campaignPagination.isLoading = false;
      hideSpinner();
    }
  };

  // RESILIENCE: Separate UI rendering for reuse with cached data
  function renderCampaignListUI(
    campaigns,
    loadMore = false,
    lastUpdate = null,
  ) {
    const listEl = document.getElementById('campaign-list');
    const dashboardView = document.getElementById('dashboard-view');
    const isOffline = lastUpdate !== null;

    // Only clear if not loading more
    if (!loadMore) {
      listEl.innerHTML = '';
      // Also remove count/button when clearing
      const existingCountDisplay = dashboardView.querySelector('#campaign-count-display');
      const existingLoadMore = dashboardView.querySelector('#load-more-campaigns-btn');
      if (existingCountDisplay) existingCountDisplay.remove();
      if (existingLoadMore) existingLoadMore.remove();
    }

    if (campaigns.length === 0) {
      listEl.innerHTML = '<p>You have no campaigns. Start a new one!</p>';
      // Remove any existing count/button when no campaigns
      const existingCountDisplay = dashboardView.querySelector('#campaign-count-display');
      const existingLoadMore = dashboardView.querySelector('#load-more-campaigns-btn');
      if (existingCountDisplay) existingCountDisplay.remove();
      if (existingLoadMore) existingLoadMore.remove();
      return;
    }

    // Determine which campaigns to render
    // If loadMore is true, we only want to render the NEW campaigns that aren't already in the DOM
    const campaignsToRender = loadMore
      ? campaigns.filter(c => !listEl.querySelector(`[data-campaign-id="${CSS.escape(c.id)}"]`))
      : campaigns;
    campaignsToRender.forEach((campaign) => {
      const campaignEl = document.createElement('div');
      campaignEl.className = 'list-group-item list-group-item-action';

      const lastPlayed = campaign.last_played
        ? new Date(campaign.last_played).toLocaleString()
        : 'N/A';
      const initialPrompt = campaign.initial_prompt
        ? campaign.initial_prompt.substring(0, 100) + '...'
        : '[No prompt]';

      campaignEl.innerHTML = `
                <div class="d-flex flex-column flex-sm-row w-100 justify-content-sm-between align-items-sm-center campaign-list-header">
                    <h5 class="mb-2 mb-sm-0 campaign-title-link text-break">${campaign.title}</h5>
                    <div class="d-flex align-items-center flex-shrink-0 campaign-list-actions mt-1 mt-sm-0">
                        ${!isOffline ? '<button class="btn btn-sm btn-outline-primary edit-campaign-btn me-2">Edit</button>' : ''}
                        <small class="text-muted text-nowrap">Last played: ${lastPlayed}</small>
                    </div>
                </div>
                <p class="mb-1 mt-2 campaign-title-link">${initialPrompt}</p>`;

      campaignEl.dataset.campaignId = campaign.id;
      campaignEl.dataset.campaignTitle = campaign.title;

      listEl.appendChild(campaignEl);
    });

    // Expose pagination data for Enhanced Search
    if (campaignPagination.estimatedTotal !== null) {
      listEl.dataset.totalCount = campaignPagination.estimatedTotal;
    } else {
      delete listEl.dataset.totalCount;
    }
    listEl.dataset.hasMore = campaignPagination.hasMore;

    // Add campaign count display and "Load More" button at the bottom (outside list-group)
    const existingCountDisplay = dashboardView.querySelector('#campaign-count-display');
    const existingLoadMore = dashboardView.querySelector('#load-more-campaigns-btn');
    const isEnhancedSearchActive = !!document.getElementById('campaign-search');

    // Update or create campaign count display
    // Show "X out of Y" format if we know total, otherwise "X campaigns" or "X+ campaigns"
    const loadedCount = campaigns.length;
    let countText;

    if (campaignPagination.estimatedTotal !== null) {
      // We know the total: show "X out of Y"
      countText = `${loadedCount} out of ${campaignPagination.estimatedTotal} campaigns`;
    } else if (campaignPagination.hasMore) {
      // We don't know total but there are more: show "X+ campaigns"
      countText = `${loadedCount}+ campaigns`;
    } else {
      // No more campaigns: show exact count
      countText = loadedCount === 1
        ? '1 campaign'
        : `${loadedCount} campaigns`;
    }

    if (!isEnhancedSearchActive) {
      if (!existingCountDisplay) {
        const countDisplay = document.createElement('div');
        countDisplay.id = 'campaign-count-display';
        countDisplay.className = 'text-muted text-center mt-3 mb-2';
        countDisplay.style.fontSize = '0.9rem';
        countDisplay.textContent = countText;
        dashboardView.appendChild(countDisplay);
      } else {
        existingCountDisplay.textContent = countText;
        existingCountDisplay.style.display = 'block';
      }
    } else if (existingCountDisplay) {
      existingCountDisplay.remove();
    }

    // Add "Load More" button at the bottom if there are more campaigns
    if (campaignPagination.hasMore && !existingLoadMore) {
      const loadMoreBtn = document.createElement('button');
      loadMoreBtn.id = 'load-more-campaigns-btn';
      loadMoreBtn.className = 'btn btn-primary w-100 mt-2 mb-3';
      loadMoreBtn.textContent = 'Load More';
      loadMoreBtn.disabled = campaignPagination.isLoading;
      loadMoreBtn.addEventListener('click', () => {
        renderCampaignList(true);
      });
      dashboardView.appendChild(loadMoreBtn);
    } else if (!campaignPagination.hasMore && existingLoadMore) {
      existingLoadMore.remove();
    } else if (existingLoadMore && campaignPagination.hasMore) {
      existingLoadMore.disabled = campaignPagination.isLoading;
      existingLoadMore.textContent = campaignPagination.isLoading ? 'Loading...' : 'Load More';
    }
  }

  // Pagination state for story loading
  let storyPagination = {
    campaignId: null,
    oldestTimestamp: null,
    oldestId: null,
    hasOlder: false,
    totalCount: 0,
    loadedCount: 0,
    loadedGeminiCount: 0,
    debugMode: false,
    isLoading: false,
  };

  // Load older story entries
  let loadOlderStoryEntries = async () => {
    if (storyPagination.isLoading || !storyPagination.hasOlder) return;

    storyPagination.isLoading = true;
    const loadBtn = document.getElementById('load-older-btn');
    if (loadBtn) {
      loadBtn.disabled = true;
      loadBtn.innerHTML =
        '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    }

    try {
      const params = new URLSearchParams({
        limit: '100',
        before: storyPagination.oldestTimestamp,
        before_id: storyPagination.oldestId || '',
        newer_count: storyPagination.loadedCount.toString(),
        newer_gemini_count: storyPagination.loadedGeminiCount.toString(),
      });
      const { data } = await fetchApi(
        `/api/campaigns/${storyPagination.campaignId}/story?${params}`,
      );

      const storyContainer = document.getElementById('story-content');
      const debugMode = storyPagination.debugMode;

      // Prepend older entries at the top (they come in chronological order)
      let newGeminiCount = 0;
      for (let i = (data.story?.length || 0) - 1; i >= 0; i -= 1) {
        const entry = data.story[i];
        if (entry?.actor === 'gemini') {
          newGeminiCount += 1;
        }
        appendToStory(
          entry.actor,
          entry.text,
          entry.mode,
          debugMode,
          entry.user_scene_number,
          entry,
          { prepend: true },
        );
      }

      // Update pagination state
      storyPagination.hasOlder = data.pagination?.has_older || false;
      storyPagination.oldestTimestamp =
        data.pagination?.oldest_timestamp || storyPagination.oldestTimestamp;
      storyPagination.oldestId =
        data.pagination?.oldest_id || storyPagination.oldestId;
      storyPagination.loadedCount += data.story.length;
      storyPagination.loadedGeminiCount += newGeminiCount;

      // Update or hide the load button
      updateLoadOlderButton();

      console.log(
        `Loaded ${data.story.length} older entries. Has more: ${storyPagination.hasOlder}`,
      );
    } catch (error) {
      console.error('Failed to load older entries:', error);
      alert('Failed to load older entries. Please try again.');
    } finally {
      storyPagination.isLoading = false;
      if (loadBtn) {
        loadBtn.disabled = false;
        loadBtn.innerHTML = '⬆️ Load older entries';
      }
    }
  };

  // Update the "load older" button visibility
  let updateLoadOlderButton = () => {
    let loadBtn = document.getElementById('load-older-btn');
    const storyContainer = document.getElementById('story-content');

    if (!storyContainer) return;

    if (storyPagination.hasOlder) {
      if (!loadBtn) {
        loadBtn = document.createElement('button');
        loadBtn.id = 'load-older-btn';
        loadBtn.className = 'btn btn-outline-secondary btn-sm w-100 mb-3';
        loadBtn.innerHTML = '⬆️ Load older entries';
        loadBtn.onclick = loadOlderStoryEntries;
        storyContainer.insertBefore(loadBtn, storyContainer.firstChild);
      }
      const remaining = Math.max(
        storyPagination.totalCount - storyPagination.loadedCount,
        0,
      );
      loadBtn.innerHTML = `⬆️ Load older entries (${remaining} more)`;
      loadBtn.style.display = 'block';
    } else if (loadBtn) {
      loadBtn.remove();
    }
  };

  let resumeCampaign = async (campaignId, retryCount = 0) => {
    showSpinner('loading');
    try {
      // Mobile gets lower story limit to reduce payload size
      const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent) ||
        window.innerWidth < 768;
      const storyLimit = isMobile ? 100 : 300;

      const params = new URLSearchParams();
      params.set('story_limit', storyLimit);

      const { data } = await fetchApi(`/api/campaigns/${campaignId}?${params}`);
      const gameTitleElement = document.getElementById('game-title');
      gameTitleElement.innerText = data.campaign.title;

      // Initialize inline editor for campaign title
      if (window.InlineEditor) {
        new InlineEditor(gameTitleElement, {
          maxLength: 100,
          minLength: 1,
          placeholder: 'Enter campaign title...',
          saveFn: async (newTitle) => {
            // Save the new title via API
            await fetchApi(`/api/campaigns/${campaignId}`, {
              method: 'PATCH',
              body: JSON.stringify({ title: newTitle }),
            });
            console.log('Campaign title updated successfully');
          },
          onError: (error) => {
            console.error('Failed to update campaign title:', error);
            alert('Failed to update campaign title. Please try again.');
          },
        });
      }

      const storyContainer = document.getElementById('story-content');
      storyContainer.innerHTML = '';

      // Initialize pagination state from response
      storyPagination = {
        campaignId: campaignId,
        oldestTimestamp: data.story_pagination?.oldest_timestamp || null,
        oldestId: data.story_pagination?.oldest_id || null,
        hasOlder: data.story_pagination?.has_older || false,
        totalCount: data.story_pagination?.total_count || data.story?.length || 0,
        loadedCount: data.story?.length || 0,
        loadedGeminiCount: (data.story || []).filter(
          (entry) => entry.actor === 'gemini',
        ).length,
        debugMode: data.game_state?.debug_mode || false,
        isLoading: false,
      };

      // Validate story data
      if (!data.story || !Array.isArray(data.story)) {
        console.error('Invalid or missing story data:', data);
        storyContainer.innerHTML =
          '<div class="alert alert-warning">No story content found. Please try refreshing the page.</div>';
        return;
      }

      // Check if we have game state with debug mode
      const debugMode = data.game_state?.debug_mode || false;

      // Update debug indicator
      const debugIndicator = document.getElementById('debug-indicator');
      if (debugIndicator) {
        debugIndicator.style.display = debugMode ? 'block' : 'none';
      }

      // Add "load older" button if there are older entries
      updateLoadOlderButton();

      // Render story with debug mode awareness and structured fields
      console.log(
        `Loading campaign ${campaignId} - Story entries: ${data.story.length}/${storyPagination.totalCount}, ` +
        `Debug mode: ${debugMode}, Has older: ${storyPagination.hasOlder}`,
      );

      // Display all story entries
      let visibleEntries = 0;
      data.story.forEach((entry) => {
        // All entries should be visible (god mode is a gameplay feature, not debug)
        visibleEntries++;
        appendToStory(
          entry.actor,
          entry.text,
          entry.mode,
          debugMode,
          entry.user_scene_number,
          entry,
          { prepend: false },
        );
      });

      console.log(
        `Displayed ${visibleEntries} story entries out of ${data.story.length} fetched (${storyPagination.totalCount} total)`,
      );

      // Check for empty story display
      if (visibleEntries === 0 && data.story.length > 0) {
        console.warn(
          'All story entries were filtered out! Debug mode:',
          debugMode,
        );
        console.warn('Story entries:', data.story);
        storyContainer.innerHTML =
          '<div class="alert alert-info">No visible story content. This may be due to debug mode filtering.</div>';
      } else if (
        data.story.length === 0 ||
        (data.story.length === 1 && data.story[0].mode === 'god')
      ) {
        // If no story or only the initial god mode prompt, retry a few times
        // This handles Firestore eventual consistency issues
        if (retryCount < 3) {
          console.warn(
            `Story data incomplete (attempt ${retryCount + 1}/3), retrying in 1 second...`,
          );
          hideSpinner();
          setTimeout(() => {
            resumeCampaign(campaignId, retryCount + 1);
          }, 1000);
          return;
        } else {
          console.error('No story entries after retries. Story:', data.story);
          storyContainer.innerHTML =
            '<div class="alert alert-danger">Campaign is still loading. Please refresh the page in a few seconds.</div>';
        }
      }

      // Add a slight delay to allow rendering before scrolling
      console.log(
        'Attempting to scroll after content append, with a slight delay.',
      ); // RESTORED console.log
      setTimeout(() => scrollToBottom(storyContainer), 100); // 100ms delay

      showView('game');
      document.getElementById('shareStoryBtn').style.display = 'block';
      document.getElementById('downloadStoryBtn').style.display = 'block';

      // Dispatch campaignLoaded event to trigger spicy mode state load
      window.dispatchEvent(new CustomEvent('campaignLoaded'));
    } catch (error) {
      console.error('Failed to resume campaign:', error);
      history.pushState({}, '', '/');
      handleRouteChange();
    } finally {
      hideSpinner();
    }
  };

  // --- Event Listeners ---
  document
    .getElementById('new-campaign-form')
    .addEventListener('submit', async (e) => {
      e.preventDefault();

      showSpinner('newCampaign');
      const character = document.getElementById('character-input').value;
      const setting = document.getElementById('setting-input').value;
      const description = document.getElementById('description-input').value;
      const title = document.getElementById('campaign-title').value;
      const selectedPrompts = Array.from(
        document.querySelectorAll('input[name="selectedPrompts"]:checked'),
      ).map((checkbox) => checkbox.value);
      const customOptions = Array.from(
        document.querySelectorAll('input[name="customOptions"]:checked'),
      ).map((checkbox) => checkbox.value);

      // Check if Dragon Knight campaign is selected
      const dragonKnightRadio = document.getElementById('dragonKnightCampaign');
      const isDragonKnight = dragonKnightRadio && dragonKnightRadio.checked;

      // Dragon Knight campaigns always use default world
      if (isDragonKnight) {
        console.log(
          'Dragon Knight campaign selected - ensuring default world is used',
        );
        // Make sure defaultWorld is in customOptions
        if (!customOptions.includes('defaultWorld')) {
          customOptions.push('defaultWorld');
        }
      }
      try {
        const { data } = await fetchApi('/api/campaigns', {
          method: 'POST',
          body: JSON.stringify({
            character,
            setting,
            description,
            title,
            selected_prompts: selectedPrompts,
            custom_options: customOptions,
          }),
        });

        // Complete progress bar if wizard is active
        if (
          window.campaignWizard &&
          typeof window.campaignWizard.completeProgress === 'function'
        ) {
          window.campaignWizard.completeProgress();
        }

        history.pushState(
          { campaignId: data.campaign_id },
          '',
          `/game/${data.campaign_id}`,
        );

        // Add a small delay to ensure Firestore data is available
        // This helps with eventual consistency issues
        setTimeout(() => {
          console.log('Loading newly created campaign after delay...');
          handleRouteChange();
        }, 500); // 500ms delay
      } catch (error) {
        console.error('Error creating campaign:', error);
        hideSpinner();

        // RESILIENCE: Better error messaging and recovery options
        let userMessage = 'Failed to start a new campaign.';
        let showRetryOption = false;

        if (
          error.message.includes('Token used too early') ||
          error.message.includes('clock')
        ) {
          userMessage =
            '⏰ Authentication timing issue detected. This usually resolves automatically.';
          showRetryOption = true;
        } else if (
          error.message.includes('401') ||
          error.message.includes('Auth failed')
        ) {
          userMessage =
            '🔐 Authentication issue. Please try signing out and back in.';
        } else if (
          error.message.includes('Network') ||
          error.message.includes('fetch')
        ) {
          userMessage =
            '🌐 Network connection issue. Please check your internet connection.';
          showRetryOption = true;
        }

        if (showRetryOption) {
          const retry = confirm(
            `${userMessage}\n\nWould you like to try again?`,
          );
          if (retry) {
            // Retry after a short delay
            setTimeout(() => {
              document
                .getElementById('new-campaign-form')
                .dispatchEvent(new Event('submit'));
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
          interactionForm.dispatchEvent(
            new Event('submit', { cancelable: true }),
          );
        }
      }
    });
  }

  if (interactionForm) {
    interactionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      let userInput = userInputEl.value.trim();
      if (!userInput || !currentCampaignId) return;
      const mode = document.querySelector(
        'input[name="interactionMode"]:checked',
      ).value;
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

      // Prepend "THINK:" for think mode if not already prefixed
      let processedInput = userInput;
      if (mode === 'think' && !userInput.toUpperCase().startsWith('THINK:')) {
        processedInput = `THINK:${userInput}`;
      }

      appendToStory('user', userInput, mode);
      userInputEl.value = '';
      try {
        const { data, duration } = await fetchApi(
          `/api/campaigns/${currentCampaignId}/interaction`,
          {
            method: 'POST',
            body: JSON.stringify({ input: processedInput, mode }),
          },
        );
        // Use user_scene_number from backend response
        // Use 'narrative' field if available (per schema), fall back to 'response' for compatibility
        // Handle empty strings as missing (defensive check)
        let narrativeText = data.narrative || data.response || '[Error: No response from server]';
        if (!narrativeText || narrativeText.trim() === '') {
          narrativeText = '[Error: Empty narrative from server]';
          console.error('⚠️ Empty narrative received:', { narrative: data.narrative, response: data.response, fullData: data });
        }
        appendToStory(
          'gemini',
          narrativeText,
          null,
          data.debug_mode || false,
          data.user_scene_number,
          data,
        );
        timerInfo.textContent = `Response time: ${duration}s`;

        // Update debug mode indicator if present
        const debugIndicator = document.getElementById('debug-indicator');
        if (debugIndicator) {
          debugIndicator.style.display = data.debug_mode ? 'block' : 'none';
        }

        // Re-enable all choice buttons now that we have a new response
        document.querySelectorAll('.choice-button').forEach((btn) => {
          btn.disabled = false;
        });
      } catch (error) {
        // Enhanced error logging for debugging
        console.error('🔴 Interaction failed:', error);
        console.error('🔴 Error name:', error.name);
        console.error('🔴 Error message:', error.message);
        console.error('🔴 Error stack:', error.stack);
        console.error('🔴 Firebase auth state:', firebase.auth().currentUser ? 'signed in' : 'NOT signed in');

        // Provide specific error messages based on error type
        let userMessage = 'Sorry, an error occurred. Please try again.';

        if (error.message?.includes('User not authenticated') || error.message?.includes('not authenticated')) {
          userMessage = '🔐 Session expired. Please refresh the page and sign in again.';
          console.error('🔴 AUTH ERROR: User not authenticated - Firebase currentUser is null');
        } else if (error.name === 'AbortError') {
          userMessage = '⏱️ Request timed out. Please try again.';
          console.error('🔴 TIMEOUT ERROR: Request was aborted');
        } else if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError') || error.message?.includes('network')) {
          userMessage = '🌐 Network error. Please check your connection and try again.';
          console.error('🔴 NETWORK ERROR: Failed to reach server');
        } else if (error.message?.includes('HTTP Error')) {
          userMessage = `⚠️ Server error: ${error.message}`;
          console.error('🔴 HTTP ERROR:', error.message);
        } else if (error.message?.includes('JSON')) {
          userMessage = '⚠️ Invalid response from server. Please try again.';
          console.error('🔴 JSON PARSE ERROR: Server returned invalid JSON');
        }

        appendToStory('system', userMessage);
        // Re-enable choice buttons even on error
        document.querySelectorAll('.choice-button').forEach((btn) => {
          btn.disabled = false;
        });
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
          title: campaignItem.dataset.campaignTitle,
        };
        const editModalEl = document.getElementById('editCampaignModal');
        const editModal = new bootstrap.Modal(editModalEl);
        document.getElementById('edit-campaign-title').value =
          campaignToEdit.title;
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
      alert('Campaign title cannot be empty.');
      return;
    }

    showSpinner('saving');
    try {
      await fetchApi(`/api/campaigns/${campaignToEdit.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ title: newTitle }),
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

  document
    .getElementById('save-campaign-title-btn')
    .addEventListener('click', saveCampaignTitle);

  // Add form submit handler for Enter key support
  document
    .getElementById('edit-campaign-form')
    .addEventListener('submit', (e) => {
      e.preventDefault();
      saveCampaignTitle();
    });

  // --- Share & Download Functionality ---
  function getFormattedStoryText() {
    const storyContent = document.getElementById('story-content');
    if (!storyContent) return '';
    const paragraphs = storyContent.querySelectorAll('p');
    return Array.from(paragraphs)
      .map((p) => p.innerText.trim())
      .join('\\n\\n');
  }

  async function downloadFile(format) {
    if (!currentCampaignId) return;
    showSpinner('saving');
    try {
      let headers = {};

      if (window.authTokenManager) {
        headers = await window.authTokenManager.getAuthHeaders();
      } else if (isTestMode && window.testAuthBypass) {
        // Use test bypass headers
        headers = {
          'X-Test-Bypass-Auth': 'true',
          'X-Test-User-ID': window.testAuthBypass.userId,
        };
      } else {
        // Normal auth flow
        const user = firebase.auth().currentUser;
        if (!user) throw new Error('User not authenticated for download.');
        const token = await user.getIdToken();
        headers = {
          Authorization: `Bearer ${token}`,
        };
      }

      const response = await fetch(
        `/api/campaigns/${currentCampaignId}/export?format=${format}`,
        {
          headers: headers,
        },
      );

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: 'Could not download story.' }));
        throw new Error(
          errorData.error || `HTTP error! status: ${response.status}`,
        );
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
      alert(
        'Share feature is only available on supported devices, like mobile phones.',
      );
      return;
    }
    const storyText = getFormattedStoryText();
    const storyTitle =
      document.getElementById('game-title').innerText ||
      'My WorldArchitect.AI Story';
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
      shareText =
        storyText.substring(0, maxShareSize) +
        '...\n\n[Story continues - full version available at WorldArchitect.AI]';

      // Ask user if they want to share truncated version
      const userChoice = confirm(
        `Your story is very long (${Math.round(storyText.length / 1000)}KB). ` +
        'Would you like to share a shortened preview, or cancel and use Download instead?',
      );

      if (!userChoice) {
        alert(
          'Consider using the Download button to save your full story instead.',
        );
        return;
      }
    }

    try {
      await navigator.share({ title: storyTitle, text: shareText });
    } catch (error) {
      console.error('Error sharing story:', error);
      // Fallback suggestion for share failures
      alert(
        'Share failed. Try using the Download button to save your story, or copy the text manually from the story area.',
      );
    }
  }

  function handleDownloadClick() {
    const downloadModal = new bootstrap.Modal(
      document.getElementById('downloadOptionsModal'),
    );
    downloadModal.show();
  }

  // Attach all action event listeners
  document
    .getElementById('shareStoryBtn')
    ?.addEventListener('click', handleShareStory);
  document
    .getElementById('downloadStoryBtn')
    ?.addEventListener('click', handleDownloadClick);
  document
    .getElementById('download-txt-btn')
    ?.addEventListener('click', () => downloadFile('txt'));
  document
    .getElementById('download-pdf-btn')
    ?.addEventListener('click', () => downloadFile('pdf'));
  document
    .getElementById('download-docx-btn')
    ?.addEventListener('click', () => downloadFile('docx'));

  // Spicy Mode Toggle Handler
  let SPICY_MODEL = window.APP_MODELS?.SPICY_MODEL || 'x-ai/grok-4.1-fast';
  let DEFAULT_GEMINI_MODEL =
    window.APP_MODELS?.DEFAULT_GEMINI_MODEL || 'gemini-3-flash-preview';
  let DEFAULT_OPENROUTER_MODEL =
    window.APP_MODELS?.DEFAULT_OPENROUTER_MODEL || 'meta-llama/llama-3.1-70b-instruct';
  let DEFAULT_CEREBRAS_MODEL =
    window.APP_MODELS?.DEFAULT_CEREBRAS_MODEL || 'zai-glm-4.6';

  const modelConstantsPromise = loadModelConstants();

  async function loadModelConstants() {
    try {
      const { data } = await fetchApi('/api/constants/models', { method: 'GET' });
      if (data?.SPICY_MODEL) {
        SPICY_MODEL = data.SPICY_MODEL;
      }
      if (data?.DEFAULT_GEMINI_MODEL) {
        DEFAULT_GEMINI_MODEL = data.DEFAULT_GEMINI_MODEL;
      }
      if (data?.DEFAULT_OPENROUTER_MODEL) {
        DEFAULT_OPENROUTER_MODEL = data.DEFAULT_OPENROUTER_MODEL;
      }
      if (data?.DEFAULT_CEREBRAS_MODEL) {
        DEFAULT_CEREBRAS_MODEL = data.DEFAULT_CEREBRAS_MODEL;
      }
    } catch (error) {
      console.warn('Failed to load model constants from backend; using defaults', error);
    }
  }

  /**
   * Show a toast notification for spicy mode changes
   */
  function showSpicyModeToast(enabled, modelName) {
    // Remove any existing toast
    const existingToast = document.getElementById('spicy-mode-toast');
    if (existingToast) {
      existingToast.remove();
    }

    // Create toast container if it doesn't exist - centered on screen
    let toastContainer = document.querySelector('.spicy-toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.className = 'spicy-toast-container position-fixed top-50 start-50 translate-middle p-3';
      toastContainer.style.zIndex = '1100';
      document.body.appendChild(toastContainer);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.id = 'spicy-mode-toast';
    toast.className = 'toast show';
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      <div class="toast-header ${enabled ? 'bg-success text-white' : 'bg-secondary text-white'}">
        <strong class="me-auto">${enabled ? '🌶️ Spicy Mode Enabled' : '❄️ Spicy Mode Off'}</strong>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">
        ${enabled ? 'Switched to Grok AI for uncensored content.' : 'Restored previous model.'}<br>
        <small class="text-muted">Now using: ${modelName}</small>
      </div>
    `;

    toastContainer.appendChild(toast);

    // Add close button handler
    toast.querySelector('.btn-close').addEventListener('click', () => {
      toast.remove();
    });

    // Auto-hide after 4 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
      }
    }, 4000);
  }

  /**
   * Handle spicy mode toggle
   */
  async function handleSpicyModeToggle(enabled) {
    try {
      await modelConstantsPromise;

      if (enabled) {
        // First, get current settings to store the pre-spicy model
        const settingsResponse = await fetchApi('/api/settings', { method: 'GET' });
        const currentSettings = settingsResponse.data || {};

        // Determine current provider and model to save for restoration later
        const currentProvider = currentSettings.llm_provider || 'gemini';
        let currentModel;
        if (currentProvider === 'openrouter') {
          currentModel = currentSettings.openrouter_model || DEFAULT_OPENROUTER_MODEL;
        } else if (currentProvider === 'cerebras') {
          currentModel = currentSettings.cerebras_model || DEFAULT_CEREBRAS_MODEL;
        } else {
          currentModel = currentSettings.gemini_model || DEFAULT_GEMINI_MODEL;
        }

        // Save spicy mode settings with the model to restore later
        await fetchApi('/api/settings', {
          method: 'POST',
          body: JSON.stringify({
            spicy_mode: true,
            pre_spicy_model: currentModel,
            pre_spicy_provider: currentProvider,
            llm_provider: 'openrouter',
            openrouter_model: SPICY_MODEL,
          }),
        });

        const spicyDisplayName = SPICY_MODEL.split('/').pop() || SPICY_MODEL;
        showSpicyModeToast(true, spicyDisplayName);
      } else {
        // Get the saved pre-spicy model
        const settingsResponse = await fetchApi('/api/settings', { method: 'GET' });
        const currentSettings = settingsResponse.data || {};

        const restoreModel =
          currentSettings.pre_spicy_model ||
          (currentSettings.pre_spicy_provider === 'openrouter'
            ? DEFAULT_OPENROUTER_MODEL
            : currentSettings.pre_spicy_provider === 'cerebras'
              ? DEFAULT_CEREBRAS_MODEL
              : DEFAULT_GEMINI_MODEL);
        const restoreProvider = currentSettings.pre_spicy_provider || 'gemini';

        // Prepare settings to restore
        const restoreSettings = {
          spicy_mode: false,
          llm_provider: restoreProvider,
        };

        // Set the appropriate model based on provider
        if (restoreProvider === 'openrouter') {
          restoreSettings.openrouter_model = restoreModel;
        } else if (restoreProvider === 'cerebras') {
          restoreSettings.cerebras_model = restoreModel;
        } else {
          restoreSettings.gemini_model = restoreModel;
        }

        await fetchApi('/api/settings', {
          method: 'POST',
          body: JSON.stringify(restoreSettings),
        });

        // Format display name for toast based on the actual model
        const displayName = restoreModel.split('/').pop() || restoreModel;

        showSpicyModeToast(false, displayName);
      }
    } catch (error) {
      console.error('Failed to toggle spicy mode:', error);
      // Revert the checkbox state on error
      const spicySwitch = document.getElementById('spicyModeSwitch');
      if (spicySwitch) {
        spicySwitch.checked = !enabled;
      }
      alert('Failed to update spicy mode. Please try again.');
    }
  }

  /**
   * Load spicy mode state from settings
   */
  async function loadSpicyModeState() {
    try {
      const { data } = await fetchApi('/api/settings', { method: 'GET' });
      const spicySwitch = document.getElementById('spicyModeSwitch');
      if (spicySwitch && data) {
        spicySwitch.checked = data.spicy_mode === true;
      }
    } catch (error) {
      console.error('Failed to load spicy mode state:', error);
    }
  }

  // Attach spicy mode toggle handler
  const spicyModeSwitch = document.getElementById('spicyModeSwitch');
  let spicyToggleInProgress = false;
  if (spicyModeSwitch) {
    spicyModeSwitch.addEventListener('change', async (e) => {
      if (spicyToggleInProgress) {
        e.preventDefault();
        e.target.checked = !e.target.checked;
        return;
      }

      spicyToggleInProgress = true;
      spicyModeSwitch.disabled = true;

      try {
        await handleSpicyModeToggle(e.target.checked);
        await loadSpicyModeState();
      } finally {
        spicyToggleInProgress = false;
        spicyModeSwitch.disabled = false;
      }
    });
  }

  // Load spicy mode state when campaign view is shown and ensure tooltips are active
  window.addEventListener('campaignLoaded', () => {
    loadSpicyModeState();

    // Initialize tooltips in the now-visible game view (e.g., spicy info button)
    const gameViewTooltips = document
      .getElementById('game-view')
      ?.querySelectorAll('[data-bs-toggle="tooltip"]');
    gameViewTooltips?.forEach((tooltipTriggerEl) => {
      bootstrap.Tooltip.getOrCreateInstance(tooltipTriggerEl);
    });
  });

  // Theme integration
  window.addEventListener('themeChanged', (e) => {
    console.log(`Theme changed to: ${e.detail.theme}`);
  });

  // Handle authentication or test mode
  if (isTestMode) {
    // In test mode, wait for test mode to be ready then proceed
    window.addEventListener('testModeReady', (e) => {
      const userEmailElement = document.getElementById('user-email');
      if (userEmailElement) {
        userEmailElement.textContent = `Test User (${e.detail.userId})`;
        userEmailElement.style.display = 'block';
      }
      handleRouteChange();
    });
  } else {
    // Normal authentication flow
    firebase.auth().onAuthStateChanged((user) => {
      const userEmailElement = document.getElementById('user-email');
      if (user && userEmailElement) {
        userEmailElement.textContent = user.email;
        userEmailElement.style.display = 'block';
      } else if (userEmailElement) {
        userEmailElement.style.display = 'none';
      }
      handleRouteChange();
    });
  }

  // Main navigation listeners (these must remain at the end of DOMContentLoaded)
  document
    .getElementById('go-to-new-campaign')
    .addEventListener('click', () => {
      isNavigatingToNewCampaignDirectly = true;
      history.pushState({}, '', '/new-campaign');
      handleRouteChange();

      // CRITICAL FIX: Enable wizard after navigation completes
      if (window.campaignWizard) {
        window.campaignWizard.enable();
      }
    });

  document.getElementById('back-to-dashboard').addEventListener('click', () => {
    history.pushState({}, '', '/');
    handleRouteChange();
  });

  // Helper function for settings navigation
  function navigateToSettings() {
    history.pushState({}, '', '/settings');
    handleRouteChange();
  }

  // Settings button navigation (dashboard)
  document.getElementById('settings-btn').addEventListener('click', navigateToSettings);

  // Game view settings button navigation
  const gameSettingsBtn = document.getElementById('game-settings-btn');
  if (gameSettingsBtn) {
    gameSettingsBtn.addEventListener('click', navigateToSettings);
  }
  window.addEventListener('popstate', handleRouteChange);
});

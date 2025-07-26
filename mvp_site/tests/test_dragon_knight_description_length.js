/**
 * Unit test for Dragon Knight campaign description length handling
 * Tests that the longer description is properly handled by the campaign wizard
 */

describe('Dragon Knight Campaign Description Length', function() {
  let campaignWizard;

  beforeEach(function() {
    // Mock DOM elements needed for testing
    document.body.innerHTML = `
      <div id="new-campaign-form" style="display: none;">
        <input id="campaign-title" />
        <input id="character-input" />
        <input id="setting-input" />
        <textarea id="description-input"></textarea>
        <input type="checkbox" id="generate-companions" />
      </div>
      <div class="interface-mode-controls">
        <button id="modern-mode-btn" class="btn btn-primary active">Modern</button>
      </div>
    `;

    // Mock window.interfaceManager
    window.interfaceManager = {
      isModernMode: () => true
    };

    // Create campaign wizard instance
    campaignWizard = new CampaignWizard();
  });

  afterEach(function() {
    document.body.innerHTML = '';
    delete window.interfaceManager;
    delete window.campaignWizard;
  });

  it('should handle long Dragon Knight description without errors', function() {
    const description = CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION;

    // Test that description is properly defined and not placeholder
    expect(description).toBeDefined();
    expect(description).not.toContain('[PLACEHOLDER');
    expect(description.length).toBeGreaterThan(1000); // Should be much longer than before

    // Test that description contains expected Dragon Knight content
    expect(description).toContain('Ser Arion');
    expect(description).toContain('Celestial Imperium');
    expect(description).toContain('Empress Sariel');
    expect(description).toContain('Campaign summary');
  });

  it('should properly format long descriptions in preview', function() {
    const longDescription = CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION;

    // Test formatting helper function
    const formatted = campaignWizard._formatDescription(longDescription, true);

    // Should truncate long descriptions for preview
    expect(formatted.length).toBeLessThanOrEqual(53); // 50 chars + "..."
    expect(formatted).toContain('...');
  });

  it('should handle Dragon Knight description in form data collection', function() {
    // Set up wizard with Dragon Knight selected
    document.body.innerHTML += `
      <div id="campaign-wizard">
        <input type="radio" id="wizard-dragon-knight-campaign" name="wizardCampaignType" value="dragon-knight" checked />
        <input type="text" id="wizard-campaign-title" value="Test Campaign" />
        <input type="text" id="wizard-character-input" value="Ser Arion" />
        <input type="text" id="wizard-setting-input" value="World of Assiah" />
        <textarea id="wizard-description-input">${CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION}</textarea>
        <input type="checkbox" id="wizard-narrative" checked />
        <input type="checkbox" id="wizard-mechanics" checked />
        <input type="checkbox" id="wizard-companions" checked />
        <input type="checkbox" id="wizard-default-world" checked />
      </div>
    `;

    const formData = campaignWizard.collectFormData();

    // Should collect the long description properly
    expect(formData.description).toBe(CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION);
    expect(formData.description.length).toBeGreaterThan(1000);
    expect(formData.title).toBe('Test Campaign');
    expect(formData.character).toBe('Ser Arion');
    expect(formData.setting).toBe('World of Assiah');
  });

  it('should populate original form with long description', function() {
    const longDescription = CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION;

    const formData = {
      title: 'Dragon Knight Campaign',
      character: 'Ser Arion',
      setting: 'World of Assiah',
      description: longDescription,
      selectedPrompts: ['narrative', 'mechanics'],
      customOptions: ['companions', 'defaultWorld']
    };

    campaignWizard.populateOriginalForm(formData);

    const descriptionInput = document.getElementById('description-input');
    expect(descriptionInput.value).toBe(longDescription);
    expect(descriptionInput.value.length).toBeGreaterThan(1000);
  });

  it('should handle campaign type change to Dragon Knight', async function() {
    // Set up wizard DOM
    document.body.innerHTML += `
      <div id="campaign-wizard">
        <input type="radio" id="wizard-dragon-knight-campaign" name="wizardCampaignType" value="dragon-knight" />
        <input type="text" id="wizard-character-input" />
        <input type="text" id="wizard-setting-input" />
        <textarea id="wizard-description-input"></textarea>
        <div id="wizard-character-section"></div>
        <div id="wizard-setting-section"></div>
        <div id="wizard-description-section"></div>
        <div id="wizard-dragon-knight-description"></div>
        <div class="campaign-type-card" data-type="dragon-knight"></div>
        <div class="campaign-type-card" data-type="custom"></div>
      </div>
    `;

    await campaignWizard.handleCampaignTypeChange('dragon-knight');

    const descriptionInput = document.getElementById('wizard-description-input');
    const characterInput = document.getElementById('wizard-character-input');
    const settingInput = document.getElementById('wizard-setting-input');

    // Should pre-fill with Dragon Knight content
    expect(descriptionInput.value).toBe(CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION);
    expect(characterInput.value).toBe('Ser Arion');
    expect(settingInput.value).toBe('World of Assiah');
  });

  it('should validate description length limits', function() {
    const description = CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION;

    // Test that even very long descriptions are accepted
    expect(description.length).toBeGreaterThan(0);
    expect(description.length).toBeLessThan(100000); // Reasonable upper limit

    // Test that it doesn't contain obvious formatting issues
    expect(description).not.toContain('undefined');
    expect(description).not.toContain('null');
    expect(description).not.toContain('[object Object]');
  });
});

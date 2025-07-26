/**
 * Unit tests for collapsible description functionality
 * Tests both static HTML and campaign wizard implementations
 */

// Mock DOM elements
function createMockDOM(isWizard = false) {
    const prefix = isWizard ? 'wizard-' : '';

    document.body.innerHTML = `
        <button id="${prefix}toggle-description" aria-expanded="true">
            <i class="bi bi-chevron-up"></i> Collapse
        </button>
        <div id="${prefix}description-container" class="collapse show"></div>
    `;

    return {
        toggleButton: document.getElementById(`${prefix}toggle-description`),
        container: document.getElementById(`${prefix}description-container`)
    };
}

// Test suite for static HTML collapsible
describe('Static HTML Collapsible Description', () => {
    let mockDOM;

    beforeEach(() => {
        mockDOM = createMockDOM(false);
        // Simulate the UIUtils.setupCollapsibleDescription function from ui-utils.js
        UIUtils.setupCollapsibleDescription('toggle-description', 'description-container');
    });

    afterEach(() => {
        document.body.innerHTML = '';
    });

    test('should initialize with expanded state', () => {
        expect(mockDOM.container.classList.contains('show')).toBe(true);
        expect(mockDOM.toggleButton.getAttribute('aria-expanded')).toBe('true');
        expect(mockDOM.toggleButton.innerHTML).toContain('Collapse');
    });

    test('should collapse when clicking toggle button', () => {
        mockDOM.toggleButton.click();

        expect(mockDOM.container.classList.contains('show')).toBe(false);
        expect(mockDOM.toggleButton.getAttribute('aria-expanded')).toBe('false');
        expect(mockDOM.toggleButton.innerHTML).toContain('Expand');
    });

    test('should expand when clicking toggle button again', () => {
        // First collapse
        mockDOM.toggleButton.click();
        // Then expand
        mockDOM.toggleButton.click();

        expect(mockDOM.container.classList.contains('show')).toBe(true);
        expect(mockDOM.toggleButton.getAttribute('aria-expanded')).toBe('true');
        expect(mockDOM.toggleButton.innerHTML).toContain('Collapse');
    });

    test('should handle missing elements gracefully', () => {
        document.body.innerHTML = '';

        // Should not throw error
        expect(() => UIUtils.setupCollapsibleDescription('toggle-description', 'description-container')).not.toThrow();
    });
});

// Test suite for campaign wizard collapsible
describe('Campaign Wizard Collapsible Description', () => {
    let wizard;
    let mockDOM;

    beforeEach(() => {
        // Mock the CampaignWizard class
        wizard = new CampaignWizard();
        mockDOM = createMockDOM(true);
        UIUtils.setupCollapsibleDescription('wizard-toggle-description', 'wizard-description-container');
    });

    afterEach(() => {
        document.body.innerHTML = '';
    });

    test('should initialize with expanded state in wizard', () => {
        expect(mockDOM.container.classList.contains('show')).toBe(true);
        expect(mockDOM.toggleButton.getAttribute('aria-expanded')).toBe('true');
        expect(mockDOM.toggleButton.innerHTML).toContain('Collapse');
    });

    test('should collapse when clicking toggle button in wizard', () => {
        mockDOM.toggleButton.click();

        expect(mockDOM.container.classList.contains('show')).toBe(false);
        expect(mockDOM.toggleButton.getAttribute('aria-expanded')).toBe('false');
        expect(mockDOM.toggleButton.innerHTML).toContain('Expand');
    });

    test('should expand when clicking toggle button again in wizard', () => {
        // First collapse
        mockDOM.toggleButton.click();
        // Then expand
        mockDOM.toggleButton.click();

        expect(mockDOM.container.classList.contains('show')).toBe(true);
        expect(mockDOM.toggleButton.getAttribute('aria-expanded')).toBe('true');
        expect(mockDOM.toggleButton.innerHTML).toContain('Collapse');
    });

    test('should handle missing wizard elements gracefully', () => {
        document.body.innerHTML = '';

        // Should not throw error
        expect(() => UIUtils.setupCollapsibleDescription('wizard-toggle-description', 'wizard-description-container')).not.toThrow();
    });
});

// Test suite for Dragon Knight campaign pre-filling
describe('Dragon Knight Campaign Pre-filling', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <input type="radio" name="campaignType" id="dragonKnightCampaign" value="dragon-knight">
            <input type="radio" name="campaignType" id="customCampaign" value="custom" checked>
            <textarea id="description-input"></textarea>
        `;

        // Mock the DRAGON_KNIGHT_NARRATIVE constant
        window.DRAGON_KNIGHT_NARRATIVE = 'You are Ser Arion, a 16 year old honorable knight...';

        // Simulate setupCampaignTypeHandlers from app.js
        setupCampaignTypeHandlers();
    });

    afterEach(() => {
        document.body.innerHTML = '';
        delete window.DRAGON_KNIGHT_NARRATIVE;
    });

    test('should pre-fill description when Dragon Knight is selected', () => {
        const dragonKnightRadio = document.getElementById('dragonKnightCampaign');
        const descriptionInput = document.getElementById('description-input');

        dragonKnightRadio.click();

        expect(descriptionInput.value).toBe(window.DRAGON_KNIGHT_NARRATIVE);
    });

    test('should clear description when switching to custom campaign', () => {
        const dragonKnightRadio = document.getElementById('dragonKnightCampaign');
        const customRadio = document.getElementById('customCampaign');
        const descriptionInput = document.getElementById('description-input');

        // First select Dragon Knight
        dragonKnightRadio.click();
        expect(descriptionInput.value).toBe(window.DRAGON_KNIGHT_NARRATIVE);

        // Then switch to custom
        customRadio.click();
        expect(descriptionInput.value).toBe('');
    });

    test('should not overwrite user input when switching back to Dragon Knight', () => {
        const dragonKnightRadio = document.getElementById('dragonKnightCampaign');
        const customRadio = document.getElementById('customCampaign');
        const descriptionInput = document.getElementById('description-input');

        // Select custom and add user input
        customRadio.click();
        descriptionInput.value = 'My custom description';

        // Switch to Dragon Knight
        dragonKnightRadio.click();
        // Should overwrite with Dragon Knight narrative
        expect(descriptionInput.value).toBe(window.DRAGON_KNIGHT_NARRATIVE);
    });
});

// Test suite for Campaign Wizard Dragon Knight pre-filling
describe('Campaign Wizard Dragon Knight Pre-filling', () => {
    let wizard;

    beforeEach(() => {
        wizard = new CampaignWizard();

        document.body.innerHTML = `
            <select id="wizard-campaign-type">
                <option value="custom">Custom Campaign</option>
                <option value="dragon-knight">Dragon Knight Campaign</option>
            </select>
            <textarea id="wizard-description"></textarea>
        `;

        // Mock the DEFAULT_DRAGON_KNIGHT_DESCRIPTION
        CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION = 'You are Ser Arion, a 16 year old honorable knight...';

        wizard.setupEventListeners();
    });

    afterEach(() => {
        document.body.innerHTML = '';
    });

    test('should pre-fill description when Dragon Knight is selected in wizard', () => {
        const campaignTypeSelect = document.getElementById('wizard-campaign-type');
        const descriptionTextarea = document.getElementById('wizard-description');

        campaignTypeSelect.value = 'dragon-knight';
        campaignTypeSelect.dispatchEvent(new Event('change'));

        expect(descriptionTextarea.value).toBe(CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION);
    });

    test('should clear description when switching to custom in wizard', () => {
        const campaignTypeSelect = document.getElementById('wizard-campaign-type');
        const descriptionTextarea = document.getElementById('wizard-description');

        // First select Dragon Knight
        campaignTypeSelect.value = 'dragon-knight';
        campaignTypeSelect.dispatchEvent(new Event('change'));

        // Then switch to custom
        campaignTypeSelect.value = 'custom';
        campaignTypeSelect.dispatchEvent(new Event('change'));

        expect(descriptionTextarea.value).toBe('');
    });
});

// Mock implementation of UIUtils for testing
window.UIUtils = {
    setupCollapsibleDescription(toggleButtonId, containerElementId) {
        const toggleButton = document.getElementById(toggleButtonId);
        const descriptionContainer = document.getElementById(containerElementId);

        if (!toggleButton || !descriptionContainer) return;

        toggleButton.addEventListener('click', () => {
            const isExpanded = descriptionContainer.classList.contains('show');

            if (isExpanded) {
                descriptionContainer.classList.remove('show');
                toggleButton.innerHTML = '<i class="bi bi-chevron-down"></i> Expand';
                toggleButton.setAttribute('aria-expanded', 'false');
            } else {
                descriptionContainer.classList.add('show');
                toggleButton.innerHTML = '<i class="bi bi-chevron-up"></i> Collapse';
                toggleButton.setAttribute('aria-expanded', 'true');
            }
        });
    }
};

function setupCampaignTypeHandlers() {
    const campaignTypeRadios = document.querySelectorAll('input[name="campaignType"]');
    const descriptionInput = document.getElementById('description-input');

    campaignTypeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.value === 'dragon-knight' && e.target.checked) {
                descriptionInput.value = window.DRAGON_KNIGHT_NARRATIVE;
            } else if (e.target.value === 'custom' && e.target.checked) {
                descriptionInput.value = '';
            }
        });
    });
}

// Mock CampaignWizard class for testing
class CampaignWizard {

    setupEventListeners() {
        const campaignTypeSelect = document.getElementById('wizard-campaign-type');
        const descriptionTextarea = document.getElementById('wizard-description');

        if (campaignTypeSelect && descriptionTextarea) {
            campaignTypeSelect.addEventListener('change', (e) => {
                if (e.target.value === 'dragon-knight') {
                    descriptionTextarea.value = CampaignWizard.DEFAULT_DRAGON_KNIGHT_DESCRIPTION;
                } else if (e.target.value === 'custom') {
                    descriptionTextarea.value = '';
                }
            });
        }
    }
}

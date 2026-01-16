class CampaignWizardEditablePreviewTests {
  constructor() {
    this.testResults = [];
  }

  assert(condition, name, details) {
    if (condition) {
      this.testResults.push({ name, status: 'PASS', details });
      return true;
    }
    this.testResults.push({ name, status: 'FAIL', details });
    return false;
  }

  getWizard() {
    return window.campaignWizard;
  }

  getEditableItem(field) {
    return document.querySelector(`.editable-preview[data-field="${field}"]`);
  }

  click(element) {
    element.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  }

  keydown(element, key) {
    element.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key }));
  }

  run() {
    this.testEnterExitTextEdit();
    this.testCheckboxSyncOnExitWithoutChange();
    this.testCheckboxEscapeCancels();
    this.testSwitchingFieldsClosesPrevious();
  }

  testEnterExitTextEdit() {
    const testName = 'Text edit saves on Enter and updates preview';

    try {
      const wizard = this.getWizard();
      if (!wizard) throw new Error('window.campaignWizard not initialized');

      const item = this.getEditableItem('title');
      const preview = document.getElementById('preview-title');
      const editInput = document.getElementById('edit-title');
      const formInput = document.getElementById('wizard-campaign-title');

      if (!item || !preview || !editInput || !formInput) {
        throw new Error('Missing DOM for title editable preview');
      }

      const nextTitle = 'Updated Title From Test';

      this.click(preview);
      this.assert(
        item.classList.contains('editing'),
        testName,
        'Enters edit mode on click',
      );

      editInput.value = nextTitle;
      this.keydown(editInput, 'Enter');

      this.assert(
        !item.classList.contains('editing'),
        testName,
        'Exits edit mode on Enter',
      );
      this.assert(
        formInput.value === nextTitle,
        testName,
        'Syncs title into form input',
      );
      this.assert(
        preview.textContent === nextTitle,
        testName,
        'Updates preview text',
      );
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message,
      });
    }
  }

  testCheckboxSyncOnExitWithoutChange() {
    const testName = 'Checkbox edits sync on click-outside exit (no change event)';

    try {
      const wizard = this.getWizard();
      if (!wizard) throw new Error('window.campaignWizard not initialized');

      const item = this.getEditableItem('personalities');
      const preview = document.getElementById('preview-personalities');
      const editContainer = document.getElementById('edit-personalities');
      const editMechanics = document.getElementById('edit-mechanics');
      const wizardMechanics = document.getElementById('wizard-mechanics');
      const outside = document.getElementById('outside-click-target');

      if (
        !item ||
        !preview ||
        !editContainer ||
        !editMechanics ||
        !wizardMechanics ||
        !outside
      ) {
        throw new Error('Missing DOM for personalities editable preview');
      }

      wizardMechanics.checked = true;

      this.click(preview);
      this.assert(
        item.classList.contains('editing'),
        testName,
        'Enters edit mode for checkbox field',
      );

      editMechanics.checked = false;
      this.click(outside);

      this.assert(
        !item.classList.contains('editing'),
        testName,
        'Exits edit mode on click outside',
      );
      this.assert(
        wizardMechanics.checked === false,
        testName,
        'Syncs checkbox state back to form on exit',
      );
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message,
      });
    }
  }

  testCheckboxEscapeCancels() {
    const testName = 'Escape cancels checkbox edits and restores snapshot';

    try {
      const wizard = this.getWizard();
      if (!wizard) throw new Error('window.campaignWizard not initialized');

      const item = this.getEditableItem('personalities');
      const preview = document.getElementById('preview-personalities');
      const editContainer = document.getElementById('edit-personalities');
      const editMechanics = document.getElementById('edit-mechanics');
      const wizardMechanics = document.getElementById('wizard-mechanics');

      if (
        !item ||
        !preview ||
        !editContainer ||
        !editMechanics ||
        !wizardMechanics
      ) {
        throw new Error('Missing DOM for personalities editable preview');
      }

      wizardMechanics.checked = true;

      this.click(preview);
      editMechanics.checked = false;
      this.keydown(editContainer, 'Escape');

      this.assert(
        !item.classList.contains('editing'),
        testName,
        'Exits edit mode on Escape',
      );
      this.assert(
        wizardMechanics.checked === true,
        testName,
        'Restores original checkbox state after cancel',
      );
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message,
      });
    }
  }

  testSwitchingFieldsClosesPrevious() {
    const testName = 'Switching editable fields closes prior field';

    try {
      const wizard = this.getWizard();
      if (!wizard) throw new Error('window.campaignWizard not initialized');

      const titleItem = this.getEditableItem('title');
      const descItem = this.getEditableItem('description');
      const previewTitle = document.getElementById('preview-title');
      const previewDesc = document.getElementById('preview-description');

      if (!titleItem || !descItem || !previewTitle || !previewDesc) {
        throw new Error('Missing DOM for title/description editable preview');
      }

      this.click(previewDesc);
      this.assert(
        descItem.classList.contains('editing'),
        testName,
        'Description enters edit mode',
      );

      this.click(previewTitle);
      this.assert(
        titleItem.classList.contains('editing'),
        testName,
        'Title enters edit mode',
      );
      this.assert(
        !descItem.classList.contains('editing'),
        testName,
        'Description edit mode closed when switching fields',
      );
    } catch (error) {
      this.testResults.push({
        name: testName,
        status: 'FAIL',
        details: error.message,
      });
    }
  }
}


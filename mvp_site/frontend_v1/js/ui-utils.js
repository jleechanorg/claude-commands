/**
 * Shared UI utility functions
 */

/**
 * Sets up collapsible description functionality for toggle button and container
 * @param {string} toggleButtonId - ID of the toggle button element
 * @param {string} containerElementId - ID of the container element to collapse/expand
 */
function setupCollapsibleDescription(toggleButtonId, containerElementId) {
  const toggleButton = document.getElementById(toggleButtonId);
  const descriptionContainer = document.getElementById(containerElementId);

  if (!toggleButton || !descriptionContainer) return;

  toggleButton.addEventListener('click', () => {
    const isExpanded = descriptionContainer.classList.contains('show');

    if (isExpanded) {
      // Collapse
      descriptionContainer.classList.remove('show');
      toggleButton.innerHTML = '<i class="bi bi-chevron-down"></i> Expand';
      toggleButton.setAttribute('aria-expanded', 'false');
    } else {
      // Expand
      descriptionContainer.classList.add('show');
      toggleButton.innerHTML = '<i class="bi bi-chevron-up"></i> Collapse';
      toggleButton.setAttribute('aria-expanded', 'true');
    }
  });
}

// Export for use in other modules
window.UIUtils = {
  setupCollapsibleDescription,
};

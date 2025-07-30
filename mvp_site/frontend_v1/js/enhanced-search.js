/**
 * Enhanced Search & Filter - Milestone 4 Interactive Features
 * Real-time campaign search, filtering, and sorting
 */

class EnhancedSearch {
  constructor() {
    this.campaigns = [];
    this.filteredCampaigns = [];
    this.currentFilters = {
      search: '',
      sortBy: 'lastPlayed',
      sortOrder: 'desc',
      theme: '',
      status: '',
    };
    this.isEnabled = false;
    this.searchDebounce = null;
    this.init();
  }

  // Debounce utility function for search performance
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  init() {
    this.checkIfEnabled();
    if (this.isEnabled) {
      this.setupSearchInterface();
      this.setupEventListeners();
      console.log('🔍 Enhanced Search activated');
    }
  }

  checkIfEnabled() {
    // Only enable in modern mode
    if (window.interfaceManager && window.interfaceManager.isModernMode()) {
      this.isEnabled = true;
    }

    // Listen for interface mode changes
    window.addEventListener('interfaceModeChanged', (e) => {
      if (e.detail.mode === 'modern') {
        this.enable();
      } else {
        this.disable();
      }
    });
  }

  enable() {
    this.isEnabled = true;
    this.setupSearchInterface();
  }

  disable() {
    this.isEnabled = false;
    this.removeSearchInterface();
  }

  setupSearchInterface() {
    const dashboardView = document.getElementById('dashboard-view');
    const campaignList = document.getElementById('campaign-list');

    if (
      !dashboardView ||
      !campaignList ||
      campaignList.previousElementSibling?.classList.contains(
        'search-filter-container',
      )
    ) {
      return;
    }

    const searchHTML = this.generateSearchHTML();
    campaignList.insertAdjacentHTML('beforebegin', searchHTML);

    this.setupEventListeners();
  }

  removeSearchInterface() {
    const searchContainer = document.querySelector('.search-filter-container');
    if (searchContainer) {
      searchContainer.remove();
    }
  }

  generateSearchHTML() {
    return `
      <div class="search-filter-container">
        <div class="search-box">
          <i class="fas fa-search search-icon"></i>
          <input type="text"
                 class="form-control"
                 id="campaign-search"
                 placeholder="Search campaigns...">
        </div>

        <div class="filter-controls">
          <div class="filter-group">
            <label for="sort-by">Sort by:</label>
            <select class="filter-select" id="sort-by">
              <option value="lastPlayed">Last Played</option>
              <option value="created">Date Created</option>
              <option value="title">Title (A-Z)</option>
            </select>
          </div>

          <div class="filter-group">
            <label for="sort-order">Order:</label>
            <select class="filter-select" id="sort-order">
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>

          <div class="filter-group">
            <label for="theme-filter">Theme:</label>
            <select class="filter-select" id="theme-filter">
              <option value="">All Themes</option>
              <option value="fantasy">Fantasy</option>
              <option value="sci-fi">Sci-Fi</option>
              <option value="mystery">Mystery</option>
              <option value="horror">Horror</option>
            </select>
          </div>

          <div class="filter-group">
            <label for="status-filter">Status:</label>
            <select class="filter-select" id="status-filter">
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="paused">Paused</option>
            </select>
          </div>


          <button type="button" class="btn btn-outline-secondary" id="clear-filters">
            <i class="fas fa-times me-1"></i>Clear
          </button>
        </div>

        <div class="filter-tags" id="active-filters"></div>

        <div class="search-stats mt-2">
          <small class="text-muted">
            Showing <span id="results-count">0</span> of <span id="total-count">0</span> campaigns
          </small>
        </div>
      </div>
    `;
  }

  setupEventListeners() {
    const searchInput = document.getElementById('campaign-search');
    const sortBy = document.getElementById('sort-by');
    const sortOrder = document.getElementById('sort-order');
    const themeFilter = document.getElementById('theme-filter');
    const statusFilter = document.getElementById('status-filter');
    const clearFilters = document.getElementById('clear-filters');

    if (!searchInput) return; // Not enabled yet

    // Real-time search with debounce
    const debouncedSearch = this.debounce((value) => {
      this.currentFilters.search = value.toLowerCase().trim();
      this.applyFilters();
    }, 300);

    searchInput.addEventListener('input', (e) => {
      debouncedSearch(e.target.value);
    });

    // Filter changes
    sortBy?.addEventListener('change', (e) => {
      this.currentFilters.sortBy = e.target.value;
      this.applyFilters();
    });

    sortOrder?.addEventListener('change', (e) => {
      this.currentFilters.sortOrder = e.target.value;
      this.updateSortOrderLabel();
      this.applyFilters();
    });

    themeFilter?.addEventListener('change', (e) => {
      this.currentFilters.theme = e.target.value;
      this.applyFilters();
    });

    statusFilter?.addEventListener('change', (e) => {
      this.currentFilters.status = e.target.value;
      this.applyFilters();
    });

    clearFilters?.addEventListener('click', () => {
      this.clearAllFilters();
    });

    // Listen for campaign list updates
    this.observeCampaignList();
  }

  updateSortOrderLabel() {
    const sortOrder = document.getElementById('sort-order');
    const sortBy = this.currentFilters.sortBy;

    if (sortOrder) {
      const options = sortOrder.querySelectorAll('option');
      if (sortBy === 'title') {
        options[0].textContent = 'A-Z';
        options[1].textContent = 'Z-A';
      } else {
        options[0].textContent = 'Newest First';
        options[1].textContent = 'Oldest First';
      }
    }
  }

  observeCampaignList() {
    const campaignList = document.getElementById('campaign-list');
    if (!campaignList) return;

    // Watch for changes to campaign list
    const observer = new MutationObserver(() => {
      this.refreshCampaignData();
    });

    observer.observe(campaignList, {
      childList: true,
      subtree: true,
    });
  }

  refreshCampaignData() {
    const campaignList = document.getElementById('campaign-list');
    if (!campaignList) return;

    // Extract campaign data from DOM
    this.campaigns = Array.from(campaignList.children).map((item) => {
      const titleElement = item.querySelector('h5, .campaign-title');
      const lastPlayedElement = item.querySelector(
        '.text-muted, .campaign-meta',
      );

      return {
        element: item,
        title: titleElement?.textContent || '',
        lastPlayed: this.parseDateFromElement(lastPlayedElement),
        created: this.extractCreatedDate(item),
        searchText: this.buildSearchText(item),
      };
    });

    this.applyFilters();
  }

  parseDateFromElement(element) {
    if (!element) return new Date(0);

    const text = element.textContent || '';
    const dateMatch = text.match(/Last played: (.+)/);
    if (dateMatch) {
      return new Date(dateMatch[1]);
    }

    return new Date(0);
  }

  extractCreatedDate(element) {
    // Try to extract creation date from data attributes or text
    const created = element.dataset.created;
    if (created) {
      return new Date(created);
    }

    // Fallback to current date if not available
    return new Date();
  }

  buildSearchText(element) {
    // Build searchable text from all campaign content
    const texts = [];

    // Title
    const title = element.querySelector('h5, .campaign-title');
    if (title) texts.push(title.textContent);

    // Description or preview text
    const description = element.querySelector('.campaign-description, p');
    if (description) texts.push(description.textContent);

    // Any other text content
    texts.push(element.textContent);

    return texts.join(' ').toLowerCase();
  }

  applyFilters() {
    if (!this.campaigns.length) {
      this.refreshCampaignData();
      return;
    }

    // Apply search filter
    this.filteredCampaigns = this.campaigns.filter((campaign) => {
      // Search filter
      if (
        this.currentFilters.search &&
        !campaign.searchText.includes(this.currentFilters.search)
      ) {
        return false;
      }

      return true;
    });

    // Apply sorting
    this.sortCampaigns(this.filteredCampaigns);

    this.updateDisplay();
    this.updateStats();
    this.updateFilterTags();
  }

  sortCampaigns(campaigns) {
    campaigns.sort((a, b) => {
      let comparison = 0;

      switch (this.currentFilters.sortBy) {
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
        case 'created':
          comparison = a.created - b.created;
          break;
        case 'lastPlayed':
        default:
          comparison = a.lastPlayed - b.lastPlayed;
          break;
      }

      return this.currentFilters.sortOrder === 'desc'
        ? -comparison
        : comparison;
    });

    return campaigns;
  }

  updateDisplay() {
    const campaignList = document.getElementById('campaign-list');
    if (!campaignList) return;

    // Hide all campaigns first
    this.campaigns.forEach((campaign) => {
      campaign.element.style.display = 'none';
    });

    // Show filtered campaigns in order
    this.filteredCampaigns.forEach((campaign, index) => {
      campaign.element.style.display = 'block';
      campaign.element.style.order = index;

      // Add modern styling if in modern mode
      if (this.isEnabled) {
        campaign.element.classList.add('campaign-item');
      }
    });

    // Show "no results" message if needed
    this.showNoResultsMessage();
  }

  showNoResultsMessage() {
    const campaignList = document.getElementById('campaign-list');
    let noResultsMessage = document.getElementById('no-results-message');

    if (this.filteredCampaigns.length === 0) {
      if (!noResultsMessage) {
        noResultsMessage = document.createElement('div');
        noResultsMessage.id = 'no-results-message';
        noResultsMessage.className = 'text-center py-5 text-muted';
        noResultsMessage.innerHTML = `
          <i class="fas fa-search fa-3x mb-3 opacity-50"></i>
          <h5>No campaigns found</h5>
          <p>Try adjusting your search or filters</p>
        `;
        campaignList.appendChild(noResultsMessage);
      }
      noResultsMessage.style.display = 'block';
    } else if (noResultsMessage) {
      noResultsMessage.style.display = 'none';
    }
  }

  updateStats() {
    const resultsCount = document.getElementById('results-count');
    const totalCount = document.getElementById('total-count');

    if (resultsCount) resultsCount.textContent = this.filteredCampaigns.length;
    if (totalCount) totalCount.textContent = this.campaigns.length;
  }

  updateFilterTags() {
    const activeFilters = document.getElementById('active-filters');
    if (!activeFilters) return;

    const tags = [];

    // Search tag
    if (this.currentFilters.search) {
      tags.push({
        label: `Search: "${this.currentFilters.search}"`,
        key: 'search',
      });
    }

    // Render tags
    activeFilters.innerHTML = tags
      .map(
        (tag) => `
      <span class="filter-tag">
        ${tag.label}
        <span class="remove-tag" data-filter-key="${tag.key}">×</span>
      </span>
    `,
      )
      .join('');

    // Add click handlers for tag removal
    activeFilters.querySelectorAll('.remove-tag').forEach((removeBtn) => {
      removeBtn.addEventListener('click', (e) => {
        const filterKey = e.target.dataset.filterKey;
        this.removeFilter(filterKey);
      });
    });
  }

  removeFilter(filterKey) {
    switch (filterKey) {
      case 'search':
        this.currentFilters.search = '';
        const searchInput = document.getElementById('campaign-search');
        if (searchInput) searchInput.value = '';
        break;
    }

    this.applyFilters();
  }

  clearAllFilters() {
    this.currentFilters = {
      search: '',
      sortBy: 'lastPlayed',
      sortOrder: 'desc',
      theme: '',
      status: '',
    };

    // Reset form controls
    const searchInput = document.getElementById('campaign-search');
    const sortBy = document.getElementById('sort-by');
    const sortOrder = document.getElementById('sort-order');
    const themeFilter = document.getElementById('theme-filter');
    const statusFilter = document.getElementById('status-filter');

    if (searchInput) searchInput.value = '';
    if (sortBy) sortBy.value = 'lastPlayed';
    if (sortOrder) sortOrder.value = 'desc';
    if (themeFilter) themeFilter.value = '';
    if (statusFilter) statusFilter.value = '';

    this.updateSortOrderLabel();
    this.applyFilters();
  }

  // Public API for external use
  search(query) {
    const searchInput = document.getElementById('campaign-search');
    if (searchInput) {
      searchInput.value = query;
      this.currentFilters.search = query.toLowerCase().trim();
      this.applyFilters();
    }
  }

  setFilter(filterType, value) {
    if (this.currentFilters.hasOwnProperty(filterType)) {
      this.currentFilters[filterType] = value;

      // Update corresponding form control
      const element = document.getElementById(
        filterType.replace(/([A-Z])/g, '-$1').toLowerCase(),
      );
      if (element) {
        element.value = value;
      }

      this.applyFilters();
    }
  }

  getResults() {
    return this.filteredCampaigns;
  }

  getTotalCount() {
    return this.campaigns.length;
  }

  getFilteredCount() {
    return this.filteredCampaigns.length;
  }
}

// Initialize enhanced search when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.enhancedSearch = new EnhancedSearch();
});

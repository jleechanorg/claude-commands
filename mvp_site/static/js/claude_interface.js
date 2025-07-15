/**
 * Claude Interface - Header Compliance Tracking
 * Manages header compliance monitoring and UI indicators for Claude interactions
 */

class ClaudeInterface {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.complianceRate = 1.0;
        this.totalResponses = 0;
        this.compliantResponses = 0;
        this.isInitialized = false;
        
        // Initialize UI components
        this.initializeUI();
        
        console.log('Claude Interface initialized with session:', this.sessionId);
    }
    
    /**
     * Generate a unique session ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Initialize UI components for compliance tracking
     */
    initializeUI() {
        // Create compliance indicator container
        this.createComplianceIndicator();
        
        // Set up periodic compliance checks
        this.setupPeriodicChecks();
        
        this.isInitialized = true;
    }
    
    /**
     * Create the compliance indicator UI element
     */
    createComplianceIndicator() {
        // Find the game view debug indicator area
        const debugIndicator = document.getElementById('debug-indicator');
        const gameViewHeader = document.querySelector('#game-view .d-flex.justify-content-between.align-items-center');
        
        if (!gameViewHeader) {
            console.warn('Game view header not found, creating compliance indicator in body');
            return;
        }
        
        // Create compliance indicator element
        const complianceDiv = document.createElement('div');
        complianceDiv.id = 'compliance-indicator';
        complianceDiv.className = 'compliance-indicator';
        complianceDiv.style.cssText = `
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        `;
        
        // Add to the header controls area
        const controlsDiv = gameViewHeader.querySelector('.d-flex.align-items-center.gap-2');
        if (controlsDiv && debugIndicator) {
            controlsDiv.insertBefore(complianceDiv, debugIndicator);
        }
        
        // Set initial state
        this.updateComplianceDisplay();
        
        // Add click handler for detailed view
        complianceDiv.addEventListener('click', () => this.showComplianceDetails());
    }
    
    /**
     * Update the compliance indicator display
     */
    updateComplianceDisplay() {
        const indicator = document.getElementById('compliance-indicator');
        if (!indicator) return;
        
        const percentage = Math.round(this.complianceRate * 100);
        const isCompliant = this.complianceRate >= 0.8; // 80% threshold
        
        // Update content
        indicator.innerHTML = `
            <span class="compliance-icon">${isCompliant ? '✅' : '⚠️'}</span>
            <span class="compliance-text">Header: ${percentage}%</span>
            <span class="compliance-count">(${this.compliantResponses}/${this.totalResponses})</span>
        `;
        
        // Update styling based on compliance
        if (isCompliant) {
            indicator.className = 'compliance-indicator compliant';
            indicator.style.backgroundColor = '#d4edda';
            indicator.style.color = '#155724';
            indicator.style.border = '1px solid #c3e6cb';
        } else {
            indicator.className = 'compliance-indicator non-compliant';
            indicator.style.backgroundColor = '#f8d7da';
            indicator.style.color = '#721c24';
            indicator.style.border = '1px solid #f5c6cb';
        }
        
        // Update hover effects
        indicator.addEventListener('mouseenter', () => {
            indicator.style.opacity = '0.8';
        });
        
        indicator.addEventListener('mouseleave', () => {
            indicator.style.opacity = '1';
        });
    }
    
    /**
     * Show detailed compliance information
     */
    showComplianceDetails() {
        const details = `
            <div class="compliance-details">
                <h6>Header Compliance Status</h6>
                <p><strong>Session ID:</strong> ${this.sessionId}</p>
                <p><strong>Compliance Rate:</strong> ${(this.complianceRate * 100).toFixed(1)}%</p>
                <p><strong>Total Responses:</strong> ${this.totalResponses}</p>
                <p><strong>Compliant Responses:</strong> ${this.compliantResponses}</p>
                <p><strong>Threshold:</strong> 80%</p>
                <hr>
                <small>Click outside to close</small>
            </div>
        `;
        
        // Create modal or tooltip
        this.showModal('Compliance Details', details);
    }
    
    /**
     * Process a Claude response and update compliance
     */
    processResponse(responseText) {
        if (!responseText || typeof responseText !== 'string') {
            console.warn('Invalid response text provided to processResponse');
            return;
        }
        
        // Validate header compliance
        const hasHeader = this.validateHeaderCompliance(responseText);
        
        // Update local statistics
        this.totalResponses++;
        if (hasHeader) {
            this.compliantResponses++;
        }
        
        // Calculate new compliance rate
        this.complianceRate = this.compliantResponses / this.totalResponses;
        
        // Update UI
        this.updateComplianceDisplay();
        
        // Show alert if compliance is low
        if (this.complianceRate < 0.8) {
            this.showComplianceAlert();
        }
        
        // Send to backend for tracking
        this.trackComplianceBackend(responseText, hasHeader);
        
        console.log(`Response processed: hasHeader=${hasHeader}, compliance=${(this.complianceRate * 100).toFixed(1)}%`);
        
        return {
            hasHeader,
            complianceRate: this.complianceRate,
            totalResponses: this.totalResponses,
            compliantResponses: this.compliantResponses
        };
    }
    
    /**
     * Validate if response contains proper header
     */
    validateHeaderCompliance(responseText) {
        if (!responseText) return false;
        
        // Check for expected header pattern: [Local: <branch> | Remote: <upstream> | PR: <info>]
        const headerPattern = /^\[Local: .+ \| Remote: .+ \| PR: .+\]/;
        return headerPattern.test(responseText.trim());
    }
    
    /**
     * Show compliance alert to user
     */
    showComplianceAlert() {
        const percentage = Math.round(this.complianceRate * 100);
        const message = `Header compliance is at ${percentage}%. Minimum required: 80%`;
        
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning alert-dismissible fade show';
        alertDiv.innerHTML = `
            <strong>Compliance Alert:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to top of game view
        const gameView = document.getElementById('game-view');
        if (gameView) {
            gameView.insertBefore(alertDiv, gameView.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }
    
    /**
     * Track compliance in backend
     */
    async trackComplianceBackend(responseText, hasHeader) {
        try {
            const response = await fetch('/api/track-compliance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    response_text: responseText,
                    has_header: hasHeader
                })
            });
            
            if (!response.ok) {
                console.warn('Failed to track compliance in backend:', response.status);
            }
        } catch (error) {
            console.error('Error tracking compliance:', error);
        }
    }
    
    /**
     * Set up periodic compliance checks
     */
    setupPeriodicChecks() {
        // Check compliance every 30 seconds
        setInterval(() => {
            this.fetchComplianceStatus();
        }, 30000);
    }
    
    /**
     * Fetch compliance status from backend
     */
    async fetchComplianceStatus() {
        try {
            const response = await fetch(`/api/compliance-status/${this.sessionId}`);
            if (response.ok) {
                const data = await response.json();
                
                // Update local state with server data
                this.complianceRate = data.compliance_rate || 0;
                this.totalResponses = data.total_responses || 0;
                this.compliantResponses = data.compliant_responses || 0;
                
                // Update UI
                this.updateComplianceDisplay();
            }
        } catch (error) {
            console.error('Error fetching compliance status:', error);
        }
    }
    
    /**
     * Show modal dialog
     */
    showModal(title, content) {
        // Create modal backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        backdrop.style.zIndex = '1050';
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'modal fade show';
        modal.style.display = 'block';
        modal.style.zIndex = '1055';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${content}
                    </div>
                </div>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(backdrop);
        document.body.appendChild(modal);
        
        // Close handlers
        const closeModal = () => {
            backdrop.remove();
            modal.remove();
        };
        
        backdrop.addEventListener('click', closeModal);
        modal.querySelector('.btn-close').addEventListener('click', closeModal);
        
        // ESC key handler
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    }
    
    /**
     * Reset compliance tracking for new session
     */
    resetSession() {
        this.sessionId = this.generateSessionId();
        this.complianceRate = 1.0;
        this.totalResponses = 0;
        this.compliantResponses = 0;
        
        this.updateComplianceDisplay();
        
        console.log('Claude Interface session reset:', this.sessionId);
    }
    
    /**
     * Get current compliance statistics
     */
    getComplianceStats() {
        return {
            sessionId: this.sessionId,
            complianceRate: this.complianceRate,
            totalResponses: this.totalResponses,
            compliantResponses: this.compliantResponses,
            isCompliant: this.complianceRate >= 0.8
        };
    }
}

// Global instance
let claudeInterface = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize in game view
    if (document.getElementById('game-view')) {
        claudeInterface = new ClaudeInterface();
        
        // Make globally accessible
        window.claudeInterface = claudeInterface;
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClaudeInterface;
}
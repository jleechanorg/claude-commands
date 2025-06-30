/**
 * Visual Validator - Browser-based UI Testing
 * Run this in the browser console to check for common UI issues
 */

const VisualValidator = {
    // Configuration
    config: {
        highlightColor: 'red',
        highlightWidth: '3px',
        consoleStyles: 'color: #007bff; font-weight: bold;'
    },
    
    // Test results storage
    results: {
        passed: [],
        failed: [],
        warnings: []
    },
    
    // Core validation checks
    checks: {
        /**
         * Check for overlapping elements
         */
        overlappingElements: function() {
            console.log('%c🔍 Checking for overlapping elements...', VisualValidator.config.consoleStyles);
            
            const elements = document.querySelectorAll('.btn, .dropdown-menu, .modal');
            const overlaps = [];
            
            for (let i = 0; i < elements.length; i++) {
                const rect1 = elements[i].getBoundingClientRect();
                if (rect1.width === 0 || rect1.height === 0) continue;
                
                for (let j = i + 1; j < elements.length; j++) {
                    const rect2 = elements[j].getBoundingClientRect();
                    if (rect2.width === 0 || rect2.height === 0) continue;
                    
                    // Check if elements overlap
                    if (!(rect1.right < rect2.left || 
                          rect1.left > rect2.right || 
                          rect1.bottom < rect2.top || 
                          rect1.top > rect2.bottom)) {
                        
                        // Exclude parent-child relationships
                        if (!elements[i].contains(elements[j]) && !elements[j].contains(elements[i])) {
                            overlaps.push({
                                element1: elements[i],
                                element2: elements[j],
                                description: `${elements[i].className} overlaps with ${elements[j].className}`
                            });
                        }
                    }
                }
            }
            
            if (overlaps.length > 0) {
                overlaps.forEach(o => {
                    VisualValidator.highlightElement(o.element1, 'red');
                    VisualValidator.highlightElement(o.element2, 'red');
                });
                VisualValidator.results.failed.push({
                    test: 'Overlapping Elements',
                    count: overlaps.length,
                    details: overlaps
                });
                console.error(`❌ Found ${overlaps.length} overlapping elements`);
            } else {
                VisualValidator.results.passed.push('No overlapping elements');
                console.log('✅ No overlapping elements found');
            }
            
            return overlaps.length === 0;
        },
        
        /**
         * Check text readability
         */
        textReadability: function() {
            console.log('%c🔍 Checking text readability...', VisualValidator.config.consoleStyles);
            
            const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6, a, button, label');
            const issues = [];
            
            textElements.forEach(el => {
                const styles = window.getComputedStyle(el);
                const opacity = parseFloat(styles.opacity);
                const color = styles.color;
                const bgColor = styles.backgroundColor;
                
                // Check for invisible text
                if (opacity === 0 && el.textContent.trim()) {
                    issues.push({
                        element: el,
                        issue: 'Text has opacity 0',
                        text: el.textContent.substring(0, 50)
                    });
                }
                
                // Check for transparent text
                if (color === 'transparent' && el.textContent.trim()) {
                    issues.push({
                        element: el,
                        issue: 'Text color is transparent',
                        text: el.textContent.substring(0, 50)
                    });
                }
                
                // Check contrast ratio (simplified)
                if (color && bgColor && color !== 'transparent') {
                    const contrast = VisualValidator.getContrastRatio(color, bgColor);
                    if (contrast < 4.5 && el.textContent.trim()) {
                        issues.push({
                            element: el,
                            issue: `Low contrast ratio: ${contrast.toFixed(2)}`,
                            text: el.textContent.substring(0, 50)
                        });
                    }
                }
            });
            
            if (issues.length > 0) {
                issues.forEach(i => VisualValidator.highlightElement(i.element, 'orange'));
                VisualValidator.results.failed.push({
                    test: 'Text Readability',
                    count: issues.length,
                    details: issues
                });
                console.error(`❌ Found ${issues.length} text readability issues`);
            } else {
                VisualValidator.results.passed.push('All text is readable');
                console.log('✅ All text is readable');
            }
            
            return issues.length === 0;
        },
        
        /**
         * Check checkbox alignment
         */
        checkboxAlignment: function() {
            console.log('%c🔍 Checking checkbox alignment...', VisualValidator.config.consoleStyles);
            
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            const misaligned = [];
            
            checkboxes.forEach(checkbox => {
                const label = checkbox.nextElementSibling || 
                             checkbox.parentElement.querySelector('label') ||
                             checkbox.closest('label');
                
                if (label) {
                    const checkboxRect = checkbox.getBoundingClientRect();
                    const labelRect = label.getBoundingClientRect();
                    
                    // Check vertical alignment
                    const verticalDiff = Math.abs(checkboxRect.top - labelRect.top);
                    if (verticalDiff > 5) {
                        misaligned.push({
                            checkbox: checkbox,
                            label: label,
                            verticalDiff: verticalDiff,
                            issue: `Checkbox misaligned by ${verticalDiff}px`
                        });
                    }
                }
            });
            
            if (misaligned.length > 0) {
                misaligned.forEach(m => {
                    VisualValidator.highlightElement(m.checkbox, 'yellow');
                    VisualValidator.highlightElement(m.label, 'yellow');
                });
                VisualValidator.results.failed.push({
                    test: 'Checkbox Alignment',
                    count: misaligned.length,
                    details: misaligned
                });
                console.error(`❌ Found ${misaligned.length} misaligned checkboxes`);
            } else {
                VisualValidator.results.passed.push('All checkboxes are aligned');
                console.log('✅ All checkboxes are properly aligned');
            }
            
            return misaligned.length === 0;
        },
        
        /**
         * Check modern mode is default
         */
        modernModeDefault: function() {
            console.log('%c🔍 Checking modern mode default...', VisualValidator.config.consoleStyles);
            
            const bodyClasses = document.body.className;
            const interfaceMode = document.body.getAttribute('data-interface-mode');
            
            if (interfaceMode === 'modern' || bodyClasses.includes('modern-mode')) {
                VisualValidator.results.passed.push('Modern mode is active');
                console.log('✅ Modern mode is default');
                return true;
            } else {
                VisualValidator.results.failed.push({
                    test: 'Modern Mode Default',
                    details: `Current mode: ${interfaceMode || 'classic'}`
                });
                console.error('❌ Modern mode is not default');
                return false;
            }
        },
        
        /**
         * Check if spinner shows when creating campaign
         */
        spinnerCheck: function() {
            console.log('%c🔍 Checking for campaign creation spinner...', VisualValidator.config.consoleStyles);
            
            // This check requires user interaction, so we'll check if the elements exist
            const launchBtn = document.querySelector('#launch-campaign');
            const spinnerContainer = document.querySelector('#campaign-creation-spinner');
            
            if (launchBtn) {
                console.log('✅ Launch campaign button found');
                if (spinnerContainer) {
                    console.log('✅ Spinner container exists (will show on click)');
                    VisualValidator.results.passed.push('Spinner implementation found');
                    return true;
                } else {
                    // Check if the function exists
                    if (window.campaignWizard && typeof window.campaignWizard.showDetailedSpinner === 'function') {
                        console.log('✅ Spinner function exists');
                        VisualValidator.results.passed.push('Spinner function implemented');
                        return true;
                    }
                }
            }
            
            VisualValidator.results.warnings.push({
                test: 'Spinner Check',
                message: 'Manual test required: Click "Begin Adventure" to verify spinner'
            });
            console.warn('⚠️  Manual verification needed for spinner');
            return null;
        }
    },
    
    // Utility functions
    highlightElement: function(element, color) {
        element.style.outline = `${this.config.highlightWidth} solid ${color}`;
        element.style.outlineOffset = '2px';
        
        // Auto-remove highlight after 5 seconds
        setTimeout(() => {
            element.style.outline = '';
            element.style.outlineOffset = '';
        }, 5000);
    },
    
    getContrastRatio: function(color1, color2) {
        // Simplified contrast calculation
        const rgb1 = this.getRGB(color1);
        const rgb2 = this.getRGB(color2);
        
        const l1 = this.getLuminance(rgb1);
        const l2 = this.getLuminance(rgb2);
        
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        
        return (lighter + 0.05) / (darker + 0.05);
    },
    
    getRGB: function(color) {
        const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (match) {
            return {
                r: parseInt(match[1]),
                g: parseInt(match[2]),
                b: parseInt(match[3])
            };
        }
        return { r: 0, g: 0, b: 0 };
    },
    
    getLuminance: function(rgb) {
        const { r, g, b } = rgb;
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    },
    
    // Main run function
    run: function() {
        console.clear();
        console.log('%c🎨 Visual Validator - UI Testing', 'font-size: 20px; color: #007bff; font-weight: bold;');
        console.log('%c' + '='.repeat(50), 'color: #ccc;');
        
        // Reset results
        this.results = { passed: [], failed: [], warnings: [] };
        
        // Run all checks
        const checkResults = [
            this.checks.modernModeDefault(),
            this.checks.overlappingElements(),
            this.checks.textReadability(),
            this.checks.checkboxAlignment(),
            this.checks.spinnerCheck()
        ];
        
        // Summary
        console.log('%c' + '='.repeat(50), 'color: #ccc;');
        console.log('%c📊 Test Summary', 'font-size: 16px; color: #007bff; font-weight: bold;');
        console.log(`✅ Passed: ${this.results.passed.length}`);
        console.log(`❌ Failed: ${this.results.failed.length}`);
        console.log(`⚠️  Warnings: ${this.results.warnings.length}`);
        
        // Detailed failures
        if (this.results.failed.length > 0) {
            console.log('\n%c❌ Failed Tests:', 'color: red; font-weight: bold;');
            this.results.failed.forEach(f => {
                console.error(f);
            });
        }
        
        // Warnings
        if (this.results.warnings.length > 0) {
            console.log('\n%c⚠️  Warnings:', 'color: orange; font-weight: bold;');
            this.results.warnings.forEach(w => {
                console.warn(w);
            });
        }
        
        // Instructions
        console.log('\n%c💡 Tips:', 'color: #666; font-weight: bold;');
        console.log('- Failed elements are highlighted on the page');
        console.log('- Highlights auto-remove after 5 seconds');
        console.log('- Run VisualValidator.captureState() to save current state');
        console.log('- Run specific checks: VisualValidator.checks.checkboxAlignment()');
        
        return this.results;
    },
    
    // Capture current state for comparison
    captureState: function() {
        const state = {
            timestamp: new Date().toISOString(),
            url: window.location.href,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            theme: document.body.getAttribute('data-theme') || 'default',
            mode: document.body.getAttribute('data-interface-mode') || 'classic',
            elements: {
                buttons: document.querySelectorAll('.btn').length,
                checkboxes: document.querySelectorAll('input[type="checkbox"]').length,
                modals: document.querySelectorAll('.modal').length,
                campaigns: document.querySelectorAll('.campaign-item').length
            }
        };
        
        console.log('%c📸 Current State Captured:', 'color: green; font-weight: bold;');
        console.table(state);
        
        // Save to localStorage
        localStorage.setItem('visualValidator_lastState', JSON.stringify(state));
        
        return state;
    }
};

// Auto-run on load
console.log('%c✨ Visual Validator loaded! Run VisualValidator.run() to start', 'color: #007bff; font-style: italic;'); 
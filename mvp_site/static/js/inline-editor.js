/**
 * Inline Editor Component
 * 
 * Provides inline editing functionality for campaign names with:
 * - Click-to-edit interface
 * - Save/cancel controls
 * - Keyboard shortcuts (Enter to save, Escape to cancel)
 * - Validation and error handling
 * - Smooth transitions and visual feedback
 */

class InlineEditor {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            maxLength: 100,
            minLength: 1,
            placeholder: 'Enter campaign name...',
            validateFn: null,
            saveFn: null,
            cancelFn: null,
            onStart: null,
            onComplete: null,
            onError: null,
            ...options
        };
        
        this.isEditing = false;
        this.originalValue = '';
        this.editContainer = null;
        this.input = null;
        this.saveBtn = null;
        this.cancelBtn = null;
        
        this.init();
    }
    
    init() {
        this.element.classList.add('inline-editable');
        this.element.addEventListener('click', this.startEdit.bind(this));
        
        // Add hover effect
        this.element.addEventListener('mouseenter', () => {
            if (!this.isEditing) {
                this.element.classList.add('inline-editable-hover');
            }
        });
        
        this.element.addEventListener('mouseleave', () => {
            this.element.classList.remove('inline-editable-hover');
        });
    }
    
    startEdit() {
        if (this.isEditing) return;
        
        this.isEditing = true;
        this.originalValue = this.element.textContent.trim();
        
        // Call onStart callback
        if (this.options.onStart) {
            this.options.onStart(this.originalValue);
        }
        
        // Create edit container
        this.createEditContainer();
        
        // Replace element content
        this.element.style.display = 'none';
        this.element.parentNode.insertBefore(this.editContainer, this.element.nextSibling);
        
        // Focus input and select text
        this.input.focus();
        this.input.select();
        
        // Add global click handler to cancel on outside click
        setTimeout(() => {
            document.addEventListener('click', this.handleOutsideClick.bind(this));
        }, 0);
    }
    
    createEditContainer() {
        this.editContainer = document.createElement('div');
        this.editContainer.className = 'inline-edit-container';
        
        // Create input
        this.input = document.createElement('input');
        this.input.type = 'text';
        this.input.className = 'inline-edit-input';
        this.input.value = this.originalValue;
        this.input.placeholder = this.options.placeholder;
        this.input.maxLength = this.options.maxLength;
        
        // Create button container
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'inline-edit-buttons';
        
        // Create save button
        this.saveBtn = document.createElement('button');
        this.saveBtn.className = 'btn btn-sm btn-success inline-edit-save';
        this.saveBtn.innerHTML = '✓';
        this.saveBtn.title = 'Save (Enter)';
        
        // Create cancel button
        this.cancelBtn = document.createElement('button');
        this.cancelBtn.className = 'btn btn-sm btn-secondary inline-edit-cancel';
        this.cancelBtn.innerHTML = '✕';
        this.cancelBtn.title = 'Cancel (Escape)';
        
        // Add buttons to container
        buttonContainer.appendChild(this.saveBtn);
        buttonContainer.appendChild(this.cancelBtn);
        
        // Add elements to edit container
        this.editContainer.appendChild(this.input);
        this.editContainer.appendChild(buttonContainer);
        
        // Event listeners
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.saveBtn.addEventListener('click', this.save.bind(this));
        this.cancelBtn.addEventListener('click', this.cancel.bind(this));
    }
    
    handleKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            this.save();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            this.cancel();
        }
    }
    
    handleInput() {
        // Remove error state on input
        this.input.classList.remove('is-invalid');
        this.removeError();
        
        // Validate length
        const value = this.input.value.trim();
        if (value.length < this.options.minLength || value.length > this.options.maxLength) {
            this.saveBtn.disabled = true;
        } else {
            this.saveBtn.disabled = false;
        }
    }
    
    handleOutsideClick(e) {
        if (this.editContainer && !this.editContainer.contains(e.target)) {
            this.cancel();
        }
    }
    
    async save() {
        const value = this.input.value.trim();
        
        // Validate
        const error = this.validate(value);
        if (error) {
            this.showError(error);
            return;
        }
        
        // If no change, just cancel
        if (value === this.originalValue) {
            this.cancel();
            return;
        }
        
        // Show loading state
        this.setLoading(true);
        
        try {
            // Call save function
            if (this.options.saveFn) {
                await this.options.saveFn(value);
            }
            
            // Update element text
            this.element.textContent = value;
            
            // Complete edit
            this.completeEdit(true);
            
        } catch (error) {
            console.error('Failed to save:', error);
            this.showError('Failed to save. Please try again.');
            this.setLoading(false);
            
            if (this.options.onError) {
                this.options.onError(error);
            }
        }
    }
    
    cancel() {
        this.completeEdit(false);
        
        if (this.options.cancelFn) {
            this.options.cancelFn();
        }
    }
    
    completeEdit(saved) {
        // Remove global click handler
        document.removeEventListener('click', this.handleOutsideClick.bind(this));
        
        // Remove edit container
        if (this.editContainer && this.editContainer.parentNode) {
            this.editContainer.parentNode.removeChild(this.editContainer);
        }
        
        // Show original element
        this.element.style.display = '';
        
        // Reset state
        this.isEditing = false;
        this.editContainer = null;
        this.input = null;
        this.saveBtn = null;
        this.cancelBtn = null;
        
        // Call complete callback
        if (this.options.onComplete) {
            this.options.onComplete(saved);
        }
    }
    
    validate(value) {
        if (value.length < this.options.minLength) {
            return `Minimum length is ${this.options.minLength} characters`;
        }
        
        if (value.length > this.options.maxLength) {
            return `Maximum length is ${this.options.maxLength} characters`;
        }
        
        if (this.options.validateFn) {
            return this.options.validateFn(value);
        }
        
        return null;
    }
    
    showError(message) {
        this.input.classList.add('is-invalid');
        
        // Remove existing error
        this.removeError();
        
        // Create error element
        const error = document.createElement('div');
        error.className = 'inline-edit-error';
        error.textContent = message;
        
        this.editContainer.appendChild(error);
    }
    
    removeError() {
        const error = this.editContainer.querySelector('.inline-edit-error');
        if (error) {
            error.remove();
        }
    }
    
    setLoading(loading) {
        if (loading) {
            this.saveBtn.disabled = true;
            this.cancelBtn.disabled = true;
            this.input.disabled = true;
            this.saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        } else {
            this.saveBtn.disabled = false;
            this.cancelBtn.disabled = false;
            this.input.disabled = false;
            this.saveBtn.innerHTML = '✓';
        }
    }
    
    destroy() {
        this.element.classList.remove('inline-editable');
        this.element.removeEventListener('click', this.startEdit.bind(this));
        
        if (this.isEditing) {
            this.cancel();
        }
    }
}

// Export for use
window.InlineEditor = InlineEditor;
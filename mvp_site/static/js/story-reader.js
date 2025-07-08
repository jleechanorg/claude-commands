/**
 * Story Reader Component - Background Story Reading with Pause/Continue
 * Provides controlled reading experience for campaign background stories
 */

class StoryReader {
    constructor() {
        this.isReading = false;
        this.isPaused = false;
        this.currentChunk = 0;
        this.chunks = [];
        this.currentText = '';
        this.readingSpeed = 50; // Words per minute
        this.timePerWord = 60000 / this.readingSpeed; // milliseconds per word
        this.chunkTimeout = null;
        this.wordTimeout = null;
        this.currentWordIndex = 0;
        this.onComplete = null;
        this.onProgress = null;
        this.userPreferences = {
            readingSpeed: 50,
            autoAdvance: true,
            showProgress: true,
            enableSounds: false
        };
        
        this.init();
    }

    init() {
        this.loadUserPreferences();
        this.setupEventListeners();
        console.log('📖 Story Reader initialized');
    }

    loadUserPreferences() {
        const saved = localStorage.getItem('storyReaderPreferences');
        if (saved) {
            this.userPreferences = { ...this.userPreferences, ...JSON.parse(saved) };
            this.readingSpeed = this.userPreferences.readingSpeed;
            this.timePerWord = 60000 / this.readingSpeed;
        }
    }

    saveUserPreferences() {
        localStorage.setItem('storyReaderPreferences', JSON.stringify(this.userPreferences));
    }

    setupEventListeners() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.isReading) {
                switch(e.key) {
                    case ' ':
                        e.preventDefault();
                        this.togglePause();
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        this.skipToNext();
                        break;
                    case 'ArrowLeft':
                        e.preventDefault();
                        this.skipToPrevious();
                        break;
                    case 'Escape':
                        e.preventDefault();
                        this.stop();
                        break;
                }
            }
        });
    }

    // Main method to start reading a story
    startReading(storyText, options = {}) {
        this.stop(); // Stop any existing reading
        
        this.onComplete = options.onComplete || null;
        this.onProgress = options.onProgress || null;
        
        // Prepare the story
        this.prepareStory(storyText);
        
        // Create the reader UI
        this.createReaderUI(options);
        
        // Start reading
        this.isReading = true;
        this.isPaused = false;
        this.currentChunk = 0;
        this.currentWordIndex = 0;
        
        this.readCurrentChunk();
        
        console.log('📖 Started reading story with', this.chunks.length, 'chunks');
    }

    prepareStory(storyText) {
        // Split story into natural chunks (paragraphs, sentences, etc.)
        this.chunks = storyText.split('\n\n').filter(chunk => chunk.trim());
        if (this.chunks.length === 0) {
            this.chunks = [storyText];
        }
    }

    createReaderUI(options) {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'story-reader-overlay';
        overlay.id = 'story-reader-overlay';

        // Create modal
        const modal = document.createElement('div');
        modal.className = 'story-reader-modal';

        // Header
        const header = document.createElement('div');
        header.className = 'story-reader-header';
        header.innerHTML = `
            <h2 class="story-reader-title">${options.title || 'Story Background'}</h2>
            <button class="story-reader-close" onclick="storyReader.stop()">
                <span aria-hidden="true">&times;</span>
            </button>
        `;

        // Content area
        const content = document.createElement('div');
        content.className = 'story-reader-content';
        content.innerHTML = `
            <div class="story-text-container" id="story-text-container">
                <p class="story-text" id="story-text"></p>
            </div>
            <div class="story-progress" id="story-progress">
                <div class="progress">
                    <div class="progress-bar" id="story-progress-bar" style="width: 0%"></div>
                </div>
                <span class="progress-text" id="story-progress-text">Chapter 1 of ${this.chunks.length}</span>
            </div>
        `;

        // Controls
        const controls = document.createElement('div');
        controls.className = 'story-reader-controls';
        controls.innerHTML = `
            <div class="control-group">
                <button class="btn btn-secondary btn-sm" onclick="storyReader.skipToPrevious()">
                    <i class="bi bi-skip-backward"></i> Previous
                </button>
                <button class="btn btn-primary" id="pause-button" onclick="storyReader.togglePause()">
                    <i class="bi bi-pause"></i> Pause
                </button>
                <button class="btn btn-secondary btn-sm" onclick="storyReader.skipToNext()">
                    Next <i class="bi bi-skip-forward"></i>
                </button>
            </div>
            <div class="speed-control">
                <label for="reading-speed">Speed:</label>
                <input type="range" id="reading-speed" min="25" max="200" value="${this.readingSpeed}"
                       onchange="storyReader.updateSpeed(this.value)">
                <span id="speed-value">${this.readingSpeed} WPM</span>
            </div>
        `;

        // Assemble modal
        modal.appendChild(header);
        modal.appendChild(content);
        modal.appendChild(controls);
        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Prevent clicks on modal from closing
        modal.addEventListener('click', (e) => e.stopPropagation());
        
        // Close on overlay click
        overlay.addEventListener('click', () => this.stop());
    }

    readCurrentChunk() {
        if (!this.isReading || this.currentChunk >= this.chunks.length) {
            this.complete();
            return;
        }

        this.currentText = this.chunks[this.currentChunk];
        const words = this.currentText.split(' ');
        this.currentWordIndex = 0;

        // Update progress
        this.updateProgress();

        // Display initial text
        const textElement = document.getElementById('story-text');
        if (textElement) {
            textElement.innerHTML = this.highlightWords(words, -1);
        }

        // Start word-by-word highlighting
        this.readNextWord(words);
    }

    readNextWord(words) {
        if (!this.isReading || this.isPaused) return;

        if (this.currentWordIndex >= words.length) {
            // Finished current chunk
            this.chunkTimeout = setTimeout(() => {
                this.currentChunk++;
                this.readCurrentChunk();
            }, 1000); // Pause between chunks
            return;
        }

        // Update display
        const textElement = document.getElementById('story-text');
        if (textElement) {
            textElement.innerHTML = this.highlightWords(words, this.currentWordIndex);
            
            // Scroll to keep current word visible
            const highlightedWord = textElement.querySelector('.current-word');
            if (highlightedWord) {
                highlightedWord.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }

        this.currentWordIndex++;
        
        // Schedule next word
        this.wordTimeout = setTimeout(() => {
            this.readNextWord(words);
        }, this.timePerWord);
    }

    highlightWords(words, currentIndex) {
        return words.map((word, index) => {
            if (index === currentIndex) {
                return `<span class="current-word">${word}</span>`;
            } else if (index < currentIndex) {
                return `<span class="read-word">${word}</span>`;
            } else {
                return `<span class="unread-word">${word}</span>`;
            }
        }).join(' ');
    }

    togglePause() {
        if (!this.isReading) return;

        this.isPaused = !this.isPaused;
        const pauseButton = document.getElementById('pause-button');
        
        if (this.isPaused) {
            if (pauseButton) {
                pauseButton.innerHTML = '<i class="bi bi-play"></i> Resume';
            }
            // Clear timeouts
            clearTimeout(this.wordTimeout);
            clearTimeout(this.chunkTimeout);
        } else {
            if (pauseButton) {
                pauseButton.innerHTML = '<i class="bi bi-pause"></i> Pause';
            }
            // Resume reading
            const words = this.currentText.split(' ');
            this.readNextWord(words);
        }
    }

    skipToNext() {
        if (!this.isReading) return;
        
        clearTimeout(this.wordTimeout);
        clearTimeout(this.chunkTimeout);
        
        this.currentChunk++;
        if (this.currentChunk >= this.chunks.length) {
            this.complete();
        } else {
            this.readCurrentChunk();
        }
    }

    skipToPrevious() {
        if (!this.isReading) return;
        
        clearTimeout(this.wordTimeout);
        clearTimeout(this.chunkTimeout);
        
        this.currentChunk = Math.max(0, this.currentChunk - 1);
        this.readCurrentChunk();
    }

    updateSpeed(newSpeed) {
        this.readingSpeed = parseInt(newSpeed);
        this.timePerWord = 60000 / this.readingSpeed;
        this.userPreferences.readingSpeed = this.readingSpeed;
        this.saveUserPreferences();
        
        const speedValue = document.getElementById('speed-value');
        if (speedValue) {
            speedValue.textContent = `${this.readingSpeed} WPM`;
        }
    }

    updateProgress() {
        const progressBar = document.getElementById('story-progress-bar');
        const progressText = document.getElementById('story-progress-text');
        
        if (progressBar && progressText) {
            const progress = ((this.currentChunk + 1) / this.chunks.length) * 100;
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `Chapter ${this.currentChunk + 1} of ${this.chunks.length}`;
        }

        if (this.onProgress) {
            this.onProgress(this.currentChunk + 1, this.chunks.length);
        }
    }

    stop() {
        this.isReading = false;
        this.isPaused = false;
        
        clearTimeout(this.wordTimeout);
        clearTimeout(this.chunkTimeout);
        
        const overlay = document.getElementById('story-reader-overlay');
        if (overlay) {
            overlay.remove();
        }
        
        console.log('📖 Story Reader stopped');
    }

    complete() {
        console.log('📖 Story reading completed');
        
        if (this.onComplete) {
            this.onComplete();
        }
        
        this.stop();
    }
}

// Create global instance
const storyReader = new StoryReader();

// Export to window for global access
window.storyReader = storyReader;
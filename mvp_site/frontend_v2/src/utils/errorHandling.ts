/**
 * Error handling utilities for Frontend v2
 */

export interface AppError {
  message: string;
  code?: string;
  details?: any;
  originalError?: any;
  retryCount?: number;
  isRetryable?: boolean;
}

export interface LoadingState {
  isLoading: boolean;
  progress?: number;
  status?: string;
  canCancel?: boolean;
}

export interface RetryOptions {
  maxRetries?: number;
  retryDelay?: number;
  exponentialBackoff?: boolean;
  shouldRetry?: (error: any, retryCount: number) => boolean;
}

/**
 * Formats error messages for user display with enhanced context and user-friendly language
 */
export function formatErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const message = error.message.toLowerCase();

    // Handle specific error types with user-friendly messages
    if (message.includes('timeout') || message.includes('timed out')) {
      return '⏱️ The request took too long to complete. Please check your connection and try again.';
    }

    if (message.includes('network') || message.includes('fetch') || message.includes('failed to fetch')) {
      const isOffline = !navigator.onLine;
      return isOffline
        ? '🌐 You appear to be offline. Please check your internet connection and try again.'
        : '🌐 Network error occurred. Please check your internet connection and try again.';
    }

    if (message.includes('authentication') || message.includes('401') || message.includes('unauthorized')) {
      return '🔒 Authentication expired. Please refresh the page and sign in again.';
    }

    if (message.includes('server') || message.includes('500') || message.includes('internal server error')) {
      return '🛠️ Server error occurred. Our team has been notified. Please try again in a few minutes.';
    }

    if (message.includes('validation') || message.includes('invalid')) {
      return `⚠️ Input validation error: ${sanitizeForDisplay(error.message)}`;
    }

    if (message.includes('not found') || message.includes('404')) {
      return '🔍 The requested resource was not found. It may have been deleted or moved.';
    }

    if (message.includes('rate limit') || message.includes('429')) {
      return '🚀 Too many requests. Please wait a moment and try again.';
    }

    if (message.includes('forbidden') || message.includes('403')) {
      return '🚫 You don\'t have permission to perform this action.';
    }

    if (message.includes('cors')) {
      return '🔒 Security error occurred. Please contact support if this persists.';
    }

    if (message.includes('campaign') && message.includes('create')) {
      const sanitizedMsg = sanitizeForDisplay(error.message);
      return `🏰 Campaign creation failed: ${sanitizedMsg.replace(/^./, str => str.toUpperCase())}`;
    }

    // Return original message with better formatting
    return error.message.charAt(0).toUpperCase() + error.message.slice(1);
  }

  if (typeof error === 'string') {
    return error.charAt(0).toUpperCase() + error.slice(1);
  }

  if (error && typeof error === 'object' && 'message' in error) {
    const message = String(error.message);
    return message.charAt(0).toUpperCase() + message.slice(1);
  }

  return '⚠️ An unexpected error occurred. Please try again or contact support if the issue persists.';
}

/**
 * Sanitizes user input to prevent XSS attacks
 * Removes HTML tags and dangerous characters while preserving readability
 * CRITICAL: This function prevents XSS vulnerabilities in error messages
 */
function sanitizeForDisplay(input: string | null | undefined): string {
  if (!input || typeof input !== 'string') {
    return 'Invalid input';
  }
  
  // Remove HTML tags completely to prevent any script injection
  let sanitized = input.replace(/<[^>]*>/g, '');
  
  // Decode common HTML entities safely
  sanitized = sanitized
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#x2F;/g, '/')
    .replace(/&#x60;/g, '`');
  
  // Remove any remaining potentially dangerous characters
  sanitized = sanitized
    .replace(/[<>"'`]/g, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '');
  
  // Limit length to prevent abuse
  const maxLength = 500;
  if (sanitized.length > maxLength) {
    sanitized = sanitized.substring(0, maxLength) + '...';
  }
  
  return sanitized.trim() || 'Error message unavailable';
}

/**
 * Shows error toast notification with better UX, offline detection, and enhanced styling
 */
export function showErrorToast(message: string, options?: { persistent?: boolean, actionable?: boolean, context?: string }): void {
  // Enhanced error display with network status detection
  const isOffline = !navigator.onLine;
  const contextPrefix = options?.context ? `[${options.context}] ` : '';
  const finalMessage = isOffline ? `🌐 Offline: ${message}` : `${contextPrefix}${message}`;

  if (options?.persistent) {
    // For critical errors that need user attention with enhanced dialog
    const confirmMessage = `❌ Error Occurred\n\n${finalMessage}\n\nWould you like to retry this operation?`;
    if (confirm(confirmMessage)) {
      // User wants to retry - trigger a custom event with context
      window.dispatchEvent(new CustomEvent('error-toast-retry', {
        detail: {
          message,
          context: options.context,
          timestamp: Date.now()
        }
      }));
    }
  } else {
    // Enhanced console logging with context
    const timestamp = new Date().toISOString();
    console.error(`❌ [${timestamp}] ${finalMessage}`);

    // Create enhanced visual notification
    if (typeof window !== 'undefined') {
      const notification = document.createElement('div');

      // Enhanced color scheme based on error type
      let bgColor = '#dc2626'; // Default red
      let iconColor = 'white';

      if (isOffline) {
        bgColor = '#f59e0b'; // Orange for offline
      } else if (message.toLowerCase().includes('authentication')) {
        bgColor = '#7c3aed'; // Purple for auth errors
      } else if (message.toLowerCase().includes('validation')) {
        bgColor = '#ea580c'; // Orange for validation errors
      } else if (message.toLowerCase().includes('server')) {
        bgColor = '#dc2626'; // Red for server errors
      }

      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15), 0 4px 8px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        max-width: 450px;
        min-width: 300px;
        font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
        font-size: 14px;
        line-height: 1.4;
        border-left: 4px solid rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(12px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        transform: translateX(100%);
        opacity: 0;
        word-wrap: break-word;
      `;

      // Add retry button for actionable errors with enhanced styling (XSS-safe)
      if (options?.actionable) {
        const container = document.createElement('div');
        
        // Create message div safely using textContent
        const messageDiv = document.createElement('div');
        messageDiv.textContent = sanitizeForDisplay(finalMessage);
        messageDiv.style.cssText = 'margin-bottom: 12px; font-weight: 500;';
        
        // Create retry button safely without innerHTML
        const retryButton = document.createElement('button');
        retryButton.textContent = '🔄 Retry Operation';
        retryButton.style.cssText = `
          background: rgba(255, 255, 255, 0.2);
          border: 1px solid rgba(255, 255, 255, 0.4);
          color: white;
          padding: 6px 12px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
          font-weight: 500;
          transition: all 0.2s ease;
        `;
        
        // Safe event handlers without inline JavaScript
        retryButton.addEventListener('mouseover', () => {
          retryButton.style.background = 'rgba(255,255,255,0.3)';
        });
        retryButton.addEventListener('mouseout', () => {
          retryButton.style.background = 'rgba(255,255,255,0.2)';
        });
        retryButton.addEventListener('click', () => {
          notification.remove();
          window.dispatchEvent(new CustomEvent('error-toast-retry', { 
            detail: { 
              message: sanitizeForDisplay(message), 
              context: sanitizeForDisplay(options.context || ''), 
              timestamp: Date.now() 
            } 
          }));
        });
        
        container.appendChild(messageDiv);
        container.appendChild(retryButton);
        notification.appendChild(container);
      } else {
        // Add close button for non-actionable errors
        const container = document.createElement('div');
        container.style.cssText = 'display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;';

        const messageDiv = document.createElement('div');
        messageDiv.textContent = sanitizeForDisplay(finalMessage);
        messageDiv.style.cssText = 'flex: 1; font-weight: 500;';

        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.onclick = () => notification.remove();
        closeButton.style.cssText = `
          background: none;
          border: none;
          color: white;
          font-size: 18px;
          cursor: pointer;
          padding: 0;
          margin: -4px 0 0 0;
          opacity: 0.7;
          transition: opacity 0.2s ease;
        `;
        closeButton.onmouseover = () => closeButton.style.opacity = '1';
        closeButton.onmouseout = () => closeButton.style.opacity = '0.7';

        container.appendChild(messageDiv);
        container.appendChild(closeButton);
        notification.appendChild(container);
      }

      document.body.appendChild(notification);

      // Enhanced animation sequence
      setTimeout(() => {
        notification.style.transform = 'translateX(0)';
        notification.style.opacity = '1';
      }, 50);

      // Auto-dismiss with longer duration for actionable errors
      const duration = options?.persistent ? 15000 : (options?.actionable ? 8000 : 6000);
      const dismissTimeout = setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        setTimeout(() => {
          if (notification.parentNode) {
            notification.remove();
          }
        }, 400);
      }, duration);

      // Allow manual dismissal to cancel auto-dismiss
      notification.addEventListener('click', () => {
        if (!options?.actionable) {
          clearTimeout(dismissTimeout);
          notification.remove();
        }
      });
    }
  }
}

/**
 * Shows success toast notification with enhanced styling and animation
 */
export function showSuccessToast(message: string, options?: { context?: string, duration?: number }): void {
  const contextPrefix = options?.context ? `[${options.context}] ` : '';
  const finalMessage = `${contextPrefix}${message}`;
  const timestamp = new Date().toISOString();

  console.log(`✅ [${timestamp}] Success: ${finalMessage}`);

  // Create enhanced visual notification
  if (typeof window !== 'undefined') {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: linear-gradient(135deg, #16a34a, #22c55e);
      color: white;
      padding: 16px 24px;
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(22, 163, 74, 0.2), 0 4px 8px rgba(0, 0, 0, 0.1);
      z-index: 10000;
      max-width: 450px;
      min-width: 300px;
      font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
      font-size: 14px;
      font-weight: 500;
      line-height: 1.4;
      border-left: 4px solid rgba(255, 255, 255, 0.4);
      backdrop-filter: blur(12px);
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
      transform: translateX(100%);
      opacity: 0;
      display: flex;
      align-items: center;
      gap: 12px;
    `;

    // Add success icon and message
    const container = document.createElement('div');
    container.style.cssText = 'display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 12px;';

    const contentDiv = document.createElement('div');
    contentDiv.style.cssText = 'display: flex; align-items: center; flex: 1; gap: 8px;';
    // Create success content safely without innerHTML
    const iconSpan = document.createElement('span');
    iconSpan.textContent = '✅';
    iconSpan.style.fontSize = '16px';
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = sanitizeForDisplay(finalMessage);
    
    contentDiv.appendChild(iconSpan);
    contentDiv.appendChild(messageSpan);

    const closeButton = document.createElement('button');
    closeButton.innerHTML = '×';
    closeButton.onclick = () => notification.remove();
    closeButton.style.cssText = `
      background: none;
      border: none;
      color: white;
      font-size: 18px;
      cursor: pointer;
      padding: 0;
      margin: 0;
      opacity: 0.7;
      transition: opacity 0.2s ease;
    `;
    closeButton.onmouseover = () => closeButton.style.opacity = '1';
    closeButton.onmouseout = () => closeButton.style.opacity = '0.7';

    container.appendChild(contentDiv);
    container.appendChild(closeButton);
    notification.appendChild(container);
    document.body.appendChild(notification);

    // Enhanced animation
    setTimeout(() => {
      notification.style.transform = 'translateX(0)';
      notification.style.opacity = '1';
    }, 50);

    // Auto-dismiss with customizable duration
    const duration = options?.duration || 4000;
    const dismissTimeout = setTimeout(() => {
      notification.style.transform = 'translateX(100%)';
      notification.style.opacity = '0';
      setTimeout(() => {
        if (notification.parentNode) {
          notification.remove();
        }
      }, 400);
    }, duration);

    // Allow manual dismissal
    notification.addEventListener('click', () => {
      clearTimeout(dismissTimeout);
      notification.remove();
    });
  }
}

/**
 * Enhanced error logging with more context
 */
export function logError(error: unknown, context?: string): void {
  const timestamp = new Date().toISOString();
  const contextStr = context || 'Error';

  if (import.meta.env?.DEV) {
    console.group(`🔥 [${contextStr}] ${timestamp}`);
    console.error('Error:', error);

    // Log additional context if available
    if (error && typeof error === 'object') {
      if ('originalError' in error) {
        console.error('Original Error:', (error as any).originalError);
      }
      if ('path' in error) {
        console.error('API Path:', (error as any).path);
      }
      if ('stack' in error) {
        console.error('Stack Trace:', (error as any).stack);
      }
    }

    console.groupEnd();
  } else {
    // In production, you might want to send to error tracking service
    console.error(`[${contextStr}]:`, error);
  }
}

/**
 * Enhanced async error handler with retry logic and loading states
 */
export async function handleAsyncError<T>(
  operation: () => Promise<T>,
  options: {
    context?: string;
    showToast?: boolean;
    fallbackMessage?: string;
    retryOptions?: RetryOptions;
    onLoadingChange?: (loading: LoadingState) => void;
    onRetry?: (retryCount: number, maxRetries: number) => void;
  } = {}
): Promise<T | null> {
  const { retryOptions = {}, onLoadingChange, onRetry } = options;
  const maxRetries = retryOptions.maxRetries || 0;
  let retryCount = 0;

  const attemptOperation = async (): Promise<T> => {
    try {
      onLoadingChange?.({
        isLoading: true,
        status: retryCount > 0 ? `Retrying... (${retryCount}/${maxRetries})` : 'Loading...',
        progress: retryCount > 0 ? (retryCount / (maxRetries + 1)) * 100 : undefined
      });

      const result = await operation();

      onLoadingChange?.({ isLoading: false, status: 'Success', progress: 100 });
      return result;
    } catch (error) {
      onLoadingChange?.({ isLoading: false });

      // Check if we should retry
      if (retryCount < maxRetries) {
        const shouldRetry = retryOptions.shouldRetry ?
          retryOptions.shouldRetry(error, retryCount) :
          isRetryableError(error);

        if (shouldRetry) {
          retryCount++;
          const delay = calculateRetryDelay(retryCount, retryOptions);

          onRetry?.(retryCount, maxRetries);
          logError(error, `${options.context} (attempt ${retryCount}/${maxRetries + 1})`);

          // Show retry status
          onLoadingChange?.({
            isLoading: true,
            status: `Connection failed. Retrying in ${Math.ceil(delay/1000)}s...`,
            progress: (retryCount / (maxRetries + 1)) * 100
          });

          await new Promise(resolve => setTimeout(resolve, delay));
          return attemptOperation();
        }
      }

      throw error;
    }
  };

  try {
    return await attemptOperation();
  } catch (error) {
    logError(error, options.context);

    if (options.showToast !== false) {
      const message = options.fallbackMessage || formatErrorMessage(error);
      showErrorToast(message, { actionable: retryCount > 0, persistent: retryCount >= maxRetries });
    }

    return null;
  }
}

/**
 * Determines if an error is retryable
 */
function isRetryableError(error: any): boolean {
  if (!error) return false;

  const message = error.message || '';

  // Network errors are retryable
  if (message.includes('network') || message.includes('fetch') || message.includes('timeout')) {
    return true;
  }

  // Server errors (5xx) are retryable
  if (error.status >= 500) {
    return true;
  }

  // Rate limiting is retryable
  if (error.status === 429) {
    return true;
  }

  return false;
}

/**
 * Calculates retry delay with exponential backoff
 */
function calculateRetryDelay(retryCount: number, options: RetryOptions): number {
  const baseDelay = options.retryDelay || 1000;

  if (options.exponentialBackoff !== false) {
    return Math.min(baseDelay * Math.pow(2, retryCount - 1), 10000);
  }

  return baseDelay;
}

/**
 * Creates a loading state manager for long-running operations
 */
export function createLoadingManager() {
  let currentState: LoadingState = { isLoading: false };
  const listeners: ((state: LoadingState) => void)[] = [];

  const setState = (newState: Partial<LoadingState>) => {
    currentState = { ...currentState, ...newState };
    listeners.forEach(listener => listener(currentState));
  };

  return {
    getState: () => currentState,
    setState,
    subscribe: (listener: (state: LoadingState) => void) => {
      listeners.push(listener);
      return () => {
        const index = listeners.indexOf(listener);
        if (index > -1) listeners.splice(index, 1);
      };
    },
    startLoading: (status?: string) => setState({ isLoading: true, status, progress: 0 }),
    stopLoading: () => setState({ isLoading: false, status: undefined, progress: undefined }),
    updateProgress: (progress: number, status?: string) => setState({ progress, status }),
    setCanCancel: (canCancel: boolean) => setState({ canCancel })
  };
}

/**
 * Network status detection utilities
 */
export class NetworkMonitor {
  private static listeners: ((online: boolean) => void)[] = [];
  private static isSetup = false;

  static setup() {
    if (this.isSetup || typeof window === 'undefined') return;

    window.addEventListener('online', () => {
      console.log('🌐 Network connection restored');
      showSuccessToast('Connection restored');
      this.listeners.forEach(listener => listener(true));
    });

    window.addEventListener('offline', () => {
      console.log('🌐 Network connection lost');
      showErrorToast('Connection lost. Working offline...', { persistent: false });
      this.listeners.forEach(listener => listener(false));
    });

    this.isSetup = true;
  }

  static isOnline(): boolean {
    return typeof navigator !== 'undefined' ? navigator.onLine : true;
  }

  static addListener(listener: (online: boolean) => void): () => void {
    this.setup();
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) this.listeners.splice(index, 1);
    };
  }
}

/**
 * Enhanced validation utilities for API requests
 */
export function validateApiRequest(data: any, requiredFields: string[]): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!data || typeof data !== 'object') {
    errors.push('Request data must be an object');
    return { valid: false, errors };
  }

  for (const field of requiredFields) {
    if (!(field in data) || data[field] === null || data[field] === undefined) {
      errors.push(`Required field '${field}' is missing`);
    } else if (typeof data[field] === 'string' && data[field].trim() === '') {
      errors.push(`Required field '${field}' cannot be empty`);
    }
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Performance monitoring for API calls
 */
export class PerformanceMonitor {
  private static measurements: Map<string, { start: number; end?: number; duration?: number }> = new Map();

  static startMeasurement(key: string): void {
    this.measurements.set(key, { start: performance.now() });
  }

  static endMeasurement(key: string): number | null {
    const measurement = this.measurements.get(key);
    if (!measurement) return null;

    const end = performance.now();
    const duration = end - measurement.start;

    this.measurements.set(key, { ...measurement, end, duration });

    if (import.meta.env?.DEV) {
      console.log(`⏱️ ${key}: ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  static getMeasurement(key: string): { start: number; end?: number; duration?: number } | null {
    return this.measurements.get(key) || null;
  }

  static clearMeasurements(): void {
    this.measurements.clear();
  }
}

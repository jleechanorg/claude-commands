/**
 * Error handling utilities for Frontend v2
 */

export interface AppError {
  message: string;
  code?: string;
  details?: any;
}

/**
 * Formats error messages for user display
 */
export function formatErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message);
  }

  return 'An unexpected error occurred. Please try again.';
}

/**
 * Shows error toast notification
 * For now, using alert() - can be replaced with proper toast library
 */
export function showErrorToast(message: string): void {
  // TODO: Replace with proper toast notification library (e.g., react-hot-toast)
  alert(`Error: ${message}`);
}

/**
 * Shows success toast notification
 */
export function showSuccessToast(message: string): void {
  // TODO: Replace with proper toast notification library
  console.log(`✅ Success: ${message}`);
}

/**
 * Logs error for debugging (development only)
 */
export function logError(error: unknown, context?: string): void {
  if (import.meta.env.DEV) {
    console.error(`[${context || 'Error'}]:`, error);
  }
}

/**
 * Standard error handler for async operations
 */
export async function handleAsyncError<T>(
  operation: () => Promise<T>,
  options: {
    context?: string;
    showToast?: boolean;
    fallbackMessage?: string;
  } = {}
): Promise<T | null> {
  try {
    return await operation();
  } catch (error) {
    logError(error, options.context);

    if (options.showToast !== false) {
      const message = options.fallbackMessage || formatErrorMessage(error);
      showErrorToast(message);
    }

    return null;
  }
}

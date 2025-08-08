/**
 * Development utilities for Frontend v2
 * Provides safe console logging that only runs in development mode
 */

const isDev = import.meta.env?.DEV || process.env.NODE_ENV === 'development';

/**
 * Safe console.log that only outputs in development
 */
export function devLog(...args: any[]): void {
  if (isDev) {
    console.log(...args);
  }
}

/**
 * Safe console.error that only outputs in development
 */
export function devError(...args: any[]): void {
  if (isDev) {
    console.error(...args);
  }
}

/**
 * Safe console.warn that only outputs in development
 */
export function devWarn(...args: any[]): void {
  if (isDev) {
    console.warn(...args);
  }
}

/**
 * Safe console.info that only outputs in development
 */
export function devInfo(...args: any[]): void {
  if (isDev) {
    console.info(...args);
  }
}

/**
 * Safe console.group that only runs in development
 */
export function devGroup(label: string): void {
  if (isDev) {
    console.group(label);
  }
}

/**
 * Safe console.groupEnd that only runs in development
 */
export function devGroupEnd(): void {
  if (isDev) {
    console.groupEnd();
  }
}

/**
 * Safe console.table that only outputs in development
 */
export function devTable(data: any): void {
  if (isDev) {
    console.table(data);
  }
}

/**
 * Development-only timer
 */
export function devTime(label: string): void {
  if (isDev) {
    console.time(label);
  }
}

/**
 * Development-only timer end
 */
export function devTimeEnd(label: string): void {
  if (isDev) {
    console.timeEnd(label);
  }
}

/**
 * Check if running in development mode
 */
export function isDevMode(): boolean {
  return isDev;
}
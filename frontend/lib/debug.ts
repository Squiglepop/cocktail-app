/**
 * Debug logging utility - only outputs in development mode.
 * Use this instead of console.log for debug statements.
 */

const DEBUG = process.env.NODE_ENV === 'development';

export const debug = {
  /**
   * Log debug info (only in development)
   */
  log: (...args: unknown[]): void => {
    if (DEBUG) console.log('[Debug]', ...args);
  },

  /**
   * Log warnings (only in development)
   */
  warn: (...args: unknown[]): void => {
    if (DEBUG) console.warn('[Debug]', ...args);
  },

  /**
   * Log errors (always - errors should never be silenced)
   */
  error: (...args: unknown[]): void => {
    console.error('[Error]', ...args);
  },

  /**
   * Log with a specific namespace prefix
   */
  ns: (namespace: string) => ({
    log: (...args: unknown[]): void => {
      if (DEBUG) console.log(`[${namespace}]`, ...args);
    },
    warn: (...args: unknown[]): void => {
      if (DEBUG) console.warn(`[${namespace}]`, ...args);
    },
    error: (...args: unknown[]): void => {
      console.error(`[${namespace}]`, ...args);
    },
  }),
};

// Pre-configured namespace loggers for common modules
export const swDebug = debug.ns('SW');
export const offlineDebug = debug.ns('Offline');
export const favouritesDebug = debug.ns('Favourites');
export const cacheDebug = debug.ns('Cache');

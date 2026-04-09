/**
 * Bit & Mortar Aesthetic System
 * 
 * Main entry point for the distributed aesthetic operating system.
 * Provides unified access to all aesthetic functionality.
 * 
 * @module bit-mortar-aesthetic
 * 
 * @example
 * // Vanilla JS usage
 * import { initAesthetic, shuffle, setEpoch } from '/core/core/index.js';
 * 
 * initAesthetic();
 * shuffle(); // Shuffle to random epoch
 * 
 * @example
 * // React usage
 * import { AestheticProvider, useAesthetic } from '/core/adapters/react/AestheticProvider.jsx';
 * 
 * function App() {
 *   return (
 *     <AestheticProvider>
 *       <MyComponent />
 *     </AestheticProvider>
 *   );
 * }
 */

// ─── Core Modules ─────────────────────────────────────────────────────────────

export {
  AESTHETIC_EPOCHS,
  getEpochCount,
  getEpochByIndex,
  getEpochByName,
  getRandomEpoch,
  searchEpochs,
  getEpochsByCentury,
  epochToCSS,
} from './aesthetics.js';

export {
  getAestheticState,
  getGlobalState,
  getAppState,
  setAestheticState,
  clearAppState,
  clearGlobalState,
  onAestheticChange,
  getAestheticDiagnostic,
  exportAestheticData,
  importAestheticData,
  initAestheticState,
} from './aestheticState.js';

export {
  applyAesthetic,
  removeAesthetic,
  shuffleAesthetic,
  nextAesthetic,
  previousAesthetic,
  resetAesthetic,
  setAestheticByName,
  watchForMutations,
  initAestheticEngine,
} from './aestheticEngine.js';

// ─── UI Components ────────────────────────────────────────────────────────────
// Note: Import directly from ../ui/ampersand.js and ../ui/epochPicker.js if needed
// These are commented out to avoid build issues with apps that don't use them
/*
export {
  initAmpersand,
  triggerShuffle,
  triggerReset,
  triggerGlobalSync,
  openEpochPicker,
  injectAmpersandStyles,
} from '/ui/ampersand.js';

export {
  openPicker,
  closePicker,
  isPickerOpen,
} from '/ui/epochPicker.js';
*/

// ─── Integration ──────────────────────────────────────────────────────────────

export {
  sendToLelu,
  syncToLelu,
  listenForLeluAesthetic,
  useLeluAestheticSync,
  initAutoSync,
  getLeluAestheticState,
  setLeluAesthetic,
  enableDebugLogging,
} from '../integration/leluBridge.js';

// ─── Convenience Functions ────────────────────────────────────────────────────

/**
 * Initialize complete aesthetic system
 * 
 * Call this once at app startup.
 * 
 * @param {Object} options
 * @param {boolean} [options.enableAmpersand=true] - Enable ampersand interactions
 * @param {boolean} [options.enablePicker=true] - Enable epoch picker overlay
 * @param {boolean} [options.autoSync=true] - Auto-sync across tabs/apps
 * @param {boolean} [options.debug=false] - Enable debug logging
 */
export function initAesthetic(options = {}) {
  const {
    enableAmpersand = true,
    enablePicker = true,
    autoSync = true,
    debug = false,
  } = options;
  
  // Initialize core
  initAestheticState();
  initAestheticEngine();
  
  // Initialize UI
  if (enableAmpersand) {
    initAmpersand();
  }
  
  if (enablePicker) {
    // Epoch picker auto-initializes
  }
  
  // Initialize sync
  if (autoSync) {
    initAutoSync();
  }
  
  // Debug mode
  if (debug) {
    enableDebugLogging(true);
  }
  
  console.log('[Aesthetic] System initialized');
}

/**
 * Quick shuffle with visual feedback
 *
 * @param {boolean} global - Sync globally
 * @returns {Promise<Object>} The new epoch
 */
export async function shuffle(global = false) {
  const { shuffleAesthetic } = await import('./aestheticEngine.js');
  const { setAestheticState } = await import('./aestheticState.js');

  const epoch = shuffleAesthetic(true);

  if (global) {
    setAestheticState(epoch, { global: true });
  }

  return epoch;
}

/**
 * Set specific epoch by name
 *
 * @param {string} name - Epoch name
 * @param {boolean} global - Sync globally
 * @returns {Promise<Object|null>} The applied epoch
 */
export async function setEpoch(name, global = false) {
  const { setAestheticByName } = await import('./aestheticEngine.js');
  const { setAestheticState } = await import('./aestheticState.js');

  const epoch = setAestheticByName(name);

  if (epoch && global) {
    setAestheticState(epoch, { global: true });
  }

  return epoch;
}

/**
 * Get current epoch
 *
 * @returns {Object}
 */
export async function getEpoch() {
  const { getAestheticState } = await import('./aestheticState.js');
  return getAestheticState().epoch;
}

// ─── Type Definitions (JSDoc) ─────────────────────────────────────────────────

/**
 * @typedef {Object} AestheticEpoch
 * @property {string} epoch - Name of the aesthetic movement
 * @property {string} period - Historical time period
 * @property {Object} palette - Color definitions
 * @property {string} palette.primary - Primary accent color
 * @property {string} palette.secondary - Secondary accent color
 * @property {string} palette.tertiary - Deep background / shadows
 * @property {string} [palette.accent] - Optional fourth color
 * @property {string} font - Primary typeface
 * @property {string} [fontSecondary] - Secondary typeface
 * @property {string} [description] - Brief movement description
 * @property {string} [keywords] - Comma-separated tags
 */

/**
 * @typedef {Object} AestheticState
 * @property {AestheticEpoch} epoch - Current epoch
 * @property {'app' | 'global' | 'default'} source - State source
 */

// ─── Version ──────────────────────────────────────────────────────────────────

export const VERSION = '1.0.0';
export const VERSION_NAME = 'Bit & Mortar Aesthetic OS v1';

// ─── Default Export ───────────────────────────────────────────────────────────

export default {
  init: initAesthetic,
  shuffle,
  setEpoch,
  getEpoch,
  VERSION,
};

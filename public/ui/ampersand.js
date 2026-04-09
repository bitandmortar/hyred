/**
 * Bit & Mortar Ampersand Controller
 * 
 * Interaction semantics for the sacred ampersand glyph.
 * The ampersand is the primary interface for aesthetic manipulation.
 * 
 * Interaction Contract:
 *   ┌────────────────────┬────────────────────────────────────────┐
 *   │ Interaction        │ Behavior                               │
 *   ├────────────────────┼────────────────────────────────────────┤
 *   │ Click &            │ Shuffle (weighted random)              │
 *   │ Shift + Click &    │ Sync globally across all apps          │
 *   │ Double-click &     │ Hard reset to global default           │
 *   │ Hold & (500ms)     │ Open epoch picker overlay              │
 *   │ Hover &            │ Show current epoch metadata tooltip    │
 *   └────────────────────┴────────────────────────────────────────┘
 * 
 * @module ampersand
 */

import { shuffleAesthetic, resetAesthetic } from '../core/aestheticEngine.js';
import { setAestheticState, getAestheticState } from '../core/aestheticState.js';
import { AESTHETIC_EPOCHS } from '../core/aesthetics.js';

// ─── State ────────────────────────────────────────────────────────────────────

let holdTimer = null;
let isHolding = false;
let clickCount = 0;
let lastClickTime = 0;

const HOLD_DURATION = 500; // ms
const DOUBLE_CLICK_WINDOW = 300; // ms

// ─── Initialization ───────────────────────────────────────────────────────────

/**
 * Initialize ampersand controller
 * Attaches event listeners to #bm-ampersand element
 * 
 * @param {Object} options
 * @param {boolean} [options.enableHover=true] - Show tooltip on hover
 * @param {boolean} [options.enableHold=true] - Open picker on hold
 * @param {Function} [options.onShuffle] - Callback on shuffle
 * @param {Function} [options.onReset] - Callback on reset
 * @param {Function} [options.onGlobalSync] - Callback on global sync
 */
export function initAmpersand(options = {}) {
  const {
    enableHover = true,
    enableHold = true,
    onShuffle,
    onReset,
    onGlobalSync,
  } = options;

  // Wait for DOM
  if (typeof document === 'undefined') return;
  
  const init = () => {
    const ampersand = document.getElementById('bm-ampersand');
    if (!ampersand) {
      console.warn('[Ampersand] Element #bm-ampersand not found');
      return;
    }

    // Attach event listeners
    attachClickHandlers(ampersand, onShuffle, onReset, onGlobalSync);
    
    if (enableHold) {
      attachHoldHandlers(ampersand);
    }
    
    if (enableHover) {
      attachHoverHandlers(ampersand);
    }

    // Add cursor pointer
    ampersand.style.cursor = 'pointer';
    
    console.log('[Ampersand] Initialized');
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}

// ─── Click Handlers ───────────────────────────────────────────────────────────

/**
 * Attach click handlers for shuffle, reset, global sync
 * 
 * @param {HTMLElement} ampersand
 * @param {Function} onShuffle
 * @param {Function} onReset
 * @param {Function} onGlobalSync
 */
function attachClickHandlers(ampersand, onShuffle, onReset, onGlobalSync) {
  ampersand.addEventListener('click', (e) => {
    const now = Date.now();
    
    // Check for double-click
    if (now - lastClickTime < DOUBLE_CLICK_WINDOW) {
      // Double-click detected - reset
      handleReset(ampersand, onReset);
      clickCount = 0;
      return;
    }
    
    clickCount++;
    lastClickTime = now;
    
    // Single click - shuffle
    // Check for shift key (global sync)
    if (e.shiftKey) {
      handleGlobalSync(ampersand, onGlobalSync);
    } else {
      handleShuffle(ampersand, onShuffle);
    }
  });
}

/**
 * Handle shuffle interaction
 * 
 * @param {HTMLElement} ampersand
 * @param {Function} onShuffle
 */
function handleShuffle(ampersand, onShuffle) {
  const epoch = shuffleAesthetic(true); // weighted towards modern
  
  // Visual feedback
  triggerAmpersandPulse(ampersand);
  
  // Callback
  if (onShuffle) onShuffle(epoch);
  
  console.log('[Ampersand] Shuffled to:', epoch.epoch);
}

/**
 * Handle reset interaction (double-click)
 * 
 * @param {HTMLElement} ampersand
 * @param {Function} onReset
 */
function handleReset(ampersand, onReset) {
  const epoch = resetAesthetic();
  
  // Visual feedback - strong pulse
  triggerAmpersandFlash(ampersand);
  
  // Callback
  if (onReset) onReset(epoch);
  
  console.log('[Ampersand] Reset to:', epoch.epoch);
}

/**
 * Handle global sync interaction (shift+click)
 * 
 * @param {HTMLElement} ampersand
 * @param {Function} onGlobalSync
 */
function handleGlobalSync(ampersand, onGlobalSync) {
  const epoch = shuffleAesthetic(true);
  setAestheticState(epoch, { global: true });
  
  // Visual feedback - glow
  triggerAmpersandGlow(ampersand);
  
  // Callback
  if (onGlobalSync) onGlobalSync(epoch);
  
  console.log('[Ampersand] Global sync:', epoch.epoch);
}

// ─── Hold Handler ─────────────────────────────────────────────────────────────

/**
 * Attach hold handler for epoch picker
 * 
 * @param {HTMLElement} ampersand
 */
function attachHoldHandlers(ampersand) {
  // Mouse
  ampersand.addEventListener('mousedown', (e) => {
    // Ignore if shift key (global sync)
    if (e.shiftKey) return;
    
    isHolding = true;
    holdTimer = setTimeout(() => {
      if (isHolding) {
        handleHold(ampersand);
        isHolding = false;
      }
    }, HOLD_DURATION);
  });
  
  ampersand.addEventListener('mouseup', () => {
    isHolding = false;
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
    }
  });
  
  ampersand.addEventListener('mouseleave', () => {
    isHolding = false;
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
    }
  });
  
  // Touch support
  ampersand.addEventListener('touchstart', (e) => {
    e.preventDefault();
    isHolding = true;
    holdTimer = setTimeout(() => {
      if (isHolding) {
        handleHold(ampersand);
        isHolding = false;
      }
    }, HOLD_DURATION);
  });
  
  ampersand.addEventListener('touchend', () => {
    isHolding = false;
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
    }
  });
}

/**
 * Handle hold interaction - open epoch picker
 * 
 * @param {HTMLElement} ampersand
 */
function handleHold(ampersand) {
  // Dispatch custom event for epoch picker
  window.dispatchEvent(new CustomEvent('open-epoch-picker', {
    detail: {
      anchor: ampersand,
      timestamp: Date.now(),
    }
  }));
  
  console.log('[Ampersand] Opening epoch picker');
}

// ─── Hover Handler ────────────────────────────────────────────────────────────

/**
 * Attach hover handler for tooltip
 * 
 * @param {HTMLElement} ampersand
 */
function attachHoverHandlers(ampersand) {
  let tooltip = null;
  
  ampersand.addEventListener('mouseenter', () => {
    const { epoch } = getAestheticState();
    
    // Create tooltip
    tooltip = createTooltip(epoch);
    
    // Position near ampersand
    const rect = ampersand.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2}px`;
    tooltip.style.top = `${rect.bottom + 8}px`;
    
    document.body.appendChild(tooltip);
  });
  
  ampersand.addEventListener('mouseleave', () => {
    if (tooltip) {
      tooltip.remove();
      tooltip = null;
    }
  });
}

/**
 * Create epoch metadata tooltip
 * 
 * @param {Object} epoch
 * @returns {HTMLElement}
 */
function createTooltip(epoch) {
  const tooltip = document.createElement('div');
  tooltip.className = 'bm-aesthetic-tooltip';
  tooltip.style.cssText = `
    position: fixed;
    z-index: 9999;
    background: rgba(0, 0, 0, 0.9);
    color: #fff;
    padding: 12px 16px;
    border-radius: 8px;
    font-family: system-ui;
    font-size: 12px;
    line-height: 1.5;
    pointer-events: none;
    transform: translateX(-50%);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    max-width: 300px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  `;
  
  tooltip.innerHTML = `
    <div style="font-weight: 700; font-size: 14px; margin-bottom: 4px; color: ${epoch.palette.primary}">
      ${epoch.epoch}
    </div>
    <div style="color: #888; font-size: 11px; margin-bottom: 8px;">
      ${epoch.period}
    </div>
    <div style="color: #aaa; font-size: 11px;">
      ${epoch.description || 'Aesthetic epoch'}
    </div>
    ${epoch.keywords ? `
      <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;">
        ${epoch.keywords.split(',').slice(0, 5).map(k => `
          <span style="
            background: rgba(255, 255, 255, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
          ">${k.trim()}</span>
        `).join('')}
      </div>
    ` : ''}
  `;
  
  return tooltip;
}

// ─── Visual Feedback ──────────────────────────────────────────────────────────

/**
 * Trigger pulse animation on shuffle
 * 
 * @param {HTMLElement} ampersand
 */
function triggerAmpersandPulse(ampersand) {
  ampersand.style.transition = 'transform 0.15s ease, color 0.15s ease';
  ampersand.style.transform = 'scale(1.3)';
  ampersand.style.color = 'var(--color-primary, #00ffca)';
  
  setTimeout(() => {
    ampersand.style.transform = 'scale(1)';
    ampersand.style.color = '';
  }, 150);
}

/**
 * Trigger flash animation on reset
 * 
 * @param {HTMLElement} ampersand
 */
function triggerAmpersandFlash(ampersand) {
  ampersand.style.transition = 'transform 0.2s ease, color 0.2s ease';
  ampersand.style.transform = 'scale(1.5) rotate(180deg)';
  ampersand.style.color = 'var(--color-secondary, #ffffff)';
  
  setTimeout(() => {
    ampersand.style.transform = 'scale(1) rotate(0deg)';
    ampersand.style.color = '';
  }, 200);
}

/**
 * Trigger glow animation on global sync
 * 
 * @param {HTMLElement} ampersand
 */
function triggerAmpersandGlow(ampersand) {
  ampersand.style.transition = 'text-shadow 0.3s ease';
  ampersand.style.textShadow = `
    0 0 10px var(--color-primary, #00ffca),
    0 0 20px var(--color-primary, #00ffca),
    0 0 30px var(--color-primary, #00ffca)
  `;
  
  setTimeout(() => {
    ampersand.style.textShadow = '';
  }, 300);
}

// ─── Programmatic Control ─────────────────────────────────────────────────────

/**
 * Manually trigger shuffle (for keyboard shortcuts, etc.)
 */
export function triggerShuffle() {
  const ampersand = document.getElementById('bm-ampersand');
  if (ampersand) {
    handleShuffle(ampersand, null);
  }
}

/**
 * Manually trigger reset
 */
export function triggerReset() {
  const ampersand = document.getElementById('bm-ampersand');
  if (ampersand) {
    handleReset(ampersand, null);
  }
}

/**
 * Manually trigger global sync
 */
export function triggerGlobalSync() {
  const ampersand = document.getElementById('bm-ampersand');
  if (ampersand) {
    handleGlobalSync(ampersand, null);
  }
}

/**
 * Manually open epoch picker
 */
export function openEpochPicker() {
  const ampersand = document.getElementById('bm-ampersand');
  if (ampersand) {
    handleHold(ampersand);
  }
}

// ─── CSS Styles ───────────────────────────────────────────────────────────────

/**
 * Inject ampersand styles
 */
export function injectAmpersandStyles() {
  const styleId = 'bm-ampersand-styles';
  
  if (document.getElementById(styleId)) return;
  
  const style = document.createElement('style');
  style.id = styleId;
  style.textContent = `
    #bm-ampersand {
      cursor: pointer;
      transition: transform 0.4s var(--ease-aesthetic, cubic-bezier(0.4, 0, 0.2, 1)),
                  color 0.3s ease,
                  text-shadow 0.3s ease;
      display: inline-block;
      user-select: none;
      -webkit-user-select: none;
    }
    
    #bm-ampersand:hover {
      transform: rotate(12deg) scale(1.2);
      color: var(--color-secondary, #ffd700);
    }
    
    #bm-ampersand:active {
      transform: rotate(-5deg) scale(0.95);
    }
    
    /* Tooltip fade in */
    .bm-aesthetic-tooltip {
      animation: bm-tooltip-fade-in 0.2s ease;
    }
    
    @keyframes bm-tooltip-fade-in {
      from {
        opacity: 0;
        transform: translateX(-50%) translateY(-8px);
      }
      to {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
      }
    }
  `;
  
  document.head.appendChild(style);
}

// Auto-inject styles on module load
if (typeof document !== 'undefined') {
  injectAmpersandStyles();
}

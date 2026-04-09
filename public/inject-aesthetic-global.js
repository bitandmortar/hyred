/**
 * Bit & Mortar Global Aesthetic Injection
 * 
 * This script is automatically injected into ALL pages across bitandmortar.com
 * It provides:
 * - Clickable ampersand in any header
 * - Location detection badge
 * - Aesthetic system initialization
 * - Cross-tab synchronization
 * - UNIFIED BRANDING (lelu style)
 * 
 * Works with both static HTML AND React apps!
 */

(function() {
  'use strict';
  
  // Prevent double-injection
  if (window.__bmAestheticInjected) return;
  window.__bmAestheticInjected = true;
  
  console.log('[Bit & Mortar] Initializing Global Aesthetic Engine...');
  
  // ─── Configuration ──────────────────────────────────────────────────────────
  
  const CONFIG = {
    baseUrl: '/core',
    cssUrl: '/ui/aesthetics.css',
    enableAmpersand: true,
    enableLocation: true,
    enablePicker: true,
    autoSync: true,
    debug: false,
  };
  
  // ─── CSS Injection ──────────────────────────────────────────────────────────
  
  function injectCSS() {
    // Inject standard aesthetics.css
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = CONFIG.cssUrl;
    document.head.appendChild(link);

    // Inject global brand override styles
    const style = document.createElement('style');
    style.textContent = `
      .bm-title {
        font-family: system-ui, -apple-system, sans-serif !important;
        letter-spacing: -0.05em !important;
        font-weight: 800 !important;
      }
      .bm-slash {
        font-family: 'JetBrains Mono', monospace !important;
        display: inline-block;
        margin: 0 4px;
      }
      .bm-sub {
        font-family: 'EB Garamond', Georgia, serif !important;
        font-style: italic !important;
        font-weight: 400 !important;
      }
      #bm-ampersand:hover {
        transform: scale(1.1);
        text-shadow: 0 0 10px var(--color-primary, #00ffca);
      }
    `;
    document.head.appendChild(style);
  }
  
  // ─── Dynamic Module Loading ─────────────────────────────────────────────────
  
  async function loadModules() {
    try {
      // Use absolute path for core imports
      const { initAesthetic, initAmpersand, shuffle } = await import(`${CONFIG.baseUrl}/index.js`);
      return { initAesthetic, initAmpersand, shuffle };
    } catch (error) {
      console.error('[Bit & Mortar] Failed to load aesthetic modules:', error);
      return null;
    }
  }
  
  // ─── Header Detection & Modification ────────────────────────────────────────
  
  function findOrCreateHeader() {
    // Try common header selectors
    const selectors = [
      'header',
      '.bm-header',
      'nav',
      '.top-bar',
      '.app-header',
      '.nav',
      '[role="banner"]',
    ];
    
    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el) return el;
    }
    
    // Create header if none exists
    const header = document.createElement('header');
    header.style.cssText = `
      position: sticky;
      top: 0;
      z-index: 9999;
      padding: 1rem 1.5rem;
      background: rgba(2, 4, 7, 0.8);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      justify-content: space-between;
      align-items: center;
    `;
    
    document.body.insertBefore(header, document.body.firstChild);
    return header;
  }
  
  function getAppName() {
    // 1. Check for explicit meta tag (e.g. <meta name="bm-app" content="lelu">)
    const meta = document.querySelector('meta[name="bm-app"]');
    if (meta) return meta.getAttribute('content');

    // 2. Detect from subdomain
    const parts = window.location.hostname.split('.');
    if (parts.length > 2 && parts[0] !== 'www') return parts[0];

    // 3. Detect from path (/apps/APP_NAME/...)
    const pathParts = window.location.pathname.split('/');
    const appsIndex = pathParts.indexOf('apps');
    if (appsIndex !== -1 && pathParts[appsIndex + 1]) {
      return pathParts[appsIndex + 1].replace(/-/g, '_');
    }

    // 4. Default
    return 'infrastructure';
  }
  
  function updateBrandElement(header) {
    const appName = getAppName();
    
    // Check if brand already exists manually in HTML
    const existing = header.querySelector('.bm-title');
    if (existing) {
      // Ensure the ampersand has the ID for interaction
      const amp = existing.querySelector('span:nth-child(1)') || existing.querySelector('.bm-ampersand');
      if (amp && !amp.id) amp.id = 'bm-ampersand';
      return;
    }

    // Create brand container
    const brand = document.createElement('div');
    brand.className = 'bm-brand-container';
    brand.style.cssText = `display: flex; align-items: center; gap: 8px;`;
    
    brand.innerHTML = `
      <h1 class="bm-title" style="margin:0; font-size: 1.5rem; color: #fff;">
        bit<span id="bm-ampersand" style="color: var(--color-primary, #00ffca); cursor: pointer; transition: transform 0.2s ease; display: inline-block;">&</span>mortar
        <span class="bm-slash" style="color: var(--color-primary, #00ffca); opacity: 0.6;">/</span>
        <span class="bm-sub">${appName}</span>
      </h1>
    `;
    
    // Insert at the beginning of the header
    header.insertBefore(brand, header.firstChild);
  }
  
  function createLocationBadge() {
    if (document.getElementById('bm-location-badge')) return null;

    const badge = document.createElement('div');
    badge.id = 'bm-location-badge';
    badge.className = 'bm-location-badge';
    badge.style.cssText = `
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: #888;
      border: 1px solid rgba(255, 255, 255, 0.05);
    `;
    
    badge.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity: 0.5;">
        <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>
        <circle cx="12" cy="10" r="3"/>
      </svg>
      <span id="bm-location-text">Was, DC</span>
    `;
    
    return badge;
  }
  
  async function detectLocation() {
    const textEl = document.getElementById('bm-location-text');
    if (!textEl) return;
    
    try {
      const response = await fetch('https://ipapi.co/json/');
      if (!response.ok) throw new Error('Geolocation failed');
      const data = await response.json();
      textEl.textContent = `${data.city}, ${data.region_code}`;
    } catch (err) {
      console.warn('[Bit & Mortar] Location detection fallback');
    }
  }
  
  // ─── Initialization ─────────────────────────────────────────────────────────
  
  async function init() {
    // Inject CSS immediately
    injectCSS();
    
    // Wait for DOM
    if (document.readyState === 'loading') {
      await new Promise(resolve => document.addEventListener('DOMContentLoaded', resolve));
    }
    
    // Load modules
    const modules = await loadModules();
    if (!modules) return;
    const { initAesthetic, initAmpersand, shuffle } = modules;
    
    // Initialize primary system
    initAesthetic({
      enableAmpersand: CONFIG.enableAmpersand,
      enablePicker: CONFIG.enablePicker,
      autoSync: CONFIG.autoSync,
      debug: CONFIG.debug,
    });
    
    // Find or create header
    const header = findOrCreateHeader();
    
    // Update brand
    updateBrandElement(header);
    
    // Add location badge if enabled
    if (CONFIG.enableLocation) {
      const badge = createLocationBadge();
      if (badge) {
        const controls = document.createElement('div');
        controls.className = 'bm-header-controls';
        controls.style.cssText = `display: flex; align-items: center; gap: 16px; margin-left: auto;`;
        controls.appendChild(badge);
        header.appendChild(controls);
        detectLocation();
      }
    }
    
    // Initialize ampersand interaction
    initAmpersand({
      enableHover: true,
      enableHold: true,
      onShuffle: (epoch) => {
        // Find all instances of 'mint green' and update if necessary
        // (The system handles CSS variables, but we can add secondary effects here)
      }
    });

    // Make shuffle available globally
    window.__bmShuffle = shuffle;
    
    console.log('[Bit & Mortar] Standardized Aesthetic Active');
  }
  
  // Start the engine
  init().catch(console.error);
  
})();

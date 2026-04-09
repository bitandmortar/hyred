// 1. NEURAL BACKGROUND ENGINE (VOID CANVAS)
const voidCanvas = document.getElementById('void-canvas');
const vCtx = voidCanvas.getContext('2d');
let dots = [];

function initVoid() {
    voidCanvas.width = window.innerWidth;
    voidCanvas.height = window.innerHeight;
    dots = [];
    for(let i=0; i<80; i++) {
        dots.push({
            x: Math.random() * voidCanvas.width,
            y: Math.random() * voidCanvas.height,
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
            size: Math.random() * 2
        });
    }
}

function animateVoid() {
    vCtx.clearRect(0, 0, voidCanvas.width, voidCanvas.height);
    vCtx.fillStyle = 'rgba(0, 255, 136, 0.2)';
    
    dots.forEach((d, i) => {
        d.x += d.vx;
        d.y += d.vy;
        if(d.x < 0 || d.x > voidCanvas.width) d.vx *= -1;
        if(d.y < 0 || d.y > voidCanvas.height) d.vy *= -1;
        
        vCtx.beginPath();
        vCtx.arc(d.x, d.y, d.size, 0, Math.PI * 2);
        vCtx.fill();
        
        // Connect dots
        for(let j=i+1; j<dots.length; j++) {
            let d2 = dots[j];
            let dist = Math.hypot(d.x - d2.x, d.y - d2.y);
            if(dist < 150) {
                vCtx.strokeStyle = `rgba(0, 209, 255, ${0.1 * (1 - dist/150)})`;
                vCtx.lineWidth = 0.5;
                vCtx.beginPath();
                vCtx.moveTo(d.x, d.y);
                vCtx.lineTo(d2.x, d2.y);
                vCtx.stroke();
            }
        }
    });
    requestAnimationFrame(animateVoid);
}

window.addEventListener('resize', initVoid);
initVoid();
animateVoid();

// 2. SKILL CLUSTER CANVAS (NEXUS MAP)
const clusterCanvas = document.getElementById('skill-cluster-canvas');
const cCtx = clusterCanvas.getContext('2d');
let nodes = [
    { label: 'RUST', x: 0.5, y: 0.3, color: '#00FF88' },
    { label: 'OMNI-CORE', x: 0.35, y: 0.5, color: '#00D1FF' },
    { label: 'DATA_PROV', x: 0.65, y: 0.5, color: '#FFD700' },
    { label: 'LLM_ORCH', x: 0.5, y: 0.7, color: '#A855F7' }
];

function drawCluster() {
    const w = clusterCanvas.parentElement.offsetWidth;
    const h = clusterCanvas.parentElement.offsetHeight;
    clusterCanvas.width = w;
    clusterCanvas.height = h;
    
    cCtx.clearRect(0, 0, w, h);
    
    // Draw Connections
    cCtx.shadowBlur = 10;
    cCtx.lineWidth = 1;
    nodes.forEach((n, i) => {
        nodes.forEach((n2, j) => {
            if(i === j) return;
            cCtx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
            cCtx.beginPath();
            cCtx.moveTo(n.x * w, n.y * h);
            cCtx.lineTo(n2.x * w, n2.y * h);
            cCtx.stroke();
        });
    });

    // Draw Nodes
    nodes.forEach(n => {
        const x = n.x * w;
        const y = n.y * h;
        
        // Glow
        cCtx.shadowColor = n.color;
        cCtx.fillStyle = n.color;
        cCtx.beginPath();
        cCtx.arc(x, y, 6, 0, Math.PI * 2);
        cCtx.fill();
        
        // Label
        cCtx.shadowBlur = 0;
        cCtx.font = '700 10px JetBrains Mono';
        cCtx.fillStyle = '#fff';
        cCtx.textAlign = 'center';
        cCtx.fillText(n.label, x, y - 15);
    });
}
window.addEventListener('resize', drawCluster);
setTimeout(drawCluster, 100);

// 3. CORE LOGIC & API
const btnGenerate = document.getElementById('btn-generate');
const btnScrape = document.getElementById('btn-scrape');
const urlInput = document.getElementById('url-input');
const jdInput = document.getElementById('jd-input');
const outputText = document.getElementById('output-text');
const atsScoreDisplay = document.getElementById('ats-score');
const ringFill = document.getElementById('ring-fill');
const marketSignals = document.getElementById('market-signals');

async function api(path, method='GET', body=null) {
    let url = `/api/hyred${path}`;
    const opts = { method, headers: {'Content-Type': 'application/json'} };
    if (body && method !== 'GET') opts.body = JSON.stringify(body);
    try {
        const r = await fetch(url, opts);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return await r.json();
    } catch(e) {
        console.error("API Error:", e);
        return { ok: false, error: e.message };
    }
}

// 4. ACTIONS
btnScrape.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) return;
    btnScrape.innerText = "SENSING...";
    const data = await api(`/scrape?url=${encodeURIComponent(url)}`, 'POST');
    if (data.ok) {
        jdInput.value = data.data.description;
        document.getElementById('ghost-status').innerText = data.aug.staleness;
        document.getElementById('market-salary').innerText = data.aug.salary;
        document.getElementById('aug-stack').innerHTML = data.aug.stack.map(s => `
            <span class="q-tag jade">${s}</span>
        `).join('');
        marketSignals.style.display = 'flex';
        btnScrape.innerText = "SYNCED";
        setTimeout(() => btnScrape.innerText = "INGEST", 2000);
    }
});

btnGenerate.addEventListener('click', async () => {
    const content = jdInput.value.trim();
    if (!content) return;
    
    // UI Feedback
    btnGenerate.innerText = "RUNNING CROSS-CORRELATION...";
    outputText.innerHTML = '<div class="stream-placeholder">INITIALIZING LLM AGENT...</div>';
    
    const data = await api('/generate', 'POST', { 
        job_description: content, 
        tone: parseInt(document.getElementById('tone-slider').value) 
    });
    
    if (data.ok) {
        outputText.innerHTML = `<pre style="white-space: pre-wrap; font-size: 0.8rem; font-family: 'JetBrains Mono';">${data.resume}</pre>`;
        atsScoreDisplay.innerText = `${data.ats}%`;
        // SVG Ring animation
        const offset = 282.6 - (282.6 * (data.ats / 100));
        ringFill.style.strokeDashoffset = offset;
        btnGenerate.innerText = "SYNCHRONIZE & MIRROR";
    } else {
        outputText.innerHTML = `<div class="error-msg" style="color: #ff4444; padding: 1rem; border: 1px solid #ff4444;">ERROR: ${data.error}</div>`;
        btnGenerate.innerText = "RETRY SYNCHRONIZATION";
    }
});

// Tab switching
document.querySelectorAll('.m-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.m-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        // Logic to switch view would go here if data exists
    });
});

// Uptime update
setInterval(() => {
    const uptimeEl = document.getElementById('uptime');
    let [h, m, s] = uptimeEl.innerText.split(':').map(Number);
    s++;
    if(s >= 60) { s = 0; m++; }
    if(m >= 60) { m = 0; h++; }
    uptimeEl.innerText = [h, m, s].map(v => String(v).padStart(2, '0')).join(':');
}, 1000);

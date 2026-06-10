/* ══════════════════════════════════════════════════════
   NOVA — app.js  |  Frontend controller (Stateless REST)
══════════════════════════════════════════════════════ */

// ── DOM refs ──────────────────────────────────────────
const sdot      = document.getElementById('sdot');
const slabel    = document.getElementById('slabel');
const novaStatus= document.getElementById('novaStatus');
const tclock    = document.getElementById('tclock');
const orbWrap   = document.getElementById('orbWrap');
const micBtn    = document.getElementById('micBtn');
const svgMic    = document.getElementById('svgMic');
const svgStop   = document.getElementById('svgStop');
const micLabel  = document.getElementById('micLabel');
const txtBox    = document.getElementById('txtBox');
const txtSend   = document.getElementById('txtSend');
const log       = document.getElementById('log');
const logEmpty  = document.getElementById('logEmpty');
const waveRow   = document.getElementById('waveRow');
const scLatency = document.getElementById('scLatency');
const scLatBar  = document.getElementById('scLatBar');
const scSession = document.getElementById('scSession');
const scSessBar = document.getElementById('scSessBar');

// ── State ─────────────────────────────────────────────
let micActive    = false;
let waveRAF      = null;
let sessionStart = Date.now();
let lastCmd      = null;
let recognition  = null;

// ── Initialize Speech Recognition (Frontend STT) ──────
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-IN'; // Uses user's native language locale

  recognition.onstart = () => {
    micActive = true;
    micBtn.classList.add('active');
    svgMic.style.display  = 'none';
    svgStop.style.display = 'block';
    micLabel.textContent  = 'LISTENING (TAP TO STOP)';
    applyState('listening');
  };

  recognition.onresult = (event) => {
    const lastResult = event.results[event.results.length - 1];
    if (lastResult.isFinal) {
      let text = lastResult[0].transcript.trim();
      console.log("[STT Heard]:", text);
      
      if (text) {
        lastCmd = Date.now();
        setMicOff();
        applyState('processing');
        addEntry('you', text);
        sendToNova(text);
      }
    }
  };

  recognition.onerror = (event) => {
    console.error('[STT Error]', event.error);
    if (event.error === 'not-allowed') {
       applyState('error');
       micLabel.textContent = 'MIC PERMISSION DENIED';
       setMicOff();
       micActive = false;
    }
  };

  recognition.onend = () => {
    if (micActive) {
      setMicOff();
      applyState('idle');
    }
  };
}

// ── Build bottom wave bars ────────────────────────────
const BARS = 58;
const barEls = [];
for (let i = 0; i < BARS; i++) {
  const b = document.createElement('div');
  b.className = 'wbar'; b.style.height = '3px';
  waveRow.appendChild(b); barEls.push(b);
}
const barTargets = barEls.map(() => 3);

// ── Particle canvas ───────────────────────────────────
(function particles() {
  const cv = document.getElementById('cvs');
  const cx = cv.getContext('2d');
  let W, H, pts;
  const resize = () => { W = cv.width = innerWidth; H = cv.height = innerHeight; };
  const mkPts  = () => pts = Array.from({length:110}, () => ({
    x: Math.random()*W, y: Math.random()*H,
    vx:(Math.random()-.5)*.3, vy:(Math.random()-.5)*.3,
    r: Math.random()*1.4+.3,  a: Math.random()*.42+.1,
  }));
  const draw = () => {
    cx.clearRect(0,0,W,H);
    for (let i=0;i<pts.length;i++) for (let j=i+1;j<pts.length;j++) {
      const dx=pts[i].x-pts[j].x, dy=pts[i].y-pts[j].y;
      const d=Math.sqrt(dx*dx+dy*dy);
      if (d<115) {
        cx.strokeStyle=`rgba(0,212,255,${(1-d/115)*.1})`;
        cx.lineWidth=.5; cx.beginPath();
        cx.moveTo(pts[i].x,pts[i].y); cx.lineTo(pts[j].x,pts[j].y); cx.stroke();
      }
    }
    pts.forEach(p=>{
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0)p.x=W; if(p.x>W)p.x=0;
      if(p.y<0)p.y=H; if(p.y>H)p.y=0;
      cx.beginPath(); cx.arc(p.x,p.y,p.r,0,Math.PI*2);
      cx.fillStyle=`rgba(0,212,255,${p.a})`; cx.fill();
    });
    requestAnimationFrame(draw);
  };
  window.addEventListener('resize',()=>{resize();mkPts();});
  resize(); mkPts(); draw();
})();

// ── Clock ─────────────────────────────────────────────
setInterval(() => {
  const n=new Date();
  tclock.textContent =
    `${String(n.getHours()).padStart(2,'0')}:`+
    `${String(n.getMinutes()).padStart(2,'0')}:`+
    `${String(n.getSeconds()).padStart(2,'0')}`;
}, 1000);

// ── Session timer ─────────────────────────────────────
setInterval(() => {
  const s = Math.floor((Date.now()-sessionStart)/1000);
  scSession.textContent =
    `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
  scSessBar.style.width = Math.min(s/3600*100,100)+'%';
}, 1000);

// ── Waveform animator ─────────────────────────────────
function startWave(mode) {
  if (waveRAF) cancelAnimationFrame(waveRAF);
  const spk = (mode==='speaking');
  const tick = () => {
    barEls.forEach((b,i) => {
      const cx   = BARS/2;
      const dist = Math.abs(i-cx)/cx;
      const maxH = spk ? (1-dist*.42)*46+5 : (1-dist*.72)*28+3;
      barTargets[i] += (Math.random()-.5)*9;
      barTargets[i]  = Math.max(3, Math.min(barTargets[i], maxH));
      b.style.height = barTargets[i]+'px';
    });
    waveRAF = requestAnimationFrame(tick);
  };
  tick();
}
function stopWave() {
  if (waveRAF) { cancelAnimationFrame(waveRAF); waveRAF=null; }
  barEls.forEach(b => b.style.height='3px');
}

// ── Apply visual state ────────────────────────────────
const STATE_MAP = {
  idle:       { label:'NOVA ONLINE',     sub:'VOICE ASSISTANT ONLINE', dc:'#00d4ff', body:'idle' },
  listening:  { label:'LISTENING…',      sub:'PROCESSING AUDIO INPUT', dc:'#00ff88', body:'listening' },
  speaking:   { label:'SPEAKING…',       sub:'GENERATING RESPONSE',    dc:'#4fc3f7', body:'speaking' },
  processing: { label:'PROCESSING…',     sub:'ANALYZING COMMAND',      dc:'#ffd700', body:'processing' },
  error:      { label:'ERROR',           sub:'PLEASE TRY AGAIN',       dc:'#ff4455', body:'idle' },
};

function applyState(s) {
  const cfg = STATE_MAP[s] || STATE_MAP.idle;

  // pill
  slabel.textContent = cfg.label;
  sdot.style.cssText = `background:${cfg.dc};box-shadow:0 0 8px ${cfg.dc}`;

  // sub-label
  novaStatus.textContent = cfg.sub;

  // body class → controls wave bar colours
  document.body.className = cfg.body;

  // orb rings
  orbWrap.className = 'orb-wrap ' + s;

  // waveform
  (s==='speaking'||s==='listening') ? startWave(s) : stopWave();

  // mic button availability
  const busy = (s==='speaking'||s==='processing');
  micBtn.disabled = busy;
  if (busy) {
    setMicOff();
    try { recognition.stop(); } catch(e){}
    micLabel.textContent = s==='speaking' ? 'NOVA IS SPEAKING…' : 'PROCESSING…';
  } else {
    micLabel.textContent = 'TAP TO SPEAK';
  }
}

// ── Mic button helpers ────────────────────────────────
function setMicOn() {
  micActive = true;
  micBtn.classList.add('active');
  svgMic.style.display  = 'none';
  svgStop.style.display = 'block';
  micLabel.textContent  = 'TAP TO STOP';
}
function setMicOff() {
  micActive = false;
  micBtn.classList.remove('active');
  svgMic.style.display  = 'block';
  svgStop.style.display = 'none';
  micLabel.textContent  = 'TAP TO SPEAK';
}

// ── Mic button click ──────────────────────────────────
micBtn.addEventListener('click', () => {
  if (micBtn.disabled) return;
  if (!recognition) {
    alert("Speech Recognition is not supported in this browser. Please use Google Chrome.");
    return;
  }
  
  if (micActive) {
    micActive = false;
    recognition.stop();
  } else {
    try {
      recognition.start();
    } catch(e) {
      console.error(e);
    }
  }
});

// ── Text input ────────────────────────────────────────
function sendText() {
  const v = txtBox.value.trim();
  if (!v) return;
  txtBox.value = '';
  lastCmd = Date.now();
  applyState('processing');
  addEntry('you', v);
  sendToNova(v);
}
txtSend.addEventListener('click', sendText);
txtBox.addEventListener('keydown', e => { if (e.key==='Enter') sendText(); });

// ── Conversation log ──────────────────────────────────
let firstMessage = true;
function addEntry(role, text) {
  if (firstMessage) {
    log.innerHTML = '';  // remove placeholder
    firstMessage = false;
  }
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;
  const who = document.createElement('div');
  who.className = 'who';
  who.textContent = role==='you' ? '▶  YOU' : '◈  NOVA';
  const body = document.createElement('div');
  body.textContent = text;
  wrap.appendChild(who);
  wrap.appendChild(body);
  log.appendChild(wrap);
  log.scrollTop = log.scrollHeight;
}

// ── REST API Call ─────────────────────────────────────
async function sendToNova(text) {
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text })
    });
    
    if (!response.ok) throw new Error("Network response was not ok");
    
    const data = await response.json();
    handleNovaReply(data.reply);
    
    if (lastCmd) {
      const ms = Date.now() - lastCmd;
      scLatency.textContent = ms + 'ms';
      scLatBar.style.width  = Math.max(10, Math.min(100, 100-ms/30)) + '%';
    }
  } catch (error) {
    console.error("Error communicating with Nova:", error);
    applyState('error');
    setTimeout(() => applyState('idle'), 3000);
  }
}

// ── TTS Handling ─────────────────────────────────────
function handleNovaReply(text) {
  addEntry('nova', text);
  
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.05;
    u.pitch = 1.1;
    
    const voices = window.speechSynthesis.getVoices();
    let fv = voices.find(v => v.name.toLowerCase().includes('zira') || v.name.toLowerCase().includes('female') || v.name.toLowerCase().includes('susan'));
    if (!fv) fv = voices.find(v => v.lang.includes('en'));
    if (fv) u.voice = fv;
    
    u.onstart = () => applyState('speaking');
    u.onend   = () => applyState('idle');
    u.onerror = () => applyState('idle');
    
    window.speechSynthesis.speak(u);
  } else {
    applyState('speaking');
    setTimeout(() => applyState('idle'), text.length * 50 + 1000);
  }
}

// ── Init ──────────────────────────────────────────────
applyState('idle');
console.log('[NOVA] Frontend ready.');

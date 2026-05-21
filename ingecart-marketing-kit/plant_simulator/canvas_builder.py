"""HTML5 Canvas builder for the Corrugated Plant Simulator.

Generates a self-contained HTML string with embedded JavaScript
simulation engine that runs at 60fps in the browser/Streamlit component.
"""
from __future__ import annotations

import json
from typing import Any, Dict


def build_canvas_html(config_dict: Dict[str, Any], height: int = 620) -> str:
    """
    Build a complete self-contained HTML simulation page.

    Parameters
    ----------
    config_dict : dict
        Output of PlantConfig.to_canvas_config()
    height : int
        Desired component height in px

    Returns
    -------
    str  : full HTML string ready for st.components.v1.html()
    """
    config_json = json.dumps(config_dict, ensure_ascii=False)
    return _HTML_TEMPLATE.replace("__SIMULATION_CONFIG__", config_json).replace(
        "__CANVAS_HEIGHT__", str(height)
    )


# ---------------------------------------------------------------------------
# HTML template with full JavaScript simulation engine
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0d1117;display:flex;flex-direction:column;align-items:center;
       font-family:'Segoe UI',monospace;overflow:hidden;user-select:none;}
  #simCanvas{display:block;cursor:crosshair;}
  #ctrlBar{display:flex;align-items:center;gap:8px;padding:6px 12px;
            background:#1a1d24;border-top:1px solid #FF6A00;width:100%;flex-wrap:wrap;}
  .btn{background:#1a1d24;border:1px solid #FF6A00;color:#FF6A00;padding:4px 14px;
       border-radius:4px;cursor:pointer;font-size:11px;font-weight:700;letter-spacing:.5px;
       transition:background .15s;}
  .btn:hover,.btn.active{background:#FF6A00;color:#0d1117;}
  .sep{width:1px;height:18px;background:#333;margin:0 4px;}
  .lbl{color:#7e848e;font-size:11px;font-weight:600;letter-spacing:.4px;}
  #simTime{color:#FF6A00;font-size:13px;font-weight:700;min-width:80px;}
  #tooltip{position:fixed;background:rgba(26,29,36,.95);border:1px solid #FF6A00;
            color:#f4f5f7;padding:8px 12px;border-radius:6px;font-size:11px;
            pointer-events:none;display:none;z-index:999;max-width:200px;line-height:1.5;}
</style>
</head>
<body>
<canvas id="simCanvas" width="1100" height="560"></canvas>
<div id="ctrlBar">
  <span class="lbl">VELOCIDAD:</span>
  <button class="btn" id="b1x" onclick="setSpeed(1)">1×</button>
  <button class="btn" id="b5x" onclick="setSpeed(5)">5×</button>
  <button class="btn active" id="b10x" onclick="setSpeed(10)">10×</button>
  <button class="btn" id="b30x" onclick="setSpeed(30)">30×</button>
  <div class="sep"></div>
  <button class="btn" id="btnPause" onclick="togglePause()">⏸ PAUSAR</button>
  <button class="btn" onclick="resetSim()">↺ RESET</button>
  <div class="sep"></div>
  <span id="simTime">⏱ 00:00:00</span>
  <div class="sep"></div>
  <span class="lbl" id="statusMsg">▶ SIMULANDO</span>
</div>
<div id="tooltip"></div>

<script>
// =============================================================
//  CORRUGATED PLANT SIMULATOR — Canvas Engine v2.0
//  INGECART Digital Twin  |  2026
// =============================================================

const CFG = __SIMULATION_CONFIG__;

const cv = document.getElementById('simCanvas');
const ctx = cv.getContext('2d');
const W = cv.width, H = cv.height;

// ---- COLOURS ----
const C = {
  bg:'#0d1117', card:'#1a1d24', cardBorder:'#252830',
  accent:'#FF6A00', accentDim:'rgba(255,106,0,0.3)',
  green:'#4fc17b', greenDim:'rgba(79,193,123,0.2)',
  yellow:'#f0c040', yellowDim:'rgba(240,192,64,0.2)',
  red:'#e05555', redDim:'rgba(224,85,85,0.2)',
  blue:'#4a90d9', blueDim:'rgba(74,144,217,0.2)',
  text:'#f4f5f7', muted:'#7e848e', dark:'#05070b',
  grid:'rgba(255,255,255,0.03)'
};

// ---- SIMULATION STATE ----
let simT = 0;        // simulated seconds
let speed = 10;
let paused = false;
let lastTs = 0;
let simDuration = (CFG.simDurationHours || 8) * 3600;
let finished = false;

// ---- METRICS ----
let met = {
  m2: 0, units: 0,
  corrEff: 0.87, oee: 0.82,
  fltUtil: 0.0, bufOcc: 0.0,
  bottlenecks: []
};

// ---- LAYOUT ----
// Equipment and connection positions depending on plant type
let EQUIP = [];
let CONNECTIONS = [];
let ZONES = {};
let forklifts = [];
let conveyorParticles = [];
let entities = [];
let taskQueue = [];
let machineStates = {};

// =============================================================
//  LAYOUT BUILDER
// =============================================================
function buildLayout() {
  const pt = CFG.plantType;
  EQUIP = [];
  CONNECTIONS = [];
  ZONES = {};

  if (pt === 'corrugator_converter') {
    EQUIP = [
      {id:'roll_store',   label:'ALMACÉN\nBOBINAS',  x:18,  y:120, w:105, h:270, type:'storage',  color:C.card, border:C.blue,   cap:CFG.corrugator?.rollStoreCapacity||100, fill:0.75},
      {id:'corrugadora',  label:'CORRUGADORA',        x:178, y:175, w:235, h:100, type:'machine',  color:C.card, border:C.green,  eff:0.873, state:'running'},
      {id:'buffer',       label:'BUFFER\nPLANO',      x:468, y:120, w:90,  h:270, type:'storage',  color:C.card, border:C.blue,   cap:CFG.bufferCapacity||150, fill:0.35},
      {id:'output',       label:'ALMACÉN\nSALIDA',    x:835, y:155, w:90,  h:200, type:'storage',  color:C.card, border:C.blue,   cap:100, fill:0.1},
      {id:'expedition',   label:'EXPEDICIÓN',         x:978, y:195, w:82,  h:120, type:'loading',  color:'#1a1209', border:C.accent, cap:50, fill:0.05},
    ];
    // Converters (stacked)
    const convs = CFG.converters || [];
    const cStartY = 120;
    const cH = convs.length > 0 ? Math.min(80, 250/convs.length) : 80;
    convs.forEach((cv, i) => {
      EQUIP.push({
        id: cv.id,
        label: cv.id+'\n'+(cv.type||'FLEXO').substring(0,8).toUpperCase(),
        x: 618, y: cStartY + i*(cH+12), w: 155, h: cH,
        type:'machine', color:C.card, border:C.green,
        eff: cv.availability||0.90, state:'running',
        speed: cv.speedUdsPerHour
      });
    });
    CONNECTIONS = [
      {from:'roll_store',  to:'corrugadora', type:'forklift', label:'bobinas'},
      {from:'corrugadora', to:'buffer',      type:'conveyor', label:'plano →'},
      {from:'buffer',      to:'converters',  type:'track',    label:'tracks'},
      {from:'converters',  to:'output',      type:'conveyor', label:'→ salida'},
      {from:'output',      to:'expedition',  type:'forklift', label:'expedir'},
    ];
    ZONES = {
      rollPickup:   {x:123, y:255},
      corrIn:       {x:178, y:225},
      corrOut:      {x:413, y:225},
      bufferIn:     {x:468, y:255},
      bufferOut:    {x:558, y:255},
      convertersIn: {x:618, y:220},
      outputIn:     {x:835, y:235},
      expedIn:      {x:978, y:255},
    };
  } else if (pt === 'corrugator_only') {
    EQUIP = [
      {id:'roll_store',  label:'ALMACÉN\nBOBINAS', x:18,  y:150, w:110, h:240, type:'storage', color:C.card, border:C.blue,  cap:CFG.corrugator?.rollStoreCapacity||100, fill:0.75},
      {id:'corrugadora', label:'CORRUGADORA',       x:195, y:185, w:280, h:110, type:'machine', color:C.card, border:C.green, eff:0.873, state:'running'},
      {id:'buffer',      label:'ALMACÉN PLANO',     x:545, y:150, w:200, h:240, type:'storage', color:C.card, border:C.blue,  cap:200, fill:0.20},
      {id:'expedition',  label:'EXPEDICIÓN',        x:820, y:200, w:90,  h:140, type:'loading', color:'#1a1209', border:C.accent, cap:50, fill:0.05},
    ];
    CONNECTIONS = [
      {from:'roll_store',  to:'corrugadora', type:'forklift', label:'bobinas'},
      {from:'corrugadora', to:'buffer',      type:'conveyor', label:'plano →'},
      {from:'buffer',      to:'expedition',  type:'forklift', label:'expedir'},
    ];
    ZONES = {
      rollPickup:{x:128,y:270}, corrIn:{x:195,y:240}, corrOut:{x:475,y:240},
      bufferIn:{x:545,y:270}, bufferOut:{x:745,y:270}, expedIn:{x:820,y:270}
    };
  } else {
    // converter_only
    EQUIP = [
      {id:'input_store', label:'ALMACÉN\nENTRADA', x:18,  y:140, w:105, h:260, type:'storage', color:C.card, border:C.blue,   cap:200, fill:0.70},
      {id:'buffer',      label:'BUFFER\nINTERMEDIO',x:185, y:140, w:90,  h:260, type:'storage', color:C.card, border:C.blue,   cap:CFG.bufferCapacity||150, fill:0.45},
      {id:'output',      label:'ALMACÉN\nSALIDA',  x:800, y:155, w:90,  h:200, type:'storage', color:C.card, border:C.blue,   cap:100, fill:0.05},
      {id:'expedition',  label:'EXPEDICIÓN',        x:950, y:200, w:85,  h:120, type:'loading', color:'#1a1209', border:C.accent, cap:50, fill:0.02},
    ];
    const convs = CFG.converters || [];
    convs.forEach((cv, i) => {
      EQUIP.push({
        id:cv.id, label:cv.id+'\n'+(cv.type||'FLEXO').substring(0,8).toUpperCase(),
        x:345, y:140+i*100, w:155, h:80,
        type:'machine', color:C.card, border:C.green,
        eff:cv.availability||0.90, state:'running', speed:cv.speedUdsPerHour
      });
    });
    CONNECTIONS = [
      {from:'input_store', to:'buffer',     type:'forklift', label:'entrada'},
      {from:'buffer',      to:'converters', type:'track',    label:'tracks'},
      {from:'converters',  to:'output',     type:'conveyor', label:'→ salida'},
      {from:'output',      to:'expedition', type:'forklift', label:'expedir'},
    ];
    ZONES = {
      inputPickup:{x:123,y:270}, bufferIn:{x:185,y:270},
      bufferOut:{x:275,y:270}, convertersIn:{x:345,y:220},
      outputIn:{x:800,y:255}, expedIn:{x:950,y:255}
    };
  }

  // Initialize machine states
  machineStates = {};
  EQUIP.forEach(eq => {
    if (eq.type === 'machine') {
      machineStates[eq.id] = {
        state: 'running',
        eff: eq.eff || 0.87,
        produced: 0,
        blockedSec: 0,
        setupSec: 0,
        runSec: 0,
        nextSetup: 14400 + Math.random()*3600,
        setupDuration: 1800,
        maintenanceDuration: 0,
        statusTimer: 0
      };
    }
    if (eq.type === 'storage') {
      eq.currentFill = eq.fill * (eq.cap || 100);
    }
  });
}

// =============================================================
//  FORKLIFT CLASS
// =============================================================
class Forklift {
  constructor(id, homeX, homeY, role) {
    this.id = id;
    this.x = homeX + Math.random()*10-5;
    this.y = homeY;
    this.homeX = homeX;
    this.homeY = homeY;
    this.role = role; // 'rolls', 'plano', 'output'
    this.state = 'idle'; // idle, toPickup, loading, toDropoff, unloading
    this.cargo = null;
    this.targetX = homeX;
    this.targetY = homeY;
    this.speed = 100; // px/sim-sec
    this.loadTimer = 0;
    this.activeSec = 0;
    this.totalSec = 0;
    this.task = null;
    this.angle = 0;
    this.trailX = homeX;
    this.trailY = homeY;
  }

  update(dt) {
    this.totalSec += dt;
    if (this.state === 'idle') {
      const task = getTask(this.role);
      if (task) {
        this.task = task;
        this.targetX = task.px;
        this.targetY = task.py;
        this.state = 'toPickup';
      } else {
        // Drift back home
        this.x += (this.homeX - this.x) * Math.min(dt * 0.5, 0.3);
        this.y += (this.homeY - this.y) * Math.min(dt * 0.5, 0.3);
      }
    } else if (this.state === 'toPickup') {
      const done = this.moveToward(this.task.px, this.task.py, dt);
      this.activeSec += dt;
      if (done) { this.state = 'loading'; this.loadTimer = 3.5; }
    } else if (this.state === 'loading') {
      this.loadTimer -= dt;
      this.activeSec += dt;
      if (this.loadTimer <= 0) {
        this.cargo = this.task.cargo;
        this.targetX = this.task.dx;
        this.targetY = this.task.dy;
        this.state = 'toDropoff';
      }
    } else if (this.state === 'toDropoff') {
      const done = this.moveToward(this.task.dx, this.task.dy, dt);
      this.activeSec += dt;
      if (done) { this.state = 'unloading'; this.loadTimer = 2.5; }
    } else if (this.state === 'unloading') {
      this.loadTimer -= dt;
      this.activeSec += dt;
      if (this.loadTimer <= 0) {
        completeTask(this.task);
        this.task = null;
        this.cargo = null;
        this.state = 'idle';
      }
    }
  }

  moveToward(tx, ty, dt) {
    const dx = tx - this.x, dy = ty - this.y;
    const dist = Math.hypot(dx, dy);
    if (dist < 3) { this.x = tx; this.y = ty; return true; }
    this.angle = Math.atan2(dy, dx);
    const step = Math.min(this.speed * dt, dist);
    this.x += (dx/dist) * step;
    this.y += (dy/dist) * step;
    this.trailX = this.x - Math.cos(this.angle)*18;
    this.trailY = this.y - Math.sin(this.angle)*18;
    return false;
  }

  get utilization() {
    return this.totalSec > 0 ? (this.activeSec / this.totalSec) * 100 : 0;
  }

  draw() {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.angle);
    const isActive = this.state !== 'idle';
    const bodyColor = isActive ? C.accent : '#555';
    // Body
    ctx.fillStyle = bodyColor;
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 0.8;
    ctx.beginPath();
    ctx.roundRect(-12, -7, 24, 14, 3);
    ctx.fill(); ctx.stroke();
    // Cabin
    ctx.fillStyle = isActive ? '#ff8833' : '#777';
    ctx.beginPath();
    ctx.rect(-10, -5, 10, 10);
    ctx.fill();
    // Forks
    ctx.fillStyle = '#bbb';
    ctx.fillRect(12, -5, 10, 2);
    ctx.fillRect(12, 2, 10, 2);
    // Cargo indicator
    if (this.cargo) {
      ctx.fillStyle = this.cargo === 'roll' ? C.green : C.blue;
      ctx.beginPath();
      ctx.arc(0, 0, 5, 0, Math.PI*2);
      ctx.fill();
    }
    // ID
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 7px Segoe UI';
    ctx.textAlign = 'center';
    ctx.fillText('F'+(this.id+1), -3, 3);
    ctx.restore();
  }
}

// =============================================================
//  TASK QUEUE
// =============================================================
function getTask(role) {
  // Generate tasks based on zone states and buffer levels
  if (finished) return null;
  if (role === 'rolls') {
    const rs = getEquip('roll_store');
    const corr = getEquip('corrugadora');
    if (rs && corr && rs.currentFill > 0 && simT % 180 < 1) {
      return {
        role:'rolls', cargo:'roll',
        px: rs.x + rs.w, py: rs.y + rs.h/2 + Math.random()*40-20,
        dx: corr.x, dy: corr.y + corr.h/2
      };
    }
  } else if (role === 'plano') {
    const buf = getEquip('buffer');
    const converters = EQUIP.filter(e => e.id.startsWith('C'));
    if (buf && converters.length && buf.currentFill > 5 && simT % 120 < 1) {
      const cv = converters[Math.floor(Math.random()*converters.length)];
      return {
        role:'plano', cargo:'pallet',
        px: buf.x + buf.w, py: buf.y + buf.h*0.3 + Math.random()*buf.h*0.4,
        dx: cv.x, dy: cv.y + cv.h/2
      };
    }
  } else if (role === 'output' || role === 'input') {
    const out = getEquip('output');
    const exp = getEquip('expedition');
    if (out && exp && out.currentFill > 3 && simT % 240 < 1) {
      return {
        role:'output', cargo:'pallet',
        px: out.x + out.w/2, py: out.y + out.h*0.5,
        dx: exp.x + exp.w/2, dy: exp.y + exp.h/2
      };
    }
    // Also handle input store
    const inp = getEquip('input_store');
    const buf = getEquip('buffer');
    if (inp && buf && inp.currentFill > 5 && simT % 150 < 1) {
      return {
        role:'input', cargo:'pallet',
        px: inp.x + inp.w, py: inp.y + inp.h/2,
        dx: buf.x, dy: buf.y + buf.h/2
      };
    }
  }
  return null;
}

function completeTask(task) { /* tasks complete themselves */ }

function getEquip(id) {
  return EQUIP.find(e => e.id === id);
}

// =============================================================
//  CONVEYOR PARTICLES
// =============================================================
function spawnConveyorParticles() {
  // Corrugadora → buffer: horizontal belt
  const corr = getEquip('corrugadora');
  const buf = getEquip('buffer');
  if (corr && buf) {
    const x1 = corr.x + corr.w, y1 = corr.y + corr.h/2;
    const x2 = buf.x, y2 = buf.y + buf.h/2;
    for (let i = 0; i < 8; i++) {
      conveyorParticles.push({
        x1, y1, x2, y2,
        t: Math.random(),
        type: 'roll_belt',
        color: C.accent
      });
    }
  }
  // Converters → output
  const out = getEquip('output');
  if (out) {
    const convs = EQUIP.filter(e => e.id.startsWith('C'));
    convs.forEach(cv => {
      for (let i = 0; i < 4; i++) {
        conveyorParticles.push({
          x1: cv.x + cv.w, y1: cv.y + cv.h/2,
          x2: out.x, y2: out.y + out.h/2,
          t: Math.random(),
          type: 'box_belt',
          color: C.blue
        });
      }
    });
  }
}

// =============================================================
//  FORKLIFT INITIALIZATION
// =============================================================
function initForklifts() {
  forklifts = [];
  const n = CFG.transport?.numForklifts || 3;
  const pt = CFG.plantType;
  const roles = pt === 'corrugator_only'
    ? ['rolls','output']
    : pt === 'converter_only'
    ? ['input','output','output']
    : ['rolls','plano','output','output','plano'];

  for (let i = 0; i < n; i++) {
    const role = roles[i % roles.length];
    let hx, hy;
    if (role === 'rolls') { hx = 155; hy = 260 + i*15; }
    else if (role === 'plano') { hx = 555; hy = 260 + i*15; }
    else { hx = 870; hy = 260 + i*15; }
    forklifts.push(new Forklift(i, hx, hy, role));
  }
}

// =============================================================
//  SIMULATION UPDATE
// =============================================================
function update(dt) {
  if (simT >= simDuration) { finished = true; return; }
  simT += dt;

  // --- Update machine states ---
  EQUIP.forEach(eq => {
    if (eq.type !== 'machine') return;
    const ms = machineStates[eq.id];
    if (!ms) return;

    if (ms.state === 'maintenance') {
      ms.maintenanceDuration -= dt;
      if (ms.maintenanceDuration <= 0) { ms.state = 'running'; eq.border = C.green; }
      return;
    }
    if (ms.state === 'setup') {
      ms.setupSec += dt;
      ms.statusTimer -= dt;
      if (ms.statusTimer <= 0) { ms.state = 'running'; eq.border = C.green; }
      return;
    }
    if (ms.state === 'running') {
      ms.runSec += dt;
      // Random maintenance
      if (Math.random() < 0.00015 * dt) {
        ms.state = 'maintenance';
        ms.maintenanceDuration = 360 + Math.random()*600;
        eq.border = C.red;
        return;
      }
      // Scheduled setup (converters only)
      if (eq.id.startsWith('C') && simT > ms.nextSetup) {
        ms.state = 'setup';
        ms.statusTimer = 1800 + Math.random()*600;
        ms.nextSetup = simT + 14400 + Math.random()*3600;
        eq.border = C.yellow;
        return;
      }
      eq.border = C.green;
      // Production
      ms.produced += (ms.eff * (eq.speed || 15000) * dt / 3600);
    }
    if (ms.state === 'blocked') {
      ms.blockedSec += dt;
      eq.border = C.red;
      // Unblock if downstream storage freed up
      const out = getEquip('output');
      if (!out || out.currentFill < (out.cap||100)*0.85) {
        ms.state = 'running'; eq.border = C.green;
      }
    }
  });

  // --- Update storage levels ---
  EQUIP.forEach(eq => {
    if (eq.type !== 'storage') return;
    const cap = eq.cap || 100;

    if (eq.id === 'roll_store') {
      // Consumption by corrugator
      const corr = machineStates['corrugadora'];
      if (corr?.state === 'running') {
        const consumption = (CFG.corrugator?.rollsPerHour || 2.5) * dt / 3600;
        eq.currentFill = Math.max(0, eq.currentFill - consumption);
        // Replenish when low
        if (eq.currentFill < cap * 0.2) eq.currentFill += cap * 0.4;
      }
    } else if (eq.id === 'corrugadora') {
      // handled above
    } else if (eq.id === 'buffer') {
      // Inflow from corrugator
      const corr = machineStates['corrugadora'];
      if (corr?.state === 'running') {
        const m2ph = CFG.corrugator?.m2PerHour || 15000;
        const palletsIn = (m2ph / 200) * dt / 3600;
        eq.currentFill = Math.min(cap, eq.currentFill + palletsIn);
      }
      // Outflow to converters
      const convs = EQUIP.filter(e => e.id.startsWith('C'));
      const activeConvs = convs.filter(c => machineStates[c.id]?.state === 'running');
      if (activeConvs.length > 0) {
        const totalM2ph = activeConvs.reduce((s, c) => s + (c.speed||1000)*0.35, 0);
        const palletsOut = (totalM2ph / 200) * dt / 3600;
        eq.currentFill = Math.max(0, eq.currentFill - palletsOut);
        if (eq.currentFill <= 0) {
          // Starvation — mark converters
          convs.forEach(c => { if (machineStates[c.id]) { eq.border = C.red; } });
        }
      }
      // Block corrugator if full
      const corrEq = getEquip('corrugadora');
      if (corrEq && machineStates['corrugadora']) {
        if (eq.currentFill >= cap * 0.95) {
          machineStates['corrugadora'].state = 'blocked';
          corrEq.border = C.red;
        }
      }
    } else if (eq.id === 'input_store') {
      if (eq.currentFill < cap * 0.2) eq.currentFill = Math.min(cap, eq.currentFill + cap*0.3);
      const buf = getEquip('buffer');
      if (buf && buf.currentFill < (buf.cap||150)*0.5) {
        const flow = Math.min(eq.currentFill, 5*dt/3600*1000);
        eq.currentFill -= flow;
        buf.currentFill = Math.min(buf.cap||150, buf.currentFill + flow);
      }
    } else if (eq.id === 'output') {
      // Inflow from converters
      const convs = EQUIP.filter(e => e.id.startsWith('C'));
      convs.forEach(cv => {
        const ms = machineStates[cv.id];
        if (ms?.state === 'running') {
          const palletsOut = (cv.speed||1000)*dt/3600/50;
          eq.currentFill = Math.min(cap, eq.currentFill + palletsOut);
          if (eq.currentFill >= cap * 0.9) {
            ms.state = 'blocked'; cv.border = C.red;
          }
        }
      });
      // Truck pickup every ~30 min
      if (simT % 1800 < dt) eq.currentFill = Math.max(0, eq.currentFill - cap*0.4);
    } else if (eq.id === 'expedition') {
      // Minor fill over time
      eq.currentFill = Math.min(cap, eq.currentFill + 0.01*dt);
      if (simT % 3600 < dt) eq.currentFill = Math.max(0, eq.currentFill - cap*0.6);
    }
  });

  // --- Update metrics ---
  const corrMs = machineStates['corrugadora'];
  if (corrMs) {
    met.m2 = corrMs.produced;
    met.corrEff = corrMs.runSec > 0
      ? (corrMs.runSec / (corrMs.runSec + corrMs.blockedSec + corrMs.setupSec + corrMs.maintenanceDuration)) * 100
      : 87;
  }
  const allMachines = Object.values(machineStates);
  met.oee = allMachines.length > 0
    ? allMachines.reduce((s, m) => s + (m.eff*100), 0) / allMachines.length
    : 82;
  const buf = getEquip('buffer');
  met.bufOcc = buf ? (buf.currentFill / (buf.cap||150)) * 100 : 0;
  met.fltUtil = forklifts.length > 0
    ? forklifts.reduce((s, f) => s + f.utilization, 0) / forklifts.length
    : 0;
  met.units = EQUIP.filter(e=>e.id.startsWith('C'))
    .reduce((s, e) => s + (machineStates[e.id]?.produced||0), 0);

  // --- Update conveyor particles ---
  conveyorParticles.forEach(p => {
    p.t = (p.t + dt * 0.08) % 1;
  });

  // --- Update forklifts ---
  forklifts.forEach(f => f.update(dt));
}

// =============================================================
//  DRAWING
// =============================================================
function draw() {
  // Background + grid
  ctx.fillStyle = C.bg;
  ctx.fillRect(0, 0, W, H);
  drawGrid();
  drawConnections();
  drawEquipment();
  drawConveyorParticles();
  forklifts.forEach(f => f.draw());
  drawKPIPanel();
  if (finished) drawFinishedOverlay();
}

function drawGrid() {
  ctx.strokeStyle = C.grid;
  ctx.lineWidth = 0.5;
  for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
  for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }
}

function drawConnections() {
  CONNECTIONS.forEach(conn => {
    const from = getEquip(conn.from === 'converters' ? EQUIP.find(e=>e.id.startsWith('C'))?.id : conn.from);
    const to = getEquip(conn.to === 'converters' ? EQUIP.find(e=>e.id.startsWith('C'))?.id : conn.to);
    if (!from || !to) return;

    const x1 = from.x + from.w, y1 = from.y + from.h/2;
    const x2 = to.x, y2 = to.y + to.h/2;

    if (conn.type === 'conveyor') {
      // Animated belt
      const len = Math.hypot(x2-x1, y2-y1);
      const angle = Math.atan2(y2-y1, x2-x1);
      ctx.save();
      ctx.translate(x1, y1);
      ctx.rotate(angle);
      ctx.fillStyle = '#2a2a3a';
      ctx.fillRect(-2, -6, len+4, 12);
      ctx.strokeStyle = '#444';
      ctx.lineWidth = 1;
      ctx.strokeRect(-2, -6, len+4, 12);
      // Rollers
      for (let i = 10; i < len; i += 20) {
        ctx.strokeStyle = '#555';
        ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(i, -6); ctx.lineTo(i, 6); ctx.stroke();
      }
      // Belt motion
      const offset = (simT * 30) % 20;
      ctx.strokeStyle = C.accent;
      ctx.lineWidth = 2;
      ctx.setLineDash([8, 12]);
      ctx.lineDashOffset = -offset;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(len, 0); ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();
    } else if (conn.type === 'track') {
      // Dashed track lines
      ctx.save();
      ctx.strokeStyle = '#444';
      ctx.lineWidth = 3;
      ctx.setLineDash([6, 4]);
      const mids = EQUIP.filter(e=>e.id.startsWith('C'));
      mids.forEach(cv => {
        const buf = getEquip('buffer') || getEquip('input_store');
        if (!buf) return;
        const bx = buf.x + buf.w, by = buf.y + buf.h/2;
        ctx.beginPath();
        ctx.moveTo(bx, by);
        ctx.lineTo(cv.x, cv.y + cv.h/2);
        ctx.stroke();
        // Arrows
        const mx = (bx+cv.x)/2, my = (by+cv.y+cv.h/2)/2;
        drawArrow(ctx, mx-5, my, cv.x-5, cv.y+cv.h/2, C.accent, 1.5);
      });
      ctx.setLineDash([]);
      ctx.restore();
    } else if (conn.type === 'forklift') {
      // Dashed path
      ctx.strokeStyle = C.muted;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Connection label
    const mx = (x1+x2)/2, my = (y1+y2)/2 - 12;
    ctx.fillStyle = C.muted;
    ctx.font = '9px Segoe UI';
    ctx.textAlign = 'center';
    ctx.fillText(conn.label, mx, my);
  });
}

function drawArrow(ctx, x1, y1, x2, y2, color, lw) {
  const angle = Math.atan2(y2-y1, x2-x1);
  ctx.save();
  ctx.strokeStyle = color; ctx.lineWidth = lw;
  ctx.setLineDash([]);
  ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
  ctx.fillStyle = color;
  ctx.translate(x2,y2); ctx.rotate(angle);
  ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(-8,-4); ctx.lineTo(-8,4); ctx.closePath(); ctx.fill();
  ctx.restore();
}

function drawEquipment() {
  EQUIP.forEach(eq => {
    const ms = machineStates[eq.id];
    const state = ms?.state || 'running';

    // Shadow
    ctx.shadowColor = eq.border;
    ctx.shadowBlur = state === 'running' ? 8 : state === 'blocked' ? 18 : 12;

    // Background
    ctx.fillStyle = eq.color;
    ctx.beginPath();
    ctx.roundRect(eq.x, eq.y, eq.w, eq.h, 6);
    ctx.fill();
    ctx.shadowBlur = 0;

    // Border
    const pulseAlpha = state === 'running' ? 0.7 + 0.3*Math.sin(simT*3) : 1.0;
    ctx.strokeStyle = hexAlpha(eq.border, pulseAlpha);
    ctx.lineWidth = state === 'blocked' ? 2.5 : 1.8;
    ctx.beginPath();
    ctx.roundRect(eq.x, eq.y, eq.w, eq.h, 6);
    ctx.stroke();

    // Status light
    const lightColor = state === 'running' ? C.green
      : state === 'blocked' ? C.red
      : state === 'maintenance' ? C.red
      : state === 'setup' ? C.yellow
      : C.muted;
    const lightX = eq.x + eq.w - 10;
    const lightY = eq.y + 10;
    ctx.fillStyle = lightColor;
    ctx.shadowColor = lightColor;
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.arc(lightX, lightY, 5, 0, Math.PI*2);
    ctx.fill();
    ctx.shadowBlur = 0;

    // Label
    ctx.fillStyle = C.text;
    ctx.font = 'bold 10px Segoe UI';
    ctx.textAlign = 'center';
    const lines = eq.label.split('\n');
    const ly = eq.y + eq.h/2 - (lines.length-1)*6;
    lines.forEach((l, i) => ctx.fillText(l, eq.x + eq.w/2, ly + i*13));

    // Fill bar (storage)
    if (eq.type === 'storage' && eq.currentFill !== undefined) {
      const fillPct = Math.min(eq.currentFill / (eq.cap || 1), 1);
      const bw = eq.w - 14;
      const bx = eq.x + 7;
      const bh = Math.min(eq.h - 35, 20);
      const by = eq.y + eq.h - bh - 8;
      // Background
      ctx.fillStyle = '#1a1d24';
      ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 3); ctx.fill();
      // Fill
      const fillColor = fillPct > 0.85 ? C.red : fillPct > 0.6 ? C.yellow : C.green;
      ctx.fillStyle = fillColor;
      ctx.beginPath(); ctx.roundRect(bx, by, bw*fillPct, bh, 3); ctx.fill();
      // Border
      ctx.strokeStyle = '#333'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 3); ctx.stroke();
      // Text
      ctx.fillStyle = '#fff';
      ctx.font = '8px Segoe UI';
      ctx.textAlign = 'center';
      ctx.fillText(`${Math.round(fillPct*100)}%`, bx+bw/2, by+bh/2+3);
    }

    // Efficiency bar (machine)
    if (eq.type === 'machine' && ms) {
      const eff = ms.eff;
      const bw = Math.min(eq.w - 14, 80);
      const bx = eq.x + 7;
      const bh = 5;
      const by = eq.y + eq.h - 14;
      ctx.fillStyle = '#1a1d24';
      ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 2); ctx.fill();
      ctx.fillStyle = state === 'running' ? C.green : (state === 'setup' ? C.yellow : C.red);
      ctx.beginPath(); ctx.roundRect(bx, by, bw*eff, bh, 2); ctx.fill();
      ctx.fillStyle = C.muted;
      ctx.font = '8px Segoe UI';
      ctx.textAlign = 'left';
      ctx.fillText(`OEE ${Math.round(eff*100)}%`, bx + bw + 4, by + 5);
    }

    // Machine production count
    if (eq.type === 'machine' && ms && ms.produced > 0) {
      ctx.fillStyle = C.accent;
      ctx.font = '9px Segoe UI';
      ctx.textAlign = 'center';
      const val = eq.id === 'corrugadora'
        ? `${(ms.produced/1000).toFixed(1)}k m²`
        : `${Math.round(ms.produced).toLocaleString()} uds`;
      ctx.fillText(val, eq.x + eq.w/2, eq.y + 16);
    }

    // Corrugator: internal roller animation
    if (eq.id === 'corrugadora' && ms?.state === 'running') {
      const numRollers = 6;
      const spacing = eq.w / (numRollers + 1);
      ctx.strokeStyle = 'rgba(255,106,0,0.4)';
      ctx.lineWidth = 1.5;
      for (let r = 0; r < numRollers; r++) {
        const rx = eq.x + spacing*(r+1);
        const cy = eq.y + eq.h/2;
        const radius = eq.h*0.25;
        const angleOffset = (simT * 4 + r * 0.8) % (Math.PI*2);
        ctx.beginPath();
        ctx.arc(rx, cy, radius, angleOffset, angleOffset + Math.PI*1.5);
        ctx.stroke();
      }
    }
  });
}

function drawConveyorParticles() {
  conveyorParticles.forEach(p => {
    const x = p.x1 + (p.x2-p.x1)*p.t;
    const y = p.y1 + (p.y2-p.y1)*p.t;
    ctx.fillStyle = p.color;
    ctx.shadowColor = p.color;
    ctx.shadowBlur = 4;
    if (p.type === 'roll_belt') {
      ctx.beginPath();
      ctx.arc(x, y, 5, 0, Math.PI*2);
      ctx.fill();
    } else {
      ctx.fillRect(x-5, y-4, 10, 8);
    }
    ctx.shadowBlur = 0;
  });
}

function drawKPIPanel() {
  const px = 8, py = 8, pw = 190, ph = 170;
  // Panel background
  ctx.fillStyle = 'rgba(13,17,23,0.85)';
  ctx.strokeStyle = C.accent;
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.roundRect(px, py, pw, ph, 6); ctx.fill(); ctx.stroke();

  ctx.fillStyle = C.accent;
  ctx.font = 'bold 10px Segoe UI';
  ctx.textAlign = 'left';
  ctx.fillText('▸ KPI EN TIEMPO REAL', px+8, py+16);

  const kpis = [
    ['⏱ Tiempo sim.', formatTime(simT)],
    ['📦 m² producidos', `${(met.m2/1000).toFixed(1)}k m²`],
    ['✂️ Uds. convert.', `${Math.round(met.units).toLocaleString()}`],
    ['🏭 Efic. corrug.', `${met.corrEff.toFixed(1)}%`],
    ['⚡ OEE medio', `${met.oee.toFixed(1)}%`],
    ['📊 Buffer', `${met.bufOcc.toFixed(0)}%`],
    ['🚛 Carretillas', `${met.fltUtil.toFixed(0)}% util.`],
  ];

  kpis.forEach(([label, val], i) => {
    const ky = py + 28 + i*19;
    ctx.fillStyle = C.muted;
    ctx.font = '9px Segoe UI';
    ctx.fillText(label, px+8, ky);
    ctx.fillStyle = C.text;
    ctx.font = 'bold 9px Segoe UI';
    ctx.textAlign = 'right';
    ctx.fillText(val, px+pw-8, ky);
    ctx.textAlign = 'left';
  });

  // Progress bar
  const prog = Math.min(simT / simDuration, 1);
  const bx = px+8, by = py+ph-14, bw = pw-16, bh = 6;
  ctx.fillStyle = '#2a2a3a';
  ctx.beginPath(); ctx.roundRect(bx, by, bw, bh, 3); ctx.fill();
  ctx.fillStyle = C.accent;
  ctx.beginPath(); ctx.roundRect(bx, by, bw*prog, bh, 3); ctx.fill();
  ctx.fillStyle = C.muted;
  ctx.font = '7px Segoe UI';
  ctx.textAlign = 'center';
  ctx.fillText(`${(prog*100).toFixed(0)}% completado`, bx+bw/2, by+bh+8);
  ctx.textAlign = 'left';
}

function drawFinishedOverlay() {
  ctx.fillStyle = 'rgba(0,0,0,0.7)';
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = C.accent;
  ctx.font = 'bold 28px Segoe UI';
  ctx.textAlign = 'center';
  ctx.fillText('✅ SIMULACIÓN COMPLETADA', W/2, H/2-20);
  ctx.fillStyle = C.text;
  ctx.font = '16px Segoe UI';
  ctx.fillText(`m² producidos: ${(met.m2/1000).toFixed(1)}k  |  OEE: ${met.oee.toFixed(1)}%`, W/2, H/2+20);
  ctx.fillText('Pulsa ↺ RESET para nueva simulación', W/2, H/2+50);
  ctx.textAlign = 'left';
}

// =============================================================
//  HELPERS
// =============================================================
function formatTime(seconds) {
  const h = Math.floor(seconds/3600);
  const m = Math.floor((seconds%3600)/60);
  const s = Math.floor(seconds%60);
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}
function pad(n) { return n < 10 ? '0'+n : String(n); }
function hexAlpha(hex, a) {
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${a})`;
}

// =============================================================
//  CONTROLS
// =============================================================
function setSpeed(s) {
  speed = s;
  ['1','5','10','30'].forEach(v => {
    const btn = document.getElementById('b'+v+'x');
    if (btn) btn.classList.toggle('active', parseInt(v)===s);
  });
}

function togglePause() {
  paused = !paused;
  const btn = document.getElementById('btnPause');
  if (btn) btn.textContent = paused ? '▶ REANUDAR' : '⏸ PAUSAR';
  document.getElementById('statusMsg').textContent = paused ? '⏸ PAUSADO' : '▶ SIMULANDO';
}

function resetSim() {
  simT = 0; paused = false; finished = false;
  conveyorParticles = [];
  buildLayout();
  initForklifts();
  spawnConveyorParticles();
  met = {m2:0, units:0, corrEff:0.87, oee:0.82, fltUtil:0.0, bufOcc:0.0, bottlenecks:[]};
  const btn = document.getElementById('btnPause');
  if (btn) btn.textContent = '⏸ PAUSAR';
  document.getElementById('statusMsg').textContent = '▶ SIMULANDO';
}

// Tooltip on hover
cv.addEventListener('mousemove', e => {
  const rect = cv.getBoundingClientRect();
  const mx = (e.clientX - rect.left) * (W / rect.width);
  const my = (e.clientY - rect.top) * (H / rect.height);
  const tip = document.getElementById('tooltip');
  let hit = null;
  EQUIP.forEach(eq => {
    if (mx > eq.x && mx < eq.x+eq.w && my > eq.y && my < eq.y+eq.h) hit = eq;
  });
  if (hit) {
    const ms = machineStates[hit.id];
    let html = `<strong>${hit.label.replace('\n',' ')}</strong><br>`;
    if (ms) {
      const stColor = ms.state==='running'?'#4fc17b':ms.state==='blocked'?'#e05555':'#f0c040';
      html += `Estado: <span style="color:${stColor}">${ms.state.toUpperCase()}</span><br>`;
      html += `OEE: ${(ms.eff*100).toFixed(1)}%<br>`;
      if (ms.produced > 0) html += `Producido: ${Math.round(ms.produced).toLocaleString()}<br>`;
    }
    if (hit.currentFill !== undefined) {
      html += `Nivel: ${Math.round(hit.currentFill)} / ${hit.cap}<br>`;
      html += `Ocupación: ${((hit.currentFill/(hit.cap||1))*100).toFixed(0)}%`;
    }
    tip.innerHTML = html;
    tip.style.display = 'block';
    tip.style.left = (e.clientX+12)+'px';
    tip.style.top = (e.clientY-10)+'px';
  } else {
    tip.style.display = 'none';
  }
});
cv.addEventListener('mouseleave', ()=>document.getElementById('tooltip').style.display='none');

// =============================================================
//  MAIN LOOP
// =============================================================
function loop(ts) {
  requestAnimationFrame(loop);
  const realDt = Math.min((ts - lastTs)/1000, 0.08);
  lastTs = ts;
  if (!paused && !finished) {
    const simDt = realDt * speed;
    update(simDt);
  }
  draw();
  document.getElementById('simTime').textContent = '⏱ '+formatTime(simT);
}

// =============================================================
//  BOOT
// =============================================================
buildLayout();
initForklifts();
spawnConveyorParticles();
requestAnimationFrame(ts => { lastTs = ts; loop(ts); });
</script>
</body>
</html>"""

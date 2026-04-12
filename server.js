// ============================================================
// VorteX Safari — Backend Server
// Express + Socket.io for real-time dashboard communication
// UNPLUGGED Round 3 — 24-Hour Hardware Hackathon
// ============================================================

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

app.use(cors());
app.use(express.json({ limit: '5mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ── Run State ────────────────────────────────────────────────
let runState = createFreshState();

function createFreshState() {
  return {
    active: false,
    startTime: null,
    endTime: null,
    detections: [],
    telemetry: [],
    rfidTriggered: false,
    aqi: null,
    gps: { lat: 0, lng: 0 },
    vehiclePosition: 0,   // 0–100 (% along track)
    vehicleSpeed: 0,
  };
}

// ── API Routes ───────────────────────────────────────────────

// Start a new run
app.post('/api/start', (_req, res) => {
  runState = createFreshState();
  runState.active = true;
  runState.startTime = Date.now();
  io.emit('run_started', { startTime: runState.startTime });
  console.log('🟢 Run started');
  res.json({ status: 'ok' });
});

// Receive telemetry from ESP32 #1 or #2
app.post('/api/telemetry', (req, res) => {
  const d = req.body;

  // Auto-start on first telemetry if not already active
  if (!runState.active && !runState.rfidTriggered) {
    runState.active = true;
    runState.startTime = Date.now();
    io.emit('run_started', { startTime: runState.startTime });
  }

  if (d.position !== undefined) runState.vehiclePosition = d.position;
  if (d.speed    !== undefined) runState.vehicleSpeed    = d.speed;
  if (d.gps)                    runState.gps             = d.gps;
  if (d.aqi      !== undefined) runState.aqi             = d.aqi;

  const entry = { ...d, timestamp: Date.now() };
  runState.telemetry.push(entry);

  io.emit('telemetry', {
    position:  runState.vehiclePosition,
    speed:     runState.vehicleSpeed,
    gps:       runState.gps,
    aqi:       runState.aqi,
    timestamp: entry.timestamp,
  });

  res.json({ status: 'ok' });
});

// Receive animal detection from ESP32-CAM
app.post('/api/detection', (req, res) => {
  const detection = {
    ...req.body,
    id: runState.detections.length + 1,
    timestamp: Date.now(),
  };
  runState.detections.push(detection);
  io.emit('detection', detection);
  console.log(`🐾 Detected: ${detection.label} (${detection.confidence}%)`);
  res.json({ status: 'ok', id: detection.id });
});

// RFID checkpoint — end of run
app.post('/api/rfid', (req, res) => {
  runState.rfidTriggered = true;
  runState.endTime = Date.now();
  runState.active = false;

  const report = generateReport();
  io.emit('rfid', { triggered: true, tagId: req.body.tagId || 'UNKNOWN' });
  io.emit('run_complete', report);
  console.log('🏁 RFID triggered — run complete');
  res.json({ status: 'ok', report });
});

// Get current run report
app.get('/api/report', (_req, res) => {
  res.json(generateReport());
});

// Get full run state (for dashboard reconnection)
app.get('/api/state', (_req, res) => {
  res.json(runState);
});

// Reset the run
app.post('/api/reset', (_req, res) => {
  runState = createFreshState();
  io.emit('run_reset', {});
  console.log('🔄 Run reset');
  res.json({ status: 'ok' });
});

// ── Report Generator ─────────────────────────────────────────
function generateReport() {
  const elapsed = runState.endTime
    ? (runState.endTime - runState.startTime) / 1000
    : runState.startTime
      ? (Date.now() - runState.startTime) / 1000
      : 0;

  return {
    totalTime:          elapsed,
    totalTimeFormatted: fmtTime(elapsed),
    totalDetections:    runState.detections.length,
    detections:         runState.detections,
    uniqueAnimals:      [...new Set(runState.detections.map(d => d.label))],
    telemetryPoints:    runState.telemetry.length,
    avgAqi:             runState.aqi,
    gpsPath:            runState.telemetry.filter(t => t.gps).map(t => t.gps),
    rfidTriggered:      runState.rfidTriggered,
    completedAt:        runState.endTime ? new Date(runState.endTime).toISOString() : null,
  };
}

function fmtTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// ── Socket.io ────────────────────────────────────────────────
io.on('connection', (socket) => {
  console.log(`📡 Dashboard connected: ${socket.id}`);
  // Send current state on connect (handles page refresh)
  socket.emit('state', runState);
  socket.on('disconnect', () =>
    console.log(`📡 Dashboard disconnected: ${socket.id}`)
  );
});

// ── Launch ───────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
  console.log('');
  console.log('=========================================');
  console.log('  🦁  VorteX Safari Server  🦁');
  console.log('=========================================');
  console.log(`  Dashboard : http://localhost:${PORT}`);
  console.log('');
  console.log('  API Endpoints:');
  console.log(`    POST /api/start      — begin a new run`);
  console.log(`    POST /api/telemetry  — vehicle position/sensors`);
  console.log(`    POST /api/detection  — animal detected`);
  console.log(`    POST /api/rfid       — RFID checkpoint`);
  console.log(`    GET  /api/report     — run summary`);
  console.log(`    GET  /api/state      — full state`);
  console.log(`    POST /api/reset      — reset run`);
  console.log('=========================================');
  console.log('');
});

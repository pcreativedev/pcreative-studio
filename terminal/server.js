// Servidor local para Pcreative Studio:
//   GET /        → index.html con xterm.js
//   GET /xterm.css | /xterm.js | /addon-fit.js → estáticos
//   WS  /?cwd=&cmd=&args=  → pty bidireccional
//
// Lo lanza ProjectWindow como subprocess. Imprime "PORT=<n>" en stdout
// para que Python sepa a qué puerto conectar.

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { WebSocketServer } = require('ws');

// ── Seguridad del WS ──────────────────────────────────────────────
// Sin esto, cualquier web abierta en el navegador podría conectar al WS
// (los WebSockets NO están sujetos a CORS) y ejecutar comandos arbitrarios.
// Defensa: token compartido en el query + chequeo de Origin + allowlist del
// comando inicial. El token se imprime en stdout (TOKEN=…) y Python lo añade
// a la URL de la página; index.html lo reenvía al WS.
const AUTH_TOKEN = process.env.PCS_TERM_TOKEN || crypto.randomBytes(24).toString('hex');
const CMD_ALLOWLIST = (process.env.PCS_TERM_ALLOW ||
  'bash,sh,zsh,fish,dash,ksh,cmd,cmd.exe,powershell,powershell.exe,pwsh,pwsh.exe,' +
  'hermes,claude,codex,gemini,opencode,node,npm,npx,git'
).split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
const cmdBase = (c) => String(c || '').replace(/\\/g, '/').split('/').pop().toLowerCase();

// Límites de recursos: nº máximo de PTYs vivos a la vez + corte por inactividad
// (se reinicia con cualquier I/O; 0 = desactivado). Defensa en profundidad.
const MAX_PTYS = parseInt(process.env.PCS_TERM_MAX_PTYS || '16', 10);
const IDLE_MS  = parseInt(process.env.PCS_TERM_IDLE_MS  || String(3 * 60 * 60 * 1000), 10); // 3h
let activePtys = 0;
// node-pty es un módulo nativo. Preferimos el fork con prebuilds
// (@homebridge/node-pty-prebuilt-multiarch) que trae binarios para
// Windows/macOS/Linux y NO necesita compilar (sin Visual Studio Build
// Tools en Windows). Fallback al node-pty estándar si solo está ese.
let pty;
try {
  pty = require('@homebridge/node-pty-prebuilt-multiarch');
} catch (e) {
  pty = require('node-pty');
}

const ROOT = __dirname;
const NM = path.join(ROOT, 'node_modules');

// Mapeo URL → fichero real
const ASSETS = {
  '/xterm.css'     : path.join(NM, '@xterm', 'xterm', 'css', 'xterm.css'),
  '/xterm.js'      : path.join(NM, '@xterm', 'xterm', 'lib', 'xterm.js'),
  '/addon-fit.js'  : path.join(NM, '@xterm', 'addon-fit', 'lib', 'addon-fit.js'),
  '/qwebchannel.js': path.join(ROOT, 'qwebchannel.js'),
  '/index.html'    : path.join(ROOT, 'index.html'),
  '/'              : path.join(ROOT, 'index.html'),
};
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js'  : 'application/javascript; charset=utf-8',
  '.css' : 'text/css; charset=utf-8',
};

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];
  const file = ASSETS[url];
  if (!file || !fs.existsSync(file)) {
    res.statusCode = 404;
    res.end('Not found');
    return;
  }
  res.setHeader('Content-Type', MIME[path.extname(file)] || 'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});

const wss = new WebSocketServer({ server });

// node-pty en Windows NO resuelve el comando desde el PATH: necesita la
// ruta ABSOLUTA del ejecutable (si no, "File not found:"). Resolvemos el
// comando buscando en PATH con las extensiones de PATHEXT. En Unix node-pty
// sí resuelve por PATH, así que devolvemos el comando tal cual.
function resolveExe(cmd) {
  if (process.platform !== 'win32') return cmd;
  if (cmd.includes('\\') || cmd.includes('/') || /\.[a-z]{2,4}$/i.test(cmd)) {
    // Ya es ruta o tiene extensión → confiamos en ella tal cual.
    if (cmd.includes('\\') || cmd.includes('/')) return cmd;
  }
  const exts = (process.env.PATHEXT || '.COM;.EXE;.BAT;.CMD').split(';');
  const dirs = (process.env.PATH || '').split(path.delimiter);
  for (const dir of dirs) {
    if (!dir) continue;
    for (const ext of ['', ...exts]) {
      const full = path.join(dir, cmd + ext);
      try { if (fs.existsSync(full)) return full; } catch (_) {}
    }
  }
  return cmd; // fallback: que node-pty lo intente y reporte el error
}

wss.on('connection', (ws, req) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  // 1) Token obligatorio: una web externa no puede conocerlo.
  if (url.searchParams.get('token') !== AUTH_TOKEN) {
    try { ws.close(1008, 'unauthorized'); } catch (_) {}
    return;
  }
  // 2) Origin: rechaza conexiones desde un host que no sea local.
  const origin = req.headers.origin;
  if (origin) {
    let oh = null;
    try { oh = new URL(origin).hostname; } catch (_) {}
    if (oh !== '127.0.0.1' && oh !== 'localhost') {
      try { ws.close(1008, 'forbidden origin'); } catch (_) {}
      return;
    }
  }

  const cwd  = url.searchParams.get('cwd')
             || process.env.HOME || process.env.USERPROFILE || process.cwd();
  const cmd  = url.searchParams.get('cmd')  || process.env.SHELL || 'bash';
  const argsRaw = url.searchParams.get('args') || '';
  const args = argsRaw ? argsRaw.split('\x1f').filter(Boolean) : [];

  // 3) Allowlist del comando inicial (los comandos que el usuario teclee
  //    dentro de la shell no pasan por aquí; esto solo limita el proceso raíz).
  if (!CMD_ALLOWLIST.includes(cmdBase(cmd))) {
    try {
      ws.send(`\r\n\x1b[31m[comando no permitido: ${cmd}]\x1b[0m\r\n`);
      ws.close(1008, 'command not allowed');
    } catch (_) {}
    return;
  }

  // 4) Cap de PTYs concurrentes: evita agotar recursos del equipo.
  if (activePtys >= MAX_PTYS) {
    try {
      ws.send(`\r\n\x1b[31m[límite de ${MAX_PTYS} terminales alcanzado]\x1b[0m\r\n`);
      ws.close(1013, 'too many ptys');
    } catch (_) {}
    return;
  }

  let p;
  try {
    p = pty.spawn(resolveExe(cmd), args, {
      name: 'xterm-256color',
      cwd,
      cols: 100,
      rows: 30,
      env: { ...process.env, TERM: 'xterm-256color' },
    });
  } catch (e) {
    ws.send(`\r\n\x1b[31m[error spawn ${cmd}: ${e.message}]\x1b[0m\r\n`);
    ws.close();
    return;
  }
  activePtys++;

  // Corte por inactividad: se rearma con cualquier I/O. Una terminal/misión sin
  // ningún dato durante IDLE_MS se considera muerta y se cierra.
  let idleTimer = null;
  const bump = () => {
    if (!IDLE_MS) return;
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
      try { ws.send(`\r\n\x1b[33m[cerrado por inactividad]\x1b[0m\r\n`); } catch (_) {}
      try { p.kill(); } catch (_) {}
    }, IDLE_MS);
  };
  let cleaned = false;
  const cleanup = () => {
    if (cleaned) return;
    cleaned = true;
    activePtys = Math.max(0, activePtys - 1);
    if (idleTimer) clearTimeout(idleTimer);
    try { p.kill(); } catch (_) {}
  };
  bump();

  p.onData(d => { bump(); try { ws.send(d); } catch (_) {} });
  p.onExit(({ exitCode }) => {
    try {
      ws.send(`\r\n\x1b[33m[proceso terminado: ${exitCode}]\x1b[0m\r\n`);
    } catch (_) {}
    cleanup();
    try { ws.close(); } catch (_) {}
  });

  ws.on('message', msg => {
    bump();
    const txt = msg.toString();
    // Si es JSON con type, lo interpretamos; si no, escribir crudo al pty.
    if (txt.startsWith('{')) {
      try {
        const data = JSON.parse(txt);
        if (data.type === 'input') return p.write(data.data);
        if (data.type === 'resize') return p.resize(data.cols, data.rows);
      } catch (_) { /* fall through */ }
    }
    p.write(txt);
  });

  ws.on('close', cleanup);
  ws.on('error', cleanup);
});

// Puerto: arg 0 = puerto fijo (o 0 → random libre)
const port = parseInt(process.argv[2] || '0', 10);
server.listen(port, '127.0.0.1', () => {
  const actualPort = server.address().port;
  // Líneas que Python parsea: puerto + token de autorización del WS.
  console.log(`PORT=${actualPort}`);
  console.log(`TOKEN=${AUTH_TOKEN}`);
});

process.on('SIGTERM', () => { server.close(); process.exit(0); });
process.on('SIGINT',  () => { server.close(); process.exit(0); });

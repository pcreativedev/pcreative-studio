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
const { WebSocketServer } = require('ws');
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
  const cwd  = url.searchParams.get('cwd')
             || process.env.HOME || process.env.USERPROFILE || process.cwd();
  const cmd  = url.searchParams.get('cmd')  || process.env.SHELL || 'bash';
  const argsRaw = url.searchParams.get('args') || '';
  const args = argsRaw ? argsRaw.split('\x1f').filter(Boolean) : [];

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

  p.onData(d => { try { ws.send(d); } catch (_) {} });
  p.onExit(({ exitCode }) => {
    try {
      ws.send(`\r\n\x1b[33m[proceso terminado: ${exitCode}]\x1b[0m\r\n`);
    } catch (_) {}
    try { ws.close(); } catch (_) {}
  });

  ws.on('message', msg => {
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

  ws.on('close', () => { try { p.kill(); } catch (_) {} });
  ws.on('error', () => { try { p.kill(); } catch (_) {} });
});

// Puerto: arg 0 = puerto fijo (o 0 → random libre)
const port = parseInt(process.argv[2] || '0', 10);
server.listen(port, '127.0.0.1', () => {
  const actualPort = server.address().port;
  // Línea que Python parsea para saber a qué puerto conectarse
  console.log(`PORT=${actualPort}`);
});

process.on('SIGTERM', () => { server.close(); process.exit(0); });
process.on('SIGINT',  () => { server.close(); process.exit(0); });

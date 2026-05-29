/* ================= NEO-TOKYO · mock data ================= */

const _MOCK_PROJECTS = [
  {
    id: 'aurora-saas', name: 'Aurora SaaS', jp: 'オーロラ',
    type: 'SaaS Landing', stack: 'Next.js 15', stackKey: 'next',
    agent: 'claude', status: 'live', cost: 4.82, tokens: '2.1M',
    updated: 'hace 3 min', accent: '#00f0ff',
    desc: 'Premium SaaS landing · bento features · pricing tiers',
    tags: ['next', 'tailwind', 'framer'], commits: 47, preview: 'saas',
  },
  {
    id: 'nordic-forge', name: 'Nordic Forge', jp: '北欧',
    type: 'Creative Agency', stack: 'Astro', stackKey: 'astro',
    agent: 'codex', status: 'building', cost: 2.10, tokens: '980K',
    updated: 'hace 12 min', accent: '#86efac',
    desc: 'Studio portfolio · 6 case studies · editorial grid',
    tags: ['astro', 'gsap', 'mdx'], commits: 23, preview: 'agency',
  },
  {
    id: 'meridian-shop', name: 'Meridian Shop', jp: '商店',
    type: 'E-commerce', stack: 'Shopify Hydrogen', stackKey: 'shopify',
    agent: 'gemini', status: 'live', cost: 7.34, tokens: '3.4M',
    updated: 'hace 1 h', accent: '#fbbf24',
    desc: 'Headless storefront · cart drawer · checkout flow',
    tags: ['hydrogen', 'remix', 'stripe'], commits: 89, preview: 'shop',
  },
  {
    id: 'kanban-flux', name: 'Flux Admin', jp: '管理',
    type: 'Dashboard / Admin', stack: 'Laravel + Vue', stackKey: 'laravel',
    agent: 'opencode', status: 'draft', cost: 0.41, tokens: '180K',
    updated: 'hace 5 h', accent: '#c084fc',
    desc: 'Analytics dashboard · charts · RBAC · dark mode',
    tags: ['laravel', 'vue', 'inertia'], commits: 8, preview: 'admin',
  },
  {
    id: 'zen-clinic', name: 'Zen Clinic', jp: '診療',
    type: 'Clínica / Booking', stack: 'WordPress', stackKey: 'wp',
    agent: 'claude', status: 'live', cost: 3.95, tokens: '1.7M',
    updated: 'ayer', accent: '#00f0ff',
    desc: 'Clínica dental Madrid · booking · paleta cálida',
    tags: ['wp', 'acf', 'elementor'], commits: 34, preview: 'clinic',
  },
  {
    id: 'pixel-arcade', name: 'Pixel Arcade', jp: '遊技',
    type: 'Landing / Game', stack: 'Tauri + React', stackKey: 'tauri',
    agent: 'codex', status: 'archived', cost: 1.22, tokens: '540K',
    updated: 'hace 3 días', accent: '#ff2e88',
    desc: 'Retro arcade microsite · CRT FX · leaderboards',
    tags: ['tauri', 'react', 'rust'], commits: 19, preview: 'arcade',
  },
];

const _MOCK_STACKS = [
  { key: 'next', label: 'Next.js 15', jp: '次世代', cat: 'React', n: 'TS' },
  { key: 'astro', label: 'Astro', jp: '星', cat: 'MPA', n: 'JS' },
  { key: 'laravel', label: 'Laravel', jp: '帆', cat: 'PHP', n: 'PHP' },
  { key: 'wp', label: 'WordPress', jp: '出版', cat: 'CMS', n: 'PHP' },
  { key: 'shopify', label: 'Hydrogen', jp: '商', cat: 'Commerce', n: 'TS' },
  { key: 'tauri', label: 'Tauri', jp: '鳥', cat: 'Desktop', n: 'Rust' },
  { key: 'sveltekit', label: 'SvelteKit', jp: '滑', cat: 'Svelte', n: 'TS' },
  { key: 'flutter', label: 'Flutter', jp: '蝶', cat: 'Mobile', n: 'Dart' },
];

// Datos REALES inyectados por el shell nativo (window.__TF_DATA__) con
// fallback a los mocks de arriba cuando se abre el prototipo suelto.
const _TF = (typeof window !== 'undefined' && window.__TF_DATA__) || {};
const PROJECTS = (_TF.projects && _TF.projects.length) ? _TF.projects : _MOCK_PROJECTS;
const STACKS = (_TF.stacks && _TF.stacks.length) ? _TF.stacks : _MOCK_STACKS;

const STATUS = {
  live:     { label: 'LIVE',     color: '#9dff3c' },
  building: { label: 'BUILDING', color: '#00f0ff' },
  draft:    { label: 'DRAFT',    color: '#fbbf24' },
  archived: { label: 'ARCHIVED', color: '#5c6e9c' },
};

/* tiny SVG mock previews per project type */
function MockPreview({ kind, accent }) {
  const a = accent || 'var(--accent)';
  return (
    <svg viewBox="0 0 200 120" style={{ width: '100%', height: '100%', display: 'block' }}>
      <rect width="200" height="120" fill="#070b16" />
      <rect width="200" height="14" fill="#0c1322" />
      <circle cx="10" cy="7" r="2" fill={a} opacity="0.8" />
      <rect x="150" y="4.5" width="42" height="5" rx="2.5" fill={a} opacity="0.3" />
      {kind === 'saas' && <>
        <rect x="14" y="26" width="90" height="9" rx="2" fill={a} opacity="0.85" />
        <rect x="14" y="40" width="64" height="5" rx="2" fill="#2a3550" />
        <rect x="14" y="49" width="40" height="11" rx="3" fill={a} opacity="0.6" />
        <rect x="120" y="26" width="66" height="44" rx="4" fill="#101a30" stroke={a} strokeOpacity="0.3" />
        <rect x="14" y="78" width="40" height="30" rx="3" fill="#0e1628" />
        <rect x="60" y="78" width="40" height="30" rx="3" fill="#0e1628" />
        <rect x="106" y="78" width="40" height="30" rx="3" fill="#0e1628" />
        <rect x="152" y="78" width="34" height="30" rx="3" fill="#0e1628" />
      </>}
      {kind === 'agency' && <>
        <rect x="14" y="24" width="120" height="14" rx="2" fill={a} opacity="0.8" />
        <rect x="14" y="58" width="55" height="48" rx="3" fill="#101a30" />
        <rect x="73" y="58" width="55" height="48" rx="3" fill="#0f1830" />
        <rect x="132" y="58" width="54" height="48" rx="3" fill="#101a30" />
      </>}
      {kind === 'shop' && <>
        {[0,1,2,3].map(i => <rect key={i} x={14 + i*45} y="24" width="40" height="50" rx="3" fill="#101a30" stroke={a} strokeOpacity="0.2" />)}
        {[0,1,2,3].map(i => <rect key={i} x={14 + i*45} y="78" width="26" height="5" rx="2" fill={a} opacity="0.5" />)}
      </>}
      {kind === 'admin' && <>
        <rect x="14" y="24" width="40" height="84" rx="3" fill="#0c1322" />
        <rect x="62" y="24" width="58" height="38" rx="3" fill="#101a30" />
        <rect x="126" y="24" width="60" height="38" rx="3" fill="#101a30" />
        <rect x="62" y="68" width="124" height="40" rx="3" fill="#0e1628" />
        <polyline points="68,98 84,84 100,90 120,72 140,80 160,66 180,74" fill="none" stroke={a} strokeWidth="1.5" />
      </>}
      {kind === 'clinic' && <>
        <rect x="14" y="26" width="80" height="8" rx="2" fill={a} opacity="0.8" />
        <rect x="14" y="38" width="60" height="4" rx="2" fill="#2a3550" />
        <rect x="14" y="48" width="34" height="10" rx="5" fill={a} opacity="0.55" />
        <circle cx="150" cy="55" r="32" fill="#101a30" stroke={a} strokeOpacity="0.3" />
        <rect x="14" y="78" width="172" height="30" rx="3" fill="#0e1628" />
      </>}
      {kind === 'arcade' && <>
        <rect x="20" y="24" width="160" height="60" rx="4" fill="#0c0818" stroke={a} strokeOpacity="0.4" />
        <text x="100" y="60" fontSize="20" fill={a} textAnchor="middle" fontFamily="monospace" opacity="0.9">★彡</text>
        <rect x="60" y="94" width="80" height="12" rx="6" fill={a} opacity="0.5" />
      </>}
    </svg>
  );
}

Object.assign(window, { PROJECTS, STACKS, STATUS, MockPreview });

/* ---- MCP catalog (.mcp.json — curated + community, from repo) ---- */
const MCP_SERVERS = [
  { id: 'filesystem', label: 'filesystem', cat: 'core', always: true, desc: 'Acceso al árbol del proyecto', lic: 'MIT' },
  { id: 'fetch', label: 'fetch', cat: 'core', always: true, desc: 'HTTP fetch / scraping', lic: 'MIT' },
  { id: 'memory', label: 'memory', cat: 'core', always: true, desc: 'Memoria persistente del agente', lic: 'MIT' },
  { id: 'github', label: 'github', cat: 'core', always: true, desc: 'Repos, PRs, issues, push', lic: 'MIT' },
  { id: 'themeforge', label: 'themeforge', cat: 'core', always: true, desc: '8 tools: create_project, estimate_cost, run_preflight, build_zip, suggest_stack…', lic: 'GPL-3' },
  { id: 'playwright', label: 'playwright', cat: 'web', desc: 'Automatización de navegador', lic: 'Apache-2' },
  { id: 'chrome-devtools', label: 'chrome-devtools', cat: 'web', desc: 'Inspección / perf / network', lic: 'MIT' },
  { id: 'figma-context', label: 'figma-context', cat: 'web', desc: 'Lee diseños de Figma (node-id)', lic: 'MIT' },
  { id: 'browsermcp', label: 'browsermcp', cat: 'web', desc: 'Control del navegador del usuario', lic: 'MIT' },
  { id: 'shopify-dev', label: 'shopify-dev', cat: 'commerce', desc: 'Schemas GraphQL Admin/Storefront', lic: 'MIT' },
  { id: 'postgres', label: 'postgres', cat: 'data', desc: 'Query a la DB provisionada', lic: 'MIT' },
  { id: 'wordpress', label: 'wordpress', cat: 'cms', desc: 'CRUD WP nativo (Automattic)', lic: 'GPL-2' },
];

/* ---- Deploy targets ---- */
const DEPLOY_TARGETS = [
  { id: 'netlify', label: 'Netlify', jp: '展開', color: '#32e6e2' },
  { id: 'vercel', label: 'Vercel', jp: '頂', color: '#e9f0ff' },
  { id: 'cloudflare', label: 'Cloudflare Pages', jp: '雲', color: '#f6821f' },
  { id: 'surge', label: 'Surge', jp: '波', color: '#9dff3c' },
];

/* ---- Pre-flight checks ---- */
const PREFLIGHT = [
  { id: 'license', label: 'LICENSE presente', status: 'pass' },
  { id: 'docs', label: 'documentation/ completa', status: 'pass' },
  { id: 'lighthouse', label: 'Lighthouse ≥ 90', status: 'pass', note: '94 perf · 100 a11y' },
  { id: 'secrets', label: 'Sin secretos (.env limpio)', status: 'pass' },
  { id: 'anticopy', label: 'Anti-copy: layout original', status: 'pass' },
  { id: 'images', label: 'Imágenes con licencia', status: 'warn', note: '2 sin atribuir' },
  { id: 'console', label: 'Sin console.error en build', status: 'pass' },
  { id: 'responsive', label: 'Responsive 320→1920', status: 'pass' },
];

/* ---- New project sub-tabs / setup ---- */
const NP_SUBTABS = [
  { k: 'vibe', label: '✨ Vibe', jp: '直感' },
  { k: 'setup', label: '🏗 Setup', jp: '基礎' },
  { k: 'mode', label: '📦 Mode', jp: '様式' },
  { k: 'extras', label: '🔌 Extras', jp: '拡張' },
  { k: 'preview', label: '👁 Preview', jp: '確認' },
];

/* ---- Operator (Hermes Mission Control) mock missions ---- */
const MISSIONS = [
  { id: 'm1', name: 'Aurora SaaS · build hero+pricing', agent: 'claude', status: 'running', progress: 68, eta: '2m 10s', step: 'wiring pricing tiers' },
  { id: 'm2', name: 'Nordic Forge · port case studies', agent: 'codex', status: 'running', progress: 34, eta: '5m 40s', step: 'scaffolding MDX' },
  { id: 'm3', name: 'Meridian Shop · checkout flow', agent: 'gemini', status: 'queued', progress: 0, eta: '—', step: 'en cola' },
  { id: 'm4', name: 'Zen Clinic · booking widget', agent: 'claude', status: 'done', progress: 100, eta: '✓', step: 'completada · $1.20' },
];

Object.assign(window, { MCP_SERVERS, DEPLOY_TARGETS, PREFLIGHT, NP_SUBTABS, MISSIONS });

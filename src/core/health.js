/**
 * Core health/discovery/launch logic.
 */
import { getClient, getTargetInfo, evaluate } from '../connection.js';
import { existsSync } from 'fs';
import { execSync, spawn } from 'child_process';

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// Run a shell command, returning trimmed stdout or '' on any failure.
function shTrim(cmd) {
  try { return execSync(cmd, { timeout: 5000 }).toString().trim(); } catch { return ''; }
}

// True if the PID is still alive (signal 0 probes without killing).
function pidAlive(pid) {
  try { process.kill(Number(pid), 0); return true; } catch { return false; }
}

// PIDs holding the CDP port LISTEN socket — the main TradingView process.
function cdpListenerPids(port, platform) {
  if (platform === 'win32') {
    const out = shTrim(`netstat -ano -p tcp | findstr LISTENING | findstr :${port}`);
    const pids = new Set();
    out.split(/\r?\n/).forEach(l => { const m = l.trim().match(/(\d+)\s*$/); if (m) pids.add(m[1]); });
    return [...pids];
  }
  const out = shTrim(`lsof -ti tcp:${port} -sTCP:LISTEN`);
  return out ? out.split(/\s+/).filter(Boolean) : [];
}

// GET a CDP HTTP endpoint with a hard timeout; resolves to body string or null.
async function cdpHttpGet(port, path) {
  const http = await import('http');
  return new Promise((resolve) => {
    const req = http.get(`http://localhost:${port}${path}`, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => resolve(data));
    });
    req.on('error', () => resolve(null));
    req.setTimeout(3000, () => { req.destroy(); resolve(null); });
  });
}

export async function healthCheck() {
  await getClient();
  const target = await getTargetInfo();

  const state = await evaluate(`
    (function() {
      var result = { url: window.location.href, title: document.title };
      try {
        var chart = window.TradingViewApi._activeChartWidgetWV.value();
        result.symbol = chart.symbol();
        result.resolution = chart.resolution();
        result.chartType = chart.chartType();
        result.apiAvailable = true;
      } catch(e) {
        result.symbol = 'unknown';
        result.resolution = 'unknown';
        result.chartType = null;
        result.apiAvailable = false;
        result.apiError = e.message;
      }
      return result;
    })()
  `);

  return {
    success: true,
    cdp_connected: true,
    target_id: target.id,
    target_url: target.url,
    target_title: target.title,
    chart_symbol: state?.symbol || 'unknown',
    chart_resolution: state?.resolution || 'unknown',
    chart_type: state?.chartType ?? null,
    api_available: state?.apiAvailable ?? false,
  };
}

export async function discover() {
  const paths = await evaluate(`
    (function() {
      var results = {};
      try {
        var chart = window.TradingViewApi._activeChartWidgetWV.value();
        var methods = [];
        for (var k in chart) { if (typeof chart[k] === 'function') methods.push(k); }
        results.chartApi = { available: true, path: 'window.TradingViewApi._activeChartWidgetWV.value()', methodCount: methods.length, methods: methods.slice(0, 50) };
      } catch(e) { results.chartApi = { available: false, error: e.message }; }
      try {
        var col = window.TradingViewApi._chartWidgetCollection;
        var colMethods = [];
        for (var k in col) { if (typeof col[k] === 'function') colMethods.push(k); }
        results.chartWidgetCollection = { available: !!col, path: 'window.TradingViewApi._chartWidgetCollection', methodCount: colMethods.length, methods: colMethods.slice(0, 30) };
      } catch(e) { results.chartWidgetCollection = { available: false, error: e.message }; }
      try {
        var ws = window.ChartApiInstance;
        var wsMethods = [];
        for (var k in ws) { if (typeof ws[k] === 'function') wsMethods.push(k); }
        results.chartApiInstance = { available: !!ws, path: 'window.ChartApiInstance', methodCount: wsMethods.length, methods: wsMethods.slice(0, 30) };
      } catch(e) { results.chartApiInstance = { available: false, error: e.message }; }
      try {
        var bwb = window.TradingView && window.TradingView.bottomWidgetBar;
        var bwbMethods = [];
        if (bwb) { for (var k in bwb) { if (typeof bwb[k] === 'function') bwbMethods.push(k); } }
        results.bottomWidgetBar = { available: !!bwb, path: 'window.TradingView.bottomWidgetBar', methodCount: bwbMethods.length, methods: bwbMethods.slice(0, 20) };
      } catch(e) { results.bottomWidgetBar = { available: false, error: e.message }; }
      try {
        var replay = window.TradingViewApi._replayApi;
        results.replayApi = { available: !!replay, path: 'window.TradingViewApi._replayApi' };
      } catch(e) { results.replayApi = { available: false, error: e.message }; }
      try {
        var alerts = window.TradingViewApi._alertService;
        results.alertService = { available: !!alerts, path: 'window.TradingViewApi._alertService' };
      } catch(e) { results.alertService = { available: false, error: e.message }; }
      return results;
    })()
  `);

  const available = Object.values(paths).filter(v => v.available).length;
  const total = Object.keys(paths).length;

  return { success: true, apis_available: available, apis_total: total, apis: paths };
}

export async function uiState() {
  const state = await evaluate(`
    (function() {
      var ui = {};
      var bottom = document.querySelector('[class*="layout__area--bottom"]');
      ui.bottom_panel = { open: !!(bottom && bottom.offsetHeight > 50), height: bottom ? bottom.offsetHeight : 0 };
      var right = document.querySelector('[class*="layout__area--right"]');
      ui.right_panel = { open: !!(right && right.offsetWidth > 50), width: right ? right.offsetWidth : 0 };
      var monacoEl = document.querySelector('.monaco-editor.pine-editor-monaco');
      ui.pine_editor = { open: !!monacoEl, width: monacoEl ? monacoEl.offsetWidth : 0, height: monacoEl ? monacoEl.offsetHeight : 0 };
      var stratPanel = document.querySelector('[data-name="backtesting"]') || document.querySelector('[class*="strategyReport"]');
      ui.strategy_tester = { open: !!(stratPanel && stratPanel.offsetParent) };
      var widgetbar = document.querySelector('[data-name="widgetbar-wrap"]');
      ui.widgetbar = { open: !!(widgetbar && widgetbar.offsetWidth > 50) };
      ui.buttons = {};
      var btns = document.querySelectorAll('button');
      var seen = {};
      for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        if (b.offsetParent === null || b.offsetWidth < 15) continue;
        var text = b.textContent.trim();
        var aria = b.getAttribute('aria-label') || '';
        var dn = b.getAttribute('data-name') || '';
        var label = text || aria || dn;
        if (!label || label.length > 60) continue;
        var key = label.replace(/[^a-zA-Z0-9 ]/g, '').substring(0, 40);
        if (seen[key]) continue;
        seen[key] = true;
        var rect = b.getBoundingClientRect();
        var region = 'other';
        if (rect.y < 50) region = 'top_bar';
        else if (rect.y < 90 && rect.x < 650) region = 'toolbar';
        else if (rect.x < 45) region = 'left_sidebar';
        else if (rect.x > 650 && rect.y < 100) region = 'pine_header';
        else if (rect.y > 750) region = 'bottom_bar';
        if (!ui.buttons[region]) ui.buttons[region] = [];
        ui.buttons[region].push({ label: label.substring(0, 40), disabled: b.disabled, x: Math.round(rect.x), y: Math.round(rect.y) });
      }
      ui.key_buttons = {};
      var keyLabels = {
        'add_to_chart': /add to chart/i, 'save_and_add': /save and add/i,
        'update_on_chart': /update on chart/i, 'save': /^Save(Save)?$/,
        'saved': /^Saved/, 'publish_script': /publish script/i,
        'compile_errors': /error/i, 'unsaved_version': /unsaved version/i,
      };
      for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        if (b.offsetParent === null) continue;
        var text = b.textContent.trim();
        for (var k in keyLabels) {
          if (keyLabels[k].test(text)) {
            ui.key_buttons[k] = { text: text.substring(0, 40), disabled: b.disabled, visible: b.offsetWidth > 0 };
          }
        }
      }
      try {
        var chart = window.TradingViewApi._activeChartWidgetWV.value();
        ui.chart = { symbol: chart.symbol(), resolution: chart.resolution(), chartType: chart.chartType(), study_count: chart.getAllStudies().length };
      } catch(e) { ui.chart = { error: e.message }; }
      try {
        var replay = window.TradingViewApi._replayApi;
        function unwrap(v) { return (v && typeof v === 'object' && typeof v.value === 'function') ? v.value() : v; }
        ui.replay = { available: unwrap(replay.isReplayAvailable()), started: unwrap(replay.isReplayStarted()) };
      } catch(e) { ui.replay = { error: e.message }; }
      return ui;
    })()
  `);

  return { success: true, ...state };
}

export async function launch({ port, kill_existing } = {}) {
  const cdpPort = port || 9222;
  const killFirst = kill_existing !== false;
  const platform = process.platform;

  const pathMap = {
    darwin: [
      '/Applications/TradingView.app/Contents/MacOS/TradingView',
      `${process.env.HOME}/Applications/TradingView.app/Contents/MacOS/TradingView`,
    ],
    win32: [
      `${process.env.LOCALAPPDATA}\\TradingView\\TradingView.exe`,
      `${process.env.PROGRAMFILES}\\TradingView\\TradingView.exe`,
      `${process.env['PROGRAMFILES(X86)']}\\TradingView\\TradingView.exe`,
    ],
    linux: [
      '/opt/TradingView/tradingview',
      '/opt/TradingView/TradingView',
      `${process.env.HOME}/.local/share/TradingView/TradingView`,
      '/usr/bin/tradingview',
      '/snap/tradingview/current/tradingview',
    ],
  };

  let tvPath = null;
  const candidates = pathMap[platform] || pathMap.linux;
  for (const p of candidates) {
    if (p && existsSync(p)) { tvPath = p; break; }
  }

  if (!tvPath) {
    try {
      const cmd = platform === 'win32' ? 'where TradingView.exe' : 'which tradingview';
      tvPath = execSync(cmd, { timeout: 3000 }).toString().trim().split('\n')[0];
      if (tvPath && !existsSync(tvPath)) tvPath = null;
    } catch { /* ignore */ }
  }

  if (!tvPath && platform === 'darwin') {
    try {
      const found = execSync('mdfind "kMDItemFSName == TradingView.app" | head -1', { timeout: 5000 }).toString().trim();
      if (found) {
        const candidate = `${found}/Contents/MacOS/TradingView`;
        if (existsSync(candidate)) tvPath = candidate;
      }
    } catch { /* ignore */ }
  }

  if (!tvPath) {
    throw new Error(`TradingView not found on ${platform}. Searched: ${candidates.join(', ')}. Launch manually with: /path/to/TradingView --remote-debugging-port=${cdpPort}`);
  }

  if (killFirst) {
    // Identify the instance actually serving CDP (the port listener), falling
    // back to the binary path. A wedged instance keeps the listener alive.
    let oldPids = cdpListenerPids(cdpPort, platform);
    if (oldPids.length === 0 && platform !== 'win32') {
      const out = shTrim(`pgrep -f ${JSON.stringify(tvPath)}`);
      oldPids = out ? out.split(/\s+/).filter(Boolean) : [];
    }

    if (oldPids.length > 0) {
      // 1) Graceful SIGTERM.
      if (platform === 'win32') shTrim('taskkill /IM TradingView.exe');
      else for (const pid of oldPids) { try { process.kill(Number(pid), 'SIGTERM'); } catch { /* gone */ } }
      for (let i = 0; i < 12 && oldPids.some(pidAlive); i++) await sleep(500); // up to 6s

      // 2) Escalate to SIGKILL for survivors (a wedged process may ignore SIGTERM).
      const survivors = oldPids.filter(pidAlive);
      if (survivors.length > 0) {
        if (platform === 'win32') shTrim('taskkill /F /IM TradingView.exe');
        else for (const pid of survivors) { try { process.kill(Number(pid), 'SIGKILL'); } catch { /* gone */ } }
        for (let i = 0; i < 10 && survivors.some(pidAlive); i++) await sleep(500); // up to 5s
      }

      // 3) Hard requirement: never relaunch while the old instance is alive.
      const stillAlive = oldPids.filter(pidAlive);
      if (stillAlive.length > 0) {
        throw new Error(`Failed to kill existing TradingView (pids still alive: ${stillAlive.join(', ')}). Kill manually and retry.`);
      }

      // 4) Confirm the CDP port is free so we don't attach to a zombie socket.
      for (let i = 0; i < 10 && cdpListenerPids(cdpPort, platform).length > 0; i++) await sleep(500);
      const portHolders = cdpListenerPids(cdpPort, platform);
      if (portHolders.length > 0) {
        throw new Error(`TradingView killed but port ${cdpPort} still has a listener (pids: ${portHolders.join(', ')}). Refusing to relaunch onto a stale socket.`);
      }
    }
  }

  const child = spawn(tvPath, [`--remote-debugging-port=${cdpPort}`], { detached: true, stdio: 'ignore' });
  child.unref();

  // Wait for the CDP HTTP endpoint to come up.
  let version = null;
  for (let i = 0; i < 20; i++) {
    await sleep(1000);
    const body = await cdpHttpGet(cdpPort, '/json/version');
    if (body) { try { version = JSON.parse(body); break; } catch { /* not ready */ } }
  }
  if (!version) {
    return {
      success: false, platform, binary: tvPath, pid: child.pid, cdp_port: cdpPort, cdp_ready: false,
      error: `TradingView relaunched (pid ${child.pid}) but CDP did not respond on port ${cdpPort} within 20s.`,
    };
  }

  // Wait for the chart page target to appear (the chart finishes loading).
  let chartTarget = null;
  for (let i = 0; i < 40; i++) {
    const body = await cdpHttpGet(cdpPort, '/json/list');
    if (body) {
      try {
        const targets = JSON.parse(body);
        chartTarget = targets.find(t => t.type === 'page' && /tradingview\.com\/chart/i.test(t.url)) || null;
        if (chartTarget) break;
      } catch { /* not ready */ }
    }
    await sleep(1000);
  }

  return {
    success: true, platform, binary: tvPath, pid: child.pid,
    cdp_port: cdpPort, cdp_url: `http://localhost:${cdpPort}`,
    browser: version.Browser, user_agent: version['User-Agent'],
    cdp_ready: true,
    chart_target_found: !!chartTarget,
    chart_target_url: chartTarget?.url || null,
    ...(chartTarget ? {} : { warning: `CDP is up on port ${cdpPort} but no chart target appeared within 40s — the chart may still be loading.` }),
  };
}

import CDP from 'chrome-remote-interface';

let client = null;
let targetInfo = null;
const CDP_HOST = 'localhost';
const CDP_PORT = 9222;
const MAX_RETRIES = 2;
const BASE_DELAY = 500;
const MAX_DELAY = 1000;

// Per-operation timeouts. Every CDP/network call below is wrapped so a wedged
// TradingView (HTTP discovery answers but the protocol command channel is dead)
// fails fast with a structured error instead of hanging forever.
const FETCH_TIMEOUT = 3000;    // GET /json/list
const CONNECT_TIMEOUT = 4000;  // CDP websocket attach
const CMD_TIMEOUT = 3000;      // Runtime.enable / Page.enable / DOM.enable / liveness ping
const EVAL_TIMEOUT = 20000;    // Runtime.evaluate (heavy data extraction can be legitimately slow)

/**
 * Race a promise against a timeout. On timeout, rejects with a labelled error.
 * The losing (possibly never-settling) promise is detached with a no-op catch so
 * a late rejection can't trigger an unhandledRejection after we've moved on.
 */
function withTimeout(promise, ms, label) {
  promise.catch(() => {});
  let timer;
  const timeout = new Promise((_, reject) => {
    timer = setTimeout(() => reject(new Error(`${label} timed out after ${ms}ms (TradingView CDP unresponsive)`)), ms);
  });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

// Known direct API paths discovered via live probing (see PROBE_RESULTS.md)
const KNOWN_PATHS = {
  chartApi: 'window.TradingViewApi._activeChartWidgetWV.value()',
  chartWidgetCollection: 'window.TradingViewApi._chartWidgetCollection',
  bottomWidgetBar: 'window.TradingView.bottomWidgetBar',
  replayApi: 'window.TradingViewApi._replayApi',
  alertService: 'window.TradingViewApi._alertService',
  chartApiInstance: 'window.ChartApiInstance',
  mainSeriesBars: 'window.TradingViewApi._activeChartWidgetWV.value()._chartWidget.model().mainSeries().bars()',
  // Phase 1: Strategy data — model().dataSources() → find strategy → .performance().value(), .ordersData(), .reportData()
  strategyStudy: 'chart._chartWidget.model().model().dataSources()',
  // Phase 2: Layouts — getSavedCharts(cb), loadChartFromServer(id)
  layoutManager: 'window.TradingViewApi.getSavedCharts',
  // Phase 5: Symbol search — searchSymbols(query) returns Promise
  symbolSearchApi: 'window.TradingViewApi.searchSymbols',
  // Phase 6: Pine scripts — REST API at pine-facade.tradingview.com/pine-facade/list/?filter=saved
  pineFacadeApi: 'https://pine-facade.tradingview.com/pine-facade',
};

export { KNOWN_PATHS };

/**
 * Sanitize a string for safe interpolation into JavaScript code evaluated via CDP.
 * Uses JSON.stringify to produce a properly escaped JS string literal (with quotes).
 * Prevents injection via quotes, backticks, template literals, or control chars.
 */
export function safeString(str) {
  return JSON.stringify(String(str));
}

/**
 * Validate that a value is a finite number. Throws if NaN, Infinity, or non-numeric.
 * Prevents corrupt values from reaching TradingView APIs that persist to cloud state.
 */
export function requireFinite(value, name) {
  const n = Number(value);
  if (!Number.isFinite(n)) throw new Error(`${name} must be a finite number, got: ${value}`);
  return n;
}

export async function getClient() {
  if (client) {
    try {
      // Quick liveness check — bounded so a half-open socket can't hang here.
      await withTimeout(
        client.Runtime.evaluate({ expression: '1', returnByValue: true }),
        CMD_TIMEOUT, 'CDP liveness check'
      );
      return client;
    } catch {
      // Drop the dead client (closes the socket, aborting any hung command).
      try { await client.close(); } catch { /* already gone */ }
      client = null;
      targetInfo = null;
    }
  }
  return connect();
}

export async function connect() {
  let lastError;
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    let c = null;
    try {
      const target = await findChartTarget();
      if (!target) {
        throw new Error('No TradingView chart target found. Is TradingView open with a chart?');
      }

      c = await withTimeout(
        CDP({ host: CDP_HOST, port: CDP_PORT, target: target.id }),
        CONNECT_TIMEOUT, 'CDP websocket connect'
      );

      // Enable required domains — each bounded. A wedged renderer never ACKs these.
      await withTimeout(c.Runtime.enable(), CMD_TIMEOUT, 'Runtime.enable');
      await withTimeout(c.Page.enable(), CMD_TIMEOUT, 'Page.enable');
      await withTimeout(c.DOM.enable(), CMD_TIMEOUT, 'DOM.enable');

      // Commit only on full success so we never expose a half-initialised client.
      client = c;
      targetInfo = target;
      return client;
    } catch (err) {
      lastError = err;
      // Close the partial connection so the hung command is aborted and the socket freed.
      if (c) { try { await c.close(); } catch { /* ignore */ } }
      if (attempt < MAX_RETRIES - 1) {
        const delay = Math.min(BASE_DELAY * Math.pow(2, attempt), MAX_DELAY);
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }
  throw new Error(`CDP connection failed after ${MAX_RETRIES} attempts: ${lastError?.message}`);
}

async function findChartTarget() {
  const resp = await fetch(`http://${CDP_HOST}:${CDP_PORT}/json/list`, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT),
  });
  const targets = await resp.json();
  // Prefer targets with tradingview.com/chart in the URL
  return targets.find(t => t.type === 'page' && /tradingview\.com\/chart/i.test(t.url))
    || targets.find(t => t.type === 'page' && /tradingview/i.test(t.url))
    || null;
}

export async function getTargetInfo() {
  if (!targetInfo) {
    await getClient();
  }
  return targetInfo;
}

export async function evaluate(expression, opts = {}) {
  const c = await getClient();
  let result;
  try {
    result = await withTimeout(
      c.Runtime.evaluate({
        expression,
        returnByValue: true,
        awaitPromise: opts.awaitPromise ?? false,
        ...opts,
      }),
      opts.timeout ?? EVAL_TIMEOUT, 'Runtime.evaluate'
    );
  } catch (err) {
    // A timed-out evaluate means this client is wedged — drop it so the next call
    // reconnects fresh instead of reusing a hung socket.
    try { await c.close(); } catch { /* ignore */ }
    if (client === c) { client = null; targetInfo = null; }
    throw err;
  }
  if (result.exceptionDetails) {
    const msg = result.exceptionDetails.exception?.description
      || result.exceptionDetails.text
      || 'Unknown evaluation error';
    throw new Error(`JS evaluation error: ${msg}`);
  }
  return result.result?.value;
}

export async function evaluateAsync(expression) {
  return evaluate(expression, { awaitPromise: true });
}

export async function disconnect() {
  if (client) {
    try { await client.close(); } catch {}
    client = null;
    targetInfo = null;
  }
}

// --- Direct API path helpers ---
// Each returns the STRING expression path after verifying it exists.
// Callers use the returned string in their own evaluate() calls.

async function verifyAndReturn(path, name) {
  const exists = await evaluate(`typeof (${path}) !== 'undefined' && (${path}) !== null`);
  if (!exists) {
    throw new Error(`${name} not available at ${path}`);
  }
  return path;
}

export async function getChartApi() {
  return verifyAndReturn(KNOWN_PATHS.chartApi, 'Chart API');
}

export async function getChartCollection() {
  return verifyAndReturn(KNOWN_PATHS.chartWidgetCollection, 'Chart Widget Collection');
}

export async function getBottomBar() {
  return verifyAndReturn(KNOWN_PATHS.bottomWidgetBar, 'Bottom Widget Bar');
}

export async function getReplayApi() {
  return verifyAndReturn(KNOWN_PATHS.replayApi, 'Replay API');
}

export async function getMainSeriesBars() {
  return verifyAndReturn(KNOWN_PATHS.mainSeriesBars, 'Main Series Bars');
}

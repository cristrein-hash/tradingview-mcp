#!/usr/bin/env python3
"""Plota os trades da XAU 15M LONG swept-runner BASE #4 FINAL hour-causal (USER_APPROVED_NOT_PRODUCTION,
Cris 2026-06-28: N435 WR47,6% +291,5R DD−11,0) no chart 15M, via convenção canônica.

FIDELIDADE: executa o engine aprovado (engine_substrate4_v5_hourcausal.py) via exec — ZERO lógica
copiada; seleção = cand[v5h != BEAR] do próprio engine. Geometria reconstruída com as fórmulas
verbatim sobre as MESMAS séries (entry=close@cj · SL=min(low p..cj)−0,1ATR · exit=entry+R·risk,
R=let-run real do engine). ASSERT do painel completo (N435 · 207W · +291,5R) antes de qualquer plot.

LIMITE DO CHART (Cris 2026-07-03): TradingView 15M carrega só até ~2025 → plota o SUBCONJUNTO
entry ≥ 2025-01-01, mantendo o **#id GLOBAL do N435** (cronológico, estável entre janelas — canon §7).
Trades 2024 não-plotáveis são contados e declarados no report (sem sampling silencioso).

Canon: long_position + label #id (fontsize 12, entry+0,5R), WIDTH 10 barras 15M (MASTER §10),
ticks 0.01, color_mode=OUTCOME (verde R>0 / vermelho R≤0), exit_policy=FONTE (let-run realizado).
Remoção prévia SELETIVA (mantém retângulos = regime detector; autorização Cris). NUNCA draw_clear.
NÃO troca timeframe (chart posicionado manualmente pelo Cris; HARD_STOP se != 15).
Sem screenshot; verificação por draw_list. Requer pause flag.
"""
import sys, json
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset

PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S, WIDTH = "PEPPERSTONE:XAUUSD", "15", 900, 10
GREEN, RED = "#1a8917", "#cc0000"
KEEP_TYPES = {"rectangle"}
CUTOFF_2025 = 1735689600  # 2025-01-01T00:00Z — limite de carregamento do chart 15M

# ---- executa o ENGINE APROVADO (namespace isolado; imprime os painéis dele) ----
ns = {"__name__": "engine_exec", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
exec(compile(open(HERE / "engine_substrate4_v5_hourcausal.py").read(),
             "engine_substrate4_v5_hourcausal.py", "exec"), ns)
cand, ROWS, PRIMK, f = ns["cand"], ns["ROWS"], ns["PRIMK"], ns["f"]

sel = sorted([c for c in cand if c["v5h"] != "BEAR"], key=lambda z: z["cj_t"])
n = len(sel); w = sum(1 for c in sel if c["R"] > 0); sm = sum(c["R"] for c in sel)
assert n == 435, n
assert abs(sm - 291.5) < 0.5, sm
assert abs(100 * w / n - 47.6) < 0.3, w
print(f"PANEL OK (engine real): N={n} WR={100*w/n:.1f}% sumR={sm:+.1f}")

# ---- geometria verbatim por trade (mesmas séries/fórmulas do engine) ----
rmap = {}
for r in ROWS:
    rmap.setdefault(r["cj_t"], r)
trades = []
for gid, c in enumerate(sel, 1):  # gid = #id GLOBAL no N435 (estável)
    r = rmap[c["cj_t"]]
    s = PRIMK[r["block"]]["series"]
    tmap = {b["t"]: i for i, b in enumerate(s)}
    p, cj = tmap[r["t"]], tmap[r["cj_t"]]
    atr = s[p]["atr"] or s[cj]["atr"]
    entry = s[cj]["c"]
    sl = min(x["l"] for x in s[p:cj + 1]) - 0.1 * atr
    risk = entry - sl
    if risk <= 0: sys.exit(f"ABORT: risco inválido gid {gid}")
    trades.append({"gid": gid, "t": int(c["cj_t"]), "entry": round(entry, 2), "sl": round(sl, 2),
                   "exit": round(entry + c["R"] * risk, 2), "R": c["R"], "win": c["R"] > 0})

plot_set = [t for t in trades if t["t"] >= CUTOFF_2025]
skip24 = len(trades) - len(plot_set)
print(f"PLOT SET: {len(plot_set)} trades ≥2025 (#{plot_set[0]['gid']}–#{plot_set[-1]['gid']}) · "
      f"{skip24} trades de 2024 FORA do alcance do chart (declarado, sem sampling)")

if "--prepare-only" in sys.argv:
    print("prepare-only: sem MCP/chart."); sys.exit(0)
if not PAUSE.exists():
    sys.exit("ERRO: pause flag ausente. Rode: touch /tmp/claude_recheck.paused")

c = MCPClient(); c.start()
report = {"removed": 0, "kept_rectangles": 0, "posicoes": 0, "labels": 0, "falhas": [],
          "skip_2024_fora_do_chart": skip24}
try:
    st = c.call_tool("chart_get_state")
    sym, res = st.get("symbol"), str(st.get("resolution"))
    report["chart_inicial"] = f"{sym}/{res}"
    if not str(sym).endswith("XAUUSD") or res != TF:
        c.stop(); sys.exit(f"HARD_STOP: chart={sym}/{res} (esperado XAUUSD/15 — NÃO troco TF, Cris posicionou)")

    # 1) remoção SELETIVA — mantém retângulos (regime detector)
    dl0 = c.call_tool("draw_list")
    entities = dl0.get("shapes") or []
    report["before"] = dl0.get("count")
    if report["before"] and not entities:
        c.stop(); sys.exit("ABORT: draw_list sem 'shapes' — formato inesperado")
    for e in entities:
        eid = e.get("id"); etype = str(e.get("name") or "").lower()
        if not eid: continue
        if any(k in etype for k in KEEP_TYPES):
            report["kept_rectangles"] += 1; continue
        rr = c.call_tool("draw_remove_one", {"entity_id": eid})
        if isinstance(rr, dict) and rr.get("success"): report["removed"] += 1
        else: report["falhas"].append(f"remove {eid} ({etype}): {str(rr)[:60]}")
    if report["falhas"]:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        c.stop(); sys.exit("ABORT: remoção seletiva incompleta — plot cancelado")

    # 2) plot canônico do subconjunto 2025+ (id global preservado)
    for t in plot_set:
        entry, sl, ex, tt, win, gid = t["entry"], t["sl"], t["exit"], t["t"], t["win"], t["gid"]
        risk = entry - sl
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": tt, "price": entry},
            "point2": {"time": tt + WIDTH * BAR_S, "price": ex},
            "overrides": json.dumps({
                "stopLevel": price_to_ticks_offset(entry, sl),
                "profitLevel": price_to_ticks_offset(entry, ex)})})
        if isinstance(r1, dict) and r1.get("success"): report["posicoes"] += 1
        else: report["falhas"].append(f"pos #{gid}: {str(r1)[:60]}")
        r2 = c.call_tool("draw_shape", {"shape": "text",
            "point": {"time": tt, "price": round(entry + 0.5 * risk, 2)},
            "text": f"#{gid}",
            "overrides": json.dumps({"color": GREEN if win else RED, "bold": True, "fontsize": 12})})
        if isinstance(r2, dict) and r2.get("success"): report["labels"] += 1
        done = report["posicoes"]
        if done % 50 == 0: print(f"  [{done}/{len(plot_set)}]")

    dl = c.call_tool("draw_list")
    report["after"] = dl.get("count")
finally:
    try: c.stop()
    except Exception: pass

print(json.dumps({k: (v if k != "falhas" else v[:10]) for k, v in report.items()},
                 indent=2, ensure_ascii=False))
if len(report["falhas"]) > 10:
    print(f"(+{len(report['falhas'])-10} falhas omitidas)")

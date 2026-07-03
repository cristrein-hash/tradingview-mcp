#!/usr/bin/env python3
"""Plota os 24 trades FINAIS da L1 EMA21 Continuation (XAU_4H_LONG_L1_EMA21_pocCut_regimeV5)
no chart 4H, via convenção canônica (PLOTTING_CANON_MASTER + skills/plotting-canon).

Fonte dos trades: l1_FINAL_regime_gated.json (N24 = approved34 − poc_cut8 − BEAR; +45,2R, 18W).
Geometria: entry = close@bar · **SL = REGRA V1 (zona_OB_low − 0,1·ATR14)** · TARGET = entry + 3R.
✅ Conflito RESOLVIDO (Cris 2026-07-03): **regra V1 = SL OFICIAL da L1** ("artefato V1 é o aprovado";
34/34 match, ver reports/_diag_l1_sl_rule_match.py). A regra "max(zona,swing6)−0,1ATR" da
APPROVED_REFINEMENT ficou como estudo in-sample não-oficial (correção no topo daquele doc).
Séries/zonas: scanner.build_series() (RAW 4H gz do HD, local, sem MCP p/ dados).

VALIDAÇÃO EMBUTIDA (validate-before-presenting): re-executa o walk (≤60 barras, regra do estudo)
por trade e ABORTA se o outcome recomputado divergir do R aprovado — garante que bar/entry/SL/target
plotados são exatamente os da aprovação (painel: sumR +45,2 · 18W/24).

Remoção prévia SELETIVA (autorização Cris): remove TODOS os desenhos EXCETO retângulos (regime
detector). NUNCA draw_clear. Gate anti-duplicação: falha na remoção → NÃO plota.
Canon: long_position + label #id (fontsize 12, entry+0,5R), width 20 barras 4H, ticks 0.01,
color_mode=OUTCOME (verde win/vermelho loss), exit_policy=FONTE (target +3R da config aprovada).
Sem screenshot; verificação por draw_list. Requer pause flag.
"""
import sys, json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/cristrein/tradingview-mcp")
L1 = REPO / "my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION"
FINAL = REPO / "my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/l1_FINAL_regime_gated.json"
sys.path.insert(0, str(L1)); sys.path.insert(0, str(REPO / "my-strategy/core"))
sys.path.insert(0, str(REPO / "alert-bridge"))
import scanner
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset

PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S, WIDTH = "PEPPERSTONE:XAUUSD", "240", 14400, 20
GREEN, RED = "#1a8917", "#cc0000"
KEEP_TYPES = {"rectangle"}

fin = json.load(open(FINAL))
assert fin["n"] == 24, fin["n"]
S = scanner.build_series()

def idx_of(ts):
    et = int(datetime.strptime(ts, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).timestamp())
    i = S.idx.get(et)
    if i is None:
        i = min(range(S.N), key=lambda k: abs(S.T[k] - et))
        if abs(S.T[i] - et) > 7200:
            sys.exit(f"ABORT: ts {ts} sem bar próximo no RAW (delta {abs(S.T[i]-et)}s)")
    return i

def walk(i, entry, sl, target, mx=60):
    for k in range(i + 1, min(i + 1 + mx, S.N)):
        if S.L[k] <= sl: return -1.0
        if S.H[k] >= target: return 3.0
    e = min(i + mx, S.N - 1)
    return round((S.C[e] - entry) / (entry - sl), 2)

trades = []
for t in fin["trades"]:
    i = idx_of(t["ts"])
    entry = S.C[i]; atr = S.ATR14[i] or 0
    dz = scanner.demand_zone(S, i)
    zlo = (dz[1] if dz else S.EMA21[i - 1])
    sl = zlo - 0.1 * atr  # REGRA V1 (decisão Cris 2026-07-03 — fiel aos outcomes do FINAL-24)
    risk = entry - sl
    if risk <= 0: sys.exit(f"ABORT: risco inválido {t['ts']}")
    target = entry + 3 * risk
    R_re = walk(i, entry, sl, target)
    if abs(R_re - t["R"]) > 0.02:
        sys.exit(f"ABORT: {t['ts']} R recomputado {R_re} != aprovado {t['R']} — geometria não reproduz")
    trades.append({"t": S.T[i], "ts": t["ts"], "entry": round(entry, 2), "sl": round(sl, 2),
                   "target": round(target, 2), "R": t["R"], "win": t["R"] > 0, "regime": t["regime"]})

trades.sort(key=lambda z: z["t"])
n = len(trades); wn = sum(1 for t in trades if t["win"]); sm = sum(t["R"] for t in trades)
assert n == 24 and wn == 18 and abs(sm - 45.2) < 0.1, (n, wn, sm)
print(f"PANEL OK (geometria REPRODUZ aprovação): N={n} W={wn} ({100*wn/n:.0f}%) sumR={sm:+.1f} "
      f"({trades[0]['ts'][:10]} -> {trades[-1]['ts'][:10]})")

if "--prepare-only" in sys.argv:
    print("prepare-only: sem MCP/chart."); sys.exit(0)
if not PAUSE.exists():
    sys.exit("ERRO: pause flag ausente. Rode: touch /tmp/claude_recheck.paused")

c = MCPClient(); c.start()
report = {"removed": 0, "kept_rectangles": 0, "posicoes": 0, "labels": 0, "falhas": []}
try:
    st = c.call_tool("chart_get_state")
    sym, res = st.get("symbol"), str(st.get("resolution"))
    if not str(sym).endswith("XAUUSD"):
        c.stop(); sys.exit(f"HARD_STOP: chart={sym} (esperado XAUUSD)")
    report["chart_inicial"] = f"{sym}/{res}"

    # 1) remoção SELETIVA — draw_list = {success,count,shapes:[{id,name}]}
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

    # 2) garantir 4H
    if res != TF:
        c.call_tool("chart_set_timeframe", {"timeframe": TF})
        import time as _t; _t.sleep(1.5)

    # 3) plot canônico dos 24
    for i, t in enumerate(trades, 1):
        entry, sl, tg, tt, win = t["entry"], t["sl"], t["target"], t["t"], t["win"]
        risk = entry - sl
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": tt, "price": entry},
            "point2": {"time": tt + WIDTH * BAR_S, "price": tg},
            "overrides": json.dumps({
                "stopLevel": price_to_ticks_offset(entry, sl),
                "profitLevel": price_to_ticks_offset(entry, tg)})})
        if isinstance(r1, dict) and r1.get("success"): report["posicoes"] += 1
        else: report["falhas"].append(f"pos #{i}: {str(r1)[:60]}")
        r2 = c.call_tool("draw_shape", {"shape": "text",
            "point": {"time": tt, "price": round(entry + 0.5 * risk, 2)},
            "text": f"#{i}",
            "overrides": json.dumps({"color": GREEN if win else RED, "bold": True, "fontsize": 12})})
        if isinstance(r2, dict) and r2.get("success"): report["labels"] += 1

    dl = c.call_tool("draw_list")
    report["after"] = dl.get("count")
finally:
    try: c.stop()
    except Exception: pass

print(json.dumps(report, indent=2, ensure_ascii=False))

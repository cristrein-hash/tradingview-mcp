#!/usr/bin/env python3
"""Plota os 53 trades do SISTEMA A "EMA-SHAKEOUT" (Lab G, POSITIVO_FRÁGIL/EXPLORATORY) no chart 15M.
Pedido Cris 2026-07-04: TODOS os 53, numeração no label, **21 fora-da-base435 em LARANJA, 32 em AZUL**
(variante de cor POR PERTENÇA autorizada pelo Cris nesta execução — outcome NÃO codificado em cor;
canon: cor é SÓ do label, widgets neutros — MASTER §8/§9, exceção declarada no report).

FONTE: universo SELADO results/lab_g_candidates.jsonl (sha verificado) + predicado sysA congelado
(byte-idêntico ao lab_g_entry_systems_analysis.py / kill-check — DA-verificado 2x). Exit = FONTE
(let-run real g_R). Canon 15M: long_position + text label, WIDTH 10 barras, ticks 0.01.
NO_CLEAR: NENHUMA remoção por default; --authorized-clear-selective (mantém rectangles) SÓ com
autorização explícita do Cris nesta execução. HARD_STOP se chart != XAUUSD/15 (não troco TF).
Sem screenshot; verificação por draw_list. Requer pause flag. --probe-only = leitura do chart apenas."""
import sys, json, hashlib
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path("/Users/cristrein/tradingview-mcp")
sys.path.insert(0, str(REPO / "alert-bridge"))
from draw_xau_4h_trades import MCPClient, price_to_ticks_offset

PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF, BAR_S, WIDTH = "PEPPERSTONE:XAUUSD", "15", 900, 10
ORANGE, BLUE = "#f57c00", "#1565c0"
KEEP_TYPES = {"rectangle"}

# ---- fonte selada + predicado congelado (fail-loud) ----
CANON = HERE / "results" / "lab_g_candidates.jsonl"
sha = hashlib.sha256(CANON.read_bytes()).hexdigest()
assert sha == (HERE / "results" / "lab_g_candidates.sha256").read_text().split()[0], "universo violado"
U = [json.loads(l) for l in open(CANON)]

def fv(r, k, d=0):
    v = r.get(k); return v if isinstance(v, (int, float)) and not isinstance(v, bool) else d
def sysA(r):
    return (r["g_v5h"] == "BULL"
            and fv(r, "h1_trend") == 1 and fv(r, "h1_pos", 0) >= 0.33
            and (fv(r, "above_ema21", 1) == 0 or fv(r, "reclaim_ema_bars", 99) <= 3)
            and (fv(r, "g_atr_spike") >= 1.27 or fv(r, "g_downrun") >= 3)
            and (fv(r, "in_demand") == 1 or fv(r, "htf_demand_any") == 1)
            and (fv(r, "g_rec_speed") >= 0.69 or fv(r, "reclaim_atr") >= 2.0)
            and r["g_knife"] == 0)

picks = sorted([r for r in U if sysA(r)], key=lambda r: r["cj_t"])
assert len(picks) == 53, f"picks={len(picks)} != 53"
netsum = sum(r["g_R"] - 0.8 / r["g_risk"] for r in picks)
w = sum(1 for r in picks if (r["g_R"] - 0.8 / r["g_risk"]) > 0)
out_n = sum(1 for r in picks if not r["g_in_base435"])
assert abs(netsum - 25.9) < 0.2 and out_n == 21, f"painel A não reproduz: {netsum:.1f}/{out_n}"
print(f"SISTEMA A OK: N53 · WR_liq {100*w/53:.1f}% · NET {netsum:+.1f} · fora-da-base {out_n} (LARANJA) · base {53-out_n} (AZUL)")

trades = []
for i, r in enumerate(picks, 1):
    entry, sl = r["g_entry"], r["g_sl"]; risk = entry - sl
    assert risk > 0
    trades.append({"id": i, "t": int(r["cj_t"]), "entry": round(entry, 2), "sl": round(sl, 2),
                   "exit": round(entry + r["g_R"] * risk, 2), "R": r["g_R"],
                   "out": not r["g_in_base435"],
                   "utc": dt.datetime.utcfromtimestamp(r["cj_t"]).strftime("%Y-%m-%d %H:%M"),
                   "yr": r["yr"]})
n24 = sum(1 for t in trades if t["yr"] == 2024)
print(f"anos: 2024={n24} · 2025={sum(1 for t in trades if t['yr']==2025)} · 2026={sum(1 for t in trades if t['yr']==2026)} "
      f"(2024 pode falhar ancoragem se o chart não carregar até lá — declarado, sem sampling silencioso)")

if "--prepare-only" in sys.argv:
    print("prepare-only: sem MCP/chart."); sys.exit(0)

c = MCPClient(); c.start()
try:
    st = c.call_tool("chart_get_state")
    sym, res = st.get("symbol"), str(st.get("resolution"))
    dl0 = c.call_tool("draw_list")
    print(f"CHART: {sym}/{res} · drawings existentes: {dl0.get('count')}")
    if "--probe-only" in sys.argv:
        kinds = {}
        for e in (dl0.get("shapes") or []):
            k = str(e.get("name") or "?").lower(); kinds[k] = kinds.get(k, 0) + 1
        print("tipos:", json.dumps(kinds, ensure_ascii=False)); c.stop(); sys.exit(0)
    if not str(sym).endswith("XAUUSD") or res != TF:
        c.stop(); sys.exit(f"HARD_STOP: chart={sym}/{res} (esperado XAUUSD/15 — não troco TF)")
    if not PAUSE.exists():
        c.stop(); sys.exit("ERRO: pause flag ausente (touch /tmp/claude_recheck.paused)")

    report = {"removed": 0, "kept": 0, "posicoes": 0, "labels": 0, "falhas": [], "before": dl0.get("count")}
    if "--authorized-clear-selective" in sys.argv:
        entities = dl0.get("shapes") or []
        if report["before"] and not entities:
            c.stop(); sys.exit("ABORT: draw_list sem 'shapes'")
        for e in entities:
            eid = e.get("id"); etype = str(e.get("name") or "").lower()
            if not eid: continue
            if any(k in etype for k in KEEP_TYPES):
                report["kept"] += 1; continue
            rr = c.call_tool("draw_remove_one", {"entity_id": eid})
            if isinstance(rr, dict) and rr.get("success"): report["removed"] += 1
            else: report["falhas"].append(f"remove {eid}: {str(rr)[:50]}")
        if report["falhas"]:
            print(json.dumps(report, ensure_ascii=False)); c.stop(); sys.exit("ABORT: remoção incompleta")

    for t in trades:
        risk = t["entry"] - t["sl"]
        r1 = c.call_tool("draw_shape", {"shape": "long_position",
            "point": {"time": t["t"], "price": t["entry"]},
            "point2": {"time": t["t"] + WIDTH * BAR_S, "price": t["exit"]},
            "overrides": json.dumps({
                "stopLevel": price_to_ticks_offset(t["entry"], t["sl"]),
                "profitLevel": price_to_ticks_offset(t["entry"], t["exit"])})})
        if isinstance(r1, dict) and r1.get("success"): report["posicoes"] += 1
        else: report["falhas"].append(f"pos #{t['id']} {t['utc']}: {str(r1)[:50]}")
        r2 = c.call_tool("draw_shape", {"shape": "text",
            "point": {"time": t["t"], "price": round(t["entry"] + 0.5 * risk, 2)},
            "text": f"#{t['id']}",
            "overrides": json.dumps({"color": ORANGE if t["out"] else BLUE, "bold": True, "fontsize": 12})})
        if isinstance(r2, dict) and r2.get("success"): report["labels"] += 1
        else: report["falhas"].append(f"label #{t['id']}: {str(r2)[:50]}")
    dl = c.call_tool("draw_list")
    report["after"] = dl.get("count")
finally:
    try: c.stop()
    except Exception: pass
print(json.dumps({k: (v if k != "falhas" else v[:12]) for k, v in report.items()}, indent=1, ensure_ascii=False))
if len(report["falhas"]) > 12: print(f"(+{len(report['falhas'])-12} falhas omitidas)")

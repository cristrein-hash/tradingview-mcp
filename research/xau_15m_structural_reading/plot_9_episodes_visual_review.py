#!/usr/bin/env python3
"""PLOT — REVISÃO VISUAL DOS 9 EPISÓDIOS (ordem Cris 2026-07-09).
Espec do Cris: RETÂNGULOS de dimensão PROPORCIONAL à região + label com definição SIMPLES.
Canon: não remove drawings do Cris · não clear · NÃO screenshot (visual é dele) · pause-flag
obrigatório · HARD_STOP se chart != XAUUSD/15. Preflight feito (cron vazio, daemon XAU ausente,
receiver intocado). Coordenadas 100%% de artefactos reais (CSV option-A, a2_regions_r4.jsonl,
a2_anchor_gt_gate_result.json) — extração embutida (reprodutível, sem output órfão).
Grupos: D2-marcados (B4,C1,C2,C4,C5,C6 — caixa do trade real entry→SL / banda da região) ·
D1-falhou (B1,B2 — bandas A2 que os 'cobriam'/late) · par B3 vs A6 (mesma perna, 7d)."""
import json, csv, sys, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/"alert-bridge"))
from draw_xau_4h_trades import MCPClient
PAUSE = Path("/tmp/claude_recheck.paused")
SYMBOL, TF = "PEPPERSTONE:XAUUSD", "15"
RED, ORANGE, GREEN, GRAY = "#cc0000", "#e8a33d", "#1a8917", "#787b86"

def ts(s): return int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())

def load_items():
    # regiões A2 (r=4)
    need = {"B01095", "B01179", "B01159", "B01007"}
    regs = {}; b1_late = None; b1_mark = ts("2026-03-05 18:00")
    for ln in open(REPO/"research/xau_15m_structural_leg_engine/results/a2_regions_r4.jsonl"):
        r = json.loads(ln)
        rid = r["region_id"].split("_")[0]
        if rid in need: regs[rid] = r
        if r["kind"] == "BOTTOM" and abs(r["extreme_t"]-b1_mark) <= 8*3600 and r["known_at"] > b1_mark:
            if b1_late is None or abs(r["extreme_t"]-b1_mark) < abs(b1_late["extreme_t"]-b1_mark):
                b1_late = r
    # trades C (option A CSV) + barras até SL (dossiês)
    want = {"2025-09-16 22:00": ("C1", 14, "0,87"), "2025-10-09 05:45": ("C2", 43, "0,91"),
            "2025-10-19 22:00": ("C3", 155, "0,58"), "2025-12-25 23:00": ("C4", 124, "0,83"),
            "2026-01-13 13:30": ("C5", 28, "0,95"), "2026-03-02 23:00": ("C6", 41, "0,73")}
    items = []
    for row in csv.DictReader(open(REPO/"research/xau_15m_bb_nas_leonardo/reports/xau_15m_option_a_candidates.csv")):
        d = dt.datetime.utcfromtimestamp(int(row["t"])).strftime("%Y-%m-%d %H:%M")
        if d in want:
            cid, bars, pos = want[d]
            t0 = int(row["t"]); ent = float(row["ent"]); sl = float(row["sl"])
            items.append({"id": cid, "t1": t0, "t2": t0+bars*900, "lo": sl, "hi": ent,
                          "col": RED, "label": f"{cid} TOPO pos384 {pos} → SL"})
    # C3 é o caso "gestão, não entrada" — cor própria
    for it in items:
        if it["id"] == "C3":
            it["col"] = ORANGE; it["label"] = "C3 entrada ok · GESTÃO fim-de-perna → SL"
    def band(rid, t1, t2, col, label):
        r = regs[rid]
        return {"id": rid, "t1": t1, "t2": t2, "lo": r["price_low"], "hi": r["price_high"],
                "col": col, "label": label}
    items.append(band("B01095", regs["B01095"]["known_at"], ts("2026-01-13 19:00")+24*3600, RED,
                      "B4 RASO NO ALTO pos384 0,83 · INVÁLIDO (Cris)"))
    items.append(band("B01179", regs["B01179"]["known_at"], ts("2026-03-08 23:00")+24*3600, RED,
                      "B2 TRAP: banda velha, perna bear VIVA"))
    items.append({"id": "B01185", "t1": b1_late["known_at"], "t2": b1_late["known_at"]+48*3600,
                  "lo": b1_late["price_low"], "hi": b1_late["price_high"], "col": RED,
                  "label": "B1 TRAP bounce: perna bear VIVA (região só nasceu depois)"})
    items.append(band("B01159", regs["B01159"]["known_at"], ts("2026-03-16 00:00")+24*3600, ORANGE,
                      "B3 FLUSH INTERMÉDIO · inválido (Cris) — igual a A6 nos números"))
    a6m = ts("2026-03-23 07:00")
    items.append(band("B01007", regs["B01007"]["known_at"], a6m+24*3600, GREEN,
                      "A6 FUNDO REAL (mesma perna que B3, 7d depois) · banda near-miss"))
    return items

def main():
    assert PAUSE.exists(), "ERRO: pause flag ausente"
    items = load_items()
    for it in items:
        print(f"{it['id']:>7} {dt.datetime.utcfromtimestamp(it['t1']).strftime('%m-%d %H:%M')}→"
              f"{dt.datetime.utcfromtimestamp(it['t2']).strftime('%m-%d %H:%M')}  "
              f"[{it['lo']:.2f}, {it['hi']:.2f}]  {it['label']}")
    c = MCPClient(); c.start(); drawn = 0; fails = []
    try:
        st = c.call_tool("chart_get_state")
        sym, res = st.get("symbol"), str(st.get("resolution"))
        if sym != SYMBOL or res != TF:
            print(json.dumps({"HARD_STOP": f"chart {sym}/{res} != {SYMBOL}/{TF}"})); return 1
        for it in items:
            r1 = c.call_tool("draw_shape", {"shape": "rectangle",
                "point": {"time": it["t1"], "price": round(it["lo"], 2)},
                "point2": {"time": it["t2"], "price": round(it["hi"], 2)},
                "overrides": json.dumps({"color": it["col"], "backgroundColor": it["col"],
                                          "transparency": 80, "linewidth": 1})})
            r2 = c.call_tool("draw_shape", {"shape": "text",
                "point": {"time": it["t1"], "price": round(it["hi"]*1.001, 2)},
                "text": it["label"],
                "overrides": json.dumps({"color": it["col"], "fontsize": 12, "bold": True})})
            if r1.get("success") and r2.get("success"): drawn += 1
            else: fails.append({"id": it["id"], "rect": r1.get("success"), "lbl": r2.get("success")})
        out = {"drawn": drawn, "requested": len(items), "fails": fails}
        (HERE/"results/plot_9_episodes_result.json").write_text(json.dumps(out, indent=2))
        print(json.dumps(out, indent=2))
    finally:
        try: c.stop()
        except Exception: pass
    return 0

if __name__ == "__main__":
    sys.exit(main())

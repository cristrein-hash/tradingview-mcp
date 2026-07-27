#!/usr/bin/env python3
"""ESTUDO retoma_engine_v1 (método canónico, read-only). Multi-fatorial (estrutura+zona+leilão+trajetória):
(1) GT: o detetor apanha os 4 fundos ideais do Cris? (2) Varredura 08-27/07 do store: todos os candidatos
+ outcome contrafactual SL-first 3R + PAINEL COMPLETO (N·WR·sumR·avgR·DD·streak). (3) NULL buy-any-reclaim
(mesmo gatilho SEM a seleção estrutural) — a seleção separa? LIMITAÇÃO DECLARADA: zonas = snapshot atual do
store (não há histórico de zonas; no runtime a zona é as-of do dossiê) -> resultado = caracterização
DIRECIONAL in-sample de 19 dias, informa o desenho; árbitro = forward (prereg). Nada é alterado."""
import sys, json, bisect, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
LX = ZoneInfo("Europe/Lisbon")
R = "/Users/cristrein/tradingview-mcp/"
sys.path.insert(0, str(Path(R) / "my-strategy/research/revalidation"))
sys.path.insert(0, str(Path(R) / "my-strategy/strategies/xau_15m_long/reversal/CP_CAPITULATION"))
import retoma_engine_v1 as re1
import cp_engine_live as cp

hm = lambda t: dt.datetime.fromtimestamp(int(t), LX).strftime("%d/%m %H:%M")

bars = sorted([json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bars_15m.jsonl") if l.strip()], key=lambda b: b["t"])
T = [b["t"] for b in bars]; O = [b["o"] for b in bars]; H = [b["h"] for b in bars]
L = [b["l"] for b in bars]; C = [b["c"] for b in bars]
pairs = [(r["t"], r["plot"]) for r in (json.loads(l) for l in open(R + "my-strategy/core/bar_store/store/bubbles_15m.jsonl") if l.strip())]
BUYS, SELLS = cp.bubbles_from_pairs(pairs)

# ZONAS DE DEMANDA existentes (store 15/60/240 union, dedup) — LIDAS, nunca inventadas
zones = []
seen = set()
for tf in ("15", "60", "240"):
    pb = json.load(open(R + f"my-strategy/core/bar_store/store/pine_boxes_{tf}.json"))["data"]
    for st in pb.get("studies", []):
        for z in st.get("zones", []):
            k = (round(z["low"], 1), round(z["high"], 1))
            if k not in seen:
                seen.add(k); zones.append({"low": z["low"], "high": z["high"]})
print(f"zonas store (union 15/60/240, dedup): {len(zones)}")

cands = re1.retoma_scan(T, O, H, L, C, BUYS, SELLS, zones)
print(f"candidatos RETOMA na janela {hm(T[0])} -> {hm(T[-1])}: {len(cands)}\n")

# outcome contrafactual (SL-first, horizonte 480b como A1/Cp)
def resolve(ent_k, ent, sl, tgt):
    for i in range(ent_k + 1, min(len(T), ent_k + 480)):
        hit_sl = L[i] <= sl; hit_tp = H[i] >= tgt
        if hit_sl and hit_tp: return "AMBIG"
        if hit_sl: return "SL"
        if hit_tp: return "TP"
    return "OPEN"

# (1) GT — os 4 fundos ideais
GT = [("A 16/07 3969", dt.datetime(2026,7,16,19,0,tzinfo=LX).timestamp(), dt.datetime(2026,7,17,4,0,tzinfo=LX).timestamp()),
      ("B 20/07 3998", dt.datetime(2026,7,20,14,0,tzinfo=LX).timestamp(), dt.datetime(2026,7,21,2,0,tzinfo=LX).timestamp()),
      ("C 24/07 4044", dt.datetime(2026,7,24,11,0,tzinfo=LX).timestamp(), dt.datetime(2026,7,24,17,0,tzinfo=LX).timestamp()),
      ("D 27/07 4065", dt.datetime(2026,7,27,14,0,tzinfo=LX).timestamp(), dt.datetime(2026,7,27,18,0,tzinfo=LX).timestamp())]
print("=== (1) GT: 4 fundos ideais do Cris ===")
gt_hits = 0
for nome, t0, t1 in GT:
    hit = [c for c in cands if t0 <= c["fundo_t"] <= t1]
    if hit:
        c = hit[0]; gt_hits += 1
        oc = resolve(c["k"], c["ent"], c["sl"], c["tgt"])
        print(f"  ✅ {nome}: fundo {c['low']} @ {hm(c['fundo_t'])} · entry {c['ent']} @ {hm(c['etime'])} · SL {c['sl']} · tgt {c['tgt']} · leg {c['legmag']}× · zona {c['zona']['low']}-{c['zona']['high']} · outcome {oc}")
    else:
        print(f"  ❌ {nome}: NÃO detetado")
print(f"GT: {gt_hits}/4\n")

# (2) painel completo da varredura
print("=== (2) TODOS os candidatos + PAINEL ===")
res = []
for c in cands:
    oc = resolve(c["k"], c["ent"], c["sl"], c["tgt"])
    res.append((c, oc))
    print(f"  {hm(c['fundo_t'])} low {c['low']} -> entry {c['ent']} @ {hm(c['etime'])} sl {c['sl']} "
          f"leg {c['legmag']}× anc {c['anchored']} bd {c['buy_dens']} ls {c['leg_sell']} -> {oc}")
dec = [x for x in res if x[1] in ("TP", "SL", "AMBIG")]
tp = sum(1 for x in dec if x[1] == "TP")
eq = 0.0; peak = 0.0; dd = 0.0; streak = 0; worst = 0
for c, oc in dec:
    r = 3.0 if oc == "TP" else -1.0
    eq += r; peak = max(peak, eq); dd = min(dd, eq - peak)
    streak = streak + 1 if r < 0 else 0; worst = max(worst, streak)
n = len(dec)
print(f"\nPAINEL (3R fixo, SL-first, in-sample 19d): N={n} decididos ({len(res)-n} open) · "
      f"WR {100*tp/max(1,n):.0f}% · sumR {eq:+.1f} · avgR {eq/max(1,n):+.2f} · DD {dd:.1f} · streak -{worst}")

# (3) NULL: buy-any-reclaim (mesmo gatilho, SEM seleção estrutural) na mesma janela
print("\n=== (3) NULL buy-any-reclaim (todos os swing-lows fractais com reclaim, sem seleção) ===")
ATR = cp.atr_series(H, L, C)
null_res = []
for p in cp.swing_lows(H, L, len(T)):
    e = cp.entry_first(p, T, O, H, L, C, ATR, len(T))
    if not e: continue
    oc = resolve(e["k"], e["ent"], e["sl"], round(e["ent"] + 3*(e["ent"]-e["sl"]), 2))
    null_res.append(oc)
nn = sum(1 for x in null_res if x in ("TP", "SL", "AMBIG"))
ntp = sum(1 for x in null_res if x == "TP")
print(f"NULL: N={nn} decididos · WR {100*ntp/max(1,nn):.0f}% · sumR {3*ntp-(nn-ntp):+.1f}")
print(f"\nSELEÇÃO: retoma WR {100*tp/max(1,n):.0f}% (N{n}) vs null {100*ntp/max(1,nn):.0f}% (N{nn})")

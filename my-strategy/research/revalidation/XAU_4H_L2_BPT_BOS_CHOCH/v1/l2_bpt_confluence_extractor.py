#!/usr/bin/env python3
"""CONFLUENCE EXTRACTOR (A) — monta a CONFLUENCIA COMPLETA por episodio (todas as vozes ortogonais juntas, RAW,
trajetoria da perna + snapshot como UMA voz). NAO testa "cada fator separa?" (anti-fragmentacao). A unidade e a
leitura convergente do episodio. Declarado: multi-fatorial convergente de trajetoria (anti-miopia/DSPA), NAO eixo-unico.
Vozes: (macro/estrutura) regime + SMC BOS/CHoCH + polaridade; (trajetoria) decaimento-de-forca + absorcao + sequencia
de divergencias; (order-flow) cluster de bubbles buy/sell no fundo + NAS bottom; (momentum) RSI oversold; (snapshot)
VA svp_state/dist_poc + supply geometry + forma da barra de entrada. Causal (so barras <= entry). Sem outcome no
pacote cego (label so no dataset p/ audit posterior). SANITY_PROBE calibracao. Verified at: 2026-06-24.
Saida: results/l2_bpt_confluence_dataset.jsonl (com label) + results/confluence_reading/reading_packet_BLIND.md (sem)."""
import gzip, json, datetime as dt, os, csv

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
RR = "repro_recovery"; BAR = 14400; LB = 36
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
BACK = {int(json.loads(l)["bar_idx"]): json.loads(l) for l in open("results/l2_bpt_raw_backbone_episodes.jsonl")}
F6 = {int(r["bar_idx"]): r for r in csv.DictReader(open("results/l2_bpt_dspa_path_features_276.csv")) if r.get("bar_idx")}
OUT = {int(r["bar_idx"]): r for r in csv.DictReader(open("results/l2_bpt_uncapped_or_proxy_outcomes_276.csv"))}

# ---- selecao do conjunto de teste: RUNNERS claros vs STOPPERS claros, espalhados por ano (calibracao, nao validacao)
ANCHORS = [4918, 4926, 3825, 3929]
runners = sorted([b for b, r in OUT.items() if float(r["mfe_R"]) >= 10.0], key=lambda b: OUT[b]["datetime"])
stoppers = sorted([b for b, r in OUT.items() if r["stop_before_2R"] == "1" and float(r["mfe_R"]) < 1.5], key=lambda b: OUT[b]["datetime"])
def spread(lst, n):
    if len(lst) <= n: return lst
    step = len(lst) / n; return [lst[int(i * step)] for i in range(n)]
SEL = sorted(set(ANCHORS + spread(runners, 14) + spread(stoppers, 14)))


def to_ep(t):
    if t is None: return None
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)


def pv(s):
    if s is None: return None
    s = str(s).replace(" ", "").replace(" ", "").replace(",", "").replace("−", "-").strip()
    m = 1.0
    if s[-1:] in ("K", "M", "B"): m = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * m
    except Exception: return None


def gv(rec, name):
    return next((s.get("values", {}) for s in (rec.get("study_values") or []) if str(s.get("name")) == name), {})


def grp(rec, cont, key):
    return next((g for g in (rec.get(cont) or []) if key in str(g.get("name", ""))), {})


ENTRY = {b: int(F[b]["ts_epoch"]) for b in SEL}
dates = set()
for b in SEL:
    for k in range(0, LB + 3):
        dates.add(dt.datetime.utcfromtimestamp(ENTRY[b] - k * BAR).strftime("%Y-%m-%d"))
bars = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if not any(d in line for d in dates): continue
        rec = json.loads(line); oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        if not isinstance(last, dict): continue
        at = to_ep(last.get("time"))
        if at is None or at in bars: continue
        svp = gv(rec, "Session Volume Profile"); act = (grp(rec, "pine_shapes_bubbles", "Bubble").get("activations_per_plot") or {})
        nas = grp(rec, "pine_labels", "NAS"); smc = grp(rec, "pine_labels", "Smart Money")
        bars[at] = {"o": last.get("open"), "h": last.get("high"), "l": last.get("low"), "c": last.get("close"),
                    "up": pv(svp.get("Up")), "dn": pv(svp.get("Down")), "tot": pv(svp.get("Total")),
                    "rsi": pv(gv(rec, "Relative Strength Index").get("RSI")),
                    "nas": [l.get("text") for l in (nas.get("labels") or [])[-3:]],
                    "smc": [l.get("text") for l in (smc.get("labels") or [])[-3:]],
                    "buy": sum(pv(act.get(f"plot_{i}")) or 0 for i in (0, 2, 4)), "buyL": pv(act.get("plot_4")) or 0,
                    "sell": sum(pv(act.get(f"plot_{i}")) or 0 for i in (6, 8, 10)), "sellL": pv(act.get("plot_10")) or 0}
bt = sorted(bars)


TRAJ = 20  # barras de trajetoria RAW entregues ao Reader (o material que o olho le no chart)


def confluence(b):
    et = ENTRY[b]; w = [bars[t] for t in bt if t <= et][-LB:]
    if len(w) < 12: return None
    bk = BACK.get(b, {}); rg = bk.get("regime_raw_mapped", {}); sd = bk.get("supply_demand_raw_mapped", {}); f6 = F6.get(b, {})
    traj = []
    for t in [x for x in bt if x <= et][-TRAJ:]:
        x = bars[t]
        traj.append({"t": dt.datetime.utcfromtimestamp(t).strftime("%m-%d %H:%M"),
                     "o": x["o"], "h": x["h"], "l": x["l"], "c": x["c"],
                     "vUp": int(x["up"]) if x["up"] else None, "vDn": int(x["dn"]) if x["dn"] else None,
                     "rsi": round(x["rsi"], 1) if x["rsi"] is not None else None,
                     "bBuy": int(x["buy"]) if x["buy"] else 0, "bSell": int(x["sell"]) if x["sell"] else 0,
                     "nas": next((t2 for t2 in reversed(x["nas"]) if t2), None),
                     "smc": next((t2 for t2 in reversed(x["smc"]) if t2), None)})
    snap = {"svp_state": f6.get("f6_svp_state"), "dist_poc_atr": f6.get("f6_dist_poc_atr"),
            "sup_cat": sd.get("sup_cat"), "dist_supply_atr": sd.get("dist_supply_atr")}
    o = OUT.get(b, {})
    label = "RUNNER" if float(o.get("mfe_R", 0)) >= 10 else ("STOPPER" if o.get("stop_before_2R") == "1" and float(o.get("mfe_R", 9)) < 1.5 else "MID")
    return {"bar_idx": b, "timestamp": dt.datetime.utcfromtimestamp(et).strftime("%Y-%m-%d %H:%M"), "_label_AUDIT_ONLY": label,
            "macro": {"weekly_slope": rg.get("weekly_slope"), "cascade": rg.get("cascade_score"),
                      "macro_broken": rg.get("macro_broken"), "v3": rg.get("v3_state")},
            "snapshot_voice": snap, "trajetoria_RAW": traj}


data = [c for b in SEL if (c := confluence(b))]
with open("results/l2_bpt_confluence_dataset.jsonl", "w") as f:
    for c in data: f.write(json.dumps(c, ensure_ascii=False) + "\n")
nr = sum(1 for c in data if c["_label_AUDIT_ONLY"] == "RUNNER"); ns = sum(1 for c in data if c["_label_AUDIT_ONLY"] == "STOPPER")
print(f"CONFLUENCE EXTRACTOR: {len(data)} episodios (RUNNER {nr} / STOPPER {ns}) -> results/l2_bpt_confluence_dataset.jsonl")

# ---- pacote CEGO: trajetoria RAW + snapshot + macro por episodio; balanceado, embaralhado por bar_idx; SEM label/outcome
import os as _os
OUTD = "results/confluence_reading"; _os.makedirs(OUTD, exist_ok=True)
sel = sorted(data, key=lambda c: c["bar_idx"])  # ordem por bar_idx (nao por label) p/ nao vazar
L = []; a = L.append
a("# PACOTE CEGO — LEITURA CONVERGENTE (confluencia, nao fatores isolados)\n")
a("> Cada episodio traz a TRAJETORIA RAW da perna (preco OHLC, volume Up/Dn, RSI, bubbles Buy/Sell, labels NAS/SMC)")
a("> + a VOZ-SNAPSHOT (value-area svp_state/dist_poc + supply geometry) + macro/regime. LEIA A CONFLUENCIA INTEIRA")
a("> como UM julgamento estrutural — NAO um fator isolado. O snapshot e UMA voz entre as outras, com valor, nao arbitro.")
a("> Voce ve a trajetoria como no chart: decaimento de forca, climax-vendedor-absorvido-que-segura, divergencias de RSI")
a("> (RSI sobe enquanto preco faz fundos mais baixos), cluster de buy-bubbles no fundo, NAS bottom, estrutura SMC.")
a("> Divergencias NAO vem como label (nao serializadas) — leia dos VALORES de RSI. SEM resultado/R/futuro pos-entry.")
a("> Para cada episodio: julgue a CONVICCAO de continuacao/fuel (alta/media/baixa), conte a HISTORIA estrutural,")
a("> diga QUAIS vozes alinham e quais dissentem e como a confluencia resolve. NAO de TAKE/SKIP, score ou gate.\n")
for c in sel:
    m = c["macro"]; s = c["snapshot_voice"]
    a("\n" + "=" * 90); a(f"## EPISODIO {c['bar_idx']} ({c['timestamp']})")
    a(f"- macro/regime: weekly_slope={m['weekly_slope']} cascade={m['cascade']} macro_broken={m['macro_broken']} v3={m['v3']}")
    a(f"- VOZ-snapshot: svp_state={s['svp_state']} dist_poc={s['dist_poc_atr']}ATR | sup_cat={s['sup_cat']} dist_supply={s['dist_supply_atr']}ATR")
    a("- TRAJETORIA RAW (ult 20 barras ate a entry; vUp/vDn=volume comprador/vendedor; bBuy/bSell=bubbles; rsi; labels):")
    a("  | t | O | H | L | C | vUp | vDn | rsi | bBuy | bSell | nas | smc |")
    a("  |---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in c["trajetoria_RAW"]:
        a(f"  | {r['t']} | {r['o']} | {r['h']} | {r['l']} | {r['c']} | {r['vUp']} | {r['vDn']} | {r['rsi']} | {r['bBuy']} | {r['bSell']} | {r['nas'] or ''} | {r['smc'] or ''} |")
text = "\n".join(L)
import re as _re
FORB = ["mfe", "runner", "trap", "winner", "loser", "_audit", "outcome", "monument", "stopper", "_label"]
hits = [x for x in FORB if x in text.lower()] + _re.findall(r"\b\d+(?:\.\d+)?\s*r\b", text.lower())
if hits:
    print("LEAK:", hits[:6]); raise SystemExit(1)
open(f"{OUTD}/reading_packet_BLIND.md", "w").write(text)
print(f"-> pacote cego: {OUTD}/reading_packet_BLIND.md ({len(sel)} episodios, trajetoria RAW; leak-check PASS, sem label/outcome)")

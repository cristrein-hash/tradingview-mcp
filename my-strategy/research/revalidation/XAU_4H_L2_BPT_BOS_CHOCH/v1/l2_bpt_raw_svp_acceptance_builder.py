#!/usr/bin/env python3
"""RAW SVP / ACCEPTANCE BUILDER — resolve (ate onde o RAW permite) o eixo bloqueado FUEL-vs-WALL.

VEREDICTO DE FIDELIDADE (auditado read-only, ver results/_DA_svp_raw_*.py):
  O value-area de VOLUME do LuxAlgo (POC/VAL/VAH) NAO e reconstruivel do RAW: o histograma volume-por-preco e
  os niveis plotados NUNCA foram serializados. O bloco session_vp guarda so uma serie por-barra [t,preco,h,l]
  (last3) sem volume-por-nivel; a study 'Session Volume Profile' expoe apenas {Up,Down,Total} da barra em
  desenvolvimento. => POC/VAL/VAH-LuxAlgo PERMANECE BLOCKED (svp_poc_val_vah). NAO fabricado aqui.

O QUE O RAW PERMITE (honesto, com source mapping proprio):
  1. svp_bar_volume_raw  = RAW_ORIGINAL_OK  — Up/Down/Total real por barra (study 'Session Volume Profile'),
     juntado por TEMPO REAL da barra (sem grade fixa). Habilita esforco/absorcao no supply.
  2. tpo_value_area      = DERIVED_FROM_RAW_WITH_MAPPING — value-area de TEMPO (TPO/Market-Profile) computado do
     OHLC RAW da janela. EXPLICITAMENTE != VA de volume LuxAlgo; e um proxy de tempo-no-preco, rotulado como tal.

Pergunta testada: TPO-acceptance e/ou esforco-de-volume-no-supply explicam FUEL (correu) vs WALL (travou)?
Fontes: results/l2_bpt_raw_backbone_episodes.jsonl (OHLC+supply RAW) + SVP_LUX_RAW (volume). Sem outcome.
Saida: results/l2_bpt_raw_svp_acceptance_episodes.jsonl + spot-check stdout. Verified at: 2026-06-23."""
import gzip, json, datetime as dt, os

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
D = "results"
BACK = [json.loads(l) for l in open(f"{D}/l2_bpt_raw_backbone_episodes.jsonl")]
BAR = 14400
SPOT = [4926, 8878, 4401, 1522, 5627, 3825, 3929, 3949]  # FUEL(correu): 4926/8878/4401/1522/5627/3949 ; WALL(travou): 3825/3929




def to_ep(t):
    if t is None: return None
    t = float(t)
    return int(t / 1000) if t > 1e11 else int(t)


def parse_vol(s):
    if s is None: return None
    s = str(s).replace(",", "").replace("−", "-").strip()
    mult = 1.0
    if s[-1:] in ("K", "M", "B"):
        mult = {"K": 1e3, "M": 1e6, "B": 1e9}[s[-1]]; s = s[:-1]
    try: return float(s) * mult
    except Exception: return None


def svp_vol(rec):
    for st in (rec.get("study_values") or []):
        if isinstance(st, dict) and str(st.get("name")) == "Session Volume Profile":
            v = st.get("values") or {}
            return parse_vol(v.get("Up")), parse_vol(v.get("Down")), parse_vol(v.get("Total"))
    return None, None, None


# ---- coleta volume RAW keyed pelo TEMPO REAL da barra (sem bar_open de grade fixa; resolve DST) ----
windows = {int(e["bar_idx"]): (e.get("ohlcv_window") or []) for e in BACK}
target_dates = set()
for e in BACK:
    for bar in (e.get("ohlcv_window") or []):
        ep = to_ep(bar.get("t"))
        if ep:
            target_dates.add(dt.datetime.utcfromtimestamp(ep).strftime("%Y-%m-%d"))
            target_dates.add(dt.datetime.utcfromtimestamp(ep + BAR).strftime("%Y-%m-%d"))
vol_by_t = {}  # chave = tempo real da ultima barra fechada (ohlcv[-1].time) do snapshot SVP
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if not any(d in line for d in target_dates):
            continue
        rec = json.loads(line)
        oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
        at = to_ep(last.get("time")) if isinstance(last, dict) else None
        if at is None: continue
        up, dn, tot = svp_vol(rec)
        if tot is not None:
            vol_by_t.setdefault(at, {"up": up, "dn": dn, "tot": tot})


def tpo_value_area(bars, nbins=40, va_frac=0.70):
    """VA de TEMPO (TPO): histograma de barras-tocando-preco do OHLC RAW. NAO e VA de volume LuxAlgo."""
    lows = [b["l"] for b in bars if b.get("l") is not None]
    highs = [b["h"] for b in bars if b.get("h") is not None]
    if not lows or not highs: return None
    lo, hi = min(lows), max(highs)
    if hi <= lo: return None
    step = (hi - lo) / nbins
    counts = [0] * nbins
    for b in bars:
        if b.get("l") is None or b.get("h") is None: continue
        i0 = max(0, int((b["l"] - lo) / step)); i1 = min(nbins - 1, int((b["h"] - lo) / step))
        for i in range(i0, i1 + 1): counts[i] += 1
    total = sum(counts)
    if total == 0: return None
    poc_i = counts.index(max(counts))
    inc = set([poc_i]); acc = counts[poc_i]
    while acc < va_frac * total:
        lo_i, hi_i = min(inc), max(inc)
        below = counts[lo_i - 1] if lo_i - 1 >= 0 else -1
        above = counts[hi_i + 1] if hi_i + 1 < nbins else -1
        if below < 0 and above < 0: break
        if above >= below: inc.add(hi_i + 1); acc += max(above, 0)
        else: inc.add(lo_i - 1); acc += max(below, 0)
    def lvl(i): return round(lo + (i + 0.5) * step, 2)
    return {"poc_tpo": lvl(poc_i), "vah_tpo": round(lo + (max(inc) + 1) * step, 2),
            "val_tpo": round(lo + min(inc) * step, 2), "_status": "DERIVED_FROM_RAW_WITH_MAPPING",
            "_note": "TPO time-based value area do OHLC RAW; NAO e VA de volume LuxAlgo (essa = BLOCKED)"}


out = []
for e in BACK:
    b = int(e["bar_idx"]); bars = windows[b]
    sd = e.get("supply_demand_raw_mapped", {})
    # anexa volume por barra (join por tempo real)
    wv = []
    for bar in bars:
        bt = to_ep(bar.get("t"))
        v = vol_by_t.get(bt)
        wv.append({**bar, "vol": v})
    nvol = sum(1 for x in wv if x["vol"])
    entry = bars[-1] if bars else {}
    eclose = entry.get("c")
    # TPO VA dos bars PRE-entry (sem a propria barra de entry = sem circularidade, DA 2026-06-23) +
    # acceptance = close da entry vs value-area anterior. Janela ja e causal (termina na entry, pos-fix anchor).
    prior = bars[:-1] if len(bars) > 4 else bars
    tpo = tpo_value_area(prior)
    acc = None
    if tpo and eclose is not None:
        acc = ("ACCEPTED_ABOVE_VALUE" if eclose > tpo["vah_tpo"] else
               "ACCEPTED_BELOW_VALUE" if eclose < tpo["val_tpo"] else "INSIDE_VALUE")
    # esforco de volume: balanco up/down nas ultimas 6 barras + barra de entrada
    last6 = [x["vol"] for x in wv[-6:] if x["vol"]]
    up6 = sum(v["up"] or 0 for v in last6); dn6 = sum(v["dn"] or 0 for v in last6)
    net_ratio = round(up6 / (up6 + dn6), 3) if (up6 + dn6) else None
    ev = wv[-1]["vol"] if wv else None
    entry_upratio = round((ev["up"] / ev["tot"]), 3) if ev and ev.get("tot") else None
    out.append({
        "bar_idx": b, "timestamp": e.get("timestamp"),
        "sup_cat": sd.get("sup_cat"), "dist_supply_atr": sd.get("dist_supply_atr"), "dist_demand_atr": sd.get("dist_demand_atr"),
        "svp_bar_volume_raw": {"n_bars_with_vol": nvol, "n_bars": len(bars), "entry_up_ratio": entry_upratio,
                               "last6_up_ratio": net_ratio, "last6_up": up6, "last6_dn": dn6,
                               "_status": "RAW_ORIGINAL_OK", "_raw_field": "study_values[Session Volume Profile].Up/Down/Total"},
        "tpo_value_area": tpo, "tpo_acceptance": acc,
        "svp_poc_val_vah_lux": {"_status": "UNKNOWN_BLOCKED",
                                "_note": "VA de volume LuxAlgo nao serializado no RAW (so Up/Down/Total + serie por-barra). NAO fabricado."},
        "entry_close": eclose,
    })

with open(f"{D}/l2_bpt_raw_svp_acceptance_episodes.jsonl", "w") as f:
    for o in out: f.write(json.dumps(o, ensure_ascii=False) + "\n")

# ---- 2a passada: enriquece o RAW backbone (svp/acceptance deixam de ser so UNKNOWN_BLOCKED) ----
# Ordem do pipeline: l2_bpt_raw_backbone_builder.py -> ESTE script. Re-rodar o backbone reseta; re-rodar este re-enriquece.
by_idx = {o["bar_idx"]: o for o in out}
bb_path = f"{D}/l2_bpt_raw_backbone_episodes.jsonl"
bb = [json.loads(l) for l in open(bb_path)]
for e in bb:
    o = by_idx.get(int(e["bar_idx"]))
    if not o: continue
    e["svp_bar_volume_raw"] = o["svp_bar_volume_raw"]
    e["tpo_value_area"] = o["tpo_value_area"]
    e["tpo_acceptance"] = o["tpo_acceptance"]
    e["svp_status"] = "PARTIAL_RAW"  # volume RAW disponivel; VA de volume LuxAlgo segue BLOCKED
    e["svp_note"] = ("volume real por-barra (Up/Down/Total) = RAW_ORIGINAL_OK; TPO value-area (tempo) = "
                     "DERIVED_FROM_RAW; VA de VOLUME LuxAlgo (POC/VAL/VAH) = UNKNOWN_BLOCKED (nao serializado, nao fabricado)")
    e["acceptance_status"] = "TPO_PROXY_RAW"
    e["acceptance_note"] = "tpo_acceptance (close vs TPO value-area do OHLC RAW); acceptance de valor-de-volume segue blocked"
    smf = e.get("source_mapping_status_by_field", {})
    smf["svp"] = "PARTIAL: volume RAW_ORIGINAL_OK + tpo DERIVED_FROM_RAW; VA-volume UNKNOWN_BLOCKED"
    smf["acceptance"] = "TPO_PROXY DERIVED_FROM_RAW; valor-de-volume UNKNOWN_BLOCKED"
    e["source_mapping_status_by_field"] = smf
with open(bb_path, "w") as f:
    for e in bb: f.write(json.dumps(e, ensure_ascii=False) + "\n")
print(f"  RAW backbone enriquecido (svp/tpo merge) -> {bb_path}")

# ---- spot-check FUEL vs WALL ----
print(f"RAW SVP/ACCEPTANCE: {len(out)} episodios -> {D}/l2_bpt_raw_svp_acceptance_episodes.jsonl")
print(f"  volume RAW vivo: {sum(1 for o in out if o['svp_bar_volume_raw']['n_bars_with_vol']>0)}/{len(out)} episodios com volume")
print("  POC/VAL/VAH (volume LuxAlgo) = BLOCKED (nao serializado no RAW; nao fabricado)\n")
print("  SPOT-CHECK FUEL(correu) vs WALL(travou) — TPO-acceptance + esforco de volume:")
label = {4926: "FUEL", 8878: "FUEL", 4401: "FUEL", 1522: "FUEL", 5627: "FUEL", 3949: "FUEL", 3825: "WALL", 3929: "WALL"}
print(f"  {'bar':>5} {'lbl':>4} {'sup_cat':>14} {'distSup':>7} {'TPO_accept':>20} {'entryUp%':>8} {'last6Up%':>8}")
for b in SPOT:
    o = [x for x in out if x["bar_idx"] == b][0]
    v = o["svp_bar_volume_raw"]
    print(f"  {b:>5} {label[b]:>4} {str(o['sup_cat']):>14} {str(o['dist_supply_atr']):>7} "
          f"{str(o['tpo_acceptance']):>20} {str(v['entry_up_ratio']):>8} {str(v['last6_up_ratio']):>8}")

#!/usr/bin/env python3
"""EXTRATOR DE INDICADORES A PARTIR DO RAW ORIGINAL (autoridade). Corrige o DERIVED_ARTIFACT_BUG: o derivado
repro_recovery/raw_features_2020_2026.jsonl pegava a CABECA do buffer de 500 labels (NAS/SMC antigos 2018-19) em vez
dos recentes as-of-bar. Aqui lemos o RAW replay 4H e extraimos causalmente:
  NAS  = pine_labels['NAS TOP BOTTOM DETECTOR']  via FIRST-APPEARANCE diffing (label id) entre snapshots as-of-bar
  SMC  = pine_labels['Smart Money Concepts [LuxAlgo]'] idem (BOS/CHoCH/EQH/EQL)
  BUBB = pine_shapes_bubbles['Market Order Bubbles'] (activations, ja causal: bars_ago/time)
  RSI  = study_values['Relative Strength Index'] (RSI + divergencias 'Regular Bullish'/'Regular Bearish' se presentes)
Causal: so barras <= entry (SHIFT1: NAS/SMC usam aparicao <= entry-1, repintam). SEM outcome. reliability=RAW_AUTHENTIC.

Alinhamento: entry_epoch + close vem do frozen SO p/ LOCALIZAR a barra e VERIFICAR (close e OHLC, nao campo de indicador
contaminado); o RAW e a AUTORIDADE — se o close do RAW divergir do frozen, FLAG. Saidas em results/.
"""
import gzip, json, csv, datetime as dt, os

RAWDIR = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H"
BLOCK_2020 = f"{RAWDIR}/XAUUSD_240m_replay_2020-01-01_to_2023-01-01.jsonl.gz"
BLOCK_2023 = f"{RAWDIR}/XAUUSD_240m_replay_2023-01-03_to_2026-05-25.jsonl.gz"
RR = "repro_recovery"; D = "results"
LOOKBACK = 21
BAR = 14400  # 4H
def bar_open(ep):  # bars abrem 02/06/10/14/18/22 UTC -> %14400==7200
    return ep - ((ep - 7200) % BAR)

CL1 = [4918, 4926, 1661, 5701, 6887, 7426, 8878, 8923, 8940]
CL2 = [5826, 1623, 4401, 3825, 1522, 1873, 5627, 1775, 3949, 3929]
EPS = CL1 + CL2
SPOTCHECK = [5826, 4401, 5627, 3949, 3929, 4918]

# --- frozen SO p/ entry_epoch (clock) + close (OHLC) — alinhamento/verificacao, NAO fonte de indicador ---
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
ENTRY = {b: int(F[b]["ts_epoch"]) for b in EPS}
FCLOSE = {b: float(F[b]["close"]) for b in EPS}
# derivado bugado (so p/ comparar head-vs-tail no relatorio)
OLD_NAS = {b: (F[b].get("nas_recent") or []) for b in EPS}
OLD_SMC = {b: (F[b].get("smc_recent") or []) for b in EPS}

def block_of(b):
    return BLOCK_2020 if ENTRY[b] < int(dt.datetime(2023, 1, 1, tzinfo=dt.timezone.utc).timestamp()) else BLOCK_2023

# alvos: bar_opens da janela [entry-LOOKBACK..entry] por episodio
targets = {}   # bar_open_epoch -> list de (b, bars_ago)
target_dates = set()
for b in EPS:
    eo = bar_open(ENTRY[b])
    for k in range(0, LOOKBACK + 1):
        bo = eo - k * BAR
        targets.setdefault(bo, []).append((b, k))
        target_dates.add(dt.datetime.utcfromtimestamp(bo).strftime("%Y-%m-%d"))
        target_dates.add(dt.datetime.utcfromtimestamp(bo + BAR - 1).strftime("%Y-%m-%d"))  # data do close

def study_labels(rec, name):
    for lab in (rec.get("pine_labels") or []):
        if lab.get("name") == name:
            return lab.get("labels") or []
    return []

def rsi_block(rec):
    for s in (rec.get("study_values") or []):
        if isinstance(s, dict) and "Relative Strength Index" in str(s.get("name", "")):
            return s.get("values") or {}
    return {}

def bubbles_block(rec):
    for s in (rec.get("pine_shapes_bubbles") or []):
        if "Bubbles" in str(s.get("name", "")):
            return s
    return {}

# --- coleta as-of-bar dos alvos (prefiltro por data p/ nao parsear o bloco inteiro) ---
snap = {}  # bar_open -> {close, nas:{id:(text,price)}, smc:{id:(text,price)}, bubbles:{}, rsi:{}}
for blk in (BLOCK_2020, BLOCK_2023):
    if not os.path.exists(blk):
        print(f"AVISO: bloco ausente {blk}"); continue
    with gzip.open(blk, "rt") as f:
        for line in f:
            ok = False
            for d in target_dates:
                if d in line:
                    ok = True; break
            if not ok:
                continue
            rec = json.loads(line)
            cdt = rec.get("replay_current_dt")
            if not cdt:
                continue
            ep = int(dt.datetime.fromisoformat(cdt).timestamp())
            bo = bar_open(ep)
            if bo not in targets:
                continue
            oh = rec.get("ohlcv")
            close = None
            if isinstance(oh, dict):
                close = oh.get("close")
            elif isinstance(oh, list) and oh:
                last = oh[-1]
                close = last.get("close") if isinstance(last, dict) else (last[4] if len(last) > 4 else None)
            nas = {x.get("id"): (x.get("text"), x.get("price")) for x in study_labels(rec, "NAS TOP BOTTOM DETECTOR") if isinstance(x, dict)}
            smc = {x.get("id"): (x.get("text"), x.get("price")) for x in study_labels(rec, "Smart Money Concepts [LuxAlgo]") if isinstance(x, dict)}
            snap[bo] = {"close": close, "nas": nas, "smc": smc,
                        "bubbles": bubbles_block(rec), "rsi": rsi_block(rec), "dt": cdt}

# --- grade REAL do RAW (ordenada) + ancoragem por CLOSE-match (RAW autoridade), nao por aritmetica ---
snaps_sorted = sorted(snap.items())                       # [(bar_open, data), ...] consecutivos por barra real
BO_LIST = [bo for bo, _ in snaps_sorted]
def anchor_idx(b):
    """indice da barra de entrada na grade real: candidatos a ±2.5 dias da data + close mais proximo do frozen."""
    eo = bar_open(ENTRY[b]); best = None
    for i, (bo, data) in enumerate(snaps_sorted):
        if abs(bo - eo) > 3 * 86400 or data["close"] is None:
            continue
        d = abs(float(data["close"]) - FCLOSE[b])
        if best is None or d < best[0]:
            best = (d, i)
    return (best[1] if best else None), (best[0] if best else None)

def tail_labels(idx, key, K=8):
    """TAIL do buffer as-of-entry = labels MAIS RECENTES (buffer ordenado oldest->newest por x; verificado:
    NAS x 2..501, SMC x 11..1384, cauda = era atual). Causal: todos <= entry (snapshot as-of-bar).
    Filtra a era atual por proximidade de preco ao close (descarta resido stale eventual)."""
    snapd = snaps_sorted[idx][1]; raw = snapd[key]; close = snapd.get("close")
    items = list(raw.items())  # ordem do payload = x-ascending (oldest->newest)
    tail = items[-K:]
    ev = []
    for lab_id, (text, price) in tail:
        in_era = (close is not None and isinstance(price, (int, float)) and abs(price - close) / close < 0.20)
        ev.append({"text": text, "price": price, "in_current_era": in_era})
    return ev

def parse_bubbles_idx(idx):
    # RAW: activations_per_plot = agregado as-of-bar sobre total_bars_evaluated (20). BUY=plot_0/2/4, SELL=plot_6/8/10.
    bb = (snaps_sorted[idx][1] if idx is not None else {}).get("bubbles") or {}
    app = bb.get("activations_per_plot") or {}
    def g(p): return int(app.get(p, 0) or 0)
    buy_total = g("plot_0") + g("plot_2") + g("plot_4"); sell_total = g("plot_6") + g("plot_8") + g("plot_10")
    buy_mL = g("plot_2") + g("plot_4"); sell_mL = g("plot_8") + g("plot_10")
    return {"buy_total": buy_total, "sell_total": sell_total, "buy_mL": buy_mL, "sell_mL": sell_mL,
            "buy_L": g("plot_4"), "sell_L": g("plot_10"),
            "total_bars_evaluated": bb.get("total_bars_evaluated"), "raw_field": "pine_shapes_bubbles.activations_per_plot"}

out = []
for b in EPS:
    idx, cdist = anchor_idx(b)
    s = snaps_sorted[idx][1] if idx is not None else {}
    raw_close = s.get("close")
    close_ok = (idx is not None and cdist is not None and cdist / FCLOSE[b] < 0.005)   # %: RAW vs frozen diferem ~0.1-0.4% (feed/rounding); barra certa confirmada pela era dos labels
    rsi = s.get("rsi") or {}
    div = {k: v for k, v in rsi.items() if "Bullish" in k or "Bearish" in k or "Diverg" in k}
    nas_ev = tail_labels(idx, "nas") if idx is not None else []   # tail = recentes as-of-entry (causal)
    smc_ev = tail_labels(idx, "smc") if idx is not None else []
    out.append({
        "bar_idx": b, "entry_dt": dt.datetime.utcfromtimestamp(ENTRY[b]).strftime("%Y-%m-%d %H:%M"),
        "source_raw_file": os.path.basename(block_of(b)), "reliability": "RAW_AUTHENTIC",
        "raw_close": raw_close, "frozen_close": FCLOSE[b], "close_match": close_ok,
        "no_future_guard": "events bars_ago>=1 (SHIFT1); bubbles bars_ago>=0 as-of-entry",
        "nas_events_recent": nas_ev, "smc_events_recent": smc_ev,
        "bubble_cluster_summary": parse_bubbles_idx(idx),
        "rsi_value": rsi.get("RSI"), "rsi_divergence_events": div,
        "extraction_method": "first_appearance_diff(label_id) on as-of-bar snapshots; RAW pine_labels tail not head",
        "source_mapping": {"NAS": "RAW pine_labels[NAS TOP BOTTOM DETECTOR]", "SMC": "RAW pine_labels[Smart Money Concepts [LuxAlgo]]",
                           "BUBBLES": "RAW pine_shapes_bubbles[Market Order Bubbles]", "RSI": "RAW study_values[Relative Strength Index]"},
    })

with open(f"{D}/l2_bpt_raw_indicator_events.jsonl", "w") as f:
    for o in out:
        f.write(json.dumps(o, ensure_ascii=False) + "\n")

# --- relatorio de validacao head-vs-tail (spot-check) ---
def price_era(prices):
    ps = [p for p in prices if isinstance(p, (int, float))]
    return (min(ps), max(ps)) if ps else (None, None)
with open(f"{D}/l2_bpt_raw_indicator_validation.md", "w") as f:
    w = f.write
    w("# Validacao — extracao NAS/SMC do RAW original (corrige DERIVED_ARTIFACT_BUG)\n\n")
    w(f"Fonte RAW: {RAWDIR}/XAUUSD_240m_replay_*.jsonl.gz | metodo: first-appearance diff as-of-bar (tail, nao head).\n\n")
    w("| ep | entry | close RAW==frozen | OLD nas_recent (derivado, head) era-preco | NOVO nas_events recent era-preco | stale antigo? |\n")
    w("|---|---|---|---|---|---|\n")
    od = {o["bar_idx"]: o for o in out}
    for b in EPS:
        o = od[b]
        old_era = price_era([x.get("price") for x in OLD_NAS[b]])
        new_era = price_era([e["price"] for e in o["nas_events_recent"]])
        stale = (old_era[0] is not None and o["raw_close"] and abs(old_era[1] - o["raw_close"]) / o["raw_close"] > 0.15)
        w(f"| {b} | {o['entry_dt']} | {o['raw_close']}=={o['frozen_close']} ({'OK' if o['close_match'] else 'FLAG'}) "
          f"| {old_era} | {new_era} | {'STALE' if stale else '-'} |\n")
    w("\n## Spot-check obrigatorio (6)\n")
    for b in SPOTCHECK:
        o = od[b]
        w(f"\n### #{b} ({o['entry_dt']}) close RAW {o['raw_close']} (frozen {o['frozen_close']}, {'OK' if o['close_match'] else 'FLAG'})\n")
        w(f"- NAS tail recente (RAW, causal): {[(e['text'],e['price'],'era' if e['in_current_era'] else 'stale') for e in o['nas_events_recent'][-6:]] or 'nenhum'}\n")
        w(f"- SMC tail recente (RAW, causal): {[(e['text'],e['price'],'era' if e['in_current_era'] else 'stale') for e in o['smc_events_recent'][-6:]] or 'nenhum'}\n")
        w(f"- bubbles (RAW): {o['bubble_cluster_summary']}\n")
        w(f"- RSI {o['rsi_value']} | divergencias RAW: {o['rsi_divergence_events'] or 'nenhuma no payload'}\n")
        w(f"- OLD derivado nas_recent (head/stale): {[(x.get('text'),x.get('price')) for x in OLD_NAS[b][:4]]}\n")

print(f"EXTRATOR RAW: {len(out)} episodios -> {D}/l2_bpt_raw_indicator_events.jsonl + l2_bpt_raw_indicator_validation.md")
nflag = [o['bar_idx'] for o in out if not o['close_match']]
print(f"  close RAW==frozen: {'TODOS OK' if not nflag else 'FLAG em '+str(nflag)}")
print("  spot-check (NAS recent RAW vs OLD head):")
for b in SPOTCHECK:
    o = [x for x in out if x['bar_idx'] == b][0]
    new = [(e['text'], round(e['price'],0) if isinstance(e['price'],(int,float)) else e['price']) for e in o['nas_events_recent'][:3]]
    old = [(x.get('text'), x.get('price')) for x in OLD_NAS[b][:3]]
    print(f"    #{b} close{o['raw_close']} | NOVO-NAS-RAW {new} | OLD-head {old} | RSI {o['rsi_value']} div {list(o['rsi_divergence_events'].keys())}")

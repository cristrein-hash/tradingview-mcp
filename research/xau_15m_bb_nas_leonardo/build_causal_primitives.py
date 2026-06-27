#!/usr/bin/env python3
"""XAU 15M BigBeluga+NAS — EXTRATOR CAUSAL DE PRIMITIVAS, fonte RAW gz EXCLUSIVA (zero dados secundários).
Single-pass stateful sobre os snapshots (cada registro = chart as-of close da barra). Deriva, só do RAW:
  • série OHLC contínua (acumula tails de 5 barras) + RSI por barra (study_values) + ATR14 + EMA21
  • eventos NAS (pine_labels text LONG/SHORT, first-appearance via id monotônico — NUNCA NAS_*_SIGNAL/TOP/BOTTOM)
  • eventos SMC (pine_labels LuxAlgo: BOS/CHoCH/EQH/EQL, first-appearance) = estrutura/fluxo operacional
  • registro de ZONAS Custom OB (=BigBeluga proxy): all_boxes id estável → born/last_seen/removed, text SUPPLY/DEMAND,
    high/low/width, x1/x2 (=ciclo de vida: virgem/mitigada/idade/permanência-após-stop p/ reentry)
Causalidade: first-appearance por id (ids monotônicos; 1º snapshot só inicializa, não emite). Consumo a jusante usa
SHIFT1 (indicadores repintam). Saída: <bloco>.primitives.json + sumário de validação. Verified 2026-06-25."""
import gzip, json, sys, math
from pathlib import Path
RAW = Path("/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M")
OUT = Path(__file__).parent / "primitives"; OUT.mkdir(exist_ok=True)
def grp(rec, key, sub):
    return next((x for x in (rec.get(key) or []) if sub.lower() in str(x.get("name", "")).lower()), None)
def fnum(x):
    try: return float(str(x).replace("−", "-"))
    except Exception: return None

def process_block(path):
    # ---- carrega snapshots em ordem temporal ----
    snaps = []
    with gzip.open(path, "rt") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except Exception: continue
            if isinstance(r, dict) and r.get("ohlcv"): snaps.append(r)
    snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
    bars = {}                      # time -> {o,h,l,c,v}
    rsi_by_t = {}                  # time -> rsi (barra corrente do snapshot)
    nas_dist_by_t = {}             # time -> NAS_DISTANCE_FROM_EMA_ATR
    nas_events, smc_events = [], []
    zones = {}                     # id -> dict(text,high,low,born_t,last_t,x1,x2,pre_existing)
    max_nas, max_smc = -1, -1
    nas_init = smc_init = False    # init POR-STREAM: seed no 1º snapshot que TEM labels (não no 1º snapshot bruto)
    first_snap = True              # só p/ tag pre_existing das zonas
    for r in snaps:
        oh = r.get("ohlcv") or []
        cur_t = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
        for b in oh:
            if isinstance(b, dict) and b.get("time") is not None:
                bars[b["time"]] = {"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"], "v": b.get("volume")}
        # RSI + NAS distance (barra corrente)
        rv = grp(r, "study_values", "Relative Strength")
        if rv and cur_t is not None: rsi_by_t[cur_t] = fnum((rv.get("values") or {}).get("RSI"))
        nv = grp(r, "study_values", "NAS")
        if nv and cur_t is not None: nas_dist_by_t[cur_t] = fnum((nv.get("values") or {}).get("NAS_DISTANCE_FROM_EMA_ATR"))
        # NAS labels (first-appearance por id; seed no 1º snapshot COM labels p/ não emitir histórico pré-existente)
        ng = grp(r, "pine_labels", "NAS")
        ng_ids = [l.get("id") for l in (ng.get("labels") or []) if l.get("id") is not None] if ng else []
        if not nas_init:
            if ng_ids: max_nas = max(ng_ids); nas_init = True
        else:
            for l in (ng.get("labels") or []) if ng else []:
                lid = l.get("id")
                if lid is None or lid <= max_nas: continue
                txt = str(l.get("text", "")).upper()
                if "LONG" in txt or "SHORT" in txt:
                    nas_events.append({"t": cur_t, "id": lid, "dir": "LONG" if "LONG" in txt else "SHORT",
                                        "price": l.get("price"), "x": l.get("x")})
            if ng_ids: max_nas = max(max_nas, max(ng_ids))
        # SMC labels (BOS/CHoCH/EQH/EQL) first-appearance
        sg = grp(r, "pine_labels", "Smart Money")
        sg_ids = [l.get("id") for l in (sg.get("labels") or []) if l.get("id") is not None] if sg else []
        if not smc_init:
            if sg_ids: max_smc = max(sg_ids); smc_init = True
        else:
            for l in (sg.get("labels") or []) if sg else []:
                lid = l.get("id")
                if lid is None or lid <= max_smc: continue
                smc_events.append({"t": cur_t, "id": lid, "text": l.get("text"), "price": l.get("price"), "x": l.get("x")})
            if sg_ids: max_smc = max(max_smc, max(sg_ids))
        # ZONAS Custom OB (all_boxes id estável)
        ob = grp(r, "pine_boxes", "Custom OB")
        for bx in (ob.get("all_boxes") if ob else []) or []:
            zid = bx.get("id")
            if zid is None: continue
            if zid not in zones:
                zones[zid] = {"text": str(bx.get("text", "")).upper(), "high": bx.get("high"), "low": bx.get("low"),
                               "born_t": cur_t, "last_t": cur_t, "x1": bx.get("x1"), "x2": bx.get("x2"),
                               "pre_existing": first_snap}
            else:
                zones[zid]["last_t"] = cur_t
                zones[zid]["high"] = bx.get("high"); zones[zid]["low"] = bx.get("low")  # extensão dinâmica
        first_snap = False
    # ---- série ordenada + ATR14 + EMA21 ----
    ts = sorted(bars)
    series = []
    ema = None; kE = 2 / 22; trs = []
    for i, t in enumerate(ts):
        b = bars[t]; o, h, l, c = b["o"], b["h"], b["l"], b["c"]
        ema = c if ema is None else c * kE + ema * (1 - kE)
        if i > 0:
            pc = bars[ts[i - 1]]["c"]; trs.append(max(h - l, abs(h - pc), abs(l - pc)))
        atr = sum(trs[-14:]) / 14 if len(trs) >= 14 else None
        series.append({"t": t, "o": o, "h": h, "l": l, "c": c, "v": b["v"],
                        "rsi": rsi_by_t.get(t), "nas_dist": nas_dist_by_t.get(t), "atr": atr, "ema21": ema})
    out = {"block": path.name, "n_bars": len(series), "t_start": ts[0] if ts else None, "t_end": ts[-1] if ts else None,
           "series": series, "nas_events": nas_events, "smc_events": smc_events,
           "zones": [{"id": k, **v} for k, v in zones.items()]}
    dst = OUT / (path.name.replace(".jsonl.gz", "") + ".primitives.json")
    dst.write_text(json.dumps(out, default=str))
    # ---- sumário de validação ----
    # ASSERT anti-flood (landmine detector p/ init-bug/overflow): nenhum timestamp deve concentrar >10 eventos
    from collections import Counter
    for nm, ev in (("NAS", nas_events), ("SMC", smc_events)):
        c = Counter(e["t"] for e in ev)
        if c and max(c.values()) > 10:
            t_bad, k = c.most_common(1)[0]
            print(f"  ⚠️ FLOOD {nm}: {k} eventos no mesmo t={t_bad} (>10) — possível init-bug/overflow. INVESTIGAR.")
    nl = sum(1 for e in nas_events if e["dir"] == "LONG"); ns = len(nas_events) - nl
    sup = sum(1 for z in zones.values() if "SUPPLY" in z["text"]); dem = sum(1 for z in zones.values() if "DEMAND" in z["text"])
    bos = sum(1 for e in smc_events if "BOS" in str(e["text"])); ch = sum(1 for e in smc_events if "CHoCH" in str(e["text"]))
    print(f"{path.name}")
    print(f"  bars={len(series)} | {out['t_start']}→{out['t_end']}")
    print(f"  NAS events: LONG={nl} SHORT={ns} (total {len(nas_events)})")
    print(f"  SMC events: BOS={bos} CHoCH={ch} (total {len(smc_events)})")
    print(f"  zonas Custom OB: SUPPLY={sup} DEMAND={dem} total={len(zones)} (pre_existing={sum(1 for z in zones.values() if z['pre_existing'])})")
    print(f"  RSI cobertura: {sum(1 for s in series if s['rsi'] is not None)}/{len(series)} | ATR ok: {sum(1 for s in series if s['atr'])}/{len(series)}")
    print(f"  -> {dst.name}\n")
    return out

if __name__ == "__main__":
    blocks = sorted(p for p in RAW.glob("XAUUSD_15m_replay_*.jsonl.gz") if "superseded" not in str(p))
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target == "all":
        for b in blocks: process_block(b)
    else:
        process_block(Path(target) if target else blocks[0])

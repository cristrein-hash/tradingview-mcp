#!/usr/bin/env python3
"""FEASIBILIDADE READ-ONLY — o volume real por-barra (study 'Session Volume Profile' Up/Down/Total) esta vivo
historicamente e difere entre um caso FUEL (4926 correu) e um WALL (3929 travou)? So confirma viabilidade do
sinal RAW antes de construir o builder. NAO fabrica POC/VAL/VAH. Verified at: 2026-06-23."""
import gzip, json, datetime as dt, os, bisect

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"
RR = "repro_recovery"
BAR = 14400
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
# 4926 = FUEL (correu +18R), 3929 = WALL (travou +0.05R)
EPS = {4926: "FUEL(correu)", 3929: "WALL(travou)"}
ENTRY = {b: int(F[b]["ts_epoch"]) for b in EPS}
FCLOSE = {b: float(F[b]["close"]) for b in EPS}
def bar_open(ep): return ep - ((ep - 7200) % BAR)


def parse_vol(s):
    if s is None: return None
    s = str(s).replace(",", "").replace("−", "-").strip()
    mult = 1.0
    if s.endswith("K"): mult, s = 1e3, s[:-1]
    elif s.endswith("M"): mult, s = 1e6, s[:-1]
    elif s.endswith("B"): mult, s = 1e9, s[:-1]
    try: return float(s) * mult
    except Exception: return None


def svp_study(rec):
    for st in (rec.get("study_values") or []):
        if isinstance(st, dict) and str(st.get("name")) == "Session Volume Profile":
            v = st.get("values") or {}
            return parse_vol(v.get("Up")), parse_vol(v.get("Down")), parse_vol(v.get("Total"))
    return None, None, None


def rec_close(rec):
    oh = rec.get("ohlcv")
    if isinstance(oh, list) and oh: return oh[-1].get("close")
    if isinstance(oh, dict): return oh.get("close")
    return None


# datas-alvo: janela de 16 barras antes de cada entry
target = set()
for b in EPS:
    eo = bar_open(ENTRY[b])
    for k in range(0, 17):
        target.add(dt.datetime.utcfromtimestamp(eo - k * BAR).strftime("%Y-%m-%d"))
snap = {}
with gzip.open(SVP, "rt") as fh:
    for line in fh:
        if not any(d in line for d in target):
            continue
        rec = json.loads(line); cdt = rec.get("replay_current_dt")
        if not cdt: continue
        bo = bar_open(int(dt.datetime.fromisoformat(cdt).timestamp()))
        up, dn, tot = svp_study(rec)
        oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else {}
        snap[bo] = {"close": rec_close(rec), "high": last.get("high"), "low": last.get("low"),
                    "up": up, "dn": dn, "tot": tot, "dt": cdt}
ss = sorted(snap.items())
ts = [b for b, _ in ss]
print(f"# snapshots SVP coletados na janela: {len(ss)}")
for b in EPS:
    eo = bar_open(ENTRY[b])
    # anchor por close-match
    best = None
    for i, (bo, d) in enumerate(ss):
        if d["close"] is None or abs(bo - eo) > 3 * 86400: continue
        dd = abs(float(d["close"]) - FCLOSE[b])
        if best is None or dd < best[0]: best = (dd, i)
    print(f"\n=== EP {b} {EPS[b]} entry_close={FCLOSE[b]} anchor_dd={best[0]:.3f} ===")
    idx = best[1]
    win = ss[max(0, idx - 9):idx + 1]
    for bo, d in win:
        ratio = (d["up"] / d["tot"]) if d["up"] is not None and d["tot"] else None
        print(f"  {d['dt'][:16]} close={d['close']} H={d['high']} L={d['low']} "
              f"up={d['up']} dn={d['dn']} tot={d['tot']} up/tot={round(ratio,2) if ratio is not None else None}")

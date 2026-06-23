#!/usr/bin/env python3
"""VERIFICA o look-ahead apontado pelo DA: a janela ohlcv_window do backbone (anchor close-match) termina
DEPOIS da barra de entry? Para cada episodio compara bar_open(window[-1].t) vs bar_open(ENTRY). >0 = futuro
(LOOK-AHEAD). Read-only. Verified at: 2026-06-23."""
import json, datetime as dt

RR = "repro_recovery"
BACK = [json.loads(l) for l in open("results/l2_bpt_raw_backbone_episodes.jsonl")]
F = [json.loads(l) for l in open(f"{RR}/raw_features_2020_2026.jsonl")]
BAR = 14400


def bar_open(ep): return ep - ((ep - 7200) % BAR)


def to_ep(t):
    if t is None: return None
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)


print(f"{'bar':>6} {'entry_dt':>16} {'win_last_dt':>16} {'Δbars':>6} {'flag':>12}")
nbad = 0; nfwd = 0
for e in BACK:
    b = int(e["bar_idx"]); entry_ep = int(F[b]["ts_epoch"]); eo = bar_open(entry_ep)
    win = e.get("ohlcv_window") or []
    if not win:
        print(f"{b:>6} (sem janela)"); continue
    last_t = to_ep(win[-1].get("t")); lo = bar_open(last_t) if last_t else None
    dbars = round((lo - eo) / BAR) if lo else None
    flag = ""
    if dbars is None: flag = "NO_T"
    elif dbars > 0: flag = "FUTURO!"; nfwd += 1
    elif dbars < -2: flag = "WRONG_SESSION"; nbad += 1
    edt = dt.datetime.utcfromtimestamp(eo).strftime("%Y-%m-%d %H:%M")
    ldt = dt.datetime.utcfromtimestamp(lo).strftime("%Y-%m-%d %H:%M") if lo else "?"
    print(f"{b:>6} {edt:>16} {ldt:>16} {str(dbars):>6} {flag:>12}")
print(f"\nRESUMO: {nfwd}/19 com barra(s) FUTURA(s) na janela | {nbad}/19 sessao errada (<-2 bars)")
print("Se nfwd>0: look-ahead REAL na janela que o reader cego viu (e no TPO/supply do backbone).")

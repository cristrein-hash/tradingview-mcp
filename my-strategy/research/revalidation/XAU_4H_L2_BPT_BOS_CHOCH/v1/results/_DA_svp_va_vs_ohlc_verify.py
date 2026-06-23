#!/usr/bin/env python3
"""VERIFICACAO DECISIVA: session_vp.last3[i].v=[t,X1,X2,X3] e VALUE-AREA [t,POC,VAH,VAL] ou OHLC [t,close,high,low]?
Teste: [X2,X3] bate com [high,low] REAL da barra (=OHLC) ou nao (=VA)? Compara o item mais novo de last3 (cujo t
== ohlcv[-1].time) contra o ohlcv[-1] high/low/close da mesma barra. Read-only. Verified at: 2026-06-23."""
import gzip, json, datetime as dt

SVP = "/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/4H/XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz"


def to_ep(t):
    t = float(t); return int(t / 1000) if t > 1e11 else int(t)


def main():
    n = 0; match_hl = 0; va_inside = 0; va_outside = 0; rows = []
    with gzip.open(SVP, "rt") as fh:
        for line in fh:
            rec = json.loads(line)
            oh = rec.get("ohlcv"); last = oh[-1] if isinstance(oh, list) and oh else None
            svp = rec.get("session_vp") or {}; l3 = svp.get("last3") or []
            if not isinstance(last, dict) or not l3: continue
            bt = to_ep(last.get("time"))
            # item de last3 cujo t == ohlcv[-1].time
            it = next((e for e in l3 if isinstance(e, dict) and to_ep((e.get("v") or [0])[0]) == bt), None)
            if not it: continue
            v = it.get("v") or []
            if len(v) < 4: continue
            x1, x2, x3 = v[1], v[2], v[3]
            bh, bl, bc = last.get("high"), last.get("low"), last.get("close")
            if bh is None or bl is None: continue
            n += 1
            # bate exatamente com high/low da barra? (=OHLC)
            if abs(x2 - bh) < 0.01 and abs(x3 - bl) < 0.01: match_hl += 1
            # X2..X3 estritamente DENTRO do range da barra? (=VA developing pode ser dentro)
            if x2 <= bh + 0.01 and x3 >= bl - 0.01: va_inside += 1
            else: va_outside += 1
            if n <= 8:
                rows.append((dt.datetime.utcfromtimestamp(bt).strftime("%Y-%m-%d %H:%M"),
                             round(x1, 2), round(x2, 2), round(x3, 2), bh, bl, bc,
                             "OHLC?" if (abs(x2-bh) < 0.01 and abs(x3-bl) < 0.01) else "VA(≠H/L)"))
            if n >= 4000: break
    print(f"# barras comparadas: {n}")
    print(f"  [X2,X3]==[high,low] da barra (=seria OHLC): {match_hl}/{n}")
    print(f"  [X2,X3] dentro do range da barra: {va_inside}/{n} | fora: {va_outside}/{n}")
    print(f"  VEREDITO: {'OHLC (X=close,high,low)' if match_hl > n*0.5 else 'VALUE-AREA (X=POC,VAH,VAL) — NAO e OHLC'}")
    print(f"  {'data':>16} {'X1=POC?':>9} {'X2=VAH?':>9} {'X3=VAL?':>9} {'barH':>9} {'barL':>9} {'barC':>9} {'tipo':>9}")
    for r in rows:
        print(f"  {r[0]:>16} {r[1]:>9} {r[2]:>9} {r[3]:>9} {r[4]:>9} {r[5]:>9} {r[6]:>9} {r[7]:>9}")


if __name__ == "__main__":
    main()

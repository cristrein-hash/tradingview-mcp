#!/usr/bin/env python3
"""Builder canônico de features diárias XAU (Production v2 — regime pipeline).

Reconstrói `xau_daily_with_features.jsonl` a partir de OHLCV diário. Definições
inferidas por engenharia reversa contra o arquivo canônico existente e validadas
com diff=0 (exceto warmup ATR — ver abaixo):

  ma_50        = SMA(close, 50)
  ma_200       = SMA(close, 200)
  rsi_14       = RSI Wilder(14) no close
  rsi_ma_14    = SMA(rsi_14, 14)
  slope_20_pct = linreg_slope(close[-20:]) / mean(close[-20:]) * 100
  atr_14       = ATR Wilder(14)

ATR: reproduz EXATO de 2016-09-01 em diante (2510/2510 bars). Os 59 primeiros bars
(2016, até 2016-09-01, n_bars=6 incompletos) divergem só por seeding Wilder da fonte
original — decai exponencialmente, some até 2016-09-01. IRRELEVANTE p/ regime atual/futuro;
o pipeline v2/v3 consome o atr_14 ARMAZENADO, não recomputa (regime reproduz 100%).

Read-only, headless, sem side effects no import, sem MCP, sem rede.
"""
import json, sys, argparse


def _sma(s, n, i):
    return sum(s[i - n + 1:i + 1]) / n if i - n + 1 >= 0 else None


def _rsi_wilder(close, n=14):
    out = [None] * len(close)
    if len(close) <= n:
        return out
    gains = [max(close[k] - close[k - 1], 0) for k in range(1, len(close))]
    losses = [max(close[k - 1] - close[k], 0) for k in range(1, len(close))]
    ag = sum(gains[:n]) / n; al = sum(losses[:n]) / n
    out[n] = 100 - 100 / (1 + ag / al) if al else 100
    for k in range(n + 1, len(close)):
        ag = (ag * (n - 1) + gains[k - 1]) / n
        al = (al * (n - 1) + losses[k - 1]) / n
        out[k] = 100 - 100 / (1 + ag / al) if al else 100
    return out


def _atr_wilder(H, L, C, n=14):
    out = [None] * len(C)
    if len(C) < n:
        return out
    TR = [H[0] - L[0]] + [max(H[k] - L[k], abs(H[k] - C[k - 1]), abs(L[k] - C[k - 1])) for k in range(1, len(C))]
    a = sum(TR[:n]) / n; out[n - 1] = a
    for k in range(n, len(C)):
        a = (a * (n - 1) + TR[k]) / n; out[k] = a
    return out


def _linreg_slope(ys):
    n = len(ys); xs = list(range(n)); mx = sum(xs) / n; my = sum(ys) / n
    num = sum((xs[k] - mx) * (ys[k] - my) for k in range(n))
    den = sum((xs[k] - mx) ** 2 for k in range(n))
    return num / den if den else 0.0


def build_features(rows):
    """rows: lista de dicts com ts/open/high/low/close/volume (ordenada por ts).
    Retorna nova lista com as features acrescentadas."""
    rows = sorted(rows, key=lambda b: b["ts"])
    C = [b["close"] for b in rows]; H = [b["high"] for b in rows]; L = [b["low"] for b in rows]
    N = len(rows)
    RSI = _rsi_wilder(C); ATR = _atr_wilder(H, L, C)
    out = []
    for i, b in enumerate(rows):
        rsi_ma = None
        if i >= 27 and all(RSI[i - 13:i + 1]):
            rsi_ma = sum(RSI[i - 13:i + 1]) / 14
        slope = None
        if i >= 19:
            w = C[i - 19:i + 1]; slope = _linreg_slope(w) / (sum(w) / 20) * 100
        out.append({**b,
                    "ma_50": _sma(C, 50, i), "ma_200": _sma(C, 200, i),
                    "rsi_14": RSI[i], "rsi_ma_14": rsi_ma,
                    "slope_20_pct": slope, "atr_14": ATR[i]})
    return out


def validate(built, ref, tol=0.01, atr_warmup_idx=73):
    """Compara features reconstruídas vs referência. Retorna (ok, relatório)."""
    ref_by_ts = {b["ts"]: b for b in ref}
    feats = ["ma_50", "ma_200", "rsi_14", "rsi_ma_14", "slope_20_pct", "atr_14"]
    report = {f: {"match": 0, "total": 0, "worst": 0.0} for f in feats}
    for i, b in enumerate(built):
        r = ref_by_ts.get(b["ts"])
        if not r:
            continue
        for f in feats:
            e, g = r.get(f), b.get(f)
            if e is None or g is None:
                continue
            # ATR: ignora warmup de seeding (primeiros bars)
            if f == "atr_14" and i < atr_warmup_idx:
                continue
            t = report[f]; t["total"] += 1; d = abs(e - g); t["worst"] = max(t["worst"], d)
            if d <= tol:
                t["match"] += 1
    ok = all(t["match"] == t["total"] and t["total"] > 0 for t in report.values())
    return ok, report


def main():
    ap = argparse.ArgumentParser(description="Build/validate XAU daily features.")
    ap.add_argument("--ohlcv", required=True, help="jsonl com ts/open/high/low/close/volume")
    ap.add_argument("--out", default=None, help="escreve features aqui (default: stdout não)")
    ap.add_argument("--validate-against", default=None, help="jsonl de referência p/ validar")
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(args.ohlcv) if l.strip()]
    built = build_features(rows)
    if args.validate_against:
        ref = [json.loads(l) for l in open(args.validate_against) if l.strip()]
        ok, rep = validate(built, ref)
        for f, t in rep.items():
            print(f"  {f:<14} {t['match']}/{t['total']}  worst={round(t['worst'],6)}")
        print("VALIDATE:", "PASS" if ok else "FAIL")
        if not ok:
            return 1
    if args.out:
        with open(args.out, "w") as fh:
            for b in built:
                fh.write(json.dumps(b) + "\n")
        print(f"[build] wrote {len(built)} rows -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

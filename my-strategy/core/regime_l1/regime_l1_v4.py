#!/usr/bin/env python3
"""regime_L1_v4 — fonte de regime EXPLÍCITA e rastreável da L1 (Production v2).

Substitui o regime legacy (v1 B / regime_B_v3), declarado IRRECUPERÁVEL. NÃO reproduz
o classificador morto, NÃO usa combined_score/breaks legacy. Define um regime D-1 limpo
e validável a partir das features diárias canônicas (ma_50/ma_200/rsi_14/rsi_ma_14/
slope_20_pct/atr_14), construídas por `core/regime/build_daily_features.py`.

Predicates (hipótese de trabalho do usuário, validada historicamente):
  BULL        : close > ma_200 AND (ma_50 >= ma_200 OR slope_20_pct > 0)
                              AND (rsi_14 >= rsi_ma_14 OR rsi_14 >= 50)
  BEAR        : close < ma_200 AND slope_20_pct < 0
  TRANSITION  : qualquer outro caso (perto da ma_200 / slope fraco-contraditório)

3 estados {BULL, TRANSITION, BEAR}. A L1 usa regime D-1 == BULL como gate-base de contexto.
Read-only, headless, sem MCP/rede/Telegram/side effects no import.
"""
import json, sys, argparse
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "regime"))
from build_daily_features import build_features  # noqa: E402


def classify(close, ma_50, ma_200, slope_20_pct, rsi_14, rsi_ma_14):
    if close is None or ma_200 is None:
        return "UNKNOWN"
    trend_up = (ma_50 is not None and ma_50 >= ma_200) or (slope_20_pct is not None and slope_20_pct > 0)
    rsi_ok = (rsi_14 is not None and rsi_ma_14 is not None and rsi_14 >= rsi_ma_14) or \
             (rsi_14 is not None and rsi_14 >= 50)
    if close > ma_200 and trend_up and rsi_ok:
        return "BULL"
    if close < ma_200 and (slope_20_pct is not None and slope_20_pct < 0):
        return "BEAR"
    return "TRANSITION"


def build_classifications(ohlcv_rows):
    feat = build_features(ohlcv_rows)
    out = []
    for b in feat:
        st = classify(b.get("close"), b.get("ma_50"), b.get("ma_200"),
                      b.get("slope_20_pct"), b.get("rsi_14"), b.get("rsi_ma_14"))
        out.append({"ts": b["ts"], "close": b["close"], "ma_50": b.get("ma_50"),
                    "ma_200": b.get("ma_200"), "slope_20_pct": b.get("slope_20_pct"),
                    "rsi_14": b.get("rsi_14"), "rsi_ma_14": b.get("rsi_ma_14"),
                    "regime_l1_v4": st})
    return out


def latest_state_before(classifications, bar_time_unix, max_stale_days=4):
    """Para o runtime: último regime_l1_v4 com ts < bar_time (D-1 causal).
    Retorna (state|None, stale: bool). stale se gap > max_stale_days."""
    last_t = last_s = None
    for r in classifications:
        try:
            t = int(datetime.fromisoformat(r["ts"][:10]).replace(tzinfo=timezone.utc).timestamp())
        except Exception:
            continue
        if t < bar_time_unix and r.get("regime_l1_v4") not in (None, "UNKNOWN"):
            last_t, last_s = t, r["regime_l1_v4"]
    if last_t is None:
        return None, True
    return last_s, (bar_time_unix - last_t) > max_stale_days * 86400


def main():
    ap = argparse.ArgumentParser(description="Build regime_l1_v4 classifications.")
    ap.add_argument("--daily", required=True, help="jsonl OHLCV diário (ts/open/high/low/close/volume)")
    ap.add_argument("--out", default=None, help="escreve classifications")
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(args.daily) if l.strip()]
    cls = build_classifications(rows)
    if args.out:
        with open(args.out, "w") as f:
            for r in cls:
                f.write(json.dumps(r) + "\n")
        print(f"[regime_l1_v4] wrote {len(cls)} -> {args.out} | último ts: {cls[-1]['ts']} = {cls[-1]['regime_l1_v4']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

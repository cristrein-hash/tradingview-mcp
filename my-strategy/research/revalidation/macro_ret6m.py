#!/usr/bin/env python3
"""
LENS ret6m — regime pelo RETORNO macro acumulado (puro, sem estrutura).

Ideia central:
    r[i] = close[i] / close[i-W] - 1   (retorno acumulado sobre janela W barras)
    BULL  se r >= +thr
    BEAR  se r <= -thr
    RANGE caso contrário (entre os limiares).

Rótulo causal close-only: usa apenas closes de barras FECHADAS <= i
(close[i] e close[i-W]). Nenhum futuro, nenhum repaint.

Grelha fechada declarada aqui: W em {90,126,180} barras x thr em {6,10}% = 6 configs.
Para i < W (sem histórico suficiente) o rótulo é RANGE (neutro).
"""

import json
import os

BASE = "/Users/cristrein/tradingview-mcp/my-strategy/research/revalidation"
RAW = os.path.join(BASE, "raw_1d_ohlc.jsonl")
OUT_DIR = os.path.join(BASE, "results")
OUT = os.path.join(OUT_DIR, "macro_ret6m_labels.json")

LENS = "ret6m"

# grelha pequena, fechada
WINDOWS = [90, 126, 180]      # barras (dias de negociação)
THRESHOLDS = [0.06, 0.10]     # 6% e 10%


def load_closes(path):
    closes = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            bar = json.loads(line)
            closes.append(float(bar["c"]))
    return closes


def label_series(closes, W, thr):
    n = len(closes)
    labels = []
    for i in range(n):
        if i < W:
            labels.append("RANGE")  # histórico insuficiente
            continue
        r = closes[i] / closes[i - W] - 1.0
        if r >= thr:
            labels.append("BULL")
        elif r <= -thr:
            labels.append("BEAR")
        else:
            labels.append("RANGE")
    return labels


def main():
    closes = load_closes(RAW)
    n = len(closes)
    assert n == 2982, f"esperava 2982 barras, obtive {n}"

    configs = []
    cid = 0
    for W in WINDOWS:
        for thr in THRESHOLDS:
            cid += 1
            labels = label_series(closes, W, thr)
            assert len(labels) == n
            assert all(x in ("BULL", "BEAR", "RANGE") for x in labels)
            configs.append({
                "id": f"c{cid}",
                "params": f"W={W}d,thr={int(thr*100)}%",
                "labels": labels,
            })

    assert len(configs) <= 6

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"lens": LENS, "configs": configs}, f)

    # resumo curto (stdout apenas; nao e metrica vs GT)
    print(f"lens={LENS} n_bars={n} n_configs={len(configs)}")
    for c in configs:
        cnt = {"BULL": 0, "BEAR": 0, "RANGE": 0}
        for x in c["labels"]:
            cnt[x] += 1
        print(f"  {c['id']} {c['params']}: "
              f"BULL={cnt['BULL']} BEAR={cnt['BEAR']} RANGE={cnt['RANGE']}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

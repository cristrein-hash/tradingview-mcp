#!/usr/bin/env python3
"""SWEEP-REJECT 4H GUARD (Cris 2026-08-14) — TRIPWIRE de proteção, NÃO edge.

O estudo multi-ano (research/xau_15m_short/sweep_reject_study_20260814.py) mostrou que este padrao NAO
tem edge preditivo (45% capture ~= baseline). Cris ordenou implementar mesmo assim como PROTECAO forward:
"precaucao facil, barata e valida — se volta a acontecer, ao menos nao quebramos outra conta".

REGRA (confirmada Cris 2026-08-14):
  LIGA  : vela 4H FECHADA com PAVIO SUPERIOR > 50% do CORPO (sweep/rejeicao no topo) -> bloqueia LONG.
  DESLIGA (retomada): QUEBRA DE ESTRUTURA no 15M = preco fecha acima do ultimo lower-high (HH) + higher-low
          (ex.: 14/08 ~06:00 HH 4336.7 > LH 4328.2, depois HL 4327.9). NAO e reclaim do high nem tempo fixo.

Stateless: block = existe um sweep 4H MAIS RECENTE que a ultima quebra-de-estrutura-up do 15M.
CONSOME store_reader (bars 4H/15M nativas) — le o preco/swings do proprio preco, nao inventa. Fail-OPEN. py3."""
import json, sys, time
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
LOG = str(BASE / "logs" / "sweep_reject_guard.jsonl")


def _bars(tf):
    try:
        import store_reader as SR
        return SR.bars(tf) or []
    except Exception:
        return []


def _ohlc(b):
    return (b.get("o", b.get("open")), b.get("h", b.get("high")),
            b.get("l", b.get("low")), b.get("c", b.get("close")))


def _t(b):
    v = b.get("t", b.get("time"))
    return int(v) if v is not None else None


def _last_4h_sweep():
    """(t, high) da vela 4H fechada MAIS RECENTE com pavio superior > 50% do corpo. (None,None) se nenhuma."""
    for b in reversed(_bars("240")):
        o, h, l, c = _ohlc(b)
        if None in (o, h, l, c):
            continue
        o, h, l, c = float(o), float(h), float(l), float(c)
        if (h - max(o, c)) > 0.5 * abs(c - o):     # pavio superior > 50% do corpo
            return _t(b), round(h, 2)
    return None, None


def _last_15m_break_up():
    """t da ultima QUEBRA DE ESTRUTURA UP no 15M = close acima do ultimo lower-high confirmado + higher-low.
    Pivots fractais m=2 causais. None se nao houver."""
    bars = _bars("15")
    O = []; H = []; L = []; C = []; T = []
    for b in bars:
        o, h, l, c = _ohlc(b)
        if None in (o, h, l, c):
            continue
        O.append(float(o)); H.append(float(h)); L.append(float(l)); C.append(float(c)); T.append(_t(b))
    n = len(C)
    if n < 20:
        return None
    ph = []; pl = []
    for k in range(2, n - 2):
        if H[k] > H[k-1] and H[k] > H[k-2] and H[k] >= H[k+1] and H[k] >= H[k+2]:
            ph.append((k + 2, H[k]))               # confirmado em k+2 (causal)
        if L[k] < L[k-1] and L[k] < L[k-2] and L[k] <= L[k+1] and L[k] <= L[k+2]:
            pl.append((k + 2, L[k]))
    last = None; hi = 0; lo = 0
    for i in range(n):
        while hi < len(ph) and ph[hi][0] <= i:
            hi += 1
        while lo < len(pl) and pl[lo][0] <= i:
            lo += 1
        if hi >= 2 and lo >= 2:
            was_lower_high = ph[hi-1][1] < ph[hi-2][1]      # o ultimo swing-high era um lower-high
            higher_low = pl[lo-1][1] > pl[lo-2][1]          # e temos um higher-low
            if was_lower_high and higher_low and C[i] > ph[hi-1][1]:  # fechou acima do lower-high = HH
                last = T[i]
    return last


def verdict():
    ts, sh = _last_4h_sweep()
    if ts is None:
        return {"block": False, "why": "sem sweep4H", "sweep_t": None, "sweep_high": None, "break15_t": None}
    up = _last_15m_break_up()
    block = (up is None) or (ts > up)               # sweep mais recente que a ultima quebra-up 15M
    return {"block": bool(block),
            "why": "sweep4H sem quebra-estrutura 15M desde" if block else "15M quebrou estrutura (HH+HL) apos o sweep",
            "sweep_t": ts, "sweep_high": sh, "break15_t": up}


def blocks_long():
    """ATIVO: True bloqueia LONG. Tripwire (nao edge). Fail-open."""
    try:
        return bool(verdict().get("block"))
    except Exception:
        return False


def tick():
    v = verdict(); v["logged_at"] = int(time.time())
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps(v) + "\n")
    except Exception:
        pass
    print("sweep-reject-guard: block=%s (%s) sweep_high=%s" % (v.get("block"), v.get("why"), v.get("sweep_high")), flush=True)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        def _rule(o, h, l, c):
            return (h - max(o, c)) > 0.5 * abs(c - o)
        t = []
        t.append(("sweep grande (o100 h130 l99 c101) dispara", _rule(100, 130, 99, 101) is True))
        t.append(("vela normal (o100 h105 l99 c104) NAO dispara", _rule(100, 105, 99, 104) is False))
        t.append(("12/08 22:00 (o4410 h4449.7 l4398.2 c4408.6) dispara", _rule(4410, 4449.7, 4398.2, 4408.6) is True))
        v = verdict()
        t.append(("verdict tem chave break15_t (release=quebra 15M)", "break15_t" in v))
        for lab, r in t:
            print("  [%s] %s" % ("OK" if r else "FAIL", lab))
        print("verdict live:", v)
        print("selftest", "PASS" if all(r for _, r in t) else "FAIL")
        sys.exit(0 if all(r for _, r in t) else 1)
    tick()

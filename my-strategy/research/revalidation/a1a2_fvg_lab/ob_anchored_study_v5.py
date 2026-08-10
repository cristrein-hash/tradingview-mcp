#!/usr/bin/env python3
"""A1A2 OB-ANCHORED v5 — gatilho ANCORADO NA DEMANDA OB DETECTOR REAL (ordem Cris 2026-08-10). Reutiliza o
PADRÃO CANÓNICO de leitura de OB do RAW (cp_engine.py / a2_context_build.py): zonas por id com TIPO REAL
(text='DEMAND'/'SUPPLY') e born_t (nascimento causal). NADA inferido/inventado.

ESTRUTURA REAL (não inventada):
  - zona demanda = OB Detector v11, `text`=='DEMAND', `born_t`<=t (causal), do RAW all_boxes.
  - toque = pullback low dentro de [zona_low, zona_high] (padrão cp_engine:145).
  - gatilho = MB3 do módulo-mãe aprovado a1_causal_entry (intocado).
  - SL = zona_low − 0.1ATR (fronteira real + buffer aprovado); alvo 3R (aprovado).
ÚNICA medição minha (declarada p/ auditoria): 'pullback low' = min low em [i-PB_WIN,i] (facto, não métrica) —
e é GATED pela zona demanda real. Sem depth/bounce/leg inventados.
Motor read-only. NÃO toca nada live. py3.9 stdlib."""
import sys, gzip, json, bisect, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from a1_causal_entry import load_series, causal_entry, HORIZON, RAW
from fvg_localization_study import panel, r_of, BLK
from fvg_localization_study_v2 import PB_WIN, SCALE_ATR, A2_MAX_ATR, HH_WIN, detect_at as detect_base
from fvg_localization_study_v3 import build_regime_lookup, regime_at


def grp(r, key, name_sub):
    for s in (r.get(key) or []):
        if name_sub in (s.get("name") or ""):
            return s
    return None


def load_ob_zones(blocks):
    """Padrão canónico cp_engine: {(blk,id): {text, high, low, born_t}} — tipo REAL + nascimento causal."""
    zones = {}
    for blk_i, blk in enumerate(blocks):
        p = RAW / blk if not str(blk).startswith("/") else Path(blk)
        snaps = []
        with gzip.open(p, "rt") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict) and r.get("ohlcv"):
                    snaps.append(r)
        snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
        for r in snaps:
            oh = r.get("ohlcv") or []
            cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
            ob = grp(r, "pine_boxes", "Custom OB")
            for bx in (ob.get("all_boxes") if ob else []) or []:
                zid = bx.get("id")
                if zid is None:
                    continue
                zk = (blk_i, zid)
                if zk not in zones:
                    zones[zk] = {"text": str(bx.get("text", "")).upper(), "high": bx.get("high"),
                                 "low": bx.get("low"), "born_t": cur}
                else:
                    zones[zk]["high"] = bx.get("high"); zones[zk]["low"] = bx.get("low")
    return zones


def _resolve(S, ei, ent, sl):
    L, H, N = S["L"], S["H"], S["N"]
    rr = ent - sl; tgt = ent + 3 * rr
    for m in range(ei + 1, min(N, ei + HORIZON + 1)):
        if L[m] <= sl: return "LOSS"
        if H[m] >= tgt: return "WIN"
    return "OPEN"


def detect_ob(S, i, zones):
    """Setup OB-ancorado catalogado na barra i. Fundo do pullback (facto) DENTRO de uma zona DEMAND real
    (born<=t) → MB3 aprovado → SL na fronteira da zona. Devolve dict ou None."""
    L, ATR, T = S["L"], S["ATR"], S["T"]
    atr = ATR[i] or 5.0
    t = T[i]
    lo0 = max(0, i - PB_WIN)
    j = min(range(lo0, i + 1), key=lambda z: L[z])          # pullback low recente (facto)
    lj = L[j]
    # zona DEMAND real (tipo do indicador) nascida <= t que CONTÉM o fundo (padrão cp_engine:145)
    dem = [z for z in zones.values()
           if "DEMAND" in z["text"] and z["born_t"] and z["born_t"] <= t
           and z["low"] is not None and z["high"] is not None and z["low"] <= lj <= z["high"]]
    if not dem:
        return None
    zl = max(z["low"] for z in dem)                          # fronteira baixa da zona tocada (mais alta = íman)
    zh = max(z["high"] for z in dem)
    start = max(0, j - 3)
    Sx = {k: (v[start:i + 1] if isinstance(v, list) else v) for k, v in S.items()}
    Sx["N"] = len(Sx["T"])
    r = causal_entry(Sx, j - start, kind="MB3")
    if not r:
        return None
    ei = r["ei"] + start
    if ei != i:
        return None
    ent = r["ent"]
    sl = round(zl - 0.1 * atr, 2)                            # SL na fronteira da zona OB real
    rr = ent - sl
    if rr <= 0.05 * atr or rr > SCALE_ATR * atr:
        return None
    o = _resolve(S, ei, ent, sl)
    return dict(ei=ei, t=t, ent=round(ent, 2), sl=sl, R=round(rr, 2), o=o, zone=(round(zl, 1), round(zh, 1)), j=j)


def main():
    S = load_series(BLK); N = S["N"]
    zones = load_ob_zones(BLK)
    from collections import Counter
    tt = Counter(z["text"] for z in zones.values())
    known, REG = build_regime_lookup()
    print(f"série {N} barras · zonas OB {len(zones)} (tipos: {dict(tt)})")

    fires = {}
    for i in range(HH_WIN + 4, N):
        r = detect_ob(S, i, zones)
        if r and r["o"] in ("WIN", "LOSS"):
            r["regime"] = regime_at(known, REG, r["t"])
            fires[i] = r
    got = list(fires.values())
    print(f"disparos OB-ancorados resolvidos: {len(got)} · por regime: {dict(Counter(r['regime'] for r in got))}")

    for REGIME in ("BULL", "RANGE", "BEAR"):
        sub = [r for r in got if r["regime"] == REGIME]
        if len(sub) < 8:
            print(f"\n[{REGIME}] n={len(sub)} — pequeno."); continue
        res = [r_of(r["o"]) for r in sub]
        print(f"\n[{REGIME}] {panel(res)['s']} · med R {st.median([r['R'] for r in sub]):.1f}pts")
        if REGIME == "BULL":
            print(f"  (baseline A1/A2 invented BULL: N266 WR37% sumR+130 avgR+0.49 ret/DD7.65)")

    # sobreposição vs baseline invented
    base = {}
    for i in range(HH_WIN + 4, N):
        rb = detect_base(S, i)
        if rb and rb["o"] in ("WIN", "LOSS"):
            base[i] = rb
    print(f"\nvs baseline invented: OB {len(fires)} · base {len(base)} · comuns {len(set(fires)&set(base))} · "
          f"só-OB {len(set(fires)-set(base))} · só-base {len(set(base)-set(fires))}")


if __name__ == "__main__":
    main()

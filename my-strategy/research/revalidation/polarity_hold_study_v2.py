#!/usr/bin/env python3
"""VALIDAÇÃO DA LEI DE POLARIDADE v2 — fixes do Devil's Advocate + filtro de FORÇA (Cris: "supply furada
COM FORÇA"). Testa se ex-supply furada COM FORÇA segura ACIMA do null (nível arbitrário), a sério.

Fixes DA sobre v1:
  1. NULL EMPARELHADO: nível arbitrário que o preço toca, mesma definição → a "lei" só vale se REAL >> NULL.
  2. GEOMETRIA CONGELADA em born_t (v1 tinha leak: o loader reescrevia high/low com snapshots futuros).
  3. DEFINIÇÃO SIMÉTRICA por FECHO (v1: hold por pavio +1ATR vs fail por fecho −0.1ATR = enviesado).
  4. FILTRO DE FORÇA: rompimento dentro de leg IMPULSO_UP (leg_v3, recurso VALIDADO — não invento threshold).
Só factos: fecho real vs fronteira real da zona OB; força = leg_v3 (existente). py3.9 stdlib."""
import sys, gzip, json, bisect, random, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "a1a2_fvg_lab"))
from a1_causal_entry import load_series, RAW
from fvg_localization_study import BLK
from fvg_localization_study_v3 import build_regime_lookup, regime_at
import leg_v3 as LV

D_ATR = 1.0     # definição SIMÉTRICA: hold=fecho +D·ATR acima; fail=fecho −D·ATR abaixo (mesma distância)
FWD = 96

_v3 = LV.build_leg_v3(); _LC = [r["t"] + 14400 for r in _v3]


def leg_at(t):
    i = bisect.bisect_right(_LC, t) - 1
    return _v3[i].get("leg") if i >= 0 else None


def load_ob_frozen(blocks):
    """OB zones com geometria CONGELADA em born_t (first-seen), tipo real. Corrige o leak :62 do v1."""
    zones = {}
    for bi, blk in enumerate(blocks):
        p = RAW / blk if not str(blk).startswith("/") else Path(blk)
        snaps = []
        with gzip.open(p, "rt") as fh:
            for l in fh:
                l = l.strip()
                if not l:
                    continue
                try:
                    r = json.loads(l)
                except Exception:
                    continue
                if isinstance(r, dict) and r.get("ohlcv"):
                    snaps.append(r)
        snaps.sort(key=lambda r: r.get("replay_current_date") or 0)
        for r in snaps:
            oh = r.get("ohlcv") or []
            cur = oh[-1]["time"] if oh and isinstance(oh[-1], dict) else None
            ob = next((s for s in (r.get("pine_boxes") or []) if "OB" in (s.get("name") or "")), None)
            for bx in (ob.get("all_boxes") if ob else []) or []:
                zid = bx.get("id")
                if zid is None:
                    continue
                zk = (bi, zid)
                if zk not in zones and bx.get("low") is not None:   # CONGELA na 1ª aparição (born)
                    zones[zk] = {"text": str(bx.get("text", "")).upper(), "high": bx["high"],
                                 "low": bx["low"], "born_t": cur}
    return zones


def resolve(S, start, zl, zh, side):
    """Definição SIMÉTRICA por FECHO. Devolve True(segurou)/False(falhou)/None(indef)."""
    C, N, ATR = S["C"], S["N"], S["ATR"]
    atr = ATR[start] or 5.0
    for m in range(start, min(N, start + FWD)):
        if side == "SUPPLY":                       # ex-supply=suporte: segura se sobe, falha se perde
            if C[m] >= zh + D_ATR * atr: return True
            if C[m] <= zl - D_ATR * atr: return False
        else:
            if C[m] <= zl - D_ATR * atr: return True
            if C[m] >= zh + D_ATR * atr: return False
    return None


def real_events(S, zones, side, force):
    T, H, L, C, N = S["T"], S["H"], S["L"], S["C"], S["N"]
    out = []
    for z in zones.values():
        if side not in z["text"] or not z["born_t"]:
            continue
        zl, zh = float(z["low"]), float(z["high"])
        b0 = bisect.bisect_left(T, z["born_t"])
        brk = None
        for b in range(b0, min(N, b0 + FWD * 3)):
            if side == "SUPPLY" and C[b] > zh: brk = b; break
            if side == "DEMAND" and C[b] < zl: brk = b; break
        if brk is None:
            continue
        if force and leg_at(T[brk]) != ("IMPULSO_UP" if side == "SUPPLY" else "IMPULSO_DOWN"):
            continue                                # FORÇA = rompimento em leg de impulso (leg_v3)
        pb = None
        for p in range(brk + 1, min(N, brk + FWD)):
            if side == "SUPPLY" and L[p] <= zh: pb = p; break
            if side == "DEMAND" and H[p] >= zl: pb = p; break
        if pb is None:
            continue
        h = resolve(S, pb, zl, zh, side)
        if h is not None:
            out.append({"t": T[pb], "held": h})
    return out


def null_rate(S, side, n, med_h, seeds=5):
    """NULL emparelhado: nível arbitrário que o preço toca (bar aleatório), mesma definição/altura."""
    N = S["N"]; rates = []
    for sd in range(seeds):
        random.seed(1000 + sd)
        held = res = 0
        tries = 0
        while res < n and tries < n * 20:
            tries += 1
            b = random.randint(FWD, N - FWD - 1)
            px = S["C"][b]; zl = px - med_h / 2; zh = px + med_h / 2
            h = resolve(S, b, zl, zh, side)
            if h is not None:
                res += 1; held += 1 if h else 0
        if res:
            rates.append(100 * held / res)
    return (st.mean(rates), st.pstdev(rates)) if rates else (0, 0)


def report(S, zones, side, known, REG):
    med_h = st.median([float(z["high"]) - float(z["low"]) for z in zones.values()
                       if side in z["text"] and z["low"] is not None])
    for force in (False, True):
        ev = real_events(S, zones, side, force)
        if not ev:
            print(f"[{side} força={force}] n=0"); continue
        n = len(ev); held = sum(1 for e in ev if e["held"])
        real = 100 * held / n
        nm, nsd = null_rate(S, side, min(n, 2000), med_h)
        tag = "COM FORÇA (leg impulso)" if force else "todos os rompimentos"
        edge = real - nm
        print(f"[{side} · {tag}] REAL n={n} segura {real:.0f}% · NULL {nm:.0f}%±{nsd:.0f} · "
              f"EDGE {edge:+.1f}pp  {'← MATERIAL' if edge >= 8 else '(marginal/nulo)'}")


def main():
    S = load_series(BLK)
    zones = load_ob_frozen(BLK)
    known, REG = build_regime_lookup()
    from collections import Counter
    print(f"série {S['N']} · zonas OB congeladas {len(zones)} ({dict(Counter(z['text'] for z in zones.values()))})")
    print(f"def SIMÉTRICA D={D_ATR}ATR fecho · FWD={FWD} · força=leg_v3 IMPULSO\n{'='*74}")
    report(S, zones, "SUPPLY", known, REG)
    print()
    report(S, zones, "DEMAND", known, REG)
    print(f"\nVEREDITO: a LEI só se prova se REAL-COM-FORÇA bater o NULL por margem MATERIAL (>=8pp).")


if __name__ == "__main__":
    main()

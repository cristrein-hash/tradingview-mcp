#!/usr/bin/env python3
"""AVALIAÇÃO COMPARATIVA (ordem Cris 2026-07-12): overlays de regime desenhados pelo Cris no 4H
vs detector 4H-nativo RAW (pós-fix causal) + impacto potencial nos gates ≠BEAR de L1 e L2.
Leitura multi-camada: composição de rótulos POR BARRA em cada janela do Cris (não snapshot),
relabel híbrido (janelas coloridas do Cris substituem; cinza=flag CONFUSO não substitui; fora
das janelas = detector mantém, como o Cris instruiu: sem overlay = detecção atual funciona).
SEM alteração no detector. Medição comparativa apenas."""
import io, json, csv, sys, bisect, contextlib, datetime as dt
import importlib.util
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
OVER = json.load(open(HERE/"results/cris_regime_overlays_20260712.json"))
COLOR2REG = {"242, 54, 69": "BEAR", "76, 175, 80": "BULL", "255, 152, 0": "RANGE",
             "184, 184, 184": "CONFUSO"}

def load_engine():
    spec = importlib.util.spec_from_file_location("eng", HERE/"engine_4h_regime_gate_RAW.py")
    eng = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(eng)
    return eng

def windows():
    out = []
    for r in OVER["cris"]:
        if r["name"] != "rectangle": continue
        bg = r.get("bg") or ""
        reg = next((v for k, v in COLOR2REG.items() if k in bg), None)
        if reg is None: continue          # sólidos = meus (fronteiras pós-fix); ignorar
        ts = sorted(p["time"] for p in r["points"])
        out.append({"id": r["id"], "reg": reg, "t0": ts[0], "t1": ts[1]})
    return sorted(out, key=lambda w: w["t0"])

def cris_label(t, wins):
    hits = [w for w in wins if w["t0"] <= t <= w["t1"] and w["reg"] != "CONFUSO"]
    if not hits: return None
    return max(hits, key=lambda w: w["t0"])["reg"]   # refinamento mais recente vence

def panel(R):
    n = len(R); sm = sum(R); wr = 100*sum(1 for x in R if x > 0)/n if n else 0
    eq = pk = dd = 0
    for x in R: eq += x; pk = max(pk, eq); dd = min(dd, eq-pk)
    mL = mW = cl = cw = 0
    for x in R:
        if x > 0: cw += 1; cl = 0
        else: cl += 1; cw = 0
        mW = max(mW, cw); mL = max(mL, cl)
    return f"N{n:>3} WR{wr:5.1f}% sumR{sm:7.1f} DD{dd:6.1f} streak-{mL}/+{mW}"

def main():
    eng = load_engine()
    wins = windows()
    D = "%Y-%m-%d"
    print("== JANELAS DO CRIS vs COMPOSIÇÃO DO DETECTOR (por barra 4H) ==")
    for w in wins:
        lab = [eng.regime_at(t) for t in eng.TS4 if w["t0"] <= t <= w["t1"]]
        c = Counter(lab); n = len(lab) or 1
        comp = " ".join(f"{k}{100*v//n}%" for k, v in c.most_common())
        agree = 100*c.get(w["reg"], 0)//n if w["reg"] != "CONFUSO" else None
        flips = sum(1 for i in range(1, len(lab)) if lab[i] != lab[i-1])
        print(f"{dt.datetime.utcfromtimestamp(w['t0']).strftime(D)}→"
              f"{dt.datetime.utcfromtimestamp(w['t1']).strftime(D)} CRIS={w['reg']:<8} "
              f"det: {comp:<40} concord={'—' if agree is None else str(agree)+'%'} flips={flips}")
    # impacto nos gates: rótulo híbrido (Cris nas janelas coloridas, detector fora)
    def hyb_at(ts): return cris_label(ts, wins) or eng.regime_at(ts)
    def hyb_prevday(ep_): return cris_label(ep_, wins) or eng.regime_prevday_close(ep_)
    def isoep(s): return int(dt.datetime.strptime(s, "%Y-%m-%dT%H:%M").replace(tzinfo=dt.timezone.utc).timestamp())
    def dep(s): return int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    L1 = json.load(open(HERE/"XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/l1_approved34.json"))
    cut8 = set(json.loads((HERE/"XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/l1_poc_cut8_ts.json").read_text()))
    l1 = sorted((isoep(t["ts"]), float(t["R"]), t["ts"]) for t in L1)
    l1c = [(ts, r, s) for ts, r, s in l1 if s not in cut8]
    print("\n== IMPACTO L1 (gate !=BEAR) ==")
    print("L1-26 atual (det)   :", panel([r for ts, r, _ in l1c if eng.regime_at(ts) != "BEAR"]))
    print("L1-26 híbrido (Cris):", panel([r for ts, r, _ in l1c if hyb_at(ts) != "BEAR"]))
    ch = [(s, r, eng.regime_at(ts), hyb_at(ts)) for ts, r, s in l1c
          if (eng.regime_at(ts) == "BEAR") != (hyb_at(ts) == "BEAR")]
    for s, r, d0, d1 in ch: print(f"  muda: {s} R{r:+.1f} det={d0} → cris={d1}")
    rows = list(csv.DictReader(open(HERE/"XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
    print("\n== IMPACTO L2 (gate !=BEAR, prevday) ==")
    for col in ("capped_realR", "realized_letrun_120"):
        l2 = [(dep(r["datetime"]), float(r[col])) for r in rows if r[col] not in ("", None)]
        print(f"[{col}]")
        print("  base           :", panel([r for _, r in l2]))
        print("  atual (det)    :", panel([r for t, r in l2 if eng.regime_prevday_close(t) != "BEAR"]))
        print("  híbrido (Cris) :", panel([r for t, r in l2 if hyb_prevday(t) != "BEAR"]))
        nch = sum(1 for t, _ in l2 if (eng.regime_prevday_close(t) == "BEAR") != (hyb_prevday(t) == "BEAR"))
        print(f"  trades com rótulo de corte alterado: {nch}")

if __name__ == "__main__":
    main()

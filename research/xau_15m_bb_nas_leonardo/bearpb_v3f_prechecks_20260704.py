#!/usr/bin/env python3
"""BEARPB V3F — PRÉ-CHECKS outcome-blind (protocolo da síntese, ANTES de qualquer leitura R3).
1/2 por citação de provas já feitas nesta sessão (regime hour-causal DA-verificado 2×: usa última
hora FECHADA; cj = p+3 FIXO 4499/4499 e features <=cj ⇒ idade>=2 do sinal é pós-confirmação, sem
look-ahead). 3: NULL DE COBERTURA (73 sinais ±6 barras vs 4 trades BEAR do Cris; 200 draws random
mesma-frequência em barras BEAR). 4: frequência re-medida na definição do MANDATO (semana-BEAR =
semana ISO com MAIORIA das barras em BEAR). Também: exporta e SELA a lista dos 73 (sha256)."""
import json, glob, bisect, random, hashlib, collections
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
random.seed(42)
# reexecuta o gerador congelado capturando os sinais
import io, contextlib, runpy
buf = io.StringIO()
gl = {}
with contextlib.redirect_stdout(buf):
    gl = runpy.run_path(str(HERE / "_bearpb_probe4_config_v3_final.py"))
signals = gl["signals"]
assert len(signals) == 73, len(signals)
(HERE / "results" / "bearpb_v3f_signals_20260704.json").write_text(json.dumps(signals, indent=1))
sha = hashlib.sha256((HERE / "results" / "bearpb_v3f_signals_20260704.json").read_bytes()).hexdigest()
print(f"SELADO: 73 sinais → results/bearpb_v3f_signals_20260704.json sha256 {sha}")

series = {}
for p in sorted(glob.glob(str(HERE / "primitives" / "*.primitives.json"))):
    for b in json.load(open(p))["series"]: series.setdefault(b["t"], b)
S = sorted(series.values(), key=lambda b: b["t"]); TS = [b["t"] for b in S]; N = len(S)
ns = {"__name__": "e", "__file__": str(HERE / "engine_substrate4_v5_hourcausal.py")}
import contextlib as cl2
with cl2.redirect_stdout(io.StringIO()):
    exec(compile((HERE / "engine_substrate4_v5_hourcausal.py").read_text(), "e", "exec"), ns)
regime_h = ns["regime_hourcausal"]
BEAR_BARS = [i for i in range(100, N - 481) if regime_h(TS[i]) == "BEAR"]
print(f"barras BEAR elegíveis: {len(BEAR_BARS)}")

# 3 — null de cobertura
AN = json.load(open(HERE / "results" / "cris_trades_analysis_20260704.json"))
T4 = [r["t"] for r in AN if r["regime"] == "BEAR"]
assert len(T4) == 4
I4 = [bisect.bisect_right(TS, t) - 1 for t in T4]
sig_i = [s["i"] for s in signals]
obs_cov = sum(1 for i4 in I4 if any(abs(si - i4) <= 6 for si in sig_i))
covs = []
for _ in range(200):
    pick = random.sample(BEAR_BARS, 73)
    covs.append(sum(1 for i4 in I4 if any(abs(si - i4) <= 6 for si in pick)))
ge = sum(1 for c in covs if c >= obs_cov) / len(covs)
print(f"PRÉ-CHECK 3 (null cobertura): obs {obs_cov}/4 · null méd {sum(covs)/len(covs):.2f} · P(null>=obs) = {100*ge:.0f}%"
      f" → {'COMPATÍVEL COM ACASO' if ge > 0.10 else 'acima do acaso'}")
age3 = sum(1 for s in signals if s.get("age", 99) <= 3)
print(f"   sinais com idade<=3 barras: {age3}/73 ({100*age3/73:.0f}%)")

# 4 — frequência na definição do mandato (semana ISO com maioria de barras BEAR)
wk_bear = collections.Counter(); wk_tot = collections.Counter()
for i in range(100, N - 481):
    w = dt.datetime.utcfromtimestamp(TS[i]).strftime("%G-%V"); wk_tot[w] += 1
for i in BEAR_BARS:
    w = dt.datetime.utcfromtimestamp(TS[i]).strftime("%G-%V"); wk_bear[w] += 1
mand_weeks = [w for w in wk_tot if wk_bear.get(w, 0) > wk_tot[w] / 2]
sig_wk = collections.Counter(dt.datetime.utcfromtimestamp(s["t"]).strftime("%G-%V") for s in signals)
in_mand = sum(v for w, v in sig_wk.items() if w in mand_weeks)
print(f"PRÉ-CHECK 4 (definição do mandato): {len(mand_weeks)} semanas-BEAR-maioria · {in_mand} sinais nelas "
      f"= {in_mand/len(mand_weeks):.2f}/sem (mandato 0-1/sem) · máx/sem {max(sig_wk.values())}")
print("PRÉ-CHECKS 1-2: por citação — regime hour-causal usa última hora FECHADA (DA kill-check 240/240 + DA labB2 "
      "pipeline 0/46); cj=p+3 FIXO (4499/4499) e features do candidato <=cj ⇒ idade>=2 é pós-confirmação: PASS.")

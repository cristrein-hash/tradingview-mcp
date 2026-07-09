#!/usr/bin/env python3
"""TESTE MÍNIMO D1-D3 — DEFINITION-FREEZE CHECK (prereg v1.1, ordem do Cris 2026-07-09).
MEDIDOR PURO: reporta valores CONTÍNUOS por episódio; NÃO corta, NÃO vota, NÃO decide (lei nº 2/3).
O registo narrativo é do READER; o caminho é decisão do CRIS. Leitura de trajetória multi-janela
(renovações de low, devolução vs range, bounces sequenciais) — não snapshot de eixo único.

Medições congeladas (prereg §Medições):
  D1: barras desde o último novo-low (janela 384) + nº e posições das renovações de low nas últimas
      192 barras (concentração/ausência).
  D2: dev_atr = (max high das 384 barras anteriores -> min low desde esse high até ao instante)/ATR
      ÷ range384_atr; + pos384 e pos96 do close no instante (reproduz números dos dossiês — A6).
  D3: bounces falhados desde o high-384: bounce = recuperação >=1,5*ATR desde o low corrente seguida
      de NOVO low; K=1,5 congelado ANTES do run; sensibilidade K=1,0 e K=2,0 reportada junto.
Dados: barras 15M CLOSED via loader F0 (sha do cache re-verificado contra o manifest ao ler — A7).
Instante = última barra fechada <= t da marca (dados só-passado; marcas retrospetivas = reconstrução
causal-no-instante, declarado). Zero outcome como input. Zero futuro."""
import json, sys, bisect, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/"xau_15m_structural_leg_engine"))
from f1_structural_leg_machine import Data

EPISODES = [
    ("A1", "2025-09-18 13:00", "winner"), ("A2", "2025-10-10 04:00", "winner"),
    ("A3", "2025-12-19 01:45", "winner"), ("A4", "2025-10-17 17:00", "winner"),
    ("A5", "2026-01-08 12:00", "winner"), ("A6", "2026-03-23 07:00", "winner"),
    ("A7", "2026-06-24 18:00", "winner"), ("A8", "2026-06-30 01:00", "winner"),
    ("A9", "2025-08-20 01:00", "winner"), ("A10", "2025-11-04 23:00", "winner"),
    ("B1", "2026-03-05 18:00", "negative"), ("B2", "2026-03-08 23:00", "negative"),
    ("B3", "2026-03-16 00:00", "negative"), ("B4", "2026-01-13 19:00", "negative"),
    ("C1", "2025-09-16 22:00", "negative"), ("C2", "2025-10-09 05:45", "negative"),
    ("C3", "2025-10-19 22:00", "negative"), ("C4", "2025-12-25 23:00", "negative"),
    ("C5", "2026-01-13 13:30", "negative"), ("C6", "2026-03-02 23:00", "negative"),
]
W384, W192 = 384, 192

def ts_of(s): return int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())

def bounces(D, j_hi, i, K):
    """bounces falhados em [j_hi, i]: recuperação >=K*ATR do low corrente seguida de NOVO low."""
    run_lo = D.L[j_hi]; armed = False; n = 0
    for k in range(j_hi, i+1):
        a = D.ATR[k] or 5.0
        if D.L[k] < run_lo:
            if armed: n += 1; armed = False
            run_lo = D.L[k]
        elif (D.C[k]-run_lo)/a >= K:
            armed = True
    return n

def measure(D, i):
    a = D.ATR[i] or 5.0
    w0 = max(0, i-W384)
    his = D.H[w0:i+1]; los = D.L[w0:i+1]
    hi384 = max(his); lo384 = min(los)
    j_hi = w0 + max(range(len(his)), key=lambda k: his[k])
    lo_since_hi = min(D.L[j_hi:i+1])
    dev_atr = (hi384-lo_since_hi)/a
    range384_atr = (hi384-lo384)/a
    ratio = dev_atr/range384_atr if range384_atr > 0 else None
    pos384 = (D.C[i]-lo384)/(hi384-lo384) if hi384 > lo384 else None
    w96 = max(0, i-96)
    h96 = max(D.H[w96:i]); l96 = min(D.L[w96:i]) if i > w96 else (D.H[i], D.L[i])
    pos96 = (D.C[i]-l96)/(h96-l96) if h96 > l96 else None
    # D1: novos lows na janela 384 (running min); último novo-low e renovações nas últimas 192
    run = float("inf"); renovs = []
    for k in range(w0, i+1):
        if D.L[k] < run:
            run = D.L[k]; renovs.append(k)
    last_nl = renovs[-1] if renovs else i
    renov_192 = [k for k in renovs if k >= i-W192]
    d1 = {"bars_since_last_new_low": i-last_nl,
          "n_low_renewals_last_192": len(renov_192),
          "renewal_positions_bars_ago": [i-k for k in renov_192][-8:]}
    d3 = {f"K{K}": bounces(D, j_hi, i, K) for K in (1.0, 1.5, 2.0)}
    return {"D1": d1,
            "D2": {"dev_atr": round(dev_atr, 1), "range384_atr": round(range384_atr, 1),
                   "ratio": round(ratio, 2) if ratio is not None else None,
                   "pos384": round(pos384, 2) if pos384 is not None else None,
                   "pos96": round(pos96, 2) if pos96 is not None else None},
            "D3_failed_bounces": d3, "atr": round(a, 2)}

def main():
    D = Data()
    rows = []
    for eid, dstr, grp in EPISODES:
        t = ts_of(dstr)
        i = bisect.bisect_right(D.TS, t)-1
        m = measure(D, i)
        rows.append({"episode": eid, "utc": dstr, "group_outcome_label_NOT_FOR_READING": grp, **m})
    out = {"prereg": "XAU_15M_CONTEXTUAL_READER_NEXT_TEST_PREREG.md v1.1",
           "note": "MEDIDOR PURO — sem cortes/votos/veredictos; registo narrativo = READER; caminho = CRIS",
           "rows": rows}
    (HERE/"results").mkdir(exist_ok=True)
    (HERE/"results/d1d3_minimal_test_result.json").write_text(json.dumps(out, indent=2))
    for r in rows:
        d1, d2, d3 = r["D1"], r["D2"], r["D3_failed_bounces"]
        print(f"{r['episode']:>4} {r['utc']}  D1: last_nl {d1['bars_since_last_new_low']:>4}b, renov192 {d1['n_low_renewals_last_192']:>2}  "
              f"D2: dev {d2['dev_atr']:>5} ratio {d2['ratio']:>5} pos384 {d2['pos384']:>5} pos96 {d2['pos96']:>5}  "
              f"D3: K1.0={d3['K1.0']} K1.5={d3['K1.5']} K2.0={d3['K2.0']}")
    print("MEASURED_OK")

if __name__ == "__main__":
    main()

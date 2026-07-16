#!/usr/bin/env python3
"""PAINEL consolidado de métricas IN-SAMPLE dos entries 15M aprovados/pré-aprovados
(A1, A2, Cp, 5ATR-A2 STACK, CASCEX v0.1) — verificação do Cris antes de aprovar produção (2026-07-16).
CORRIGIDO pós Devil's Advocate: 5ATR = STACK aprovado N181 (não o CSV256 baseline); coluna exit-method
(exits mistos NÃO comparáveis por avgR); ret/DD de A1/A2 marcado como artefacto de N-minúsculo; ressalvas
de regime/janela surfaçadas.

FONTES (agrega o já-selado; nenhum re-backtest):
- A1/A2: A1_MB3_ENTRY_PREREG_FORWARD_20260714.md §8 — cadeia causal: +8-lookahead(inflado) -> fractal-only
         11/14 & 14/18 -> +SL low-real = A1 13/14, A2 16/18 (FINAL selado). loser A1=#1; A2=#6,#13.
         Exit 3R-IDEALIZADO (win=+3/loss=-1); §3 marca tight-R como "fill otimista" -> avgR = TETO.
- Cp:    CP_ENGINE_PREREG_FORWARD_20260716.md §8 (bear2026 regime-único, N21, limiares/5GT, GT5/5, null22%).
- 5ATR:  project_xau_15m_8atr_stack_preapproved.md — STACK FINAL +macro≠BEAR APROVADO Cris 2026-06-27:
         N181 WR65.2 +75.6R DD-3.0 streak3. Exit let-run R-real. (CSV 256-trade = intermédio NÃO-aprovado.)
- CASCEX: XAU15M_CASCEX_V01_PREAPPROVAL_20260705.md — N34, MAS DA-veto: NET confinado à janela vista do Cris
         (fora = NET-neutro; compra forma, não expectancy); multiplicidade P-efetivo 0.004-0.03.

TODAS = IN-SAMPLE (desenho), NENHUMA validada OOS (cânon do projeto: validação=convergência intra-dados).
Forward = árbitro. avgR NÃO comparável entre exits diferentes (ver coluna).
"""

# (engine, N, WR%, sumR, avgR, maxDD, streak, exit_method, caveat, no_power, dd_artifact)
ROWS = [
    ("A1 MB3", 14, 92.9, 38.0, 2.71, -1.0, -1, "3R-idealizado",
     "N sem poder (doc exige ≥20 fwd); fill otimista tight-R (avgR=teto)", True, True),
    ("A2 MB3", 18, 88.9, 46.0, 2.56, -1.0, -1, "3R-idealizado",
     "N sem poder; fill otimista tight-R (avgR=teto)", True, True),
    ("Cp capitulação", 21, 43.0, 12.6, 0.60, -4.0, -4, "3R-fixo (+opens)",
     "SÓ bear-2026 (regime único); limiares afinados/5 GT (overfit-risk); bubbles sem known_at", False, False),
    ("5ATR-A2 STACK", 181, 65.2, 75.6, 0.42, -3.0, -3, "let-run R-real",
     "STACK aprovado Cris 27/06 (base5ATR+h1_eff≥0.15+macro≠BEAR); ≠ CSV256 baseline", False, False),
    ("CASCEX v0.1", 34, 55.9, 39.6, 1.17, -4.8, -4, "3R-fixo",
     "⚠️ NET CONFINADO à janela vista (fora=NET-neutro); multiplicidade P-ef 0.004-0.03; disjunto dos GT", False, False),
]

print(f"{'ENGINE':<16}{'N':>5}{'WR%':>7}{'sumR':>8}{'avgR':>7}{'maxDD':>7}{'ret/DD':>9}{'strk':>6}  {'exit':<16}")
for name, N, wr, sumR, avg, dd, strk, ex, cav, nopow, ddart in ROWS:
    rdd = sumR / abs(dd) if dd else float('inf')
    rdd_s = (f"{rdd:.1f}*" if ddart else f"{rdd:.1f}")   # * = artefacto N-minúsculo
    npow = " ⚠N" if nopow else ""
    print(f"{name:<16}{N:>5}{wr:>7.1f}{sumR:>+8.1f}{avg:>+7.2f}{dd:>7.1f}{rdd_s:>9}{strk:>6}  {ex:<16}{npow}")

print("\nCAVEATS (surfaçadas pós-DA):")
for name, *_rest in ROWS:
    cav = _rest[7]
    print(f"  {name:<16} {cav}")
print("\nLEITURA HONESTA:")
print("  · avgR NÃO comparável entre linhas (exits diferentes: 3R-idealizado vs 3R-fixo vs let-run).")
print("  · A1/A2 ret/DD (*) = artefacto de 1-loss @ N-minúsculo (14/18) — NÃO é 5-7× melhor, é ruído.")
print("  · TODAS in-sample; nenhuma forward-validada. Janelas diferentes (Cp=só bear2026; 5ATR=2024-26).")
print("  · Mais robusto por N+DD+streak: 5ATR-A2 STACK (N181, DD-3, streak-3). Cp=melhor 'construção'(bear).")
print("  · CASCEX headline +39.6R sobrestima edge durável (confinado à janela vista).")

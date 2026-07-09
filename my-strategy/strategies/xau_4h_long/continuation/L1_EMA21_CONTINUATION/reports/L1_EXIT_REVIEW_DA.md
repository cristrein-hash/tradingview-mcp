# L1 EXIT REVIEW — Devil's Advocate (consolidado)

**2026-07-09.** DA do exit-review da L1. Dois passes reais (Agent tool, general-purpose). Read-only. Verdict final: **PASS** (manter +3R; nenhuma alternativa robusta).

## Pass 1 — ronda A–E (H=60) → **PARTIAL**
Apontou 2 FLAWs reais:
1. **Horizonte truncava a tese.** H=60 (~10 dias) vs TPs ideais do Cris de 1–3 meses → a hipótese de runner **não foi testada, foi impedida**. (`C+E≡C`, `D+E≡D` confirmavam que o regime-flip nem disparava dentro de 60 barras.)
2. **Look-ahead no E.** `regime_before(j)` consumia o close diário do próprio dia para barras intraday.
**Correções aplicadas (v2):** horizontes 60/150/300/600/FULL; regime **strict prior-day** (floor à meia-noite → só dias anteriores). Re-executado com null (holding aleatório) + jackknife.

## Pass 2 — trailing ratchet + hardening → **PASS** (com 2 correções obrigatórias, ambas resolvidas)
Contexto: o Cris objetou (com razão) que as regras C/D eram strawman. Testado trailing ratchet real (Chandelier/ATR/R-ladder/swing). `CHAND_5` parecia edge (+123,7R, null p=0,045).
Verdicts do DA:
- **Causalidade:** OK — chandelier usa `hh=max(H[i..j-1])` e `ATR[j-1]`, atualiza picos só após o teste de saída; SL0 de dados ≤ barra i. **Sem look-ahead.**
- **Knife-edge em k:** OK, diagnóstico correto e damning. Só k=5,0 perto de significativo; em 2/3 conjuntos falha p<0,05 (scanner 0,05; estudo 0,056). Vizinhos mortos. "Significância" carregada por ~2 trades num único k.
- **88%-de-2025:** OK, correto e fatal. Cross-check 3 conjuntos: share 2025 = 87,5% / 91,1% / 92,3%. Fora de 2025 ≤3 trades/ano.
- **Jackknife (2 trades=55%):** OK, mas enquadrar knife-edge + 2025 + concentração como **3 vistas de um facto** (edge vive em ~2 trades num ano), não 3 nails independentes. Fat tail é o objetivo de um runner — o problema não é a concentração em si, é a **k-seleção apoiada em 2 trades**.
- **Null model:** justo para a claim de captura (absorve a beta corretamente; CHAND_4 falha p=0,96 = capta menos que aleatório). Não valida claims de DD.
- **Conclusão (c) "tight-chandelier = melhoria robusta de DD":** **CONCERN — overstated/untested.** Exigiu per-ano.
- **Anatomia de pullback:** **mal-escopada** (drawdown global 300-bar, não intra-ride; `<=4ATR: 0%` é tell-tale) → **descartar**.

## Resolução das 2 correções obrigatórias
1. **(c) testada EX-2025** (`l1_exit_chand4_ex2025.py`): CHAND_4 vs +3R excluindo 2025 → CHAND_4 **perde sumR** nos 3 conjuntos (16,7<22 · 11,3<13 · 10,5<15); DD/streak só marginalmente melhores; ret/DD inconsistente (pior no estudo-34). → **conclusão (c) refutada**: não há benefício de trailing robusto sequer conservador. Não recomendado.
2. **Anatomia descartada** do argumento (não citada no relatório final).

## Veredito final
**PASS.** "Manter +3R; nenhuma alternativa de saída robusta; CHAND_5 = overfit 2025/knife-edge/2-trades; captura de runner = beta direcional, não skill causal" é **defensável, replicado nos 3 conjuntos e livre de look-ahead.** Nenhum bug. Nenhum exit robusto de captura de runner foi indevidamente descartado — fora de 2025 não existem runners multi-R para colher (≤3,5R/ano). A única alavanca potencial (exposição/sizing regime-condicional) fica como pesquisa futura, não um exit rule.

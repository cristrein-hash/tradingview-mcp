# N83 EXIT TRAILING (addendum, ordem Cris) — relatório
**2026-07-09.** Trailing RATCHET real testado antes de concluir (lição L1 aplicada: stop só sobe, buffer ATR, saída intrabar no stop elevado, floor=SL estrutural, causal ≤ m−1). 10 regras pré-registradas + 5 vizinhos. JSONs: `xau_15m_n83_exit_trailing_result.json` + `xau_15m_n83_rlad_robustness_result.json`. DA focado: PASS_EXPLORATORY_CANDIDATE c/ 3 correções (incorporadas).

## Resultado (população N83 congelada; baseline 3R = +125R/WR62,7/DD−4/stk4)
| regra | sumR | WR | DD | stk | nota |
|---|---|---|---|---|---|
| Chandelier k=2..6 | 32,8–104,2 | — | melhor DD | — | todos < 125 |
| CHAND_8 | 128,8 | 60,2 | −3,8 | 4 | ≈hold; marginal |
| ATR-trail / SWBUF | 41–65 | — | — | — | < 125 |
| **RLAD (lock floor(maxR)−1, ativa ≥2R)** | **143,0** | 73,5* | −4 | 4 | único materialmente acima |

*WR 73,5 = composição deslocada (41% dos wins são locks de +1R; winners avg 2,70R vs 3,00R) — não headline como "ganha em WR".

## Hardening do RLAD (o que o derruba como adoção)
1. **Excesso ≈ exposição, não timing:** null duration-matched (fechar a mercado na MESMA duração por-trade do RLAD, SL0 ativo) = **138,8R** → dos +42,5R sobre o null fraco, ~90% é exposição; **o ratchet adiciona só +4,2R** sobre fechar a mercado no mesmo bar. RLAD = extrator de convexidade/duração com piso garantido, não skill de timing. (O p=0,0 do null U[1,dur] era instrumento fraco.)
2. **Delay-1-bar INVERTE a edge: 113 < 125** (3R fixo = 125 inalterado). Exige entry on-close + stops resting; fragilidade de alinhamento de dados de 1ª classe.
3. Vizinhos: plateau no lado "loose" (129,5–143 ≥ 125); precipício = BE-antes-de-2R (101/86 — mata pullbacks normais de markup; mecanismo interpretável). Jack-drop-best −9 (1 trade = +6 dos +18). Slippage ok (141,3/139,6). Fill-fiction 1/83 (0,11R, negligível). 0 exits de horizonte.
4. Multiplicidade: best-of-~15 looks; população com o leak da base (tudo condicional).

## Conclusão do trailing
**Manter 3R fixo como exit oficial.** Nenhum trailing bate o 3R de forma material E robusta: o único candidato (RLAD) tem ~90% do excesso em exposição, inverte com 1 barra de latência e paga multiplicidade. **RLAD fica como candidato EXPLORATORY** (piso garantido + duração; interpretável) a re-testar na base reparada, decisão do Cris. Veredito do bloco (FAIL da base por event-selection lookahead) inalterado.

# L1 EMA21 4H LONG Continuation — EXIT REVIEW · RELATÓRIO FINAL

**Data:** 2026-07-09 · **Status:** `EXIT_REVIEW_COMPLETE` · **Decisão:** **manter o exit fixo +3R** (nenhuma alternativa aprovada) · **Produção:** `NOT_AUTHORIZED`

Executado conforme `L1_EXIT_REVIEW_PREREG.md`. Baseline V1 apenas. Read-only sobre RAW; sem produção/chart/commit. DA obrigatório corrido (verdict abaixo + `L1_EXIT_REVIEW_DA.md`).

---

## 1. Bootstrap
- Repo `/Users/cristrein/tradingview-mcp`; HEAD==origin==`028c0a4`.
- Safety report: BLOCKER=3 / WARNING=1 / INFO=50 (baseline pré-existente, report-only — nada bloqueado).
- Working tree: só `scanner.py` (V1) + artifacts L1 autorizados.

## 2. Motor validado (gate)
Cutoff canónico **recuperado empiricamente = H=60 barras** (único horizonte que reproduz o split salvo `16T/16S/2TIME` e sumR **byte-exato**: estudo-34 +35.2R, FINAL-24 +45.2R). O exit-A (fixo +3R, first-touch) reproduz a baseline nos 3 conjuntos → motor de simulação fiável. Todas as regras avaliadas **on-close, causais** (info ≤ barra j-1 para stops trailing; floor estrutural SL0 = `zone_OB_low−0.1ATR`).

## 3. Baseline V1 (a bater)
| Conjunto | N | +3R sumR | WR | maxDD | streak |
|---|---|---|---|---|---|
| FINAL-24 (primário) | 24 | **+45.2R** (H60) / +48 (H≥150) | 75% | −3.0 | 3 |
| Scanner-31 V1 (secundário) | 31 | **+34.2R** / +37 | 55% | −4.0 | 4 |
| Estudo-34 (terciário) | 34 | **+35.2R** / +38 | 53% | −4.0 | 4 |

## 4. Exits executados (matriz)
**Ronda 1 (prereg A–E):** A fixo-3R · B let-run · B2 let-run+BE · C EMA21-close-trail · D swing-close-trail · D2 · E regime-flip · C+E · D+E. → **corrigidos 2 FLAWs do 1º DA:** (i) horizonte estendido 60/150/300/600/FULL (os TPs ideais do Cris duram 1–3 meses; H=60 impedia testar a tese de runner); (ii) regime-flip passado a **strict prior-day** (eliminado look-ahead de close diário same-day).
**Ronda 2 (objeção do Cris — trailing a sério):** as regras C/D eram strawman (saída no 1º close<EMA/swing = shakeout; stop nunca ratchetava). Testado trailing **RATCHET real**: Chandelier `hh−k·ATR` (k=2…10), ATR-trail, R-ladder, swing+buffer. Anatomia de pullback: **mal-escopada — descartada** (media drawdown global 300-bar, não intra-ride).

## 5. Resultado por conjunto (H=300, horizonte justo)
- **Nenhum exit estrutural causal bate o +3R de forma robusta.**
- **Let-run cego (B):** captura runners (FINAL-24 até +295R FULL) mas = **beta direcional** (holding aleatório com o mesmo SL já dá ~2× a baseline; null p=0,32 no FULL) e **destrói o perfil** (WR→29%, streak 6–11, reverte 10 winners, segura meses) → incompatível FundedNext.
- **Regime-flip (E, causal):** +113R (H300) mas **não bate o holding aleatório** (p=0,108/0,127/0,112) → beta, não skill.
- **Trailing ratchet — o candidato sério:** `CHAND_5` parecia edge (FINAL-24 +123,7R, ret/DD 58,9, WR 79, streak 3, null p=0,045). **Hardening derrubou-o:**
  - **Knife-edge em k:** só k=5,0 passa o null; k=4,5 (p=0,94) e k=5,5 (p=0,08) falham. Salto descontínuo 55,6→123,7 entre k4,5 e k5,0. **Não é plateau** (edge real teria vários k significativos).
  - **88–92% do ganho vem SÓ de 2025** (parábola do ouro 2600→4700): por-ano FINAL-24 `2025:+108,3` vs todos os outros ≤+3,5R.
  - **Jackknife:** 2 trades = 55% do total; top trade 50R.
  - **EX-2025 (teste decisivo):** o tight-chandelier CHAND_4 **perde R vs +3R** nos 3 conjuntos (16,7<22 · 11,3<13 · 10,5<15); só reduz DD/streak marginalmente, e o ret/DD é inconsistente (pior no estudo-34). → não há benefício de trailing robusto sequer no modo conservador.

## 6. Melhor candidato
**NENHUM aprovado.** O único que "brilha" (CHAND_5) é overfit a 2025 / k-a-rigor / 2 trades. Fora de 2025 os continuation batem ~3R e estagnam (EX-2025: WR 42–64%, sem runners multi-R cavalgáveis) — **o +3R está bem casado com o que a estratégia realmente produz.** A intuição "continuation corre limpo → trailing cavalga" **é verdadeira só em ano de tendência forte (2025)**; é regime-condicional, não um edge de saída durável.

## 7. DA verdict
- 1º DA (ronda 1): **PARTIAL** → 2 FLAWs corrigidos (horizonte + causalidade regime).
- DA final (trailing): **PASS** com 2 correções obrigatórias — ambas resolvidas com dados: (c) benefício tight-chandelier testado EX-2025 e **refutado**; anatomia de pullback **descartada** (mal-escopada). Causalidade re-confirmada limpa (sem look-ahead).

## Conclusão
**Manter o exit fixo +3R como o exit aprovado da L1.** Nenhuma alternativa de saída (let-run, regime-flip, trailing ratchet) o bate de forma robusta: a captura de runners é beta direcional de 2025, não skill causal, e degrada WR/streak/hold-time. A alavanca real para colher parábolas tipo-2025 **não é um trigger de exit mais esperto — é exposição/sizing condicional ao macro-regime**, que fica como **pesquisa futura proposta, NÃO aprovada**.

## Próximo passo
- Manter +3R. Exit-review encerrada.
- (Futuro, requer autorização do Cris) explorar **sizing/exposição regime-condicional em BULL forte** como camada separada — não é um exit rule, e não altera a L1 aprovada.

**PRODUÇÃO: NOT_AUTHORIZED · SL: não reaberto (V1) · nada commitado/pushed.**

### Artifacts (reprodutíveis, salvos)
`l1_exit_review.py`(+result H60) · `l1_exit_review_v2.py`(+result horizontes/strict/null) · `l1_exit_review_v2_robustness.py`(+result) · `l1_exit_trailing.py` · `l1_exit_trailing_wide.py` · `l1_exit_chand_harden.py` · `l1_exit_chand4_ex2025.py` (+ respetivos `_result.json`) · `_l1_exit_probe_horizon.py` · `_l1_exit_v2_extract.py` · `l1_cris_tp_extensions.json` (ground-truth chart).

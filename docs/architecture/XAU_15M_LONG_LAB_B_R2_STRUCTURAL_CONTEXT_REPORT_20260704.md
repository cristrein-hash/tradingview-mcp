# LAB B r2 — STRUCTURAL CONTEXT · RELATÓRIO FINAL (2026-07-04)

## 1. Executive verdict
**RISK_CONTROL_ONLY** — o contexto estrutural NÃO entregou edge nem review-layer pleno pelos critérios do prereg §7. Os dois produtos reais da rodada: (a) **canon negativo FB1**: a tese fundadora (losers sob teto/supply) foi REFUTADA como corte por 4 buscas independentes — teto convergente carrega PRÊMIO (conv4 avgNET +2,78; htfceil +1,87; runners vivem no meio-alto/teto) → SKIP por teto = taxar pagadores; (b) **FB2-SIZE50** (fundo/early-leg sem estrutura, floor 0,5 via F4): risk-control magro e honesto — +236,6 NET (101,3% retenção), DD −11%, 53/53 runners, MAS ganho é aritmético (z≈1,7 pós ~100 looks) e **2026 flagged é positivo (+4,4) → a variante custou −2,2 no regime vigente**. TUDO = CALIBRAÇÃO (canon 45-grupos); árbitro = extensão RAW não-BEAR.

## 2. Discovery synthesis
Workflow `wf_6e643ea3-184` (4 perspectivas + DA-pré + síntese; ~100 predicados examinados, ledger integral declarado). Doc: `..._DISCOVERY_20260704.md`. Incidente de integridade no universo canônico durante o discovery → arquivo re-verificado e SELADO (sha `f27fb229...`, chmod a-w); regra nova: subagents não escrevem no dir compartilhado.

## 3-4. Hypotheses tested / rejected before test
Testadas (congeladas no prereg): FB1 proteção · FB2 fundo (SKIP bloqueado→SIZE_50) · FB3 limbo pós-breakout · FB4 classes · FB5 forward-ledger. Rejeitadas antes do teste: DEADMID (sentinela 99 em 50% + não-reprodução 75≠97 + 11 runner-kills na replicação) · CAL8 como família separada (⊂E2 15/17) · SKIP de teto em qualquer forma (canon FB1) · H1/H4 box lenses (refutadas nos looks do regimebox).

## 5. Baseline reproduction
N435 · +291,5 bruto · +233,6 NET · WR_liq 46,0 · DD −14,2 · stk −8 · 53 runners — fail-loud PASS em toda execução; universo selado verificado por sha no preâmbulo.

## 6. Results (NET-SB; CSV integral em results/)
| Variante | N | WR | NET | DD | stk | runners | ret% |
|---|---|---|---|---|---|---|---|
| BASELINE | 435 | 46,0 | 233,6 | −14,2 | −8 | 53 | 100 |
| FB1 união protegida (nada removido) | 226 | 49,1 | 180,6* | −10,3 | — | 34 | — |
| FB2 flagged | 42 | 33,3 | −6,0 | — | — | 2 | — |
| FB2 SKIP (**BLOQUEADO**: 2 runner-kills, ambos 2026) | 393 | 47,3 | 239,6 | −11,0 | −6 | 51 | 102,6 |
| **FB2 SIZE_50 (acionável via F4, floor 0,5)** | 435 | 46,0 | **236,6** | −12,6 | −8 | **53** | **101,3** |
| FB3 flagged (16; 0 runners; null 95,6%) | 16 | 31,2 | −9,5 | — | — | 0 | — |
| FB3 SKIP (prateleira; anulado por FB1: resíduo N4 −1,9) | 419 | 46,5 | 243,2 | −14,2 | −8 | 53 | 104,1 |
\*77% do NET e 64% dos runners da base moram DENTRO da união protegida (52% dos trades).

## 7. WR/streak/DD impact
**WR: inalterado** em toda variante acionável (46,0). **Streak: inalterado** (−8; o SKIP bloqueado daria −6). **DD: −11% na FB2-SIZE50** (−14,2→−12,6). O DA quantificou o teto estrutural: 57% dos trades da janela do max-DD estão DENTRO da classe protegida FB1 → **DD/streak são estruturalmente inatacáveis por contexto ex-ante sem taxar pagadores** (concordância 4 buscas + DA; agora medido).

## 8. Runner preservation
Gate cumprido: FB2-SIZE50 53/53 · FB3 flagged 0 runners · FB1 = proteção. Os 2 runner-kills do FB2-SKIP são ambos de 2026 (+3,7/+3,5) = veto automático correto (regime vigente contradiz).

## 9. Annual/episode robustness
FB2: sinal negativo 100% em 2024-25; 2026 flagged POSITIVO (+4,4). FB3: dano 2024-pesado (−8,1 de −9,5). Jackknife FB2: flagged-sum varia −10,8/−3,8 sem melhor/pior semana. Nulls week-aware: FB2-SKIP pct 96,0 · FB2-SIZE50 pct 96,0 (week-aware do DA; 98,6 uniforme) · FB3 pct 95,6 — nada disso é validação (pós-seleção de ~100 looks).

## 10. DA verdict
Independente, não commitou. **Adjudicação central: o BLOCKED do FB3 era bug do MEU assert** (sign-flip + 2 convenções) — feats do regime box provados CAUSAIS (0/435 + pipeline 0/46); assert corrigido → PASS 35/35. +4 correções materiais (dedup order-gamed: conv4⊂htfceil; rb_p3 catch-all; números do discovery; descrição invertida). Veredito DA: RISK_CONTROL_ONLY. Doc: `..._DA_20260704.md`.

## 11. What becomes Lab C/D/F4
- **F4**: FB2-SIZE50 é COMPONÍVEL (overlap chain_pos 12%, sem dupla-taxação) + classes FB4 (QUICKPOP alvo-curto WR62 · KNIFE_RUNNER floor>0 sempre, 13/53 runners) como anotações de gestão.
- **Lab C (SL)**: herda canon FB1 (não alargar/estreitar por teto).
- **Lab D (re-entry)**: FB2 morde 12/20 loss-runs — a região fundo/early-leg é onde disciplina de retry importa.
- **Forward-ledger (FB5 + FB2 + FB3)**: listas exatas de cj_t congeladas no summary.json; regra pré-registrada; **gap de poder declarado: N≥15/família exige múltiplas extensões RAW** (~5,5 sem ≈ 2,6-6,2 flags).

## 12. Recommendation (dados; decisão Cris)
- **Adotar como canon de calibração:** FB1 anti-veto-teto (com as correções do DA: fundir conv4/htfceil, remover rb_p3 da união) — protege contra a classe inteira de "cortar teto" em rodadas futuras.
- **FB2-SIZE50**: candidato risk-control COMPONÍVEL com F4 — se adotado, é sizing operacional, não estratégia; ressalva 2026 explícita.
- **Aceitar o negativo central**: WR/streak não se movem por contexto estrutural ex-ante nesta base. Rotas restantes para os eixos FN: F4 (conta) · janela não-BEAR (Sistema A) · Lab C/D.

# LAB B r2 — DA ADVERSARIAL (2026-07-04)

Dois DAs reais: (i) **DA-pré** dentro do discovery `wf_6e643ea3-184` (demoveu FB2 a SIZE_50; fundiu E2/CAL8/CAL5; matou DEADMID; impôs 9 exigências de execução); (ii) **DA pós-resultado independente** (subagent real; scripts `_DA_labB2_{1..4}*.py`, não commitou — git log verificado; selo sha do universo verificado antes/depois).

## Adjudicação central: FB3 — feats do regime box são CAUSAIS; o BLOCKED era bug do MEU assert
O assert v1 do lab deu 20/20 mismatches → BLOCKED provisório. O DA reproduziu byte-a-byte, diagnosticou **100% sign-flip** (`prev_hi_dist` = (phi−entry)/atr no probe original, (entry−phi) no assert) + 2 convenções erradas do assert (estado por hora usando close da hora CORRENTE — que não existe em cj_t; timeline por bloco truncando o segmento anterior). **Causalidade provada duas vezes:** recompute independente na spec correta = 0/435 mismatches; pipeline inteiro reconstruído só com barras ≤ cj_t = 0/46. Assert corrigido no script (3 diffs) → **PASS 35/35**. FB3 desbloqueado.

## Bugs/correções materiais (aplicados)
- **B1/B2** assert FB3 (acima) — o script oficial agora carrega as convenções adjudicadas.
- **B3** descrição do FB3 invertida no print (teto herdado fica ABAIXO do entry — pós-breakout); corrigido.
- **B4** números do discovery: FB2 WR 28,6→**33,3**; conv4 avg "+0,881"→**avgNET +2,78** (htfceil +1,874 ✓; runner-rate 31,8% ✓). Doc corrigido.
- **B5** dedup order-gamed: **conv4 ⊂ htfceil (22/22)** — na ordem inversa conv4 = 0% novos = kill pela própria regra; conv4/htfceil = 1 lente com 2 thresholds; a regra <30% é dependente de ordem → não é regra. Report carrega.

## Ataques que colaram (moldura obrigatória do report)
1. **FB2-SIZE50 é aritmética, não sinal:** ganho = −0,5×flagged_sum = +2,99 exato; z≈1,7 no size-null week-aware (pct 96,0, não 98,6 uniforme); **2026 flagged é NET-POSITIVO +4,4 → a variante CUSTOU −2,2 em 2026** (regime vigente contradiz no agregado, não só nos runners); fragilidade jackknife (−10,8/−3,8 sem melhor/pior semana).
2. **rb_p3 é catch-all:** 96 trades (33% do BULL), avgNET 0,425 < BULL 0,487, sumNET pct 35,9% de subsets aleatórios — não mede classe pagadora; injeta 34% da união FB1 e é a única fonte do conflito FB3∩FB1 (12/16).
3. **Preço da proteção FB1 (52% da base):** união detém 64% dos runners e 77% do NET, e **57% dos trades da janela do max-DD estão DENTRO dela** → sob o canon, DD/streak ficam estruturalmente inatacáveis por contexto (quantificação do que o discovery já admitia).
4. **FB3 na prática anulado pelo FB1:** overlap 12/16 via rb_p3; resíduo acionável N4, −1,9 ≈ nada. Precedência FB1>FB3 resolvida no report.
5. **FB5 sem poder:** extensão de ~5,5 semanas gera 2,6-6,2 flags/família vs N≥15 exigido — arbitragem exigirá múltiplas extensões.

## Dissolvidos
Determinismo byte-idêntico (stdout+csv+json, 2 re-runs) · baseline e FB2 (42/−6,0/WR33,3/SIZE50 +236,6) reproduzidos do zero · overlap F4 12% confirmado com implementação independente de chain+exits · runner-kills 2×2026 confirmados (veto do SKIP correto) · FB4/FB5 contagens e listas congeladas 6/6 True · selo sha intacto.

## Rótulos honestos (prereg §7) e veredito
**FB1** = canon negativo (refutação do teto) robusto; união = REVIEW_LAYER de calibração com defeitos (remover rb_p3; fundir conv4/htfceil) · **FB2** = RISK_CONTROL_ONLY no máximo (magro; 2026 negativo; forward-ledger obrigatório) · **FB3** = CANDIDATE_SHELF anulado na prática por FB1 · **FB4** = anotação OK · **FB5** = listas OK + gap de poder declarado.
**VEREDITO GLOBAL DO DA: RISK_CONTROL_ONLY** — mapping causal provado (não BLOCKED); nenhuma família passa o §7 como edge/review pleno; tudo = CALIBRAÇÃO aguardando extensão RAW não-BEAR.

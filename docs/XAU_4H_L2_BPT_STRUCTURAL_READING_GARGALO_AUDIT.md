# L2/BPT — AUDITORIA PROFUNDA: GARGALO DE CORTES E MANUTENÇÕES ERRADAS (62)

**2026-06-22.** Diagnóstico/calibração nos 62 (ensino). Cris flagou T9 (entrada bear-market que NÃO devia
acionar) + perda de muitos winners. Auditoria trade-a-trade dos 62 + leitura nova dos prints + raiz do gargalo.
NÃO produção, NÃO 276/OOS, NÃO promoção. Ground truth = verdicts visuais do Cris + tipo de saída.

## 1. Os dois erros (quantificados sobre os 62)
- **CORTES ERRADOS (winners perdidos): 16** — incl. 3 RUNNERS (S20/S25/S35 em REVIEW) + S26 RUNNER em SKIP.
  Dos 15 Cris=PROTECT, só **5 viraram TAKE** na leitura anterior (10 perdidos).
- **MANUTENÇÕES ERRADAS (junk mantido): 3** — T9, T12, T40 viraram TAKE e stoparam.
- Concordância da leitura anterior com os verdicts do Cris (n=18 labeled): **6/18**.

## 2. Confirmação VISUAL (leitura nova dos prints, ZIP3)
- Print 16.00.47: anotação direta **"T8 + S7 + T10 = WINNERS; T9 + F11 = SKIPS"** → **T9 É SKIP** pela tua
  leitura; meu reading o fez TAKE (manutenção errada confirmada).
- Print 16.37.20: **"ENTRADA EM PULLBACK BULL INTRA-BEAR MACRO REGIME — TAKE QUE DEVERIA SER SKIP"** (aponta
  T42) + "WINNER CURTO... BOM SKIP" → bull-pullback dentro de bear-macro = SKIP. Meu macro não gateou isto.

## 3. GARGALO nível 1 — agregação cega + lente Auction INVERTIDA (corrigível)
Assinatura dos 16 cortes errados: **Auction ≠ TAKE em 16/16** (Volumetria 13/16). Em S25/S26/S27/S29/S30/S35/
S36/S37 o **macro disse TAKE (correto)** mas a Auction disse "under-supply-rejecting" — a **leitura INVERTIDA
já refutada** (memory matrix-v0): perto/sob supply em bull-leg = **markup rompendo (BOM)**, não rejeição. Minha
agregação deu peso-igual de veto às 4 lentes (exigia 3/4 TAKE), então a lente invertida derrubou winners para
REVIEW. **Viola a prioridade causal do canon** (macro = camada 1 dominante, não veto-igual).

**Correção nível 1 (causal priority + supply-inverte-em-bull):** big winners TAKE **8→23**; Cris PROTECT como
TAKE **5→12**; concordância com Cris **6/18→13/18**; T9→SKIP, T42→SKIP, T12→REVIEW. **15 winners resgatados.**

## 4. GARGALO nível 2 — MEDIÇÃO DE REGIME quebrada (o gargalo PROFUNDO, NÃO resolvido)
Mesmo a leitura corrigida ainda erra, e SEMPRE pela mesma fonte — o **escalar de regime (regimeB combined /
macro_broken / família BULL-RISK) MIS-MEDE o macro**:
- **T19 (MACRO_BULL_LEG, winner) → SKIP errado:** `broken & combined<0` **over-fira dentro de bull-leg** (o
  escalar regimeB contradiz a leg confirmada) — o MESMO bug do full276.
- **T40 (Cris=BLOCK, bear-junk) → continua TAKE:** regimeB pontua cs=+3 (bull) → o gate não o pega; o escalar
  **não enxerga** o bear-junk que o teu print enxerga.
- **S26/S27 (PROTECT winners, RANGE/CORRECTIVE) → caem em REVIEW** porque a família macro os rotula RISK.
- **S13/S14/S15/S19 (winners) → SKIP** por `broken&combined<0` em RANGE — alguns OK (S19 Cris=BLOCK_acceptable),
  outros = a tensão bear-context-winner (bottom-reversals) que só veto-humano resolve.
- **T34 (Cris=PROTECT_entry_fix_SL) → NOVO corte REVIEW→SKIP** pelo mesmo over-fire `broken&combined<0` em
  MACRO_BEAR_LEG: um trade que o Cris PROTEGE (com fix de SL) morto pelo escalar de regime — REFORÇA que o
  gargalo é a medição de regime, não a entrada (Cris diz: entrada boa, conserta o SL).

**É o erro recorrente de TODAS as features de regime** (regime_diag/v1/has-overhead/leg-state todos fracos): as
mesmas features quebradas que rotulam entrada bull-run boa como RISK/late-top E não separam o bear-junk real.
A qualidade da leitura estrutural está **TETADA pela camada de regime**, que é o gargalo de fundo. **Regra
reafirmada: visual > feature-audit cru; resultado que contradiz o visual = UNTRUSTED.**

## 5. Trade-a-trade
`results/l2_bpt_full62_3way_audit.csv` (62: meu policy vs Cris vs outcome + tipo de erro + votos das 4 lentes) e
`results/l2_bpt_full62_corrected_reading.csv` (62: old_policy vs corrected_policy + por quê).

## 6. Conclusão (não-superficial)
O gargalo é **DUPLO com raiz comum** (regime/contexto mal-medido), exatamente o documentado:
1. **Cortes errados** ← lente Auction invertida (near-supply-em-bull lida como rejeição) + agregação peso-igual.
   **Corrigível** e já corrigido (resgata 15 winners, concordância 6→13/18).
2. **Manutenções erradas + resíduo de cortes** ← o **escalar de regime não-confiável** (over-fira em bull, cego
   ao bear-junk). **NÃO corrigível por agregação** — exige medição de regime ancorada no VISUAL, não no regimeB.

## 7. Próximo passo (diagnóstico, sem promoção)
O frente real NÃO é mais lente/agregação — é **a medição de regime/contexto macro ancorada na leitura visual**
(o backbone que distingue bull-run-continuation de bull-pullback-intra-bear), que continua sendo o problema
não-resolvido de toda a frente. Aguardo direção; nada implementado em produção.

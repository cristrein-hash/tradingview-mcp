# XAU 4H L2/BPT — Macro-Context Visual Reconciliation Audit (OB Demand 4H)

**Status:** `RECONCILIATION · NOT_STRATEGY · NOT_VALIDATION` · **Data:** 2026-06-17
**RAW gz read-only · sem backtest/PnL/filtro/plotagem/MCP/produção/SLIM.** Corrige o diagnóstico `a6d8e3a` (marcado UNTRUSTED).

> Os campos `visual_reconciliation_status` = **NEEDS_USER_VISUAL_CONFIRM**: aqui meço estrutura causal do RAW (boxes Custom OB v11), não a leitura literal do gráfico. Cris confirma contra o chart.

---

## 1. O diagnóstico anterior bate com o gráfico? **NÃO.**

O `a6d8e3a` concluiu `at_D1_demand = 0/17` e "macro não separa". **Isso era artefato de threshold/semântica**, não realidade. Re-medindo **sem threshold apertado** (`results/l2_bpt_macro_context_gt_visual_reconciliation.csv`, 17 BOM + 6 NAO):

| Camada | BOM | NAO | mediana dist (ATR) |
|---|--:|--:|---|
| **4H demand abaixo presente** | **16/17** | **6/6** | BOM 2.76 · NAO 2.08 |
| **D1 demand abaixo presente** | **17/17** | **6/6** | BOM 2.12 · NAO 1.33 |
| 4H supply overhead presente | 12/17 | 6/6 | BOM **2.27** · NAO **0.78** |

→ **Demanda abaixo existe em quase 100% dos casos** (4H e D1). O `0/17` anterior só acontecia porque eu exigia `inside OR near ≤ 0.5·ATR` — e a demanda relevante fica tipicamente **~2 ATR abaixo** (suporte da perna, não colado no preço).

## 2. O erro veio de não medir OB Demand 4H? **SIM (em parte).**

Dois erros combinados:
1. **Não medi "demanda 4H relevante abaixo / origem da perna"** — só `inside_demand` e `near ≤0.5ATR`. A demanda que importa para L2/BPT está abaixo, ~2 ATR (suporte estrutural), e foi ignorada.
2. **`at_d1_demand` com tolerância 0.5·ATR_D1** zerou tudo: D1 demand existe em 17/17 mas a ~2.1 ATR_D1 → fora da janela → `0/17` falso.

## 3. Campos semanticamente errados

- `at_D1_demand` (def `inside OR near_from_above ≤0.5ATR`): **semântica errada para L2/BPT** — a estratégia não entra *dentro* da demanda; entra no reclaim *acima* da polaridade, com a demanda como **suporte distante abaixo**. A flag binária "está na demanda" é a pergunta errada.
- `supply_overhead` binário (presente sim/não): **inútil** — presente em quase todos. O que separa é a **distância** ao supply (ver §4).
- `near_custom_ob_demand ≤0.5ATR`: threshold arbitrário, mascara o suporte real.

## 4. Campos tecnicamente certos mas inúteis / o sinal que emerge

- Presença binária de demand/supply: **tecnicamente correta, inútil** (quase sempre 1).
- **Sinal que emerge (corrigido):** **distância ao supply overhead 4H** discrimina direcionalmente:
  - **5/17 BOM entram SEM supply overhead** (céu limpo: GT02, GT03, GT08, GT18, GT25); os outros 12 com supply **distante** (mediana 2.27 ATR).
  - **NAO: 6/6 com supply overhead, 4/6 a ≤1 ATR** (GT06A 0.98, GT12 0.59, GT14_NAO 0.33, GT19A 0.23) → **NAO compra contra o teto**.
  - Não é separador limpo (GT01 0.46, GT24 0.25, GT20 1.03 são BOM com supply perto; GT06B é NAO com supply longe 3.63) — **small-n, direcional, precisa confirmação visual + n maior**.
- `GT08` é o único BOM sem demand 4H abaixo na snapshot as-of (tem D1 demand) → flag para visual.

## 5. O que precisa ser redefinido

- **Demanda 4H relevante:** não "inside/near", mas **a OB demand abaixo da entrada que é origem/suporte da perna** — medir por **distância em ATR** + se foi **tocada/respeitada no retest** + se está **abaixo do SL estrutural** + **frescor** (não mitigada).
- **Supply overhead relevante:** **distância em ATR ao supply imediato acima** (proximidade = risco), + frescor + se está **bloqueando o target**; binário "existe" é inútil.
- Trocar todas as flags binárias presença→**distância+qualidade**.

## 6. Camadas macro que NÃO devem ser usadas ainda

- `at_D1_demand` (def atual) — **descartar** como flag binária; redefinir como distância+contexto.
- `supply_overhead` binário — **não usar como veto** (mataria 12/17 BOM + os 4 frágeis, conforme `a6d8e3a` já alertou). Usar só **distância** como soft context.
- `macro_leg` — REFERENCE_ONLY (5 linhas manuais; não derivado).
- Todo o resultado `a6d8e3a` permanece **UNTRUSTED**.

## 7. Definição visual correta de demand/supply para L2/BPT (proposta — NÃO implementar)

- **OB Demand 4H relevante** = box DEMAND **abaixo da entrada**, que (a) é **origem da perna** que produziu o CHoCH, (b) foi **tocada/respeitada** no retest, (c) está **abaixo do SL estrutural**, (d) **fresca** (não mitigada), (e) a **distância em ATR** define "suporte próximo" vs "longe". Presença sozinha não basta.
- **Supply overhead relevante** = box SUPPLY **acima da entrada**, **fresco**, a **curta distância em ATR** (bloqueia o movimento), distinguindo **rompido/aceito** (preço passou) de **rejeitado** (preço virou). NAO ≈ entrar logo abaixo de supply fresco próximo; BOM ≈ supply distante ou já rompido / céu limpo.
- **Box útil vs irrelevante:** filtrar por idade (x1/x2), por toque/mitigação, e por estar no caminho do trade. Caixa antiga distante e já mitigada = irrelevante.

## DA appendix

- Não defendi o resultado anterior? ✅ marcado UNTRUSTED + refutado com dados.
- Output técnico não tratado como verdade vs GT visual? ✅ status NEEDS_USER_VISUAL_CONFIRM.
- `at_D1_demand=0/17` não usado como conclusão? ✅ diagnosticado como artefato (D1 demand existe 17/17 a ~2 ATR).
- `supply_overhead` não usado como veto? ✅ explicitado que mataria 12/17 BOM.
- OB Demand 4H auditada explicitamente? ✅ 16/17 BOM têm demand 4H abaixo (~2.76 ATR).
- Não inventei definição sem exemplos? ✅ proposta §7 ancorada nos 23 eventos; não implementada.
- Backtest/PnL/plotagem? ❌ nenhum. Produção intacta? ✅. Caminho B? ❌.

**DA verdict: PASS — diagnóstico anterior refutado (demand below existe 16-17/17; 0/17 = artefato de threshold). Sinal real = distância ao supply overhead (NAO compra contra o teto; small-n). Flags binárias a redefinir como distância+qualidade. Nada promovido; produção intacta.**

---

*Read-only. RAW-only. Outputs: este doc + `results/l2_bpt_macro_context_gt_visual_reconciliation.csv` (23 eventos). Script: `.../v1/macro_visual_reconcile.py` (RAW gz; py_compile OK). `a6d8e3a` = UNTRUSTED.*

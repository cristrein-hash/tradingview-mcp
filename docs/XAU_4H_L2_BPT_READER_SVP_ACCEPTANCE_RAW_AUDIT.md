> ⚠️ **RETRATAÇÃO (2026-06-23):** o §1 deste doc concluiu que POC/VAH/VAL de volume estavam `UNKNOWN_BLOCKED`
> ("não serializado no RAW"). **ISSO ESTAVA ERRADO** — por misleitura do layout `session_vp.last3.v=[t,POC,VAH,VAL]`
> (assumido como `[t,price,h,l]`). A VA de volume REAL existe no RAW, foi extraída por `extract_svp.py` →
> `repro_recovery/svp_bars.jsonl`, consumida pela DSPA F6 e validada causal no commit 7f3c852. Correção completa:
> `docs/XAU_4H_L2_BPT_SVP_VOLUME_PROVENANCE_AUDIT.md` + memória [[reference_svp_value_area_provenance]]. O TPO
> (tempo) permanece como contexto secundário válido, mas NÃO é a VA de volume e NÃO era o único caminho. As
> seções abaixo ficam como registro histórico do erro.

# XAU 4H L2/BPT — SVP / ACCEPTANCE RAW AUDIT (eixo FUEL-vs-WALL) — 2026-06-23

Bloco: mapear `session_vp` → POC/VAL/VAH + acceptance ao RAW para resolver o eixo bloqueado que os audits
RAW-clean apontaram como decisivo (supply-as-FUEL vs supply-as-WALL). Read-only audit primeiro; build só se
reconstruível com fidelidade. **Não fabricar POC/VAL/VAH.** Durante o DA deste bloco descobriu-se também um
**look-ahead no anchor** (corrigido aqui — ver §5).

Scripts: `results/_DA_svp_raw_structure_audit.py`, `_DA_svp_raw_study_audit2.py`, `_DA_svp_volume_feasibility.py`,
`_DA_lookahead_window_check.py` (read-only); builder `l2_bpt_raw_svp_acceptance_builder.py` →
`results/l2_bpt_raw_svp_acceptance_episodes.jsonl` (+ merge no backbone). Gate exit 0. Fonte RAW:
`XAUUSD_4H_replay_2019-12_to_2026-current_SVP_LUX_RAW.jsonl.gz`.

> CANON: diagnóstico de leitura por episódio (SANITY_PROBE). NÃO é gate/edge/hit-rate, NÃO vira regra/policy/score.
> `ACCEPTED_ABOVE_VALUE → FUEL` é achado DIAGNÓSTICO, jamais regra operacional. POC/VAL/VAH não fabricado.

---

## 1. VEREDICTO DE FIDELIDADE — POC/VAL/VAH (VA de VOLUME LuxAlgo) = **NÃO reconstruível → BLOCKED**

Auditoria da estrutura RAW do bloco SVP, registro a registro (independe do anchor — definitivo):

| Container RAW | O que tem | Serve p/ POC/VAL/VAH? |
|---|---|---|
| `session_vp` = `{id, n, ok, last3}` | série **por-barra** `[time, preço, high, low]`, só os **últimos 3** itens/snapshot | **NÃO** — sem volume-por-nível; perfil completo não serializado |
| `study_values["Session Volume Profile"]` | `{Up, Down, Total}` = volume real da **barra em desenvolvimento** | **NÃO** — volume da barra, não histograma volume×preço; sem níveis POC/VAH/VAL |
| `pine_lines` / `pine_labels` | só SMC / HTF Power of Three / NAS | **NÃO** — nenhuma linha/label POC/VAH/VAL plotada |

**Conclusão:** o value-area de **VOLUME** do LuxAlgo (POC/VAL/VAH) **nunca foi serializado** — nem o histograma
volume×preço, nem os níveis plotados. **O que falta exatamente:** (a) distribuição volume-por-nível-de-preço da
sessão; (b) níveis POC/VAH/VAL desenhados. Sem isso, qualquer POC/VAL/VAH seria **fabricado** — proibido.
**Permanece `UNKNOWN_BLOCKED`** (`svp_poc_val_vah`). Destravar no futuro = re-capturar a **plotagem** da SVP.

---

## 2. O QUE O RAW PERMITE (honesto, source-mapped, NÃO é o VA de volume)

1. **`svp_bar_volume_raw` — RAW_ORIGINAL_OK.** Volume real por barra (`Up/Down/Total` da study Session Volume
   Profile), juntado por **tempo real da barra** (sem grade fixa). 19/19 episódios vivos. Volume nativo SVP
   (validado real). Métricas: `entry_up_ratio`, `last6_up_ratio`.
2. **`tpo_value_area` — DERIVED_FROM_RAW_WITH_MAPPING.** Value-area de **TEMPO** (TPO/Market-Profile) do OHLC RAW
   das barras **PRÉ-entry** (sem a própria barra de entry = sem circularidade). `tpo_acceptance` = close da entry
   vs VAH/VAL anterior. **EXPLICITAMENTE ≠ VA de volume LuxAlgo** — proxy de tempo-no-preço, rotulado como tal.

---

## 3. SPOT-CHECK CAUSAL — o eixo FUEL-vs-WALL é explicado?

8 casos (FUEL = correu; WALL = travou), **janela causal (pós-fix do anchor, §5)**:

| bar | lbl | sup_cat | distSup | TPO_acceptance | entryUp% | last6Up% |
|---|---|---|---|---|---|---|
| 4926 | FUEL | SUPPLY_BLOCKS | 1.61 | **ACCEPTED_ABOVE_VALUE** | 1.0 | 0.78 |
| 3949 | FUEL | SUPPLY_FAR | 2.42 | **ACCEPTED_ABOVE_VALUE** | 1.0 | 0.63 |
| 8878 | FUEL | SUPPLY_NEAR | 0.59 | INSIDE_VALUE | – | 0.54 |
| 4401 | FUEL | SUPPLY_BLOCKS | 1.57 | INSIDE_VALUE | 1.0 | 0.72 |
| 1522 | FUEL | SUPPLY_FAR | 2.40 | INSIDE_VALUE | 0.0 | 0.77 |
| 5627 | FUEL | SUPPLY_BLOCKS | 1.87 | ACCEPTED_BELOW_VALUE | 0.0 | 0.44 |
| 3825 | WALL | SUPPLY_NEAR | 0.61 | ACCEPTED_BELOW_VALUE | 0.885 | **0.24** |
| 3929 | WALL | SUPPLY_BLOCKS | 1.34 | INSIDE_VALUE | 1.0 | 0.64 |

**Resolução PARCIAL — honesta (e mais fraca que a versão contaminada por look-ahead, que dava 3/3):**
- **`ACCEPTED_ABOVE_VALUE` → FUEL, 2/2** (4926, 3949). Aceitação acima do value-area de tempo é sinal RAW limpo
  do **polo FUEL**, mas **raro** (2 de 8). Achado diagnóstico, NÃO regra.
- **`ACCEPTED_BELOW_VALUE` divide:** 5627 (FUEL, correu) e 3825 (WALL, travou) — abaixo do valor NÃO discrimina.
- **`INSIDE_VALUE` (4 casos) ambíguo** (3 FUEL, 1 WALL). O **esforço de volume** ajuda só parcialmente: 3825
  (WALL) tem `last6Up%=0.24` (venda → wall), mas **3929 (WALL) tem 0.64** (compra e travou) — volume sozinho
  **não fecha o wall** por bloqueio estrutural.

**Veredicto:** eixo **ADIANTADO, não fechado**. Sinal RAW limpo só no polo FUEL quando há aceitação acima do
value-area de tempo (raro); `INSIDE/BELOW` e a discriminação do WALL exigem o **VA de VOLUME LuxAlgo**, que
permanece **BLOCKED**. Nada fabricado. `supply colado = fade` segue **REFUTADO/quarentenado** (bloco anterior).

---

## 4. STATUS DOS CAMPOS (manifest, 23 signals, gate exit 0)

| campo | status |
|---|---|
| `svp_bar_volume_raw` | **RAW_ORIGINAL_OK** (Up/Down/Total real por barra) |
| `tpo_value_area` / `tpo_acceptance` | **DERIVED_FROM_RAW_WITH_MAPPING** (TPO tempo; ≠ volume VA; pré-entry) |
| `svp_poc_val_vah` (VA de volume LuxAlgo) | **UNKNOWN_BLOCKED** (não serializado; não fabricado) |
| `acceptance` (textual antiga) | UNMAPPED_DERIVED_DISALLOWED; proxy honesto = `tpo_acceptance` |
| backbone `svp_status` / `acceptance_status` | `PARTIAL_RAW` / `TPO_PROXY_RAW` |

---

## 5. LOOK-AHEAD NO ANCHOR (achado do DA) + FIX DE FUNDAÇÃO

O DA deste bloco encontrou look-ahead no anchor herdado do `l2_bpt_raw_backbone_builder.py`:
- **Causa 1:** o anchor `close-match` (versão a72b012) escolhia a barra de **close mais próximo** do frozen — sem
  trava causal — e em **13/19 episódios** caía 1-2 barras DEPOIS da entry; ep 1661 caiu na sessão errada (−15
  barras), sem warning. A janela que o reader cego viu e o supply/demand foram computados em barra futura.
- **Causa 2 (mais funda):** `bar_open()` assumia grade 4H fixa em UTC. A grade do feed **desloca com o DST de
  NY** (ex.: mar/2023 abre 03/07/11/…; ago/2023 abre 02/06/10/…), então o `bar_open` de offset fixo errava o
  bar para parte dos episódios — o que o close-match mascarava à custa de causalidade.

**Fix (este bloco):** anchor por **as-of join no timestamp REAL da última barra fechada** (sem assumir grade):
o snapshot ancorado é aquele cuja última barra fechada == entry (ENTRY[b]); fallback as-of (≤1 barra antes);
**nunca barra futura**. Resultado: **19/19 causal (zero futuro), 19/19 entry exata**. Fidelity de close vira
WARNING: 3/19 (1661, 4401, 1775) têm feed RAW PEPPERSTONE ~$13 ≠ frozen — diferença de **feed**, não look-ahead,
declarada por episódio (`anchor_close_fidelity`, `warnings`). O volume SVP também passou a juntar por tempo real.

**Impacto sobre o bloco anterior (RAW backbone + Clusters 1/2, já pushado c3fcbeb..97998e3):**
- A leitura cega dos clusters 1/2 e o supply/demand do backbone **anteriores** tinham 1-2 barras futuras + grade
  DST errada. Ex.: `dist_supply` de 5627 era 0.84 ATR (contaminado) e causalmente é **1.87 ATR** (SUPPLY_BLOCKS).
- **Consequência:** as conclusões de lente daquele bloco precisam de **re-validação** sobre janelas causais. Os
  pacotes `raw_rebuild_cluster{1,2}` e os `reader_dossier_RAW_FROZEN.md` são **pré-fix** (mantidos como histórico).
  **NÃO re-lidos neste bloco** (escopo: sem novo Reader/cluster). Recomendado como próximo bloco autorizado.
- O backbone foi re-rodado causal aqui (foundation corrigida). O **veredicto SVP (§1) independe do anchor** — a
  não-serialização do VA de volume é estrutural.

---

## 6. Próxima etapa recomendada (NÃO executada aqui)

1. **Re-validar Clusters 1/2 sobre o backbone causal** (regenerar pacotes + re-ler com subagentes frescos +
   re-rodar outcome audits) — confirma se as lentes (FUEL/WALL, regime-inverte-significado, RSI-blow-off) sobrevivem
   sem o espiar de 1-2 barras. **Pré-requisito antes de Cluster 3.**
2. Eixo FUEL-vs-WALL só fecha com **VA de VOLUME** — exige re-captura da plotagem SVP (POC/VAH/VAL) no RAW.
3. **Não avançar Cluster 3** enquanto o eixo decisivo (volume VA) seguir bloqueado e os clusters não forem re-validados.

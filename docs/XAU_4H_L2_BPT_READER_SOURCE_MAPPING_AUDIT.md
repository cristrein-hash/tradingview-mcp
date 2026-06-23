# XAU 4H L2/BPT — READER VIVO SOURCE MAPPING AUDIT — 2026-06-23

Auditoria sistêmica de fonte de TODOS os campos do Reader Vivo após o incidente NAS/SMC. Gate executável:
`…/v1/source_gate/check_reader_sources.py` (PASS). Manifest: `…/v1/source_gate/reader_raw_source_manifest.yaml`.
Inventário: `…/v1/results/l2_bpt_reader_source_mapping_inventory.csv`. Política: `docs/RAW_SOURCE_GATE_POLICY.md`.

## O incidente
Conclusão errada "NAS/SMC stale/unreliable" tirada de DERIVADO (`raw_features_2020_2026.jsonl`) que extraía a
**cabeça** do buffer de 500 labels (2018-19) em vez da cauda recente. RAW-first violado. Auditoria provou: o RAW
original tem tudo autêntico. Detalhe: `docs/architecture/NAS_SMC_SOURCE_INCIDENT.md`.

## RAW original vs derivado bugado (spot-check, `results/l2_bpt_raw_indicator_validation.md`)
6 episódios obrigatórios (5826, 4401, 5627, 3949, 3929, 4918): NAS/SMC do RAW são **era-correta** (preços ~close),
o derivado-head era 2018-19. RSI-divergência 'Regular Bullish' do 4918 saiu do RAW. close RAW==frozen OK (<0.5%).

## Mapa por indicador/campo (resumo; detalhe no manifest)

### RAW_ORIGINAL_OK (entram no pacote cego — fonte = RAW)
| campo | RAW field |
|---|---|
| NAS TOP/BOTTOM | `pine_labels[NAS TOP BOTTOM DETECTOR]` (tail as-of-bar) |
| SMC BOS/CHoCH/EQH/EQL | `pine_labels[Smart Money Concepts LuxAlgo]` |
| Market Order Bubbles | `pine_shapes_bubbles[...].activations_per_plot` |
| RSI + divergência | `study_values[Relative Strength Index]` (RSI, Regular Bullish/Bearish) |
| OHLCV (forma) | `ohlcv` (DERIVED_FROM_RAW_WITH_MAPPING — frozen fiel, fidelity <0.4%) |

### BLOQUEADOS — fora do pacote cego até mapear ao RAW
| campo | status | RAW base | ação |
|---|---|---|---|
| nas_recent / smc_recent | DERIVED_ARTIFACT_BUG | pine_labels | NÃO USAR (usar RAW) |
| bubbles_recent | UNMAPPED_DERIVED | pine_shapes_bubbles | usar RAW |
| sup_cat / pol_cat / clean_sky / dist_supply / dist_demand | UNMAPPED_DERIVED | `pine_boxes[Custom OB Detector v11]` | mapear de pine_boxes |
| acceptance | UNMAPPED_DERIVED | ohlcv + SVP | reconstruir pela forma (não confiar textual) |
| SVP / POC / VAL / VAH | UNMAPPED_DERIVED | `session_vp` (bloco SVP_LUX_RAW) | mapear do session_vp |
| weekly_slope / cascade / leg (Camada 1) | UNMAPPED_DERIVED | OHLC 1D/weekly | mapear o cômputo de regime ao RAW |
| Custom OB boxes / SMC boxes-lines | UNKNOWN_BLOCKED | `pine_boxes`/`pine_lines` | extrair do RAW |

## Impacto sobre Clusters 1 e 2 (honesto)
- A leitura cega dos clusters 1/2 rodou **form-only** (sem indicador) e sobre OHLC/contexto **derivado**. Resultados
  (9/9 e 9/10) permanecem válidos como diagnóstico de leitura, MAS o backbone de auction (sup_cat/clean_sky/SVP/weekly)
  veio de derivado não-mapeado. A correção do indicador (NAS/SMC/bubbles/RSI=RAW) só cobre a camada de indicador.
- **Próximos pacotes cegos:** os campos BLOQUEADOS (auction context + SVP + regime) ficam FORA até serem mapeados ao
  RAW (`pine_boxes[Custom OB]`, `session_vp`, OHLC 1D/weekly). É o débito de fonte declarado, não escondido.

## DÉBITO BASELINE + RATCHET (buraco sistêmico do DA, fechado)
Dois rounds de DA. Round 1: o gate via só manifest + 1 layer (PASS falso). Round 2: o scan por NOME de builder
(filename-glob) tinha rename-escape (builder novo com outro nome passava; assemblers upstream não varridos).
**Correção final (content-driven, rename-proof):** o enforcement do check #8 é no **ARTEFATO DE INPUT que o Reader cego
lê** — `results/blind_pack_*/reading_packet_BLIND.md` (+ `*agent_input*.json`) — varrido por **nomes de campo
bloqueados** (`nas_recent`, `smc_recent`, `bubbles_recent`, `sup_cat`, `pol_cat`, `clean_sky`, `dist_4h_supply/demand`,
`dist_poc`, `above/below_value`). Assim **qualquer** builder (qualquer nome) que produza um input cego com campo
bloqueado é pego no artefato. Provado adversarialmente: input cego novo com `sup_cat` → gate exit 1 (independe do nome).

Round 3 (re-DA): o scan estava ancorado em `blind_pack_*/` — dois agent-inputs cegos (`_structural_agent_input_blind.json`,
`_microstructure_agent_input_blind.json`) ficavam em `results/` root e escapavam (HOLE A, live). **Correção:** scan
**recursivo por nome `*blind*` em `results/**`** (qualquer localização, md/json/txt). Provado: novo `*_blind.json` em
`results/` root OU novo `*BLIND.txt` sob `blind_pack_` com sup_cat → gate exit 1.

Débito ATUAL declarado (baseline explícito = 6 inputs cegos existentes; ação=mapear Camada-1 ao RAW):
- `_structural_agent_input_blind.json`, `_microstructure_agent_input_blind.json`, `_deep_eracontrol_blind.json`, `_structural_blind_compact.json` (pipeline antigo, em results/ root): sup_cat/pol_cat/dist_4h_*.
- `blind_pack_cluster2/reading_packet_BLIND.md` e `blind_pack_cluster4918/reading_packet_BLIND.md`: sup_cat/pol_cat/clean_sky/above_value.
- Fontes UPSTREAM declaradas (report-only): `l2_bpt_episode_context_assembler.py` (8 campos, lê o frozen direto), `l2_bpt_reader_dossier_assembler.py` (5), os 2 packet builders, `l2_bpt_blind_pack_cluster4918.py` (PIL: + nas/smc/bubbles_recent).

**RATCHET:** o gate **FALHA (exit 1)** em qualquer INPUT cego NOVO (`*blind*` md/json/txt em results/**) com campo bloqueado fora do baseline. Débito só pode encolher.
**Limite declarado (bloco futuro):** o scan assume que input cego carrega `blind` no nome (convenção do protocolo); enforcement 100% à prova exigiria um *reader input manifest* dirigindo o scan. Documentado, não escondido.
**Ação:** mapear Camada-1 (sup_cat/clean_sky/SVP/weekly + Custom OB boxes + session_vp + OHLC 1D/weekly) ao RAW —
bloco futuro. Até lá, cluster novo NÃO pode embutir esses campos sem mapeamento (gate barra).

Limites conhecidos (não fechados neste bloco, declarados): o gate não EXECUTA o `fidelity_check` (string), nem
cruza `current_source` com a realidade do disco — defesa adicional para bloco futuro.

## Protocolo futuro (fail-fast)
1. Todo pacote cego declara `source_mapping_status` por campo.
2. Campos UNMAPPED_DERIVED_DISALLOWED / UNKNOWN_BLOCKED ficam FORA do pacote.
3. `check_reader_sources.py` roda e tem de dar exit 0 antes de qualquer pacote/cluster novo.
4. RAW vence derivado; RAW≠chart = source-mapping incident; nenhum derivado entra por "parece funcionar".
5. `allowed_as_decision=NO` para todos — indicador/feature é evidência de leitura, nunca gate/score/veto.

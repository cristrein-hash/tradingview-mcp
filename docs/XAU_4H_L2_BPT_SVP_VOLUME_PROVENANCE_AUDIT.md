# XAU 4H L2/BPT — SVP/SMC VOLUME PROVENANCE AUDIT — 2026-06-23

Bloco fechado pedido por Cris após suspeita (correta) de que o veredicto "VA de volume BLOCKED" era
incompleto/errado. Objetivo: provar definitivamente se POC/VAH/VAL de volume estão (1) no RAW, (2) como objetos
plotados, (3) em artefato antigo validado, (4) reconstruíveis via proxy, (5) realmente bloqueados.

## VEREDITO: O BLOQUEIO ANTERIOR ESTAVA ERRADO — a VA JÁ EXISTE e JÁ FOI VALIDADA

Categoria final: **PRIOR_VALIDATED_RAW_EXTRACTION_EXISTS.** Os níveis POC/VAH/VAL de volume **estão serializados
no RAW** e já foram extraídos, consumidos e validados causalmente — meses atrás. O bloco SVP (commit 1267c8d)
declarou `UNKNOWN_BLOCKED` por **misleitura do layout do campo** (2º incidente de fonte do dia).

## Categorização por fonte

| Fonte | Resultado | Evidência |
|---|---|---|
| 1. RAW `session_vp.last3[i].v` | **RAW_LEVELS_FOUND** | `v = [time, POC, VAH, VAL]` — provado VALUE-AREA, não OHLC (ver §prova) |
| 2. pine_lines/boxes/labels/shapes do SVP | **NOT_FOUND** | dump exaustivo 7 episódios (`_DA_svp_provenance_object_audit.py`): só SMC desenha linhas/boxes/labels; SVP não plota via esse container |
| 3. study_values `Session Volume Profile` | só `{Up,Down,Total}` (volume da barra, NÃO a VA) | confirmado todos episódios |
| 4. Artefato antigo validado | **PRIOR_VALIDATED_ARTIFACT_FOUND** | `repro_recovery/svp_bars.jsonl` (10073 bars, `vp=[POC,VAH,VAL]`) via `extract_svp.py`; consumido por DSPA F6; validado commit 7f3c852 |
| 5. Proxy | desnecessário (a VA real existe) | TPO (tempo) e volume-weighted são proxies inferiores; descartados |

## A prova (v = VALUE-AREA, não OHLC)
`results/_DA_svp_va_vs_ohlc_verify.py` comparou `[v2,v3]` de cada `session_vp.last3.v` contra o high/low REAL da
barra (4000 barras): **0,12% (485/4000) batem com high/low** → não é OHLC; **85% ficam FORA do range da barra**
→ é uma VA de sessão (mais larga que 1 barra 4H), que desenvolve intra-sessão. Ordenação VAH≥POC≥VAL confirmada.
**Confirmação visual (Cris):** print do indicador SVP com `Value Area Volume = 70`, `Row Size = 24`,
`Extend POC/VAH/VAL Right` — a VA existe e é plotada. Minha heurística antiga (`len(v)==4 → [t,price,h,l]`) errou
o layout.

## Pipeline existente (FONTE DE VERDADE — não recriar)
- `extract_svp.py`: RAW gz `session_vp.last3` → `repro_recovery/svp_bars.jsonl` (`vp=[POC,VAH,VAL]`, vol, rsi, close, as-of-bar).
- `l2_bpt_dspa_path_features.py` **F6**: → `f6_dist_poc_atr`, `f6_above_value`, `f6_below_value`, `f6_svp_state`
  (`results/l2_bpt_dspa_path_features_276.csv`). **Cross-check confirmou identidade** com a VA as-of-entry (3825 IN_VALUE/0.0; 3929 IN_VALUE/−0.3; 3949/4401/4918/4926 ACCEPTING_ABOVE_VALUE; dist_poc idêntico).
- Validação causal: commit `7f3c852` + `results/l2_bpt_svp_causality_verification.csv` (1682 sessões, VP mutável intra-sessão, VA width cresce, 0 look-ahead, volume real).
- Status canônico: `svp_poc_val_vah` = **DERIVED_FROM_RAW_WITH_MAPPING**, allowed_in_blind_packet=YES, allowed_as_decision=NO.

## Achado: a VA REAL resolve o eixo FUEL-vs-WALL (diagnóstico nos 9 contrastivos, NÃO regra)
| bar | lbl | svp_state (VA real) | dist_poc | → |
|---|---|---|---|---|
| 4918/4926/4401/3949 | FUEL | ACCEPTING_ABOVE_VALUE | +0.86/+2.07/+1.31/+2.83 | acima da VA → correu |
| 8878/5627/1522 | FUEL | IN_VALUE | +0.21/+0.16/+0.16 | acima do POC → correu |
| 3825/3929 | WALL | IN_VALUE | 0.0/−0.3 | no/abaixo do POC → travou |

**9/9 separados:** aceito acima da VA, ou acima do POC dentro da VA → FUEL; no/abaixo do POC → WALL.
Notavelmente **4926 = ACCEPTING_ABOVE_VALUE** (a VA real o confirma como fuel — o que o proxy TPO e a leitura
sem-VA erravam). **Isto é CALIBRAÇÃO nos 9, não validação** — exige set independente dentro do corpus; **não vira
gate/score/regra** ([[feedback_calibration_vs_validation_45_groups]]).

## Impacto / correção
- `source_gate/reader_raw_source_manifest.yaml`: `svp_poc_val_vah` UNKNOWN_BLOCKED → **DERIVED_FROM_RAW_WITH_MAPPING**.
- `docs/XAU_4H_L2_BPT_READER_SVP_ACCEPTANCE_RAW_AUDIT.md`: §1 ("BLOCKED") **corrigido** (header de retratação).
- Operating Manual: lentes `QUARANTINED_PENDING_VOLUME_VA` / `STILL_INSUFFICIENT` premissadas em "VA indisponível"
  estão **ERRADAS na premissa** — a VA existe; o eixo é RE-TESTÁVEL (próximo bloco, sob autorização: re-ler Clusters
  1/2 COM a VA; validar a separação acima/abaixo-POC dentro do corpus, sem virar regra).
- Builders de proxy (TPO ok como contexto secundário; volume-weighted) NÃO são o caminho — a VA real é superior.

## Próxima etapa recomendada (NÃO executada — fora do escopo deste bloco)
Re-ler Clusters 1/2 **com a VA real** (svp_state/dist_poc/above_value via F6/svp_bars), re-rodar audits, e validar a
separação FUEL/WALL DENTRO do corpus (não como regra). Não iniciar Cluster 3 antes disso.

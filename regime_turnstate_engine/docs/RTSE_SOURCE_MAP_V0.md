# RTSE_SOURCE_MAP_V0 — Mapa de Fontes & Proveniência

**Status:** PLANNING. Documentação only. Define O QUE pode entrar, com que rastreio, e o que é terminantemente proibido. É o gate L0 (Source & Provenance).

---

## 1. Princípio
Nada entra no RTSE sem **proveniência rastreável**. Cada estado emitido carrega de onde veio, em que barra, sob qual política de shift. Sem rastreio → `data_quality != OK` → não vai para validação séria. Isto materializa a parede anti-look-ahead/anti-proxy como código, não como boa intenção.

## 2. Classificação obrigatória de cada feature
Toda feature entra com um selo:
- `RAW_DIRECT` — lida direto do OHLCV/campo RAW da fonte.
- `RAW_DERIVED_VERIFIED` — derivada de RAW, com derivação auditada e shift-correta (ex.: regime v5, swept_prior_low, h1_pos, bottom-power).
- `RESEARCH_ONLY` — usável em pesquisa/calibração, **nunca** em validação de promoção.
- `REJECTED` — proibida (ver §4).
- `UNKNOWN` — sem trace → **bloqueada**; não entra em validação até virar RAW_DERIVED_VERIFIED ou ser REJECTED.

## 3. Inputs PERMITIDOS (com fonte)
| Input | Selo | Fonte | TF |
|---|---|---|---|
| OHLCV RAW | RAW_DIRECT | RAW replay / dataset_registry | 15M/1H/4H/1D |
| pine_boxes/labels/study_values RAW | RAW_DIRECT | TradingView RAW (nunca SLIM) | — |
| `stable_daily_state` (regime) | RAW_DERIVED_VERIFIED | `engine_regime15m_v5.py` (D-1) | 1D |
| `intraday_drawdown_override` | RAW_DERIVED_VERIFIED | regime v5 (1H closes) | 1H |
| 4H-native regime fallback (pré-2024) | RAW_DERIVED_VERIFIED | `engine_4h_regime_gate_RAW.py` | 4H |
| `swept_prior_low` | RAW_DERIVED_VERIFIED | lab (null p=0) | 15M/1H |
| `h1_pos` | RAW_DERIVED_VERIFIED | (null p=0,018) | 1H |
| `bottom_power_fingerprint` | RAW_DERIVED_VERIFIED | bottom-power engine (AUC~0,70) | 15M/1H |
| HTF alignment (h4_up/h1d_up) | RAW_DERIVED_VERIFIED | stack 15M aprovado | 4H/1D |
| External Factors snapshot | RAW_DERIVED_VERIFIED | `external_factors_v2/snapshots/latest.json` (as-of) | — (só prior de confiança) |

## 4. Inputs PROIBIDOS (e por quê)
| Proibido | Motivo |
|---|---|
| outcome futuro / resultado do trade | look-ahead direto |
| `true_reversals_M8` / labels M8 como FEATURE | label forward = circularidade; M8 é só RÉGUA (validação) |
| capped realR | mistura outcome no input |
| endpoint humano / leitura manual do Cris | hindsight, não-causal |
| SLIM / proxy não-validado | proibição permanente (feedback_never_use_slim_features) |
| pivot futuro / confirmação futura escondida | look-ahead |
| zona/golden-zone hindsight | macro-bottom refutado = hindsight |
| feature interpretativa sem RAW/source-trace | UNKNOWN → bloqueada |

## 5. Contrato de proveniência (cada estado emitido)
```
{
  "as_of_bar": "<ts close>",
  "timeframe": "15M|1H|4H|1D",
  "source_fields": ["<lista RAW usada>"],
  "feature_seals": {"<feature>": "RAW_DIRECT|RAW_DERIVED_VERIFIED|..."},
  "shift_policy": "close_only_shift1",
  "daily_policy": "D-1",
  "provenance_hash": "<sha das primitivas+config>",
  "config_hash": "<sha rtse_registry>",
  "git_sha": "<commit>",
  "missing_inputs": [],
  "data_quality": "OK|DEGRADED|BLOCKED"
}
```
- `data_quality=DEGRADED` (input faltando não-crítico) → estado emitido com confiança reduzida + flag.
- `data_quality=BLOCKED` (input crítico ausente ou selo UNKNOWN/REJECTED) → **não emite estado** (default-deny de dado).

## 6. Regra de ouro
Se uma feature não consegue responder SIM a "essa info existia no close da barra, foi shift-correta, e tem trace RAW?" → ela é `UNKNOWN` ou `REJECTED`. Ponto. (Auditada pelo RTSE Lookahead Red-Team Agent — `RTSE_VALIDATION_PROTOCOL_V0` §Red-team.)

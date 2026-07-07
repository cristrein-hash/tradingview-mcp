# XAU 15M LONG — N96 · RAW-Native Multi-Timeframe Loser Filter Audit

**Cris 2026-07-07.** RAW-first absoluto. Read-only análise; extração de primitives 30M/1H autorizada pelo Cris. Sem push sem autorização.

## 1. Executive verdict
**NO_CLEAN_FILTER_FOUND** (gate automático) — **com ganho de processo maior: extração RAW-native completa 15M/30M/1H/4H/1D concluída** (corrige a contaminação do Fractal-MTF). As assinaturas descritivas das famílias de loser são REAIS e RAW-native, mas **não formam filtro preditivo out-of-fold** (LOO hit-3R 0,525 < base 0,542; mining-null P=0,605). A assinatura de **D (bear ativo) = RSI-HTF fraco** fica como candidata a **REVIEW_LAYER / flag de revisão humana**, não gate — pendente forward.

## 2. O que é o N96
- **Onde:** `research/xau_15m_bb_nas_leonardo/entry_engine_master_20260707.py` + `agent_ctx_kit.py` (commits 2baf2e2/28db774). Reproduz byte: **N96, 52 winners / 44 losers, hit-3R 54,2%** (reclaim-R subset 61,4%).
- **Período:** 2025-08-01 → 2026-07-02. **Fonte:** 15M primitives (RAW-15M lineage, source guard PASS) = **VERIFIED_DERIVED**.
- **Não depende** de blocos contaminados (Fractal-MTF/FaseD/ER). Independente.

## 3. Mapa corrigido dos 44 losers (correções do Cris incorporadas)
- **C — Distribuição de topo / topo de range bear (22):** #17,18,20,21,23,25,31,36,42,46,48,55,**56,57,58,59,60**,65,79,83,84,85.
- **D — Bear ativo (14):** #27,49,50,66,67,68,69,**80**,86,87,89,92,93,94.
- **R — Range neutro (4):** #5,6,7,8 (consolidação meio-agosto em uptrend).
- **Gestão / NÃO-FILTRAR (4):** **#24, #32, #64, #77** (recuperáveis por gestão humana / BE / timing).

## 4. Correções do Cris incorporadas
- **#56-#60 = distribuição/topo de range BEAR** (não range inocente) → família **C**.
- **#58 = C.** **#80 = D** (confirmado).
- **#64, #77, #24 = gestão/BE** (quase-winners, SL ajustável a ~0) → **não filtrar**.
- **#32 = timing** (o certo era esperar a demanda inferior, como no #33) → **não filtrar**.

## 5. RAW / source mapping por timeframe
| TF | fonte | source guard | disponível | estado |
|---|---|---|---|---|
| 15M | `primitives/` (9 blocos) | PASS | sim | RAW-15M lineage |
| **30M** | `htf_primitives/XAUUSD_30m_*` (4 blocos) | extractor validado (`build_30m1h_primitives.py`, cópia fiel de `build_htf_primitives`) | **sim — extraído 2026-07-07** | RAW 30M nativo |
| **1H** | `htf_primitives/XAUUSD_60m_*` (3 blocos) | idem | **sim — extraído** | RAW 1H nativo |
| 4H | `htf_primitives/htf_4H` | `build_htf_primitives` (RAW 4H gz) | sim | RAW 4H nativo |
| 1D | `htf_primitives/htf_1D` | idem | sim | RAW 1D nativo |
- Cobertura 30M/1H: 2024-05 → 2026-05-25 (falta ~5 sem finais, igual ao gap RAW-15M pré-extensão). Cobre a maioria do N96.
- **Zero resample. Zero Fractal-MTF. Zero SLIM.** Causalidade verificada: `CAUSAL_BAD=0/96` (barras HTF corrente excluídas; zonas por born_t, nunca last_t).

## 6. Feature audit (medianas WIN vs famílias, RAW-native, causal)
`n96_loser_raw_mtf_feature_audit.py` → `results/n96_loser_raw_mtf_feature_audit.{csv,summary.json}`.
Sinais descritivos reais (direção estrutural correta):
- **D (bear ativo):** 4H_rsi **45,9** vs WIN 56,2 · 1D_rsi **46,8** vs 57,2 · 1D_trend ~0 vs +0,81 · 4H_trend −0,69. → comprou fraqueza HTF.
- **C (topo/exaustão):** 4H_rsi **61,3** vs 56,2 · 1D_rsi **61,6** vs 57,2 (sobrecomprado) · 1D_trend +1,42 (esticado) · longe de demanda (4H_dem 1,13 / 1D_dem 2,14 vs WIN 0,65/1,63).
- **Winners:** no MEIO — RSI-HTF ~56-57, tendência 1D moderada, demanda a distância média.
- SMC EQH/CHoCH em 30M/1H/4H/1D saíram ~0 na janela testada (janela de eventos curta / direção não capturada — feature a melhorar, não conclusiva). 15M eqh: C=1,0 vs WIN 0,5.

## 7. Resultados (filtro preditivo)
`n96_loser_htf_oof_test.py` → LOO out-of-fold logistic sobre features HTF RAW-native + mining-null:
- **OOF hit-3R 0,525 < base 0,542 · poison 1,31 (corta mais winner que loser) · 2025 15/22, 2026 16/37 · mining-null P=0,605.**
- **Veredito: NO_EDGE_OOF.** As medianas separam in-sample mas o classificador não generaliza — provável confound de regime (RSI-HTF correlaciona com o ano/regime), o mesmo muro de toda a sessão, agora confirmado com a **fonte RAW correta** (não é problema de fonte).

## 8. DA adversarial
Ver `XAU_15M_N96_RAW_MTF_LOSER_FILTER_DA_20260704.md`. Resumo: source RAW-native ✓ · lookahead 0/96 ✓ · resample proibido = não usado ✓ · OOF+mining-null falha = sem overfit a explorar · runner-kill não aplicável (sem gate adotado).

## 9. Candidatas
- **Gate automático:** NENHUM limpo (OOF falha).
- **Review layer / flag humano:** **D = RSI-HTF fraco (4H/1D rsi < ~50 + tendência HTF↓)** — mecanicamente forte e consistente; candidato a *flag de revisão*, não gate. Pendente forward.
- **Gestão/BE:** #24,#32,#64,#77 já identificados como recuperáveis (não são alvo de filtro).
- **Descartado:** classificador multivariado HTF como gate (não generaliza).

## 10. Próximo passo recomendado (sem iniciar sozinho)
Testar a hipótese ÚNICA pré-registada "**cut D = 4H_rsi<50 & 1D_rsi<50**" em **forward / janela virgem** (ou nas próximas ops live do Cris), onde um p de hipótese-única seria honesto. E, se quiser, estender 30M/1H/4H/1D até hoje (coleta autorizada) para fechar o gap de ~5 semanas.

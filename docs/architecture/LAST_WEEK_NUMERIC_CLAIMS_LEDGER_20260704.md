# LAST WEEK — NUMERIC CLAIMS LEDGER (provenance)

**Incident audit** (Cris 2026-07-07) · read-only · janela auditada **2026-06-30 → 2026-07-07** (últimos 7 dias; nome do ficheiro = 20260704 conforme instrução). 198 commits, todos autor `Cristiano Trein` (+Co-Authored Claude), todos pushed, working tree limpo.

**Cadeia de proveniência canónica (15M):** RAW gz 15M (`/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M`) → `build_causal_primitives.py` (RAW-only, verificado) → `primitives/*.json` (derived, committed, 9 blocos) → scripts de pesquisa. Forçada por `_source_guard.py` (PASS calibrado). Manifests/checksum na cadeia `RAW_15M_EXTENSION_*_20260704.md`.

**Status inicial de cada claim = UNVERIFIED → classificado abaixo.**

| claim_id | claim (nº) | onde | script gerador | input (fonte) | output | source_guard | reprod. | STATUS |
|---|---|---|---|---|---|---|---|---|
| C01 | Base N435 WR47,6% +291,5R · SB +233,6R (XAU 15M swept-runner) | memory / 04_STATUS_MASTER | engine substrate4 v5 (pré-semana) | primitives (RAW-15M lineage) | results/*.json | PASS | não re-rodado nesta auditoria | **VERIFIED_DERIVED** (lineage OK; rerun byte não executado — ver required reruns) |
| C02 | Lab E slippage SB +233,6R r/DD16,4 (435/435 DA) | project card | lab_e (pré-semana) | primitives | results | PASS | não | **VERIFIED_DERIVED** |
| C03 | Lab A P1 disp-early +19R p=0,726 · P5 budget · resto FAILS | project card | lab_a scripts | primitives + r3_target_universe | results/jsonl | PASS | não | **VERIFIED_DERIVED** |
| C04 | Lab F 26 variantes NO_STREAK_DD_WR_SOLUTION; F4 sizing RISK_CONTROL | project card | lab_f | primitives | results | PASS | não | **VERIFIED_DERIVED** |
| C05 | Lab G Sistema A EMA-SHAKEOUT N53 WR60,4 DD−3,2 NET+25,9; 21/53 fora-base; 15 flushes sem sweep | project card | lab_g (universo 4499+240) | primitives → lab_g_candidates.jsonl (intermediário sancionado) | results | PASS | não | **VERIFIED_DERIVED** |
| C06 | universos 4499/4502/4742 candidates | vários | lab_g/context inventory | primitives | jsonl | PASS | não | **VERIFIED_DERIVED** |
| C07 | RAW 15M extension +2714 barras (9º bloco) 2026-05-25→07-03; kill-check N=0; source guard 7/7 | RAW_15M_EXTENSION docs | safe_backtest + build_causal_primitives | **RAW gz 15M direto** | primitives + manifest+SHA+roundtrip | PASS | manifest/checksum validados | **VERIFIED_RAW** |
| C08 | MTF-signature 35 manuais lift 5,7–6,7× = FILL-FICTION (refutada) | project card | mtf signature scripts | primitives + shapes MCP | results | PASS | não | **VERIFIED_DERIVED** (conclusão = REFUTAÇÃO, não claim ativa) |
| C09 | PLT/DM assimilação: escada markup r=3 9/10; confluência N101 recall14 | XAU15M_PLTDM_ASSIMILATION | bottom_pltdm_confluence_20260707 | primitives + shapes MCP (labels Cris) | results | PASS | reproduz (determinístico) | **VERIFIED_DERIVED** |
| C10 | Entry engine 3R: MARKUP master 54,2% (N96) · reclaim-R 61,4% | entry_engine_master | entry_engine_master_20260707 / agent_ctx_kit | primitives | results/entry_*.json | PASS | **reproduz byte (96/52W/44L/0.542)** | **VERIFIED_DERIVED** |
| C11 | supply_above 72% = LOOKAHEAD parcial; causal 66,7% N9 | filter study §5 | verify_supply_causal_20260707 | primitives + zones | results | PASS | reproduz | **VERIFIED_DERIVED** (auto-refutada) |
| C12 | Kaufman ER perna-anterior OOF 63,5% null 0,038 (impulse_efficiency) | filter study §6c | wf agents + verify_final_phase | primitives | results | PASS | reproduz | **PARTIAL** (promissor-não-validado; multiplicidade não-corrigida — declarado) |
| C13 | Classificador de fase FaseD∩FSM4 N44 68,2% → MATO pelo DA (mining artifact) | provenance N/A | workflow phase + DA | primitives | results | PASS | reproduz; DA=artefato | **INVALID** (winner's-curse composto, já marcado NOT_FOR_DECISION) |
| C14 | **Fractal MTF htf_demand_retest OOF 0,647 mining_null 0,01** | XAU15M_TOTAL_STRUCTURAL_READING §MTF | mtf_feat_htf_demand_retest + mtf_kit | **15M RESAMPLEADO (não RAW 4H/1D)** | results/mtf_feat_*.json | **FAIL** | reproduz o número, mas fonte inválida | **SUSPECT → INVALID (RAW-FIRST VIOLATION)** |
| C15 | classificador fase LOO 0,509 (confound regime, não generaliza) | doc | phase_classifier_loo | primitives | results | PASS | reproduz | **VERIFIED_DERIVED** (negativo honesto) |

**Nota C14:** a violação é dupla — (1) resampleei 15M→4H/1D à mão em vez de ler RAW 4H/1D; (2) reinventei deteção de demanda por zigzag quando **`htf_primitives/htf_4H.primitives.json` + `htf_1D.primitives.json` já existiam** (construídos por `build_htf_primitives.py` do RAW 4H/1D em 2026-06-28) com o OB detector nativo. Source guard FAIL. **O número 0,647 é reproduzível mas a fonte é inválida → não confiável.**

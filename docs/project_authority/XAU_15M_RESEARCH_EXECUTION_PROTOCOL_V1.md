# XAU 15M — Canonical Research Execution Protocol V1

**Cris 2026-07-08. AUTORIDADE.** Processo **action-based e executável** (não memória, não só doc) obrigatório para todos os labs XAU 15M — **especialmente antes do XAU 15M SHORT**. Enquanto este protocolo não estava vivo, o Claude teve liberdade de escolher o caminho de leitura e escolheu atalhos. Este protocolo **remove essa liberdade** com manifests, source guards, blockers e fail-loud.

> **STATUS GLOBAL:** `NO_NEW_STRATEGY_WORK` · `NO_XAU_15M_SHORT` · `NO_NEW_LAB` até o gate passar por lab. Todo lab 15M futuro **tem** de passar `scripts/safety/run_xau_15m_lab_gate.py`.

## A. Problema que resolve (erros raiz recentes)
1. Leitura RAW errada / escolha de ficheiro errado.
2. Resample 15M→HTF usado como fonte (em vez de RAW/primitives nativos).
3. Derived sem lineage (sem source_ref/checksum).
4. **Análise global descontextualizada** — indicadores cruzados como média global.
5. Indicadores avaliados ANTES da leitura estrutural (regime macro + perna).
6. Resultados sem claim ledger ("fiz uma análise, apareceu 61%").
7. Subagents a gerar métricas sem artefato.
8. Commits com vereditos prematuros (ex.: NO_CLEAN_FILTER).

**A trava mais importante:** _sem `macro_regime` + `leg_state` + `family_label`, nenhum indicador pode virar evidência._ Esta regra sozinha teria impedido quase todos os erros recentes.

## B. Ordem obrigatória de qualquer lab 15M
`Prompt → Manifest → Source Guard → Structural Buckets → Indicator Scan → Claim Ledger → DA → Report` (nunca mais `Prompt → Claude escolhe ficheiros → mede → narra`).

- **Stage 0 — Bootstrap:** `git status --short`, safety report, HEAD vs origin, working tree, commits pendentes.
- **Stage 1 — Gate manifest:** nenhum lab começa sem `docs/architecture/XAU_15M_<LAB>_GATE_MANIFEST.md` (template `docs/templates/XAU_15M_LAB_GATE_MANIFEST_TEMPLATE.md`). Sem manifest, o script do lab **aborta**.
- **Stage 2 — RAW/source mapping:** RAW direto · derived · source_ref · checksum · manifest · source guard (`check_xau_15m_raw_lineage.py` → `RAW_LINEAGE_PASS`) · stale status.
- **Stage 3 — Structural-first reading:** ANTES de qualquer indicador, gerar tabela: `trade_id, entry_time, macro_regime, leg_state, regime_phase, position_in_leg, family_label, causal_regime_source`. O script aborta se tentar indicator scan sem bucket (`check_xau_15m_structural_first.py`).
- **Stage 4 — Indicator crossing DENTRO de baldes:** SMC · OB/demand/supply · Bubbles · NAS · SVP (só se source-válido) · RSI · volume · ATR · regime · HTF context. **Global scan como decisão = PROIBIDO.**
- **Stage 5 — Hypothesis freeze:** congelar hipóteses antes do cálculo (pré-registo no manifest).
- **Stage 6 — Execution:** script determinístico, fail-loud (assert N96 reproduz, etc.).
- **Stage 7 — Null / DA:** null apropriado (permutação intra-bucket, feature-search, mining-null) + **DA adversarial via Agent tool real**.
- **Stage 8 — Claim ledger:** todo número → `script/input/output/source_ref/checksum` (template `docs/templates/XAU_15M_CLAIMS_LEDGER_TEMPLATE.csv`).
- **Stage 9 — Report:** o relatório só pode usar claims do ledger.
- **Stage 10 — Commit:** só se `run_xau_15m_lab_gate.py` = `XAU_15M_LAB_GATE_PASS`.

## C. Baldes estruturais obrigatórios (lista canónica)
Indicadores só podem ser avaliados **dentro** destes baldes (nomes exatos aceites pelo blocker):
`BULL_impulse` · `BULL_pullback` · `BULL_excess_top` · `RANGE_neutral` · `RANGE_distribution_top_bear` · `RANGE_accumulation_bottom` · `BEAR_active` · `BEAR_shallow_bounce` · `BEAR_deep_capitulation` · `countertrend_bounce_in_bear` · `management_do_not_filter`.

Primeiro responde **onde o trade está no mercado**, depois pergunta se RSI/SMC/Bubbles/OB/NAS discriminam.

## D. Regras de fonte (proibições — blocker `check_xau_15m_raw_lineage.py`)
Proibido: **SLIM/proxy** · **resample HTF como substituto de RAW/primitives nativos** (`allow_resample=false` default) · staging/cache/tmp sem lineage · derived sem checksum/source_ref · **Supabase como fonte de validação** · **memória como validação** · **chart visual como dado quantitativo** · fontes contaminadas (**Fractal-MTF / FaseD∩FSM4 / Kaufman-ER**) como decisão. RAW multi-TF (15M/30M/1H/4H/1D) já coletado no HD externo — nunca resamplear/reinventar.

## E. Regras para subagents
- Subagents **não committam, não push**.
- Não podem reportar métrica sem artefato (ledger + output).
- O agente principal **verifica `git log` depois** de cada subagent.
- Se não se fez spawn de um `Agent` tool real, **não chamar de "agent"** no doc.

## F. Status language (proibido "validated" nu)
Usar sempre qualificador: `VERIFIED_RAW` · `VERIFIED_DERIVED` · `EXPLORATORY` · `REVIEW_LAYER` · `RISK_CONTROL` · `INVALID` · `NOT_FOR_DECISION`. "approved/validated" sem DA real = bloqueado.

## Enforcement (executável)
```
python scripts/safety/run_xau_15m_lab_gate.py --manifest <m.md> --report <r.md> --ledger <l.csv> [--results a.csv ...]
```
Corre: RAW lineage → structural-first → claims ledger → safety report. **Sem `XAU_15M_LAB_GATE_PASS`, o lab não está completo e não pode ir a commit/aprovação.** Labs antigos (pré-2026-07-08) ficam _grandfathered_ (não re-validados retroativamente); todo lab novo 15M/SHORT passa pelo gate.

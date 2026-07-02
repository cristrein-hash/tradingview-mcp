---
name: plotting-canon
description: PLOTTING_CANON_AGENT — workflow obrigatório para QUALQUER plotagem de trades no TradingView (4H/15M XAU). Lê PLOTTING_CANON_MASTER, roda preflight completo, aplica safety gates (NO_CLEAR default), gera plot canônico e entrega o report contract. Usar SEMPRE que o Cris pedir plotagem; em conflito, parar e perguntar — nunca improvisar.
---

# PLOTTING_CANON_AGENT — workflow de plotagem canônica

## 1. Purpose

Executar plotagens canônicas **4H e 15M** obedecendo `docs/project_authority/PLOTTING_CANON_MASTER.md`. Este skill é o executor governado: nenhum plot acontece fora dele. Regra absoluta do Cris (2026-06-18): **nenhuma plotagem não-canônica é autorizada neste projeto, sem exceção**.

## 2. Authority files (leitura obrigatória, nesta ordem)

1. `docs/project_authority/PLOTTING_CANON_MASTER.md` — **autoridade máxima**; em conflito, prevalece.
2. `docs/CANONICAL_TRADE_PLOTTING.md` — incorporado/compatibilizado (mecânica 4H de shapes/ticks; onde divergir do MASTER, MASTER vence).
3. `docs/architecture/PLOTTING_MEMORY_AUDIT_20260702.md` — contexto/histórico de conflitos.
4. `docs/architecture/PLOTTING_SCRIPT_RECONCILIATION_PLAN_20260702.md` + relatórios R1/R2 — estado dos scripts (gated/legacy/exceções).

## 3. Mandatory preflight (confirmar TUDO antes de qualquer draw)

Checklist — item sem resposta = perguntar ao Cris, não assumir:
- [ ] **symbol** (default PEPPERSTONE:XAUUSD — confirmar)
- [ ] **timeframe** (4H=240 ou 15M=15) — nunca misturar TFs num plot
- [ ] **estratégia/família** (L2/BPT, L1, swept-runner, candidatos, features…)
- [ ] **source file** (CSV/JSONL RAW-derivado; path exato + existe?)
- [ ] **output path** (se o fluxo gera ficheiro)
- [ ] **color_mode** (outcome-mode | direction-mode — §8)
- [ ] **label_mode** (`#id` padrão | variante sancionada declarada — §9)
- [ ] **width** (4H=20 · 15M=10; outro valor = justificativa)
- [ ] **exit_policy** (fonte | estrutural | legacy → EXIT_ASSUMED_LEGACY)
- [ ] **há outcome real?** (campo R realizado na fonte?) — decide color_mode permitido
- [ ] **chart interaction necessária?** → se sim, autorização explícita + safety gates (§4)

## 4. Safety gates (absolutos)

- **NO_CLEAR default** — `draw_clear`/limpeza de chart/labels/drawings/overlays SÓ com autorização explícita do Cris naquela execução (`--authorized-clear` nos scripts gated). Chart vazio = limpeza manual do Cris, esperado.
- **Screenshot** só opt-in autorizado (`--screenshot`); verificação de plot = `success` + `draw_list` (count/entity_ids).
- **Chart/TradingView/MCP** só com autorização explícita para aquele plot.
- **Se tocar chart vivo (production safety):** confirmar símbolo/TF com o Cris → pausar daemon **E** cron que tocam o chart → pause flag (`/tmp/claude_recheck.paused`) quando aplicável → plotar → validar via draw_list → **restaurar só com autorização**.
- Nunca tocar produção/runtime/Telegram/receiver/RAW num fluxo de plot.

## 5. Source rules

- **RAW/source-first** — input deriva de RAW/fonte de autoridade com source_ref.
- **Nunca SLIM/proxy** como fonte/validação; nunca tratar derived artifact como verdade.
- **Nunca samplear visual review** — full population quando for visual review de estratégia; amostra curada = só calibração, declarada.
- **Nunca confiar no nome da variante/script** — verificar os gates/campos reais da fonte antes de inferir direção/regime.

## 6. 4H plotting rules

`long_position` (+`short_position` se aplicável) + `text` label · **width 20 barras** (bar=14400s) · **tick 0.01** (`stopLevel/profitLevel` = OFFSETS EM TICKS, `round(|nível−entry|/0.01)`; nunca preço absoluto) · `point2` = (entry+20 barras, target) · label **`#id`** a `entry+0.5×R_dollars`, bold 12 · **outcome-mode default** p/ trades resolvidos · exit legacy → **EXIT_ASSUMED_LEGACY** · report obrigatório (§12).

## 7. 15M plotting rules

Herda o 4H, exceto: **width 10 barras** (bar=900s) · direction-mode permitido p/ features/candidatos/sets sem outcome · **regime/swept-runner/substrate#4/8ATR = contexto declarado pela FONTE (campo/coluna), nunca regra visual automática do plotter**.

## 8. Color modes (declarar SEMPRE no report)

- **outcome-mode** (default p/ trades resolvidos): verde `#1a8917` winner (`close_R>0`) · vermelho `#cc0000` loser. **Só com outcome real e confiável da fonte.**
- **direction-mode:** verde LONG · vermelho SHORT — candidatos/features/sets mistos/sem outcome, ou quando a direção é o objeto visual.
- **Proibido:** outcome-mode com exit assumido/legacy (não há outcome) · misturar modos sem separação declarada · cor no widget (cor é SÓ do label).
- Azul `#1565c0` = neutro sem-outcome (qualquer modo).

## 9. Label modes

`#<chronological_id>` (padrão; `#1`=mais antigo, estável entre replots) · `F#`/`T#` (reversões) · `#N·2u` (adds) · azul candidatos/features. **Qualquer exceção/variante = declarada no report**; R/métricas no label só a pedido explícito do Cris.

## 10. Exit policy

**fonte explícita > política estrutural documentada (SL zona/swing −0.1×ATR14, TARGET +3R) > default legacy declarado (−1.0ATR/+2.7ATR)**. Caiu no legacy → report marca **`EXIT_ASSUMED_LEGACY`** destacado, e **outcome-mode fica proibido** nesse plot (usar azul/direction-mode). Legacy NUNCA é tratado como outcome validado.

## 11. Script selection

- **Preferir scripts reconciliados** (R1): `alert-bridge/draw_xau_4h_trades.py` (helper + corpo alinhado), `plot_capit_rsi_trades.py`, `plot_t8_canonical.py`, `plot_new_only.py` (4H) · `plot_strategy_canonical.py`, `plot_chosen_canonical.py`, `plot_5atr_*.py`, `plot_candidates_canonical.py`, `plot_reversals_canonical.py` (15M).
- **NUNCA usar** scripts com banner `DO_NOT_USE_AS_CANONICAL` (legacy pré-canon, one-shots históricos) nem `plot_script.py` (DEPRECATED, bug preço absoluto).
- Exceções (`EXCEPTION_PLOT`) só com nova autorização explícita + declaração no report.
- **Script contradiz o MASTER → parar e reportar** (não corrigir por conta própria; não copiar convenção do script).
- Script novo necessário → seguir o MASTER + helper `price_to_ticks_offset`; validar com `alert-bridge/test_canonical_plotting.py` antes de tocar chart.

## 12. Execution report contract (obrigatório em todo resultado)

`symbol` · `timeframe` · `strategy/family` · `source_file` · `output_path` · `script_used` · `command` (exato) · `color_mode` · `label_mode` · `width` · `exit_policy` (marcar EXIT_ASSUMED_LEGACY quando for) · `outcome_source` · `counts` (trades plotados / shapes success / draw_list total) · `warnings` (trades pulados, campos faltantes, conflitos) · `checksum` (sha256) se houver output file.

## 13. Conflict behavior

Conflito (doc×doc, script×master, fonte ambígua, campo faltante, direção incerta, width/label/color divergente) → **PARAR. Não improvisar. Listar o conflito com fontes exatas. Pedir decisão do Cris.** Falha histórica a não repetir: 3 reincidências de plot não-canônico por recall ruim — na dúvida, reler o MASTER, nunca inventar marcador.

## 14. Do-not-do

Não limpar chart sem autorização · não usar SLIM · não samplear visual review · não alterar produção/runtime · não tocar RAW · **não misturar 4H e 15M** · não usar outcome-mode sem outcome real · não copiar script legado como canônico · não usar vertical_line/text-only como substituto de posição · não inventar overrides · não verificar por screenshot · não apagar desenhos do Cris · não trocar symbol/timeframe do chart sem confirmação.

## 15. Templates de solicitação

- **"plot canonical 4H"** → preflight §3 → script reconciliado 4H → width 20, `#id`, outcome-mode (se outcome real) → report §12.
- **"plot canonical 15M"** → preflight §3 → script reconciliado 15M → width 10, `#id`, outcome-mode (se outcome real) → report §12.
- **"plot candidates/features direction-mode"** → preflight §3 → direction-mode declarado, azul p/ sem-outcome, SL estrutural/target +3R se sem exit → report §12.
- **"visual review full population"** → confirmar população completa da fonte (sem sampling) → plot canônico do TF → report §12 com counts totais + confirmação full-population.

## 16. Approval / status

- Criado 2026-07-02, **após** PLOTTING_CANON_MASTER_APPROVED + reconciliação R1 (`d645b17`) e R2 (`4270180`) aprovadas.
- Status: **PLOTTING_CANON_AGENT_READY_PENDING_USER_APPROVAL** — vira READY/APPROVED quando o Cris aprovar este skill.
- Escopo desta criação: doc/workflow-only — nenhum plot gerado, nenhum chart/script/produção tocado.

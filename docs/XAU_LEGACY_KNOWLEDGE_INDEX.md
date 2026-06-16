# XAU Legacy Knowledge Index (repo-side, 2026-06-16)

Índice **mínimo** que blinda no repo o essencial das estratégias XAU legacy antes de arquivar/desconectar legacy.
Captura rica completa: memory `~/.claude/.../memory/` (27 files) + `catalog.json` + `LEGACY_KNOWLEDGE_REGISTER.md` + `candidates/` + safety pack `~/Desktop/TRADING/L2_REBOOT_SAFETY_PACK_2026-06-09`. Este doc é o **ponteiro + resumo**, não substitui as fontes.

Destinos: `KEEP_REFERENCE` · `KEEP_FOR_REVALIDATION` · `ARCHIVE_AFTER_CAPTURE` · `DO_NOT_TOUCH_SOURCE_OF_TRUTH`.

| Estratégia/Família | Status | Hipótese central | Gates/conceitos | Razão aprov./rej./pausa | Lição reaproveitável | Reavaliar? | Destino |
|---|---|---|---|---|---|---|---|
| **L1 EMA21 CONTINUATION** (nova) | **OPERACIONAL** | continuação de alta XAU 4H em tendência (EMA21/SMA50, regime BULL D-1) | EMA21>SMA50 + slopes + BOS + OB zone + body≥0.35 + F5 vol≤1.0; RSI exhaustion gate | aprovada (human-discretionary) | RSI-only gate; vol leg morto sob F5 | — | **KEEP_OPERATIONAL** |
| **XAU 4H continuation (antiga)** | superseded | continuação 4H pré-rebuild | gates antigos (não documentados fielmente) | substituída pela L1 nova | reconstrução exige stop/trigger humano (config doc era auto-inconsistente) | não | KEEP_REFERENCE |
| **DEMAND_BREAKOUT** | REJECTED | breakout de zona de demanda data-driven | OB demand + breakout | rejeitado em review visual: comprava em zonas que agiam como venda; data-only insuficiente | hipótese deve nascer de auction logic, dado só valida | não | **ARCHIVE_AFTER_CAPTURE** |
| **REVERSAL_CAPITULATION** | REJECTED | reversão em capitulação (NAS+RSI1D<50+ATR>1.3) | NAS bottom + RSI + ATR expandindo | rejeitado: PF 0.47 na revalidação canônica RAW | slim inflava; validar sempre em RAW | não | **ARCHIVE_AFTER_CAPTURE** |
| **SWEEP / reversal discretionary** | RESEARCH/WATCH | sweep de liquidez + reentrada (BASE+SWEEP) | NAS + sweep/reentry + CHoCH/BOS | discricionária, n pequeno | sweep+reentry é gatilho objetivo válido | parcial | KEEP_REFERENCE |
| **BB confluence (INTRADAY)** | RESEARCH | confluência Bollinger intraday | BB + confluência | forward test parado ~2026-04-30 | NOT_DEPLOYED | parcial | KEEP_FOR_REVALIDATION |
| **L2 / BPT / Reason Atlas** | RESEARCH_CORE | leitura macro de leg + zona REVIEW irredutível no miolo BULL_EXPANSION | macro-location D1, at_d1_demand, NAS ordering, acceptance | miolo irredutível no entry; separação é post-entry (lookahead) | o que separa good/bad é gestão/exit, não filtro de entrada | sim (eixos ortogonais c/ coleta) | KEEP_REFERENCE (safety pack) |
| **regime_B v1/v2/v3** | MORTO | regime D-1 cascade/stage/breaks | combined_score = Σbreaks + vol_score; MACRO_BROKEN overlay | v1 B irrecuperável (script perdido); substituído por regime_L1_v4 | scorer reproduzível 100% dado os breaks; breaks/vol_score não reconstruíveis | não | **ARCHIVE (feito)** `dead_regime_B_v3/` |
| **Caminho A (A1/A1'/BALANCE)** | INVALIDADO | reversão/bottom-catcher natural bull | bsw∈(0,30] + bubble_buy + exit stair | A1' SUPERTREND look-ahead (88%→46% pós-audit) | look-ahead via close diário do mesmo dia; SHIFT1 obrigatório | não | KEEP_REFERENCE (caso-escola) |
| **Caminho B v1.5/v1.6** | OFICIAL (memory) | bottom catcher 4H convergente | 4 agents + anti_demand + rsi≤30 + V_stair + filtro composto | aprovado em memory (WL ±20% ok); não migrado ao novo core | filtro composto OB/bubble/NAS; V_stair climax conditional | sim (migração futura) | KEEP_FOR_REVALIDATION |
| **XAU 1H DEMAND_RECLAIM** | PAUSADO | reentrada demand reclaim 1H (L4+Secondary) | cluster+CHoCH+maturity + drop_20_atr≤4.64 + BE2R | hipótese oficial v1.1; sistema em pausa mantida | drop_20 preserva winners removendo losers | sim | KEEP_FOR_REVALIDATION |
| **XAU 15M/30M (pending)** | POTENCIAL | intraday agressivo contextualizado por 1H/4H | (a definir) | só stubs + datasets replay coletados | datasets multi-TF prontos no HD externo | sim | KEEP_FOR_REVALIDATION |

## Weekly review audit (read-only)
- **LaunchAgent `weekly-review`:** CARREGADO (`RunAtLoad=false`, cron; **last exit code 1** = última execução falhou — provável: lê `strategy_eval_log`/`strategy_signals` do monitor **dormant**, agora stale/vazio). `archive-weekly` também carregado (manutenção de retenção).
- **Executa:** `weekly_review.py --mode cron` → digest semanal compacto por frente (contagem `matches_by_strategy`).
- **Envia Telegram?** **SIM** — `send_telegram(msg)` em cron, **mesmo canal** das notificações L1.
- **Relatório ou sinal de trade?** **Relatório de manutenção** (stats), **NÃO** sinal de trade (sem SETUP_VALIDO/buy/entry/order).
- **Interfere na nova L1?** Não operacionalmente (sem ordem, sem falso sinal). Só **cosmético**: um digest semanal chegaria no mesmo chat. Lê logs legacy stale (monitor dormant) → tende a vazio/erro.
- **Veredito:** **DECOMMISSION_CANDIDATE** (não HARD_STOP). É ruído legacy ligado ao monitor dormant; pode ser feito bootout quando conveniente. Sem risco de trade. Decisão do usuário.

## Conclusão
Preservação repo-side agora **SUFICIENTE** para arquivar legacy morto sem perder conhecimento. **Source-of-truth (RAW/manifests/event store/journal novo) = DO_NOT_TOUCH.** Próximo: arquivar só o que está **morto, duplicado e sem uso operacional** — nunca research/RAW.

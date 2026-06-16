# Valor estratégico dos live signals vs RAW (2026-06-16, read-only)

## 1. Executive summary
Live signals **NÃO são redundantes** com RAW: medem uma verdade **diferente e complementar**. RAW valida **edge** (funciona historicamente); o event store live valida **operação** (o sinal realmente dispara, no tempo certo, completo, entregável, sem repaint). O **gap entre os dois = "edge histórico vs operação real"** — e o event store É o dataset para medir esse gap. Conclusão honesta: **não romantizar legacy, mas não apagar valor real**: o **event store (`indicator_signals.jsonl`) é forward data valioso e vivo** (16k sinais, ~700/dia, multi-ativo) → preservar; o **weekly_review atual é ruído** → decommissionar; o **conceito do D2R (forward outcome) é um gap real** → redesenhar.

## 2. RAW vs live signals — diferença filosófica e prática
- **RAW** = verdade **histórica** para backtest: close-only, sem repaint, história completa, reprodutível. **Suficiente para validar EDGE.**
- **Live signals/event store** = verdade **operacional forward**: o que os indicadores **de fato disparam em tempo real**, com timestamp/preço/versão/hash. **Necessário para validar OPERAÇÃO.**
- São camadas ortogonais: edge ≠ operação. Ter RAW **não** torna live redundante.

## 3. O que live signals validam que backtest NÃO valida
- **Timing/latência:** o sinal chega quando o backtest assume? (fechamento vs atraso)
- **Repaint real:** o sinal histórico "perfeito" persiste ao vivo ou repinta?
- **Alert fidelity / disponibilidade de campos:** o payload chega completo (todos os campos que a estratégia usa)?
- **Densidade/ruído real:** quantos sinais/dia de fato, falsos positivos, clustering.
- **Dedup/entrega:** duplicatas, sinais perdidos, entregabilidade Telegram.
- **Gap edge↔operação:** comparar "candidato no RAW backtest" vs "sinal que realmente chegou" para a mesma barra.
→ **Só o forward/event store responde isso.**

## 4. O que live signals NÃO validam
- **Edge/expectância:** amostra forward curta, sem negativos limpos, indicadores mudam de versão → **não** prova edge. Edge = RAW.
- **Risco de cherry-picking / survivorship / logging incompleto:** o event store loga o que disparou, não o que **deveria** ter disparado.
- Conclusão: live = **geração de hipótese + evidência operacional**, nunca validação de edge isolada.

## 5. Valor dos alarmes antigos / `indicator_signals.jsonl`
- **VIVO e source-of-truth do comportamento live dos indicadores** (16.173 sinais, ETH/XAU/XAG/EUR/US500, ~700/dia, schema com ts_signal/indicator/price/hash/payload). Receiver PID 841 ainda escreve.
- **Valor:** (a) auditoria de alert delivery, (b) **dataset forward** multi-ativo, (c) comparação backtest↔live, (d) monitoramento de indicador, (e) controle de repaint/latência, (f) **geração de hipótese**.
- **Path perigoso (recheck→SETUP_VALIDO→Telegram de trade):** já NEUTRALIZADO. **Sem risco ativo.**
- **Preservar 30–90+ dias** como coleta forward — é grátis (já roda) e valioso. **Não deletar.**

## 6. Valor do D2R (correção da análise anterior)
- D2R era o **bridge sinal-live → R realizado** (forward outcome). Isso é uma **função útil real**, não só legacy morto.
- O novo `outcome.py` cobre **R post-hoc dos candidatos L1 sobre RAW** — **NÃO** cobre o **forward outcome do event store** (live signal → R realizado). **→ gap real.**
- **Recomendação:** o **conceito** vira uma **camada nova de forward outcome** (join `indicator_signals.jsonl` → R medido sobre RAW/forward), que permite comparar **backtest-R vs forward-R**. Código D2R legacy = **ARCHIVE_AFTER_CAPTURE**; conceito = **REDESIGN_FOR_NEW_CORE** (não morre).

## 7. Valor do weekly_review
- Conceito útil (digest periódico), implementação morta (lê logs do monitor dormant, falha exit 1, polui canal de sinal).
- **Deve virar:** **L1 weekly health digest** + **signal quality digest** (densidade/repaint live vs backtest) + **forward validation digest** + **journal/outcome completeness**. Em **canal de manutenção separado**.

## 8. Riscos de manter
- weekly_review: ruído Telegram no canal de sinal + digest falho. Baixo risco, alta confusão.
- D2R/enrich dormant: peso morto inofensivo.

## 9. Riscos de desligar cedo demais
- **Desligar receiver/event store = ALTO:** perde a coleta forward viva (irreversível em termos de dados não-coletados).
- Apagar D2R antes de capturar o conceito de forward-outcome = perder a especificação de uma camada útil.
- Apagar `indicator_signals.jsonl` = destruir o dataset forward.

## 10. Recomendação final
- **Sinais live ajudam mesmo tendo RAW? PARCIAL → SIM, para a camada OPERACIONAL** (não para edge). São complementares, não redundantes.
- **Manter coleta forward viva** (receiver + event store). **Decommissionar só o weekly_review** (ruído). **Redesenhar** o conceito de forward-outcome (ex-D2R) e o health/digest (ex-weekly).

## 11. Preservar 30–90 dias (forward data)
`indicator_signals.jsonl` + receiver vivo; `outcomes_current.jsonl` (Signal Outcome Lab seed); `.runtime_state/` da L1 (runs/dedup/log). **Não deletar nesse horizonte.**

## 12. Redesenhar para o novo core
- **Forward outcome layer** (live signal → R realizado; compara backtest-R vs forward-R) — ex-D2R, limpo.
- **L1 health/digest** (regime freshness, scheduler runs/exit, dedup anomalies, chart-restore failures, journal completeness) — ex-weekly_review, canal separado.
- **Telegram:** **2 canais** — `signal` (só candidate notifications) e `maintenance` (health/digest). Nunca misturar.

## 13. Pode ser decommissionado agora
- **`weekly-review` LaunchAgent** (bootout + arquivar plist) — único ruído ativo.
- **NÃO agora:** D2R/enrich (arquivar depois, conceito capturado), receiver/event store (HARD_STOP).

## 14. Classificação final
| Item | Classe |
|---|---|
| RAW/backtest | **HARD_STOP_DO_NOT_TOUCH / CORE_KEEP** (verdade de edge) |
| live signal event store (`indicator_signals.jsonl` + receiver) | **KEEP_AS_FORWARD_DATA / HARD_STOP** (verdade operacional viva) |
| old alarms (recheck→Telegram trade) | KEEP_REFERENCE (neutralizado) |
| D2R | **ARCHIVE_AFTER_CAPTURE (código) + REDESIGN_FOR_NEW_CORE (conceito forward-outcome)** |
| weekly_review | **DECOMMISSION_NOW + REDESIGN_FOR_NEW_CORE** |
| recheck:931 | KEEP_REFERENCE (neutralizado) |
| monitor legacy | KEEP_REFERENCE (dormant) |
| new L1 scheduler/runtime | **CORE_KEEP** |
| future outcome/health layer | REDESIGN_FOR_NEW_CORE (a construir) |

## 15. Próximo bloco recomendado
Mínimo e reversível: **decommission do `weekly-review`** (bootout + arquivar plist). Mantém receiver/event store/RAW intocados. **Depois** (frentes separadas, com autorização): (a) desenhar o **forward outcome layer** sobre o event store, (b) o **L1 health digest** em canal de manutenção. Não apagar D2R/enrich ainda — arquivar quando o conceito forward-outcome estiver especificado.

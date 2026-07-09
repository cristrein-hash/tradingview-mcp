# L1 NAS-LIVE CAUSALITY GATE — Devil's Advocate

**2026-07-09.** DA real (Agent tool, general-purpose) com leituras MCP read-only ao vivo (CDP 9222, chart XAU 4H). Verdict: **BLOCKED (NO-GO) confirmado; root cause corrigido.**

## Verificações (per-ponto)
1. **Filtro/handle correto:** OK. Filtros "NAS"/""/"TOP BOTTOM"/"DETECTOR" → exatamente 1 estudo `NAS TOP BOTTOM DETECTOR` (entity `pkqE7L`), todos `n_bars=0`. Não há 2º estudo NAS nem plot-title escondido. RSI controlo `n_bars=8` limpo.
2. **Transiente vs fundamental:** CONCERN → **root cause do meu verdict estava parcialmente errado.** Re-leu após 3s = idêntico `n_bars=0` (`data().lastIndex()=null` = série vazia). MAS o ledger prova que a MESMA tool leu NAS por-barra em Junho (27 valores), `pineFeatures.plot=1`, e o estudo está `visible:false` (partilha `n_bars=0` com todos os ocultos). **Reframe: "não legível enquanto oculto/não-computado", NÃO "labels-only, incapaz de plot series".**
3. **Controlo RSI comparável:** OK — prova que o mecanismo lê quando existe série numérica; não prova que NAS seja permanentemente ilegível, só no estado oculto atual.
4. **Entrada 2017 no ledger:** FLAW confirmado — `bar_time 2017-02-27` persistido em 2026-06-18 = misalignment real. Guard `persist_after_bar_close_ok` **cego** a bar_times antigos.
5. **Fail-closed:** OK, robusto — match por timestamp exato + `blocked_bar_not_closed`; poluição só BLOQUEIA, nunca dispara errado.
6. **Fontes live alternativas:** OK — nenhuma dá o número agora: `data_get_study_values` (NAS ausente), `data_get_indicator` (só inputs), `pine_labels/lines/boxes` (0), `pine_shapes` (só 2 shapes LONG/SHORT, sem distância). Única fonte historicamente-provada = `at_bar`/data-window **quando o estudo está ativo**.
7. **BLOCKED vs PARTIAL vs FAIL:** CONCERN → **BLOCKED-BY-STATE / RECUPERÁVEL (≈PARTIAL)** como GO/NO-GO = NO-GO (correto), mas não impossibilidade fundamental.

## Correção adicional do DA (que eu tinha omitido)
**`nas_from_history` = CÓDIGO MORTO (zero call-sites).** O runtime mantém o ledger append-only mas **nunca o lê** para o sinal — depende 100% do `at_bar` devolver i-1 na janela viva. O "path ledger" que eu creditei como provado está **construído mas não wired.**

## Veredito final
**A conclusão operacional MANTÉM-SE e não foi flipada: NENHUMA leitura live devolve NAS(i-1) agora (estudo oculto/não-computado); runtime fail-closes; produção NOT_AUTHORIZED.** Correções honradas no relatório:
1. Root cause = **estado do estudo (oculto)**, não limitação fundamental de plot.
2. Fix mais barato = tornar o estudo visível/computado e re-verificar **antes** de mexer no Pine.
3. **Wire o ledger** (dead code) + guard contra bar_time distante de persisted_at.

Tudo recuperável **sem recomputação de NAS** (proibida), mas exige mudanças de chart/runtime/indicador → **autorização explícita do Cris**. Nenhum bug que inverta o NO-GO; nenhuma fonte live funcional encontrada.

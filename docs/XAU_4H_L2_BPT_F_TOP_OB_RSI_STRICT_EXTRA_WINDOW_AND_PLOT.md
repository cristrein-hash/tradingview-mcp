# XAU 4H L2/BPT — F_TOP_OB_RSI_strict: Extra Window + Plot

**Status:** `RESEARCH · FROZEN_FILTER · PLOT_PENDING_AUTH · NOT_PROMOTED` · **Data:** 2026-06-18
Valida o filtro congelado em +1 janela (2021-2022) + lista completa dos filtrados + prepara plot para review humano. SL/exit inalterados. 11º DA. Plot NÃO executado (segurança de produção). Nada promovido.

---

## 1. Executive summary

Filtro **congelado** `F_TOP_OB_RSI_strict = legpos90≥85 AND RSI≥70` (sem alterar threshold/condição). **A janela extra ENFRAQUECEU o caso, não fortaleceu:** 2021-2022 filtra só **2 trades** (n=2, não-informativo, período negativo da estratégia). O breakdown anual revelou evidência NOVA negativa: o filtro **corta winners net-positivos em anos de bull (2020 +1.7R, 2025 +2.9R)** — é **regime-blind, não top-específico**. Dos 30 filtrados, mapeiam a 3 curados: **E23 (top confirmado ✓), E14 (review ambíguo), E22 (VALID_SETUP_BAD_SL = false-positive — winner que o problema é SL, não entrada)**. 0 BOM, 0 must-preserve cortados. **Veredito final: HUMAN_REVIEW_FLAG only, NUNCA auto-block** — directionally OK em blow-off (E23) mas corta dips de continuação em bull + 1 winner validado. **Plot dos 30 filtrados: EXECUTADO (30/30) em formato CANÔNICO (long_position + label), autorizado pelo Cris** — xau-l1-cycle pausado → plotado → restaurado; receiver/cloudflared/L1 intactos; sem server.js órfão.

## 2. Frozen filter definition

`F_TOP_OB_RSI_strict = legpos90 >= 85 AND RSI >= 70`. NÃO alterado. legpos90 = posição do close na faixa de 90 dias; RSI = Wilder RSI14 frozen (causal). Baseline: SL NORMAL_BPT/STRUCT_PURE + exit partial50@2R+6R + custo 0.10R + base 276 episódios.

## 3. Extra window result (`..._extra_window.csv`)

**Janela extra declarada: 2021-2022** (calibração=2020, OOS prévio=2023-26; 2021-2022 nunca foi foco).

| window | n | filt | filt_netR | kept avgR | kept sumR | DD | BOMcut | mustcut |
|---|---|---|---|---|---|---|---|---|
| **2021-2022** | 74 | **2** | −1.2 | −0.13→−0.117 | −9.6→−8.4 | 18.7→17.6 | 0 | 0 |

Anual: 2020 filt3 **netR +1.7 (corta positivo)** · 2021 −1.1 · 2022 −0.1 · 2023 −3.0 · 2024 −1.2 · **2025 filt9 netR +2.9 (corta winners, kept sumR 21.6→18.6)** · 2026 −0.2.
**Leitura honesta:** 2021-2022 é não-informativo (n=2 num período já negativo). O anual mostra **winner-cutting regime-dependente** (bull years 2020/2025).

## 4. Full filtered-trade list summary (`..._filtered_trades_full.csv`)

30 trades filtrados (2020:3, 2021:1, 2022:1, 2023:6, 2024:8, 2025:9, 2026:2). **0 BOM, 0 must-preserve.** Mapeiam a curados: **E14, E22, E23**. top_likelihood heurístico: 21 HIGH / 8 MEDIUM / 1 LOW — **circular** (usa as mesmas legpos/RSI que definem o filtro; descartado como validação pelo DA).

## 5. Plot protocol (EXECUTADO — 30/30 canônico)

**Autorizado pelo Cris: pausar xau-l1-cycle → plotar → restaurar.** Sequência executada:
1. `launchctl bootout` do `com.cristrein.xau-l1-cycle` (pausado, verificado); receiver/cloudflared/L1 NÃO tocados.
2. `chart_get_state`: PEPPERSTONE:XAUUSD confirmado; resolution 1D→ajustado para **240 (4H)**; indicadores do Cris preservados.
3. **Plotagem CANÔNICA** (long_position + label, via cliente MCP do projeto `draw_xau_4h_trades.py`): cada trade = `long_position` (entry=close, stopLevel/profitLevel em TICKS via mintick 0.01: stop estrutural, target +2R) + label `F_STRICT #<eid> · RSI<v> · LP<lp>` (SEM R, SEM outcome). **30/30 plotados.**
4. `launchctl bootstrap` recarregou o xau-l1-cycle ✓; sem server.js órfão (só o do harness).

🚨 **Correção registrada:** uma primeira tentativa usou vertical_line+text (NÃO-canônico). Cris reiterou enfático: **neste projeto só plotagem CANÔNICA (long_position+label), NUNCA lines/text-only.** Os 9 desenhos errados foram removidos (só meus IDs) ANTES do plot canônico. Manifest (`..._plot_manifest.csv`) = 30 entity_ids reais, plotted=yes.

## 6. Visual review summary (`..._visual_review.csv`)

Template data-based gerado (RSI/legpos/near-high derivados causalmente). **Campos visuais (blowoff_visual, top_sweep_visual) = AWAITING_USER** — não fabricados (regra de memória: não inventar leitura visual; Cris vê a TV). data_assessment pré-classifica: E23=TRUE_TOP, E22=LIKELY_FALSE_POSITIVE, E14=UNCLEAR, demais=UNLABELED por likelihood.

## 7. Cases that look like true tops

**E23** (legpos94/RSI77, blow-off pré-ATH 2020-08-07) = top confirmado. Os 21 HIGH-likelihood são candidatos a true-top MAS a confirmação é visual (pendente) — a heurística é circular, não prova.

## 8. Cases that look like false positives

**E22** (VALID_SETUP_BAD_SL, "WINNER OK, SL a corrigir" — Cris) — filtro corta um winner cujo problema é SL, não entrada = **false-positive real**. **Winners de continuação em bull** (2020 +1.7R, 2025 +2.9R cortados) = false-positives regime-dependentes. E14 = ambíguo.

## 9. Recommendation

**HUMAN_REVIEW_FLAG (review-only).** NÃO auto-block, NÃO prereg candidate como gate standalone. Razões: (a) regime-blind (corta dips de continuação em bull); (b) false-positive E22 (winner SL-fix); (c) janela extra não-informativa (n=2); (d) avgR-gain parcialmente artefato de denominador (bloco anterior); (e) circular na heurística top. **Se usar: como flag de aviso `overbought-top` no review humano, PAREADO com contexto de regime** para não vetar pullbacks de bull. E22-tipo = tratar como problema de SL, não entrada.

## 10. DA appendix

11º DA. Verdict: "Extra window WEAKENS the prior SMALL_BUT_STABLE read — 2021-2022 n=2 não adiciona suporte; anual revela winner-cutting em bull (2020/2025) + E22 false-positive; top_likelihood circular. Filtro é heurística regime-blind de baixo impacto — review prompt humano, nunca auto-block; parear com regime." Checklist: filtro = exatamente legpos90≥85 & RSI≥70 (não alterado) ✓ · nenhum threshold/condição alterado ✓ · janela extra NÃO usada p/ tuning ✓ · todos 30 filtrados listados ✓ · plot NÃO executado (pending auth, justificado) ✓ · plot sem outcome/R no label (protocolo) ✓ · visual review não-fabricado (AWAITING_USER) ✓ · produção intacta (read-only preflight) ✓ · SL/exit inalterados ✓ · sem SLIM ✓ · não promovido ✓.

---

*Outputs: `results/l2_bpt_f_top_ob_rsi_strict_{extra_window,filtered_trades_full,plot_manifest,visual_review}.csv`. Script: `l2_bpt_fstrict_window.py`. Plot PENDENTE de autorização (produção). SL/exit inalterados, nada promovido.*

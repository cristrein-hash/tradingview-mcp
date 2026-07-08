# L2/BPT XAU 4H · Trend-Exit / Regime-Flip — Official Approval

**Cris 2026-07-08.** Decisão oficial. Este doc é o **status canónico** da estratégia (supersede o status do checkpoint técnico `L2_BPT_TREND_EXIT_EXPLORATORY_CHECKPOINT_20260708.md`, que permanece como registo técnico/DA).

## Decisão do Cris
**Aprovo a estratégia L2/BPT com o novo exit trend-exit / regime-flip como OFICIAL APROVADA**, pendente apenas de entrar em produção mais adiante, quando eu autorizar.

## Status
`USER_APPROVED_OFFICIAL_NOT_PRODUCTION` (= `OFFICIAL_APPROVED_PENDING_PRODUCTION_AUTHORIZATION`).
Operacional: `NOT_PRODUCTION` · `NO_RUNTIME` · `NO_TELEGRAM` · `NO_AUTO_TRADING` · `NO_STRATEGY_RULES_WIRING` · `NO_MONITOR` · `NO_BROKER` · `PRODUCTION_PENDING_EXPLICIT_CRIS_AUTHORIZATION`.

## O que está aprovado
- Estratégia XAU 4H LONG **L2/BPT** (entrada: reversão estrutural em zona de demanda, seleção por regime — o esqueleto aprovado dos 17) **com o novo exit de gestão-de-tendência**.
- **Exit causal:** segurar enquanto o regime/tendência persiste; sair na virada/invalidação estrutural (regra testada: hold até o regime virar BEAR, com SL estrutural stop-first, cap de horizonte).
- **DA confirmou causalidade: NÃO é look-ahead** (FSM reimplementado estritamente-online = byte-idêntico na era de trading).

## Explicação simples da lógica
Em **macro-regime BULL / tendência ativa**, o exit **segue a estrutura/regime** em vez de cortar num horizonte fixo (as 120 barras do let-run cortavam o bull cedo demais). Enquanto a tendência aguenta, a posição corre; sai quando o regime vira / a estrutura invalida. O nível de saída é conhecido **barra-a-barra** — causal, sem prever o futuro.

## Números principais
| exit | FULL-base (245) | SELECT-17 |
|---|---|---|
| let-run HZ120 (anterior) | +52.5R | +36.2R |
| hold 500 (referência) | +257.6R | +90.3R |
| **trend-exit / regime-flip (aprovado)** | ~**+385.7R a +399.2R** (conforme warmup) | **+105.3R** (retDD 26×, streak 3, DD −4.1) |
- **#6:** vira winner **mecânico +1.15R**. O alvo discricionário **+3R** do Cris fica registado como **leitura humana**, não regra mecânica.

## DA verdict (aceito)
- **Causalidade PASS** (não look-ahead; online-causal SELECT-17 +105.3R idêntico, FULL +385.7R).
- **Caveat aceito:** ~78% do ganho nos 17 vem de **horizonte/exposição** (120→500 barras), não só inteligência de regime; o detector adiciona ~+15R sobre o hold-500, sobre 2 topos macro in-sample.
- **Caveat aceito:** full-base tem **DD/streak hostil (DD ~−72 / streak 22)**; produção futura exige **camada de execução/risco** (gestão de DD, modelo de gap nos stops largos de 2025).

## Não produção
`NOT_PRODUCTION`. Sem runtime, Telegram, monitor, broker ou wiring em strategy_rules. **Produção futura SÓ com autorização explícita do Cris.**

## Próximos passos possíveis (NÃO iniciados)
- Camada de execução/risco (controlo de DD/streak, modelo de gap) antes de produção.
- Prereg formal do exit no full-base + forward.
- Decidir mecanização (ou não) do alvo discricionário +3R do #6.
- Extensão daily/HTF para forward/live.

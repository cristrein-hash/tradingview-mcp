# PREREG — BEAR-ONLY SKIP · JANELA VIRGEM 2024-25 · ONE-SHOT (2026-07-09)

> Decisão do Cris: NÃO rodar a Fase 3A na base queimada ("os números já são conhecidos"). Testar
> S2a+S3 em janela virgem, UMA vez, sem tocar thresholds. NÃO é backtest de estratégia — é teste
> virgem de SKIP. Sem entry · sem produção/Telegram/broker/runtime/chart · sem BULL/RANGE · sem
> filtros novos · sem outcome como seletor · sem ajuste pós-resultado (qualquer ajuste = novo prereg).

## 1. Declaração de virgindade (SEM maquiagem)
Janela: **2024-07-01 → 2025-04-08 UTC** (início pós-warmup macro ~40 dias + 400 barras de stream;
fim ANTES da primeira marca GT 2025-04-09).
**Status honesto: `NOT_FULLY_VIRGIN_AT_PRICE_LEVEL / VIRGIN_AT_OUTCOME_AND_SELECTION_LEVEL`** —
as máquinas (F0/A2/estágio-1 do F1.5) PROCESSARAM os preços desta janela (bounds de plausibilidade
GT-free foram medidos nela), MAS: zero outcomes computados nela até hoje · zero GT (marcas começam
2025-04-09) · zero dossiês (todos ≥2025-04) · zero tuning com alvo nesta janela (S3 K/ndesc
calibrados só na base 2025-08+; S2a = filtro externo). Nenhum humano/LLM leu episódios daqui.

## 2. Universo (congelado ANTES de outcomes — ordem obrigatória)
Gerador = **definição FROZEN da Opção B live-fireable** (a mesma da base n=166), re-implementada
RAW-only sobre F0 (primitives banidos e inexistentes em 2024-25): walk online zz(6·ATR15) sem
confirmação futura · candidato = running low da down-leg · janela de reclaim 24 barras · trigger =
close>EMA21(15M) & close>prev · só MARKUP-live (higher-low vs último L confirmado) · 1 entry por
candidato · SL V1 = low−0,1·ATR[cand] · risk >0,05·ATR. ATR=SMA14-TR e EMA21 recomputados do F0
(fonte primitives da lib original indisponível — VARIANTE DECLARADA).
**Check de consistência obrigatório:** o reimplementado corre também na janela 2025-08→2026-07 e
compara com os 166 conhecidos (taxa de match por timestamp reportada; <80% match = STOP e investigar
antes do virgem).
**Sequência dura:** (1) gerar candidatos + macro + flags S2a/S3 → (2) CONGELAR
`results/virgin_bear_universe_frozen.json` (IDs+flags, SEM outcomes) → (3) só depois computar
outcomes (3R first-touch SL-first, SL prioridade na mesma barra, horizonte 1440 barras, TIME
excluído dos resolvidos).
**Universo do teste = candidatos com macro v5 == BEAR no entry.** BULL/RANGE: contados e EXCLUÍDOS.
Se BEAR n<15: reportar `UNDERPOWERED` junto ao verdict (sem esticar a janela — isso seria tuning).

## 3. Eixos congelados (ZERO alteração)
- **S2a**: px_vs_ema1d_atr ≥ 0 (EMA21 do 1D price-agg interna, dia FECHADO D-1; variante price-agg
  declarada — o nativo não existe nesta janela).
- **S3**: `S3_n_desc_peaks ≥ 2` do código PINADO sha16 `b749b7a62386fd7c` (degraus descendentes;
  bounce K=1,5·ATR desde o high-384). Sem sensibilidade, sem re-tuning.

## 4. Run ÚNICO: A. S2a only · B. S3 only · C. OR · D. AND — nada mais.

## 5. Métricas
total candidates · L/W do universo BEAR virgem · por composite: losers skipped / winners skipped /
losers remaining / winners preserved / skip precision / false-skip rate · overlap · S2a-only ·
S3-only · contagem por semana ISO (cluster) · **null estratificado + cluster-aware**: permutação de
outcomes POR BLOCO semana-ISO dentro do BEAR virgem, 2000 trials, seed 20260709, estatística =
losers cortados por C e por B (P = fração ≥ obs).

## 6. Verdicts permitidos (e só estes)
`PASS_SKIP_REPLICATES_IN_VIRGIN_WINDOW` · `PARTIAL_S2A_ONLY_REPLICATES` ·
`PARTIAL_S3_WEAK_OR_OVERFIT` · `FAIL_SKIP_DOES_NOT_REPLICATE` · `BLOCKED_WINDOW_NOT_VIRGIN`.
Leitura (critério do Cris): PASS exige C cortar muitos losers + matar poucos winners + S3
acrescentar além do S2a + cluster-null não explodir. Se falhar: S3 encerra como calibração;
preserva-se só S2a/capitulation como filtro contextual.

## 7. DA obrigatório antes do verdict. Commit só se limpo. Todos os looks no ledger.

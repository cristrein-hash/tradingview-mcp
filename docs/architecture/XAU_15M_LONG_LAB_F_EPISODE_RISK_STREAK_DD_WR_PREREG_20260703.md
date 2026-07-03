# LAB F — EPISODE RISK / STREAK / DD / WR · PRÉ-REGISTRO (2026-07-03, ANTES de qualquer cálculo)

**Bloco:** XAU_15M_LONG_LAB_F_EPISODE_RISK_STREAK_DD_WR · research-only / prereg-first / multi-agent / LONG-only · sem produção/Telegram/runtime/chart/plot/RAW-write. Autorização integral Cris 2026-07-03 (F0→F7 sem fragmentação).

## 1. Strategy scope
XAU 15M LONG only · base #4 · N435 · detector v5 retido · **SB $0,80 obrigatório** · OFICIAL_FN (cost gate passed) · NOT production. **Adendo Cris: toda família é avaliada em DUAS baselines — BASE (market@cj) e BASE+P1 (antecipação disp-early do Lab A r2 onde disparou, senão cj) — com avaliação das diferenças entre elas.**

## 2. Problem statement
WR líquido ~46% · streak −8 · FundedNext WR/streak não-resolvidos (Lab A COMPLETE: NO_STRUCTURAL_SOLUTION_FOR_WR_STREAK) · **STREAK_ANATOMY: 97% da dor é cluster/episódio/calendário** (15 intra-episódio + 20 ≤2 semanas de 36 runs ≥3). Alvo = controlar CLUSTER RISK (camada de gestão de exposição), não otimizar entrada isolada. Reframe: não é filtro de feature; não é matar trades por hindsight.

## 3. Baseline reproduction (fail-loud, JOIN)
BASE: N435 · +291,5 bruto / +233,6 SB · WR_liq 46,0 · DD −14,2 · r/DD 16,4 · streak −8 · anos 13,6/183,4/36,6 · 73% meses+ · pior mês −5,0 · runners 53. BASE+P1: +315,5 / **+257,1** · WR_liq 46,7 · DD −13,5 · streak −8 · runners 56 (reproduzir do script do Lab A r2). Não bater → PARAR.

## 4. Source/data mapping
Trades via exec do engine real (`engine_substrate4_v5_hourcausal.py`, `cand[v5h≠BEAR]`), geometria via rmap (como Labs E/A) → trade_id=cj_t · entry_time · R bruto (let-run; close_time não materializado — exit interno ao letrun, declarado) · SB_net_R = R − 0,80/risk_usd · year/month/week(ISO)/day · regime v5h · risk_usd · runner flag (R≥3) · loser flag (NET≤0). **Episode mapping (2 níveis, causais, congelados no Lab A r2):** (i) `cluster_id` = cadeia com gap ≤96 barras entre entradas consecutivas; (ii) `chain_pos` estrita = gap ≤96b E anterior stopado E |flush−flush_prev| ≤1,0·ATR_prev. Ambos decidíveis com barras ≤ entrada. Source: primitives RAW-only, zero SLIM, source guard ativo. Se mapping se provar insuficiente para alguma família → BLOCKED_BY_EPISODE_MAPPING (não improvisar).

## 5. Famílias pré-registradas (configs CONGELADAS — ledger completo, sem best-of-N escondido; discovery NÃO pode adicionar configs a esta rodada: ideias novas → defer)
- **F1 — Episode cooldown** (após trade com NET≤0, pausar entradas do MESMO cluster por X barras; novo cluster sempre reabre): X ∈ {8, 24, 96} → 3 configs. Risco declarado: cortar fail-then-retry winners.
- **F2 — Max trades por episódio/janela**: {máx 1/cluster · máx 2/cluster · máx 2/dia-UTC} → 3 configs. Runners perdidos = métrica de 1ª classe.
- **F3 — Loss circuit breaker**: após {2, 3} NETs≤0 consecutivos dentro de janela de 48 barras, pausar até novo cluster (gap>96b) → 2 configs.
- **F4 — Exposure budget / scaled sizing** (muda TAMANHO, não seleção — nunca vender como edge): pesos {1,0/0,5/0,25} por chain_pos → 1 config (cross-ref: P5 0,5/0,3/0,2 do Lab A r2 = referência já medida). Métricas em R ponderado, risco-normalizadas + bootstrap.
- **F5 — Calendar/session risk guard** (running totals causais): {daily-stop: dia UTC acumulando ≤−3R NET → pausa até próximo dia · weekly-stop: semana ISO ≤−5R NET → pausa até próxima semana} → 2 configs. Exige null de calendar-shuffle; filtro fraco não vira regra.
- **F6 — Quality tier / defer-to-review**: PONTE report-only (tiers operacionais size/REVIEW; se exigir contexto profundo → Lab B). Sem execução numérica nesta rodada.
- **F7 — Re-entry discipline**: PONTE report-only para Lab D (formalizar quando perda permite retry), informada pela anatomy.
- **F8 — Continuation-abort (momentum time-stop)** — *adição autorizada Cris 2026-07-03, congelada ANTES da execução; derivada do kill-PASS do P2 (Lab A r2: misses do buy-stop têm base-avgR −0,56 = são losers)*. Regra causal: entrada normal da linha (cj ou P1); se `high` não atingir o nível de continuação `max(high[p..cj])+0,05·ATR_cj` (âncora herdada do P2, congelada) em **W=8 barras** pós-entrada, sair a mercado no close da 8ª barra (SL prevalece se tocado antes; se o nível romper, trade segue let-run normal). 2 modos congelados: **F8a** aborta sempre · **F8b** aborta só se close<entry na 8ª barra (não aborta trade já em lucro). Aceite explícito do Cris: perder lucro para limpar métricas prop (avaliar por PASS_RISK_CONTROL, ou PASS_STRONG se retention ≥75%). Null: abort ALEATÓRIO da mesma fração na mesma barra (500 reps) — separa a informação do "não-rompeu" de mero time-stop. Nota: é regra de EXIT (gestão de exposição), não seleção — runners intocados por construção (romperam por definição). Atenção DA: interação trail/1R do letrun nos 8 primeiros bars.
**Ledger executável: 13 configs × 2 baselines = 26 painéis** + nulls. Zero varredura além do declarado.

## 6. Nulls obrigatórios
Baseline #4 fail-loud · **random-drop de mesmo N** (500 reps) por config de seleção (F1/F2/F3/F5) · **episode-aware null** (drop aleatório restrito a trades com chain_pos≥1 ou cluster multi-trade, mesmo N, 500 reps — o null justo para famílias que só cortam em sequência) · **calendar-shuffle** para F5 (permutar rótulos dia/semana entre trades, 500 reps) · F4: bootstrap por blocos de episódio (≥1000) para streak/DD distribucional; sem claim de edge · bruto E SB-net sempre · sem best-of-N sem penalização (Bonferroni informal no ledger).

## 7. Métricas por variante
N efetivo · WR_liq · sumR bruto/NET · avgR · DD · r/DD · worst streak (obs + bootstrap q95) · pior mês · pior semana · % meses+ · anos+ (painel por-ano) · runners preservados/perdidos (base R≥3) · losers cortados · trades skipped/reduzidos · **retention % do SB-net vs baseline da mesma linha (BASE ou BASE+P1)** · FN-proxy (WR≥50 · streak≤6 · runners≥48 (BASE) / ≥51 (P1, prop.) · sumR_liq≥200 · anos+ 2024≥10 · costR med≤0,15).

## 8. Acceptance criteria (congelados)
- **PASS_STRONG**: melhora material WR/streak/DD **e retém ≥75% do SB-net** da linha.
- **PASS_RISK_CONTROL**: reduz DD/streak forte, lucro cai <75% — serve para prop-firm sizing, não é edge.
- **FAIL**: melhora cosmética, ou mata lucro/runners desproporcionalmente, ou não bate nulls.
- **REVIEW**: precisa visual/contexto (Cris).
Adicionais duros: runner-kill desproporcional = FAIL · dependência de poucos episódios (leave-episódio >15% do delta) = FAIL · null (random-drop E episode-aware) não batido (p≥0,05) = sem claim de seleção · simplicidade operacional avaliada.

## 9. Forbidden interpretations
Não aprovar produção · não mascarar perda de lucro como edge · não selecionar por hindsight · **não confundir sizing com melhora de estratégia** · não transformar calendar filter fraco em regra · não extrapolar SHORT · não mexer em gates/detector · não misturar filtros estruturais profundos (→ ponte Lab B/C).

## 10. Outputs
Script `research/xau_15m_bb_nas_leonardo/lab_f_episode_risk_streak_dd_wr_analysis.py` · results `results/lab_f_episode_risk_results.csv` + `results/lab_f_episode_risk_summary.json` (pequenos) · DA `..._DA_20260703.md` · report `..._REPORT_20260703.md` (veredito ∈ {EPISODE_RISK_ENGINE_FOUND · RISK_CONTROL_FOUND_NOT_EDGE · NO_STREAK_DD_WR_SOLUTION · BLOCKED_BY_EPISODE_MAPPING · PROMISING_NEEDS_VISUAL_OR_CONTEXT}) · commit `"Evaluate XAU 15M long episode risk streak drawdown controls"` — **sem push sem autorização**. Subagents nunca commitam; git log verificado após cada um.

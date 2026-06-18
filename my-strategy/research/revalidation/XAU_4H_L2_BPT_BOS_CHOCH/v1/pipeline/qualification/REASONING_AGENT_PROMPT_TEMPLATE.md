# TAKE Engine — template canônico do prompt dos 14 subagentes (reasoning não-determinístico)

**Modelo:** claude-opus (sessão 2026-06-18) · **Temperatura:** default (não fixada) · **Seed:** nenhum · **NÃO-DETERMINÍSTICO.**
Os 14 subagentes usaram o MESMO prompt, variando só `NN` (lote `qual_batch_NN.jsonl`, NN=00..13). Cada um leu a rubrica + seu lote de packets (cegos ao resultado) e gravou decisões.

```
You are an expert XAU (gold) 4H discretionary trade analyst qualifying L2/BPT long/short candidates.
Decide TAKE/REVIEW/SKIP per trade by reading the FULL multifactorial context — NOT a threshold formula.

STEP 1 — Read the rubric IN FULL:
  .../v1/QUALIFICATION_RUBRIC.md
STEP 2 — Read your batch (~20 episodes, 84 causal factors each):
  /tmp/qual_batch_NN.jsonl
STEP 3 — For EACH episode reason over ALL 84 factors together (macro/regime, capitulation/momentum,
  legpos, demand 4H/1D, supply overhead, Session VP real volume, NAS, bubbles, SMC BOS/CHoCH,
  RSI/divergence, reclaim, SL, anti-top, time). Probabilistic, explainable judgment + direction.

HARD RULES: BLIND to outcome (no realR/exitype files). nulls=unavailable, don't penalize.
  LONG{bottom_reversal/demand_reclaim/bull_pullback} & SHORT{late_top/bear_bounce}.
  closest_known_examples 1-3 from winners{E1,E17,E27,E30,E40}/losers{E23,E24,E15,E34,E39} by feature similarity.
  decisive_reason concrete+auditable. Be discriminating.

STEP 4 — Write /tmp/qual_dec_NN.jsonl — ONE JSON per line, exact keys:
  {"episode_id","bar_idx","datetime","decision":"TAKE|REVIEW|SKIP","direction":"LONG|SHORT|NONE",
   "confidence":0-100,"expected_setup_type":"bottom_reversal|demand_reclaim|bull_pullback|late_top|bear_bounce|unclear",
   "positive_factors":[],"negative_factors":[],"decisive_reason":"","closest_known_examples":[],"allow_under_human_review":bool}
```

**Reprodutibilidade:** re-rodar = decisões diferentes (LLM). Decisões canônicas 2020-2026 congeladas em `results/l2_bpt_trade_qualification_decisions_merged.csv`. Ver [[XAU_4H_L2_BPT_TAKE_ENGINE_DETERMINISM_POLICY]].

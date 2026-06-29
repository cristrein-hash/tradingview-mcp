# External Factors v2 — Camada de Teorias (núcleo humano credível) + Forward-Scoring

**Meta (Cris, 2026-06-29):** agregar conhecimento/teorias das fontes mais credíveis de ouro numa **análise
contextual realtime PROGRESSIVA** ao longo da produção, trazendo **ML + validação para operações reais** —
**construção sólida de longo prazo**, sem auto-ilusão.

## Princípio (o que torna a meta válida — NÃO é "agregar opinião")
Opinião perma-bull como feature de ML = lixo-entra-lixo-sai. A disciplina (5 pilares, aprovados):
1. **Teoria → afirmação FALSIFICÁVEL** com observável + horizonte. Ex.: *"fiscal dominance → ouro sobe quando
   real yield cai"* ⇒ `claim: dir(real_yield↓)→gold↑ ; horizon: 4-8 sem`.
2. **Ledger as-of** (timestamp do que foi dito) — `snapshots/theory_ledger.jsonl` (append-only, dedup).
3. **Forward-scoring** contra o realtime — a realidade dá nota (hit-rate, Brier, lead/lag). Validação forward
   GENUÍNA no tempo (≠ OOS histórico fitado, que é proibido; isto é reality-grading ao vivo = permitido).
4. **Credibility-weights que ATUALIZAM** — scoreboard aprende quais fontes preveem; perma-bulls se expõem,
   rigorosos ganham peso. O "ML" é o scoreboard que pondera por acerto REAL, não modelo que ingere opiniões.
5. **Sempre contexto, NUNCA gate** — Tier-2, não dispara trade, até a Fase 4.

## Fontes do núcleo (FREE + NÃO-DEALER; dealers descartados)
RSS keyless via `collectors/theory_sources_collect.py`:
- **GOLD_OBSERVER** (Jan Nieuwenhuijs) — CB flows/dados primários. bias=independente/gold-bull-lean.
- **LYN_ALDEN** — real-rates/fiscal, even-handed. bias=independente.
- **INGWT** (In Gold We Trust/Incrementum) — valuation/real-rates. bias=fund/perma-bull-mandato.
- **MACROVOICES** — macro institucional cross-asset. bias=independente/neutro.
- Extensível: CPM/Jeffrey Christian + Jim Bianco via YouTube RSS (resolver channel_id). DESCARTADOS: Kitco,
  BullionVault, Heraeus(refiner), Sprott, Money Metals, Schiff, Maloney (dealer/doom-marketing).

## Formato de coleta e armazenamento
- **`theory_ledger.jsonl`** (append-only, dedup por theory_id=hash(source+title)). Cada entrada:
  `{theory_id, source_id, source_name, tier, bias, focus, title, url, author, published_ts, collected_ts,
    summary, claim:null, predicted_gold_dir:null, horizon_days:null, scored:false, outcome:null, brier:null}`.
  Campos de claim/outcome preenchidos depois (claim=LLM Tier-2; outcome=scorer forward).
- **`theory_feed.json`** = recentes (≤45d) p/ grounding do monitor/fleet.
- **`theory_scoreboard.json`** (`runtime/theory_score.py`) = hit-rate/Brier/weight por fonte. Weight ativa em
  scored≥10 (até lá = 0.5 neutro, status "acumulando").

## Análise comparativa realtime (Tier-2)
`agents/fleet.py` (claude -p) recebe `theories` + o EF técnico (Tier-1 real-yields/USD/VIX, fed_path slope,
gold COT, eventos) e produz, por tema, **ACORDOS e DIVERGÊNCIAS** humano×técnico em `external_directional_notes`
(labels, sem número novo). Ex.: "humanos bullish CB-demand vs técnico headwind (USD↑ + no-cut + COT net-short)".

## Roadmap progressivo (longo prazo)
1. ✅ HOJE: coleta + ledger + scoreboard scaffold + comparação Tier-2 (fase **acumulando**).
2. Próximo: extração de **claim falsificável** por item (skill `theory-extractor`, LLM, labels-only) → preenche
   predicted_gold_dir + horizon.
3. Depois: **scorer forward** liga outcome (retorno real do ouro no horizonte via gold_collect/COMEX) → hit/Brier.
4. Maturação (semanas/meses de produção): credibility-weights por fonte estabilizam → ponderação informa o
   contexto; entra na decisão só na **Fase 4** (com sign-off, default-deny, human-in-loop).

⚠️ **Honestidade:** hoje é fase ACUMULANDO — só fica estatisticamente significativo após semanas/meses de
produção. É exatamente o ponto: a validação acontece ao longo do tempo real, não num backtest fitado.

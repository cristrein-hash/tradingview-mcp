# XAU 4H L2/BPT — Detector v2.2 Recall Audit (RESGATE)

**Data:** 2026-06-17 · **Tipo:** RECALL-ONLY audit (recuperação de detector salvo) · **NOT_VALIDATION / NOT_BACKTEST.**
**Sem PnL, sem outcome, sem target/stop, sem otimização, sem plotagem, sem produção.** RAW-only.

> Objetivo do bloco: localizar, auditar e recuperar o **Detector v2.2** (candidate generator de recall alto) salvo no safety pack, ANTES de tentar reparar o detector do census v1. Recall-gate é pré-condição a qualquer censo/backtest (`feedback_recall_gate_before_backtest`).

---

## 1. Localização e identidade do detector

| Item | Valor |
|---|---|
| **Path** | `~/Desktop/TRADING/L2_REBOOT_SAFETY_PACK_2026-06-09/L2_detector_v2_2.py` |
| **sha256** | `e919e7fa2ace0f6a181ad0875c2d4244b1088664b6d83916f4b9f339de3862be` |
| **Última modificação** | 2026-06-08 19:31 |
| **Audit script** | `L2_detector_v2_2_audit.py` · sha256 `6051cf6ac1b25c19ff1b76d67d276ff5abe90a9e9c6c6eb73a34548cd6f68942` |
| **Ground Truth** | `L2_ground_truth_v1.json` · sha256 `b1a60cbe76ec405e2febe855d5235b27e2a38c6b9092242b7dc1b4cf29f37b53` (v1, locked 2026-06-08; **17 BOM_HIGH**, 10 NAO_CONFIRMED) |
| **Read-only?** | Sim. Não toca produção, não escreve em log/chart, sem MCP/Telegram/broker. |

### Dependências / fonte de dados
- **`/tmp/raw_features_2020_2026.jsonl`** — RAW 4H (schema antigo validado: `ts_epoch, open/high/low/close/volume, rsi, bubbles_recent[{plot_id,bars_ago}], nas_recent, smc_recent`). **Cópia congelada existe no pack** (9880 barras, 2020-01→2026) → recall re-rodado **fielmente** sobre o input original.
- **`/tmp/XAU_1D_bars.jsonl`** — 1D `{time, close}`. **Regenerado do RAW 1D `.gz`** (`/Volumes/GUTS_ LACIE/.../XAUUSD_1D_...gz`, 3584 barras). Usado só para `SMA200_D` que é **dead code** (não referenciado no caminho de candidatos) → não afeta recall.
- **Fonte = RAW** (zero slim, zero CSV derivado, zero proxy). ✅ regra `feedback_never_use_slim_features` respeitada.

---

## 2. O que o detector realmente faz

**É um CANDIDATE GENERATOR (Camada 1), não uma strategy engine.** Não computa entrada/stop/target/PnL — só marca quais barras são candidatas L2.

- **Universo:** XAUUSD 4H, bar `i` de 50→N (2020→2026).
- **6 fontes de polaridade causais** (`gather_polarities_v2_2`, lookback 100 bars): `fractal_3_3`, `fractal_2_2`, `topo_duplo`, `range_top`, `swing_high_simples`, `nivel_interno`. Dedup mínimo por (level 0.1, p). Todas usam só passado (no máx. confirmação p+3).
- **Variant 1 — classic_BOS:** para cada polaridade: break permissivo (`close>level`), aceitação mínima (≥1 close acima em 6 bars), timing ≤100 bars, banda de entrada **`low ≤ level+0.8ATR`**, `close ≥ level−0.7ATR`, pullback tocou a banda, e candle tipo **A** (verde, close≥level) **ou B** (absorção: corpo vermelho + pavio inf ≥20%) **ou B_ctx** (vermelho + ≥5 bubbles SELL em 10 bars). Score favorece `fractal_3_3`/`topo_duplo`.
- **Variant 2 — contextual_no_BOS** (fallback p/ GT27-like): close dentro de 1.0ATR do level + tipo B_ctx.
- **Único veto duro Camada 1:** `falso_tipo_B_dump_direto` (anti-GT06A: corpo>0.5, pavios curtos). Demais blockers = **diagnóstico apenas** (não vetam).
- **Dedup:** 1 trigger por `entry_idx` (maior score).
- **Tolerâncias:** CHoCH/BOS implícito via break+aceitação; banda ±0.8/−0.7 ATR; timing ≤100 bars.
- **Lookahead:** ✅ ausente — polaridades só de barras passadas (confirmação ≤ p+3 < i), break/aceitação em `k<i`, decisão no bar `i`. **Sem SLIM/proxy.**

---

## 3. Recall-only vs Ground Truth (re-rodado LIVE 2026-06-17)

**Tolerância temporal:** DIRETO (mesma barra) ou NEAR ±2 barras 4H (±8h).

| Métrica | Valor |
|---|---|
| **BOM_HIGH capturados** | **17/17 (100%)** — 15 DIRETO + 2 NEAR±2 (GT01, GT20) |
| Densidade | 7763 candidatos / 7 anos = **1109/ano** |
| NAO_CONFIRMED que viraram candidato | **8/10** (0 corretamente rejeitados além do dump_direto) |
| Source dominante nos BOM | `fractal_3_3` 16/17, `swing_high_simples` 1/17 |

GT-a-GT (mode | source): GT01 NEAR-2·fractal_3_3 · GT02/03/08/09/10/15/17A/18/21/24/25 DIRETO·fractal_3_3 · GT13A/13B/23 DIRETO·fractal_3_3 · GT27 DIRETO·swing_high_simples · GT20 NEAR-2·fractal_3_3.

> O bootstrap (`L2_BOOTSTRAP_STATE.md`) registrava **16/16** sobre um GT de 16 BOM; o GT v1 atual tem **17** (GT20 adicionado) e o v2.2 também o recaptura → **17/17**. Recall confirmado, não herdado.

**Caveat crítico (DA):** recall alto **NÃO é edge**. v2.2 é recall-maximizing — captura 17/17 winners MAS também 8/10 NAOs e ~1109 candidatos/ano. É um **gerador de candidatos**; a separação winner/loser (camadas 2-3: contexto, gestão, exit) é o trabalho ainda não feito. Recall ≠ performance.

---

## 4. Comparação com Census v1 (GT-by-GT)

Census v1 (`run_l2_bpt_census_v1.py`, Williams 5/5 SHIFT5 → protected_LH → CHoCH → retest → reclaim → SL R-bounded).

| Métrica | Detector v2.2 | Census v1 |
|---|--:|--:|
| **BOM_HIGH capturados (±2 bars)** | **17/17** | **0/17** (estimativa prévia ≤2/17 — ambas nulas) |
| Fontes de polaridade | 6 permissivas | 1 (Williams 5/5 confirmado) |
| Banda de entrada | low ≤ level+0.8ATR | retest low ≤ pol+0.15ATR |
| R-bound | nenhum | ABORT se SL >1.5ATR (`R_ceiling`) |

**Breakdown da perda no census v1 (tabela completa: `results/gt_recall_diagnostic.csv`):**

| stage onde census v1 perdeu o GT | n | diferença causal provável |
|---|--:|---|
| **`no_CHoCH_episode_near`** | **13** | polaridade de `fractal_3_3` (v2.2) nunca virou protected_LH Williams 5/5 (census) → CHoCH nem se formou perto do winner |
| `episode_resolved_R_ceiling` | 2 | SL estrutural >1.5ATR → census aborta; v2.2 não tem R-bound (GT09, GT21) |
| `episode_resolved_timeout_no_retest` | 1 | retest estrito (≤0.15ATR em 24b) vs banda larga v2.2 (GT10) |
| `episode_resolved_timeout_no_reclaim` | 1 | reclaim estrito (verde, body≥0.5) vs tipo A/B/B_ctx v2.2 (GT23) |

**Conclusão causal:** o census v1 perde os winners majoritariamente **antes do CHoCH** — a fonte de polaridade Williams 5/5 SHIFT5 é estruturalmente mais restritiva que as 6 fontes do v2.2 (em especial `fractal_3_3`, que ancora 16/17). Os 4 GTs que chegaram a formar CHoCH morreram em R_ceiling/retest/reclaim estritos. Isso explica o recall ~0 e confirma: **o census v1 mediu um detector que descarta os winners-alvo → métricas net-negativas são nulas como evidência sobre o conceito** (conceito NÃO refutado).

---

## 5. Status e decisão

- **Detector v2.2 = candidate generator, NÃO strategy.** Recall 17/17 confirmado.
- **v2.2 é a base de recall-alignment** para a frente L2/BPT. **Census v1 NÃO serve de base** (recall ~0).
- **NÃO rodar backtest sobre v2.2** (sem outcome/PnL definido) · **NÃO usar como veto operacional** · **NÃO virou estratégia** sem autorização explícita.
- Próximo trabalho real = **camadas 2-3 sobre o candidate set do v2.2** (contexto/gestão/exit que separam os 17 BOM dos 8 NAOs + dos ~1109/ano), com recall-gate como pré-condição permanente.

---

## 6. Devil's Advocate (checklist do bloco)

- v2.2 localizado? ✅ path + sha256 + data acima.
- recall 16/16 ou real confirmado? ✅ **17/17 LIVE** (re-rodado sobre input congelado original; bootstrap dizia 16/16 sobre GT de 16).
- não mediu performance? ✅ recall-only; zero PnL/outcome/target/stop.
- não chamou recall de edge? ✅ §3 caveat explícito — recall ≠ edge; 8/10 NAOs também capturados.
- não usou SLIM como verdade? ✅ RAW-only; input congelado RAW + 1D do `.gz`; caveat de schema documentado.
- não criou detector novo? ✅ apenas auditou/recuperou o v2.2 salvo.
- não tocou produção? ✅ receiver/cloudflared/xau-l1-cycle/broker/pause-flag intactos; nada escrito fora de docs + `results/gt_recall_diagnostic.csv`.

**DA verdict: PASS — v2.2 recuperado e recall 17/17 confirmado fielmente; classificado como candidate generator (não edge); divergência causal vs census v1 atribuída por estágio; nenhuma performance medida; produção intacta.**

---

*Read-only. RAW-only (zero slim). Recall-only (sem PnL/OOS). Outputs: este doc + `.../v1/results/gt_recall_diagnostic.csv`. Inputs `/tmp` regeneráveis (input 4H = cópia congelada do pack; 1D do `.gz`).*

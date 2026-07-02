# L2/BPT XAU 4H LONG — RTSE CHECKPOINT DE PRESERVAÇÃO + RECONCILIAÇÃO

**Data:** 2026-07-02
**Autor:** sessão Claude Code (bootstrap + resgate de memória), autorizado por Cris
**Natureza:** checkpoint de **preservação** + **reconciliação de leitura**. NÃO é promoção, NÃO é validação para produção, NÃO houve backtest novo.
**Escopo autorizado:** preservar untracked, fixar estado, reconciliar memória × DA. Sem produção, sem implementação nova, sem push.

> ⚠️ Separação estrita: a Secção 2 descreve o que a estratégia **afirma ser**; as Secções 3–5 separam o que está **provado por ficheiro** do que estava **só em memória** e das **contradições**. "Aprovado pelo utilizador" ≠ "validado para produção".

---

## 1. Estado Git (antes / depois)

| Momento | HEAD | Working tree |
|---|---|---|
| Antes do checkpoint | `26f6bca` | 83 scripts untracked em `regime_turnstate_engine/validation/` + `alert-bridge/logs/` |
| Depois do commit de preservação | `aab8b11` | só `alert-bridge/logs/` untracked (excluído: 2,2 GB, não é pesquisa) |

- Commit de preservação: **`aab8b11`** — *"Preserve RTSE L2-BPT research state before reconciliation"* — 83 ficheiros `.py` (381,5 KB), sem secrets, sem dumps.
- **HEAD continua ~47 commits à frente de `origin/main` (`092da36`). NÃO houve push** (conforme regra).
- Classificação dos 83 preservados: **65** `phase*.py` (test/fase) · **17** `_DA_*.py` (audits) · **1** `_plot_*.py` (helper) · **0** reports/CSV/JSON/logs/lixo.

---

## 2. O que é a estratégia candidata (conforme memória declarada)

- **Módulo:** RTSE — `regime_turnstate_engine/` (não `my-strategy/`).
- **Nome:** L2/BPT XAU 4H LONG — "Engine estrutural de níveis de regime".
- **Tese:** posição do entry vs os **níveis (hi/lo) do REGIME ANTERIOR**, condicional à direção do regime corrente. Níveis conhecidos no fecho do regime anterior → causal por construção. Detector de regime = `phase10_hybrid_regime.py`.
- **Versão viva declarada — V2 ZONA-PURA:**
  - BULL → entry na zona TOP do regime anterior (terço superior).
  - BEAR → entry na zona de **capitulação profunda** = lo mínimo dos regimes significativos (≥15 barras) nos ~180 dias antes do bear (`phase48_bear_deep_zone.py`).
  - RANGE → entry no fundo do range corrente (pos < 0,34).
  - **Painel:** `N17 · WR53% · +36,2R · avgR+2,13 · DD−4,1 · streak3` — composição **BULL 6 / BEAR 1 / RANGE 10**.
- **V1** (esqueleto dist/rsi, +53,7→+63,1R): **SUPERSEDED** pela V2.
- **V3** (gatilho-de-zona, N31 +64,6R): **REJEITADA** por Cris (piorou vs V2; o excesso era beta do let-run).
- **phase50–77 (2026-07-01):** tentativas de expansão (L2-após-V2, bull-reteste, continuação, swing, afinar capitulação) — **todas refutadas** como diluição ou beta long-gold. V2-pura declarada como TETO.
- **Lead vivo residual:** `bull_break` 1-após-capitulação (`phase77`, N16 WR62% +40R streak4) — **mas ganho concentrado em 3 trades de 2023** (jackknife sem-2023 ≈ neutro).
- **R vem de:** `my-strategy/research/revalidation/XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_regua_structural.csv`, coluna `letrun_struct − 0,35` (custo). Fonte RAW-derivada (não SLIM).

---

## 3. O que está COMPROVADO por ficheiro/commit

- ✅ Detector de regime `phase10_hybrid_regime.py` — **commitado** (dependência central da tese).
- ✅ Lógica V2 BEAR-deep (`phase48_bear_deep_zone.py`) e zona-entries (`phase47_zone_entries.py`) — **existem e agora estão commitadas** em `aab8b11`; são causais por construção (usam `segs[j] j<idx`, ATR lag i−1). Isto foi lido, não re-executado.
- ✅ Cadeia DA committada que **pressiona** a tese:
  - `f53ac72` (`_DA_acceptance_structure_filter_audit.py`): RANGE filter causal mas **selection-overfit** (rank 273–391/457, null **p=1.0**), **inverte sob let-run**.
  - `d976c8d` + `26f6bca` (`_DA_phase35_causal_zones.py`): reconstrução causal das zonas + Ponto 7 = **os 6 vencedores hand-drawn são 5 BULL + 1 RANGE, 0 BEAR**; **BEAR elegível avgR = −0,593**.
  - `00bfb37` (`phase20_causal_demandlow_da.py`): decomposição causal do achado FUNDO.
- ✅ Ground-truth (`cris_regime_boxes.csv`, `raw_30m_ohlc.jsonl`) e docs canónicos RTSE V0 — commitados de sessões anteriores.

---

## 4. O que antes estava APENAS em memória / untracked (agora preservado, ainda NÃO validado)

- 🟡 Todo o painel V2 (N17 +36,2R), o esqueleto V1, os vereditos phase50–77 e o lead `bull_break` estavam **só em memória + scripts untracked**. Preservados em `aab8b11` — mas preservação ≠ validação.
- 🔴 **Não existe report formal** que fixe o book V2 (este documento é o primeiro).
- 🔴 **`04_STRATEGY_STATUS_MASTER.md` não tem entrada** para esta estratégia — a governança formal não a conhece.
- 🟡 Os scripts foram **lidos**, não re-executados neste checkpoint (Etapa 4 = read-only). Os números do painel dependem de reprodução futura sob gate manifest.

---

## 5. Contradições e tensões

| # | Fonte committada (DA) | Afirmação | Tensão com a memória |
|---|---|---|---|
| 1 | `26f6bca` / `_DA_phase35_causal_zones.py` (Ponto 7) | 6 vencedores hand-drawn = **5 BULL + 1 RANGE, 0 BEAR**; **BEAR elegível avgR = −0,593** | Contra o headline "BEAR-capitulação = coração". **Mas** a memória V2 já declara BEAR **n=1** (só 2023-10-06) e "não robustez estatística" → tensão é com o *headline*, não com o corpo. |
| 2 | `f53ac72` / `_DA_acceptance_structure_filter_audit.py` | RANGE filter **selection-overfit** (rank 273–391/457), **null p=1.0**, inverte sob let-run | Contra "RANGE = metade da V2 (10 trades)". **Mas** phase51/52 (na própria memória) já concluíram "RANGE-fundo pior que random" e "é BETA" → **consistente** com os caveats internos. |
| 3 | phase51/52 (memória, preservado) | "SEM edge de entrada estrutural. É BETA." Só bull-fallback n6 sobrevive exit-neutro | Contra o headline "+53,7/+63,1R aprovado". O lucro do let-run é **beta long-gold**, não alpha estrutural. |
| 4 | `26f6bca` (data 01/jul 16:48) vs "APROVADO 01/jul" | DA-refutação e aprovação são do **mesmo dia** | Ambíguo: não é claro pela memória se a aprovação foi **antes** ou **depois** do DA Ponto 7. Precisa decisão do Cris. |

**Leitura de síntese:** as DA committadas **não introduzem** uma refutação nova e surpreendente — elas **materializam e formalizam** os caveats que o próprio corpo da memória já continha (BEAR n=1; RANGE/let-run = beta; edge-puro ausente). A tensão real é entre o **headline otimista** da memória ("aprovado, RANGE+BEAR coração, +53,7R") e a **substância** (V2 = 17 trades, BEAR n=1, lucro dominado por beta do let-run). O checkpoint deve rebaixar o headline à substância, sem apagar a pesquisa.

---

## 6. Veredito provisório

- ❌ **NÃO é produção.** Nenhum wiring, nenhum registo em governança, nenhum Telegram/monitor/catalog.
- 🟡 **Aprovado pelo utilizador apenas como candidato / research checkpoint**, até reconciliação decidida por Cris.
- ❌ **Não validado OOS** (por design da trava do projeto — validação mora dentro dos 276 por convergência, não por held-out).
- ⚠️ **Slippage/gap/custos não modelados** (entradas/SL perto de níveis = zonas de liquidez).
- ⚠️ **2024 piora** (memória: +13,9→+6,5 sob as camadas) — a confirmar reproduzindo `phase40_debug_2024.py`.
- ⚠️ **Amostras finas:** V2 total n=17; BEAR n=1; capitulação n=11 (refino n=5); bull_break concentrado em 2023.

---

## 7. Próximo passo mínimo seguro recomendado

1. **Decisão do Cris** sobre o escopo da aprovação (A–E na Secção de Reconciliação abaixo). Sem isto, não avançar.
2. Se mantido como candidato: reproduzir o painel V2 sob **gate manifest** + source-field mapping (RAW-first), para converter os números-de-memória em números-de-ficheiro.
3. Registar a decisão em `04_STRATEGY_STATUS_MASTER.md` com o status conservador escolhido (ex.: `RESEARCH` / `ACTIVE_CANDIDATE`).
4. Só depois considerar qualquer passo operacional — **fora do escopo deste checkpoint**.

---

## RECONCILIAÇÃO — tabela de claims (Etapa 4)

| Claim | Evidência que suporta | Evidência que contradiz | Impacto | Status |
|---|---|---|---|---|
| Tese "níveis do regime anterior" é causal | `phase47/48` + `_DA_phase39_skeleton` (segs j<idx, ATR lag, RSI closed-bar); detector `phase10` committado | — (a causalidade não é o problema) | Backbone metodológico sólido | **PRESERVAR** |
| V2 zona-pura N17 +36,2R avgR+2,13 DD−4,1 streak3 | `phase47/48` (lidos, causais); memória | Números só em memória, não reproduzidos sob gate; DA mostra que o lucro tem forte componente beta (let-run) | Headline da estratégia | **PRECISA RAW AUDIT** (reproduzir sob gate manifest) |
| BULL = zona-top do regime anterior (6 trades) | `phase48` keep(BULL); Ponto 7 DA: 5 dos 6 winners hand-drawn são BULL | Pullbacks de uptrend ⇒ parte é beta long-gold (phase51/52) | Componente mais defensável | **PRESERVAR** (como candidato, medir alpha vs beta) |
| RANGE = fundo do range (10 trades) = metade da V2 | `phase48` keep(RANGE) | `f53ac72` overfit p=1.0 inverte sob let-run; phase52 "RANGE-fundo pior que random" | Metade do N da V2 é frágil/beta | **REBAIXAR** (marcar como beta-suspeito) |
| BEAR = capitulação profunda = coração | `phase48` bear_deep; memória (+8R em 2023-10-06) | `26f6bca` BEAR elegível avgR=−0,593; **n=1**; 0 BEAR nos winners hand-drawn | Componente mais fraco em amostra | **PRECISA VISUAL / n insuficiente** (não robusto com n=1) |
| Esqueleto V1 +53,7/+63,1R "aprovado sem fitting" | memória; `phase39/40/41` | phase51 "é BETA"; contém refinos in-sample (THR=3, NB≤14/RS≤60 n5) | Headline inflado vs substância | **REBAIXAR** (V1 superseded pela V2; lucro = beta) |
| V3 gatilho-de-zona +64,6R | `phase50` | `_DA_phase50_ztrigger` + phase51: não bate random-p95; Cris rejeitou | — | **REJEITAR** (já rejeitado) |
| bull_break 1-após-capit N16 +40R streak4 | `phase73–77` | jackknife: +15,5R vêm de 3 trades 2023; sem-2023 ≈ neutro | Melhor expansão, mas concentrada | **PRESERVAR como lead** (não promover) |
| Expansões (L2-pós-V2, bull-reteste, swing, capit-expandida) | — | phase56–72: todas diluem ou = beta | Fecham vias de +N | **REJEITAR** (esgotadas) |

### Pergunta central — a aprovação deve continuar como:

- **A) V2 zona-pura integral (BULL + RANGE + BEAR)** — ⚠️ desaconselhado: RANGE frágil (overfit/beta) + BEAR n=1 avgR negativo no elegível.
- **B) V2 BULL/RANGE reduzida** — ⚠️ RANGE ainda sob suspeita de beta (f53ac72).
- **C) V2 BULL-only** — componente mais defensável, mas grande parte ainda é beta long-gold (phase51/52); N cai muito.
- **D) Apenas lead de pesquisa, sem estratégia aprovada** — coerente com "edge-puro ausente / é beta" + amostras finas.
- **E) Congelar tudo como refutado/superseded** — forte demais: o backbone causal e o BULL têm valor de pesquisa; a preservação já protege o trabalho.

**Recomendação (não-decisão):** **D** — manter como **lead de pesquisa / candidato preservado**, com o backbone causal e o componente BULL sinalizados como o que tem mais substância, e RANGE/BEAR explicitamente rebaixados até mais dados. Motivo: as DA committadas convergem com os caveats internos da memória (beta ≫ alpha, n finos), o headline "+53,7R aprovado" não sobrevive à leitura da substância, mas o trabalho é causalmente limpo e vale preservar para retomar. **Aguardo a tua decisão A–E — não decido sozinho.**

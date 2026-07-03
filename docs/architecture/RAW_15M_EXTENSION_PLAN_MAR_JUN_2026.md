# RAW 15M EXTENSION PLAN — cobertura BEAR-2026 (2026-07-03)

**Modo executado: plan-only / read-only.** Zero coleta, zero TradingView/MCP/chart/Replay, zero escrita RAW, zero scripts alterados, zero backtest, zero plot, zero produção.
**Fontes:** audit XAU 15M (2723465) · authority docs reconciliados (e842023) · PLOTTING_CANON_MASTER + skills/plotting-canon (regra, não usados — sem plot) · **skill `replay-backtest-manager`** (protocolo canônico de coleta, lido) · `config/paths.py` · HD externo (leitura direta: RAW dir + manifests) · `build_causal_primitives.py` · `_source_guard.py` (via audit) · `safe_backtest_window.sh` · `run_xau_replay_feature_collect.py`.

## 0. ⚠️ CORREÇÃO DE ESCOPO (achado desta fase — corrige o audit)

O audit (conflito #4) afirmou "RAW termina 2026-02". **ERRADO no fim da cobertura:** a leitura direta do HD revela o **8º bloco** `XAUUSD_15m_replay_2026-02-25_to_2026-05-25_rerun_customOBbaseline.jsonl.gz` (130M, 5710 bars, manifest sha256 + roundtrip YES, primitives construídas 26-jun) — também registrado no skill replay-backtest-manager como source-of-truth do período. A causa provável do erro: nome do 8º ficheiro com sufixo `_rerun_customOBbaseline` levou o inventário a lê-lo como variante, não como extensão de cobertura.

- **Cobertura real: 2024-05-25 → 2026-05-25** (8 blocos contíguos de 3 meses, todos com manifest+checksum).
- **BEAR-2026 do Cris (a partir de 29-jan) já está coberto até 2026-05-25.**
- **Gap verdadeiro: 2026-05-25 → hoje (2026-07-03) ≈ 5,5 semanas ≈ ~2.600 barras** — muito menor que "mar→jun".
- O nome do bloco (`MAR_JUN_2026`) derivou do erro do audit; o alvo correto é **mai→jul-2026**. Errata do audit incluída aqui (audit já pushed; não reescrever histórico — esta seção é a correção canônica).

## 1. Executive verdict

**READY_FOR_RAW_EXTENSION** — pipeline maduro e testado 8×, protocolo canônico existente (skill replay-backtest-manager + `safe_backtest_window.sh --replay-collect` wired), zero risco de overwrite por design (bloco novo = ficheiro novo), manifests/checksums padrão já estabelecidos. Escopo corrigido: 1 bloco curto (~5,5 semanas) em vez de 4 meses. Nada bloqueia exceto as autorizações (§10).

## 2. Current RAW coverage

- **Local:** `/Volumes/GUTS_ LACIE/TradingData/raw_replay/XAUUSD/15M/` (= `RAW_DATA_ROOT/raw_replay/XAUUSD/15M`, paths.py).
- **8 blocos contíguos** `2024-05-25 → 2026-05-25` (128-134M gz cada; boundaries encadeados; blocos com ~1 dia de sobreposição no início por design — ex.: manifest do 8º diz dataset 2026-02-24→2026-05-25).
- **Manifests:** `TradingData/manifests/XAUUSD_15m_replay_*_manifest.txt` — todos com original/archived sha256, roundtrip_verified YES, contagem de bars, indicadores registrados.
- **Indicadores do baseline (8º bloco, o layout validado):** Custom OB Detector v11 — Alert (baseline) · LuxAlgo SMC · NAS Top Bottom · Market Order Bubbles · RSI.
- **Superseded preservado:** versão pré-baseline do 8º período em `15M/superseded/` (nunca deletada).
- **Lacuna única:** 2026-05-25 → presente.

## 3. Target coverage

- **Período:** 2026-05-25 → data da coleta (proposto: fechar em **2026-07-25** se a coleta ocorrer após essa data, mantendo grade de meses; senão, até o dia da coleta — decisão do Cris; blocos de 3 meses são o padrão, um bloco curto é aceitável e registrado no manifest).
- **Símbolo/TF:** PEPPERSTONE:XAUUSD · 15 (chart resolution "15").
- **Fonte:** TradingView Replay per-bar via `run_xau_replay_feature_collect.py` DENTRO de `safe_backtest_window.sh --replay-collect` (nunca python bare) — o mesmo método dos 8 blocos.
- **Causal boundary:** cada registro = estado do chart as-of close da barra (replay_step); first-appearance por id; SHIFT1 a jusante (contrato já implementado no builder).
- **Expected output:** `alert-bridge/logs/backtests/XAUUSD_15m_replay_2026-05-25_to_<END>.jsonl` (~350-400MB raw p/ 5,5 semanas) → gz ~45-55MB no HD + manifest.
- **Pré-condição dura:** chart com o MESMO indicator baseline do 8º bloco (Custom OB v11 baseline etc.) — confirmação manual do Cris no preflight (skill §5 "Confirm chart manually").

## 4. Current pipeline (mapeado)

`RAW HD (blocos gz)` → `build_causal_primitives.py` (leitor EXCLUSIVO do RAW; 1 bloco → 1 `primitives/*.primitives.json`; OHLC/RSI/ATR/EMA21 + eventos NAS/SMC first-appearance + ciclo de vida de zonas Custom OB) → `primitives/` + `bubbles/*.jsonl` (known_at) + `htf_primitives/` → engines 15M (`engine_regime15m_v5`, `engine_substrate4_v5_hourcausal`, builders 5ATR/8ATR, labs). `_source_guard.py` proíbe mecanicamente qualquer fonte fora de RAW-gz-15M + primitives.
**Downstream que dependeria da extensão:** primitives do bloco novo (aditivo) → re-run opcional do detector v5 e da base #4 sobre a janela estendida (fase futura autorizada; NÃO neste bloco). Nota de portabilidade (não-blocker): `build_causal_primitives.py` hardcoda o path do HD em vez de usar `config/paths.py` (RAW_DATA_ROOT) — candidato a alinhamento futuro.

## 5. Files/scripts inventory

- **Coleta:** `alert-bridge/run_xau_replay_feature_collect.py` (TF-agnóstico, per-bar, nunca fake — flags de availability) · wrapper obrigatório `alert-bridge/safe_backtest_window.sh` (`--replay-collect --timeframe 15 --start-date … --end-date …` — wired, verificado L54/80/110; header do script menciona só --smoke = comentário stale, não-blocker).
- **Build:** `research/xau_15m_bb_nas_leonardo/build_causal_primitives.py` (aditivo por bloco).
- **Validação/guards:** `_source_guard.py` · manifests (protocolo do skill §Archival Procedure) · `verify_swept_subset.py` etc. (downstream).
- **Skill/protocolo:** `~/.claude/skills/replay-backtest-manager/SKILL.md` — preflight (5 checks), maintenance window rules, real collection commands, post-collection report, archival procedure, deletion rules, known risks. **Este plano segue o skill; não reinventa.**

## 6. Risk map

| Risco | Avaliação | Mitigação |
|---|---|---|
| Overwrite de RAW vivo | **Nulo por design** — bloco novo = ficheiro novo; nada toca os 8 existentes | nome único + sandbox-first (§7) |
| Duplicate bars na fronteira 2026-05-25 | Real (blocos têm ~1 dia de overlap por design) | validação de continuidade (§8): dedup por timestamp na junção, como nos blocos anteriores |
| Timestamp/timezone | Baixo — mesmo coletor/exchange dos 8 blocos | monotonicidade + freq esperada (§8) |
| Session gaps (fds/feriados) | Esperado, não é erro | gap detection distingue fds de buraco real |
| Partial candle no fim da coleta | Real (última barra pode ser incompleta) | descartar último bar se replay não fechou; registrar no manifest |
| Replay export drift (layout de indicadores mudou desde 26-mai) | **RISCO PRINCIPAL** — se o chart não tiver o baseline Custom OB v11 idêntico, o bloco novo é inconsistente com o 8º | preflight manual do Cris (símbolo/TF/indicadores) ANTES do replay_start; comparar `_feature_availability` do 1º snapshot vs manifest do 8º bloco |
| TradingView/market-data restrictions | RAW é uso interno (nunca redistribuído/migrado a Supabase como conteúdo) | política existente mantida |
| Chart interaction | Coleta EXIGE chart/MCP/Replay | só sob autorização explícita + janela do skill (pausa daemon/cron/flag, restore trap EXIT) |
| Enrich/evaluator/orfãos interferindo | Conhecido (skill §preflight 1-2) | preflight completo do skill (enrich ausente, zero server.js órfão, /health público 200, daemon carregado antes da janela) |

## 7. Safe collection protocol proposal (a executar SÓ com aprovações §10)

1. **Preflight (skill §Mandatory Preflight, 5 checks)** + confirmação manual do Cris de símbolo/TF/indicadores no chart.
2. **Janela:** `alert-bridge/safe_backtest_window.sh --replay-collect --timeframe 15 --symbol PEPPERSTONE:XAUUSD --start-date 2026-05-25 --end-date <END>` — pausa recheck+daemon, restart TV, valida CDP, coleta, **restore garantido em todo exit path** (trap).
3. **Sandbox-first:** output nasce em `alert-bridge/logs/backtests/` (local, fora do HD) — o RAW vivo do HD **não é tocado** durante a coleta. Nada é movido ao HD antes da validação §8.
4. **Pós-coleta imediato:** row count + primeira/última barra + `_feature_availability` do 1º snapshot comparado ao manifest do 8º bloco (layout idêntico?).
5. **Arquivamento (skill §Archival Procedure):** sha256 do original → gzip → sha256 do gz → cópia ao HD → `gzip -t` → **roundtrip** (gunzip|sha256 == original) → manifest novo em `TradingData/manifests/` (mesmo formato dos 8) → local retido até aprovação de deleção (skill §Local Deletion Rules).
6. **source_ref/registry:** registrar o bloco novo no dataset registry (`scripts/build_dataset_registry.py`) + batch delta Supabase futuro (`source_registry`, pointer+checksum — aplicação manual Cris).
7. **Nunca:** rodar 2 blocos sem autorização · deletar local sem roundtrip+aprovação · tocar receiver/cloudflared/secrets.

## 8. Validation protocol (pós-coleta, pré-uso)

1. Schema check (campos do coletor presentes; availability flags coerentes).
2. Timestamps monotônicos, sem duplicatas internas; frequência esperada 900s (com gaps de sessão legítimos).
3. **Continuidade com o fim existente:** junção com o 8º bloco — overlap de ~1 dia deduplicado por timestamp; zero buraco entre 2026-05-25 e o 1º bar novo (excl. fds).
4. Gap detection (buracos > sessão normal = FAIL investigável).
5. Sample rows: 3 barras espalhadas inspecionadas (OHLCV + labels coerentes).
6. **Dry-run de primitives em SANDBOX only:** rodar `build_causal_primitives.py` numa CÓPIA do bloco em `/tmp` (ou output para dir sandbox) — validar contagens/eventos SEM escrever em `primitives/` oficial até aprovação de rebuild (§10.4).
7. **Nenhum backtest sério** nesta fase (protocolo 03 §Research exige bloco próprio com manifest).

## 9. Rollback

- **Sandbox:** descartar = `rm` do jsonl local + primitives sandbox em /tmp (nada oficial tocado).
- **Se o gz já foi ao HD:** remover o ficheiro novo + manifest novo (os 8 blocos originais nunca são modificados — rollback não os afeta por construção).
- **Cold copy:** original local retido até aprovação de deleção = cópia de segurança natural; sha256 em manifest permite verificação a qualquer momento.
- Primitives oficiais: só mudam na fase de rebuild autorizada; rollback = deletar o `.primitives.json` novo (aditivo).

## 10. Required approvals (separadas — nada automático)

1. **Approval to collect** (rodar a janela + Replay no período alvo; um bloco só).
2. **Approval to touch chart/TradingView/MCP** (implícita na coleta, mas explícita: pausar daemon/cron, restart TV, Replay; confirmação manual do chart pelo Cris no preflight).
3. **Approval to write RAW** (mover gz+manifest ao HD após validação §8.1-5).
4. **Approval to rebuild primitives** (rodar builder no bloco novo para o dir oficial).
5. **Approval to run any backtest** (re-adaptação regime v5/base #4 sobre a janela estendida — bloco próprio com manifest).

## 11. Recommendation (menor próxima ação segura)

Corrigir a premissa de escopo com o Cris (este doc, §0: gap = mai→jul, ~5,5 semanas, BEAR-2026 já quase todo coberto) e **decidir o END date do bloco** (coletar já até hoje vs. esperar 2026-07-25/08-25 para bloco maior). Só então, se aprovado, executar §7 passo 1 (preflight, ainda sem coleta). Observação factual: como o BEAR-2026 já está coberto até mai, a re-adaptação de regime (fase 4 da ordem do Cris) **poderia começar sobre a base atual sem esperar a coleta** — a extensão agrega as 5,5 semanas finais, não o BEAR inteiro. Decisão de ordem = Cris.

## 12. Acceptance criteria (cumpridos)

- [x] Plano criado · [x] zero coleta · [x] zero escrita RAW · [x] zero chart/TV/MCP/Replay · [x] zero produção/runtime · [x] zero scripts alterados · [x] escopo corrigido com evidência (leitura direta do HD + manifests + skill) · [x] safety OK · [x] commit local, sem push sem autorização.

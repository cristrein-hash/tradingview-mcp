# L1 EMA21 4H LONG Continuation — NAS-LIVE REMEDIATION · RELATÓRIO

**Data:** 2026-07-09 · **Verdict:** **PASS — RESOLVED-FOR-DRYRUN** (DA PASS) · **Produção:** `NOT_AUTHORIZED`

Remedia o bloqueador NAS-live diagnosticado antes (ver `L1_NAS_LIVE_CAUSALITY_GATE_REPORT.md`, que é o estado PRÉ-remediação = BLOCKED). Prova causalidade de `NAS_dist_EMA(i-1) ≥ 1.31` no fecho da barra 4H, **sem aproximação/repaint/valor-corrente**. Sem produção/Telegram/cycle. Runtime alterado só em modo fail-closed/dry-run.

## 1. Bootstrap
HEAD==origin==`bd1c749` (após commit do diagnóstico) · safety baseline BLOCKER=3/W=1/INFO=50.

## 2. Chart-state fix (Fase 2) — feito
- Estudo `NAS TOP BOTTOM DETECTOR` (`pkqE7L`) estava `visible:false` → `data_get_study_values_at_bar` devolvia `n_bars=0`.
- `indicator_toggle_visibility(pkqE7L, true)` (1ª execução: `visible_before=False` → toggle success → `visible_after=True`) + tempo de recompute → o estudo passou a devolver a **série completa por barra**: `NAS_DISTANCE_FROM_EMA_ATR` com timestamps 4H distintos (`n_bars=50`, ≥1.31 em 9/50). RSI controlo sempre funcionou.
- **i-1 direto = DISPONÍVEL.** Data-window também expõe a distância.
- **Caveat (a):** a visibilidade é estado-de-chart, **não garantida por código** — um reload de layout pode revertê-la. Se reverter → série vazia → runtime **fail-closes** (`blocked_missing_closed_bar_study_values`), não dispara. Frágil-mas-seguro.

## 3. Não-repaint (Fase 5) — provado
- **Match direto live-vs-RAW = IMPOSSÍVEL por cobertura:** RAW replay termina 2026-06-09; live at_bar expõe só os últimos 50 bars (2026-06-26+) e o ledger é 2026-06-16..23 — **janelas disjuntas** (`overlap_bars=0`, `ledger_raw_overlap=0`). Documentado, não é falha.
- **Substituto causal = dupla-leitura:** 49 barras FECHADAS lidas 2× → `max_abs_diff = 0.0` (idênticas). A distância da barra fechada **não repinta**. O DA observou ainda a barra *forming* a repintar live (−1.063→−1.204) enquanto as fechadas ficam idênticas — o que **valida** o design (excluir forming + congelar no fecho).
- **Caveat (b):** não existe cross-check numérico live/ledger-vs-RAW (janelas disjuntas). A ponte para o edge backtestado (N24/75%/+45R, computado sobre `nas_at` do RAW) é *mesmo-indicador* (o estudo live é o mesmo Pine que gerou os `study_values` do RAW) + concordância de escala (live −3…+2 vs ledger RAW −3.2…+1.87). Razoável, **não** é prova de equivalência numérica.

## 4. Ledger wiring fail-closed (Fase 3) — implementado + testado
Alterado **só** `runtime_xau.py` (fail-closed; NÃO altera threshold 1.31 / SHIFT1 / SL / exit / entrada):
- **`_bar_time_plausible()` guard:** rejeita bar_time fora de época (`<1.5e9`) ou distante de now (>30 dias) → mata a corrupção tipo-2017.
- **`persist_feature` enriquecido:** guard + grava `{bar_time, nas_dist, symbol, timeframe, threshold, source_study_id, source_method, persisted_at, closed_bar_confirmed}`; rejeita duplicado **conflitante**.
- **`nas_from_history` (era DEAD CODE) wired como fonte AUTORITÁRIA do SHIFT1:** o gate usa o **valor CONGELADO do ledger de i-1** (persistido no fecho de i-1, no ciclo anterior) — imune a repaint — com **cross-check** contra a série viva (bloqueia mismatch >0.05) e **fail-closed** se o ledger não tiver i-1. Novos estados: `blocked_missing_nas_shift1_ledger`, `blocked_nas_shift1_ledger_mismatch`.
- **Dry-run test 7/7 PASS** (`l1_nas_ledger_wiring.py`, ledger temporário): T1 usa i-1 do ledger (1.50, source=`ledger_frozen`) · T2 ausência→bloqueia · T3 corrupto-2017 rejeitado (write+read) · T4 NAS(i)=9.99 **NÃO** usado (usa 1.50) · T5 mismatch→bloqueia · conflicting-dup + wrong-symbol→bloqueiam.
- **Caveat (c):** primeiro ciclo após qualquer gap **fail-closes** até o ledger repopular (i-1 vem do ciclo anterior). Fail-safe.

## 5. Fase 4 (Pine) — NÃO necessária
A série foi recuperada pelo chart-state fix; a distância é um `plot()` real (confirmado no RAW: `study_values` do "NAS TOP BOTTOM DETECTOR" incluem `NAS_DISTANCE_FROM_EMA_ATR`). Sem alteração de Pine.

## 6. Segurança / confirmação negativa
- `scanner.py` **intacto** (`git diff` vazio): `NAS_DIST_SHIFT1_MIN=1.31`, `TARGET_R=3.0`, `SL_ATR_BUFFER=0.1`, `RSI_VS_MA_THR=-9.35`.
- Produção OFF: LaunchAgent `com.cristrein.xau-l1-cycle` **não carregado**; `RunAtLoad=false`; sem cron. Telegram não emitido; cycle não ligado; broker não tocado.
- **Flag pré-existente (NÃO introduzido por esta remediação, NÃO corrigido — fora de escopo):** o plist dormente carrega `--send-telegram` e o consumer está allow-listed → emissão live está gated **só** pelo agente estar descarregado, não por lock de código. Recomenda-se um **dry-run lock de código** antes de qualquer go-live. (Não toquei no plist/LaunchAgent.)

## 7. DA verdict (Fase 6)
**PASS — RESOLVED-FOR-DRYRUN.** Sem leak de causalidade; SHIFT1 provadamente i-1-congelado + cross-check + fail-closed em todos os modos de falha; scanner e 1.31/3.0/0.1 intactos; corrupção 2017 agora inerte; produção descarregada. Detalhe em `L1_NAS_LIVE_REMEDIATION_DA.md`.

## Estado final
- **NAS-live: RESOLVED-FOR-DRYRUN** (era BLOCKED). i-1 causal disponível + wiring fail-closed provado.
- **Produção: NOT_AUTHORIZED.** Rótulo honesto = "pronto para production-gate DRY-RUN", **não** produção live.
- 3 caveats que acompanham qualquer claim de "resolvido": (a) depende do estudo NAS ficar visível/computado; (b) sem cross-check numérico live-vs-RAW (cobertura disjunta); (c) fail-close de warmup no 1º ciclo pós-gap.

## Próximo passo (requer autorização)
Se o Cris aprovar: **L1 production-gate DRY-RUN** (correr o runtime `--once` read-only, sem `--send-telegram`, sem cycle, observando os estados/ledger a acumular ao vivo) — ainda sem Telegram operacional. Antes de qualquer go-live: (1) dry-run lock de código; (2) garantir persistência da visibilidade do estudo NAS; (3) idealmente uma janela de overlap live-vs-RAW para o cross-check numérico.

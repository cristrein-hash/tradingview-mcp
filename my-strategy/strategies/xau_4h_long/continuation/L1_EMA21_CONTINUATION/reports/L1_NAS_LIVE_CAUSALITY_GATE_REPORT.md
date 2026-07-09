# L1 EMA21 4H LONG Continuation — NAS-LIVE CAUSALITY GATE · RELATÓRIO

**Data:** 2026-07-09 · **Verdict:** **BLOCKED (NO-GO para produção) — recuperável** · **Produção:** `NOT_AUTHORIZED`

Pergunta técnica: *no runtime live, dá para usar causalmente `NAS_dist_EMA(i-1) ≥ 1.31` no fecho da barra 4H, sem aproximação/repaint/valor-corrente-errado?* **Resposta: NÃO com o wiring atual — o estudo NAS não devolve a série por barra enquanto está oculto/não-computado, e o ledger que resolveria isto é código morto.** Read-only; sem produção/runtime/chart/Telegram/commit.

## 1. Bootstrap
HEAD==origin==`4b58ac9` · working tree limpo · safety BLOCKER=3/W=1/INFO=50 (baseline).

## 2. Diagnóstico NAS
**Fonte no backtest (funciona):** `scanner.load_series()` lê `NAS_DISTANCE_FROM_EMA_ATR` do **RAW replay gravado** (`study_values` no JSONL) — existe porque foi gravado no replay. **Não é uma leitura live-reproduzível.**

**Fonte no runtime (o problema):** `tv_read_adapter.read_xau_snapshot` → `data_get_study_values_at_bar(study_filter="NAS")` → `nas_series` por barra. `runtime_xau.align_study_values` alinha **por timestamp exato** (`nas_shift1 = nas_by_t.get(prev_t)`).

**Prova live (read-only, hoje, chart em PEPPERSTONE:XAUUSD/240):**
| leitura | resultado |
|---|---|
| `data_get_study_values_at_bar` filtro "NAS" | 1 estudo `NAS TOP BOTTOM DETECTOR` (entity `pkqE7L`) · **`last_index=None` · `n_bars=0`** (série VAZIA) |
| idem, controlo "Relative Strength" | `last_index=303 · n_bars=8` · RSI/RSI-MA por barra, timestamps 4H distintos ✅ |
| `data_get_study_values` (data-window) | NAS ausente · sem token "DISTANCE" |
| `data_get_indicator(pkqE7L)` | `visible:false` · só inputs (pineId+numéricos), sem valor por barra |
| `pine_shapes` no NAS | só 2 shape-plots (`NAS BOTTOM/LONG`, `NAS TOP/SHORT`), 0 ativações/50 barras — a **distância não está lá** |

**Consegue i-1 direto?** **NÃO** (nem i). Toda via live devolve vazio agora.
**Risco de barra aberta/repaint:** o runtime já trata (só barra fechada via `blocked_bar_not_closed`; match por time exato). O problema atual não é repaint — é **ausência total da série** enquanto o estudo está oculto.

**Root cause (corrigido pelo DA — NÃO é limitação fundamental):** o estudo NAS está `visible:false`/não-computado → `data().lastIndex()=null` → série vazia (partilha `n_bars=0` com todos os estudos ocultos: Custom OB, HTF PO3, Volume, SVP…). **A MESMA tool leu NAS por-barra em Junho (27 valores reais no ledger)** e `pineFeatures.plot=1` → a distância **é** exponível como série; só não é legível **enquanto oculto/inativo**. É **BLOCKED-BY-STATE, recuperável**, não impossibilidade.

## 3. Ledger (Path B) — construído mas NÃO ligado
`runtime_xau.persist_feature` grava append-only `.runtime_state/l1_feature_history.jsonl` `{bar_time, nas_dist, persisted_at}` por barra fechada. **27 entradas reais** (2026-06-16→23). MAS:
- **`nas_from_history` (o leitor do ledger) é CÓDIGO MORTO — zero call-sites.** O runtime nunca usa o ledger como fonte do SHIFT1; depende 100% do `at_bar` devolver i-1 na janela viva. **O "path ledger" está desenhado e construído, mas não wired.**
- **Ledger poluído:** 1 entrada corrupta `bar_time=1488207600` (2017-02-27) persistida em 2026-06-18 → misalignment real na captura. O guard `persist_after_bar_close_ok` é **cego** a bar_times antigos (2026≥2017+4H é trivialmente verdade).
- **Fail-closed intacto:** uma entrada-lixo nunca casa por timestamp exato com um `prev_t` real de 2026 → `blocked_missing_closed_bar_study_values`. **Poluição só BLOQUEIA, nunca dispara errado.** (verificado)

## 4. Artifacts criados
- `reports/l1_nas_live_causality_probe.py` + `_result.json` (ledger consistency + read-only MCP).
- `reports/_l1_nas_raw_tool_dump.py` (dump cru da tool: NAS vazio vs RSI OK).
- `reports/L1_NAS_LIVE_CAUSALITY_GATE_REPORT.md` (este) + `L1_NAS_LIVE_CAUSALITY_GATE_DA.md`.

## 5. DA verdict
**BLOCKED (NO-GO) confirmado** — nenhuma via live devolve NAS(i-1) agora; runtime fail-closes; produção não pode avançar. **Correções do DA honradas:** (a) root cause = estado do estudo (oculto), não "labels-only fundamental"; (b) `nas_from_history` = dead code; (c) fix mais barato = tornar o estudo visível antes de mexer no Pine.

## 6. Próximo passo (remediação — requer autorização; NÃO executado)
Ordem de menor→maior custo, tudo **sem recomputar NAS** (proibido):
1. **Tornar o estudo `NAS TOP BOTTOM DETECTOR` visível/computado** no chart e re-verificar se `at_bar`/data-window ressurgem `NAS_DISTANCE_FROM_EMA_ATR` (Junho indica que sim). *Requer tocar no chart → autorização.*
2. **Wire o ledger (fail-closed):** ler i-1 de `nas_from_history` (não da janela `at_bar`); alimentar a cada barra fechada; **adicionar guard** que rejeita `bar_time` distante de `persisted_at` (corrige a cegueira que deixou passar o 2017); não emitir sinal sem ≥1 ciclo anterior válido. *Mudança de runtime → autorização.*
3. **Só se 1+2 falharem:** expor `NAS_DISTANCE` como `plot(display=display.data_window)` no Pine do NAS. *Mudança de indicador → autorização.*
4. Após qualquer fix: **sanity contra o scanner** (comparar NAS-live(i-1) vs RAW gravado em janelas conhecidas) antes de qualquer produção.

**Conclusão:** o bloqueador NAS-live **continua ativo** — produção `NOT_AUTHORIZED`. É **recuperável** sem recomputação, mas exige mudanças de chart/runtime/indicador que precisam de autorização explícita do Cris. Nada foi tocado/commitado.

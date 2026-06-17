# XAU Visual Macro Monitoring Agent — Design

**Status:** `DESIGN_ONLY · NOT_IMPLEMENTED · CONSULTATION` · **Data:** 2026-06-17
**Nada executado · sem daemon · sem scheduler · sem broker/ordens · sem Telegram · sem MCP/chart write · sem alterar L1/strategy_rules/catalog · sem Caminho B.** Só este documento.

---

## 1. Executive summary

Proposta de uma camada de **inteligência de contexto visual** ("XAU Visual Macro Analyst") que lê o chart de XAU em múltiplos timeframes, captura screenshots full-res, e produz **leituras macro-estruturais textuais** (aceitação/rejeição, BOS/CHoCH, supply/demand, exaustão, bear leg vs pullback, SL estrutural provável) para **revisão humana** — **nunca** para decidir/enviar trade. O gargalo atual não é falta de indicador; é que a leitura mecânica confunde reclaim-válido com repique-em-bear-leg e SL-estrutural com SL-curto. Esta camada existe para **ensinar/assistir essa leitura**, marcada sempre como `VISUAL_CONTEXT / HUMAN_REVIEW`.

**Restrição central (a que define tudo):** o chart TradingView (via CDP :9222) é um **recurso único compartilhado** com a produção — o daemon `com.cristrein.xau-l1-cycle` + cron (`monitor_xau_4h_strategies.py`) controlam o MESMO chart. Um agente visual que mexe no chart **colide** com a L1. Logo o design é dominado por **lock/restore + janelas de não-colisão**, não por features.

## 2. Objetivo do agente visual

Produzir, de forma recorrente e auditável, um **mapa estrutural multi-timeframe** do XAU que um humano (Cris) usa para decidir — capturando o que as métricas genéricas não capturam: maturidade da perna, aceitação real, qualidade de supply/demand, exaustão, divergência entre TFs.

## 3. O que ele deve fazer

- Capturar screenshots **full-res** por timeframe, vinculados a `symbol/timeframe/timestamp`.
- Ler estrutura: BOS/CHoCH, polaridade, retest/reclaim, **aceitação vs rejeição**, supply absorvida vs rejeitada, demand útil vs irrelevante, exaustão, top sweep / liquidity grab, **bear leg vs pullback bull**, macro-leg.
- Comparar timeframes (15M/30M/1H/4H/1D) e sinalizar divergências.
- **Cross-check obrigatório contra RAW/OHLCV** (nunca confiar só em pixel/UI).
- Gerar leitura textual estruturada + fila de revisão humana.
- Propor SL estrutural provável (modelo flexível, §sob SL) — como sugestão, não ordem.

## 4. O que ele NUNCA deve fazer

- Executar/enviar trade, tocar broker, enviar Telegram automático.
- Decidir estratégia, alterar L1/strategy_rules/catalog, remover pause flag.
- Rodar como daemon antes de design aprovado.
- Tratar screenshot como **validação estatística** (é contexto, não backtest).
- Controlar o chart **enquanto a L1 está controlando** (colisão).
- "Ler" preço/níveis por pixel da UI sem confirmar no RAW.

## 5. Timeframes recomendados

Núcleo: **1D · 4H · 1H** (macro → operacional → timing). Opcionais: 15M/30M (refino de timing/aceitação intrabar), 12H (ponte macro). v0 = **3 TFs (1D/4H/1H)** para limitar custo e colisão.

## 6. Fluxo operacional seguro

```
[trigger humano/on-demand] → check production safety →
  IF L1 ativo no chart: ABORTA ou usa instância/aba separada →
  acquire chart lock → snapshot layout atual (restore point) →
  para cada TF: set_timeframe → settle → capture_screenshot full-res →
  data_get_ohlcv (RAW) do mesmo range → vincular →
  restore layout original → release lock →
  Visual Reader analisa imagens + RAW → multi-TF synth →
  outputs marcados VISUAL_CONTEXT/HUMAN_REVIEW
```
**Hard rule:** sempre **restore** do estado do chart ao terminar; se algo falhar, **restaura produção primeiro, depois diagnostica** (incident-response).

## 7. Arquitetura modular proposta

1. **No-Trade Safety Guard** (wrapper externo) — verifica: L1 idle? receiver/cloudflared ok? broker inativo? pause-state coerente? Só então libera. Aborta caso contrário.
2. **Screenshot Collector** — set TF → settle → `capture_screenshot` full-res → nomeia/arquiva → restore.
3. **Visual Context Reader** — lê 1 imagem + RAW do range, produz leitura estrutural por TF.
4. **Multi-Timeframe Synthesizer** — concilia 1D/4H/1H, sinaliza divergência/alinhamento.
5. **Auction Theory Classifier** — aceitação/rejeição, absorção vs distribuição, top sweep.
6. **Exhaustion Detector** — clusters NAS/bubbles + RSI div como contexto (não gate).
7. **Supply/Demand Quality Reader** — absorvida/rompida vs rejeitada; distância+frescor.
8. **Human Review Pack Builder** — monta o board + fila para o Cris.
9. **Memory/Knowledge Updater** — guarda leituras+correções do Cris como ground-truth para melhorar a taxonomia (treino futuro).

Módulos 3–9 são **stateless analisadores** (sem tocar chart); só 1–2 tocam o chart, sob lock.

## 8. Screenshot capture protocol

- **Full-res:** região `chart` (sem painéis irrelevantes) ou `full`; resolução nativa da janela; evitar redimensionar.
- **Nomeação:** `XAUUSD_<TF>_<UTCyyyymmddHHMM>_<barTime>.png` (TF e bar-time explícitos → nunca analisar screenshot errado).
- **Vínculo:** cada PNG acompanha um sidecar `*.json` com `{symbol, timeframe, captured_at, last_bar_time, visible_range, ohlcv_ref}`.
- **Settle:** aguardar render (indicadores desenham async) antes de capturar — senão boxes/labels faltam (visto no incidente: drawings só ancoram com histórico carregado).
- **Cross-check:** sempre puxar `data_get_ohlcv` do mesmo range; se preço lido na imagem ≠ RAW, **descartar a leitura** (a UI engana — labels sobrepõem, drawings deslocam).
- **Histórico carregado:** garantir que o range alvo está carregado (scroll/visible_range) ANTES de capturar — drawings/estrutura fora do histórico não renderizam.

## 9. Visual analysis checklist (o que o agente deve aprender)

estrutura macro · BOS/CHoCH · polaridade · retest/reclaim · **aceitação vs rejeição** · supply absorvida vs rejeitada · demand útil vs irrelevante · exaustão · top sweep / liquidity grab · **bear leg vs pullback bull** · RSI/NAS/Bubbles como contexto · divergência entre TFs · **SL estrutural provável** · **trade should exist / should not exist**. Cada item com definição operacional + "o que confirma / o que invalida" (herdar da taxonomia `XAU_4H_L2_BPT_VISUAL_DISCRIMINATION_TAXONOMY.md`).

### Refino de `acceptance_after_reclaim` (correção do Cris)
Não basta "2–4 candles sem fechar abaixo". Adicionar leitura macro: (a) reclaim **não** logo após bear displacement dominante; (b) defende polaridade; (c) evita LH/LL imediato; (d) supply próxima **rompida/aceita**, não rejeitada; (e) **se há bear leg clara → long bloqueado ou review-only**.

### Modelo de SL flexível (correção do Cris)
`SL_RETEST_LOW` · `SL_STRUCTURE_LOW` (swing low estrutural) · `SL_DEMAND_BASE` · `SL_POLARITY_CLOSE_INVALIDATION` · `SL_TOO_TIGHT_FLAG` (mecânico dentro da respiração normal). O agente sugere **qual SL a estrutura pede** — e flag quando um "loser" provavelmente era winner com SL estrutural (não salva por SL; sinaliza para revisão).

## 10. Multi-timeframe synthesis

Board por bar: `{1D: macro_leg/direção, 4H: estrutura/aceitação, 1H: timing/retest}`. Regra de coerência: long só é "contexto válido" se **1D não está em bear displacement dominante** E 4H mostra aceitação. Divergência (4H bull / 1D bear) → `NEEDS_SECOND_REVIEW` / review-only.

## 11. Integração com L2/BPT e L1 sem contaminar

- **L1 (`xau-l1-cycle` + cron `monitor_xau_4h_strategies.py`) controla o chart.** O agente visual **nunca** roda concorrente: ou (a) janela quando L1 está idle (ler o schedule do cron), ou (b) **instância/aba/layout TradingView separada** dedicada ao agente, ou (c) lock cooperativo + restore. Recomendo (b) longo prazo (isolamento total), (a/c) para v0.
- **L2/BPT:** o agente alimenta a taxonomia visual (ground-truth do Cris) — é **upstream de research**, não toca o runtime L1.
- Nunca remover pause flag; nunca tocar receiver/broker; logs e outputs **separados** dos de produção.

## 12. Como armazenar outputs

- `visual/screenshots/` (PNG + sidecar json) — **gitignored** (binário pesado); manifest versionado.
- `visual/visual_reading.jsonl` — leitura por (symbol,TF,bar) — gitignored, regenerável; summaries versionados.
- `visual/visual_summary.md`, `visual/episode_labels.csv`, `visual/mtf_context_board.csv` — versionados.
- `visual/human_review_queue.csv` — versionado.
- Tudo carimbado `VISUAL_CONTEXT / HUMAN_REVIEW`, com `captured_at` e `ohlcv_ref`.

## 13. Uso para treinamento futuro

As **correções do Cris** (visual_confirm CONFIRMED/CORRECTED) viram ground-truth acumulado → calibra a definição de aceitação/bear-leg/SL e mede recall do classificador visual contra esse GT (recall-gate antes de qualquer uso quantitativo). Nunca usar as leituras como validação estatística por si — só como rótulos para auditar/calibrar.

## 14. Riscos e hard stops

- **Colisão de chart com L1** → corrupção do estado operacional. **Hard stop:** não rodar se L1 ativo; restore sempre.
- **Sobrecarga TradingView/CDP** (muitos set_TF/screenshot) → throttle, poucos TFs, on-demand.
- **Vision lê UI errado** (labels sobrepostos, drawings deslocados — visto agora) → cross-check RAW obrigatório; descartar leitura divergente.
- **Confundir imagem com verdade estatística** → todo output marcado VISUAL_CONTEXT, nunca "validação".
- **Daemon prematuro / complexidade** → começar on-demand, 1 símbolo, 3 TFs.
- **Orphan server.js / processo chart** → cleanup + health antes/depois.

## 15. Implementação mínima sugerida (NÃO executar agora)

**v0 (on-demand, sem daemon):** 1 símbolo (XAU), 3 TFs (1D/4H/1H), trigger manual. Fluxo: Safety Guard → (se L1 idle) lock+restore → 3 screenshots full-res + sidecar + RAW → Visual Reader produz `visual_summary.md` + `episode_labels.csv` com o checklist §9 → fila de revisão. **Sem scheduler, sem Telegram, sem decisão de trade.** ~1 script + 1 doc de checklist. Implementação **só após autorização** e via Plan agent (regra CLAUDE.md para mudança arquitetural).

## 16. Próximo bloco recomendado (somente se autorizado)

"**v0 Visual Collector + Reader (on-demand, 3 TFs, sem daemon)**" — implementar o Safety Guard + Screenshot Collector + Visual Reader sobre XAU 1D/4H/1H, validando lock/restore e cross-check RAW num único ciclo manual, sem tocar produção. Pré-requisito: confirmação de que a L1 pode ser observada/janela-de-idle, ou criação de uma aba/layout TradingView dedicada.

---

## DA appendix

- Não implementou nada? ✅ design-only.
- Não tocou MCP/chart (write)? ✅ (só `launchctl` read-only para ancorar a §11).
- Não criou daemon/scheduler? ✅. Não tocou broker/L1/pause? ✅.
- Não prometeu validação por screenshot? ✅ (explicitamente VISUAL_CONTEXT, não backtest).
- Separou contexto visual de validação estatística? ✅ §12/§13/§14.
- Arquitetura simples para começar? ✅ v0 = 1 símbolo, 3 TFs, on-demand, sem daemon.
- Próximo passo depende de autorização? ✅ §16.
- Restrição central (chart compartilhado com L1) endereçada? ✅ §1/§6/§11/§14.

**DA verdict: PASS — documento de arquitetura entregue; restrição de chart-compartilhado-com-L1 é o eixo do design; visual tratado como Human-Review Intelligence, não motor de trade; v0 mínima proposta sem executar; nada tocado.**

---

*Design/consultation only. Nenhuma execução, nenhum chart write, nenhum daemon. Produção intacta. Implementação futura via Plan agent + autorização explícita.*

# MAPA FUNDAMENTADO — Sistema de leitura live (2026-07-24)

Verificado por leitura de código + estado vivo (não suposição). Motivo: agi (tunei `classify_zone`) sem primeiro
perceber a natureza do sistema — o padrão recorrente que o Cris teme. Este mapa é a imagem partilhada ANTES de
qualquer decisão de consolidação.

## 1. O pipeline de leitura sancionado: E0 → E1 → E2

**E0 (`alert-bridge/context_engine.py`, daemon `context-engine`, VIVO)** — compõe o dossiê `market_context.json`.
Corre os readers (mtf, micro, macro, confluence, magnets), monta-os em **vozes descritivas**. Regime = 2 vozes
convergentes (v5-4H + Layer1-1D) *"NÃO é veto, compõem UMA imagem"*. **Não decide, não emite.**

**E1 (`e1_detector.py`, daemon `e1-detector`, VIVO — 2153 candidatos, último 15:46)** — 6 gatilhos estruturais que
ecoam os engines aprovados: R1 sweep+reclaim · R3 CHoCH · R4 zone_reject · R5 **ema_reclaim (leg-bottom/top + EMA21,
pos_in_leg freshness)** · R6 macro_event. Gera candidatos com entry/SL/target/RR (SL 15M-local, alvo cap 3-5R).
🔑 **A `confluence_score` (mtf_align/zona/auction/momentum/svp/macro) é CALCULADA mas DESCRITIVA — voz p/ E2, NÃO
gate** (des-enviesamento E1_E2_DEBIAS 2026-07-18: *"mtf_align+svp_htf eram agreement de regime a decapitar
reversões"*). SHADOW (0 Telegram), permissivo/recall-alto — a precisão é do E2.

**E2 (`e2_quality.py`, daemon `e2-quality`, VIVO — 25 reads + 42 verdicts) — SHADOW: 0 Telegram.** Dois passos:
(1) gate causal duro (3 vetos: bad_rr/chase/stale); (2) **UM read contextual Opus da IMAGEM COMPOSTA COMPLETA**
(`render_composite` = dossiê inteiro como briefing top-down). System-prompt: *"És UM olhar a ler o TODO… não há
tabela de pontos a somar… o regime é UMA leitura entre várias, não default direcional… convergência = as leituras
apontam para o mesmo lado e encadeiam uma causa."* Teses guardadas verbatim em `e2_shadow.jsonl`; outcome
backfilled dias depois. **Árbitro = shadow multi-dia NÃO-VISTO (nunca afinar ao dia visível).**

## 2. O caminho PARALELO (onde eu me desviei)

**price-shock (`price_shock_cycle.py`, daemon `price-shock`, VIVO — dispara Telegram)** — lê o E0, deteta choque
por excursão + toque em zona OB 15M, e decide via `classify_zone` = **aritmética** (perna + regra-zona + contagem
de suportes + limiar FORTE/FRACO). **NÃO alimenta o E1.** É um segundo caminho de decisão, mecânico, a alertar live
— enquanto o read sancionado (E2) que faz o juízo CERTO (convergência) está em shadow. Passei a sessão a afiar este.

## 3. De onde vêm os alertas Telegram HOJE
price-shock (mecânico), L1/L2/Cp (estratégias aprovadas), AMD. **NÃO do E2** (shadow). Ou seja: o read de
convergência sancionado **não fala contigo**; o mecânico fala.

---

## RESPOSTAS ÀS PERGUNTAS DO CRIS

### Q1 — Como integrar a lógica de legs/zonas ao que existe, e como muda FRACO/FORTE?
A lógica **já existe** no E1 (R5 ema_reclaim = leg-bottom/top+EMA21+pos_in_leg; R4 zone_reject; R1 sweep+reclaim) e
no E0 (mtf leg/swings/pos_in_leg por TF). O meu `_leg_1h` é uma **reimplementação**. Integração correta:
- Se o **toque-em-zona** do price-shock é um gatilho que o E1 não tem (E1 espera reject/reclaim confirmado; o
  price-shock apanha o toque + choque, mais cedo), **adiciona-se como 7º gatilho no `detect()` do E1** — um
  candidato, não um classificador.
- **FRACO/FORTE deixa de ser aritmética e passa a ser o veredicto do E2:** FORTE ↔ convergência alta/conviction;
  FRACO ↔ low/incoherent. A perna-1H torna-se **UMA leitura na imagem composta que o E2 já lê** (secção ESTRUTURA
  MTF), lida em contexto — não um gate mecânico. O achado do cruzamento (perna-alignment separa) entra como
  **contexto do read**, não como score.

### Q2 — Guards: como voltou a ocorrer? O que falta?
O `consolidation_guard` valida o **input** ("consome o E0?") — o `classify_zone` consome, logo passou. **Ponto cego:
não valida o PAPEL do output** (é um classificador de decisão/qualidade que duplica o E2?) nem conhece que "o read
sancionado é o E2". Além disso eu **editei** um ficheiro existente (não criei fresco), por isso a heurística de
"reader paralelo novo" não disparou. O que falta (implementável): um CHECK que dispare ao escrever/editar
**aritmética de qualidade** (`FORTE|FRACO|classify|score|supports|conviction`) e redirija ao E2/E1. Mas — honesto —
um guard-regex **interrompe**, não substitui entendimento. O fix durável = (a) este mapa como doc canónico de
bootstrap; (b) guard que force lê-lo antes de tocar em código de sinal/qualidade; (c) o check FORTE/FRACO→E2.
**Não é impossível; é interromper no momento certo + ter o mapa. Nenhum guard sozinho garante — a disciplina de
bootstrap é o que faltou.**

### Q3 — Porquê em SHADOW se autorizaste o sistema completo live? Como ativar sem errar?
E1/E2 estão em shadow **por design** (código + memória `project_camada2_e2_convergence_read`): o árbitro é
**forward multi-dia NÃO-VISTO** (anti-overfit; limiares "a calibrar no shadow, não fixar a hoje"). O E2 lê+arquiva
(`e2_shadow.jsonl`), com outcome backfilled dias depois. Pendente: **backfill + painel** de performance. **A lacuna
real:** a STACK (L1/L2/Cp/AMD/price-shock) foi live, mas o **READ de convergência ficou em shadow** — e isso não te
foi bem sinalizado. Para ativar sem errar: (1) rever os reads shadow acumulados (25 reads + verdicts + outcomes
backfilled) — o read converge bem no forward-não-visto? (2) se sim, **ligar o E2 a emitir Telegram** e **aposentar
o `classify_zone` do price-shock** (o price-shock vira só gatilho→E1); (3) o read passa a ser o **único alertador
sancionado**. "Nunca mais errar" = o read (convergência) alerta, não a aritmética; e a ativação respeita o
forward-não-visto (ativar cedo = o overfit que o shadow evita).

## 4. Decisão de consolidação (para o Cris)
- **A:** price-shock deixa de ter `classify_zone`; o toque-em-zona/choque vira gatilho no E1; o juízo é do E2; ativa-se o E2 a emitir Telegram após rever o shadow. **(consolidação no sancionado)**
- **B:** mantém-se price-shock mecânico como alerta-rápido de baixa-confiança E ativa-se o E2 como read de alta-confiança em paralelo (dois níveis explícitos).
- **C:** primeiro revê-se o shadow do E2 (performance forward) antes de decidir A/B.

Recomendação: **C → depois A.** Não construo nada até decidires.

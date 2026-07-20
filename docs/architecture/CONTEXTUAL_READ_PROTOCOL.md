# CONTEXTUAL READ PROTOCOL (CRP) — leitura contextual fixa de TODOS os indicadores

**Cris 2026-07-20.** Resolve a bagunça: eu lia indicadores ad-hoc (por enquadramento/memória), subconjunto
inconsistente, e enchia o vazio com invenção (BB próprio, zona à mão) quando o indicador real já estava no
store. Este protocolo remove essa liberdade. **Organizado, metódico, simples, definitivo.**

## A REGRA (uma frase)
Antes de QUALQUER trabalho de contexto/zona/nível/análise/decisão de mercado, corro **UMA** leitura completa —
`my-strategy/core/contextual_read.py` — que carrega **TODOS** os indicadores do store. **Nunca subconjunto
ad-hoc. Nunca inventar um proxy.** Se um indicador falta ao que preciso, leio-o via MCP (`data_get_pine_boxes`
/ `data_get_study_values` / `chart_scroll_to_date` para dias anteriores) — nunca computo um substituto.

## QUANDO (gatilhos — obrigatório correr o CRP antes)
- "o que está no chart / onde estão as zonas / níveis / suporte-resistência"
- qualquer análise MTF / relatório / avaliação de trade
- desenhar no chart · definir zona/íman/entry/SL/TP
- qualquer decisão/skip de estratégia · responder ao Cris sobre contexto de mercado
- antes de dizer "não existe" um dado (primeiro CRP, depois MCP scroll-back, só então "não existe")

## O QUE (inventário FIXO — o que o chart/store têm; ler SEMPRE tudo)
Por TF **1D · 4H · 1H · 15M · 5M**:
- **ZONAS (`pine_boxes`):** **Custom OB Detector v11** (zona principal de supply/demand, persiste multi-dia) ·
  **Smart Money Concepts** · **HTF Power of Three** · **Sessions [LuxAlgo]**.
- **VALORES (`study_values`):** **RSI (+MA)** · **DMI (ADX/+DI/-DI)** · **SVP (Up/Down/Total)** ·
  **NAS (RSI/dist-EMA/sinais)** · **Market Order Bubbles** · **Choppiness** · **Volume** · **SMC PlotCandle**.

## COMO (fonte única)
- `python3 my-strategy/core/contextual_read.py` — lê o store (`pine_boxes_*` + `study_values_*` + `bars_*`),
  zero MCP, vista organizada por TF com cada zona marcada vs preço (◄PREÇO / ↑acima / ↓abaixo).
- Dias anteriores / verificação viva → MCP (`chart_scroll_to_date` + `data_get_pine_boxes`). As zonas do OB
  Detector **persistem** — a zona de há dias ainda está no chart, sem desculpa de "só tenho agora".

## ENFORCEMENT (garantia, não promessa)
- **Zona/nível SÓ vem do OB Detector/SMC/SVP** (lidos). Computar BB/banda/std-dev própria ou hardcodar um
  nível de preço = **PROIBIDO**. Tripwire `scripts/safety/check_no_invented_zones.py` (a afinar) apanha o padrão.
- Memória permanente [[feedback_never_invent_read_existing_indicator]] (carrega toda sessão).

## Estado
Leitor `contextual_read.py` = FEITO e testado (mostra OB Detector + tudo). Protocolo = DEFINIDO.
Pendente (limpeza, não novo): remover funções mortas `check_bb15m`/`check_zones` do price-shock · afinar a
tripwire (falsos-positivos em código aprovado: L2 pstdev de normalização, e1 COLLAPSE_S=3600s).

# DETETOR DE DISTRIBUIÇÃO DE TOPO — PROPOSTA V3 (literatura × features existentes)
Data: 2026-08-28 · Ordem Cris: "estudar na web fontes confiáveis... proposta profunda e mensurável,
quantificada com nossas lógicas de leitura estrutural + indicadores contextualizados."
Estado: PROPOSTA para aprovação — NADA implementado, NADA preregistado ainda.
Antecedente: V15/V1H (minha regra rasteira) reprovada — estudo em results_v2_summary.json.

## 1. O que a literatura diz que É distribuição de topo (quantificável)

WYCKOFF (StockCharts ChartSchool — canónico): distribuição = RANGE no topo com eventos ordenados:
BC (clímax de compra: spread largo+volume climático) → AR (queda automática que define o fundo do range)
→ ST (retestes do topo com volume/spread DECRESCENTES) → UT/UTAD (fura o topo e fecha de volta DENTRO
= bull trap) → SOW (quebra o fundo do range com spread+volume EXPANDIDOS) → LPSY (rally fraco que
falha abaixo do topo = lower high). Discriminador vs consolidação: volume CAI nos rallies e SOBE nas
quedas dentro do range. Sem SOW não é distribuição — é só consolidação.

VSA (Tom Williams): barras mecânicas — no-demand (sobe com volume < 2 barras anteriores e spread
estreito), upthrust (novo máximo, fecho no terço inferior, volume alto), effort-vs-result (volume alto
sem avanço de preço = absorção). Única hard-rule canónica: volume < das 2 barras anteriores.

MARKET/VOLUME PROFILE (Dalton): topo em distribuição = poor high (≥2 TPOs no máximo exato, sem cauda
de rejeição) + VALUE A MIGRAR PARA BAIXO (POC/VAH/VAL de cada sessão a construir mais baixo sob o
máximo) + P-shape que falha → b-shape. Aceitação a descer sob um high = distribuição.

SMC (LuxAlgo/ICT, mecânico): sweeps REPETIDOS de buyside sem displacement de continuação = absorção;
CHoCH interno antes do externo; OBs bearish não-mitigados a empilhar acima; preço em premium do range.

ACADÉMICO: LPPLS (Sornette) previu o topo do OURO 2011 com meses de antecedência (arxiv 1012.4118) —
só close diário, aplicável ao nosso 1D como flag macro. OBV/divergência: evidência fraca. TD Sequential:
não validado. (Descartados da proposta principal.)

## 2. Convergência das 4 escolas (é isto que dá confiança na estrutura)
Todas descrevem O MESMO processo por ângulos diferentes:
- fura máximos mas não segura (UT/UTAD = upthrust VSA = sweep-sem-displacement SMC = poor high Dalton);
- esforço sem resultado nos rallies (volume decrescente nos ST = no-demand = effort-vs-result);
- aceitação desce sob o máximo (value migration = LPSY lower highs = OB supply a empilhar);
- confirmação = quebra do fundo do range com força (SOW = CHoCH/BOS down = b-shape).
A minha V1 falhada media SÓ o 1º ângulo, sem volume, sem range, sem fases — por isso era rasteira.

## 3. Mapeamento evento-da-literatura → feature JÁ PRONTA no nosso stack

UT/UTAD (fura e fecha dentro):
  · sweep_reject_guard (LIVE): pavio 4H >50% corpo = já é um detetor de upthrust 4H.
  · AMD F1 (LIVE): sweep+reclaim de PDH/PWH com rejeição decisiva (wick, close_pos) = UTAD mecânico.
  · liquidity_map (LIVE): pool BSL com status CAPTURADA:SWEEP = captura sem run, por pool D/4H/1H.
ST com volume decrescente / no-demand / effort-vs-result:
  · VRVP Up/Down/Total nos study_values (5/15/60/240/1D, LIVE) = volume por janela visível;
  · Session Volume Profile 15M (LIVE). Sem volume por barra no store — usar Δ dos perfis entre reads
    OU adicionar campo volume ao bar_store (o TV tem; decisão de coleta, não invenção).
Range de distribuição (BC→AR define topo/fundo):
  · context_structure.leg (LIVE): perna 1H/4H com pos_in_leg; topo da perna + lateralização = range.
  · EQH do SMC (LIVE, 15/60/240/1D): máximos iguais = topo do range testado.
Value migration / aceitação a descer:
  · SVP Levels POC/VAH/VAL (LIVE, todos os TFs): série temporal do POC/VA por sessão — POC de hoje
    < POC de ontem sob o mesmo máximo = migração para baixo, medível direto do indicador.
LPSY / lower highs pós-quebra:
  · smc_labels CHoCH/BOS down (LIVE) + fractals do context_structure.
Supply a empilhar acima:
  · pine_boxes OB v11 + SMC supply zones (LIVE): contagem de OBs bearish não-mitigados acima do preço.
Premium do range:
  · calculável do leg (equilibrium 50%).
Exaustão auxiliar: NAS_TOP_SIGNAL, RSI vs RSI-MA, price_shock MAJOR no topo (todos LIVE).
Macro: LPPLS sobre bars_1d (research futura separada, não entra no detetor tático).

## 4. A proposta: DISTRIB SCORE por FASES (não flag binária de janela fixa)
Máquina de estados sobre o topo da perna 4H/1H ativa (não janela de N barras — corrige o defeito
do weekend por construção, porque as fases são ancoradas a EVENTOS, não a horas):

FASE A — TOPO CANDIDATO: preço no terço superior da perna 4H (pos_in_leg ≥ 0.67) E pelo menos um de:
  BSL D/4H relevante ≤ 1 ATR acima OU EQH 60/240 formado OU OB supply não-mitigado ≤ 1 ATR acima.
FASE B — TESTE SEM ACEITAÇÃO (acumula pontos, cada um lido de indicador existente):
  +1 por pool BSL → CAPTURADA:SWEEP (liquidity_map) no topo candidato (máx 2);
  +1 sweep_reject 4H armado (guard existente) ou AMD F1 short armado no mesmo topo;
  +1 volume dos rallies a cair: Up/Total do VRVP no reteste < no impulso anterior (no-demand);
  +1 POC/VAH da sessão a construir ABAIXO da sessão anterior sob o mesmo máximo (value migration);
  +1 CHoCH interno 15M down no topo (smc_labels 15) com estrutura 60 ainda intacta (interno antes do externo).
FASE C — CONFIRMAÇÃO (SOW): CHoCH/BOS down 60 ou 240 (smc_labels/choch axes) — aqui o choch_guard
  atual JÁ atua; o novo detetor cobre exatamente o buraco A→C que esta semana explorou.
SAÍDA/RESET: aceitação acima (fecho 4H acima do topo + displacement ≥ 0.5 ATR) OU nova perna de alta.

Uso proposto (se aprovado e SE o estudo validar): score ≥ limiar em FASE B = contexto DISTRIB ativo →
suprime/etiqueta compras de pullback A1/A2/AMD-long até reset ou até SOW. Limiar NÃO escolhido agora —
é o objeto do estudo (curva score×resultado, sem afinar ao dia visível).

## 5. Validação proposta (prereg separado, só após aprovação do desenho)
- Reconstrução causal do score sobre o histórico (RAW canónico + registry as-of dos indicadores; onde o
  indicador histórico não existe no RAW, o componente fica fora do backtest e só entra em forward —
  declarado, sem re-derivar à mão: Regra C).
- Split dos sinais LONG do censo real por score na entrada; painel completo por nível de score; null
  block-shuffle sobre avgR (lucro); semestres+jackknife; semana 24-28/08 descritiva (não pontua).
- Gates de leitura como referência, veredito = Cris (adenda já em vigor).
- Se suportado: shadow forward com critério de sucesso pré-definido ANTES de ligar a qualquer emissor.

## 6. Decisões que só o Cris pode tomar
D1. Aprovar/editar o desenho por fases e os 5 componentes do score (secção 4).
D2. Volume: aceitar proxy VRVP/SVP entre reads, ou mandar adicionar volume por barra ao bar_store
    (coleta nova, mexe no store — só com ordem).
D3. Backtest limitado aos componentes com histórico as-of no RAW vs forward-only para os restantes.
D4. LPPLS 1D como research macro separada: quer ou não.

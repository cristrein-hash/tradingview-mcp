# SPEC — LÓGICA DE ENTRY 15M LONG (Cris, 2026-07-10)

> Base: detector v2 sem filtro de autoridade (32/42 cobertos; commit d9493b5).
> **A entry não nasce do "sinal". Nasce da RELAÇÃO entre preço e região.**
> STATUS: `SPEC_ONLY_NOT_IMPLEMENTED`. Sem backtest, sem produção.

## Uso correto do detector
O detector só responde: **onde** existe demanda válida · **qual tipo** de demanda é · **quando** a
região ficou conhecida · se ainda é válida. **Ele não compra.**

## Entry contextual correta (sequência obrigatória, DEPOIS da região conhecida)
1. Preço **volta** à região válida (reteste).
2. Região é **defendida**.
3. Reação mostra **mudança real de comportamento**.
4. Entrada ocorre no **reteste/reclaim após defesa**.

NUNCA: no candle que cria a região · no rompimento · no primeiro bounce cego.

## Por família

### BULL pullback
- **Entry boa**: pullback proporcional · toca/defende demanda válida · não está no topo esticado ·
  reclaim após defesa.
- **Evitar**: micro pullback alto · compra no topo da perna · reclaim sem limpeza do excesso.

### RANGE
- **Entry boa**: somente fundo real do range · toque na base · defesa clara · entrada no reclaim
  da base.
- **Evitar**: meio do range · topo do range · zona velha sem autoridade.

### BEAR capitulação
- **Entry boa**: capitulação profunda · perna bear deixa de pressionar · bounce raso já falhou
  antes · região nasce do flush ou reteste terminal · entrada só no reteste/reclaim depois da
  capitulação.
- **Evitar**: repique raso · estrutura acima ainda pressionando · S2a/S3 bloqueando.

### PLT / suporte convertido
- **Entry boa**: zona rompida · aceitação acima · reteste posterior · defesa da zona · reclaim
  após defesa.
- **Evitar**: comprar o rompimento · comprar a confirmação · usar PLT como explicação universal.

## Fórmula
**REGIÃO válida + CONTEXTO correto + RETESTE + DEFESA + RECLAIM = entry candidata.**
Se faltar uma parte: **sem entry.**

## Ponto principal
O detector encontra **onde** o trade poderia existir. A entry decide **quando** o mercado confirmou
que aquela região está viva. Esse é o caminho causal correto.

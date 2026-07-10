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

## Definições operacionais (Cris, 2026-07-10 — respostas às 5 perguntas)

### 1. DEFESA
Não é "tocou e pronto". Defesa = preço entra/toca a região · **não fecha rompendo a região com
força** · fecha **dentro ou acima** da região. Leitura simples: **tocou a demanda e não aceitou
abaixo**. Uma barra pode bastar, desde que não seja rompimento claro. Não exigir várias barras
no início.

### 2. RECLAIM
Não é só "fechou verde". Reclaim = **após defender a região**, fecha **acima do topo da barra de
defesa OU acima do topo da região**. Ordem obrigatória: **defesa primeiro, reclaim depois**.
Não comprar o primeiro toque.

### 3. Mudança real de comportamento
NÃO mecanizar demais por enquanto. Mecânica mínima: parou de fazer low novo · defendeu a região ·
fez fechamento de retomada. "Mudança real" fica como **leitura do Reader**, não regra dura final.

### 4. Entry / SL / alvo
- entry = **fechamento da barra de reclaim**
- SL = **piso da região − 0,1·ATR**
- alvo inicial = **3R**
- **Cuidado**: região larga demais → SL pesado → marcar como **RISCO_RUIM**, não forçar entrada.

### 5. Topo esticado / D2
D2 **NÃO** é filtro universal. Uso correto: veto contextual **em BULL**, quando a entrada está no
**topo/alto da estrutura SEM pullback proporcional**. Não usar D2 para bloquear todo BULL alto.

### Resumo final (Cris)
Entry correta = **toque na região + defesa + reclaim**. Não compra rompimento. Não compra
confirmação da região. Não compra primeiro bounce. D2 só veta compra de topo sem pullback
suficiente.

## ORDEM DE LEITURA OBRIGATÓRIA (Cris, 2026-07-10 — correção à Etapa 1)

**ERRO a evitar**: a máquina perguntar "houve reclaim?" ANTES de perguntar "que tipo de fundo é
este?". Sequência mecânica reteste→defesa→reclaim sozinha NÃO lê contexto e repete erro antigo.

Ordem correta:
1. **Qual família estrutural?**
2. **A região é válida para essa família?**
3. **O movimento até ela faz sentido?**
4. **O preço está corrigindo, capitulando ou só repicando?**
5. **Só então** observar defesa/reclaim.

**Defesa/reclaim são GATILHOS FINAIS, não a lógica da entry.
A lógica da entry é CONTEXTO + FAMÍLIA + POSIÇÃO + REAÇÃO.**

# 03 — Backtest Validation Protocol

## Objetivo

Definir o protocolo obrigatório para qualquer backtest, revalidation, recalibração ou análise estratégica dentro do projeto Trading System.

## Regra central

**Nenhum backtest sério sem RAW, gate manifest e sanity check.**

Backtest não é geração de tabela. Backtest é validação de hipótese com fonte rastreável e semântica correta.

## Níveis de análise

### 1. Screening

Permitido com dados derivados se autorizado.

Uso:

- gerar ideias;
- procurar frequência;
- detectar possíveis padrões;
- levantar hipóteses.

Status:

**EXPLORATORY ONLY**

### 2. Research Backtest

Exige RAW/source trace e sanity checks.

Uso:

- medir uma hipótese definida;
- comparar versões;
- estudar regime;
- preparar visual review.

Status:

**RESEARCH / NOT VALIDATED**

### 3. Revalidation Candidate

Exige:

- RAW backtest;
- visual review;
- walk-forward;
- sensibilidade;
- slippage/cost review;
- documentação.

Status:

**ACTIVE_CANDIDATE**

### 4. Validated

Exige aprovação explícita do usuário, OOS/shadow/paper ou evidência operacional suficiente.

Status:

**VALIDATED**

## Passo 0 — Confirmar escopo

Antes de rodar qualquer coisa, responder internamente:

- Qual estratégia/hipótese?
- Qual timeframe?
- Qual ativo?
- Qual período?
- Qual fonte de dados?
- Qual output?
- O que NÃO será feito?

Se houver ambiguidade, perguntar.

## Passo 1 — Gate Manifest

Todo backtest precisa declarar gates em linguagem natural e código/pseudocódigo.

Exemplo:

```text
Gate 1: vela 1H bullish reclaim
Gate 2: RSI < 50
Gate 3: SELL bubbles >= 20 em 50 velas
Gate 4: large SELL bubbles >= 2
Gate 5: CHoCH/BOS swing entre 20 e 30 velas anteriores
Gate 6: NAS LONG recente em até 5 velas
```

Depois declarar os predicados exatos:

```python
prev_close < prev_open
close > open
high > prev_open
rsi < 50
sell_bubble_count_50 >= 20
large_sell_count_50 >= 2
```

## Passo 2 — Nome não é definição

Se o usuário disser “voltar ao original” ou citar uma variante, verificar:

- definição textual do usuário;
- definição interna do código;
- gates reais implementados.

Se houver divergência, parar e perguntar.

## Passo 3 — Fonte de dados

Backtests sérios devem usar RAW.

O manifest deve listar:

- path dos RAW files;
- timeframe;
- período;
- indicador fonte;
- extractor/schema se houver;
- campos usados.

SLIM-only não é permitido para validação.

## Passo 4 — Sanity checks

Antes de rodar o dataset inteiro, validar exemplos pequenos:

- 1 exemplo que deve passar;
- 1 exemplo que deve falhar;
- 1 exemplo borderline;
- 1 winner visual conhecido, se houver;
- 1 loser visual conhecido, se houver.

Para cada exemplo:

- timestamp;
- campos usados;
- gates pass/fail;
- motivo.

## Passo 5 — Execução read-only

Toda primeira rodada deve ser read-only:

- sem alteração em repo;
- sem produção;
- sem catalog;
- sem monitor;
- sem strategy_rules;
- sem outcomes;
- sem push;
- sem PDF, salvo pedido explícito.

Outputs temporários em `/tmp`.

## Passo 6 — Métricas mínimas

Relatório curto deve conter:

- n trades;
- n eventos, se aplicável;
- win rate;
- total R;
- avg R;
- PF;
- MFE/MAE;
- hit 1R/2R/3R/5R/10R/20R;
- max losing streak;
- noTop1/noTop3/noTop5/noTop10;
- resultado por período/regime;
- drawdown aproximado se disponível.

## Passo 7 — Event-level quando necessário

Se múltiplos trades ocorrem no mesmo movimento/região, não tratar como oportunidades independentes.

Mas nunca apagar candidatos internos sem análise.

Modelo correto:

```text
1 evento
→ múltiplos candidatos internos
→ escolher policy sem hindsight
→ preservar análise dos candidatos alternativos
```

Distinguir:

- duplicata literal: mesmo timestamp, entry, stop, risk;
- candidato alternativo: entry/stop/risk diferentes.

Candidatos alternativos não devem ser descartados automaticamente.

## Passo 8 — Visual review

Backtest não valida Auction Theory sozinho.

Visual review deve responder:

- o trade parece coerente com a tese?
- entrada é cedo, correta ou tarde?
- zona é real?
- pressão foi absorvida ou continua ativa?
- SMC/NAS/Bubbles/RSI aparecem como no dado?
- stop faz sentido?
- target é realista?

## Passo 9 — Walk-forward e sensibilidade

Antes de qualquer promoção:

- dividir por tempo;
- dividir por regime;
- testar thresholds próximos;
- verificar se edge depende de 1–3 trades;
- medir noTopN;
- revisar slippage/custos.

## Passo 10 — Status final

Nenhum backtest sai diretamente para produção.

Estados possíveis:

- EXPLORATORY
- SUSPECT
- RESEARCH
- ACTIVE_CANDIDATE
- REJECTED
- VALIDATED

Promoção exige autorização explícita do usuário.

## Relatório padrão curto

Usar este formato:

```text
PASS/FAIL:
Fonte:
Gates:
n:
Métricas principais:
Achado:
Limitações:
Próxima menor ação:
Não feito:
```

## Regra final

Se a semântica do indicador importa, o backtest precisa provar que está lendo o indicador certo do jeito certo. Caso contrário, os números não significam validação.

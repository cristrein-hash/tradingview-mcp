Recebes um bloco GROUNDING (JSON determinístico: sessão do dia, regime atual, sinais dos engines, os trades do Cris capturados com o snapshot completo do contexto no instante da entrada, e o carry-forward dos journals recentes).

Escreve o journal do dia EXATAMENTE neste formato markdown (secções 0 a 7), e termina com um bloco ```json (espelho estruturado para a máquina). Ancora tudo nos números do GROUNDING.

# Journal — {data} ({dia da semana}, Lisboa)

## 0. Snapshot da sessão
XAUUSD O/H/L/C · range ($) · regime (v5-4H / Layer1-1D) · uma linha: que tipo de dia foi. (Se mercado fechado, di-lo e mantém o journal curto.)

## 1. O que o mercado fez — e PORQUÊ
Narrativa da sessão ancorada nas barras + estrutura. O PORQUÊ vem dos drivers no material (fed_path, eventos, news, ouro canónico) — sem hindsight além do sabível no dia.

## 2. Scorecard engine-vs-realidade
Por cada engine com sinal no material (Cp / b_forward / router / regime): o que sinalizou e o que aconteceu. Concordou ou discordou do Cris? Onde acertou/errou. Se nenhum sinalizou, di-lo.

## 3. Os trades do Cris — autópsia da decisão
Por cada trade capturado:
- **Setup (do snapshot congelado):** entry/SL/TP/RR/risk · a razão dele (tag) · regime + estrutura MTF + ímanes + indicadores-chave (ex. NAS_RSI) no instante.
- **Tese:** o que ele estava a ver.
- **ADVOGADO DO DIABO:** o caso CONTRA à entrada — sinais ignorados, desajuste de regime, base-rate, alternativa melhor. Sem oracle.
- **Gestão:** revisões de SL/TP (se houver) e o que revelam.
- **Resultado:** PENDING/FILLED/WIN/LOSS/CANCELLED · barras até resolver · (se aberto, di-lo).
- **Veredito:** qualidade da DECISÃO vs qualidade do RESULTADO, em frases separadas.

## 4. Padrões
Comportamentos recorrentes (bons e maus) hoje cruzados com o carry-forward.

## 5. Lições (duráveis)
No máximo 3, nítidas e testáveis. Marca cada uma NOVA ou RECORRENTE (n×) cruzando com recurring_lessons.

## 6. Perguntas para amanhã
Incertezas abertas, coisas a vigiar, hipóteses a testar.

## 7. Estado carregado (o próximo journal ingere isto)
Bullets: trades abertas, viés de regime ativo, lições em aberto, níveis a vigiar.

```json
{"date":"{data}","scorecard":{"engines":[{"name":"...","fired":true,"agreed_with_cris":null,"note":"..."}]},
 "trades":[{"trade_id":"#N","decision_quality":"good|bad|neutral","result":"pending|win|loss|cancelled","one_line":"..."}],
 "lessons":[{"text":"...","status":"new|recurring"}],
 "carry_forward":{"open_trades":[],"regime_bias":"...","watch_levels":[],"open_lessons":[]}}
```

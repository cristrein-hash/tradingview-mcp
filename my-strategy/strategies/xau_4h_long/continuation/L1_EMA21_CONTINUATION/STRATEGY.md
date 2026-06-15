# XAU 4H LONG — CONTINUATION
## L1 · EMA21 CONTINUATION

## Status
- **USER_APPROVED_FINAL**
- **HUMAN_DISCRETIONARY**
- **CONTINUATION**
- Não é fully mechanical. Não executa automaticamente. Exige confirmação humana.

---

## O que a estratégia faz (linguagem simples)
Procura **continuações de alta** no ouro (XAUUSD) no gráfico de 4 horas, dentro de uma
tendência de alta já estabelecida. A ideia é entrar comprado quando o preço **respira e
retoma** a tendência de forma calma (sem clímax de volume, sem exaustão), apoiado na EMA21
sobre a SMA50 e numa zona de demanda (Custom OB).

Um **scanner / base rule** gera o **candidato**. A **decisão final é humana**: o operador
olha o gráfico e confirma. Não é um robô — é um assistente que aponta o setup e sinaliza
quando provável exaustão deve fazer **bloquear ou revisar** a entrada.

---

## Base rule (resumida)
- Ativo / TF: **XAUUSD 4H, LONG**.
- Regime macro **D-1 = BULL** (regime_B_v3, consultado no dia anterior — causal, SHIFT1).
- `close > EMA21 > SMA50` com **slopes** de EMA21/SMA50 positivos (continuação, não fundo).
- **BOS causal** (estrutura de alta confirmada por barras já fechadas).
- Toque em **zona de demanda Custom OB v11**.
- `body_pct ≥ 0.35` (barra com corpo, não doji).
- **F5 / volume quiet continuation:** `vol_ratio_med50 ≤ 1.0` (volume calmo, não clímax).
- **Stop estrutural LONGO preservado** (conforme `rebuild_v3` — Cris aprovou o respiro;
  o `R_CEIL 1.5ATR` foi removido, que era o real conserto da reconstrução). Slippage 0.1R.
- Exit **V_stair_A** (BE@+2R → degraus até +20R, time_stop 60 barras).

Princípio anti-lookahead: **close-only-causal**. Toda feature usa apenas barras já fechadas;
indicadores que repintam (OB/SMC) usam SHIFT1.

---

## Regra final de BLOCK / REVIEW (aprovada)
```
BLOCK / REVIEW  if  vol_entry_z >= 1.993  OR  rsi_vs_ma <= -9.35
```
- `vol_entry_z` = z-score do volume da barra de entrada vs média móvel de 50 barras.
  ≥1.993 = entrada em **barra de clímax de volume (>2σ)** = blow-off / exaustão.
- `rsi_vs_ma` = RSI menos sua própria MA. ≤ −9.35 = **divergência bearish no topo** da continuação.
- Confirmado **visualmente** pelo usuário como bloqueio de **exaustão real**.
- **Uso human-discretionary:** flag de REVIEW/bloqueio. O operador confirma no chart antes de
  descartar o candidato. Não é gate automático.

---

## Métricas principais — antes / depois da regra (n=38, reconstrução in-sample rebuild_v3)
| | n | WR | sumR | PF | maxDD | losing streak | monumentais |
|---|---|---|---|---|---|---|---|
| **FULL (base rule)** | 38 | 31.6% | 14.9R | 1.76 | 7.9R | 6 | #36 (+9.5R), #38 (+6.53R) |
| **+ regra BLOCK/REVIEW** | 34 | 35.3% | 19.3R | 2.26 | 5.7R | 6 | #36, #38 **preservados** |

- A regra **corta zero winners** e preserva os dois monumentais — verificado na validação
  temporal (terços + por ano): melhora ou não-piora todos os blocos, bloqueia só losers
  (6 trades R≤0 espalhados em 4 anos), streak estável.

---

## Limitações (honestidade obrigatória)
- **Não é fully mechanical** — base rule gera candidato; **decisão final é humana**.
- **Não executar automaticamente.** Sem produção, sem alertas, sem Telegram ligado.
- **Precisa confirmação humana** no chart antes de operar ou descartar.
- **Não é edge auto-validado.** n=38 é reconstrução in-sample; o KEEP rotulado foi marcado
  vendo o resultado (artefato in-sample). A regra de filtro é **PROMISING_BUT_NEEDS_MORE_DATA**:
  os terços de n=38 **não são OOS verdadeiro** (o set que derivou a regra não a valida), e o
  Monte Carlo coloca a contagem de regras limpas no acaso. O que sustenta a regra é
  **causalidade + robustez**, não a estatística de contagem.
- **Telegram será formatado depois** (usando os modelos existentes), nunca antes de autorização.
- **candidate ≠ trade · KEEP ≠ entrada.** Modos de execução/monitoramento (`NONE`/`MANUAL`/`MCP_MONITORED`/`BROKER_AUTHORIZED`) e regras de outcome teórico vs real estão no contrato em `README.md` (Execution / Monitoring Modes). MCP/chart e broker são camadas **autorizadas futuras**, hoje inertes — nada ativado silenciosamente.

---

## Próximos passos futuros (sem ligar produção)
- Integrar o **scanner / base rule** na nova arquitetura (strategy engine), mantendo
  human-in-the-loop.
- **Validação OOS real** com thresholds CONGELADOS como estão: holdout forward **ou**
  cross-asset EUR/USOUSD + mecanismo pré-registrado + ≥8–10 losers novos bloqueados / 0
  winners novos (gate para sair de `PROMISING_BUT_NEEDS_MORE_DATA`).
- **Desenhar o Telegram depois**, reusando modelos de notificação existentes.
- **Não ligar produção sem autorização** explícita do usuário. Permissão de rota só via
  registry, quando houver fluxo seguro.

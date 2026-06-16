# XAU 4H LONG — CONTINUATION
## L1 · EMA21 CONTINUATION

## Status
- **governance_status: USER_APPROVED_FINAL · HUMAN_DISCRETIONARY** (humano autorizou rodar; entrada é decisão humana)
- **evidence_status: NOT_VALIDATED_OOS** (`PROMISING_BUT_NEEDS_MORE_DATA`)
- **CONTINUATION**
- Não é fully mechanical. Não executa automaticamente. Exige confirmação humana.

---

## ⚠️ RECLASSIFICAÇÃO 2026-06-16 (ler primeiro — supersede prosa conflitante abaixo)
Este banner é a **fonte canônica** onde o texto histórico abaixo divergir.

1. **governance ≠ evidence.** A L1 está **operacional por decisão humana** (USER_APPROVED_FINAL, human-discretionary) e por arquitetura segura. Isso **não** significa edge validado. **evidence_status = NOT_VALIDATED_OOS.**
2. **Números antigos são in-sample / research, NÃO prova de edge.** FULL-38, **KEEP-19 (+32.6R)**, terços por ano = reconstruções `NOT_VALIDATION` / rótulo humano (Cris marcou winners olhando o chart). `mechanizable_now=false`, veredito `NEEDS_CAUSAL_FILTER_BEFORE_ANY_CLAIM`. **Não usar esses números como prova de edge.** O gate `rsi_vs_ma≤−9.35` "corta 0 winners" é **seleção in-sample** (threshold tunado sobre os mesmos n=38); os "monumentais" #36 +9.5R / #38 +6.53R **não são ≥20R**.
3. **🔴 REGIME SPLIT-BRAIN.** O `scanner.py` (autoridade da base-rule que gerou os números acima) **ainda gateia em `regime_B_v3`**; o `runtime_xau.py` (caminho LIVE do scheduler) gateia em **`regime_l1_v4`**. São classificadores **diferentes** → **os números in-sample NÃO correspondem ao gate que roda ao vivo** e precisam ser **re-derivados sob `regime_l1_v4`**. `regime_B_v3` está declarado **morto como autoridade** (ver `core/regime_l1/regime_l1_v4.py`); sua presença no scanner é legado pendente de migração, não autoridade atual.
4. **vol_entry_z é HISTÓRICO, não ativo.** O leg `vol_entry_z >= 1.993` foi **removido** (morto sob F5 **e** derivado de matriz bugada). O gate operacional é **RSI-only**. Qualquer texto abaixo que trate o leg de volume como parte ativa está **superseded**.
5. **Base-rule live PENDENTE.** O runtime live confirma regime+RSI gate, mas **ainda não confirma a base-rule estrutural completa** (EMA/SMA/BOS/OB/F5) → marca `needs_base_confirmation` e **não emite `operational_candidate`** ao vivo. A L1 **não é fully mechanized** enquanto isso não existir.
6. **Próximo bloco técnico (toca código — exige autorização):** unificar `scanner.py` + `runtime_xau.py` em `regime_l1_v4`; **re-derivar candidatos/números sob o regime live**; só então planejar gate manifest + RAW OOS.

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
- Regime macro **D-1 = BULL** (causal, SHIFT1). ⚠️ **SPLIT-BRAIN (ver banner):** o `scanner.py` ainda usa `regime_B_v3` (legado, morto como autoridade); o **runtime LIVE usa `regime_l1_v4`**. A autoridade atual é `regime_l1_v4`; números gerados sob `regime_B_v3` precisam re-derivação.
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

## Regra final — GATE de exaustão (RSI-only, AUTOMÁTICO) — decisão do usuário 2026-06-15
```
exhaustion_gate  if  rsi_vs_ma <= -9.35     (AUTOMÁTICO — bloqueia o candidato)
```
- `rsi_vs_ma` = RSI menos sua própria MA. ≤ −9.35 = **divergência bearish no topo** da continuação.
- **É GATE AUTOMÁTICO**, não flag: se `exhaustion_gate=true`, o scanner emite `state=blocked_exhaustion`
  e o candidato **NÃO é operacional** → **não gera candidate notification**.
- **A revisão humana filtra apenas a ENTRADA**, nunca o gate nem o envio do sinal.
- **🔴 Leg de volume REMOVIDO (2026-06-15):** `vol_entry_z>=1.993` foi eliminado por (1) ser artefato
  de uma matriz de análise bugada (auditoria abaixo) e (2) ser estruturalmente morto sob o gate-base F5
  (`vol_ratio_med50<=1.0` ⇒ volume de entrada ≤ mediana ⇒ vol_entry_z sempre negativo ⇒ leg de spike
  nunca dispara). A regra canônica é **RSI-only**.
- Comparação usa valor arredondado exibido: `round(rsi_vs_ma,2) <= -9.35`.
- **Convenção de precisão (2026-06-15):** o flag compara o valor **arredondado** exibido
  (`round(vol_entry_z,3) >= 1.993`, `round(rsi_vs_ma,2) <= -9.35`), fiel à análise aprovada
  (que usou valores arredondados) e garantindo que o flag exibido = flag aplicado. Threshold
  inalterado.

### 🔴 Auditoria 2026-06-15 — autoridade da regra + leg vol_entry_z MORTO

Auditoria read-only de 100% dos 38 candidatos contra RAW/scanner canônico (fonte de verdade), reconciliando contra a matriz `/tmp` antiga (evidência histórica).

- **Autoridade:** a regra é **FLAG human-discretionary de BLOCK/REVIEW, NÃO gate automático** (4 fontes oficiais concordam: STRATEGY/README/scanner/journal). O scanner emite `candidate=bool(passed)` da regra-base; os flags de exaustão são informativos e **não** suprimem o candidato. Comportamento **inalterado** nesta auditoria.
- **🔴 Leg `vol_entry_z>=1.993` é ESTRUTURALMENTE INERTE (morto):** o gate-base **F5 exige `vol_ratio_med50 <= 1.0`** (volume de entrada ≤ mediana). Volume é right-skewed (mean > median) → **todo candidato L1 tem `vol_entry_z < 0` por construção** → o leg de spike `>=1.993` **nunca dispara**. Confirmado: 38/38 candidatos com vol_entry_z negativo no scanner canônico.
- **Causa da divergência #11 (`SAME_TRADE_FIELD_MISMATCH` / `BUG_IN_OLD_ANALYSIS`):** mesmo trade/bar; matriz `/tmp` tinha a coluna `vol_entry_z` BUGADA (35/38 divergentes; #11 matriz=1.993 vs RAW=−0.93; #19 matriz=2.686 vs RAW=−0.38), enquanto `rsi_vs_ma` batia 100%. O scanner está correto; a matriz antiga (origem do leg vol) era inválida. **A regra congelada que "bloqueava #11/#19" via vol_entry_z era artefato da matriz bugada.**
- **Flag operante canônico = `rsi_vs_ma <= -9.35` SOZINHO** → flaga #3, #15, #18, #32 (4 losers, **0 winners**, monumentais #36/#38 preservados). Se aplicado como gate: FULL-38 sumR 14.87→18.27, WR 31.6→35.3%, n→34.
- **DECISÃO PENDENTE do usuário (não alterada unilateralmente):** o leg vol_entry_z está morto e foi derivado de dado bugado → re-validar/re-derivar o flag de exaustão como **rsi_vs_ma-only** sobre dados canônicos, OU manter como está (leg vol inofensivo porque nunca dispara). A regra segue `PROMISING_BUT_NEEDS_MORE_DATA`; esta auditoria reforça que precisa re-derivação canônica antes de qualquer promoção a gate.

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

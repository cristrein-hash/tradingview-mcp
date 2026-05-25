# XAU 30M LONG — Candidate Packet (draft pendente)

**Status:** RESEARCH (pre-CANDIDATE — falta hipótese e critérios)
**Criado:** 2026-05-25 (draft preparado por Claude pra preenchimento por Cris)

⚠️ **Alerta antes de prosseguir:** TF 30M tem evidência mais fraca que TF 15M LONG na auditoria D2R Phase 2. Considerar se vale o investimento de criar agora ou esperar.

---

## Cabeçalho pré-preenchido

```yaml
strategy_id: xauusd_30m_long_<short_name>
display_name: <preencher>
asset: PEPPERSTONE:XAUUSD
base_symbol: XAUUSD
timeframe: 30
direction: LONG
status: RESEARCH
created_at: 2026-05-25
author: Cris+Claude

approved_by: pending
approved_at: null
last_promotion_at: null
last_promotion_to: null
exception_to_pipeline: none
```

---

## ⚡ Slots obrigatórios pra preencher

### 1. Hipótese operacional
*(preencher: 2-3 frases)*

### 2. Critérios objetivos
*(entrada, filtros, invalidação, stop, target — mesmo formato do template padrão)*

### 3. Backtest
*(janela mínima 6 meses ou n=30 trades)*

---

## 📚 Memory scan — contexto e referências (preparado 2026-05-25)

### Evidência D2R Phase 2 sobre TF 30M LONG

Mesma auditoria que validou 15M LONG mostra TF 30M LONG **modesto, não-estrela**:

| TF + Dir | n | avg R | win% | PF |
|---|---|---|---|---|
| TF 4H LONG | 12 | +1.43 | 75% | 9.61 |
| **TF 15M LONG** | 18 | +1.50 | **72%** | 6.38 ⭐ |
| **TF 30M LONG** | **28** | **+0.63** | **50%** | **2.26** |
| TF 1H LONG | 21 | +0.41 | 48% | 1.86 |

PF 2.26 é positivo mas próximo do mínimo (1.2 do pipeline). Win 50% sem expectancy alta significa **margem fina** — qualquer queda no slippage real pode derrubar a estratégia.

### Implicação prática

3 caminhos possíveis (Cris escolhe):

1. **Adiar XAU 30M LONG.** Focar só em 15M onde a evidência D2R é forte (PF 6.38). Voltar a 30M depois que 15M tiver shadow validado.

2. **Construir XAU 30M LONG com gates MAIS restritivos** que 15M, pra elevar expectancy. Ex: exigir confluência multi-TF (regime 1H + 4H alinhados), ou só operar em horários específicos.

3. **Tratar 30M como TF auxiliar** — não estratégia própria, mas filtro pra entradas 15M (ex: "só entra 15M se 30M também confirma").

### Infraestrutura disponível (mesma do 15M)

- Custom OB v12 alertando em 30M
- NAS TopBottom em 30M
- Bubbles 6 alertas em 30M
- RSI bear/bull div + crosses em 30M

---

## Próximo passo

Cris decide: criar XAU 30M LONG agora (com hipótese mais cuidadosa dado evidência fraca) **ou** adiar pra depois de 15M estar em SHADOW validado.

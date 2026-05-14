# XAUUSD 1H Deep Audit — 2026-05-12

## Sample window
- Data: PEPPERSTONE_XAUUSD 1H, 13959 rows, **2024-01-01 → 2026-05-12 (2.36 anos)**
- HTF context: 4H (7.36y), 12H (13.89y), 1D (28.05y) — alinhados via `merge_asof backward`
- DXY filter: NÃO testado nesta rodada (CSV ausente; refinamento futuro)

## Variantes testadas
44 configs = 11 variantes de sinal × 4 targets (2R / 2.5R / 3R / 4R).

Stop = `low − 0.5 × ATR(14)`. BE após +1R. Max hold = 20 candles 1H. Spread = 0.05R.

## TOP 10 (ordenado por total_r_net @ 0.05R spread)

| # | Strategy | n | tpw | total_r | avg_r | PF | win% | streak | no_top5 | no_top10 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | body60+HTF1D+HTF4H target 3R | 126 | 1.06 | +28.82 | +0.229 | 1.62 | 44.4% | 9 | +14.07 | -0.29 |
| 2 | **body60+HTF1D+HTF4H target 2.5R** | **127** | **1.07** | **+27.00** | **+0.213** | **1.57** | **44.9%** | **9** | **+14.75** | **+2.50** |
| 3 | body60_r12 (no HTF) target 3R | 130 | 1.10 | +26.70 | +0.205 | 1.54 | 43.8% | 9 | +11.95 | -2.40 |
| 4 | body60_r12 (no HTF) target 2.5R | 131 | 1.10 | +26.30 | +0.201 | 1.52 | 44.3% | 9 | +14.05 | +1.80 |
| 5 | body60+HTF1D+HTF4H target 4R | 125 | 1.05 | +25.39 | +0.203 | 1.54 | 44.0% | 9 | +8.44 | -3.61 |
| 6 | body60_r12 target 4R | 129 | 1.09 | +23.28 | +0.180 | 1.47 | 43.4% | 9 | +6.33 | -5.72 |
| 7 | body60+HTF1D+HTF4H target 2R | 131 | 1.10 | +19.89 | +0.152 | 1.39 | 44.3% | 9 | +10.14 | +0.39 |
| 8 | body60_r12 target 2R | 135 | 1.14 | +18.69 | +0.138 | 1.35 | 43.7% | 9 | +8.94 | -0.81 |
| 9 | decisive(body70)+HTF1D target 2.5R | 82 | 0.69 | +13.95 | +0.170 | 1.47 | 43.9% | 12 | +1.70 | -8.09 |
| 10 | decisive(body70)+HTF1D+HTF4H target 2.5R | 82 | 0.69 | +13.95 | +0.170 | 1.47 | 43.9% | 12 | +1.70 | -8.09 |

## Vencedor selecionado: `body60 + HTF1D + HTF4H + target 2.5R`

Razão da escolha sobre o #1 (target 3R):
- **no_top10 = +2.50R (positivo)** — robustez extra contra fat-tail
- avg_r ligeiramente menor (+0.213 vs +0.229) mas PF e win% praticamente idênticos
- Sample n maior (127 vs 126)
- Target menor = trades fecham mais rápido = menos exposição a reversão intraday

### Métricas finais
- **n = 127 trades** em 2.36 anos (~1.07/sem, 4.58/mês)
- **Total net R @ 0.05R = +27.00R**
- **Avg net R/trade = +0.213R**
- **PF net = 1.57**
- **Win rate = 44.9%**
- **Max losing streak = 9**
- **no_top5 = +14.75R ✅** (sobrevive remoção dos 5 melhores)
- **no_top10 = +2.50R ✅** (sobrevive remoção dos 10 melhores — raro)

### Year-by-year

| Ano | n | Total R | Avg | Win% |
|---|---:|---:|---:|---:|
| 2024 | 49 | **−5.82** | −0.119 | 34.7% ⚠️ |
| 2025 | 62 | **+28.25** | +0.456 | 53.2% ✅ |
| 2026 (parcial, 4.5m) | 16 | **+4.57** | +0.286 | 43.8% ✅ |

**2024 foi negativo.** Mesma pegada do EURUSD 4H — regime macro daquele ano não favoreceu LONG XAU intraday.

### Cost sensitivity

| Spread | Total Net | Avg | PF |
|---:|---:|---:|---:|
| 0.00 | +33.35 | 0.263 | 1.76 |
| 0.05 | **+27.00** | **0.213** | **1.57** |
| 0.07 | +24.46 | 0.193 | 1.50 |
| 0.10 | +20.65 | 0.163 | 1.40 |

Estável até 0.10R spread — não é estratégia "no limite" do custo.

## Observações

### Body 60% > Body 70% em XAU
A intuição vencedora do EURUSD V2 (body ≥ 0.7) **não se aplica** em XAUUSD. Body 60% gerou +13R a mais que body 70% no mesmo combo HTF.
- Hipótese: XAU tem mais bars de continuação com pavio superior moderado que ainda têm follow-through positivo. Filtro body 70% perde sinais bons.

### HTF12H não acrescenta nada
Adicionar HTF12H bullish ao filtro HTF1D+HTF4H não muda resultados (linhas 9–10 do top idênticas). HTF12H entre HTF4H e HTF1D é redundante para XAU.

### Session filter (London/NY) reduziu volume sem melhorar qualidade
Variantes com filtro de sessão saíram do top 10 — XAU tem trades válidos fora dessas janelas.

### Rejection-based 1H continua sem edge
Audit anterior já mostrou (PF 0.95–1.05, no_top5 negativo). Não revisitado nesta rodada.

### Pullback EMA50 (mirror ETHUSD 1H) foi mediocre
Sinal `PULLBACK_EMA50_RSI_reclaim+HTF1D` não entrou no top 10 — padrão que funciona em ETH não traduz pra XAU.

## Classificação proposta: `SETUP_CANDIDATO_FORTE` (intraday)

**Por que NÃO SETUP_VALIDO_INTRADAY direto:**

| Critério | Mínimo | XAU 1H result |
|---|---:|---|
| n | ≥ 30 | 127 ✅ |
| PF | ≥ 1.40 | 1.57 ✅ |
| avg_r_net | ≥ 0.15 | +0.213 ✅ |
| no_top5 positivo | sim | +14.75 ✅ |
| no_top10 positivo | sim | +2.50 ✅ |
| max_streak | ≤ 12 | 9 ✅ |
| trades/sem | ≥ 2 | 1.07 ⚠️ abaixo |
| Anos cobertos | ≥ 3 | 2.36 ⚠️ |
| Anos positivos | ≥ 80% | 2 de 3 (66.7%) ⚠️ |

6 de 9 critérios atendidos, 3 marginais. **Mesma decisão conservadora do EURUSD 1H + ETHUSD 1H:** ativar como CANDIDATO_FORTE, promover a VALIDO_INTRADAY após validação ao vivo (30+ trades reais, mantendo avg_r ≥ +0.15 e no_top5 ≥ 0).

## Stop / Target / Gestão recomendados
- Stop: `low − 0.5 × ATR(14)`. Rejeitar se R > 5 × ATR.
- Target: **2.5R fixo**
- BE após +1R
- Trailing desabilitado
- Max hold: 20 candles 1H (~20h)

## Follow-up recomendado
1. Re-rodar com filtro DXY < EMA50(DXY) no 4H — espero ~10–15% melhoria adicional baseado em correlação XAU/DXY
2. Após 30 trades reais, reavaliar promoção a SETUP_VALIDO_INTRADAY
3. Considerar substituir/aposentar o módulo legacy `XAUUSD_1H_LONG_REJECTION_EXECUTION` (n=21 forward-test, rejection-based confirmado sem edge no audit)

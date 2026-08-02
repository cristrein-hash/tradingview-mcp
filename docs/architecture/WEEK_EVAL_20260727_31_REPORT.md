# Avaliação da Semana 27-31/07/2026 — trades ideais vs funil do sistema + arquivo da Retoma v1

Relatório final (Cris + Claude, domingo 02/08). Scripts reprodutíveis: `research/week_eval_20260802_ideal_trades.py`
(parte 1), `week_eval_20260802_funnel_cross.py` (parte 2), `week_eval_20260802_retoma_vs_reader.py` (parte 3).
Devil's Advocate (lookahead/validade): **CLEAN-WITH-CAVEATS** (caveats incorporados abaixo).

## Parte 1 — Os 6 trades ideais do Cris (plotados no chart; teto com hindsight)
| Dir | Entry | SL | TP | RR | Janela ideal |
|-----|-------|-----|-----|-----|--------------|
| SHORT | 4106,06 | 4118,36 | 4028,47 | 6,3R | Seg 01:00 → Ter 10:45 |
| SHORT | 4089,57 | 4101,86 | 4038,69 | 4,1R | Seg 13:00 → Ter 06:30 |
| SHORT | 4088,35 | 4104,81 | 4018,04 | 4,3R | Seg 09:00 → Ter 11:15 |
| SHORT | 4068,68 | 4078,69 | 4043,75 | 2,5R | Ter 01:00 → 02:30 |
| LONG | 4011,48 | 3994,50 | 4110,47 | 5,8R | Ter 15:15 → Qua 20:00 |
| LONG | 4067,76 | 4057,74 | 4107,88 | 4,0R | Qua 19:30 → 19:45 |

**Teto +27,0R (WR 100% por construção — hindsight, não alcançável).** DNA: entrada no extremo estrutural
(supply band 4068-4106 / OB 4H 3995-4010), stop cirúrgico 10-17 pts atrás da estrutura, alvo na estrutura
oposta. 4 classes: fade-de-supply, quebra-de-continuação, acumulação-no-OB, momentum-de-evento.

## Parte 2 — O funil do sistema em cada janela (E1 candidatos + E2 verdicts)
Do teto: sistema surfou +2,5R (o SHORT 4068 = continuação com-perna, E2 conv50 às 00:46 de 28/07 — a classe
do R8 `bos_continuation`, que o trade do Cris validou antes de existir). Decomposição das 4 causas de miss:
1. **Timing do go-live (8,4R)** — E1 TINHA os candidatos dos 2 shorts de 2ª (14 e 16); o E2 só ligou 2ª à
   noite (nessa noite surfou 3 shorts da mesma perna). Resolvido por si.
2. **Fade-de-topo (6,3R)** — classe mantida discricionária até agora → **Cris aprovou estudo: R10 construído**.
3. **LONG no OB 4H (5,8R)** — lacuna real de geração (zone_reject só dispara no reclaim de SAÍDA; zero
   candidatos no toque do bloco) → **Cris aprovou: R9 construído e LIVE**.
4. **Momentum de evento (4,0R)** — fora de scope por design (veto-de-evento); trade humano (o real +1.600$).

## Features novas (construídas 02/08, provas completas)
- **R9 `ob_touch_hold` (E1_OB_TOUCH=1, LIVE shadow):** toque (wick ≤0,25·ATR15 da borda) + hold (fecho do
  lado protetor; fecho além do bloco = faca ⇒ nada) no OB 4H/1D. ATR do TF DA ZONA (com ATR15 a âncora
  matava qualquer fecho causal junto a bloco 4H). SL = extremo do bloco ∓0,1·ATR. Dedup por episódio.
  **Replay: gera o LONG do monstro 28/07 14:15 UTC entry 4022,45 SL 3992,97** (custo da causalidade:
  entra no fecho do hold, não no wick ideal 4011). 9 candidatos na semana, 0 em faca.
- **R10 `top_fade` (E1_TOP_FADE=0, ESTUDO):** anti-evento (high_impact/evento≤45min/barra vertical) + raid
  profundo na zona (≥ meio do bloco) + ≥2 episódios de retest rejeitados + rsi<70 + SL na última rejeição.
  3 correções guiadas por sonda (não fitting): prev_high-60M vira a própria referência do sweep (errado) →
  raid-profundo; rsi<rsi_ma mal-temporizado no breakdown → rsi<70; SL swept-high dava R>2·ATR → última
  rejeição. **Replay: gera o SHORT do topo de 2ª 27/07 11:15 UTC entry 4097,17 SL 4106,55; ZERO no FOMC.**
  Aceitação semana 5/5 PASS · selftest 16 casos PASS · regressão OFF byte-idêntica. Commit `53b06a5`.

## Parte 3 — Retoma v1 vs Reader (painel pós-DA) → **RETOMA ARQUIVADA**
**Retoma v1 (dry, forward verificado):** N=12 (10 resolvidos, 2 OPEN) · WR 10% (1W/9L) · somaR −6,0R ·
avgR −0,60R · maxDD −8R · pior streak 8L → **prereg REPROVADO (baliza ≤5)** · seq `LLLLLLLLWL`.
**Reader E2:** 58 verdicts · 0/28 longs surfaced · 8/30 shorts surfaced (o lado que pagou).
**Caveats DA (obrigatórios):** (1) recusas contextuais únicas da mesma classe ≈16-19, não 28 (resto =
duplicados/bad_rr/outra zona); (2) 3 dos 9 losses nunca chegaram ao reader (gap E1) — não-lido ≠ recusado;
(3) o reader recusou TAMBÉM o repique vencedor 2× (custo +3R) — honesto: "recusou os losers que leu E o
winner"; (4) atribuição do WIN ao FOMC = narrativa não verificada.
**Conclusão:** direção da tese confirmada (recusar tudo −0R > mecânica −6R na semana hostil), mas o teste
discriminante (dizer SIM em regime favorável) fica para o forward. **Decisão Cris 2026-08-02: ARQUIVAR** —
router deixa de registar candidatos novos (`RETOMA_ARCHIVED=True`), resolução SL-first continua até os 2
OPEN fecharem. A classe estrutural herda no R9 (comprar NO OB, não perseguir repiques).

## Lições da semana (permanentes)
1. O DNA do Cris = 4 classes; o sistema agora gera 3 delas (continuação R8, OB-touch R9, fade R10-estudo);
   momentum-de-evento fica humano por design.
2. Causal vs ideal: o sistema entra no FECHO da confirmação (mais tarde/pior preço que o wick ideal) — é o
   custo da causalidade, não um bug.
3. Reader: provou o NÃO em regime hostil; falta provar o SIM em regime favorável (próximo forward).

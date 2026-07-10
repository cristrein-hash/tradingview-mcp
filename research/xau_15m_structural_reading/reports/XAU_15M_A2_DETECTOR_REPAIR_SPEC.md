# SPEC — REPARO DO DETECTOR A2 (2026-07-10)

> Base: autópsia dos 42 (`AUSENCIA_REAL = 0/42` — corrigir o detector existente, não inventar tese
> nova) + `XAU_15M_DEMAND_REGION_SPEC.md` + conhecimento visual ZONAS A2. Foco único: DETECTOR DE
> REGIÕES. Sem entry, sem outcome, sem backtest, sem skip, sem primitives. r_cycle=4 mantido.

## Causas → correções

**1. GEOMETRIA (11 BULL + 2 CAP + 2 RANGE): banda por ACEITAÇÃO/corpos, não wick estreito.**
- REGIÃO-FUNDO: `price_low = L1 − 0,1·ATR` (mantido) · `price_high = maior CLOSE nas ±4 barras em
  torno do extremo` (a tampa dos corpos na base), com largura mínima 0,7·ATR e máxima 2,5·ATR.
- REGIÃO-TOPO (para conversão): simétrico — `price_low = menor CLOSE nas ±4 barras do topo` ·
  `price_high = H1 + 0,1·ATR`. A conversão herda a ZONA INTEIRA.

**2. INVALIDAÇÃO_ERRADA (5 velas; furos 0,01-0,11): tolerância estrutural.**
- Zona só morre com **fecho além da banda por >0,5·ATR** (quebra real) OU **2 fechos consecutivos**
  além da banda (aceitação do outro lado). Furo ≤0,5·ATR sem sequência = tolerado (zona viva).

**3. ~~ZONA_VELHA: autoridade 168h~~ — `AUTHORITY_FILTER = REJECTED_AS_IMPLEMENTED (Cris 2026-07-10)`.**
- Revisão visual das 9 velas "SEM AUTORIDADE": TODAS zonas válidas (ex.: #40 — zona de out/2025
  segurou a capitulação de jun/2026, 8 meses depois). O filtro quase eliminou zonas boas sem provar
  que filtrava sujeira: evidência de dano, zero evidência de benefício.
- **NÃO usar idade/autoridade para invalidar zona. Se a zona está bem formada e o preço reage nela,
  permanece válida.** Origem do filtro registada: conceito do DA (estratificar por idade) +
  implementação dura (168h, exclusão) decidida pelo Claude SEM solicitação do Cris.

**4. FAMÍLIAS (tratamento próprio, spec §2):**
- **CAPITULAÇÃO**: não exigir zona pré-existente — a região que NASCE do próprio flush
  (known_at ≤24h após a vela) conta como detecção correta (âncora para reteste futuro; a entry vive
  1,5-38h depois).
- **BULL_PULLBACK**: cobertura por zona pré-existente com autoridade (fundo OU topo convertido) —
  geometria corrigida deve alcançar a zona visual.
- **RANGE**: fundo real do range — zona no fundo; meio/topo não vale (autoridade + geometria).
- **PLT/convertido**: rompida + aceite acima + zona inteira herdada + invalidação tolerante.

## Constantes do reparo (definições da spec, não grid)
corpo_janela = ±4 barras · largura banda ∈ [0,7, 2,5]·ATR · tolerância de quebra = 0,5·ATR ou 2
fechos · autoridade = 168h re-armável por defesa · janela late capitulação = 24h.

## Gate (único teste autorizado)
Contra os 42 apenas: cobertos / falhando / motivo simples por vela. Sem outcome, sem entry, sem
métricas além de contagens. Parar após o gate.

## Status
`REPAIR_SPEC — detector v2` · produção não autorizada · entry inexistente.

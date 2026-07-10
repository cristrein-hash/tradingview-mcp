# SPEC — RÉGUA DA PAUSA (degrau de escada / PLT intra-perna) — 2026-07-10

> Escrita APERTADA e EX-ANTE, antes de rodar (ordem Cris). Complementa
> `XAU_15M_A2_DETECTOR_REPAIR_SPEC.md`. Família-alvo: BULL_PULLBACK apenas.
> STATUS: `SPEC_ONLY_NOT_TESTED`. Roda só com ordem.

## 1. Contexto obrigatório (escopo)
- Macro = BULL (v5 hour-causal) E perna de markup viva (máquina de ciclos em UP).
- Fora disso, NENHUMA pausa vira zona. (Não é camada global.)

## 2. Definição de PAUSA (todas as condições, sem exceção)
- **Início**: as últimas **8 barras 15M consecutivas** têm range total (max high − min low) ≤ **1,5·ATR15**.
- **Extensão**: a pausa continua enquanto os FECHOS permanecerem dentro do range corrente da pausa;
  os extremos podem alargar até um teto de **2,5·ATR15** de range total — acima disso a pausa é
  descartada (não é pausa, é range/estrutura maior).
- **Topo da pausa** = max HIGH da pausa. **Teto de corpos** = max CLOSE. **Piso de corpos** = min CLOSE.

## 3. Rompimento + Aceitação (a zona só nasce aqui)
- **Rompimento** = primeiro FECHO acima do topo da pausa.
- **Aceitação** = **2 fechos consecutivos acima do topo** OU **1 fecho ≥0,5·ATR acima**.
- A zona é PUBLICADA no fecho da barra de aceitação (known_at = esse fecho). Sem aceitação = nada.
  Rompimento-pavio rejeitado nunca vira zona.

## 4. Geometria da zona (demanda-candidata para reteste)
- **Zona = [piso de corpos da pausa − 0,1·ATR, teto de corpos da pausa]** (aceitação/corpos,
  conforme reparo; nunca só wick). Largura forçada a **[0,7, 2,5]·ATR** (alarga ao mínimo /
  trunca ao máximo a partir do piso).

## 5. Autoridade, supersessão e morte
- **Supersessão**: nova zona publicada ACIMA → a anterior perde autoridade de detecção
  (vira histórica). No máximo **1 degrau com autoridade por perna** + o anterior por
  **transição de 24h**.
- **Autoridade**: 168h re-armável por defesa (regra do reparo).
- **Invalidação**: fecho >0,5·ATR abaixo do piso OU 2 fechos consecutivos abaixo (regra do reparo).
- **Morte da perna**: ciclo vira DOWN (queda ≥4·ATR) ou macro deixa de ser BULL → TODOS os degraus
  da perna perdem autoridade imediatamente.

## 6. Trava anti-sujeira (obrigatória no run)
- Por construção: ≤1 zona por pausa rompida-e-aceite.
- **Referência declarada**: a escada real do Cris ≈ ~10 topos em ago-out/2025 (~1/semana em markup).
- **Se o run produzir densidade muito acima dessa ordem (degraus/semana em markup), PARAR e
  REPORTAR — régua frouxa. PROIBIDO afinar constantes em silêncio depois de olhar.**

## 7. Constantes (todas aqui, nenhuma no código)
pausa_min = 8 barras · range_início ≤1,5·ATR · range_teto ≤2,5·ATR · rompimento = fecho > max high ·
aceitação = 2 fechos consec. OU 1 fecho ≥0,5·ATR acima · zona = [min close − 0,1·ATR, max close] ·
largura ∈ [0,7, 2,5]·ATR · supersessão 24h · autoridade 168h · invalidação 0,5·ATR ou 2 fechos ·
morte = viragem de ciclo/regime.

## 8. Gate autorizável (quando o Cris ordenar)
Só os 42 (foco: as 11 BULL não detectadas) + densidade degraus/semana como trava do §6.
Sem entry, sem outcome, sem backtest.

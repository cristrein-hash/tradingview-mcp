# XAU 4H L2/BPT — DIAGNÓSTICO DO GARGALO ATUAL (exit + leitura acoplados)

**2026-06-22.** Diagnóstico sob o target de convexidade UNCAPPED. Dois gargalos acoplados, agora quantificados.
DIAGNÓSTICO; full 276; sem produção/promoção/OOS. realR capado não-árbitro.

## 1. O maior gargalo agora: exit, leitura, risk/SL ou feature?
Decomposição por episódio (T5 bottleneck classification, n=276):
- **EXIT_ONLY 68 (25%)** — leitura certa (TAKE num runner), o cap clipou. **Exit calibrado sozinho recupera.**
- **READING_ONLY 83 + SUPPLY_CONTEXT 32 + REGIME 2 + BEAR_PULLBACK 3 + RANGE_TOP = ~120 (43%)** — erro de
  LEITURA que o exit NÃO conserta. **Este é o gargalo real e perene.**
- **RISK_SL** (stop cedo com corrida disponível) e **RESIDUAL 85** — mistos/irredutíveis com features atuais.

## 2. Calibrar exit sozinho resolve o quê?
Recupera os **68 EXIT_ONLY** + parte dos B (51 runners prejudicados por exit). Melhor exit = **let-run static**
(SL estrutural + time-stop 120, SEM target/partial/BE): sumR +144.6R custado (vs +84.2R capado). Exits "espertos"
(partial50, BE@2R) **destroem** convexidade (partial50 +31R).
**FLAG CRÍTICO (DA aad41aa):** o +144R é **72% concentrado em 10 trades** — removendo-os, −24.5R em 266 trades;
Lstreak 16 / maxDD 28.9 = **prop-firm-fatal**. let-run NÃO é exit promovível sozinho: é captura de convexidade-BETA
concentrada em ~10 barras-monstro de bull-markup em 6 anos. **E 9 dos top-15 winners de let-run foram SKIPADOS pela
leitura** — o maior R foi cortado pelo lens supply/TOP. → **isto reforça que a edge mora na LEITURA, não no exit;
o exit resolve a MEDIÇÃO/captura, mas o valor está em não-cortar esses 9-10 monstros.**

## 3. Refinar a leitura resolve o quê?
Os ~120 READING + o streak/DD do let-run. É onde mora a automação perene.

## 4-7. O padrão estrutural dos erros (T4 error map) — A DESCOBERTA
**Winners SKIPADOS = 37 runners cortados pela leitura.** Concentração: **22/37 em contexto TOP**, 12 PULLBACK.
Motivo: a leitura corta longs perto de topo que eram **markup-through-supply** (continuação de bull-run rotulada
como top-risk).
**Losers MANTIDOS = 86.** Motivo: **51 bull_no_run** (contexto bull, não correu) + **32 supply_misread** (supply
rejeitando ignorada) + 3 bear_pullback_long.

**Os dois erros são UM SÓ eixo — o supply-lens contextual, errado nas DUAS direções:**
- perto-de-supply em bull forte = **markup** (runner) → a leitura corta errado (37 winners skipados).
- perto-de-supply em range/topo = **rejeição** (loser) → a leitura mantém errado (32 supply_misread).

**Ressalva de circularidade (DA):** a assinatura TOP→SKIP é PARCIALMENTE tautológica — TOP (label) e SKIP (policy)
vêm do MESMO engine (73/74 TOP→SKIP). O resíduo NÃO-circular e real: dentro do contexto supply-near/TOP/PULLBACK há
**37 runners E 86 losers que a leitura não distingue.**
**Prova quantitativa (T6, lift loser/runner):** `supply_reject` lift **1.08** (31 runners + 78 losers — não separa);
TOP 0.84, range 0.79, engine_SKIP 0.95, regimeB 0.99 — **todos ≈1 = não-discriminativos** (e matam 28-37 runners).
**Único notável: `bear_leg_block` lift 1.63** (5 runners / 19 losers) — corta losers 1.63× mais que runners.
Reconcilia o legbear RETRATADO: sob R capado parecia ruim, sob convexidade é o blocker NARROW menos-pior (bear-markdown
genuíno). Os demais layers (clean_sky, macro_phase_BULLRUN) preservam runners mas mantêm losers igual (lift ~0.9).

## 8. Próxima feature/leitura — e por que NÃO é construível agora (correção DA)
A tentação é um **disambiguador de supply-near** (markup vs rejeição por ACEITAÇÃO). **MAS o DA flagou: isso é
REBRAND de trabalho já refutado** — `microstructure_features.py` já tentou markup-vs-rejection (BREAKOUT_ACCEPTANCE vs
FAILED_BREAKOUT) e a leitura INVERTEU; acceptance não separou. **E o OHLC sub-4H contíguo que aceitação exige NÃO
EXISTE** (o frozen é só 4H). Logo a feature de aceitação **não é construível com os dados atuais** e overlaps refutado.

## Conclusão (NÃO superficial)
Dois gargalos acoplados, ambos reais: (1) **exit** — resolve a MEDIÇÃO/captura (let-run), mas o +144R é beta
concentrada em ~10 monstros e Lstreak-16 é fatal; (2) **leitura** — o eixo supply-markup-vs-rejeição, errado nas duas
direções, é o gargalo perene; lift 0.93-1.08 = nenhum blocker separa. **bear_leg_block (lift 1.63) é o único sinal
de separação real, e é narrow.** O que NÃO temos: o primitivo de aceitação que distinguiria markup de rejeição —
exige OHLC sub-4H contíguo inexistente.

**Guardrail do próximo bloco (DA):** antes de qualquer disambiguador de supply: (1) **adquirir/validar OHLC sub-4H
contíguo** (não existe hoje); (2) qualquer feature sucessora deve bater **lift > 1.0 separando os 37 runners dos 86
losers** via null/sub-janela DENTRO dos 276 — `supply_reject` lift 1.08 / `bear_leg` 1.63 são as baselines a bater.
Sem isso = repetir a inversão da microstructure. Automação segue a meta; nada de resignação a beta nem human-endpoint.

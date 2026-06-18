# XAU 4H L2/BPT — A parede do filtro de bear-leg (CONFIRMADA — banner intermediário corrigido)

> 🔄 **CORRIGIDO 2026-06-18 (final):** houve um banner intermediário dizendo que a confluência volume×1D-bear "FUNCIONA parcialmente" (gate 1D-bear AND volume-climax≥1.55), remetendo a `XAU_4H_L2_BPT_VOLUME_CONFLUENCE_BREAKTHROUGH.md`. **Esse breakthrough foi RETRATADO no mesmo dia** — era artefato do tick-volume do frozen; com volume REAL (Session VP) o subconjunto 1D-bear NÃO separa (ver `XAU_4H_L2_BPT_REAL_DATA_CONFLUENCE.md`). Portanto **a "parede" deste documento (corpo §1-6) está CONFIRMADA**: o subconjunto reversão-de-fundo × bounce-em-bear não é filtrável na entrada por NENHUM gate automático (indicador isolado OU confluência). Resolução real = veto humano via flags Telegram ([[project_l2_bpt_telegram_bear_flags_FUTURE]]). Volume do frozen = tick-volume NÃO-CONFIÁVEL.

**Status:** `DIAGNOSTIC · DEFINITIVE_NEGATIVE · RECALL_GATED` · **Data:** 2026-06-18
Testes das propostas do Cris (Q2). Sem outcome/produção. Conclusão estrutural: o subconjunto reversão-de-fundo × bounce-em-bear NÃO é filtrável na entrada sem perder winners.

---

## 1. Q1 — por que E1/E17 caem em bear junto com 5/8 traps

Estrutural: o crash COVID rompeu swing lows → estado 1D = bear; E1/E17 são o **reclaim no fundo desse bear**, igual a E6/E7 serem reclaims no bear da correção. A máquina 1D não separa "reclaim no fundo de capitulação" de "bounce fraco no meio da perna" — ambos são reclaims em bear, low legpos.

## 2. Q2 — release só após NAS LONG + bubble 1D: TESTADO, NÃO funciona

| variante | recall (winners) | traps | razão |
|---|---|---|---|
| 1D-bear amplo | ❌ bloqueia E1/E17 | 5/8 | E1/E17 em bear igual aos traps |
| bear-leg madura (age+LH) | ✅ 0 | 0/8 | traps disparam o reset bull |
| **release c/ NAS LONG+bubble** | ❌ E1/E17 | 5/8 | **E1/E17 têm 0 sinal antes da entrada (cedo demais); traps até têm bubble** |
| bear-leg qualificada por topo de exaustão | ❌ E1/E17 | 5/8 (LB45) | **47 "topos" nos 45d antes do crash COVID — perna do COVID também qualifica** |

**Evidência crua (debug):** E1 (2020-03-23) e E17 (2020-04-01): bear desde 2020-03-12, **NAS_LONG=0, BUY_bubble=0** na janela. E6/E7: **1 BUY bubble** (2020-10-08). O sinal de fundo aponta o lado errado.

## 3. Conclusão definitiva (a parede é estrutural)

**7 abordagens** (swing 4H, slope 1D, legpos, exaustão, máquina-estado 1D, NAS+bubble release, topo-qualificado) convergem: **winners reversão-de-fundo (E1/E17/E27/E30/E40) e traps bounce-em-bear (E6/E7/E11/E39) são indistinguíveis na entrada.** Os winners são bottom-catches agressivos *pré-confirmação*; a diferença ("fundo segura e corre" vs "bounce falha") só existe **depois** = é OUTCOME, não dado de entrada. Confirma a própria leitura do Cris (E10: "não tem como diferenciar de reversão bull sob nenhuma forma").

## 4. O que ISSO significa (direção, não derrota)

A edge NÃO pode vir de filtrar perfeitamente esse subconjunto. Tem que vir de:
1. **SL estrutural (3-4 ATR, sem teto) + BE** — winners = R grande; understood-losers = −1R.
2. **Aceitar os understood-losers** (Cris: "E11 loser compreensível").
3. **Único filtro limpo:** extreme-top E24 (legpos>90 + exaustão clara) — remove os piores topos; usar como veto-soft, não gate de toda bear leg.

## 5. O passo decisivo (único que resta para saber se há edge)

**Medir o outcome real da PRUNED_BASE_V2 por episódio:** SL estrutural (swing-low origem, sem teto 1.5ATR) + BE + alvo flex, **lift vs base rate**, segmentado por legpos. Recall-gate primeiro. Pergunta: a R dos winners carrega a estratégia aceitando os understood-losers indistinguíveis? **Sem essa medição, qualquer filtro de entrada extra é prematuro — e o dado já mostrou que esse subconjunto não é filtrável.**

## 6. DA appendix
- Testou as propostas do Cris de forma justa (3 variantes + debug cru)? ✅
- Recall-gate respeitado (descartou tudo que matava E1/E17)? ✅
- Não forçou positividade / não overfitou? ✅ (negativo definitivo com evidência crua)
- Não promoveu filtro? ✅. Produção intacta? ✅.

**DA verdict: PASS — Q2 testada e refutada com evidência empírica precisa; a parede é estrutural (subconjunto não filtrável na entrada, 7 abordagens); direção = SL estrutural + aceitar understood-losers + E24 como único filtro limpo; decisivo = medir outcome real. Sem deslumbre, sem outcome promovido.**

---
*Read-only. Scripts: extract_1d_v2.py, release_gate.py, topqualified.py, debug_signals.py. Sem outcome/produção.*

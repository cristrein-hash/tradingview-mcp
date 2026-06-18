# XAU 4H L2/BPT — 1D Leg Decomposition (resultado honesto + implicação)

**Status:** `DIAGNOSTIC · RECALL_GATED · HONEST_NEGATIVE_FOR_HARD_GATE` · **Data:** 2026-06-18
Máquina de estado de estrutura 1D causal (CHoCH/BOS sobre pivots Williams no daily). Recall-gate contra os 9 winners + respeitar E10. Sem outcome/produção/SLIM.

---

## 1. O que foi construído

Máquina de estado 1D causal: perna de alta vigora até um close diário romper abaixo do último swing low confirmado (→ **bear leg**); a bear leg persiste até um close romper acima do último swing high (→ volta **bull**). Entry bloqueado se estado 1D = bear. Pivots Williams k=3/5/7, SHIFT causal.

## 2. Resultado (recall-gated, honesto)

**Bloqueio 1D-bear amplo (k=3/5):**
- ❌ **RECALL FALHA:** bloqueia **E1 e E17** (winners) — as reversões em V do crash COVID mar/2020: o 1D estava bear, mas elas são o catch da virada.
- Pega 5/8 traps (E6,E7,E11,E36,E37); ✅ E10 bull (não bloqueado), E12 bear.

**Bloqueio "bear leg madura" (age≥15-30d + ≥1-2 lower-highs):**
- ✅ **RECALL OK** (0 winners bloqueados), ✅ E10 passa, ✅ E12 bloqueado.
- ❌ **Pega 0/8 traps.**

**Não há meio-termo limpo.** Entre over-block (mata winners) e under-block (pega nada).

## 3. Por quê — a dificuldade estrutural (definitiva)

**Os traps de bear-bounce SÃO os reclaims que disparam o "reset bull" da máquina.** No bar de entrada do trap, o estado 1D já virou bull (o reclaim acabou de quebrar o último swing high). Logo, no **momento da entrada**, E6/E7/E11/E39 são **indistinguíveis de um reset bull válido** (E10, E40) por estrutura 1D. E as reversões-de-fundo winners (E1/E17) acontecem em contexto 1D-bear igual aos traps de bounce. **5+ abordagens** (swing 4H, slope 1D, legpos, exaustão, máquina de estado 1D) convergem: **este subconjunto não é separável como gate pré-entrada sem perder winners.**

## 4. A implicação realista (não é fracasso — é direção)

Não tentar filtrar perfeitamente os bear-bounce traps na entrada (o dado diz que não dá sem perder winners). O caminho real, alinhado com a própria leitura do Cris ("E11 = loser COMPREENSÍVEL pela lógica da estratégia"; "E10 = entrada correta indistinguível"):

1. **Aceitar os understood-losers** — alguns bear-bounce reclaims serão tomados e perderão; é parte da estratégia.
2. **SL estrutural (3-4 ATR, sem teto)** + BE — o que converte os 12 "SL-curto" e limita os understood-losers a −1R.
3. **O único filtro limpo validado:** topo macro extremo estilo **E24** (legpos>90 + exaustão clara) — esse SEPAROU; usar como de-prioritização/veto-soft de topo, não como gate de toda bear leg.
4. **legpos** como contexto (maturidade), não gate duro.
5. **A pergunta que decide tudo:** os winners (lift 1.83×, R grande com SL estrutural) pagam os understood-losers? → **medir outcome real da base com SL estrutural sem teto, por episódio, lift vs base rate.** É isso que diz se há edge líquida.

## 5. O que o gate 1D ainda serve

- E10/E12 comportaram-se corretamente em toda versão (E10 não-bloqueado, E12 bloqueado) — o estado 1D é leitura de contexto útil, só não é o trap-killer.
- O extreme-top (E24) continua sendo o achado limpo — usar como veto-soft de topo.

## 6. Próximo bloco recomendado

**Medir o outcome real da PRUNED_BASE_V2 por episódio** com: SL estrutural (swing-low de origem, sem teto 1.5ATR) + BE + alvo flex, **lift vs base rate**, segmentado por legpos e por estado 1D. Recall-gate primeiro (os 9 winners). Isso responde a pergunta-chave: a R dos winners carrega a estratégia aceitando os understood-losers? Sem isso, qualquer filtro adicional é prematuro.

## 7. DA appendix

- Recall-gate aplicado e respeitado? ✅ (over-block descartado por matar E1/E17).
- Não promoveu gate que falha recall? ✅. Não forçou positividade? ✅ (negativo honesto reportado).
- Não overfitou (testou k=3/5/7, age 15-30, lh 1-2)? ✅. E10 exceção respeitada? ✅. Produção intacta? ✅.

**DA verdict: PASS — máquina de estado 1D causal construída e recall-gated; gate duro de bear leg NÃO separa o subconjunto bear-bounce (traps = reclaims que disparam o reset; 5 abordagens convergem); implicação realista = SL estrutural + aceitar understood-losers + extreme-top como único filtro limpo; próximo = medir outcome real por episódio. Sem deslumbre, sem outcome promovido.**

---

*Read-only. Outputs: este doc. Scripts: `leg1d.py`, `leg1d_mature.py`, `build_1d_ohlc.py` (1D OHLC em `/tmp/XAU_1D_ohlc.jsonl`). Sem outcome/produção.*

# XAU 4H L2/BPT — Trade Qualification Engine: STATUS CONSOLIDADO

**Status:** `RESEARCH · CONSOLIDATED · BEST-CURRENT-ADVANCE · NO_PRODUCTION · NOT_PROMOTED` · **Data:** 2026-06-18
Consolidação do estado da frente XAU 4H LONG — L2/BPT / Trade Qualification Engine. **Sem novos filtros, sem ajustar engine, sem reclassificar os 276, sem plotagem, sem chart/MCP, sem produção, sem SLIM, sem SHORT, sem regime v3.** Foundation: [[XAU_4H_L2_BPT_TRADE_QUALIFICATION_ENGINE]] · [[XAU_4H_L2_BPT_QUALIFICATION_VISUAL_RECONCILIATION]].

---

## 1. Estado atual (consolidado)
1. **O TAKE engine é o melhor avanço atual da frente.** Camada de decisão trade-a-trade (84 fatores causais, raciocínio cego ao resultado). Discriminação forte e validada:
   - Monotônico **TAKE > REVIEW > SKIP** (avgR +0.91 / +0.40 / +0.07; WR 53% / 39% / 21%; DD 4.4R / 10.5R / 15.8R).
   - TAKE bate **legpos-random P0.994**, **state-matched P0.996**, **SL-matched P0.983**.
   - **Held-out NON-GT** (sem os 10 casos curados): TAKE ainda **+0.73R** → não é imitação dos curados.
2. **A reconciliação visual (20 prints full-res) NÃO gerou filtro novo confiável.** A primeira leitura visual ("supply wall", "down cascade", "knife mid-fall") foi viés de confirmação e não sobreviveu ao DA/dados (esses sinais marcam winners na mesma proporção; `trend_90` dos losers é até mais forte que dos winners).
3. **Supply distance contínua é o ÚNICO refinamento técnico vivo.** Entre os trades com supply capando o alvo, o único separador W/L real foi a *distância* ao supply (cohenD 0.83), não a *presença* (flag binário). Registrado como feature futura (§2), NÃO implementado.
4. **A continuation lane high-legpos/uptrend foi REJEITADA** por overfit / bull-market beta (64 variantes de filtro todas "boas" = drift do bull; Bonferroni p≈1.0; apaga 2022 circularmente; 0/2 nos casos fora do bull). Beta empacotado como alpha = modo A1' SUPERTREND.
5. **Não tentar extrair mais filtros locais dos mesmos 276 episódios.** Winners/losers estão estatisticamente emaranhados nos eixos óbvios; qualquer filtro novo sobre esta base faz overfit no drift por construção.
6. **A próxima prova precisa ser OOS / regime não-bull / amostra independente** — não mais leitura desta mesma amostra.

---

## 2. Future Engine Feature: `supply_distance_continuous`
**NÃO implementar agora.** Registro de melhoria para a próxima iteração/OOS.
- **O quê:** usar a **distância à zona de supply como variável CONTÍNUA** (`dist_4h_supply_low_atr`) no raciocínio do engine.
- **Não usar** `supply_present` / `supply_blocks_2ATR` boolean como decisão — binarizar joga fora o sinal que a distância carrega (a presença de supply marca winners e losers igual; a distância separa: winners tinham supply mais longe, +1.22 vs +0.87 ATR).
- **Quando testar:** apenas na **próxima iteração / OOS**, junto com a re-validação do engine. **Não retunar nos 276 atuais** (seria o mesmo overfit que estamos proibindo).
- **Como testar (futuro):** comparar engine-com-supply-distance vs engine-atual em amostra independente, não na base de calibração.

---

## 3. Aprendizados negativos congelados — `DO_NOT_RETRY` (sem novo dado)
Não repetir nenhum destes sem **dado novo / amostra independente**:
- ❌ **supply presence hard flag** (binário) como decisão — usar distância contínua (§2), não presença.
- ❌ **down cascade visual narrative** — refutada (trend dos losers é mais forte, sinal invertido).
- ❌ **knife-midfall narrative** — viés de confirmação; reclaim_body<0 marca winners igual.
- ❌ **high-legpos continuation lane** — bull beta / overfit (Bonferroni p≈1.0).
- ❌ **novos filtros locais nos mesmos 276 episódios** — overfit no drift garantido.
- ❌ **visual confirmation sem DA/data check** — toda leitura visual exige reconciliação numérica + DA antes de virar regra.

---

## 4. Próximo plano recomendado (NÃO executar neste bloco)
- **Opção A — Validar o TAKE engine em janela/regime independente.** Rodar o engine (mesma rubrica/fatores, sem retune) sobre uma janela temporal held-out ou um recorte de regime não-bull já disponível; medir se TAKE>SKIP e se bate baseline fora da amostra de calibração.
- **Opção B — Construir amostra nova não-bull / held-out.** Gerar episódios L2/BPT de um período/segmento independente (ex.: recorte não coberto pelos 276, ou regime de chop/correção) para testar generalização real.
- **Opção C — Só DEPOIS testar `supply_distance_continuous`** como feature adicional, sobre a amostra independente (A ou B) — nunca sobre os 276.
- **Ordem sugerida:** A ou B primeiro (provar generalização do engine como está) → só então C (refinamento). Nenhuma executada neste bloco.

---

## 5. DA curto (auto-verificação deste bloco)
- Não adicionou filtro novo? ✅ (só documentação).
- Não mudou o engine? ✅ (nenhum script de decisão tocado).
- Não usou os mesmos 276 para overfit? ✅ (nenhuma re-execução/reclassificação).
- Supply distance ficou como FUTURA feature, não regra? ✅ (§2, "não implementar agora").
- Produção intacta? ✅ (sem chart/MCP/daemon/SL/exit; xau-l1-cycle inalterado).
- Sem plotagem? ✅.

---
*Consolidação documental. Artefatos do engine: `results/l2_bpt_trade_qualification_{matrix,outcomes,decisions_merged}.csv`, scripts `qualification_extract.py`/`validate_qualification.py`, rubrica `QUALIFICATION_RUBRIC.md`. DAs: ab5e8395 (causalidade), a1c384b6 (refutação engine), a71e63332604c75d9 (refutação melhorias). Nada promovido, produção intocada.*

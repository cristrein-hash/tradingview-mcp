# MANIFEST — L1 · EMA21 CONTINUATION

## Data
2026-06-15

## Decisão do usuário
Persistir a **primeira estratégia aprovada da nova arquitetura** de forma simples, organizada
e segura — **sem ligar produção** e sem criar complexidade desnecessária.

Status declarado pelo usuário:
- **governance_status: USER_APPROVED_FINAL · HUMAN_DISCRETIONARY** (human-in-the-loop; scanner/base rule gera candidato, decisão final humana)
- **evidence_status: NOT_VALIDATED_OOS** (`PROMISING_BUT_NEEDS_MORE_DATA`)
- **CONTINUATION** — não fully mechanical, não full automation.

> ⚠️ **ATUALIZAÇÃO 2026-06-16 — ver banner de RECLASSIFICAÇÃO em `STRATEGY.md`.** (a) Números desta era (FULL-38/KEEP-19/+32.6R) são **in-sample/research `NOT_VALIDATION`**, não prova de edge. (b) **Regime split-brain:** scanner=`regime_B_v3` (morto/legado), runtime live=`regime_l1_v4` → re-derivar sob regime live. (c) O leg `vol_entry_z` foi **removido** (morto + dado bugado); gate é **RSI-only**.

Regra de exaustão **canônica atual (RSI-only)** — o leg de volume foi removido (2026-06-15):
```
blocked_exhaustion  if  round(rsi_vs_ma, 2) <= -9.35
```
> Histórico (NÃO usar): a regra originalmente registrada era `vol_entry_z >= 1.993 OR rsi_vs_ma <= -9.35`. O leg `vol_entry_z` é **estruturalmente morto sob F5 e foi derivado de matriz bugada** → eliminado. Mantido aqui só como registro do que mudou.

## Arquivos fonte usados (referência, não copiados)
- `my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/rebuild_v3/trades.jsonl`
  (38 trades reconstruídos; JSON array — ler com `json.load`).
- `my-strategy/research/revalidation/XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/rebuild_v3/summary.json`
  (FULL-38 / KEEP-19 / BLOCK_TOP-17; reconciliação base rule + SL; R_CEIL removido).
- **Prints recuperados:**
  `backups/recovered_xau_4h_continuation_2026-06-14/supporting_evidence/29_EMA21_prints/`
  (14 prints EMA21_A + MANIFEST; usados para confirmação visual da exaustão).
- Matriz de features causal da regra de filtro: `/tmp/L1_volumetry_matrix.json` (volátil — features
  computadas só de barras ≤ entry; firewall anti-lookahead). Recriável via `/tmp/build_L1_matrix.py`.

## O que foi criado
Pasta nova simples:
`my-strategy/strategies/xau_4h_long/continuation/L1_EMA21_CONTINUATION/`
- `STRATEGY.md`
- `MANIFEST.md`

Somente esses dois arquivos. Nenhuma outra pasta/arquivo de arquitetura criado.

## O que NÃO foi alterado
- Produção **intacta**: receiver, cloudflared não tocados.
- LaunchAgents **não tocados**. Pause flag **não removida**.
- `monitor`, `claude_recheck`, `strategy_rules`, `catalog.json` antigo, Telegram — **não alterados**.
- Alertas **não ativados**.
- **Registry operacional NÃO populado** (é design-only; sem fluxo seguro ainda).
- **Nenhum novo backtest** rodado. Nenhuma nova arquitetura grande criada.
- Sem commit / push.

## Status final
**SALVA como USER_APPROVED_FINAL / HUMAN_DISCRETIONARY.**
Estratégia persistida apenas como documentação leve (2 arquivos). Não conectada ao runtime.
Filtro = `PROMISING_BUT_NEEDS_MORE_DATA` (precisa OOS real com thresholds congelados antes de
qualquer promoção a mecânica/produção).

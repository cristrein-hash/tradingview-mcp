# E1 INTER-CONTEXTUALIZADO vs E1 ENTREGUE — contrafactual 2 anos (prereg selado 29/08, ordem Cris)
PERGUNTA: que resultado teria tido o E1 se as 7 regras tivessem sido inter-contextualizadas como o Cris
pediu, vs o E1 que foi entregue (regras isoladas)? Mesmo harness de replay (e1_edge_2y: dossiê
reconstruído do RAW barra a barra), mesmos 2 anos, mesma resolução SL-first 3R, 3 fixes do DA
(dedup por bar_time, resolução causal, split por TF).

## BRAÇO A (baseline): e1_detector.detect() ENTREGUE, sem alterações.
## BRAÇO B (inter-ctx): mesmas 7 regras + as 4 mudanças, SELADAS AGORA:
B1. SITUAÇÃO PRIMEIRO: lado permitido por TF = trend do dossiê nesse TF com veto choch: choch.dn=True
    no TF → LONGs desse TF suspensos; choch.up=True → SHORTs suspensos. (Campos que já existem.)
B2. FUSÃO POR SITUAÇÃO: candidatos da MESMA direção na MESMA barra cujos entries distem <=0.5×ATR15
    fundem-se em 1 (fica o de SL mais estrutural = mais largo); n_regras_concordantes registado.
    Convergência >=2 regras = candidato "forte" (métrica reportada em separado).
B3. PRÉ-CONDIÇÕES CRUZADAS (do texto da resposta ao Cris, sem knobs novos):
    - sweep_reclaim LONG só se o low varrido está a <=0.5×ATR15 de zona conhecida (zones.below do dossiê);
      espelho p/ SHORT com zones.above.
    - ema_reclaim só se trend do TF 60 = direção do candidato (tendência confirmada).
    - Regras de continuação (bos_continuation, ema_reclaim) suspensas no TF com choch contrário fresco
      (fresco = o campo choch atual do dossiê, sem janela nova — é o estado que o E0 já mantém).
B4. EXCLUSÃO MÚTUA: LONG e SHORT emitidos na mesma barra no mesmo TF → ambos cancelados.
Parâmetro único novo: 0.5×ATR15 nas distâncias (B2/B3) — valor herdado do CLUSTER_ATR canónico do
liquidity_map, não afinado. ZERO outros knobs.

## MÉTRICAS (por braço): N, WR, sumR, avgR, maxDD, streak a custo 0/0.2; por (dir,tf); por semestre;
LONG-only em destaque (direção viva). B adicional: painel dos candidatos convergentes (>=2 regras).
Null block-shuffle no delta avgR A-vs-B (LONG). Jackknife semestral. DA adversarial OBRIGATÓRIO.
Veredito = Cris. Uso: resposta factual + anexo ao relatório de ressarcimento.
LIMITAÇÕES DECLARADAS: camada Opus fora dos dois braços (justo); zonas as-of dependem da cobertura do
pine RAW (igual nos dois braços); contrafactual — não prova o que o Cris TERIA lucrado, prova o que o
DETETOR teria emitido.

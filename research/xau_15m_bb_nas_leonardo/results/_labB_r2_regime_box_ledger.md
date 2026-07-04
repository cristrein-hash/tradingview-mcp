# LAB B r2 — REGIME BOX — thesis freeze + look ledger

Data: 2026-07-04. Autor: síntese própria desta sessão de análise (subagent spawnado pelo orquestrador p/ Lab B r2; sem commit/push).
Base: N435 (g_in_base435==1, g_v5h!='BEAR'), NET-SB = g_R − 0,80/g_risk. Baseline +233,6 NET · WR_liq 46,0 · runners 53.

## CONGELADO ANTES DE QUALQUER LEITURA DE OUTCOME (probe1 = estrutura só)

Features construídas (validadas: reconstrução v5h == g_v5h 435/435):
- `rbox_pos` = (entry − lo_seg)/(hi_seg − lo_seg), segmento = run de horas com mesmo v5h, bars 15m t∈[início_seg, cj_t]
- `rbox_age_h` = idade do regime em horas de mercado
- `rboxhi_dist_atr` = (hi_seg − entry)/ATR (headroom ao topo do regime)
- `prev_state`, `prev_hi_dist_atr` = (hi_box_do_regime_anterior − entry)/ATR (teto herdado; >0 = teto acima)
- `censored` (22 RANGE sem segmento anterior nos dados)

Calibrações DECLARADAS (na distribuição da BASE, por regime — lição P3-vacuidade):
- bins de rbox_pos e rbox_age = quartis da base POR REGIME
- bandas estruturais fixas: prev_hi_dist ∈ {≤−10, (−10,−2], (−2,0], >0}; rboxhi_dist ∈ {≤1, (1,3], (3,8], >8}

Hipóteses (predicado exato, ANTES de ver R):
- **H1 BULL-sob-teto-herdado:** v5h==BULL AND prev_hi_dist_atr ≥ −2.0 (teto do RANGE anterior ainda acima ou <2 ATR abaixo). Tese: BULL jovem ainda brigando com o teto do regime anterior = supply herdada → losers. Saída candidata: SKIP ou REVIEW.
- **H2 BULL-infante:** v5h==BULL AND rbox_age_h ≤ q25_BULL(=178h). Tese: convergente com H1 (mesma fase estrutural por outro eixo). Só vale como par de convergência, não isolado.
- **H3 topo-do-regime (extensão):** rboxhi_dist_atr ≤ 1.0 (compra a <1 ATR da máxima do regime corrente). ATENÇÃO prior #2/#5: pode ser célula PAGADORA (new-high runs). Medir frio; saída provável = context-class/size, NUNCA presumir ruim.
- **H4 RANGE-top-sob-teto-BULL:** v5h==RANGE AND rbox_pos ≥ 0.9 AND prev_state==BULL AND prev_hi_dist_atr > 0. Tese: long no topo do range com máxima do BULL anterior acima = zona clássica de rejeição.
- **H5 regime-velho:** rbox_age_h ≥ q90 por regime (BULL 1085h / RANGE 1032h). Tese: late-cycle. Medir frio, sem direção presumida.
- **H6 RANGE-céu-limpo-estrutural (proteção):** v5h==RANGE AND prev_hi_dist_atr ≤ 0 (range JÁ acima do teto BULL anterior). Tese: célula pagadora a PROTEGER (context-class), candidata a rota F4 full-size.

Disciplina: eliminação convergente ASSIMÉTRICA (2+ lentes independentes concordando), preservação de runners 1ª classe, painel completo em qualquer proposta de corte (base vs base−flag: N·WR·sumR·avgR·DD·r/DD·streak·por-ano·runners), checar overlap com clusters ≤2-semanas (STREAK_ANATOMY) e com losses g_week.

## LOOK LEDGER
- LOOK #0 (probe1): distribuições estruturais SEM outcome. OK.
- LOOK #1 (probe2): células quartil×regime (pos, age) + bandas (prev_hi, rboxhi) com N/WR/avgNET/sumNET/runners + leitura H1–H6. [executado após freeze acima]

## LOOK #1 — resultado (frio)
- H1 REFUTADA como corte: BULL sob/perto do teto herdado é PAGADOR (N56 WR53,6 avg+0,806 run9); base−H1 degrada r/DD 16,4→11,2 e streak −8→−13. H1∧H2 (BULL fresh-breakout jovem) ainda mais forte (N31 WR64,5 avg+1,362) → vira classe PROTEGIDA.
- H4 REFUTADA como corte: RANGE-top sob teto BULL é a MELHOR célula (N19 avg+2,121 run6); removê-la mata 2024 (+13,6→−6,9). Classe PROTEGIDA.
- H3/H5: não acionáveis (desvios pequenos, sem assimetria de runner).
- POCKET REAL (banda adjacente da grade congelada, leitura within-grid declarada): **BULL ∧ prev_hi_dist_atr ∈ (−10,−2] = "limbo pós-breakout"** — N30 WR33,3 avgNET−0,326 sumNET−9,8 e SÓ 1 runner. Custo de runner ≈ zero → candidato SKIP/REVIEW, MAS não era hipótese primária → exige convergência + estabilidade antes de propor.
- Confirmado prior #2/#5 na escala do regime: topo do box paga (BULL posQ4 avg+0,861), headroom médio (3,8] é runner-carried (WR37,5 mas 14 runners).

## LOOK #2 — congelado ANTES de executar
Alvo: dissecar o limbo L7 := BULL ∧ prev_hi_dist_atr ∈ (−10,−2].
Sub-predicados de convergência (lentes independentes, jsonl), previsão declarada: limbo é pior quando teto tem caráter de supply confirmado; melhor quando céu limpo:
 a) n_supply_overhead ≥ mediana BASE
 b) rbox_age_h ∈ (178,415] (BULL adolescente, Q2)
 c) h1n_clean_sky_atr ≤ mediana BASE
Estabilidade: por-ano, jackknife por semana (remover pior semana), lista dos 30 (episódios/clusters), overlap com losses multi-stop. Painel completo base vs base−L7 e base−(L7∧confirmação).
Saída esperada: família REVIEW/size (ou SKIP se convergência limpa e runner-cost ~0 se mantiver).

## LOOK #2 — resultado (frio)
- Lente c) MORTA nesta calibração: mediana BASE de h1n_clean_sky_atr = 99 (sentinela "sem teto H1") → predicado vácuo, fires em 30/30. Declarado; "conf>=2" reinterpreta-se como (a ∨ b).
- Previsão congelada CONFIRMADA em sinal: L7∧supply≥med avg −0,538 vs supply<med −0,113; L7∧age(178,415] −0,793 vs fora −0,125. Convergência dupla real (a∧b) N8 avg −0,707, 0 runners.
- L7∧(a∨b): N16, WR31,2, avgNET −0,597, sumNET −9,5, 0 runners. L7 restante N14 avg −0,016 (flat) e detém o único runner (+3,96 → PRESERVAR).
- Estabilidade: dano por ano ≈ −8,1/−0,4/−1,0 (2024-pesado mas sem ano positivo); jackknife semanal dentro de L7: remove melhor semana → −13,7; remove pior → −6,0 (não é artefato de 1 semana). 3 clusters de episódio: ago–set/2024 (grind sob teto com supply), jan/2025, jan/2026.

## LOOK #3 — regra final RB-SKIP-1 (probe4)
RB-SKIP-1 := v5h==BULL ∧ prev_hi_dist_atr∈(−10,−2] ∧ (n_supply_overhead≥16 ∨ rbox_age_h∈(178,415])
- Painel: BASE N435 WR46,0 run53 +233,6 avg+0,537 DD−14,2 r/DD16,40 stk−8/+6 | 13,6/183,4/36,6 → BASE−RB-SKIP-1 N419 WR46,5 run53 +243,2 avg+0,580 DD−14,2 r/DD17,07 stk−8/+6 | 21,7/183,8/37,7.
- Cluster hygiene: piores semanas −4,9/−4,7/−4,7 → −4,7/−3,9/−3,8; piores dias −4,8/−4,7/−4,3 → −4,7/−4,3/−3,5; dias c/ 2+ full-stops 43→40; 3+ 13→12.
- HONESTO: max-DD (janela mar/2025) e max-streak (−8) NÃO são tocados — vivem noutro lugar. Ganho = +9,6 NET, 0 runner perdido, poda de 3 clusters multi-stop estruturais.

## INCIDENTE (2026-07-04, registrado)
Durante probe3, um `ln -sf` desnecessário substituiu `results/lab_g_candidates.jsonl` (untracked) por symlink auto-referente. Regenerado imediatamente via `lab_g_context_inventory.py` (dono declarado do ficheiro, "regenerável") e verificado contra medições pré-incidente: 4739 rows · base 435 · sumNET +233,6 · runners 53 — MATCH exato. Guard de integridade adicionado em probe3/probe4 (asserts).

## STATUS: nenhuma escrita fora de results/_labB_r2_* · zero commits (subagent não commita) · zero chart/MCP/produção.

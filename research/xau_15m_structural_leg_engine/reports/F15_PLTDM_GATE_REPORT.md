# F1.5 — PLT/DM GATE REPORT (2026-07-09) — STATUS: `BLOCKED_F15_GATE`

Scripts: `f15_pltdm_gate.py` · `f15_contingency.py` · `f15_diag_best.py` ·
Results: `results/f15_pltdm_gate_result.json` · `f15_contingency_result.json` · `f15_diag_best_result.json`
· Ledger: `claims_ledger.csv` (todos os looks contados).

## Sequência executada (tudo pré-registado ou declarado como amendment)
1. **Estágio-1, grid pré-registado (162 configs, janela pré-holdout, bounds GT-free): 0/162 plausíveis.**
   Todos degenerados (~99,9% LEG_DOWN) pelo flush override — defeito de transposição de escala do
   D_flush (ATR15 vs % do v5), previsto pelo DA da auditoria (ataque B).
2. **AMENDMENT A1 (declarado, ledgered):** sub-grid M×K_up×K_down com override OFF → 18 configs,
   **8 plausíveis** (17-20 pernas/mês, duração mediana 18-21h, ocupações 22-40% equilibradas).
3. **Estágio-2, matcher PLT/DM verbatim (±0,7 ATR, ±2d, greedy 1:1):** melhor config
   **PLT 6/10 · DM 4/11** (fasquia: ≥9/10 e ≥10/11) — **NENHUM passa**. FP/dia 0,75-1,17 ·
   precision 0,125-0,156 na janela ago-out/2025.
4. **Contingência pré-registada esgotada** (eff_thr×slope_thr, 8 células novas, top-6/célula):
   melhor continua **6/10 + 4/11**. `any_pass=false`.

## Diagnóstico (CORRIGIDO pelo DA F0-F1.5, sonda verificada — correção 4)
O falhanço é de **PLACEMENT/escala, não de cardinalidade**: na janela há candidatos a MAIS
(74 = 37 tops + 37 bots para 21 marcas), mas os extremos de fronteira-de-run caem em NÍVEIS errados:
**nos misses, 10/11 marcas não têm NENHUM candidato a ±0,7 ATR do nível em toda a janela** (candidato
mais próximo em ±2d fica 1,7-11,2 ATR do nível); 16/37 runs na janela são LEG_FLAT (extremos sem
significado de swing, diluem a precision para 0,13-0,16). Os flips UP/FLAT/DOWN acontecem em
tempos/níveis descorrelacionados dos degraus da escada. Conclusão operacional INALTERADA: nenhuma
combinação eff/slope/K coloca os extremos nos degraus (contingência confirma teto 6+4 em 8 células);
falta a ESCALA INTERMÉDIA da escada, que o leg-walk antigo (zigzag r=6, banido) capturava.
**Erratum declarado:** o campo `amendment.reason` do result json cita "previsto pelo DA (ataque B)" —
citação imprecisa; a fonte real é a CLASSE de risco do review R1 / DA-ataque-6; o defeito exato
ATR15-vs-% não fora previsto. Corrigido no código para runs futuros; o json histórico fica intacto.

## Diagnóstico informativo (config exploratório M15/K5/K5/OFF/24 — NADA congelado)
- Proximidade aos **VELA DE FUNDO pré-2026: 16/25** (matcher v2; fundos = leg bottoms macro) —
  informativo apenas; holdout BULL-2026 e círculos-2026 **NÃO tocados**.
- **INVALIDO em estado de rejeição: 1/4** (phases provisórias mid-grid, event layer não calibrada —
  fraqueza esperada nesta fase, sem leitura de decisão).
- **⚠️ DESVIO DE ORDEM C7 DECLARADO (DA F0-F1.5 correção 6):** a secção acima leu marcas 2026
  (4 INVALIDO) e a lista nominal dos 9 misses pré-2026 SEM freeze (gate BLOCKED ⇒ nada congelou).
  **Quarentena:** o design do A2 justifica-se EXCLUSIVAMENTE pelo diagnóstico PLT/DM (placement);
  os looks `DIAG_F25`/`DIAG_INV` contam como LOOKS QUEIMADOS da fase F2 no ledger.
- **Distinção obrigatória reconstrução-vs-uso (DA correção 5):** o matcher PLT/DM compara coordenadas
  RETROATIVAS do extremo (top_t/bot_t) com as marcas visuais do Cris — legítimo como gate de
  EQUIVALÊNCIA de reconstrução (marca visual também é retrospetiva). **Nenhum destes recalls é
  utilizável em entry/F2: para USO só vale t_known** (= fecho da barra do flip; antedate de 15 min
  do open corrigido no código).

## Ponte para a fasquia do Cris (declaração C6 obrigatória)
Densidade sósia 28-108:1 ⇒ o engine sozinho NUNCA atinge losers ≤10; e NESTE estado (gate BLOCKED)
a máquina nem sequer entrega as regiões da escada — **sem chance operacional na forma atual**; o
caminho existe via A2 (abaixo), que reconstrói a escala intermédia da escada.

## Caminho proposto (DECISÃO DO CRIS, nada será executado sem ordem)
**AMENDMENT A2 — extremos de ciclo de PULLBACK (sub-legs):** dentro de um run LEG_UP, cada transição
de fase IMPULSE→PULLBACK publica o running-max como degrau-topo (candidato PLT) e cada
PULLBACK→IMPULSE (reclaim) publica o running-min como degrau-fundo (candidato DM), **known_at = barra
da transição** (SEM backdating de decisão). **Aviso frontal (DA, frente 4): a metade DM
(PULLBACK→IMPULSE publica o min no reclaim) COINCIDE NA LETRA com "pivô confirmado-por-rally" — a
stop-condition do manifest bate de frente nela.** A defesa possível: a proibição do Cris atacava o
zigzag como ESTRUTURA e o uso epistémico backdated; no A2 a estrutura continua a ser runs de estado,
a direção vem da máquina, e o known_at nunca é backdated — mas **só o Cris decide se a proibição é
de mecânica ou de epistemologia.** **Alternativa B (não toca na proibição): 2ª camada de histerese
em buckets 15M-nativos** — mais fiel ao v5, mais constantes novas (grid a pré-registar); apresentada
em pé de igualdade com A2, não como nota de rodapé.
**+ redesenho do flush override** (A1 permanente): dd como % do pico com janela rolante (análogo
fiel ao v5) em vez de ATR15 sobre running-peak.

## Confirmação negativa
Sem eventos como decisão · sem entry · sem backtest · sem produção/Telegram/broker · sem chart ·
holdout 2026 intocado · todos os looks no ledger (162+18+~56 contingência + diagnósticos).

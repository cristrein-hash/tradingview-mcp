# LAB A — DA ADVERSARIAL (2026-07-03)

Dois DAs reais no fluxo: (i) **DA pré-execução** (perspectiva do engine multi-agentes) — impôs 8 exigências de desenho ANTES de rodar (same-bar fill+stop, gap≤SL→−1, horizonte ancorado em cj, na→market, seleção adversa MEDIDA, miss=filtro-disfarçado→painel cronológico com miss=0, regimes touch/through, decomposição de exit) — todas implementadas; (ii) **DA pós-resultado** independente (script `_DA_lab_a_geometry_attack.py`; **não commitou** — regra de governança cumprida).

## Bugs materiais encontrados pelo DA pós-resultado (corrigidos e re-executados)
1. **Same-bar-stop indevido em entradas at-close:** a regra conservadora (low do bar de fill ≤ SL → −1) é física correta para fills LIMIT, mas estava sendo aplicada a entradas no CLOSE (delay-nulls e RECLAIM), onde o low PRECEDE a entrada. Corrigido: NULL_delay_cj2 137,1→**173,0** · cj4 117,4→**153,5** · RECLAIM 60,2→**102,6** (a frase "RECLAIM = pior" era FALSA; pior é mid-risk 80,8).
2. **Fill-rate null com custo fixo (mediana):** subestimava o custo da base (Jensen). Corrigido para custo por-trade: p 0,806→**0,506** — leitura correta: a melhor variante é **indistinguível de miss aleatório**, não "pior que aleatório".
3. Menores: label de regime nas linhas THROUGH; código morto; WR net vs gross na citação.

## Ataques dissolvidos (a favor do resultado)
- Horizonte ancorado em cj: **Δ = 0,0 NET** (não pune fills tardios de forma material).
- Same-bar-stop em fills limit = física correta (23 casos em LIM_0.3; 1 gap-open).
- Custo SB sobre risco menor = física do Lab E, não dupla penalização (déficit CR2: 21,7R bruto + só 4,3R de custo).
- Robustez: CR2 perde nos 3 anos; jackknife-episódio sem dependência; 17/17 negativas com mesmo mecanismo (multiplicidade a favor do negativo).
- Seleção adversa direta INTACTA e é a evidência central: base-avgR missed 1,4-2,7 vs filled 0,23-0,55 em toda variante limit.

## Veredito DA
**FAILS, escopado:** *post-signal execution geometry fails* — o gatilho no nível do sinal (A1/A3/A4) NÃO foi testado (BLOCKED, builder re-scan futuro); o rótulo do relatório carrega esse escopo obrigatório. Números publicados = pós-correção, verificados independentemente.

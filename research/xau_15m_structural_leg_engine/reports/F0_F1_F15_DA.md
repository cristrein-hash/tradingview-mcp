# DA — BLOCO F0→F1.5 (2026-07-09) — VERDICT: `BLOCKED_F15_GATE` ENDOSSADO

> Devil's Advocate real (Agent tool, general-purpose, read-only + sonda declarada) atacando
> implementação E veredito do bloco F0→F1.5. 9 frentes. Sonda verificou o matcher/candidatos.

## Verdict
**`BLOCKED_F15_GATE` — endossado e REFORÇADO pela sonda; limpo de lookahead no caminho de decisão e
de fonte banida; 7 correções de higiene exigidas ANTES do commit (todas aplicadas, ver baixo).**

## Ataques CONFIRMADOS → correções aplicadas
1. **GT PLT/DM não declarado no manifest** (manual_shapes_pltdm alimenta o gate sem checksum) →
   adicionado a derived_files com sha256 `b5c70f92…`.
2. **Cache F0 sem registo no manifest + lido sem verificação** → declarado (sha `e968f17b…`) e
   `load_cached()` agora verifica sha fail-loud.
3. **Truncation test substancialmente vácuo** (Data pré-computado partilhado ⇒ só o loop do walk é
   testado; n=12 vs 200 da spec §9.1) → claim reescrita no F1 report com escopo honesto; camadas
   pré-computadas verificadas por inspeção de índices (DA confirmou causais); truncation VERDADEIRO
   (Data reconstruído) = pré-requisito de F2.
4. **Diagnóstico "cardinalidade" era o mecanismo ERRADO** — sonda: 74 candidatos p/ 21 marcas
   (excesso, não falta); **10/11 misses sem NENHUM candidato a ±0,7 ATR do nível na janela inteira**;
   16/37 runs FLAT diluem precision. Mecanismo real = PLACEMENT/escala. Conclusão operacional
   (falta a escala intermédia; eff/slope/K não resolvem) INALTERADA → parágrafo reescrito.
5. **Desvio de ordem C7**: secção "pós-freeze" corrida sem freeze (INVALIDO-2026 + lista de misses
   vistos) → desvio declarado + quarentena (A2 justifica-se só pelo PLT/DM; DIAG_* = looks queimados
   de F2, reclassificados NOT_FOR_DECISION no ledger).
6. **Ledger frágil + citação inexistente** ("previsto pelo DA ataque B") → ledger append-safe;
   citação corrigida (classe R1/ataque-6; o defeito exato não fora previsto); erratum declarado no
   F15 report (json histórico intacto).
7. **t_known antedatado 15 min** (open vs close da barra do flip) → corrigido no código (t+900);
   distinção reconstrução-vs-uso escrita no F15 report (matcher = gate de equivalência com
   coordenadas retroativas, LEGÍTIMO; uso em F2 = só t_known).

## Ataques REFUTADOS (verificados)
Primitives/proxy: nenhuma fresta (cadeia f0→f1→f15 fechada; assert de substrings banidas) · loader
closed-bar: regra profundidade≥1 sólida e conservadora (contiguidade 8/8 nas fronteiras; 1 barra
final excluída = perda declarada, não lookahead) · bucket 1H/macro: índices estritamente anteriores
(sem self-inclusion) · zigzag escondido no código atual: NÃO (extremos só no fecho de run; PULLBACK
é rótulo report-only; grep-clean) · BULL top-buy: não existe camada de emissão em F0-F1.5 · matcher
used-set/janela/FLAT: hits idênticos sem used-set; pernas pós-janela entram; FLAT dilui precision
não recall · FP/dia e precision: aritmética verificada ✓ · A1 = tuning pós-resultado: não
materializado (gatilho GT-free 0/162; tudo falhou igual; contingência era pré-registada).

## A2 vs proibição do zigzag (frente 4 — para o Cris arbitrar)
Contra: a metade DM do A2 (publicar o min no reclaim) **coincide na letra com "pivô
confirmado-por-rally"** (stop-condition do manifest). A favor: estrutura continua a ser runs de
estado; direção vem da máquina; known_at nunca backdated; e a sonda prova que o GT vive nessa escala
(10/11 misses sem candidato ao nível — a escala macro não contém a escada). **Mecânica vs
epistemologia: decisão do Cris.** Alternativa B (2ª histerese em buckets 15M-nativos) não toca na
proibição — apresentada em pé de igualdade.

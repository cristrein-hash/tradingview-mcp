# PREREG — FASE 3A: BEAR-ONLY SKIP COMPOSITE (2026-07-09, v1.1 pós-DA)

## 1. STATUS: `PREREG_ONLY_NOT_TESTED`
Autorizado pelo Cris APENAS o prereg. O teste NÃO roda sem ordem separada dele.
**v1.1 aplica os 6 edits do DA (`..._PREREG_DA.md`, PARTIAL): o bloco é re-enquadrado como
FORMALIZAÇÃO + ROBUSTEZ EPISÓDICA — não teste de descoberta.**

## 2. Objetivo (re-enquadrado — DA edit 1)
**Os headline-numbers dos 4 composites JÁ SÃO CONHECIDOS/DERIVÁVEIS dos agregados publicados**
(A=21L/1W · B=40L/6W · C=51L/6W look queimado · **D = A∩B = 11 marcados, 10L/1W, derivável por
aritmética**). Este bloco NÃO descobre nada disso. O que fica GENUINAMENTE aberto e é o objeto real:
(a) **robustez episódica/cluster** dos cortes (concentração temporal); (b) **null cluster-aware**;
(c) painel completo §8 formalizado no ledger.

## 3. Não-objetivos
Não valida estratégia · não cria entry · não backtesta (outcomes pré-existentes da base) · não
produção · **não BULL · não RANGE** (descoberta separada).

## 4. Universo (CONGELADO pré-teste)
- Candidatos **macro==BEAR** da base causal live-fireable (macro v5 ≡ regime_csv, 166/166 verificado
  pelo DA anterior). Fonte: `xau_15m_live_fireable_candidates.csv` (sha16 6d1d8cb1e731adce).
- **n=78 (61 losers / 17 winners)** · IDs (t) congelados em `results/bear_universe_frozen.json`
  (sha16 `44012c97308ed910`, escrito ANTES deste prereg ser testado). BULL/RANGE excluídos pelo
  campo `macro` (DA edit 6); os 78 incluídos estão fixados por ID.

## 5. Eixos permitidos (definições EXATAS do ledger, agora CONGELADAS)
**S2a — profundidade 1D:** `px_vs_ema1d_atr ≥ 0` onde px_vs_ema1d_atr = (entry_px − EMA21 do 1D
price-agg interna, último dia FECHADO D-1) / ATR15 da barra de entrada. Threshold 0 = a cláusula do
filtro capitulation VALIDADO (não deste sample). Caveat: variante price-agg (21L/1W aqui vs 22L/0W
do nativo); **calibração, não validação**.
**S3 — estrutura acima (DA edit 3 — prosa corrigida + código pinado):** flag = `S3_n_desc_peaks ≥ 2`
de `skip_family_discovery.py` (**sha16 `b749b7a62386fd7c` PINADO — a implementação É a definição**),
onde ndesc conta **DEGRAUS descendentes do fim da lista de picos (≥2 degraus ⇒ ≥3 picos)**; bounce =
recuperação ≥1,5·ATR15 do low corrente seguida de novo low, desde o high-384.
**Declaração dura (DA edit 3): K=1,5 e ndesc≥2 são o ARGMAX da grelha de sensibilidade corrida
NESTA base (87% = máximo em ambas as dimensões)** — a otimização já aconteceu; congelar aqui só
impede RE-otimização, não desfaz a contaminação. Escopo BEAR-only congelado.

## 6. Eixos PROIBIDOS neste teste
S2b âncora HTF · S1 pos384 · S4 autoridade de região · S5 range-third · OB proximity · indicadores
novos · outcome/MFE/MAE como input · GT manual como seletor.

## 7. Composites (SÓ estes 4; TODOS já conhecidos/deriváveis — DA edit 1)
A. S2a only (21L/1W em 22) · B. S3 only (40L/6W em 46) · C. S2a OR S3 (51L/6W em 57, LOOK QUEIMADO)
· D. S2a AND S3 (**derivável: 11 marcados, 10L/1W** — both=11; L: 21+40−51; W: 1+6−6).
**Nenhum composite produz headline novo. O run formaliza o painel §8 + responde SÓ às perguntas
abertas do §2.** Árbitro de decisão = janela virgem 2024-25/próximo bear, nunca esta base.

## 8. Métricas (todas, por composite)
BEAR candidates total (78) · losers skipped · winners skipped · winners preserved · losers
remaining · skip precision (L skipped / total skipped) · false-skip rate (W skipped / 17) ·
overlap S2a∩S3 · S2a-only · S3-only · **losers remaining vs fasquia ≤10** (nota: 61 losers no
universo; o caminho ≤10 refere-se à estratégia downstream completa — aqui mede-se a contribuição
BEAR) · counts por EPISÓDIO/cluster (agrupamento por semana ISO + gap ≥48h entre candidatos;
resultado dependente de 1 episódio = falha §10).

## 9. O que está PRÉ-DECIDIDO (DA edit 2 — sem teatro decisório)
Declarado a priori, dos números conhecidos: **C FALHA as cláusulas de winners** (+5W adicionais vs
A; falsa-skip 6/17=35%); **D ⊆ A nunca adiciona losers** (melhoria-material-sobre-A é impossível
por construção); "corta a maioria" → A não (21/61) · B sim · C sim · D não; sensibilidade <70% já
se sabe passar (mínimo da grelha = 73% — critério removido como decisão). Critérios de contagem de
winners (n=17; 1 winner = 5,9pp) = **DESCRITIVOS, nunca gates**.

## 10. Critérios ABERTOS (os únicos decidíveis pelo run)
(a) **Concentração episódica**: os cortes de B e do incremento C∖A concentram-se? FALHA se >50% dos
cortes incrementais **de C sobre A** caírem numa única semana ISO. Cluster = semana ISO; candidatos
na mesma semana com gap <48h = 1 episódio (regra única, sem ambiguidade).
(b) **Null cluster-aware** (§11) com P>0,05 = FALHA.

## 11. Null / DA (obrigatórios; algoritmo por extenso — DA edit 5)
Já publicado (não re-descoberto): incremento C-sobre-A hipergeom p=0,0032. NOVO e único conteúdo
inferencial: **permutação por BLOCOS: unidade = semana ISO dentro do universo BEAR-78; permuta-se o
vetor de outcomes POR BLOCO inteiro (preserva autocorrelação intra-semana); 2000 trials; seed
20260709; estatística = losers cortados pelo incremento C∖A; P = fração de trials ≥ observado.**
DA adversarial real antes de qualquer conclusão. Todos os looks no claims ledger.

## 12. Interpretação permitida (teto)
Mesmo se forte: **`BEAR_ONLY_SKIP_COMPOSITE = CALIBRATION_RESULT_NOT_VALIDATED`**.
NUNCA: `APPROVED_STRATEGY` · `PRODUCTION_READY`. Validação = janela virgem 2024-25 + próximo bear +
revisão visual do Cris.

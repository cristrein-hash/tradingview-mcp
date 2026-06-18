# XAU 4H L2/BPT — Auditoria E1/E17 Exit + SL

**Status:** `RESEARCH · DIAGNOSTIC · NO_PRODUCTION · NO_SLIM · NO_PROMOTION · n=2` · **Data:** 2026-06-18
Auditoria trade-a-trade de E1/E17 (big V-reversal winners mutados) para decidir se o exit aprovado partial50@2R+6R precisa exceção. Método: matriz 2×2 {SL estrutural vs tight} × {6 variantes de exit} + verificação de drawdown (MAE-antes-MFE). DA dedicado. Não promove regra.

---

## 1. Executive summary

**A causa da mutação de E1/E17 NÃO é o partial — é o SL, e o SL é grande porque a seleção de pivô pega fundo demais.** Sob o SL estrutural swing-origin, E1 e E17 **nunca chegam a +2R** (MFE E1 +0.84R, E17 +1.28R), então **TODAS as 6 variantes de exit dão R idêntico** (mecânica: o exit não dispara abaixo de +2R). O compressor é o SL: E17 pivô a **8.36ATR** (risk 129pts), E1 a **5.30ATR**. **Verificação de drawdown refuta survivorship:** E17 subiu **+10.7ATR com −0.04ATR de drawdown** (nunca underwater); E1 fez **+4.5ATR/60b (+7.7ATR/120b) com só −0.63ATR de drawdown**. Ou seja, ambos subiram quase reto — um SL defendido tight (~0.5-1ATR) os capturaria como monumentais reais (E17 +5.9R, E1 +4.5R/60b) **sem ser survivorship**. **Mesma causa raiz do E13** (seleção de pivô errada — E13 raso demais, E1/E17 fundo demais). **Recomendação: manter partial50@2R+6R SEM exceção** (o exit está exonerado por mecânica, não dispara); o lever real é **seleção de swing defendido (SL/entrada)**, não o exit. Sem produção, nada promovido.

## 2. Reconstrução E1/E17 (`results/l2_bpt_e1_e17_exit_sl_audit.csv`)

| | E1 | E17 |
|---|---|---|
| entry_ts | 2020-03-23 22:00 | 2020-04-01 14:00 |
| entry / ATR | 1572.7 / 22.68 | 1582.4 / 15.46 |
| SL estrutural (swing-origin) | 5.30ATR (120pts) | **8.36ATR (129pts)** |
| SL tight (6-bar) | 3.96ATR | 1.03ATR |
| **MFE sob SL estrut** | **+0.84R** (nunca +1R) | **+1.28R** (+1R@bar42, nunca +2R) |
| MAE sob SL estrut | −0.12R | −0.00R |
| maxHigh 60b / 120b | +4.5ATR / +7.7ATR | +10.7ATR / +10.7ATR |
| **drawdown real (pior low antes do pico)** | **−0.63ATR** | **−0.04ATR** |
| partial sai / runner BE | nunca (não atinge +2R) | nunca (não atinge +2R) |

## 3. Diagnóstico da causa (Tarefa 2)

**Causa = `SL_TOO_LARGE_COMPRESSES_R`, que é consequência de seleção de pivô fundo demais.** NÃO é `PARTIAL50_CAPS_TAIL` nem `BE_ON_RUNNER_TOO_EARLY`.

- **Qual componente corta mais R: SL largo ou partial/BE?** **SL largo, sem ambiguidade.** Prova mecânica: sob o SL estrutural nenhum dos dois atinge +2R, então o partial/BE **literalmente nunca dispara** — as 6 variantes dão R idêntico (E1 +0.64, E17 +0.91). O exit não pode mutar o que não toca.
- **E1/E17 deixam de ser monumentais por causa do partial?** NÃO. **Por causa do SL grande?** SIM. Com SL tight a R explode (E17 +0.91→+5.9R no no-partial+6R; veja §4).
- **Pivô fundo demais:** os dois trades subiram quase reto (drawdown −0.04/−0.63ATR), logo a estrutura defendida real está a ~0.5-1ATR — mas o `m_swing` (pivô 5/5 mais recente abaixo da entrada) pegou o low do **crash COVID** muito mais fundo. **Mesma família do E13** (raso demais): a heurística de seleção de pivô é o elo fraco, nos dois sentidos.
- **E1 — time-stop é o culpado?** Secundário. Em 60b E1 já faz +4.5ATR (= +4.5R num SL ~1ATR); o time-stop só limita o extra (+7.7ATR em 120b). O primário continua sendo o SL largo.

## 4. Variantes de exit (diagnóstico, não promover) — Tarefa 3

| Variante | E1 (SL estrut / tight) | E17 (SL estrut / tight) |
|---|---|---|
| A partial50@2R+6R (atual) | +0.64 / +0.88 | +0.91 / **+3.90** |
| B no-partial +3R | +0.64 / +0.88 | +0.91 / +2.90 |
| C no-partial +6R | +0.64 / +0.88 | +0.91 / **+5.90** |
| D partial25@2R runner75 +6R | +0.64 / +0.88 | +0.91 / +4.90 |
| E partial50@3R +6R | +0.64 / +0.88 | +0.91 / +4.40 |
| F partial50@2R BE-only-after+3R | +0.64 / +0.88 | +0.91 / +3.90 |

**Leitura:** sob o SL estrutural, TODAS as variantes são iguais (não dispara). A diferença só aparece quando o SL é tight — e aí o que governa é o SL, não a escolha de exit (E17 vai de +0.91R para +3.9-5.9R só por apertar o SL). Confirma: **o exit não é a alavanca; o SL é.** Nenhuma variante "salva" E1/E17 mantendo o SL estrutural. Risco de virar loser: nenhuma variante vira loser (não há trade-off de downside aqui — o problema é upside comprimido pelo SL).

## 5. Assinatura causal — é identificável antes do outcome? (Tarefa 4)

E1: rsi 62.4, bear_leg=SIM, demand 3.51ATR, NAS LONG@0b, reclaim verde body60%. E17: rsi 40.7, bear_leg=SIM, demand **0.03ATR** (na demanda), NAS LONG@3b, reclaim verde body11%. Ambos = **V-reversal de bear** (bear_leg + reclaim + demand + NAS LONG) — assinatura **identificável na entrada (causal, não hindsight)**. **MAS** (DA): n=2 é **lead, não regra** (calibração ≠ validação). E como o fix é SL-selection e não exit, a assinatura alimenta o trabalho de SL/entrada, não uma exceção de exit.

## 6. Recommendation (Tarefa 5) — Opção 1

**Manter partial50@2R+6R SEM exceção.** Justificativa: o exit está **exonerado por mecânica** (não dispara abaixo de +2R; irrelevante para E1/E17), não por uma edge frágil de 2 trades. Criar exceção de exit para V-reversal seria **overfit resolvendo o componente errado**.

**Porém o sistema não está clean-billed** — esta auditoria indicia, como itens SEPARADOS de pesquisa (não exit):
- **SL pivot-selection (defended-swing):** E13 (raso), E1/E17 (fundo) → a heurística "pivô 5/5 mais recente" falha nos dois sentidos. Lever real = selecionar o **swing defendido** (o que de fato segurou, ~pior low antes da continuação), não o mais recente nem o mais fundo. Re-derivar o SL *tradeable* de E17 buscando a banda 0.5–8.36ATR com checagem MAE-antes-MFE (já parcialmente feito: drawdown −0.04ATR ⇒ SL ~0.5ATR serviria).
- **Time-horizon (E1):** secundário; o time-stop 60b limita a cauda multi-semana (+4.5→+7.7ATR). Considerar só depois do SL.

**partial50 segue APROVADO. SL estrutural segue APROVADO como direção** (com o refinamento de pivot-selection sinalizado). Nada de exceção de exit.

## 7. DA appendix

DA dedicado (6º da frente). Respostas:
- **Exceção usa info causal ou hindsight?** N/A — recomendando NENHUMA exceção. A assinatura V-reversal é causal mas n=2 = lead.
- **Teste limitado a 2 trades?** SIM, explicitamente diagnóstico. Mas a conclusão "partial não é a causa" é **certeza MECÂNICA** (o exit não dispara <+2R), independente de amostra — não uma claim estatística sobre 2 trades.
- **Tentando salvar monumentais por overfit?** NÃO — recomendação é contra qualquer exceção de exit.
- **Survivorship no SL tight?** Refutado por dado: E17 drawdown −0.04ATR, E1 −0.63ATR — subiram quase reto; SL defendido tight é tradeable, não survivorship.
- **partial serve ao prop-firm?** SIM (inalterado). **SL estrutural aprovado?** SIM (com refinamento pivot-selection). **Produção?** Intacta.
- **DA caveat incorporado:** E1 (time-horizon) e E17 (SL pivot) são modos de falha distintos — não tratar como uma classe "V-reversal" única; ambos compartilham a raiz pivot-too-deep mas E1 tem componente time-stop adicional. n=2 signature = lead, não finding.

---

*Outputs: `results/l2_bpt_e1_e17_exit_sl_audit.csv`. Script: `/tmp/e1e17_audit.py`. Sem produção, sem SLIM, sem chart, exit inalterado.*

# RETOMA ENGINE v1 — PREREG FORWARD (congelado 2026-07-27)

XAU 15M LONG · **retoma-de-demanda em higher-low** — a camada órfã do router em regime BEAR/recuperação.
Aprovado Cris 2026-07-27 ("SEGUE COM O ENGINE DE RETOMA PELO MÉTODO CANÓNICO"). Alert-only impossível:
**DRY puro** (0 Telegram) até este prereg passar.

## Origem (caracterização, research/cp_char_fresh_bottoms_20260727.py)
4 fundos ideais do Cris (A 16/07 3969 · B 20/07 3998 · C 24/07 4044 · D 27/07 4065): zero passa os gates
do Cp e cada um falha um MIX diferente (não há limiar único para "afinar"); 3/4 são HIGHER-LOWS de retoma,
não capitulações; TODOS têm reclaim. Classe estruturalmente distinta → engine próprio; **Cp congelado intocado**.

## Definição CONGELADA (my-strategy/research/revalidation/retoma_engine_v1.py)
Candidato = TODAS as condições:
1. Swing-low fractal M=3 confirmado (p+3) — verbatim Cp.
2. `legMag >= 8×ATR` — PRINCÍPIO "metade do canónico Cp (15)": queda real, não ruído. NÃO derivado dos GT.
3. `cp.fundo_ok(p) is None` — complemento do Cp por construção (zero overlap de sinais).
4. ANCORAGEM: low dentro de zona de demanda EXISTENTE (OB/SMC do store, nunca inventada) ou <=0.5×ATR
   da borda superior — lição S1 aprovada.
5. Gatilho = `entry_first` verbatim Cp (1º reclaim C>H[-1] e C>O em p+3..p+96 sem tocar SL).
6. SL = min(zona.low, low do fundo) − 0.1×ATR (padrão dos SLs estruturais do Cris, 3997.55×3) · alvo 3R fixo.
7. Leilão (buy_dens/leg_sell) = VOZ registada, NUNCA veto.

## DA lookahead (obrigatório, executado 2026-07-27)
- Caminho preço→entrada→outcome: **LIMPO** (fractal p+3, ATR lag, reclaim sem índice futuro, SL-first,
  AMBIG contado como perda).
- **CIRCULARIDADE RETRO (material):** zonas do store = snapshot sem data de criação; em B/C/D o zona.low
  ≈ low do próprio fundo → a validação retroativa da ancoragem valida-se a si própria. **Consequência
  assumida: o painel in-sample (N44 WR41% +28R) e o GT 4/4 = caracterização direcional APENAS, nunca
  evidência de edge.**
- Null in-sample usou SL diferente do motor (não comparável 1:1) — declarado.
- Bubbles sem known_at (caveat herdado do próprio baseline Cp).

## Forward limpo POR CONSTRUÇÃO (a resposta ao DA)
Coletor = ramo BEAR do router (`ENTRY_ROUTER/run_router_cycle.py::run_retoma`, ciclo 900s DRY):
- Zonas **as-of do ciclo** (só existe o que existe no momento) e **gravadas no registo** (`zona_asof`) — auditável.
- Só regista candidato com **entrada fresca <=2 barras** — o passado NUNCA é varrido com zonas de hoje.
- Ledger `.router_state/retoma_ledger.jsonl`, dedup por fundo_t, resolve OPEN→WIN/LOSS SL-first a cada ciclo.

## Balizas PASS (padrão B-engine; congeladas AGORA, antes de qualquer dado forward)
- N >= 20 candidatos RESOLVED no forward.
- hit-3R >= 45% · streak <= 5 · expectância líquida > 0.
- Bater o null buy-any-reclaim da MESMA janela forward com o MESMO SL estrutural (correção do defeito i do DA).
- Só depois: decisão do Cris sobre Telegram/produção (`RETOMA_PRODUCTION_AUTHORIZED`).

## Invalidação declarada
Se o forward mostrar que os "higher-lows em demanda" em BEAR são facas disfarçadas (WR << null), a camada
morre — não se afina ao resultado (feedback_principio_vs_fit).

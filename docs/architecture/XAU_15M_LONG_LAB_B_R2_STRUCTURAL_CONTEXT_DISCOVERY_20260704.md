# LAB B r2 — STRUCTURAL CONTEXT · DISCOVERY (2026-07-04)

**Engine multi-agente real:** workflow `wf_6e643ea3-184` (4 perspectivas — Market Structure, Regime Box, Runner Preservation, Streak/DD — + DA-pré + síntese; 413k tokens, 98 tool-calls; subagents sem commit, git log verificado). Fontes obrigatórias do mandato lidas (maturação, Labs A/E/F/G, RAW extension, L2/BPT, room_above, refutações). Priors duros injetados: vacuidade P3 · room_above anti-monotônico · fail-then-fire · anatomy 97% · "topo-de-box96 paga" · rota F4.

## 1. Achado central (convergência genuína de 4 buscas independentes): **TESE FUNDADORA REFUTADA COMO CORTE**
Supply-overhead / topo-de-perna / teto-480 / MTF-sky apertado **NÃO carregam toxicidade residual pós-gates da base — carregam PRÊMIO** (flagged avg +0,62 a +2,78 NET; conv4 avgNET +2,78 e htfceil +1,87 verificados pelo DA — o "+0,881" original era de outra métrica; CONV4 com taxa de runner 31,8% ✓). SKIP por teto = taxar os pagadores. Runners vivem no meio-alto/teto (miolo legpos60 [0,49-0,76) = 26/53 runners, +126,6 NET). Estende o prior P3 de vacuidade para INVERSÃO DE SINAL. → vira **FB1 ANTI-VETO TETO** (canon negativo + classes protegidas full-size).

## 2. Onde os losers realmente moram: **FUNDO/early-leg sem estrutura** (FB2)
`legpos60≤0,25 AND h1_pos≤0,61` → 42/435, WR 33,3 (o "28,6" original do agente não reproduziu — correção DA), flagged −6,0 NET; SKIP daria +239,6, DD −23%, stk 8→6, nulls week-aware p≤0,0005. **MAS** DA-pré (fatal parcial): os 2 runner-kills são AMBOS de 2026 (+3,7/+3,5) — o regime vigente contradiz exatamente nos runners; CAL8⊂E2 (convergência ilusória); CAL5 puro positivo. → demovida para **SIZE_50 via F4 (floor 0,5, nunca 0)**; SKIP BLOQUEADO até forward-ledger na extensão RAW.

## 3. Demais famílias congeladas
**FB3** limbo pós-breakout (BULL sob teto herdado do regime anterior + confirmação): 16/435, −9,5 NET, **0 runner-kill**, null p=0,0025 — CANDIDATE em prateleira (OR precisa colapsar; morto COMO resposta a DD/streak). **FB4** classes p/ F4: QUICKPOP (room_above≤1,11: WR62, pouco combustível → gestão de alvo) · KNIFE_RUNNER (ema21_dist≤0,16: WR31 mas 13/53 runners → nunca zerar). **FB5** forward-ledger congelado (CONV1/EXT/CAL3/CAL4/H4_MIDLID; DEADMID = KILL por sentinela+não-reprodução).

## 4. Ledger + honestidade
~100+ predicados examinados sobre o MESMO N435; zero correção formal de multiplicidade; nulls pós-seleção → **TUDO = CALIBRAÇÃO** (canon 45-grupos). Única evidência robusta a fitting = a refutação do teto (negativa). **Exigência aceita: DD −14,2 e stk −8 NÃO são endereçáveis por contexto estrutural ex-ante sem taxar payers** — rota viva = F4 sizing + canon anti-veto-teto. Árbitro final = extensão RAW futura (não-BEAR).

## 5. Incidente de integridade (registrado)
Durante o workflow, `results/lab_g_candidates.jsonl` foi clobberado por symlink de agente-irmão (04:01) e regenerado; valores canônicos re-verificados (4739 · 435 · +233,6 · 53) e o arquivo foi SELADO (sha256 `f27fb229f9159a8c521347114ea0652c3aac26ca81d4abc326d40d8a7c9e3ee9` em `results/lab_g_candidates.sha256` + chmod a-w). Regra nova: subagents não escrevem no dir compartilhado; asserts de integridade no preâmbulo de todo script da rodada.

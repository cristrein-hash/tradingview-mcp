# L1 NAS-LIVE REMEDIATION — Devil's Advocate (final)

**2026-07-09.** DA real (Agent tool, general-purpose) com leituras MCP read-only ao vivo + testes de fronteira dos guards + leitura do código/ledger/LaunchAgent. Verdict: **PASS — RESOLVED-FOR-DRYRUN.**

## 1. Source DA — CONCERN
- Live agora: NAS `pkqE7L` devolve `n_bars=50`, 50 distâncias não-nulas, 9 ≥1.31. Fix a funcionar, estável (não transiente).
- `phase_pass` do probe = lógica sólida.
- FLAW de evidência (não do fix): o probe salvo mostra `visible_before=true` (foi re-run após o toggle). O toggle real `false→true` ocorreu na 1ª execução (out de bash), não no JSON salvo. A mudança de visibilidade **não é code-controlled** → caveat (a): reload de layout reverte → série vazia → fail-closed non-firing.

## 2. Causality DA — OK (sem leak)
- SHIFT1 = `previous_closed_bar_time` (i-1), nunca eval/forming. `closed_idx` = maior índice com `now≥t+14400`; forming excluído.
- Ledger congelado: cycle N persiste bar N → cycle N+1 lê bar N como i-1. Sem forward leak. T4 provou NAS(i)=9.99 não usado (usa 1.50).
- **Observação decisiva do DA:** a barra forming `1783562400` mudou `-1.063→-1.2045` entre leituras, enquanto fechadas `1783533600/548000` byte-idênticas por horas → (a) fechadas estáveis, (b) prova porque excluir forming + congelar é necessário.
- `live_shift1` garantidamente não-None antes do bloco ledger (alignment já bloqueia) → não há via de o ledger disparar sem match live.

## 3. Runtime safety DA — OK + flag de postura
- Fail-closed em todos os modos (missing/mismatch/corrupt→block). 7/7 wiring reproduzido.
- `scanner.py` intacto (`git diff` vazio): 1.31/3.0/0.1/-9.35. Só `runtime_xau.py` mudou (working-tree).
- Produção OFF: `com.cristrein.xau-l1-cycle` não em `launchctl list`; `RunAtLoad=false`; sem cron.
- **FLAG pré-existente (não introduzido/nem corrigido aqui):** plist tem `--send-telegram` e consumer allow-listed → emissão gated só pelo agente descarregado, não por lock de código. Recomendar dry-run lock antes de go-live.

## 4. Data integrity DA — OK
- Guard testado na fronteira: 2017→`epoch_out_of_range`; `1_499_999_999`→reject / `1.5e9`→`far_from_ref`; 29d ok / 31d reject; futuro/string/huge reject.
- Entrada 2017 real do ledger agora **inerte na leitura** (`bar_time_guard`), não re-gravável.
- Retrocompat: 27 entradas antigas (sem symbol/tf) legíveis; wrong-symbol ainda bloqueia.
- Conflicting-dup rejeitado. Minor: janela de 30d torna as entradas de Junho ilegíveis em ~1 semana (cache rolante, irrelevante p/ i-1 ~4h).

## 5. Production readiness DA — CONCERN (coverage gap), sem overclaim
- Rótulo correto = RESOLVED-FOR-DRYRUN (não live). Probes escopados a causalidade/wiring, não a autorização de produção.
- **Residual (b) real:** zero cross-check numérico live/ledger-vs-RAW (janelas disjuntas). Ponte ao edge backtestado = mesmo-indicador + concordância de escala, não prova de equivalência.
- Residual (a) chart-state e (c) warmup fail-close: ambos fail-safe.

## Ledger autoritário = melhoria líquida, não fragilidade
A prova "live não-repinta (49 idênticas)" é fraca (leituras a segundos, mesmos bars carregados; não cobre formação de barra nova — e o DA apanhou o forming a repintar). O **congelamento-no-fecho do ledger é a proteção real** de repaint; a dupla-leitura é substituto fraco. Exigir ambos (ledger + match live) só adiciona modos de falha **conservadores** (bloqueia quando ledger ausente mesmo com live ok) — todos fail-closed, nenhum dispara errado.

## Veredito final
**PASS — RESOLVED-FOR-DRYRUN.** Sem leak de causalidade, sem via de disparo live, sem bug de guard/wiring. SHIFT1 provadamente i-1-congelado + cross-check + fail-closed; scanner/1.31/3.0/0.1 intactos; 2017 inerte; produção descarregada. Rótulo honesto: **"pronto para production-gate dry-run", NÃO produção live.** 3 caveats obrigatórios (a/b/c) + flag pré-existente do plist `--send-telegram` a resolver com dry-run lock antes de go-live.

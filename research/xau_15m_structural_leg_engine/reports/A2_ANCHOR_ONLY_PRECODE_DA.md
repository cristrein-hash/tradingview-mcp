# DA PRÉ-CÓDIGO — A2-ANCHOR-ONLY (2026-07-09)

> Devil's Advocate real (Agent tool, general-purpose, read-only + 2 sondas GT-free declaradas)
> atacando a spec A2 ANTES de codar. 10 frentes do Cris + bónus de ambiguidades.

## Verdict original: `BLOCKED_A2_SPEC_AMBIGUOUS` → **resolvido no mesmo dia (spec v1.1 §13 + manifest v1.2)**
"Não é lookahead by design — a disciplina known_at/first_valid_bar é correta e executável."
Bloqueios eram: 1 contradição com o manifest, 1 gap de desenho quantificado, ~12 ambiguidades.
**Todos os edits exigidos foram aplicados → status efetivo: `PASS_READY_TO_CODE_A2_F0_F15`.**

## Ataques CONFIRMADOS → resoluções
- **A. Manifest proibia a mecânica** (stop-condition "pivô confirmado-por-rally" escrita pré-A2) →
  manifest v1.2: stop-condition reescrita na forma EPISTÉMICA (proibido = USO retroativo/entry no
  evento; reversor por threshold com uso só-futuro = permitido por decisão do Cris); r_cycle/pos96
  registados no grid; outputs A2 declarados; citação de versão corrigida.
- **B. Gap de polaridade QUANTIFICADO (o achado central):** sonda GT-free — cobertura de fundos da
  máquina por região-fundo ativa = 15,7% (r=4), MAS por **topo rompido-para-cima (suporte convertido)
  = 40,3%**; a demanda da escada é o último topo rompido (assimilação PLT/DM: único discriminador na
  direção certa) e a v1 matava a região-topo exatamente no breakout → **spec §13.2: topo quebrado
  vira `converted_support` (evento versionado); gate mede os DOIS canais separados** — a tese dos
  35 prints do Cris entra na máquina.
- **C. Dente fingido no passo 3** → §13.3: passo 3 = REPORT-PARA-DECISÃO-DO-CRIS declarado sem dente
  automático; dente automático só no passo 1; **sem contingência de grid A2** (0/3 = BLOCKED).
- **D. pos96 não captura o trap dominante** (92,9-95,8% dos fundos retestados são depois invalidados)
  → §13.4: métrica `retested→invalidated` por contexto e canal.
- **E. Densidade 5-9× o GT em r=4** (12,7 regiões/sem vs GT 0,7/sem) → declarado; FP/dia e
  regiões/semana no report; ponto de operação = Cris.
- **F. Campo boilerplate** `no_entry_on_confirmation` → agora COMPUTADO e asserido no guard.
- **G. Grid vs drop BULL 2,8 ATR** → risco declarado + sem expansão silenciosa.
- **12 ambiguidades** (origem do ciclo, estado inicial, warmup, reteste-vs-invalidação na mesma
  barra, pos96, empate, convenções da marca, edge cases, vida da região, estados, source bars,
  n do truncation) → TODAS fechadas em §13.5, uma a uma.

## Ataques REFUTADOS (o núcleo está limpo)
Confirmação NUNCA vira entry (não existe camada de entry; geometria: no flip o close está ≥4 ATR
acima do low, fora da banda) · proibição executável (known_at + first_valid_bar + testes explícitos)
· a banda-fundo É retestada (80-88%; 1º reteste p50 12h em r=4 — dentro da janela 10-38h do modo
reteste do Cris; modo lag-curto 1,5-2,2h declarado inalcançável) · cobertura causal bem definida ·
RAW HD only (cadeia F0 sha-verified; GT só na avaliação com import-guard) · estrutura/indicador/entry
separados (camada 100% price-only; macro v5 verbatim causal).

## Sondas
2 SANITY_PROBEs GT-free (zero toques em PLT/DM/42/50/INVALIDO; zero looks de gate queimados),
ledgered como probes GT-free no claims_ledger.

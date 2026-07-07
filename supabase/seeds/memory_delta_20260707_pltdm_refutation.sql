-- ============================================================================
-- SUPABASE MEMORY — DELTA SEED · seed:memory_delta_20260707_pltdm_refutation
-- ============================================================================
-- Bloco: refutacao da hipotese "significancia" dos PLT + reframe sequencial (2026-07-07, pos-rejeicao Cris).
-- APLICACAO: autonoma via scripts/supabase/apply_memory_delta.py.
-- ROLLBACK: delete from memory_items where tags @> array['seed:memory_delta_20260707_pltdm_refutation'];
-- Total: 1 row.
-- ============================================================================
begin;

insert into memory_items (id, scope, visibility, category, title, body, tags, source_ref, status) values
(
  md5('seed:memory_delta_20260707_pltdm_refutation:memory_items:pltdm-caminhada-sequencial-pernas')::uuid,
  'product', 'internal', 'project',
  'PLT/DM = caminhada sequencial de pernas (processo), NAO feature de snapshot — hipotese significancia REFUTADA; Cris rejeitou fronteira recall/N por miopia',
  'Cris REJEITOU a fronteira recall x N do detector PLT/DM: "ainda estas a achar fundos de forma MIOPE, nao por evento contextual; nao me sugiras mais seguimentos INDUTIVOS." Diagnostico permanente aceito: os meus calculos limitam-se ao tempo-grafico LOCAL (zigzag r=3 = poucas barras) enquanto PLT/DM abrangem SEMANAS — miopia recorrente (ja aconteceu varias vezes; por isso Cris pediu analise por EVENTO com GRANDE intervalo de tempo). Escala macro diaria testada (bottom_macro_event / bottom_active_demand_20260707.py): densidade 6-11:1 NAO aceitavel; a maquina de UMA demanda ativa (ultimo higher-low) MISSA os proprios fundos PLT/DM do Cris (09-02/04/11/30, 10-14/15/17) -> "ultimo higher-low" != a DM dele. REFUTACAO CENTRAL (plt_significance_20260707.py): medida a historia de largo-contexto dos 10 PLT ANTES do rompimento -> os PLT do Cris NAO sao resistencias significativas: mediana 1 reacao (varios FRESCOS, span 0d: 09-11@3625, 10-14@4178); topos genericos rompidos tem MAIS historia (mediana 4 reacoes); 31% dos genericos ja batem a fasquia de significancia dos PLT -> significancia NAO seleciona. CONCLUSAO: o que define um PLT nao e atributo estatico da barra; e a POSICAO SEQUENCIAL no markup — a referencia da perna CORRENTE, marcada ao CAMINHAR a estrutura perna-a-perna. A diferenca N926->N54 EXISTE mas vive no PROCESSO sequencial (caminhada das pernas), nao numa feature de snapshot; todo filtro por-barra/pool bate no muro por procurar PROPRIEDADE onde ha PROCESSO. LICAO DE METODO PERMANENTE: quando um label manual do Cris resiste a toda separacao por feature, considerar que e um PROCESSO sequencial/path-dependente, nao uma propriedade — modelar como automato de estado que caminha a estrutura, nao como filtro de pool. AGUARDA decisao de paradigma do Cris (AskUserQuestion sem resposta): (1) automato de caminhada de pernas [1 referencia/perna]; (2) Cris marca as pernas macro e eu ancoro; (3) leitura evento-a-evento 1-a-1 sem produzir N/densidade ate o criterio estar claro. NAO disparar mais detetores agregados sem essa decisao.',
  array['seed:memory_delta_20260707_pltdm_refutation','pltdm','caminhada-pernas-sequencial','miopia-tempo-grafico','processo-nao-feature','licao-metodo','aguarda-decisao-cris'],
  'docs/architecture/XAU15M_PLTDM_ASSIMILATION_20260707.md sec 6b; plt_significance/bottom_macro_event/bottom_active_demand_20260707.py (commit 603198a)',
  'active'
)
on conflict (id) do nothing;

commit;

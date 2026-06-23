#!/usr/bin/env python3
"""PACOTE DE LEITURA CEGO (fase 2) — cluster 3a (24) + continuação 3b 4926.
Emite, por episódio, o dossiê SEM outcome e SEM leitura prévia (para não ancorar o Reader fresco):
Camada 1 (backbone) · Camada 0 (forma + sequência 4H real) · Camada 2 (perguntas vivas + foreground + probes) ·
3a (sósias: superfície idêntica + weekly/cascade que VARIAM, sem mfe) · 3b (âncora + irmão, sem mfe).
Guard: remove _AUDIT/mfe/runner/monumental e prior_living_reading ANTES de emitir. Outcome só na fase 3.
Saída: results/blind_pack_cluster4918/reading_packet_BLIND.md"""
import json, csv
D = "results"; OUT = f"{D}/blind_pack_cluster4918"
SOS = {int(r['bar_idx']): r for r in csv.DictReader(open(f"{D}/l2_bpt_sosia_clusters.csv"))}
DOSS = {}
for l in open(f"{D}/l2_bpt_reader_dossier_276.jsonl"):
    r = json.loads(l)
    # GUARD cego: remove TODO outcome + leitura prévia
    r.pop("_AUDIT_outcome_NOT_FOR_READING", None)
    r.pop("prior_living_reading", None)
    for x in r.get("camada_3a_sosias", {}).get("sosias_same_surface", []):
        x.pop("_AUDIT_mfe_R", None); x.pop("_AUDIT_mfe_R_source", None)
    for x in r.get("camada_3b_continuation", {}).get("siblings", []):
        x.pop("_AUDIT_mfe_R", None); x.pop("_AUDIT_mfe_R_source", None)
    DOSS[int(r["bar_idx"])] = r

# membros: cluster 24 (superfície) + 4926 (continuação 3b)
cl24 = sorted(b for b, r in SOS.items() if r['cluster_id'] == SOS[4918]['cluster_id'])
MEMBERS = cl24 + [4926]
def fn(v):
    try: return float(v)
    except (TypeError, ValueError): return None

L = []; a = L.append
a("# PACOTE DE LEITURA CEGO — cluster 4918 (3a superfície) + continuação 3b\n")
a("> LEITURA CEGA: zero outcome, zero R, zero futuro pós-entry. Você lê a estrutura ATÉ a entry e interpreta livre.")
a("> NÃO classifique TAKE/SKIP. NÃO pontue. NÃO some fatores. Leia o EPISÓDIO, não meça o trade.\n")
a("## A superfície é IDÊNTICA — o discriminador está FORA dela (Camada 1)")
a("Todos os sósias compartilham flush=FLUSH_V · clean_sky=True · demand=DEMAND_SUPPORTING_RETEST · acceptance=ACCEPTED_ABOVE_RES.")
a("O que VARIA (e onde mora a leitura):\n")
a("| bar | data | weekly | cascade | (4926=continuação, superfície diferente) |")
a("|---|---|---|---|---|")
for b in MEMBERS:
    r = SOS.get(b, {})
    tag = "  ← continuação 3b do 4918" if b == 4926 else ""
    a(f"| {b} | {r.get('datetime','?')[:10]} | {r.get('weekly','?')} | {r.get('cascade','?')} |{tag} |")
a("")

for b in MEMBERS:
    d = DOSS[b]; c1 = d["camada_1_backbone"]; c0 = d["camada_0_form"]
    pf = c0.get("path_form_276", {}); mic = c0.get("micro_fields_276", {})
    wk = c1.get("weekly_1d_context", {}); rb = c1.get("regime_B", {})
    c2 = d["camada_2_evidence"]; s3a = d["camada_3a_sosias"]; s3b = d["camada_3b_continuation"]
    a("\n" + "=" * 96)
    a(f"## EPISÓDIO {b}  ({d['timestamp']})" + ("   [continuação 3b — superfície diferente dos sósias]" if b == 4926 else "   [sósia de superfície, cluster 24]"))
    wks = fn(wk.get("weekly_slope_decisions")); wks = wks if wks is not None else fn(wk.get("weekly_slope_20pct"))
    a(f"\n### Camada 1 — backbone (FIXAR PRIMEIRO)")
    a(f"- leg={c1.get('macro_reader_leg')} | weekly_slope={('%.3f'%wks) if wks is not None else '?'} | cascade={rb.get('cascade_score')} "
      f"| combined={rb.get('combined_score')} | macro_broken={rb.get('macro_broken')} | v3={rb.get('v3_state')}")
    a(f"- sup_cat={c1.get('sup_cat')} | pol_cat={c1.get('pol_cat')} | clean_sky={c1.get('clean_sky')} | bottom_turn={c1.get('bottom_turn')}")
    a(f"\n### Camada 0 — forma viva")
    a(f"- path: flush={pf.get('flush')} (drop={pf.get('drop_atr')}ATR vel={pf.get('flush_velocity_atr_bar')}) | "
      f"sweep_low_reclaim={pf.get('sweep_low_reclaim')} depth={pf.get('sweep_depth_atr')} | acceptance={pf.get('acceptance')} | "
      f"structure={pf.get('structure')} BOS={pf.get('BOS')} CHoCH={pf.get('CHoCH')}")
    a(f"- rsi={mic.get('rsi')} rsi_min8={mic.get('rsi_min8')} | dist_supply={mic.get('dist_4h_supply_low_atr')}ATR | dist_demand={mic.get('dist_4h_demand_low_atr')}ATR | dist_POC={pf.get('dist_poc_atr')}ATR")
    seq = c0.get("price_sequence_4h") or []
    a(f"- forma 4H real (últimas {min(14,len(seq))} barras 4H até a entry):")
    for bar in seq[-14:]:
        mk = "ENTRY>" if bar.get("entry") else "      "
        a(f"    {mk} {bar['t']}  O{bar['o']} H{bar['h']} L{bar['l']} C{bar['c']}  rng{bar['rng']} body{bar['body']:+}")
    a(f"\n### Camada 2 — perguntas vivas + lentes (evidência condicional; NÃO votar)")
    a(f"- perguntas ativas: {', '.join(c2.get('active_reading_objectives', [])) or '(nenhuma específica)'}")
    fg = c2.get("foreground_by_objective", {})
    for obj, lst in fg.items():
        if lst:
            a(f"  - {obj}: " + ", ".join(x['name'] for x in lst))
    pr = c2.get("contradiction_probes", [])
    a(f"- contradiction/invalidation probes ({len(pr)}): " + ", ".join(x['name'] for x in pr)
      + ("  [OBRIGATÓRIAS — sósia conflitante]" if c2.get("contradiction_probes_mandatory") else ""))
    a(f"\n### Camada 3a — sósias mesma superfície (o que varia FORA do match)")
    if s3a.get("available"):
        a(f"- cluster {s3a.get('cluster_id')} HARD={s3a.get('is_hard_cluster')} | este: weekly={s3a.get('this_episode',{}).get('weekly')} cascade={s3a.get('this_episode',{}).get('cascade')}")
        for x in s3a.get("sosias_same_surface", [])[:10]:
            # SEM block_type/decision (leitura prévia = ancoraria; Reader lê do zero)
            a(f"    - {x['bar_idx']} {x.get('datetime','')[:10]} weekly={x.get('weekly')} cascade={x.get('cascade')}")
    a(f"### Camada 3b — continuação estrutural")
    if s3b.get("available") and s3b.get("siblings"):
        a(f"- âncora swing-high bar {s3b.get('anchor_swinghigh_bar')} ({s3b.get('anchor_date')}) | irmãos de perna: "
          + ", ".join(str(x['bar_idx']) for x in s3b.get('siblings', [])))
    else:
        a("- (sem irmão de movimento)")

with open(f"{OUT}/reading_packet_BLIND.md", "w") as f:
    f.write("\n".join(L))
# verificação cega — tokens ESTRUTURADOS de outcome (não a palavra 'runner' em descrição de lente=metodologia)
blob = "\n".join(L).lower()
leak_tokens = [k for k in ("_audit", "mfe_r", "mfe=", "is_loser", "is_runner", "is_monumental",
                           "block_type", "block_decision", "provisional_decision") if k in blob]
print(f"PACOTE CEGO gerado: {OUT}/reading_packet_BLIND.md  ({len(MEMBERS)} episódios: {MEMBERS})")
print(f"  outcome/prior-leak no texto: {'NENHUM (PASS)' if not leak_tokens else 'FAIL '+str(leak_tokens)}  | prior_living_reading removido: PASS")
print("  (nota: palavras 'runner/monumental' que restem vêm de DESCRIÇÕES DE LENTES = metodologia, não outcome deste episódio)")
print("  contém: superfície idêntica + weekly/cascade variando + forma 4H + perguntas vivas + probes + 3a/3b. SEM outcome.")

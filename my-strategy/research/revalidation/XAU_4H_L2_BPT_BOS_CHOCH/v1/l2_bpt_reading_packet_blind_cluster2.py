#!/usr/bin/env python3
"""PACOTE DE LEITURA CEGO — Cluster 2 (10 episodios long em MACRO NEGATIVO, sub-blocos A/B/C/D).
TRAVAS DO CRIS (obrigatorias): o pacote NAO pode conter R / trap / runner / mfe / outcome / block_decision /
winner / loser / qualquer label de resultado / qualquer indicacao de qual episodio correu ou falhou.
=> NAO inclui Camada 2 (nomes de lentes vazam 'winners'/'loser'/'trap'); NAO inclui leitura previa; NAO inclui _AUDIT.
Sub-blocos A/B/C/D = estrutura de INVESTIGACAO (mecanismo), nunca rotulo de desfecho. Episodios = so pares em macro negativo.
Conteudo: Camada 1 (backbone) + Camada 0 (forma + sequencia 4H real) + 3a (sosias: weekly/cascade) + 3b.
Leak check ESTRITO no fim — se falhar, NAO escreve/para. Saida: results/blind_pack_cluster2/reading_packet_BLIND.md"""
import json, os, re, sys
D = "results"; OUT = f"{D}/blind_pack_cluster2"
os.makedirs(OUT, exist_ok=True)
DOSS = {}
for l in open(f"{D}/l2_bpt_reader_dossier_276.jsonl"):
    r = json.loads(l)
    r.pop("_AUDIT_outcome_NOT_FOR_READING", None)
    r.pop("prior_living_reading", None)
    r.pop("camada_2_evidence", None)   # <- nomes de lentes/objetivos vazam termos de resultado; FORA do pacote cego
    for x in r.get("camada_3a_sosias", {}).get("sosias_same_surface", []):
        x.pop("_AUDIT_mfe_R", None); x.pop("_AUDIT_mfe_R_source", None); x.pop("block_type", None); x.pop("block_decision", None)
    for x in r.get("camada_3b_continuation", {}).get("siblings", []):
        x.pop("_AUDIT_mfe_R", None); x.pop("_AUDIT_mfe_R_source", None)
    DOSS[int(r["bar_idx"])] = r

# sub-blocos = estrutura de investigacao (mecanismo). Perguntas NEUTRAS (sem implicar qual correu).
SUBBLOCKS = [
    ("A. macro negativo + CLEAN SKY", "clean sky em macro negativo significa espaco real para subir, ou apenas um repique dentro da queda?", [5826, 1623]),
    ("B. macro negativo + SUPPLY PROXIMO", "supply proximo aqui e combustivel a ser consumido por um impulso fresco, ou parede que rejeita em momentum fraco? (lente OM1)", [4401, 3825]),
    ("C. macro negativo + FLUSH sob supply", "o flush e capitulacao que esgota a venda, ou um repique dentro da queda?", [1522, 1873, 5627, 1775]),
    ("D. macro negativo EXTREMO (weekly ~-0.65)", "o que distingue os dois episodios em macro extremo, dado que a aceitacao de valor diverge entre eles?", [3949, 3929]),
]
def fn(v):
    try: return float(v)
    except (TypeError, ValueError): return None

L = []; a = L.append
a("# PACOTE DE LEITURA CEGO — Cluster 2: 10 long-setups em MACRO NEGATIVO (weekly<0, cascade profundo)\n")
a("> LEITURA CEGA: zero futuro pos-entry, zero resultado. Leia a estrutura ATE a entry e interprete livre.")
a("> NAO classifique TAKE/SKIP. NAO pontue. NAO some fatores. Leia o EPISODIO, nao meca o trade.\n")
a("## PERGUNTA VIVA")
a("Em macro negativo (weekly<0, cascade profundo), o que faz um long se desenvolver de verdade vs apenas repicar?")
a("Leia cada episodio cego e diga a NATUREZA + o que esperaria ver depois da entry se a leitura estiver correta.\n")
a("## TRAVA — o weekly NAO decide aqui")
a("Em TODOS os episodios weekly < 0 e cascade <= -2. NAO conclua nada SO do weekly (ele e negativo em todos).")
a("Procure o MECANISMO mais fundo: maturidade da queda, capitulacao real vs repique, base/absorcao, reclaim sustentado,")
a("supply consumida vs supply-parede, mudanca de value, continuidade estrutural, compressao antes da expansao.")
a("Os sub-blocos A/B/C/D sao estrutura de INVESTIGACAO (cada um isola um mecanismo) — procure o mecanismo, nao 'a regra do cluster'.\n")
a("## Contexto (todos macro negativo) — campos que variam FORA do regime")
a("| sub | bar | data | weekly | cascade | flush | acceptance | rsi | dist_supply_atr | dist_demand_atr | structure |")
a("|---|---|---|---|---|---|---|---|---|---|---|")
for title, q, members in SUBBLOCKS:
    for b in members:
        d = DOSS[b]; c1 = d["camada_1_backbone"]; c0 = d["camada_0_form"]
        pf = c0.get("path_form_276", {}); mic = c0.get("micro_fields_276", {}); rb = c1.get("regime_B", {})
        wk = c1.get("weekly_1d_context", {})
        weekly = fn(wk.get("weekly_slope_decisions")); weekly = weekly if weekly is not None else fn(wk.get("weekly_slope_20pct"))
        a(f"| {title[0]} | {b} | {d['timestamp'][:10]} | {round(weekly,2) if weekly is not None else '?'} | {rb.get('cascade_score')} | "
          f"{pf.get('flush')} | {pf.get('acceptance')} | {mic.get('rsi')} | {mic.get('dist_4h_supply_low_atr')} | {mic.get('dist_4h_demand_low_atr')} | {pf.get('structure')} |")

for title, q, members in SUBBLOCKS:
    a("\n" + "#" * 100)
    a(f"# SUB-BLOCO {title}")
    a(f"**Pergunta de investigacao:** {q}")
    a(f"**Episodios (pares em macro negativo — sem rotulo de desfecho):** {members}\n")
    for b in members:
        d = DOSS[b]; c1 = d["camada_1_backbone"]; c0 = d["camada_0_form"]
        pf = c0.get("path_form_276", {}); mic = c0.get("micro_fields_276", {})
        wk = c1.get("weekly_1d_context", {}); rb = c1.get("regime_B", {})
        s3a = d["camada_3a_sosias"]; s3b = d["camada_3b_continuation"]
        wks = fn(wk.get("weekly_slope_decisions")); wks = wks if wks is not None else fn(wk.get("weekly_slope_20pct"))
        a("\n" + "=" * 92)
        a(f"## EPISODIO {b}  ({d['timestamp']})")
        a(f"\n### Camada 1 — backbone (NOTE: weekly NEGATIVO; nao decida so por ele)")
        a(f"- leg={c1.get('macro_reader_leg')} | weekly_slope={('%.3f'%wks) if wks is not None else '?'} | cascade={rb.get('cascade_score')} "
          f"| combined={rb.get('combined_score')} | macro_broken={rb.get('macro_broken')} | v3={rb.get('v3_state')}")
        a(f"- sup_cat={c1.get('sup_cat')} | pol_cat={c1.get('pol_cat')} | clean_sky={c1.get('clean_sky')} | bottom_turn={c1.get('bottom_turn')}")
        a(f"\n### Camada 0 — forma viva")
        a(f"- path: flush={pf.get('flush')} (drop={pf.get('drop_atr')}ATR vel={pf.get('flush_velocity_atr_bar')}) | "
          f"sweep_low_reclaim={pf.get('sweep_low_reclaim')} depth={pf.get('sweep_depth_atr')} | acceptance={pf.get('acceptance')} | "
          f"structure={pf.get('structure')} BOS={pf.get('BOS')} CHoCH={pf.get('CHoCH')}")
        a(f"- rsi={mic.get('rsi')} rsi_min8={mic.get('rsi_min8')} | dist_supply={mic.get('dist_4h_supply_low_atr')}ATR | "
          f"dist_demand={mic.get('dist_4h_demand_low_atr')}ATR | dist_POC={pf.get('dist_poc_atr')}ATR")
        seq = c0.get("price_sequence_4h") or []
        a(f"- forma 4H real (ultimas {min(14,len(seq))} barras 4H ate a entry):")
        for bar in seq[-14:]:
            mk = "ENTRY>" if bar.get("entry") else "      "
            a(f"    {mk} {bar['t']}  O{bar['o']} H{bar['h']} L{bar['l']} C{bar['c']}  rng{bar['rng']} body{bar['body']:+}")
        a(f"\n### Camada 3a/3b (contraste estrutural)")
        if s3a.get("available"):
            a(f"- 3a cluster {s3a.get('cluster_id')} | este weekly={s3a.get('this_episode',{}).get('weekly')} cascade={s3a.get('this_episode',{}).get('cascade')}")
            for x in s3a.get("sosias_same_surface", [])[:8]:
                a(f"    - sosia {x['bar_idx']} {x.get('datetime','')[:10]} weekly={x.get('weekly')} cascade={x.get('cascade')}")
        if s3b.get("available") and s3b.get("siblings"):
            a(f"- 3b ancora swing-high {s3b.get('anchor_swinghigh_bar')} ({s3b.get('anchor_date')}); irmaos: " + ", ".join(str(x['bar_idx']) for x in s3b.get('siblings', [])))
        else:
            a("- 3b: sem irmao de movimento")

text = "\n".join(L)
# ---- LEAK CHECK ESTRITO (Cris) — se falhar, NAO escreve e para ----
FORBIDDEN = ["runner", "trap", "winner", "loser", "mfe", "outcome", "block_decision", "block_type",
             "provisional", "_audit", "is_loser", "is_runner", "monument"]
low = text.lower()
hits = {w: low.count(w) for w in FORBIDDEN if w in low}
# 'R' isolado de resultado (ex '+18R'): procura digito seguido de R isolado
rmult = re.findall(r"\b\d+(?:\.\d+)?\s*r\b", low)
if hits or rmult:
    print("LEAK CHECK FALHOU — pacote NAO escrito. Corrija antes do Reader.")
    print(f"  termos proibidos encontrados: {hits}")
    print(f"  padroes R-multiple: {rmult[:10]}")
    sys.exit(1)
with open(f"{OUT}/reading_packet_BLIND.md", "w") as f:
    f.write(text)
print(f"PACOTE CEGO Cluster 2 gerado: {OUT}/reading_packet_BLIND.md")
print(f"  10 episodios, 4 sub-blocos (A clean-sky, B supply-proximo, C flush, D extremo)")
print(f"  LEAK CHECK ESTRITO: PASS (0 termos proibidos: {FORBIDDEN})")
print("  SEM Camada 2 (nomes de lentes vazariam termos) · SEM leitura previa · SEM _AUDIT · SEM rotulo de desfecho.")
print("  weekly NEGATIVO em todos (nao e o discriminador). Sub-blocos = estrutura de investigacao.")

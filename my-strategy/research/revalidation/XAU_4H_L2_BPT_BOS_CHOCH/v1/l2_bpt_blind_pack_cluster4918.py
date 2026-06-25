#!/usr/bin/env python3
"""VISUAL BLIND PACK — pré-entry, cego ao outcome (fase 1 do dossiê interpretativo do cluster 4918).

REGRAS (Cris, travas críticas):
  read-only · NÃO toca produção/chart/MCP · plot ESTÁTICO LOCAL do RAW canônico · corte NA ENTRY (zero barras
  futuras) · SEM outcome/R/winner-loser/exit/target-hit/stop-hit · mesmo template + mesma janela p/ todos ·
  camadas só se CAUSAIS (senão UNKNOWN, não inventa) · SEM classificar TAKE/SKIP · SEM conclusão interpretativa.

CEGO AO _AUDIT: este script NUNCA lê `_AUDIT_outcome_NOT_FOR_READING` nem mfe/runner/monumental. Remove esses
campos do dossiê ANTES de usar (guard explícito). Outcome só entra na FASE 3 (audit pós-leitura), outro script.

Fonte: repro_recovery/raw_features_2020_2026.jsonl (4H frozen) + repro_recovery/XAU_1D_ohlc.jsonl (1D, D-1) +
results/l2_bpt_reader_dossier_276.jsonl (só campos NÃO-audit: forma/path/backbone/sósia-superfície/continuação-âncora).
Saída: results/blind_pack_cluster4918/<bar>.png + manifest.json + report.txt.
"""
import json, csv, hashlib, datetime as dt, os
from PIL import Image, ImageDraw, ImageFont

D = "results"; RR = "repro_recovery"
OUT = f"{D}/blind_pack_cluster4918"
os.makedirs(OUT, exist_ok=True)
CLUSTER = [4918, 4926, 1661, 5701, 8878, 6887]
W = 110            # janela 4H (barras lead-in até a entry, inclusive) — MESMA p/ todos
D1_BARS = 60       # barras 1D (D-1, só dias COMPLETOS antes da entry)

# ---------------------------------------------------------------- dados (read-only)
RAWPATH = f"{RR}/raw_features_2020_2026.jsonl"
F = [json.loads(l) for l in open(RAWPATH)]
O = [r['open'] for r in F]; H = [r['high'] for r in F]; L = [r['low'] for r in F]
C = [r['close'] for r in F]; TS = [r['ts_epoch'] for r in F]
ATR = [None] * len(F); trs = []
for i in range(1, len(F)):
    trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
    if i >= 14:
        ATR[i] = sum(trs[i - 14:i]) / 14
D1 = [json.loads(l) for l in open(f"{RR}/XAU_1D_ohlc.jsonl")]
def d1ts(r): return r.get('ts_epoch') or r.get('ts') or r.get('time')
D1 = [r for r in D1 if d1ts(r) is not None]
D1.sort(key=lambda r: d1ts(r))

# dossiê — REMOVER tudo de outcome ANTES de usar (guard cego)
def strip_audit(d):
    d.pop("_AUDIT_outcome_NOT_FOR_READING", None)
    s3a = d.get("camada_3a_sosias", {})
    for x in s3a.get("sosias_same_surface", []):
        x.pop("_AUDIT_mfe_R", None); x.pop("_AUDIT_mfe_R_source", None)
    s3b = d.get("camada_3b_continuation", {})
    for x in s3b.get("siblings", []):
        x.pop("_AUDIT_mfe_R", None); x.pop("_AUDIT_mfe_R_source", None)
    return d
DOSS = {}
for l in open(f"{D}/l2_bpt_reader_dossier_276.jsonl"):
    r = strip_audit(json.loads(l))
    DOSS[int(r["bar_idx"])] = r

def d10(t): return dt.datetime.utcfromtimestamp(int(t)).strftime('%Y-%m-%d %H:%M')
def dday(t): return dt.datetime.utcfromtimestamp(int(t)).strftime('%Y-%m-%d')
def fn(v):
    try: return float(v)
    except (TypeError, ValueError): return None

# bubble mapping CANÔNICO (memória feedback_validate_plot_id_mapping, confirmado 2026-06-07)
BUB = {"plot_0": ("BUY", "s"), "plot_2": ("BUY", "m"), "plot_4": ("BUY", "L"),
       "plot_6": ("SELL", "s"), "plot_8": ("SELL", "m"), "plot_10": ("SELL", "L"), "plot_12": ("POC", "")}
SZR = {"s": 3, "m": 5, "L": 8, "": 4}
CBUY = (0, 150, 150); CSELL = (210, 120, 0); CPOC = (140, 140, 140)  # teal/laranja — NÃO verde/vermelho (sem viés outcome)

# ---------------------------------------------------------------- fontes
def font(sz):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc"):
        try: return ImageFont.truetype(p, sz)
        except OSError: continue
    return ImageFont.load_default()
F11, F13, F16, F20 = font(11), font(13), font(16), font(20)

# ---------------------------------------------------------------- candle renderer (genérico)
def draw_candles(dr, bars, x0, y0, w, h, mark_last=True, fade_future_gutter=18):
    """bars = lista de dicts {o,h,l,c}. Desenha candles em [x0,x0+w]×[y0,y0+h]. Última barra = entry (linha vertical)."""
    lo = min(b['l'] for b in bars); hi = max(b['h'] for b in bars)
    pad = (hi - lo) * 0.06 or 1.0; lo -= pad; hi += pad
    def yof(p): return y0 + h - (p - lo) / (hi - lo) * h
    n = len(bars)
    usable = w - fade_future_gutter
    cw = usable / n
    bw = max(1, cw * 0.62)
    for i, b in enumerate(bars):
        cx = x0 + i * cw + cw / 2
        up = b['c'] >= b['o']
        col = (60, 70, 80) if up else (150, 60, 60)
        body = (90, 110, 130) if up else (180, 90, 90)
        dr.line([(cx, yof(b['h'])), (cx, yof(b['l']))], fill=col, width=1)
        yy = sorted([yof(b['o']), yof(b['c'])])
        dr.rectangle([cx - bw / 2, yy[0], cx + bw / 2, max(yy[1], yy[0] + 1)], fill=body, outline=col)
    if mark_last:
        ex = x0 + (n - 1) * cw + cw / 2
        dr.line([(ex, y0), (ex, y0 + h)], fill=(40, 120, 220), width=2)
        # gutter em branco à direita = "corte na entry, sem futuro"
        dr.rectangle([x0 + usable, y0, x0 + w, y0 + h], fill=(248, 249, 251))
    return yof, lo, hi, x0, cw, usable

# ---------------------------------------------------------------- render por episódio
manifest = {"source_4h": RAWPATH, "source_1d": f"{RR}/XAU_1D_ohlc.jsonl",
            "source_states": f"{D}/l2_bpt_reader_dossier_276.jsonl (campos NÃO-audit)",
            "sha256_4h": hashlib.sha256(open(RAWPATH, 'rb').read()).hexdigest()[:16],
            "window_4h_bars": W, "window_1d_bars_D-1": D1_BARS, "episodes": []}
WID, HGT = 1480, 1000

def render(b):
    dsr = DOSS.get(b, {})
    c1 = dsr.get("camada_1_backbone", {}); c0 = dsr.get("camada_0_form", {})
    pf = (c0.get("path_form_276") or {}); mic = (c0.get("micro_fields_276") or {})
    wk = (c1.get("weekly_1d_context") or {}); rb = (c1.get("regime_B") or {})
    s3a = dsr.get("camada_3a_sosias", {}); s3b = dsr.get("camada_3b_continuation", {})
    bars4h = [dict(o=O[j], h=H[j], l=L[j], c=C[j]) for j in range(b - W + 1, b + 1)]

    img = Image.new("RGB", (WID, HGT), (255, 255, 255)); dr = ImageDraw.Draw(img)
    # título — SEM outcome
    dr.text((20, 14), f"BLIND PACK (pré-entry, cego ao outcome) — bar_idx {b}  |  entry {d10(TS[b])} UTC",
            fill=(20, 20, 20), font=F20)
    dr.text((20, 40), "corte NA entry (linha azul) · sem barras futuras · sem R/winner-loser/exit · auction layers só causais",
            fill=(110, 110, 110), font=F11)

    # painel 4H principal
    cx0, cy0, cw_, ch = 20, 70, 1140, 470
    dr.rectangle([cx0, cy0, cx0 + cw_, cy0 + ch], outline=(210, 210, 210))
    dr.text((cx0 + 6, cy0 + 4), f"XAU 4H — {W} barras lead-in até a entry", fill=(90, 90, 90), font=F13)
    yof, lo, hi, gx0, gcw, usable = draw_candles(dr, bars4h, cx0, cy0 + 24, cw_, ch - 30)

    # overlays causais: demand/supply APROX (derivado de dist_atr — rotulado approx, não box exato)
    atr_b = ATR[b] or 0; cl_b = C[b]
    ds = fn(mic.get("dist_4h_supply_low_atr")); dd = fn(mic.get("dist_4h_demand_low_atr"))
    def hline(price, color, label):
        y = yof(price)
        if cy0 + 24 <= y <= cy0 + 24 + (ch - 30):
            for xx in range(int(gx0), int(gx0 + usable), 8):
                dr.line([(xx, y), (xx + 4, y)], fill=color, width=1)
            dr.text((gx0 + usable - 230, y - 13), label, fill=color, font=F11)
    if ds is not None and atr_b:
        hline(cl_b + ds * atr_b, (170, 70, 70), f"supply~ approx (+{ds:.2f}ATR, de dist)")
    if dd is not None and atr_b:
        hline(cl_b - dd * atr_b, (40, 130, 90), f"demand~ approx (-{dd:.2f}ATR, de dist)")

    # bubbles causais: aparição AT bar j (bars_ago==0) dentro da janela
    nb = 0
    for i, j in enumerate(range(b - W + 1, b + 1)):
        for bub in (F[j].get("bubbles_recent") or []):
            if bub.get("bars_ago") != 0:
                continue
            typ, sz = BUB.get(bub.get("plot_id"), (None, ""))
            if typ is None:
                continue
            cxp = gx0 + i * gcw + gcw / 2; r = SZR.get(sz, 4)
            if typ == "BUY":
                yb = yof(L[j]) + 6
                dr.polygon([(cxp, yb), (cxp - r, yb + r * 1.6), (cxp + r, yb + r * 1.6)], fill=CBUY)  # tri up-ish below
                nb += 1
            elif typ == "SELL":
                yb = yof(H[j]) - 6
                dr.polygon([(cxp, yb), (cxp - r, yb - r * 1.6), (cxp + r, yb - r * 1.6)], fill=CSELL)
                nb += 1
    # legenda bubbles
    dr.polygon([(cx0 + 8, cy0 + ch - 14), (cx0 + 3, cy0 + ch - 6), (cx0 + 13, cy0 + ch - 6)], fill=CBUY)
    dr.text((cx0 + 18, cy0 + ch - 16), "buy bubble", fill=CBUY, font=F11)
    dr.polygon([(cx0 + 100, cy0 + ch - 6), (cx0 + 95, cy0 + ch - 14), (cx0 + 105, cy0 + ch - 14)], fill=CSELL)
    dr.text((cx0 + 110, cy0 + ch - 16), "sell bubble  (sinal de auction, NÃO outcome)", fill=CSELL, font=F11)

    # painel 1D (D-1, só dias COMPLETOS antes da entry) — contexto superior
    entry_day0 = int(dt.datetime(*dt.datetime.utcfromtimestamp(TS[b]).timetuple()[:3]).replace(tzinfo=dt.timezone.utc).timestamp())
    d1c = [r for r in D1 if d1ts(r) < entry_day0][-D1_BARS:]
    dx0, dy0, dw, dh = 20, cy0 + ch + 16, 560, 300
    dr.rectangle([dx0, dy0, dx0 + dw, dy0 + dh], outline=(210, 210, 210))
    dr.text((dx0 + 6, dy0 + 4), f"XAU 1D — {len(d1c)} dias COMPLETOS antes da entry (D-1, sem o dia em curso)",
            fill=(90, 90, 90), font=F13)
    if d1c:
        # 1D RAW tem só time/high/low/close (sem open) -> HLC: open = close do dia anterior (encadeado)
        d1bars = [dict(o=(d1c[i - 1]['close'] if i > 0 else r['close']), h=r['high'], l=r['low'], c=r['close'])
                  for i, r in enumerate(d1c)]
        draw_candles(dr, d1bars, dx0, dy0 + 24, dw, dh - 30, mark_last=False, fade_future_gutter=4)

    # painel de ESTADOS CAUSAIS (do dossiê, sem outcome)
    px0, py0, pw, ph = 600, cy0 + ch + 16, 880, 300
    dr.rectangle([px0, py0, px0 + pw, py0 + ph], outline=(210, 210, 210))
    dr.text((px0 + 6, py0 + 4), "ESTADOS CAUSAIS (dossiê — sem outcome)", fill=(60, 60, 60), font=F13)
    wks = fn(wk.get("weekly_slope_decisions")); wks = wks if wks is not None else fn(wk.get("weekly_slope_20pct"))
    sosn = len(s3a.get("sosias_same_surface", [])) if s3a.get("available") else 0
    sibn = len(s3b.get("siblings", [])) if s3b.get("available") else 0
    def uk(v): return v if v not in (None, "", "None") else "UNKNOWN"
    lines = [
        f"Camada 1 backbone: leg={uk(c1.get('macro_reader_leg'))}  weekly_slope={('%.2f'%wks) if wks is not None else 'UNKNOWN'}"
        f"  cascade={uk(rb.get('cascade_score'))}  combined={uk(rb.get('combined_score'))}  v3={uk(rb.get('v3_state'))}",
        f"   sup_cat={uk(c1.get('sup_cat'))}  pol_cat={uk(c1.get('pol_cat'))}  clean_sky={uk(c1.get('clean_sky'))}  bottom_turn={uk(c1.get('bottom_turn'))}",
        "",
        f"Camada 0 forma/path: flush={uk(pf.get('flush'))} (drop={uk(pf.get('drop_atr'))}ATR vel={uk(pf.get('flush_velocity_atr_bar'))})"
        f"  sweep_low_reclaim={uk(pf.get('sweep_low_reclaim'))} depth={uk(pf.get('sweep_depth_atr'))}",
        f"   acceptance={uk(pf.get('acceptance'))}  structure={uk(pf.get('structure'))}  BOS={uk(pf.get('BOS'))}  CHoCH={uk(pf.get('CHoCH'))}",
        f"   rsi={uk(mic.get('rsi'))}  rsi_min8={uk(mic.get('rsi_min8'))}  dist_supply={uk(mic.get('dist_4h_supply_low_atr'))}ATR  dist_demand={uk(mic.get('dist_4h_demand_low_atr'))}ATR",
        f"   SVP: dist_POC={uk(pf.get('dist_poc_atr') or (dsr.get('engine_states_reference',{}).get('dspa_path',{}) or {}).get('dist_poc'))}ATR  (VAL/VAH exatos = UNKNOWN no RAW)",
        "",
        f"Camada 3a sósias mesma superfície: cluster={uk(s3a.get('cluster_id'))}  HARD={uk(s3a.get('is_hard_cluster'))}  n_sósias={sosn}",
        f"   superfície={s3a.get('surface_signature_matched') if s3a.get('available') else 'UNKNOWN'}",
        f"Camada 3b continuação: anchor_swinghigh={uk(s3b.get('anchor_swinghigh_bar'))} ({uk(s3b.get('anchor_date'))})  irmãos_de_perna={sibn}",
        "",
        f"bubbles plotadas (aparição causal na janela): {nb}   |   nas_recent@entry={len(F[b].get('nas_recent') or [])}   smc_recent@entry={len(F[b].get('smc_recent') or [])}",
    ]
    yy = py0 + 26
    for ln in lines:
        dr.text((px0 + 8, yy), ln, fill=(40, 40, 40), font=F11); yy += 17

    path = f"{OUT}/blind_{b}_{dday(TS[b])}.png"
    img.save(path)
    manifest["episodes"].append({"bar_idx": b, "entry_ts_utc": d10(TS[b]), "png": path,
                                 "window_4h_first_ts": d10(TS[b - W + 1]), "n_1d_bars": len(d1c),
                                 "bubbles_drawn": nb, "fields_used": ["o/h/l/c (4H RAW)", "ATR14",
                                 "dist_4h_supply/demand_low_atr (approx)", "bubbles_recent bars_ago==0",
                                 "weekly/cascade/leg/sup_cat (dossiê não-audit)", "3a surface", "3b anchor"]})
    return path

# ---------------------------------------------------------------- run
paths = [render(b) for b in CLUSTER]
json.dump(manifest, open(f"{OUT}/manifest.json", "w"), indent=2, ensure_ascii=False)

# report de no-outcome-leak (verificação explícita)
leak_checks = []
for b in CLUSTER:
    dsr = DOSS.get(b, {})
    has_audit = "_AUDIT_outcome_NOT_FOR_READING" in dsr  # já foi strip-ado
    sib_audit = any("_AUDIT_mfe_R" in x for x in dsr.get("camada_3b_continuation", {}).get("siblings", []))
    sos_audit = any("_AUDIT_mfe_R" in x for x in dsr.get("camada_3a_sosias", {}).get("sosias_same_surface", []))
    leak_checks.append((b, has_audit or sib_audit or sos_audit))
with open(f"{OUT}/report.txt", "w") as f:
    f.write("VISUAL BLIND PACK — cluster 4918 — relatório de integridade (fase 1, pré-entry)\n")
    f.write("="*88 + "\n")
    f.write(f"episódios: {CLUSTER}\n")
    f.write(f"janela 4H: {W} barras (mesma p/ todos) | 1D: {D1_BARS} dias D-1 completos | template idêntico\n")
    f.write("TRAVAS: candles cortam NA entry (range slice [b-W+1 : b+1], nenhuma barra após b); linha vertical na entry;\n")
    f.write("        sem outcome/R/winner-loser/exit/target-hit/stop-hit; bubbles=cor teal/laranja (buy/sell), NÃO verde/vermelho.\n")
    f.write("        demand/supply = APROX derivado de dist_atr (rotulado); SVP VAL/VAH exatos = UNKNOWN (não inventado).\n\n")
    leaked = [b for b, x in leak_checks if x]
    f.write(f"OUTCOME-LEAK CHECK: {'NENHUM (PASS)' if not leaked else 'VAZAMENTO em '+str(leaked)+' (FAIL)'}\n")
    f.write("  (dossiê foi strip-ado de _AUDIT/mfe/runner/monumental ANTES do uso; render nunca acessou outcome)\n\n")
    for b in CLUSTER:
        f.write(f"  bar {b}  entry {d10(TS[b])}  -> {OUT}/blind_{b}_{dday(TS[b])}.png\n")

print("VISUAL BLIND PACK gerado (fase 1, pré-entry, cego ao outcome).")
print(f"  {len(paths)} PNGs em {OUT}/")
for b in CLUSTER:
    print(f"    bar {b}  {d10(TS[b])}  -> blind_{b}_{dday(TS[b])}.png")
print(f"  manifest: {OUT}/manifest.json | report: {OUT}/report.txt")
print(f"  OUTCOME-LEAK: {'NENHUM (PASS)' if not [b for b,x in leak_checks if x] else 'FAIL '+str([b for b,x in leak_checks if x])}")
print("  Camadas causais: candles 4H + entry-cut + bubbles(buy/sell) + demand/supply approx + 1D D-1 + estados do dossiê.")
print("  SEM TAKE/SKIP, SEM conclusão interpretativa, SEM outcome. Fase 2 (leitura cega) só após tua revisão visual.")

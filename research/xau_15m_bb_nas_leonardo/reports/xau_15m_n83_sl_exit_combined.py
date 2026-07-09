#!/usr/bin/env python3
"""FASE 8 — COMBINED SL+EXIT (N83). Achado F6: SL atual (A) domina TODAS as alternativas em todas as
métricas -> não há 'melhor SL' a combinar; a matriz reduz-se à escolha de exit sob SL atual.
Documenta as 4 células pedidas + flag exploratory (best-of-5 exits). Output: ..._combined_result.json."""
import json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
sl=json.load(open(HERE/"xau_15m_n83_sl_review_result.json"))["alts"]
ex=json.load(open(HERE/"xau_15m_n83_exit_review_result.json"))["alts"]
cur_sl_cur_exit=ex["C_fixed_3R_current"]
best_sl=max(sl.items(),key=lambda kv:(kv[1]["sumR"],kv[1]["PF"] or 0))
best_ex=max(ex.items(),key=lambda kv:(kv[1]["sumR"],kv[1]["PF"] or 0))
res={"finding_f6":"SL atual (A demand-0.1ATR V1) DOMINA todas as alternativas (sumR/WR/PF/DD/streak) -> best_SL = current",
     "cells":{
        "current_sl_current_exit":{"sumR":cur_sl_cur_exit["sumR"],"WR":cur_sl_cur_exit["WR"],"DD":cur_sl_cur_exit["maxDD_R"],"streak":cur_sl_cur_exit["streak"]},
        "best_sl_current_exit":{"name":best_sl[0],"note":"= current (A venceu)","sumR":best_sl[1]["sumR"]},
        "current_sl_best_exit":{"name":best_ex[0],"sumR":best_ex[1]["sumR"],"WR":best_ex[1]["WR"],"DD":best_ex[1]["maxDD_R"],"streak":best_ex[1]["streak"],
                                 "flag":"EXPLORATORY (best-of-5 exits pré-registrados; multiplicidade não paga; exige robustez F9 + DA)"},
        "best_best":"= current_sl + best_exit (mesma célula acima)"},
     "decision_pending":"F9 robustez + F10 DA antes de qualquer decisão; default = KEEP_CURRENT_SL_EXIT salvo robustez clara"}
(HERE/"xau_15m_n83_sl_exit_combined_result.json").write_text(json.dumps(res,indent=2,ensure_ascii=False))
print(json.dumps(res,indent=2,ensure_ascii=False))

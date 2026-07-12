#!/usr/bin/env python3
"""QUERY (plano Cris/Claude-chat 2026-07-12, ponto 3): exposição dos sets L1/L2 à janela
macro-range congelada 2021-05-01..2022-10-31 — decide se a camada de contenção tem valor
prático para o sistema real ou é research sem exposição. Query pura, sem outcome/tuning."""
import json, csv, datetime as dt
from collections import Counter
from pathlib import Path
BASE = Path(__file__).resolve().parent
A = dt.datetime(2021, 5, 1, tzinfo=dt.timezone.utc).timestamp()
B = dt.datetime(2022, 11, 1, tzinfo=dt.timezone.utc).timestamp()

def ep(s, fmt): return dt.datetime.strptime(s, fmt).replace(tzinfo=dt.timezone.utc).timestamp()
def w(ts): return sum(1 for t in ts if A <= t < B)
def rng(ts):
    ts = sorted(ts); f = "%Y-%m-%d"
    return (dt.datetime.utcfromtimestamp(ts[0]).strftime(f),
            dt.datetime.utcfromtimestamp(ts[-1]).strftime(f))

def main():
    L1 = json.load(open(BASE/"XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/l1_approved34.json"))
    l1_ts = [ep(t["ts"], "%Y-%m-%dT%H:%M") for t in L1]
    final = json.load(open(BASE/"XAU_4H_LONG_CONTINUATION_L1_EMA21_A_F5/l1_FINAL_regime_gated.json"))["trades"]
    f_ts = [ep(t["ts"], "%Y-%m-%dT%H:%M") for t in final]
    rows = list(csv.DictReader(open(BASE/"XAU_4H_L2_BPT_BOS_CHOCH/v1/results/l2_bpt_uncapped_or_proxy_outcomes_276.csv")))
    l2_ts = [ep(r["datetime"], "%Y-%m-%d") for r in rows]
    print("L1-34 aprovadas: janela total", rng(l1_ts), "| em 2021-05..2022-10:", w(l1_ts), "/", len(l1_ts))
    print("L1-24 FINAL gated: janela total", rng(f_ts), "| em 2021-05..2022-10:", w(f_ts), "/", len(f_ts))
    print("L2-276: janela total", rng(l2_ts), "| em 2021-05..2022-10:", w(l2_ts), "/", len(l2_ts))
    print("L2 por ano:", dict(sorted(Counter(dt.datetime.utcfromtimestamp(t).year for t in l2_ts).items())))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""SHIM (AUDIT-FIX 19/08 D6): o módulo real é htf_location_gate.py — o nome antigo herdava a linha
reclaim (deletada 19/08) mas o gate é o HTF Location Gate genérico (aprovado Cris 17/08), consumido
pelo reader E2 (espelho SHORT). Import antigo continua a funcionar via este shim."""
from htf_location_gate import *          # noqa: F401,F403
from htf_location_gate import load_dossier, gate_short  # noqa: F401  (símbolos usados pelo e2)

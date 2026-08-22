# ADENDA V2 (selada 2026-08-22, aprovada Cris) — corrige os 2 desvios da auditoria

Mudanças vs prereg ff2caf2 (TUDO o resto igual, incluindo DA-fix fill-bar-SL):
A. CONFLUÊNCIA obrigatória: o FVG 15M elegível tem de SOBREPOR um FVG 1H bullish fresco (formado nas
   últimas 32 barras 1H, não-preenchido, computado causalmente do RAW 1H canónico). Zona de entrada =
   topo do FVG 15M (inalterado); a sobreposição qualifica, não muda níveis.
B. GATE DE REGIME como o live: barra i só é elegível se regime in (BULL, RANGE) pelo MESMO padrão do
   a1a2 live (Layer1 1D causal — labels do build_layer1 real, D-1); BEAR = sem setup.
Multiplicidade da série A2 declarada: 4º teste nos mesmos dados → gates NÃO relaxam (iguais ao ff2caf2:
N≥40 fills · sumR c0.35>0 · WR>null+3pp · sem semestre ≤−5R · jackknife). DA obrigatório.

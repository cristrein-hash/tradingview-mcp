# PACOTE DE LEITURA RAW-CLEAN POS-ANCHOR-FIX — Cluster 2 (macro negativo) — RAW-clean POS-FIX

> LEITURA CEGA, FONTE 100% RAW ORIGINAL, **backbone CAUSAL pos-fix** (commit 1267c8d: as-of join por
> timestamp real, 19/19 causal+exato, SEM look-ahead). Camada-1 (forma/supply-demand/regime), indicadores
> (NAS/SMC/bubbles/RSI) e volume RAW. TPO value-area = de TEMPO (proxy, NAO VA de volume). POC/VAL/VAH de
> VOLUME LuxAlgo = BLOCKED (nao serializado, nao inventado).
> SEM resultado/R/futuro pos-entry. NAO classifique TAKE/SKIP. Leia o EPISODIO; campos BLOCKED limitam a
> leitura — declare isso. (Esta e a base FINAL; os pacotes pre-fix sao historicos contaminados por look-ahead.)

## Contexto (regime RAW-derived price; supply/demand RAW Custom OB causal)
| sub | bar | data | weekly | cascade | sup_cat | clean_sky | distSup | distDem | tpo_acc | causal |
|---|---|---|---|---|---|---|---|---|---|---|
| A | 5826 | 2023-10-06 | -0.21 | -2 | SUPPLY_FAR | True | 5.86 | 1.7 | ACCEPTED_ABOVE_VALUE | True |
| A | 1623 | 2021-01-20 | -0.25 | -1 | SUPPLY_FAR | True | 9.93 | 0.48 | ACCEPTED_ABOVE_VALUE | True |
| B | 4401 | 2022-11-04 | -0.47 | -1 | SUPPLY_BLOCKS | False | 1.57 | 0.87 | INSIDE_VALUE | True |
| B | 3825 | 2022-06-23 | -0.27 | -2 | SUPPLY_NEAR | False | 0.61 | 0.35 | ACCEPTED_BELOW_VALUE | True |
| C | 1522 | 2020-12-23 | -0.3 | -1 | SUPPLY_FAR | False | 2.4 | 0.77 | INSIDE_VALUE | True |
| C | 1873 | 2021-03-18 | -0.49 | -3 | SUPPLY_BLOCKS | False | 1.23 | 2.31 | INSIDE_VALUE | True |
| C | 5627 | 2023-08-22 | -0.25 | -2 | SUPPLY_BLOCKS | False | 1.87 | 10.57 | ACCEPTED_BELOW_VALUE | True |
| C | 1775 | 2021-02-24 | -0.33 | -3 | SUPPLY_BLOCKS | False | 1.73 | 1.27 | ACCEPTED_BELOW_VALUE | True |
| D | 3949 | 2022-07-21 | -0.67 | -2 | SUPPLY_FAR | False | 2.42 | None | ACCEPTED_ABOVE_VALUE | True |
| D | 3929 | 2022-07-18 | -0.67 | -2 | SUPPLY_BLOCKS | False | 1.34 | 1.35 | INSIDE_VALUE | True |

##########################################################################################
# SUB-BLOCO A. macro negativo + CLEAN SKY


========================================================================================
## EPISODIO 5826 (2023-10-06 18:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.20672742120024806 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_FAR clean_sky=True has_overhead=True dist_supply=5.86ATR dist_demand=1.7ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.862 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_ABOVE_VALUE poc_tpo=1821.1 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1822.76 H1824.56 L1820.69 C1821.33
    O1821.33 H1822.3 L1818.58 C1820.44
    O1820.49 H1825.99 L1810.4 C1821.25
    O1821.28 H1834.85 L1820.91 C1831.78
    O1831.83 H1831.83 L1831.83 C1831.83

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['EQL', 'BOS', 'CHoCH', 'BOS', 'CHoCH'] | bubbles sell_mL=16 buy_mL=0 | RSI=51.60 div=nenhuma

========================================================================================
## EPISODIO 1623 (2021-01-20 03:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.24515687359469396 cascade=-1 combined=-1 macro_broken=True v3=TRANSITION (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_FAR clean_sky=True has_overhead=True dist_supply=9.93ATR dist_demand=0.48ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=0.143 last6_up=0.217 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_ABOVE_VALUE poc_tpo=1839.36 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1844.69 H1845.3 L1833.06 C1835.9
    O1835.87 H1843.42 L1833.37 C1840.84
    O1840.82 H1841.31 L1837.09 C1839.99
    O1839.66 H1850.43 L1839.46 C1849.83
    O1849.78 H1849.78 L1849.78 C1849.78

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'SHORT', 'LONG'] | SMC(RAW)=['BOS', 'CHoCH', 'CHoCH', 'CHoCH', 'CHoCH'] | bubbles sell_mL=0 buy_mL=0 | RSI=49.49 div=nenhuma

##########################################################################################
# SUB-BLOCO B. macro negativo + SUPPLY PROXIMO


========================================================================================
## EPISODIO 4401 (2022-11-04 02:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.4691936913007228 cascade=-1 combined=-1 macro_broken=True v3=TRANSITION (fidelity=False)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.57ATR dist_demand=0.87ATR
- anchor: causal=True exato=True close_fidelity=False warnings=['regime close fidelity vs RAW > 1pct', 'anchor close fidelity vs frozen > 0.5pct (feed RAW != frozen)']
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.723 | tpo_acceptance(TEMPO,NAO-volume)=INSIDE_VALUE poc_tpo=1628.53 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1624.18 H1625.06 L1616.64 C1619.3
    O1619.59 H1631.6 L1618.9 C1629.4
    O1629.45 H1632.35 L1628.5 C1629.57
    O1629.43 H1633.94 L1628.6 C1633.85
    O1633.89 H1633.89 L1633.89 C1633.89

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'SHORT', 'SHORT'] | SMC(RAW)=['BOS', 'CHoCH', 'EQL', 'BOS', 'BOS'] | bubbles sell_mL=11 buy_mL=0 | RSI=50.02 div=nenhuma

========================================================================================
## EPISODIO 3825 (2022-06-23 02:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.26997088709584843 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_NEAR clean_sky=False has_overhead=True dist_supply=0.61ATR dist_demand=0.35ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=0.885 last6_up=0.244 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_BELOW_VALUE poc_tpo=1837.32 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1828.63 H1847.82 L1827.33 C1844.53
    O1844.39 H1845.3 L1835.75 C1840.67
    O1840.65 H1841.72 L1837.3 C1837.95
    O1837.01 H1838.63 L1832.88 C1833.08
    O1833.09 H1833.09 L1833.09 C1833.09

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'BOS', 'CHoCH', 'BOS', 'CHoCH'] | bubbles sell_mL=0 buy_mL=0 | RSI=47.75 div=nenhuma

##########################################################################################
# SUB-BLOCO C. macro negativo + FLUSH sob supply


========================================================================================
## EPISODIO 1522 (2020-12-23 23:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.29687934753456635 cascade=-1 combined=-1 macro_broken=True v3=TRANSITION (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_FAR clean_sky=False has_overhead=True dist_supply=2.4ATR dist_demand=0.77ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=0.0 last6_up=0.765 | tpo_acceptance(TEMPO,NAO-volume)=INSIDE_VALUE poc_tpo=1870.2 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1865.59 H1872.33 L1863.83 C1865.64
    O1865.7 H1878.51 L1857.06 C1876.5
    O1876.5 H1877.42 L1869.96 C1873.27
    O1873.31 H1874.01 L1869.85 C1873.13
    O1872.26 H1872.26 L1872.26 C1872.26

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'SHORT'] | SMC(RAW)=['EQH', 'CHoCH', 'BOS', 'CHoCH', 'CHoCH'] | bubbles sell_mL=0 buy_mL=2 | RSI=52.77 div=nenhuma

========================================================================================
## EPISODIO 1873 (2021-03-18 22:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.48772223687760213 cascade=-3 combined=-3 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.23ATR dist_demand=2.31ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=0.0 last6_up=0.573 | tpo_acceptance(TEMPO,NAO-volume)=INSIDE_VALUE poc_tpo=1733.11 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1750.04 H1752.88 L1732.7 C1736.65
    O1736.71 H1737.69 L1719.23 C1723.04
    O1722.99 H1736.23 L1721.47 C1734.7
    O1734.69 H1737.27 L1732.35 C1736.46
    O1734.53 H1734.53 L1734.53 C1734.53

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'CHoCH', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=0 buy_mL=1 | RSI=54.90 div=['Regular Bearish']

========================================================================================
## EPISODIO 5627 (2023-08-22 14:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.24545820039007285 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.87ATR dist_demand=10.57ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=0.0 last6_up=0.443 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_BELOW_VALUE poc_tpo=1895.06 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1894.68 H1897.27 L1893.63 C1895.07
    O1895.08 H1897.28 L1893.81 C1895.39
    O1895.41 H1903.71 L1895.08 C1902.78
    O1902.77 H1904.44 L1889.13 C1890.3
    O1890.29 H1890.29 L1890.29 C1890.29

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'BOS', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=15 buy_mL=0 | RSI=48.77 div=nenhuma

========================================================================================
## EPISODIO 1775 (2021-02-24 15:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.32880931965237004 cascade=-3 combined=-3 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.73ATR dist_demand=1.27ATR
- anchor: causal=True exato=True close_fidelity=False warnings=['anchor close fidelity vs frozen > 0.5pct (feed RAW != frozen)']
- SVP/acceptance: volume RAW entry_up=0.0 last6_up=0.066 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_BELOW_VALUE poc_tpo=1805.88 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1804.86 H1813.83 L1804.71 C1810.26
    O1810.25 H1811.16 L1806.04 C1808.33
    O1808.21 H1810.14 L1803.13 C1807.19
    O1807.16 H1810.26 L1783.56 C1785.68
    O1785.67 H1785.67 L1785.67 C1785.67

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'CHoCH', 'BOS', 'CHoCH', 'BOS'] | bubbles sell_mL=4 buy_mL=0 | RSI=55.17 div=nenhuma

##########################################################################################
# SUB-BLOCO D. macro negativo EXTREMO


========================================================================================
## EPISODIO 3949 (2022-07-21 18:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.6656697849668259 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_FAR clean_sky=False has_overhead=True dist_supply=2.42ATR dist_demand=NoneATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.627 | tpo_acceptance(TEMPO,NAO-volume)=ACCEPTED_ABOVE_VALUE poc_tpo=1690.69 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1692.11 H1693.84 L1690.81 C1693.15
    O1693.14 H1693.77 L1682.19 C1684.46
    O1684.51 H1710.35 L1680.87 C1705.76
    O1705.76 H1718.27 L1703.7 C1713.81
    O1713.82 H1713.82 L1713.82 C1713.82

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['BOS', 'BOS', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=5 buy_mL=0 | RSI=54.01 div=nenhuma

========================================================================================
## EPISODIO 3929 (2022-07-18 10:00)

### Camada 1 backbone (RAW causal pos-fix)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.6656697849668259 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB, causal): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.34ATR dist_demand=1.35ATR
- anchor: causal=True exato=True close_fidelity=True warnings=[]
- SVP/acceptance: volume RAW entry_up=1.0 last6_up=0.64 | tpo_acceptance(TEMPO,NAO-volume)=INSIDE_VALUE poc_tpo=1712.95 | POC/VAL/VAH de VOLUME = **UNKNOWN_BLOCKED**

### Camada 0 forma (RAW OHLC causal, ultimas barras ate a entry)
    O1704.93 H1707.07 L1703.56 C1707
    O1707.12 H1714.57 L1705.87 C1714.31
    O1714.36 H1718.24 L1713.15 C1714.42
    O1714.4 H1723.87 L1711.82 C1722.06
    O1722.07 H1722.07 L1722.07 C1722.07

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['BOS', 'BOS', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=10 buy_mL=0 | RSI=51.02 div=nenhuma
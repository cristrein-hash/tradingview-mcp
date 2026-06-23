# PACOTE DE LEITURA RAW-CLEAN — Cluster 2 (macro negativo) — RAW-clean

> LEITURA CEGA, FONTE 100% RAW ORIGINAL. Camada-1 (forma/supply-demand/regime) reconstruida do RAW;
> indicadores (NAS/SMC/bubbles/RSI) do RAW; SVP/acceptance = BLOCKED_UNMAPPED (nao computado, nao inventado).
> SEM resultado/R/futuro pos-entry. NAO classifique TAKE/SKIP. Leia o EPISODIO; campos BLOCKED limitam a leitura — declare isso.

## Contexto (regime RAW-derived price; supply/demand RAW Custom OB)
| sub | bar | data | weekly | cascade | sup_cat(RAW) | clean_sky | distSup | distDem |
|---|---|---|---|---|---|---|---|---|
| A | 5826 | 2023-10-06 | -0.21 | -2 | SUPPLY_FAR | True | 5.86 | 1.7 |
| A | 1623 | 2021-01-20 | -0.25 | -1 | SUPPLY_FAR | True | 9.63 | 0.78 |
| B | 4401 | 2022-11-04 | -0.47 | -1 | SUPPLY_NEAR | False | 0.27 | 2.17 |
| B | 3825 | 2022-06-23 | -0.27 | -2 | SUPPLY_NEAR | False | 0.39 | 0.57 |
| C | 1522 | 2020-12-23 | -0.3 | -1 | SUPPLY_BLOCKS | False | 1.92 | 0.9 |
| C | 1873 | 2021-03-18 | -0.49 | -3 | SUPPLY_BLOCKS | False | 1.54 | 0.08 |
| C | 5627 | 2023-08-22 | -0.25 | -2 | SUPPLY_NEAR | False | 0.84 | 11.59 |
| C | 1775 | 2021-02-24 | -0.33 | -3 | SUPPLY_NEAR | False | 0.65 | 2.35 |
| D | 3949 | 2022-07-21 | -0.67 | -2 | SUPPLY_FAR | False | 2.42 | None |
| D | 3929 | 2022-07-18 | -0.67 | -2 | SUPPLY_BLOCKS | False | 1.64 | 1.05 |

##########################################################################################
# SUB-BLOCO A. macro negativo + CLEAN SKY


========================================================================================
## EPISODIO 5826 (2023-10-06 18:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.20672742120024806 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_FAR clean_sky=True has_overhead=True dist_supply=5.86ATR dist_demand=1.7ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1822.76 H1824.56 L1820.69 C1821.33
    O1821.33 H1822.3 L1818.58 C1820.44
    O1820.49 H1825.99 L1810.4 C1821.25
    O1821.28 H1834.85 L1820.91 C1831.78
    O1831.83 H1831.83 L1831.83 C1831.83

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['EQL', 'BOS', 'CHoCH', 'BOS', 'CHoCH'] | bubbles sell_mL=16 buy_mL=0 | RSI=51.60 div=nenhuma

========================================================================================
## EPISODIO 1623 (2021-01-20 03:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.24515687359469396 cascade=-1 combined=-1 macro_broken=True v3=TRANSITION (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_FAR clean_sky=True has_overhead=True dist_supply=9.63ATR dist_demand=0.78ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1835.87 H1843.42 L1833.37 C1840.84
    O1840.82 H1841.31 L1837.09 C1839.99
    O1839.66 H1850.43 L1839.46 C1849.83
    O1849.78 H1854.5 L1847.68 C1852.75
    O1852.72 H1852.72 L1852.72 C1852.72

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'SHORT', 'SHORT', 'LONG'] | SMC(RAW)=['BOS', 'CHoCH', 'CHoCH', 'CHoCH', 'CHoCH'] | bubbles sell_mL=0 buy_mL=0 | RSI=49.49 div=nenhuma

##########################################################################################
# SUB-BLOCO B. macro negativo + SUPPLY PROXIMO


========================================================================================
## EPISODIO 4401 (2022-11-04 02:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.4691936913007228 cascade=-1 combined=-1 macro_broken=True v3=TRANSITION (fidelity=False)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_NEAR clean_sky=False has_overhead=True dist_supply=0.27ATR dist_demand=2.17ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1619.59 H1631.6 L1618.9 C1629.4
    O1629.45 H1632.35 L1628.5 C1629.57
    O1629.43 H1633.94 L1628.6 C1633.85
    O1633.89 H1648.57 L1633.03 C1647.09
    O1647.14 H1647.14 L1647.14 C1647.14

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'SHORT', 'SHORT'] | SMC(RAW)=['BOS', 'CHoCH', 'EQL', 'BOS', 'BOS'] | bubbles sell_mL=11 buy_mL=0 | RSI=50.02 div=nenhuma

========================================================================================
## EPISODIO 3825 (2022-06-23 02:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.26997088709584843 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_NEAR clean_sky=False has_overhead=True dist_supply=0.39ATR dist_demand=0.57ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1844.39 H1845.3 L1835.75 C1840.67
    O1840.65 H1841.72 L1837.3 C1837.95
    O1837.01 H1838.63 L1832.88 C1833.08
    O1833.09 H1835.08 L1831.11 C1834.79
    O1834.75 H1834.75 L1834.75 C1834.75

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'BOS', 'CHoCH', 'BOS', 'CHoCH'] | bubbles sell_mL=0 buy_mL=0 | RSI=47.75 div=nenhuma

##########################################################################################
# SUB-BLOCO C. macro negativo + FLUSH sob supply


========================================================================================
## EPISODIO 1522 (2020-12-23 23:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.29687934753456635 cascade=-1 combined=-1 macro_broken=True v3=TRANSITION (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.92ATR dist_demand=0.9ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1865.7 H1878.51 L1857.06 C1876.5
    O1876.5 H1877.42 L1869.96 C1873.27
    O1873.31 H1874.01 L1869.85 C1873.13
    O1872.26 H1879.97 L1871.01 C1876.96
    O1876.94 H1876.94 L1876.94 C1876.94

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'SHORT'] | SMC(RAW)=['EQH', 'CHoCH', 'BOS', 'CHoCH', 'CHoCH'] | bubbles sell_mL=0 buy_mL=2 | RSI=52.77 div=nenhuma

========================================================================================
## EPISODIO 1873 (2021-03-18 22:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.48772223687760213 cascade=-3 combined=-3 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.54ATR dist_demand=0.08ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1736.71 H1737.69 L1719.23 C1723.04
    O1722.99 H1736.23 L1721.47 C1734.7
    O1734.69 H1737.27 L1732.35 C1736.46
    O1734.53 H1737.76 L1728.49 C1731.25
    O1731.25 H1731.25 L1731.25 C1731.25

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'CHoCH', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=0 buy_mL=1 | RSI=54.90 div=['Regular Bearish']

========================================================================================
## EPISODIO 5627 (2023-08-22 14:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.24545820039007285 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_NEAR clean_sky=False has_overhead=True dist_supply=0.84ATR dist_demand=11.59ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1895.08 H1897.28 L1893.81 C1895.39
    O1895.41 H1903.71 L1895.08 C1902.78
    O1902.77 H1904.44 L1889.13 C1890.3
    O1890.29 H1899.13 L1890.06 C1897.68
    O1897.72 H1897.72 L1897.72 C1897.72

### Indicadores (RAW): NAS(RAW)=['SHORT', 'SHORT', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'BOS', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=15 buy_mL=0 | RSI=48.77 div=nenhuma

========================================================================================
## EPISODIO 1775 (2021-02-24 15:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.32880931965237004 cascade=-3 combined=-3 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_NEAR clean_sky=False has_overhead=True dist_supply=0.65ATR dist_demand=2.35ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1810.25 H1811.16 L1806.04 C1808.33
    O1808.21 H1810.14 L1803.13 C1807.19
    O1807.16 H1810.26 L1783.56 C1785.68
    O1785.67 H1804.44 L1783.76 C1797.64
    O1797.56 H1797.56 L1797.56 C1797.56

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['CHoCH', 'CHoCH', 'BOS', 'CHoCH', 'BOS'] | bubbles sell_mL=4 buy_mL=0 | RSI=55.17 div=nenhuma

##########################################################################################
# SUB-BLOCO D. macro negativo EXTREMO


========================================================================================
## EPISODIO 3949 (2022-07-21 18:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.6656697849668259 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_FAR clean_sky=False has_overhead=True dist_supply=2.42ATR dist_demand=NoneATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1692.11 H1693.84 L1690.81 C1693.15
    O1693.14 H1693.77 L1682.19 C1684.46
    O1684.51 H1710.35 L1680.87 C1705.76
    O1705.76 H1718.27 L1703.7 C1713.81
    O1713.82 H1713.82 L1713.82 C1713.82

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['BOS', 'BOS', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=5 buy_mL=0 | RSI=54.01 div=nenhuma

========================================================================================
## EPISODIO 3929 (2022-07-18 10:00)

### Camada 1 backbone (RAW)
- regime (DERIVED_FROM_RAW price): weekly_slope=-0.6656697849668259 cascade=-2 combined=-2 macro_broken=True v3=BEAR (fidelity=True)
- supply/demand (RAW Custom OB boxes): sup_cat=SUPPLY_BLOCKS clean_sky=False has_overhead=True dist_supply=1.64ATR dist_demand=1.05ATR
- SVP/POC/VAL/VAH/acceptance: **BLOCKED_UNMAPPED** (RAW tem itens VP brutos; VA nao computada — leia sem isso)

### Camada 0 forma (RAW OHLC, ultimas barras ate a entry)
    O1707.12 H1714.57 L1705.87 C1714.31
    O1714.36 H1718.24 L1713.15 C1714.42
    O1714.4 H1723.87 L1711.82 C1722.06
    O1722.07 H1722.17 L1711.46 C1718.96
    O1719.02 H1719.02 L1719.02 C1719.02

### Indicadores (RAW): NAS(RAW)=['LONG', 'LONG', 'LONG', 'LONG', 'LONG'] | SMC(RAW)=['BOS', 'BOS', 'BOS', 'BOS', 'BOS'] | bubbles sell_mL=10 buy_mL=0 | RSI=51.02 div=nenhuma
# COLD STORAGE MANIFEST — 2026-07-02

**Escopo:** arquivar fora do repo ativo dumps pesados/regeneráveis + backups datados, com prova de integridade e restore documentado.
**Commit base:** `e62d468` · **Máquina:** darwin (macOS), HD externo `GUTS_ LACIE`.
**Resultado:** repo **2,7G → 558M** (~2,2G recuperados). Nada tracked/produção/runtime vivo tocado.

## Paths arquivados (ambos untracked + gitignored)
| Path original | Ficheiros | Tamanho (bytes reais) | Última mod |
|---|---|---|---|
| `alert-bridge/logs/backtests/` | 22 | 2.323.952.084 (~2,2G) | 18 jun 2026 (stale) |
| `backups/` | 150 | 33.186.604 (~32M) | 16 jun 2026 (stale) |

**Confirmação de segurança:** ambos untracked/gitignored; `lsof` vazio (nenhum processo aberto); o receiver vivo (`com.cristrein.tv-webhook-receiver`) escreve em `alert-bridge/logs/` **raiz**, NÃO em `logs/backtests/` (subdir do backtest-runner on-demand). Raiz `logs/` (claude_recheck, d2r logs, etc.) **preservada intacta**. Nenhum ficheiro tracked/produção/RAW/strategy_rules/catalog/plist incluído.

## Destino (HD externo)
`/Volumes/GUTS_ LACIE/trading_system_cold_storage/`
| Arquivo | Tamanho comprimido | SHA256 |
|---|---|---|
| `alert-bridge-logs-backtests_20260702.tar.zst` | 14M | `89e79ebe4f803143e16698437306680fbe6a2c5c486ec1afec9dcdf3de5f5e34` |
| `backups-dated_20260702.tar.zst` | 16M | `41acabcc1006cf6de80d77502f2556c8b0d69cf16b445c8129911be63556f97a` |
| `SHA256SUMS.txt` | — | (contém os 2 acima) |

## Comandos exatos usados
```bash
DEST="/Volumes/GUTS_ LACIE/trading_system_cold_storage"; mkdir -p "$DEST"
tar -cf - -C alert-bridge/logs backtests | zstd -T0 -q -o "$DEST/alert-bridge-logs-backtests_20260702.tar.zst"
tar -cf - backups            | zstd -T0 -q -o "$DEST/backups-dated_20260702.tar.zst"
cd "$DEST" && shasum -a 256 *.tar.zst > SHA256SUMS.txt
```

## Verificação de integridade (toda PASS antes de remover local)
- `zstd -t *.tar.zst` → OK (2.357.309.440 bytes descomprimidos verificados).
- Contagem de ficheiros: backtests 22=22 ✅ · backups 150=150 ✅.
- Bytes reais (stat %z, independente de filesystem): backtests 2.323.952.084=2.323.952.084 ✅ · backups 33.186.604=33.186.604 ✅.
- **Roundtrip `diff -rq`** (extração completa p/ sandbox no HD → comparação de conteúdo): **backtests CONTEÚDO IDÊNTICO ✅ · backups CONTEÚDO IDÊNTICO ✅**.
- (Nota: `du -k` diferia por block-size do filesystem do HD; bytes reais + diff provam identidade.)

## Restore instructions
```bash
DEST="/Volumes/GUTS_ LACIE/trading_system_cold_storage"
# verificar integridade antes de restaurar:
cd "$DEST" && shasum -a 256 -c SHA256SUMS.txt && zstd -t *.tar.zst
# restaurar backtests (recria alert-bridge/logs/backtests/):
zstd -dc "$DEST/alert-bridge-logs-backtests_20260702.tar.zst" | tar -xf - -C /Users/cristrein/tradingview-mcp/alert-bridge/logs
# restaurar backups (recria ./backups/):
zstd -dc "$DEST/backups-dated_20260702.tar.zst" | tar -xf - -C /Users/cristrein/tradingview-mcp
```

## Confirmação de remoção local
- `rm -rf alert-bridge/logs/backtests` → confirmado ausente ✅
- `rm -rf backups` → confirmado ausente ✅
- Sandbox roundtrip temporário (`/Volumes/GUTS_ LACIE/cold_storage_roundtrip_tmp`) removido ✅
- Espaço recuperado: **~2,2G** (repo 2,7G → 558M).

## Riscos / rollback
- **Risco:** nulo para produção (paths stale, untracked, não-runtime; receiver logs raiz intactos).
- **Rollback:** restaurar via secção acima (arquivos + SHA256 no HD externo). Regeneráveis também: backtests via re-run do backtest-runner; backups eram snapshots datados.
- **Não fazer push sem nova autorização.**

#!/bin/bash
# Copia template JSON pro clipboard.
# Usage: ./cp.sh xau_small_buy
DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE="$1"
FILE="${DIR}/${TEMPLATE}.json"
if [ ! -f "$FILE" ]; then
    echo "Templates disponiveis:"
    ls "$DIR"/*.json | xargs -n1 basename | sed 's/\.json//'
    exit 1
fi
pbcopy < "$FILE"
echo "Clipboard: ${TEMPLATE} ($(wc -c < "$FILE" | tr -d ' ') bytes)"

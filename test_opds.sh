#!/bin/bash
# test_opds.sh — Тестирование OPDS-эндпойнтов
# Проверяет доступность всех маршрутов на одном сервере
#
# Использование:
#   ./test_opds.sh [host]
#
# По умолчанию: 127.0.0.1:8000

set -euo pipefail

HOST="${1:-127.0.0.1:8000}"
BASE_URL="http://${HOST}"
TMPDIR="/tmp/opds_test_$$"
PASS=0
FAIL=0
SKIP=0

mkdir -p "$TMPDIR"

# List of OPDS endpoints to test
ENDPOINTS=(
    "/opds/"
    "/opds/time"
    "/opds/time/0"
    "/opds/time/1"
    "/opds/authorsindex/"
    "/opds/sequencesindex/"
    "/opds/genresindex/"
    "/opds/random-books/"
    "/opds/random-sequences/"
    "/opds/rnd/genresindex/"
    "/opds/search"
    "/opds/search?searchTerm=толстой"
    "/opds/search/authors?searchTerm=толстой"
    "/opds/search/sequences?searchTerm=космос"
    "/opds/search/books?searchTerm=война"
    "/opds/search/booksanno?searchTerm=приключение"
)

echo ""
echo "================================================================"
echo "  OPDS Endpoint Test"
echo "  Server: $BASE_URL"
echo "================================================================"

for endpoint in "${ENDPOINTS[@]}"; do
    display="$endpoint"
    
    printf "  %-55s" "$display"
    
    # Fetch response with headers
    out="$TMPDIR/response.xml"
    hdr="$TMPDIR/headers.txt"
    status=$(curl -sS -D "$hdr" -o "$out" -w "%{http_code}" \
        "${BASE_URL}${endpoint}" 2>/dev/null || echo "000")
    
    # Check connectivity
    if [ "$status" = "000" ]; then
        echo "  SKIP (no connection)"
        SKIP=$((SKIP + 1))
        continue
    fi
    
    # Check for expected status
    if [ "$status" = "200" ]; then
        # Extract Content-Type from headers file
        content_type=$(grep -i '^Content-Type:' "$hdr" 2>/dev/null | head -1 | tr -d '\r' || echo "")
        
        if echo "$content_type" | grep -qi "xml"; then
            lines=$(wc -l < "$out" || echo 0)
            echo "  PASS (200, ${lines} lines)"
            PASS=$((PASS + 1))
        else
            echo "  FAIL (200 but wrong Content-Type: ${content_type})"
            FAIL=$((FAIL + 1))
        fi
    elif [ "$status" = "404" ]; then
        echo "  SKIP (404 not found)"
        SKIP=$((SKIP + 1))
    elif [ "$status" = "401" ]; then
        echo "  AUTH (401 unauthorized)"
        SKIP=$((SKIP + 1))
    else
        echo "  FAIL ($status)"
        FAIL=$((FAIL + 1))
        
        # Show response body for non-200/404
        if [ -s "$out" ]; then
            echo "    Response:"
            head -5 "$out" | sed 's/^/    /'
        fi
    fi
done

echo ""
echo "================================================================"
echo "  PASSED:  $PASS"
echo "  FAILED:  $FAIL"
echo "  SKIPPED: $SKIP"
echo "  TOTAL:   $((PASS + FAIL + SKIP))"
echo "================================================================"

# Cleanup
rm -rf "$TMPDIR"

[ "$FAIL" -gt 0 ] && exit 1
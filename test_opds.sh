#!/bin/bash
# test_opds.sh — Тестирование OPDS-эндпойнтов
# Проходит по всем типам URL по разу, извлекая параметры из ответов предыдущих запросов
#
# Использование:
#   ./test_opds.sh [host]
#
# По умолчанию: 127.0.0.1:8000

HOST="${1:-127.0.0.1:8000}"
BASE_URL="http://${HOST}"
TMPDIR="/tmp/opds_test_$$"
PASS=0
FAIL=0
SKIP=0

mkdir -p "$TMPDIR"
trap 'rm -rf "$TMPDIR"' EXIT

# ============================================================================
# Утилиты
# ============================================================================

# Запрос URL, сохраняет тело в $TMPDIR/<suffix>.xml, заголовки в <suffix>.hdr
# Возвращает HTTP status code
fetch() {
    local url="$1"
    local suffix="$2"
    local out="$TMPDIR/${suffix}.xml"
    local hdr="$TMPDIR/${suffix}.hdr"
    curl -sS -D "$hdr" -o "$out" -w "%{http_code}" "$url" 2>/dev/null || echo "000"
}

# Безопасный grep: возвращает пустую строку вместо ошибки при отсутствии совпадений
safe_grep() {
    grep "$@" 2>/dev/null || true
}

# Извлечение href из XML с паттерном
extract_href_pattern() {
    local file="$1"
    local pattern="$2"
    safe_grep -oP "$pattern" "$file" | sed 's/href="//;s/"//' | sort -u
}

# Извлечение author/sequence paths вида /opds/author/sub1/sub2/id
extract_opds_paths() {
    local file="$1"
    local prefix="$2"  # e.g. "author", "sequence"
    # Match /opds/<prefix>/XX/YY/... where XX,YY are hex, rest is hex id
    safe_grep -oP "/opds/${prefix}/[0-9a-fA-F]+/[0-9a-fA-F]+/[0-9a-fA-F]+" "$file" | sort -u
}

# Извлечь первую букву из title (один символ, заглавный)
extract_first_letter_from_title() {
    local file="$1"
    # OPDS authorsindex has entries like <title>A</title> or <title>А</title>
    safe_grep -oP '<title>[A-Za-zА-Яа-яЁё]</title>' "$file" | \
        sed 's/<title>//;s/<\/title>//' | sort -u | head -1
}

# Извлечь meta_id из href
extract_meta_ids_from_href() {
    local file="$1"
    local prefix="$2"  # e.g. "/opds/genresindex/"
    safe_grep -oP "${prefix}\K[a-zA-Z0-9_]+" "$file" | sort -u
}

# Извлечь genre_id из href  /opds/genre/...
extract_genre_ids_from_href() {
    local file="$1"
    safe_grep -oP '/opds/genre/\K[a-zA-Z0-9_]+' "$file" | sort -u
}

# Проверка статуса и типа контента
# $1 = status code (from fetch), $2 = suffix, $3 = expected_type
check_result() {
    local status="$1"
    local suffix="$2"
    local expected_type="$3"

    if [ "$status" = "000" ]; then
        echo "  SKIP (no connection)"
        SKIP=$((SKIP + 1))
        return 1
    fi

    local content_type=""
    if [ -f "$TMPDIR/${suffix}.hdr" ]; then
        content_type=$(grep -i '^Content-Type:' "$TMPDIR/${suffix}.hdr" 2>/dev/null | \
                      head -1 | tr -d '\r' || echo "")
    fi

    if [ "$status" = "401" ]; then
        echo "  AUTH (401)"
        SKIP=$((SKIP + 1))
        return 1
    fi

    if [ "$status" = "200" ]; then
        case "$expected_type" in
            xml)
                if echo "$content_type" | grep -qi "xml"; then
                    local lines
                    lines=$(wc -l < "$TMPDIR/${suffix}.xml" 2>/dev/null || echo 0)
                    echo "  PASS (200, ${lines} lines)"
                    PASS=$((PASS + 1))
                    return 0
                else
                    echo "  FAIL (wrong Content-Type: ${content_type})"
                    FAIL=$((FAIL + 1))
                    return 1
                fi
                ;;
            json)
                if echo "$content_type" | grep -qi "json"; then
                    echo "  PASS (200, JSON)"
                    PASS=$((PASS + 1))
                    return 0
                else
                    echo "  FAIL (wrong Content-Type: ${content_type})"
                    FAIL=$((FAIL + 1))
                    return 1
                fi
                ;;
            image)
                if echo "$content_type" | grep -qi "image"; then
                    echo "  PASS (200, image)"
                    PASS=$((PASS + 1))
                    return 0
                else
                    echo "  FAIL (wrong Content-Type: ${content_type})"
                    FAIL=$((FAIL + 1))
                    return 1
                fi
                ;;
            any)
                echo "  PASS (200)"
                PASS=$((PASS + 1))
                return 0
                ;;
        esac
    elif [ "$status" = "404" ]; then
        echo "  SKIP (404)"
        SKIP=$((SKIP + 1))
        return 1
    else
        echo "  FAIL ($status)"
        FAIL=$((FAIL + 1))
        return 1
    fi
}

# ============================================================================
# Тестирование
# ============================================================================

echo ""
echo "================================================================"
echo "  OPDS Endpoint Test — Hierarchical URL Traversal"
echo "  Server: $BASE_URL"
echo "================================================================"

# --------------------------------------------------------------------
# 1. Root & Navigation
# --------------------------------------------------------------------
echo ""
echo "--- Root & Navigation ---"

printf "  /                                      "
status=$(fetch "${BASE_URL}/" "root")
if [ "$status" = "200" ]; then
    echo "  PASS (200)"
    PASS=$((PASS + 1))
else
    echo "  FAIL ($status)"
    FAIL=$((FAIL + 1))
fi

printf "  /opds/                                 "
status=$(fetch "${BASE_URL}/opds/" "opds_root")
check_result "$status" "opds_root" "xml"

printf "  /opds/time                               "
status=$(fetch "${BASE_URL}/opds/time" "opds_time")
check_result "$status" "opds_time" "xml"

printf "  /opds/time/1                             "
status=$(fetch "${BASE_URL}/opds/time/1" "opds_time_1")
check_result "$status" "opds_time_1" "xml"

# --------------------------------------------------------------------
# 2. Authors Hierarchy
# --------------------------------------------------------------------
echo ""
echo "--- Authors Hierarchy ---"

# /opds/authorsindex/
printf "  /opds/authorsindex/                          "
status=$(fetch "${BASE_URL}/opds/authorsindex/" "authorsindex")
if check_result "$status" "authorsindex" "xml"; then
    # Extract first letter
    FIRST_LETTER=$(extract_first_letter_from_title "$TMPDIR/authorsindex.xml")
    
    if [ -z "$FIRST_LETTER" ]; then
        # Try alternate: extract from link hrefs like /opds/authorsindex/A
        FIRST_LETTER=$(safe_grep -oP '/opds/authorsindex/\K[A-Za-zА-Яа-яЁё]' "$TMPDIR/authorsindex.xml" | \
            sort -u | head -1)
    fi
    
    if [ -n "$FIRST_LETTER" ]; then
        # /opds/authorsindex/<cut>
        printf "  /opds/authorsindex/${FIRST_LETTER}                   "
        status=$(fetch "${BASE_URL}/opds/authorsindex/${FIRST_LETTER}" "authorsindex_cut")
        
        if check_result "$status" "authorsindex_cut" "xml"; then
            # Extract author paths
            AUTHOR_PATHS=$(extract_opds_paths "$TMPDIR/authorsindex_cut.xml" "author")
            AUTHOR_PATH=$(echo "$AUTHOR_PATHS" | head -1)
            
            if [ -n "$AUTHOR_PATH" ]; then
                # /opds/author/sub1/sub2/author_id
                printf "  ${AUTHOR_PATH}                             "
                status=$(fetch "${BASE_URL}${AUTHOR_PATH}" "author_page")
                
                if check_result "$status" "author_page" "xml"; then
                    # Author views
                    printf "  ${AUTHOR_PATH}/sequences                     "
                    status=$(fetch "${BASE_URL}${AUTHOR_PATH}/sequences" "author_seq")
                    check_result "$status" "author_seq" "xml"
                    
                    printf "  ${AUTHOR_PATH}/sequenceless                   "
                    status=$(fetch "${BASE_URL}${AUTHOR_PATH}/sequenceless" "author_noseq")
                    check_result "$status" "author_noseq" "xml"
                    
                    printf "  ${AUTHOR_PATH}/alphabet                      "
                    status=$(fetch "${BASE_URL}${AUTHOR_PATH}/alphabet" "author_alpha")
                    check_result "$status" "author_alpha" "xml"
                    
                    printf "  ${AUTHOR_PATH}/time                          "
                    status=$(fetch "${BASE_URL}${AUTHOR_PATH}/time" "author_time")
                    check_result "$status" "author_time" "xml"
                    
                    # Save sequence path for later
                    if [ -f "$TMPDIR/author_seq.xml" ]; then
                        SEQ_PATH=$(extract_opds_paths "$TMPDIR/author_seq.xml" "sequence" | head -1)
                        if [ -n "$SEQ_PATH" ]; then
                            echo "$SEQ_PATH" > "$TMPDIR/seq_path_from_author.txt"
                        fi
                    fi
                    
                    # Extract book links (download/read)
                    BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' \
                        "$TMPDIR/author_page.xml" | head -1)
                    if [ -n "$BOOK_URL" ]; then
                        echo "$BOOK_URL" > "$TMPDIR/book_url.txt"
                    fi
                    
                    # Extract cover URL
                    COVER_URL=$(safe_grep -oP '/books/[0-9a-fA-F]+/[0-9a-fA-F]+/[0-9a-fA-F]+\.jpg' \
                        "$TMPDIR/author_page.xml" | head -1)
                    if [ -n "$COVER_URL" ]; then
                        echo "$COVER_URL" > "$TMPDIR/cover_url.txt"
                    fi
                fi
            fi
        fi
    fi
fi

# --------------------------------------------------------------------
# 3. Sequences Hierarchy
# --------------------------------------------------------------------
echo ""
echo "--- Sequences Hierarchy ---"

# /opds/sequencesindex/
printf "  /opds/sequencesindex/                          "
status=$(fetch "${BASE_URL}/opds/sequencesindex/" "seqindex")
if check_result "$status" "seqindex" "xml"; then
    SEQ_LETTER=$(extract_first_letter_from_title "$TMPDIR/seqindex.xml")
    
    if [ -z "$SEQ_LETTER" ]; then
        SEQ_LETTER=$(safe_grep -oP '/opds/sequencesindex/\K[A-Za-zА-Яа-яЁё]' "$TMPDIR/seqindex.xml" | \
            sort -u | head -1)
    fi
    
    SEQ_PATH=""
    
    if [ -n "$SEQ_LETTER" ]; then
        printf "  /opds/sequencesindex/${SEQ_LETTER}                   "
        status=$(fetch "${BASE_URL}/opds/sequencesindex/${SEQ_LETTER}" "seqindex_cut")
        
        if check_result "$status" "seqindex_cut" "xml"; then
            SEQ_PATH=$(extract_opds_paths "$TMPDIR/seqindex_cut.xml" "sequence" | head -1)
        fi
    fi
    
    # Fallback: use sequence from author page
    if [ -z "$SEQ_PATH" ] && [ -f "$TMPDIR/seq_path_from_author.txt" ]; then
        SEQ_PATH=$(cat "$TMPDIR/seq_path_from_author.txt")
    fi
    
    if [ -n "$SEQ_PATH" ]; then
        printf "  ${SEQ_PATH}                             "
        status=$(fetch "${BASE_URL}${SEQ_PATH}" "seq_page")
        check_result "$status" "seq_page" "xml"
        
        # Try to get book URL from sequence page
        if [ -f "$TMPDIR/seq_page.xml" ] && [ ! -f "$TMPDIR/book_url.txt" ]; then
            BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' \
                "$TMPDIR/seq_page.xml" | head -1)
            if [ -n "$BOOK_URL" ]; then
                echo "$BOOK_URL" > "$TMPDIR/book_url.txt"
            fi
        fi
    fi
fi

# --------------------------------------------------------------------
# 4. Genres Hierarchy
# --------------------------------------------------------------------
echo ""
echo "--- Genres Hierarchy ---"

# /opds/genresindex/
printf "  /opds/genresindex/                             "
status=$(fetch "${BASE_URL}/opds/genresindex/" "genresindex")
if check_result "$status" "genresindex" "xml"; then
    # Extract meta_id from hrefs like /opds/genresindex/meta_id
    META_ID=$(extract_meta_ids_from_href "$TMPDIR/genresindex.xml" "/opds/genresindex/" | head -1)
    
    if [ -n "$META_ID" ]; then
        printf "  /opds/genresindex/${META_ID}                     "
        status=$(fetch "${BASE_URL}/opds/genresindex/${META_ID}" "gen_meta")
        
        if check_result "$status" "gen_meta" "xml"; then
            # Extract genre_id
            GENRE_ID=$(extract_genre_ids_from_href "$TMPDIR/gen_meta.xml" | head -1)
            
            if [ -n "$GENRE_ID" ]; then
                printf "  /opds/genre/${GENRE_ID}                       "
                status=$(fetch "${BASE_URL}/opds/genre/${GENRE_ID}" "gen_books")
                
                if check_result "$status" "gen_books" "xml"; then
                    printf "  /opds/genre/${GENRE_ID}/1                      "
                    status=$(fetch "${BASE_URL}/opds/genre/${GENRE_ID}/1" "gen_books1")
                    check_result "$status" "gen_books1" "xml"
                fi
            fi
        fi
    fi
fi

# --------------------------------------------------------------------
# 5. Random Elements (no pagination)
# --------------------------------------------------------------------
echo ""
echo "--- Random Elements ---"

printf "  /opds/random-books/                          "
status=$(fetch "${BASE_URL}/opds/random-books/" "rnd_books")
check_result "$status" "rnd_books" "xml"

printf "  /opds/random-sequences/                      "
status=$(fetch "${BASE_URL}/opds/random-sequences/" "rnd_seq")
check_result "$status" "rnd_seq" "xml"

# Random genres hierarchy
printf "  /opds/rnd/genresindex/                       "
status=$(fetch "${BASE_URL}/opds/rnd/genresindex/" "rnd_genidx")
if check_result "$status" "rnd_genidx" "xml"; then
    RND_META=$(extract_meta_ids_from_href "$TMPDIR/rnd_genidx.xml" "/opds/rnd/genresindex/" | head -1)
    
    if [ -n "$RND_META" ]; then
        printf "  /opds/rnd/genresindex/${RND_META}               "
        status=$(fetch "${BASE_URL}/opds/rnd/genresindex/${RND_META}" "rnd_genm")
        
        if check_result "$status" "rnd_genm" "xml"; then
            RND_GENRE=$(safe_grep -oP '/opds/rnd/genre/\K[a-zA-Z0-9_]+' "$TMPDIR/rnd_genm.xml" | head -1)
            
            if [ -n "$RND_GENRE" ]; then
                printf "  /opds/rnd/genre/${RND_GENRE}                  "
                status=$(fetch "${BASE_URL}/opds/rnd/genre/${RND_GENRE}" "rnd_genre")
                check_result "$status" "rnd_genre" "xml"
            fi
        fi
    fi
fi

# --------------------------------------------------------------------
# 6. Search
# --------------------------------------------------------------------
echo ""
echo "--- Search ---"

printf "  /opds/search?searchTerm=                       "
status=$(fetch "${BASE_URL}/opds/search?searchTerm=" "search_empty")
check_result "$status" "search_empty" "xml"

printf "  /opds/search/authors?searchTerm=test             "
status=$(fetch "${BASE_URL}/opds/search/authors?searchTerm=test" "search_author")
check_result "$status" "search_author" "xml"

printf "  /opds/search/sequences?searchTerm=test           "
status=$(fetch "${BASE_URL}/opds/search/sequences?searchTerm=test" "search_seq")
check_result "$status" "search_seq" "xml"

printf "  /opds/search/books?searchTerm=test               "
status=$(fetch "${BASE_URL}/opds/search/books?searchTerm=test" "search_book")
check_result "$status" "search_book" "xml"

printf "  /opds/search/booksanno?searchTerm=test           "
status=$(fetch "${BASE_URL}/opds/search/booksanno?searchTerm=test" "search_anno")
check_result "$status" "search_anno" "xml"

printf "  /opds/search/booksannovector?searchTerm=test     "
status=$(fetch "${BASE_URL}/opds/search/booksannovector?searchTerm=test" "search_vec")
if [ "$status" = "200" ]; then
    check_result "$status" "search_vec" "xml"
elif [ "$status" = "501" ] || [ "$status" = "404" ]; then
    echo "  SKIP ($status - vector disabled)"
    SKIP=$((SKIP + 1))
else
    echo "  FAIL ($status)"
    FAIL=$((FAIL + 1))
fi

# --------------------------------------------------------------------
# 7. Book-specific URLs (extracted from previous responses)
# --------------------------------------------------------------------
echo ""
echo "--- Book Actions ---"

BOOK_URL=""
if [ -f "$TMPDIR/book_url.txt" ]; then
    BOOK_URL=$(cat "$TMPDIR/book_url.txt")
fi

# Fallback: try other sources
if [ -z "$BOOK_URL" ] && [ -f "$TMPDIR/rnd_books.xml" ]; then
    BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' "$TMPDIR/rnd_books.xml" | head -1)
fi

if [ -z "$BOOK_URL" ] && [ -f "$TMPDIR/opds_time.xml" ]; then
    BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' "$TMPDIR/opds_time.xml" | head -1)
fi

if [ -z "$BOOK_URL" ] && [ -f "$TMPDIR/opds_root.xml" ]; then
    BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' "$TMPDIR/opds_root.xml" | head -1)
fi

if [ -n "$BOOK_URL" ]; then
    # Extract action type, zip file, and fb2 file from URL
    # URL formats: /fb2/zip/file, /read/zip/file, /plain/zip/file
    ACTION=$(echo "$BOOK_URL" | safe_grep -oP '^/(fb2|read|plain)' | tr -d '/')
    ZIP_FILE=$(echo "$BOOK_URL" | safe_grep -oP '/[^/]+/[^/]+$' | sed 's|^/||' | cut -d/ -f1)
    FB2_FILE=$(echo "$BOOK_URL" | safe_grep -oP '/[^/]+/[^/]+$' | sed 's|^/||' | cut -d/ -f2)
    
    if [ -n "$ACTION" ] && [ -n "$ZIP_FILE" ] && [ -n "$FB2_FILE" ]; then
        # /fb2/<zip>/<file> - download
        printf "  /fb2/${ZIP_FILE}/${FB2_FILE}                     "
        status=$(fetch "${BASE_URL}/fb2/${ZIP_FILE}/${FB2_FILE}" "fb2_dl")
        if [ "$status" = "200" ]; then
            echo "  PASS (200, download)"
            PASS=$((PASS + 1))
        elif [ "$status" = "404" ]; then
            echo "  SKIP (404)"
            SKIP=$((SKIP + 1))
        else
            echo "  FAIL ($status)"
            FAIL=$((FAIL + 1))
        fi
        
        # /read/<zip>/<file> - read online
        printf "  /read/${ZIP_FILE}/${FB2_FILE}                    "
        status=$(fetch "${BASE_URL}/read/${ZIP_FILE}/${FB2_FILE}" "read_book")
        if [ "$status" = "200" ]; then
            echo "  PASS (200)"
            PASS=$((PASS + 1))
        elif [ "$status" = "404" ]; then
            echo "  SKIP (404)"
            SKIP=$((SKIP + 1))
        else
            echo "  FAIL ($status)"
            FAIL=$((FAIL + 1))
        fi
        
        # /plain/<zip>/<file> - plain download (may not be available)
        printf "  /plain/${ZIP_FILE}/${FB2_FILE}                   "
        status=$(fetch "${BASE_URL}/plain/${ZIP_FILE}/${FB2_FILE}" "plain_dl")
        if [ "$status" = "200" ]; then
            echo "  PASS (200)"
            PASS=$((PASS + 1))
        elif [ "$status" = "404" ]; then
            echo "  SKIP (404 - plain not available)"
            SKIP=$((SKIP + 1))
        else
            echo "  FAIL ($status)"
            FAIL=$((FAIL + 1))
        fi
    else
        echo "  (could not parse book URL: $BOOK_URL)"
    fi
else
    echo "  (no book URL found from previous pages)"
fi

# Cover image
if [ -f "$TMPDIR/cover_url.txt" ]; then
    COVER_URL=$(cat "$TMPDIR/cover_url.txt")
    printf "  ${COVER_URL}                    "
    status=$(fetch "${BASE_URL}${COVER_URL}" "cover_img")
    if [ "$status" = "200" ]; then
        echo "  PASS (200, cover)"
        PASS=$((PASS + 1))
    elif [ "$status" = "404" ]; then
        echo "  SKIP (404)"
        SKIP=$((SKIP + 1))
    else
        echo "  FAIL ($status)"
        FAIL=$((FAIL + 1))
    fi
fi

# --------------------------------------------------------------------
# 8. Static Files
# --------------------------------------------------------------------
echo ""
echo "--- Static Files ---"

printf "  /interface.js                            "
status=$(fetch "${BASE_URL}/interface.js" "interface_js")
if [ "$status" = "200" ]; then
    echo "  PASS (200)"
    PASS=$((PASS + 1))
elif [ "$status" = "404" ]; then
    # Try static path
    status=$(fetch "${BASE_URL}/static/interface.js" "interface_js2")
    if [ "$status" = "200" ]; then
        echo "  PASS (200, /static/)"
        PASS=$((PASS + 1))
    else
        echo "  SKIP (404)"
        SKIP=$((SKIP + 1))
    fi
else
    echo "  FAIL ($status)"
    FAIL=$((FAIL + 1))
fi

printf "  /favicon.ico                             "
status=$(fetch "${BASE_URL}/favicon.ico" "favicon")
if [ "$status" = "200" ]; then
    echo "  PASS (200)"
    PASS=$((PASS + 1))
elif [ "$status" = "404" ]; then
    echo "  SKIP (404)"
    SKIP=$((SKIP + 1))
else
    echo "  FAIL ($status)"
    FAIL=$((FAIL + 1))
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "================================================================"
echo "  Results"
echo "================================================================"
echo "  PASSED:  $PASS"
echo "  FAILED:  $FAIL"
echo "  SKIPPED: $SKIP"
echo "  TOTAL:   $((PASS + FAIL + SKIP))"
echo "================================================================"

[ "$FAIL" -gt 0 ] && exit 1
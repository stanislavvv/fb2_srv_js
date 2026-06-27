#!/bin/bash
# test_opds_data.sh — Тестирование OPDS-эндпойнтов с сохранением данных
# Проходит по всем типам URL по разу, извлекая параметры из ответов предыдущих запросов
# Сохраняет файлы ответов в ./tmp с именами, основанными на URL (замена / на _)
#
# Использование:
#   ./test_opds_data.sh [host]
#
# По умолчанию: 127.0.0.1:8000

HOST="${1:-127.0.0.1:8000}"
BASE_URL="http://${HOST}"
TMPDIR="./tmp"
PASS=0
FAIL=0
SKIP=0
AUTH_ARGS=""

mkdir -p "$TMPDIR"
# Не удаляем каталог при выходе — сохраняем данные

# ============================================================================
# Утилиты
# ============================================================================

# Преобразует URL в имя файла: http://HOST:PORT/path/to/resource -> _path_to_resource
# Хост и порт не входят в имя файла
url_to_suffix() {
    local url="$1"
    echo "$url" | sed 's|http://[^/]*||' | tr '/' '_'
}

# Получает путь к файлу тела из URL
url_to_xml() {
    local url="$1"
    local suffix
    suffix=$(url_to_suffix "$url")
    echo "$TMPDIR/${suffix}.xml"
}

# Получает путь к файлу заголовков из URL
url_to_hdr() {
    local url="$1"
    local suffix
    suffix=$(url_to_suffix "$url")
    echo "$TMPDIR/${suffix}.hdr"
}

# Запрос URL, сохраняет тело в $TMPDIR/<url-based>.xml, заголовки в <url-based>.hdr
# Возвращает HTTP status code
fetch() {
    local url="$1"
    local suffix
    suffix=$(url_to_suffix "$url")
    local out="$TMPDIR/${suffix}.xml"
    local hdr="$TMPDIR/${suffix}.hdr"
    curl -sS $AUTH_ARGS -D "$hdr" -o "$out" -w "%{http_code}" "$url" 2>/dev/null || echo "000"
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

# Извлечь sub2 (третий сегмент) из href индексов авторов/серий
# Например: /opds/authorsindex/A/AFT -> AFT
# sub2 — это префикс имени (любые символы кроме /), URL-кодированный
extract_index_sub2() {
    local file="$1"
    local prefix="$2"  # e.g. "/opds/authorsindex/" or "/opds/sequencesindex/"
    local sub1="$3"    # e.g. "A"
    # Extract href values from XML, then get the third segment (sub2) from matching URLs
    safe_grep -oP 'href="\K[^"]+' "$file" | \
        grep -P "^${prefix}${sub1}/" | \
        sed "s|^${prefix}${sub1}/||" | \
        sort -u
}

# Получить XML файл для данного URL
get_xml_file() {
    url_to_xml "$1"
}

# Получить HDR файл для данного URL
get_hdr_file() {
    url_to_hdr "$1"
}

# Проверка статуса и типа контента
# $1 = url, $2 = expected_type
check_result() {
    local url="$1"
    local status="$2"
    local expected_type="$3"

    if [ "$status" = "000" ]; then
        echo "  SKIP (no connection)"
        SKIP=$((SKIP + 1))
        return 1
    fi

    local xml_file
    local hdr_file
    xml_file=$(get_xml_file "$url")
    hdr_file=$(get_hdr_file "$url")

    local content_type=""
    if [ -f "$hdr_file" ]; then
        content_type=$(grep -i '^Content-Type:' "$hdr_file" 2>/dev/null | \
                      head -1 | tr -d '\r' || echo "")
    fi

    if [ "$status" = "401" ]; then
        if [ -n "$AUTH_ARGS" ]; then
            echo "  FAIL (401 - auth failed)"
            FAIL=$((FAIL + 1))
        else
            echo "  AUTH (401)"
            SKIP=$((SKIP + 1))
        fi
        return 1
    fi

    if [ "$status" = "200" ]; then
        case "$expected_type" in
            xml)
                if echo "$content_type" | grep -qi "xml"; then
                    local lines
                    lines=$(wc -l < "$xml_file" 2>/dev/null || echo 0)
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
# Инициализация авторизации
# ============================================================================

if [ -f "config.ini" ]; then
    ZIPS_PATH=$(grep -oP '^zips_path\s*=\s*\K.*' config.ini | tr -d ' \r')
    if [ -n "$ZIPS_PATH" ] && [ -f "${ZIPS_PATH}/passwd" ]; then
        while IFS= read -r line; do
            line=$(echo "$line" | tr -d '\r' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            [ -z "$line" ] && continue
            echo "$line" | grep -q '^#' && continue
            if echo "$line" | grep -q ':'; then
                AUTH_USER=$(echo "$line" | cut -d: -f1)
                AUTH_PASS=$(echo "$line" | cut -d: -f2-)
                AUTH_ARGS="-u ${AUTH_USER}:${AUTH_PASS}"
                break
            fi
        done < "${ZIPS_PATH}/passwd"
    fi
fi

# ============================================================================
# Тестирование
# ============================================================================

echo ""
echo "================================================================"
echo "  OPDS Endpoint Test — Hierarchical URL Traversal (Data Save)"
echo "  Server: $BASE_URL"
if [ -n "$AUTH_ARGS" ]; then
    echo "  Auth: enabled (${AUTH_USER})"
else
    echo "  Auth: disabled"
fi
echo "  Data saved to: $TMPDIR/"
echo "================================================================"

# --------------------------------------------------------------------
# 1. Root & Navigation
# --------------------------------------------------------------------
echo ""
echo "--- Root & Navigation ---"

printf "  /                                      "
status=$(fetch "${BASE_URL}/")
if [ "$status" = "200" ]; then
    echo "  PASS (200)"
    PASS=$((PASS + 1))
else
    echo "  FAIL ($status)"
    FAIL=$((FAIL + 1))
fi

printf "  /opds/                                 "
status=$(fetch "${BASE_URL}/opds/")
check_result "${BASE_URL}/opds/" "$status" "xml"

printf "  /opds/time                               "
status=$(fetch "${BASE_URL}/opds/time")
check_result "${BASE_URL}/opds/time" "$status" "xml"

printf "  /opds/time/1                             "
status=$(fetch "${BASE_URL}/opds/time/1")
check_result "${BASE_URL}/opds/time/1" "$status" "xml"

# --------------------------------------------------------------------
# 2. Authors Hierarchy
# --------------------------------------------------------------------
echo ""
echo "--- Authors Hierarchy ---"

AUTHORSINDEX_URL="${BASE_URL}/opds/authorsindex/"
printf "  /opds/authorsindex/                          "
status=$(fetch "$AUTHORSINDEX_URL")
if check_result "$AUTHORSINDEX_URL" "$status" "xml"; then
    # Extract first letter
    FIRST_LETTER=$(extract_first_letter_from_title "$(get_xml_file "$AUTHORSINDEX_URL")")
    
    if [ -z "$FIRST_LETTER" ]; then
        # Try alternate: extract from link hrefs like /opds/authorsindex/A
        FIRST_LETTER=$(safe_grep -oP '/opds/authorsindex/\K[A-Za-zА-Яа-яЁё]' "$(get_xml_file "$AUTHORSINDEX_URL")" | \
            sort -u | head -1)
    fi
    
    if [ -n "$FIRST_LETTER" ]; then
        AUTHORSINDEX_CUT_URL="${BASE_URL}/opds/authorsindex/${FIRST_LETTER}"
        printf "  /opds/authorsindex/${FIRST_LETTER}                   "
        status=$(fetch "$AUTHORSINDEX_CUT_URL")
        
        if check_result "$AUTHORSINDEX_CUT_URL" "$status" "xml"; then
            # Extract sub2 for three-level index: /opds/authorsindex/{sub1}/{sub2}
            AUTH_SUB2=$(extract_index_sub2 "$(get_xml_file "$AUTHORSINDEX_CUT_URL")" "/opds/authorsindex/" "$FIRST_LETTER" | head -1)
            
            AUTH_PATH=""
            
            if [ -n "$AUTH_SUB2" ]; then
                AUTHORSINDEX_SUB2_URL="${BASE_URL}/opds/authorsindex/${FIRST_LETTER}/${AUTH_SUB2}"
                printf '%s' "  /opds/authorsindex/${FIRST_LETTER}/${AUTH_SUB2}  "
                status=$(fetch "$AUTHORSINDEX_SUB2_URL")
                
                if check_result "$AUTHORSINDEX_SUB2_URL" "$status" "xml"; then
                    # Extract author paths from three-level index
                    AUTHOR_PATHS=$(extract_opds_paths "$(get_xml_file "$AUTHORSINDEX_SUB2_URL")" "author")
                    AUTH_PATH=$(echo "$AUTHOR_PATHS" | head -1)
                else
                    AUTHOR_PATHS=""
                fi
            else
                AUTHOR_PATHS=""
            fi
            
            if [ -z "$AUTH_PATH" ]; then
                # Fallback: try extracting from two-level index
                AUTHOR_PATHS=$(extract_opds_paths "$(get_xml_file "$AUTHORSINDEX_CUT_URL")" "author")
                AUTH_PATH=$(echo "$AUTHOR_PATHS" | head -1)
            fi
            
            if [ -n "$AUTH_PATH" ]; then
                # /opds/author/sub1/sub2/author_id
                AUTHOR_URL="${BASE_URL}${AUTH_PATH}"
                printf '%s' "  ${AUTH_PATH}                             "
                status=$(fetch "$AUTHOR_URL")
                
                if check_result "$AUTHOR_URL" "$status" "xml"; then
                    # Author views
                    AUTHOR_SEQ_URL="${AUTHOR_URL}/sequences"
                    printf '%s' "  ${AUTH_PATH}/sequences                     "
                    status=$(fetch "$AUTHOR_SEQ_URL")
                    check_result "$AUTHOR_SEQ_URL" "$status" "xml"
                    
                    AUTHOR_NOSEQ_URL="${AUTHOR_URL}/sequenceless"
                    printf '%s' "  ${AUTH_PATH}/sequenceless                   "
                    status=$(fetch "$AUTHOR_NOSEQ_URL")
                    check_result "$AUTHOR_NOSEQ_URL" "$status" "xml"
                    
                    AUTHOR_ALPHA_URL="${AUTHOR_URL}/alphabet"
                    printf '%s' "  ${AUTH_PATH}/alphabet                      "
                    status=$(fetch "$AUTHOR_ALPHA_URL")
                    check_result "$AUTHOR_ALPHA_URL" "$status" "xml"
                    
                    AUTHOR_TIME_URL="${AUTHOR_URL}/time"
                    printf '%s' "  ${AUTH_PATH}/time                          "
                    status=$(fetch "$AUTHOR_TIME_URL")
                    check_result "$AUTHOR_TIME_URL" "$status" "xml"
                    
                    # Save sequence path for later
                    if [ -f "$(get_xml_file "$AUTHOR_SEQ_URL")" ]; then
                        SEQ_PATH=$(extract_opds_paths "$(get_xml_file "$AUTHOR_SEQ_URL")" "sequence" | head -1)
                        if [ -n "$SEQ_PATH" ]; then
                            echo "$SEQ_PATH" > "$TMPDIR/.seq_path_from_author.txt"
                        fi
                    fi
                    
                    # Extract book links (download/read)
                    BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' \
                        "$(get_xml_file "$AUTHOR_URL")" | head -1)
                    if [ -n "$BOOK_URL" ]; then
                        echo "$BOOK_URL" > "$TMPDIR/.book_url.txt"
                    fi
                    
                    # Extract cover URL
                    COVER_URL=$(safe_grep -oP '/books/[0-9a-fA-F]+/[0-9a-fA-F]+/[0-9a-fA-F]+\.jpg' \
                        "$(get_xml_file "$AUTHOR_URL")" | head -1)
                    if [ -n "$COVER_URL" ]; then
                        echo "$COVER_URL" > "$TMPDIR/.cover_url.txt"
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

SEQINDEX_URL="${BASE_URL}/opds/sequencesindex/"
printf "  /opds/sequencesindex/                          "
status=$(fetch "$SEQINDEX_URL")
if check_result "$SEQINDEX_URL" "$status" "xml"; then
    SEQ_LETTER=$(extract_first_letter_from_title "$(get_xml_file "$SEQINDEX_URL")")
    
    if [ -z "$SEQ_LETTER" ]; then
        SEQ_LETTER=$(safe_grep -oP '/opds/sequencesindex/\K[A-Za-zА-Яа-яЁё]' "$(get_xml_file "$SEQINDEX_URL")" | \
            sort -u | head -1)
    fi
    
    SEQ_PATH=""
    SEQ_SUB2=""
    
    if [ -n "$SEQ_LETTER" ]; then
        SEQINDEX_CUT_URL="${BASE_URL}/opds/sequencesindex/${SEQ_LETTER}"
        printf "  /opds/sequencesindex/${SEQ_LETTER}                   "
        status=$(fetch "$SEQINDEX_CUT_URL")
        
        if check_result "$SEQINDEX_CUT_URL" "$status" "xml"; then
            # Extract sub2 for three-level index: /opds/sequencesindex/{sub1}/{sub2}
            SEQ_SUB2=$(extract_index_sub2 "$(get_xml_file "$SEQINDEX_CUT_URL")" "/opds/sequencesindex/" "$SEQ_LETTER" | head -1)
            
            if [ -n "$SEQ_SUB2" ]; then
                SEQINDEX_SUB2_URL="${BASE_URL}/opds/sequencesindex/${SEQ_LETTER}/${SEQ_SUB2}"
                printf '%s' "  /opds/sequencesindex/${SEQ_LETTER}/${SEQ_SUB2}  "
                status=$(fetch "$SEQINDEX_SUB2_URL")
                
                if check_result "$SEQINDEX_SUB2_URL" "$status" "xml"; then
                    SEQ_PATH=$(extract_opds_paths "$(get_xml_file "$SEQINDEX_SUB2_URL")" "sequence" | head -1)
                fi
            fi
            
            if [ -z "$SEQ_PATH" ]; then
                SEQ_PATH=$(extract_opds_paths "$(get_xml_file "$SEQINDEX_CUT_URL")" "sequence" | head -1)
            fi
        fi
    fi
    
    # Fallback: use sequence from author page
    if [ -z "$SEQ_PATH" ] && [ -f "$TMPDIR/.seq_path_from_author.txt" ]; then
        SEQ_PATH=$(cat "$TMPDIR/.seq_path_from_author.txt")
    fi
    
    if [ -n "$SEQ_PATH" ]; then
        SEQ_URL="${BASE_URL}${SEQ_PATH}"
        printf '%s' "  ${SEQ_PATH}                             "
        status=$(fetch "$SEQ_URL")
        check_result "$SEQ_URL" "$status" "xml"
        
        # Try to get book URL from sequence page
        if [ -f "$(get_xml_file "$SEQ_URL")" ] && [ ! -f "$TMPDIR/.book_url.txt" ]; then
            BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' \
                "$(get_xml_file "$SEQ_URL")" | head -1)
            if [ -n "$BOOK_URL" ]; then
                echo "$BOOK_URL" > "$TMPDIR/.book_url.txt"
            fi
        fi
    fi
fi

# --------------------------------------------------------------------
# 4. Genres Hierarchy
# --------------------------------------------------------------------
echo ""
echo "--- Genres Hierarchy ---"

GENRESINDEX_URL="${BASE_URL}/opds/genresindex/"
printf "  /opds/genresindex/                             "
status=$(fetch "$GENRESINDEX_URL")
if check_result "$GENRESINDEX_URL" "$status" "xml"; then
    # Extract meta_id from hrefs like /opds/genresindex/meta_id
    META_ID=$(extract_meta_ids_from_href "$(get_xml_file "$GENRESINDEX_URL")" "/opds/genresindex/" | head -1)
    
    if [ -n "$META_ID" ]; then
        GEN_META_URL="${BASE_URL}/opds/genresindex/${META_ID}"
        printf "  /opds/genresindex/${META_ID}                     "
        status=$(fetch "$GEN_META_URL")
        
        if check_result "$GEN_META_URL" "$status" "xml"; then
            # Extract genre_id
            GENRE_ID=$(extract_genre_ids_from_href "$(get_xml_file "$GEN_META_URL")" | head -1)
            
            if [ -n "$GENRE_ID" ]; then
                GEN_BOOKS_URL="${BASE_URL}/opds/genre/${GENRE_ID}"
                printf "  /opds/genre/${GENRE_ID}                       "
                status=$(fetch "$GEN_BOOKS_URL")
                
                if check_result "$GEN_BOOKS_URL" "$status" "xml"; then
                    GEN_BOOKS1_URL="${BASE_URL}/opds/genre/${GENRE_ID}/1"
                    printf "  /opds/genre/${GENRE_ID}/1                      "
                    status=$(fetch "$GEN_BOOKS1_URL")
                    check_result "$GEN_BOOKS1_URL" "$status" "xml"
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

RND_BOOKS_URL="${BASE_URL}/opds/random-books/"
printf "  /opds/random-books/                          "
status=$(fetch "$RND_BOOKS_URL")
check_result "$RND_BOOKS_URL" "$status" "xml"

RND_SEQ_URL="${BASE_URL}/opds/random-sequences/"
printf "  /opds/random-sequences/                      "
status=$(fetch "$RND_SEQ_URL")
check_result "$RND_SEQ_URL" "$status" "xml"

# Random genres hierarchy
RND_GENIDX_URL="${BASE_URL}/opds/rnd/genresindex/"
printf "  /opds/rnd/genresindex/                       "
status=$(fetch "$RND_GENIDX_URL")
if check_result "$RND_GENIDX_URL" "$status" "xml"; then
    RND_META=$(extract_meta_ids_from_href "$(get_xml_file "$RND_GENIDX_URL")" "/opds/rnd/genresindex/" | head -1)
    
    if [ -n "$RND_META" ]; then
        RND_GENM_URL="${BASE_URL}/opds/rnd/genresindex/${RND_META}"
        printf "  /opds/rnd/genresindex/${RND_META}               "
        status=$(fetch "$RND_GENM_URL")
        
        if check_result "$RND_GENM_URL" "$status" "xml"; then
            RND_GENRE=$(safe_grep -oP '/opds/rnd/genre/\K[a-zA-Z0-9_]+' "$(get_xml_file "$RND_GENM_URL")" | head -1)
            
            if [ -n "$RND_GENRE" ]; then
                RND_GENRE_URL="${BASE_URL}/opds/rnd/genre/${RND_GENRE}"
                printf "  /opds/rnd/genre/${RND_GENRE}                  "
                status=$(fetch "$RND_GENRE_URL")
                check_result "$RND_GENRE_URL" "$status" "xml"
            fi
        fi
    fi
fi

# --------------------------------------------------------------------
# 5a. Author from Random Books
# --------------------------------------------------------------------
echo ""
echo "--- Author from Random Books ---"

# Extract author URL from /opds/random-books/
RND_AUTH_PATH=""
if [ -f "$(get_xml_file "$RND_BOOKS_URL")" ]; then
    RND_AUTH_PATH=$(extract_opds_paths "$(get_xml_file "$RND_BOOKS_URL")" "author" | head -1)
fi

if [ -n "$RND_AUTH_PATH" ]; then
    RND_AUTH_URL="${BASE_URL}${RND_AUTH_PATH}"
    printf '%s' "  ${RND_AUTH_PATH} (from rnd)                 "
    status=$(fetch "$RND_AUTH_URL")

    if check_result "$RND_AUTH_URL" "$status" "xml"; then
        # Author views
        printf '%s' "  ${RND_AUTH_PATH}/sequences (from rnd)        "
        status=$(fetch "${RND_AUTH_URL}/sequences")
        check_result "${RND_AUTH_URL}/sequences" "$status" "xml"

        printf '%s' "  ${RND_AUTH_PATH}/sequenceless (from rnd)     "
        status=$(fetch "${RND_AUTH_URL}/sequenceless")
        check_result "${RND_AUTH_URL}/sequenceless" "$status" "xml"

        printf '%s' "  ${RND_AUTH_PATH}/alphabet (from rnd)         "
        status=$(fetch "${RND_AUTH_URL}/alphabet")
        check_result "${RND_AUTH_URL}/alphabet" "$status" "xml"

        printf '%s' "  ${RND_AUTH_PATH}/time (from rnd)             "
        status=$(fetch "${RND_AUTH_URL}/time")
        check_result "${RND_AUTH_URL}/time" "$status" "xml"
    fi
else
    printf "  (no author URL from random-books)                "
    echo "  SKIP (no data)"
    SKIP=$((SKIP + 1))
fi

# --------------------------------------------------------------------
# 5b. Sequence from Random Sequences
# --------------------------------------------------------------------
echo ""
echo "--- Sequence from Random Sequences ---"

# Extract sequence URL from /opds/random-sequences/
RND_SEQ_PATH=""
if [ -f "$(get_xml_file "$RND_SEQ_URL")" ]; then
    RND_SEQ_PATH=$(extract_opds_paths "$(get_xml_file "$RND_SEQ_URL")" "sequence" | head -1)
fi

if [ -n "$RND_SEQ_PATH" ]; then
    RND_SEQ_FULL_URL="${BASE_URL}${RND_SEQ_PATH}"
    printf '%s' "  ${RND_SEQ_PATH} (from rnd)                    "
    status=$(fetch "$RND_SEQ_FULL_URL")
    check_result "$RND_SEQ_FULL_URL" "$status" "xml"
else
    printf "  (no sequence URL from random-sequences)        "
    echo "  SKIP (no data)"
    SKIP=$((SKIP + 1))
fi

# --------------------------------------------------------------------
# 6. Search
# --------------------------------------------------------------------
echo ""
echo "--- Search ---"

printf "  /opds/search?searchTerm=                       "
status=$(fetch "${BASE_URL}/opds/search?searchTerm=")
check_result "${BASE_URL}/opds/search?searchTerm=" "$status" "xml"

printf "  /opds/search/authors?searchTerm=test             "
status=$(fetch "${BASE_URL}/opds/search/authors?searchTerm=test")
check_result "${BASE_URL}/opds/search/authors?searchTerm=test" "$status" "xml"

printf "  /opds/search/sequences?searchTerm=test           "
status=$(fetch "${BASE_URL}/opds/search/sequences?searchTerm=test")
check_result "${BASE_URL}/opds/search/sequences?searchTerm=test" "$status" "xml"

printf "  /opds/search/books?searchTerm=test               "
status=$(fetch "${BASE_URL}/opds/search/books?searchTerm=test")
check_result "${BASE_URL}/opds/search/books?searchTerm=test" "$status" "xml"

printf "  /opds/search/booksanno?searchTerm=test           "
status=$(fetch "${BASE_URL}/opds/search/booksanno?searchTerm=test")
check_result "${BASE_URL}/opds/search/booksanno?searchTerm=test" "$status" "xml"

printf "  /opds/search/booksannovector?searchTerm=test     "
status=$(fetch "${BASE_URL}/opds/search/booksannovector?searchTerm=test")
if [ "$status" = "200" ]; then
    check_result "${BASE_URL}/opds/search/booksannovector?searchTerm=test" "$status" "xml"
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
if [ -f "$TMPDIR/.book_url.txt" ]; then
    BOOK_URL=$(cat "$TMPDIR/.book_url.txt")
fi

# Fallback: try other sources
if [ -z "$BOOK_URL" ] && [ -f "$(get_xml_file "$RND_BOOKS_URL")" ]; then
    BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' "$(get_xml_file "$RND_BOOKS_URL")" | head -1)
fi

if [ -z "$BOOK_URL" ]; then
    TIME_URL="${BASE_URL}/opds/time"
    if [ -f "$(get_xml_file "$TIME_URL")" ]; then
        BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' "$(get_xml_file "$TIME_URL")" | head -1)
    fi
fi

if [ -z "$BOOK_URL" ]; then
    OPDS_ROOT_URL="${BASE_URL}/opds/"
    if [ -f "$(get_xml_file "$OPDS_ROOT_URL")" ]; then
        BOOK_URL=$(safe_grep -oP '(?:/fb2|/read|/plain)/[^/]+/[^"]+' "$(get_xml_file "$OPDS_ROOT_URL")" | head -1)
    fi
fi

if [ -n "$BOOK_URL" ]; then
    # Extract action type, zip file, and fb2 file from URL
    # URL formats: /fb2/zip/file, /read/zip/file, /plain/zip/file
    ACTION=$(echo "$BOOK_URL" | safe_grep -oP '^/(fb2|read|plain)' | tr -d '/')
    ZIP_FILE=$(echo "$BOOK_URL" | safe_grep -oP '/[^/]+/[^/]+$' | sed 's|^/||' | cut -d/ -f1)
    FB2_FILE=$(echo "$BOOK_URL" | safe_grep -oP '/[^/]+/[^/]+$' | sed 's|^/||' | cut -d/ -f2)
    
    if [ -n "$ACTION" ] && [ -n "$ZIP_FILE" ] && [ -n "$FB2_FILE" ]; then
        # /fb2/<zip>/<file> - download
        FB2_URL="${BASE_URL}/fb2/${ZIP_FILE}/${FB2_FILE}"
        printf '%s' "  /fb2/${ZIP_FILE}/${FB2_FILE}                     "
        status=$(fetch "$FB2_URL")
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
        READ_URL="${BASE_URL}/read/${ZIP_FILE}/${FB2_FILE}"
        printf '%s' "  /read/${ZIP_FILE}/${FB2_FILE}                    "
        status=$(fetch "$READ_URL")
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
        PLAIN_URL="${BASE_URL}/plain/${ZIP_FILE}/${FB2_FILE}"
        printf '%s' "  /plain/${ZIP_FILE}/${FB2_FILE}                   "
        status=$(fetch "$PLAIN_URL")
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
COVER_URL=""
if [ -f "$TMPDIR/.cover_url.txt" ]; then
    COVER_URL=$(cat "$TMPDIR/.cover_url.txt")
fi

if [ -n "$COVER_URL" ]; then
    COVER_FULL_URL="${BASE_URL}${COVER_URL}"
    printf '%s' "  ${COVER_URL}                    "
    status=$(fetch "$COVER_FULL_URL")
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
status=$(fetch "${BASE_URL}/interface.js")
if [ "$status" = "200" ]; then
    echo "  PASS (200)"
    PASS=$((PASS + 1))
elif [ "$status" = "404" ]; then
    # Try static path
    status=$(fetch "${BASE_URL}/static/interface.js")
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
status=$(fetch "${BASE_URL}/favicon.ico")
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
echo "  Data saved to: $TMPDIR/"
echo "================================================================"

[ "$FAIL" -gt 0 ] && exit 1
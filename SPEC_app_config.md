# Config file spec

## config.ini

Sections will be chosen by environment variable `APP_ENV`. The `APP_ENV` value is used as the section name (e.g., if `APP_ENV=production`, the `[production]` section is used). If `APP_ENV` is not set, `development` is used by default.

Section reading order:
1. First, values from `[common]` section are loaded (these are base defaults)
2. Then, values from the current section (`[development]` or `[production]`) are loaded
3. Values from the current section **override** values from `[common]` with the same name

Section vars:

```ini
[section_name]
; more logs for logs god
debug = yes                    ; yes|no (converted to boolean True/False)
; postgres connection
pg_host = 127.0.0.1            ; string
pg_base = books                ; string
pg_user = books                ; string
pg_pass = ExamplePassword      ; string

; data dirs
zips_path = ./data             ; filesystem path (string)
pages_path = ./data/pages      ; filesystem path (string)
inpx_file = flibusta_fb2_local.inpx  ; string - archive with .inp files

; for cover pics resize
pic_width = 200                ; integer - max width for cover previews

; show books with deleted=1
hide_deleted = no              ; yes|no (converted to boolean True/False)

; web/opds interface configuration
app_root = /books              ; URL path like '/books' (string), default '' (empty)
web_title = Home OPDS directory ; string
listen_host = 127.0.0.1        ; string - e.g., '0.0.0.0'
listen_port = 8000             ; string - port number
page_size = 50                 ; integer - web page size
search_result_limit = 500      ; integer - max search page size

; memory usage hints for app
; these defaults are for Orange Pi 3 LTS (max 0.5GB RAM usage)
; how many authors/sequences load to ram at one pass
max_pass_length = 4000         ; integer
; how many genres load to ram at one pass
max_genre_pass_length = 5      ; integer
; hint for .list processing in bytes
books_pass_size_hint = 1048576 ; integer - bytes

; vector search configuration
; make tables, may create vectors and use vector search in interface
vector_search = yes            ; yes|no (converted to boolean True/False)
; local ollama url
openai_url = http://127.0.0.1:11434/v1  ; string - URL to OpenAI-compatible API
; example openai model, in ollama use something like "embeddinggemma"
openai_model = text-embedding-3-small   ; string - model name
; does not need for ollama (local installation)
;openai_key = ...              ; string - API key for remote OpenAI API
```

Section `[common]` will be used with any `APP_ENV` content and has the lowest priority. Default values are defined in `app/config.py`:

```ini
[common]
; more logs for logs god
debug = yes
; postgres connection
pg_host = 127.0.0.1
pg_base = books
pg_user = books
pg_pass = ExamplePassword
; data dirs
zips_path = ./data
pages_path = ./data/pages
inpx_file = flibusta_fb2_local.inpx
; for cover pics resize
pic_width = 200
; show books with deleted=1
hide_deleted = no
; web/opds interface root, default ''
;app_root = /books
web_title = Home OPDS directory
listen_host = 127.0.0.1
listen_port = 8000
; used in indexing and in random pages
page_size = 50
search_result_limit = 500

[development]
page_size = 10
search_result_limit = 50

[production]
app_root = /books
debug = no
hide_deleted = yes
```

## Users and passwords file

Should be located at `{zips_path}/passwd` (relative to the `zips_path` from config).

Format:

```
user1:password1
user2:password2
```

If file is omitted or does not exist, any username/password is allowed.

## Type conversion

The following config variables are converted from string to appropriate types:

| Config variable | Type | Allowed values |
|-----------------|------|----------------|
| `debug` | boolean | `yes` → `True`, `no` → `False` |
| `hide_deleted` | boolean | `yes` → `True`, `no` → `False` |
| `vector_search` | boolean | `yes` → `True`, `no` → `False` |
| `page_size` | integer | Numeric string |
| `search_result_limit` | integer | Numeric string |
| `pic_width` | integer | Numeric string |
| `max_pass_length` | integer | Numeric string |
| `max_genre_pass_length` | integer | Numeric string |
| `books_pass_size_hint` | integer | Numeric string |
| `listen_port` | integer | Numeric string |
| All other variables | string | Any text value |
# Config file spec

## config.ini

Sections will be choosen by environment variable `APP_ENV`

Section vars:

```ini
[section_name]
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

; web/opds interface configuration
app_root = /books
web_title = Home OPDS directory
listen_host = 127.0.0.1
listen_port = 8000

; used in indexing and in random pages
page_size = 50
search_result_limit = 500

; .inpx == .zip contained .inp for .zip with .fb2
inpx_file = some_file.inpx

; memory usage hints for app
; theese defaults -- for Orange Pi 3 LTS for use no more than 0.5GB RAM
; how many authors/sequences load to ram at one pass
max_pass_lenth = 4000
; how many genres load to ram at one pass
mas_genre_pass_length = 5
; hint for .list processing in bytes
books_pass_size_hint = 1048576
```

Section `[common]` will be used with any `APP_ENV` content with low priority. Something like this:

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

Should be `zips_path/passwd`

Format:

```
user1:password1
user2:password2
```

If file omitted -- any user/password allowed

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
; web/opds interface root
app_root = /books
web_title = Home OPDS directory
listen_host = 127.0.0.1
listen_port = 8000
; used in indexing and in random pages
page_size = 50
search_result_limit = 500
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
; web/opds interface root
app_root = /books
web_title = Home OPDS directory
listen_host = 127.0.0.1
listen_port = 8000
; used in indexing and in random pages
page_size = 50
search_result_limit = 500

[development]
app_root = /
page_size = 10
search_result_limit = 50

[production]
debug = no
hide_deleted = yes
```

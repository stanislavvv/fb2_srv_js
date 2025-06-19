# ToDo

  * generate .zip.list from .zip -- process every fb2 in .zip, create jsonl for it, write to .zip.list, if .zip.list older than .zip or does not exist -- DONE
  * fill database from .zip.list -- create db struct if needed and fill tables for books, authors, sequences and so on -- DONE
  * create static files for (see SPEC_static_files.md):
    * authors -- DONE
    * sequences -- DONE
    * genres -- IN-PROGRESS
    * covers (aa/bb/aabbcc...ee.jpg) -- DONE (but not for nginx)
  * opds interface for static files + DB

## Small parts

  * indexing at all:
    * debug log config param using (now always 'debug = yes')
  * static files:
    * covers: inspect image cover creations in *lists (see base64 decode errors in `cover` commands)
    * covers: copy default cover to root of covers tree (for nginx `@try_files` directive) + prepare nginx example
  * database:
  * opds:

# ToDo

  * generate .zip.list from .zip -- process every fb2 in .zip, create jsonl for it, write to .zip.list, if .zip.list older than .zip or does not exist -- DONE
  * fill database from .zip.list -- create db struct if needed and fill tables for books, authors, sequences and so on -- DONE
  * create static files for (see SPEC_static_files.md):
    * authors -- DONE
    * sequences -- DONE
    * genres -- DONE
    * covers (aa/bb/aabbcc...ee.jpg)
  * opds interface for static files + DB

## Small parts

  * if can't decode image data -- set cover to null (see f.fb2-379005-382982.zip/381738.fb2) -- TESTING
  * predecode .inpx and store predecoded data for history and use historic diff for `new_lists` (or not use, if does not exists) -- NOT REALIZED (every file is unique)
  * inspect image cover creations in *lists (see base64 decode errors in `cover` commands)

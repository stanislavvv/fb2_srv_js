# ToDo

  * generate .zip.list from .zip -- process every fb2 in .zip, create jsonl for it, write to .zip.list, if .zip.list older than .zip or does not exist
  * fill database from .zip.list -- create db struct if needed and fill tables for books, authors, sequences and so on
  * create static files for (see SPEC_static_files.md):
    * authors
    * sequences
    * genres
  * opds interface for static files + DB

## Small parts

  * if can't decode image data -- set cover to null (f.fb2-185838-188548.zip for test .list creation)
  * predecode .inpx and store predecoded data for history and use historic diff for `new_lists` (or not use, if does not exists)

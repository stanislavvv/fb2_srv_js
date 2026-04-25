# ToDo

OPDS interface is done and working

Nothing global ToDo

## Critical


## Small parts

  * common:
    * [bug][minor] date_time format in output: "YYYY-MM-DD HH:MM:SS_00:00" instead of ISO 8601
  * indexing:
    * [bug] too aggressive quota marks removal ('"word" word' -> 'word" word'): some names stored wrong
    * [bug] make_id() duplicates uppercase conversion
    * [feature] per-zip/global author name replacement (mostly for joining nickname and real name)
  * opds: -- no tasks
  * docs:
    * nginx example for covers (`@try_files` and default cover)

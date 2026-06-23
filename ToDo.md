# ToDo

OPDS interface is done and working

Nothing global ToDo

## Critical


## Small parts

  * common:
    * [bug][minor] date_time format in output: "YYYY-MM-DD HH:MM:SS_00:00" instead of ISO 8601
  * indexing:
    * [bug] too aggressive quota marks removal ('"word" word' -> 'word" word'): some names stored wrong -- testing
    * [bug] make_id() duplicates uppercase conversion -- testing
    * [feature] per-zip/global author name replacement (mostly for joining nickname and real name)
  * opds:
    * add golang variant for webapp -- python eat too much ram in idle. See ToDo_golang.md
  * docs:
    * nginx example for covers (`@try_files` and default cover)

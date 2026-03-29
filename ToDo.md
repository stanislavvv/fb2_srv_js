# ToDo

OPDS interface is done and working

Nothing global ToDo

## Critical

  * [bug] str_normalize() does not remove special characters, required by spec
  * [bug] date_time format in output: "YYYY-MM-DD HH:MM:SS_00:00" instead of ISO 8601

## Small parts

  * indexing:
    * [bug] make_id() duplicates uppercase conversion
    * per-zip/global author name replacement (mostly for joining nickname and real name)
  * opds:
    * [bug] pagination: "next" link always added, no check for last page
    * [bug] page = last_page + 1 should return empty feed with rel="prev" link
  * docs:
    * nginx example for covers (`@try_files` and default cover)
    * [maybe] spec to THIS library opds output -- by ai, need some editing

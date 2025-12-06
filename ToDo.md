# ToDo

OPDS interface is done and working

Nothing global ToDo

## Small parts

  * common:
    * configfile fields types (hide_deleted must be boolean)
  * indexing:
    * [lowprio] pagination from config (hardcoded to 50 at now)
  * opds:
    * [BUG] must sort by number in sequence books list
    * [BUG] wrong sort in author's sequenses list
    * [bug] wrong headers in random books in genre, author sequences
    * [bug] no language field in book entry
    * [feature] add plain-fb2 output and use in-js xslt for book reading
    * [feature] last+1 page in paginated must be empty page with opds header (need testing in booreaders)
  * docs:
    * nginx example for covers (`@try_files` and default cover)
    * [maybe] spec to THIS library opds output

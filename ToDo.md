# ToDo

OPDS interface is done and working

Nothing global ToDo

## Small parts

  * common:
    * configfile fields types (hide_deleted must be boolean)
  * indexing:
    * per-zip/global author name replacement (mostly for joining nickname and real name)
    * [lowprio] pagination from config (hardcoded to 50 at now)
  * opds:
    * [BUG] after inter-booklist navigaton (next page in genre, from author's sequence to sequence, reload by link) page MUST scroll to beginnig
    * [feature] add plain-fb2 output and use in-js xslt for book reading (in-browser xslt works bad)
    * [feature] last+1 page in paginated must be empty page with opds header (need testing in booreaders)
  * docs:
    * nginx example for covers (`@try_files` and default cover)
    * [maybe] spec to THIS library opds output

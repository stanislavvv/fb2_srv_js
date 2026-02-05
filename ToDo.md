# ToDo

OPDS interface is done and working

Nothing global ToDo

## Small parts

  * common:
    * configfile fields types (hide_deleted must be boolean)
  * indexing:
    * per-zip/global author name replacement (mostly for joining nickname and real name)
    * [bug] `vector` parameter need run several times with different max_pass_lenth for process all books (may be rewrite into .zip.list processing?)
  * opds:
    * [BUG] after inter-booklist navigaton (next page in genre, from author's sequence to sequence, reload by link) page MUST scroll to beginnig
    * [feature] add plain-fb2 output and use in-js xslt for book reading (in-browser xslt works bad)
    * [chrome bug] chrome VERY SLOW render big html without js, especially with embedded images. May be feature above will help.
    * [feature] last+1 page in paginated must be empty page with opds header (need testing in booreaders)
  * docs:
    * nginx example for covers (`@try_files` and default cover)
    * [maybe] spec to THIS library opds output

# ToDo

OPDS interface is done and working

Nothing global ToDo

## Small parts

  * common:
    * configfile fields types (hide_deleted must be boolean)
  * indexing:
    * [lowprio] pagination from config (hardcoded to 50 at now)
  * opds:
    * [bug] wrong headers in random books in genre, author sequences
    * [feature] add plain-fb2 output and use in-js xslt for book reading
    * [feature] last+1 page in paginated must be empty page with opds header (need testing in booreaders)
    * [lowprio] [feature] try css for xml as in https://www.w3schools.com/xml/cd_catalog_with_css.xml (with `text/xhtml` content-type) and test book reader
  * docs:
    * nginx example for covers (`@try_files` and default cover)
    * [maybe] spec to THIS library opds output

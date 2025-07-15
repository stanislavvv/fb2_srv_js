# ToDo

OPDS interface is done and working

Nothing global ToDo

## Small parts

  * indexing:
    * test deleted flag in config
    * [lowprio] pagination from config (hardcoded to 50 at now)
  * opds:
    * [feature] last+1 page in paginated must be empty page with opds header (need testing in booreaders)
    * css in simple lists (test in mobile browser)
    * [lowprio] [feature] try css for xml as in https://www.w3schools.com/xml/cd_catalog_with_css.xml (with `text/xhtml` content-type) and test book reader
    * test app root from config
  * docs:
    * nginx example for covers (`@try_files` and default cover)
    * [maybe] spec to THIS library opds output

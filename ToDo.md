# ToDo

  * opds interface for static files + DB
    * /opds base:
      * `/opds/authorsindex` -- single letter links to three-letter lists which links to authors
        * `/opds/author/{id[0:2]}/{id[2:2]}/{id}` -- tree for author
      * `/opds/sequencesindex` -- as for authors, but for sequences
        * `/opds/sequence/{id[0:2]}/{id[2:2]}/{id}` -- books list in sequence
      * `/opds/genresindex` -- genres groups links to genres in group which links to genres
        * `/opds/genre/{id}` -- paginated books list in genre with `/{number}` in next pages
  * /opds optional:
    * `/opds/search`
    * `/opds/time` -- books by date, simple list with `/{number}` in next pages
    * `/opds/random-books` -- one page of random books list 
    * `/opds/random-sequences` -- one page of random sequences list
    * `/opds/rnd-genresindex` -- as in genresindex but links to `rnd-genre` instead `genre`
      * `/opds/rnd-genre/{id}` -- one page of random books list in this genre

## Small parts

  * opds:
    * user URL and LANG arrays instead hardcoded strings -- DONE (may be)
    * authors non-sequences books page must use prepared data
  * docs:
    * nginx example for covers (`@try_files` and default cover)
    * spec to url tree -- DONE (may be it even complete)
    * [maybe] spec to THIS library opds output

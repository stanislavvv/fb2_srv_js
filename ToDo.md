# ToDo

OPDS interface is done and working

  * opds interface for static files + DB -- DONE
    * /opds base:
      * `/opds/authorsindex` -- single letter links to three-letter lists which links to authors -- DONE
        * `/opds/author/{id[0:2]}/{id[2:2]}/{id}` -- tree for author -- DONE
      * `/opds/sequencesindex` -- as for authors, but for sequences -- DONE
        * `/opds/sequence/{id[0:2]}/{id[2:2]}/{id}` -- books list in sequence -- DONE
      * `/opds/genresindex` -- genres groups links to genres in group which links to genres -- DONE
        * `/opds/genre/{id}` -- paginated books list in genre with `/{number}` in next pages -- DONE
  * /opds optional: -- DONE
    * `/opds/search` -- DONE
      * `/search/authors` -- List of found authors -- DONE
      * `/search/sequences` -- List of found sequences -- DONE
      * `/search/books` -- List of found books -- DONE
    * `/opds/time` -- books by date, simple list with `/{number}` in next pages -- DONE
    * `/opds/random-books` -- one page of random books list -- DONE
    * `/opds/random-sequences` -- one page of random sequences list -- DONE
    * `/opds/rnd-genresindex` -- as in genresindex but links to `rnd-genre` instead `genre` -- DONE
      * `/opds/rnd-genre/{id}` -- one page of random books list in this genre -- DONE

## Small parts

  * indexing:
    * use URL from config.py in data path (with removing `^/opds`)
  * opds:
    * authors non-sequences books page must use prepared data (opds_struct.py, opds_book_list, `elif layout == "author_nonseq":`)
    * approot usage in all urls (for use '/books/opds/' in site subtree)
  * docs:
    * nginx example for covers (`@try_files` and default cover)
    * [maybe] spec to THIS library opds output

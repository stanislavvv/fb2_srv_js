# Static files for web/opds interface

## Some basic info

* group of genres will be named as genres meta
* meta_id, meta_name takes from external genres_meta.list (must fail if not exists)
* genre_id, genre_name takes from external genres.list (must fail if not exists)
* any other *_id is string calculated from corresponding normalized name/title:
    * collision will be ignored (no collision case in production data)
    * minimal length 30 letters
* data normalization for id calculation is:
  * space stripping
  * special characters removal
  * uppercase
  * similar character replace (like 'Ё' to 'Е')
* any search will use database, not theese files
* any sort will be custom for separate latin and cyrillic
* field `deleted` -- for user interface, not for storage
* if path spec contains struct like '[aa]/[bb]' for lower files count in single directory, then:
  * [aa] and [bb] must not be zero-length
  * only '[aa]/[bb]' but not '[aa]/[bb]/[cc]'


## Directory tree struct

* authors/[aa]/[bb]/[author_id]/ -- author's data directory

  * [author_id] -- author's id
  * [aa] -- string[2], first 2 letters of author's id
  * [bb] -- string[2], second 2 letters of author's id

  Files:
  * all.json -- all author's books array `[book_info, ...]`
  * index.json -- author's info as in author_info
  * sequences.json -- author's sequences list like `[{"name": "Seq name", "id": "seq_id", "cnt": 1}, ...]` where cnt is a count of books in sequence with this id for this author
  * sequenceless.json -- author's books ids list for books not in any sequence like `["book_id", ...]`

* authorsindex/ -- root dir of author's lists data directory

  Files:
  * index.json -- list of uppercased first letters of all authors names in silly_dict format with first letter as "key"

* authorsindex/[a] -- directory for authors lists for [a]
  * [a] -- First letter of author's name in upper case

  Files:
  * index.json -- silly_dict with [aaa] as "key"
    * [aaa] -- left justified string[3] of first 3 letters of author's name in uppercase
  * [aaa].json -- dict of author_id:author_name for authors with [aaa] like: `{"author_id": "author name", ...}`

* sequences/[aa]/[bb]/ -- sequence data directory

  * [aa] -- string[2], first 2 letters of sequence id
  * [bb] -- string[2], second 2 letters of sequence id

  Files:
  * [sequence_id].json -- all sequence's books array with items as in SPEC_list.md without cover data

* sequencesindex/ -- sequences lists directory
  Files:
  * index.json -- list of uppercased first letters of all sequences names in silly_dict format with first letter as "key"

* sequenceindex/[a]/ directory for sequences lists for [a]

  * [a] -- First letter of author's name in upper case

  Files:
  * index.json -- silly_dict with [aaa] as "key"
    * [aaa] -- left justified string[3] of first 3 letters of sequence name in upper case
  * [aaa].json -- dict of sequence_id:sequence_name for sequences with [aaa] like: `{"seq_id": "Seq Name", ...}`

* genres/[genre_id]/ -- genre data directory

  Files:
  * all.json -- book_id list in genre like: `["book_id", ...]`
  * [int].json -- per-page genre's books array with items as in SPEC_list.md without cover data, page size from config
    * [int] -- int page number from 0, no upper limit

* genresindex/ -- genres lists directory

  Files:
  * index.json -- dict of meta_id:meta_name like: `{"1": "meta name", ...}`, data from genres_meta.list
  * [meta_id].json -- dict of genre_id:genre_name in [meta_id] like `{"genre_id", "genre name", ...}`, data from corresponded part of genres.list
    * [meta_id] -- as in genres_meta.list

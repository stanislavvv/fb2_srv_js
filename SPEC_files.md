# Static files for web/opds interface

## Some requirements for filesystem

Any linux fs should works fine.

* min 255 characters in single filename
* case-sensitive
* min 2047 characters in full filename (with path)

## Some basic info

* all directories from current doc created in config.ini's `pages_path` 
* group of genres will be named as genres meta
* meta_id, meta_name data takes from external genres_meta.list (must hard fail in indexing/warn in interface if not exists or fallback to id from genres.list or to some default value), meta_id "[0-9a-z_-]+".
* genre_id, genre_name takes from external genres.list (must hard fail in indexing/warn in interface if not exists or fallback to genre_id (for genre_name too) from indexed books), genre_id currently string "[0-9a-z_-]+"
* other (not genre_id or meta_id) *_id is string calculated from corresponding character sequence.
  * author_id -- string, calculated from author's name with normalization
  * seq_id -- string, calculated from sequence name with normalization
  * book_id -- string, calculated from raw path 'zipfilename/bookfilename'. 'zipfilename/bookfilename' MUST be unique in library. 'bookfilename' MUST be unique in 'zipfilename'. 'zipfilename' is unique in data directory as filesystem property (path used as-is, no normalization).
  * collisions will be ignored (no collision seen in production data)
  * length for calculated id must be >=30 characters (current implementation use md5 with 32 char result)
* data normalization for id calculation (if applicable) is:
  * space stripping
  * special characters removal
  * uppercase (not for path)
  * similar character replace (like 'Ё' to 'Е', implementation depended)
* any search will use database, not theese files
* field `deleted` -- book is marked deleted and may be hidden for user. Boolean in database, in files is int {0,1} (1 in file == true in database). This field for interface, all data must remains, because 'hide_deleted' field in config.

### Configuration data for books genre classification files format

If any *.list was changed, all library must be reindexed from scratch.

1. `genres_meta.list` -- text, one meta genre per line.

Contains initial meta genres list. Unchangeable during normal operations.

All genres groups/meta genres in this library must be from this list. This restriction implemented using genres.list's 'meta_id' field.

Line format:

`<meta_id>|<meta_name>`

* `meta_id` -- string, id of genre group/meta genre. Current data use '[0-9]+' (numeric string)

* `meta_name` -- string in utf-8, name of genres group/meta genre

2. `genres.list` -- text, one genre per line

Contains initial genres list for this library. Unchangeable during normal operations.

All genres in interface must be from this list (only if list exists). During indexing books, jsonl_book (see SPEC_lists.md) genres not from this list must be replaced via genres_replace.list or to default value (currently 'other').

If this file deleted, right indexing not possible. Interface must work with wrong genre names in books lists.

Line format:

`<meta_id>|<genre_id>|<genre_name>`

* `meta_id` -- must exists `genres_meta.list`
* `genre_id` -- string
* `genre_name` -- string in utf-8

3. `genres_replace.list` -- text, one replacement per line

Contains replacements for wrong genres, found in some books in library. Unchangeable during normal operations. Add new lines only if wrong genres in new books and commit it in git.

Used for indexing, not in interface.

Line format:

`<wrong_genre_id>|<genre_id>[,genre_id]`

* `wrong_genre_id` -- string as in genre field in processed book (can't specify WRONG content, but it is not genre_id from genres_list)
* `genre_id` -- exactly as in genres.list (if any replacement will be added, genre_id MUST taken from it)

Can be multiple comma-separated `genre_id` in genres replacement for jsonl_book line (see SPEC_lists.md)

Can be empty `genre_id` field for deleting wrong genre item from jsonl_book line during indexing.

## Directory tree struct

* authors/[aa]/[bb]/[author_id]/ -- author's data directory

  * [author_id] -- author's id (as in basic info)
  * [aa] -- string[2], first 2 characters of author_id
  * [bb] -- string[2], next 2 characters of author_id

  Files:
  * all.json -- array of book_info (see SPEC_lists.md) of books from this author
  * index.json -- author's info as in author_info (see SPEC_lists.md)
  * sequences.json -- array of sequence_info_cnt where `cnt` field is a count of books in sequence with this id for this author. Contain all sequences of this author.
  * sequenceless.json -- author's books ids list for books not in any sequence like `["book_id", ...]`

* authorsindex/ -- root dir of author's lists data directory

  Files:
  * index.json -- silly_dict (see SPEC_lists.md) with [a] as "key"
    * [a] -- First character of author's name in upper case (no other normalization). Only for author's in library, not all letters in all alphabets.

* authorsindex/[a] -- directory for authors lists for [a], if any exists.

  Files:
  * index.json -- silly_dict with [aaa] as "key"
    * [aaa] -- left justified space padded string[3] of first 3 characters of author's name in uppercase (any amount authors == one record).
  * [aaa].json -- dict of author_id:author_name for authors with [aaa] like: `{"author_id": "author name", ...}`

* sequences/[cc]/[dd]/ -- sequence data directory, create when need (new [cc]/[dd] from new [seq_id])

  * [cc] -- string[2], first 2 characters of seq_id
  * [dd] -- string[2], next 2 characters of seq_id

  Files:
  * [seq_id].json -- array of book_info for all books in this sequence. Created only if one or more books are in this sequence. seq_id -- calculated from sequence name, see basic info.

  Any other files in this directory is a mistake and must be ignored.

* sequencesindex/ -- sequences index lists root directory
  Files:
  * index.json -- silly_dict with [a] as "key"
    * [a] -- First character of sequence name in upper case (no other normalization)

* sequencesindex/[a]/ directory for sequences lists for [a]

  Files:
  * index.json -- silly_dict with [aaa] as "key"
    * [aaa] -- left justified space padded string[3] of first 3 characters of sequence name in upper case
  * [aaa].json -- sequence_info dict (see SPEC_lists.md) for sequences with [aaa] in name

* genres/[genre_id]/ -- genre data directory. 

  Directory and content exists only if any books in genre.

  Files:
  * all.json -- all book_id list in genre like: `["book_id", ...]` (for taking random books in genre without database, not really book list). ToDo: change filename to book_ids.json in implementation.
  * [int].json -- per-page array of book_info in genre_id, page size hardcoded to 50, last page size in {1..50}, empty page must not exist
    * [int] -- int page number from 0, no upper limit, first page in genre == 0.json

* genresindex/ -- genres lists directory

  Files:
  * index.json -- dict of meta_id:meta_name like: `{"1": "meta name", ...}`, contains meta's from genres_meta.list only if corresponding genres in meta have books.
  * [meta_id].json -- dict of genre_id:genre_name in [meta_id] like `{"genre_id": "genre_name", ...}`, based on genres.list, genres_replace.list and genres_meta.list. Data appended only if any book found in genre.
    * [meta_id] -- as in genres_meta.list
    * genre_id, genre_name -- as in genres.list

* books/ -- per-book info directory
  * books/[ee]/[ff]/ -- books data directory. Create for corresponding book_id
    * [ee] -- string[2], first 2 characters of book_id
    * [ff] -- string[2], next 2 characters of book_id

    Files:
    * [book_id].json -- book_info struct
    * [book_id].jpg -- book cover, if exists in book

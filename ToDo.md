# ToDo

OPDS interface is done and working

Nothing global ToDo

## Critical

None

## Refactoring

  * [refactor] extract common auth module (`app/auth.py`):
    - merge `@opds.before_request` from `view_opds.py` and `@require_auth` from `view_static.py`
    - move `_check_auth()` and `_auth_required_response()` to a shared module
    - implement two decorators: one for blueprint `before_request`, one for individual routes

  * [refactor] add path validation decorator (for `view_opds.py`):
    - create `@validate_path_params(**validators)` decorator
    - remove duplicated `validate_id()` calls from 20+ route handlers

  * [refactor] single session for batch DB operations (`app/data.py`):
    - functions `get_exist_authors()`, `get_exist_seqs()`, `get_exist_genres()`, `get_exists_book()` each create a separate connection
    - accept `session` as argument and reuse one session from calling code

  * [future] multi-term search conditions builder (`app/opds_db.py`):
    - function `build_multiterm_conditions()` to generate AND/OR ILIKE conditions
    - remove 4 identical search pattern copies in `opds_books_db()` and `opds_simple_list_db()`

## Small parts

  * common:
    * [bug][minor] date_time format in output: "YYYY-MM-DD HH:MM:SS_00:00" instead of ISO 8601
  * indexing:
    * [bug] too aggressive quota marks removal ('"word" word' -> 'word" word'): some names stored wrong -- testing
    * [bug] make_id() duplicates uppercase conversion -- testing
    * [feature] per-zip/global author name replacement (mostly for joining nickname and real name) -- testing
  * opds:
    * add golang variant for webapp -- python eat too much ram in idle. See ToDo_golang.md -- testing
    * [feature] add "+" and "-" buttons for font size in web interface.
  * docs:
    * nginx example for covers (`@try_files` and default cover)

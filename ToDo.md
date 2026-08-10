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

  * [future] multi-term search conditions builder (`app/opds_db.py`):
    - function `build_multiterm_conditions()` to generate AND/OR ILIKE conditions
    - remove 4 identical search pattern copies in `opds_books_db()` and `opds_simple_list_db()`

## Small parts

  * common:
    * [bug][minor] date_time format in output: "YYYY-MM-DD HH:MM:SS_00:00" instead of ISO 8601
  * indexing:
    * [feature] per-zip/global author name replacement (mostly for joining nickname and real name)
  * opds: None
  * docs:
    * nginx example for covers (`@try_files` and default cover)

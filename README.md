# Revised fb2_srv_semipg

## Setup app

  * `make venv` -- create python virtualenv and install modules
  * create postgres database (see `docker-compose.yml.example`)
  * create `config.ini` (see `SPEC_app_config.md` and `app/config.py`) with appropriate values

## Index .zip for web interface

### Create .zip.list

  * first run: `./datachew.sh lists` -- for every `.zip` file create corresponding `.zip.list`
  * every update run `./datachew.sh new_lists` -- create `.zip.list` only for new `.zip` (or `.zip` with new `.zip.replace`)

### Fill books to database

  * `./datachew.sh tables` -- must run on empty db and may be omitted other case
  * `./datachew.sh fillonly` -- books will be filled to database (skipped, if exists)

### Create static indexes

  * `./datachew.sh covers` -- make dir/file struct for book covers previews
  * `./datachew.sh authors` -- make static indexes for authors

### Run development server

useful for debug configuration

```shell
./opds.sh
```

### Run production server

```shell
./gunicorn.sh
```

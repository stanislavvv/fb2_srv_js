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

  * `./datachew.sh books` -- make dir/file struct for books/covers
  * `./datachew.sh authors` -- make static indexes for authors

### Create vector data

Used in vector search if enabled in config

`./datachew.sh vectors`

1. get books annotations from database
2. get per-book vectors from openai-like embeddings service
3. store books vectors in database

### Run development server

useful for debug configuration

```shell
./opds.sh
```

### Run production server

```shell
./gunicorn.sh
```

### Simple authorization if need

Sometimes library must not be open for all internet as by default now.

If you need login-pass access to library -- create file `passwords` in `zips_path` directory with lines like:

```
login:password
```

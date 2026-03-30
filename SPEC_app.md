# Application Specification

## Common Considerations

This service provides a web interface for accessing an FB2 book library through OPDS protocol. The indexing process extracts metadata from FB2 files, stores it in PostgreSQL, and generates static data files for efficient web access.

All URLs and file paths are relative to `app_root`.

### Basic Requirements
- Filesystem: Unix-like (255-char filename limit, case-sensitive, 2047-char path)

### ID Generation
IDs are generated as hash of normalized string. Current implementation uses MD5 
(hex-encoded, 32 characters).

### Configuration Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `app_root` | Base path for all URLs | `'/'`, `'/books'` |
| `pages_path` | Static data files directory | `'/var/lib/fb2_data/pages'` |
| `zips_path` | FB2 zip files directory | `'/var/lib/fb2_zips'` |
| `inpx_file` | INPX container filename | `'library.inpx'` |
| `hide_deleted` | Skip deleted books during indexing (default: false) | |
| `vector_search` | Enable vector search | |
| `author_placeholder` | Placeholder for missing authors | `'Автор Неизвестен'` |
| `pic_width` | Max width for cover images | `300` |
| `max_pass_length` | Batch size for authors/sequences | `4000` |
| `max_pass_length_gen` | Batch size for genres | `5` |
| `books_pass_size_hint` | Batch size for book lists (bytes) | `10485760` |
| `page_size` | Web page size (books per page) | `50` |
| `search_result_limit` | Max search page size | `500` |
| `default_cover_image` | Path to default cover image | `'/books/default.jpg'` |
| `default_cache_seconds` | OPDS responses cache time (sec) | `604800` |
| `static_file_cache_seconds` | Static files cache time (sec) | `2592000` |
| `random_cache_seconds` | Random elements cache time (sec) | `300` |
| `xslt_file` | XSLT file for FB2 to HTML conversion | `'fb2_to_html.xsl'` |
| `debug` | Enable debug logs | |
| `max_search_query_length` | Maximum search query length | `128 chars` |


### Genre Identification

- `<meta_id>` -- string identifier for genre group, `[0-9a-z_]+`
- `<gen_id>` -- text genre identifier, `[0-9a-z_]+`
- Genre set is broader than original FB2 format

### Additional Configuration Files

Genre classification files (stored in app root, not data directory). Missing or invalid file causes indexing hard fail.

| File | Purpose | Format |
|------|---------|--------|
| `genres_meta.list` | Meta genre groups | `<meta_id>|<meta_name>` |
| `genres.list` | Individual genres | `<meta_id>|<genre_id>|<genre_name>` |
| `genres_replace.list` | Genre replacements | `<wrong_id>|<genre_id>[,genre_id,...]` |

Field types: `meta_id`, `genre_id` -- string identifier; `meta_name`, `genre_name` -- UTF-8 string.

## Data Structures

### book_info (Index Data)

Index data for database and static files. Same as `jsonl_book`, without `cover` field.

### author_info

```json
{
  "name": "string",    // '--- unknown ---' if not defined in book
  "id": "string",      // hash(normalized author name)
  "info": "text"       // Author biography (default: '')
}
```

### sequence_info

```json
{
  "name": "string",
  "id": "string",
  "cnt": int    // optional, count of books in this sequence (used in lists)
}
```

### sequence_ref

Book-sequence binding data.

```json
{
  "name": "string",
  "id": "string",    // hash(normalized sequence name)
  "num": int         // optional, volume/sequence number, 0 == unknown
}
```

### silly_dict

Key existence check. Value is `1` or object count.

```json
{"key": 1, ...}
```

### jsonl_book (Pre-index Data)

Intermediate data during indexing. One JSON structure per line.

```json
{
  "zipfile": "filename.zip",      // required
  "filename": "filename.fb2",     // required
  "genres": ["string", ...],      // required, non-empty array
  "authors": [ ... ],             // required, non-empty array
  "sequences": null || [ ... ],   // optional
  "book_title": "string",         // required
  "cover": {
    "content-type": "image/jpeg",  // or image/png
    "data": "base64(image)"
  },
  "book_id": "string",            // required
  "lang": "string[2]",            // required (ISO 639-1)
  "date_time": "YYYY-MM-DD[T[HH:MM:SS[.SSS][(+|-)HH:MM]]]",  
  // ISO 8601 compatible, time and timezone optional
  // Examples: "2024-01-15", "2024-01-15T00:00:00", "2024-01-15T14:30:00+05:00"
  "size": "string(int(filename size in bytes))",  // required
  "annotation": "text/stripped html string",      // optional (may be null)
  "pub_info": {                   // optional (may be null)
    "isbn": null || "string",
    "year": null || "string[4]",  // str(year)
    "publisher": null || "string",
    "publisher_id": "string"      // hash(normalized publisher)
  },
  "deleted": 0 || 1               // optional, default: 0
}
```

## URL Specification

URL Parameter Notation:
- `<id>` -- alphanumeric string (MD5 result)
- `<sub1>` -- first 2 hex chars of ID (e.g., `05`)
- `<sub2>` -- next 2 hex chars of ID (e.g., `ef`)
- `<cut>` -- first uppercase letter from name
- `<cut1>` -- first uppercase letter
- `<cut2>` -- first 1-3 uppercase letters, left-padded to 3
- `<page>` -- page number (int >= 0), omit if 0
- ID Path Format: `<sub1>/<sub2>/<full_id>` (e.g., `05/ef/05ef7b17...`)

### Core URLs

- `/` -- Library entry point
- `/fb2/<zip_file>/<filename>` -- Download FB2 zip
- `/plain/<zip_file>/<filename>` -- Download plain `.fb2` file
- `/read/<zip_file>/<filename>` -- Read in browser (XSL->HTML)
- `/books/<sub1>/<sub2>/<book_id>.jpg` -- Book cover image
- `/interface.js` -- JavaScript interface file
- `/favicon.ico` -- Favicon file

### OPDS URLs

All OPDS URLs begin from `/opds`:

#### Root and Navigation

- `/opds/` -- Main menu with primary sections

#### Books Lists

- `/opds/time` -- All books by date (newest first)
- `/opds/time/<page>` -- Paginated books by date

#### Authors

- `/opds/authorsindex/` -- List of first letters for authors
- `/opds/authorsindex/<cut>` -- Authors by first 1 uppercase chars
- `/opds/authorsindex/<cut1>/<cut2>` -- Authors by 1 char + 3 char, uppercased
- `/opds/author/<sub1>/<sub2>/<author_id>` -- Author page
- `/opds/author/<sub1>/<sub2>/<author_id>/sequences` -- Author's sequences
- `/opds/author/<sub1>/<sub2>/<author_id>/sequenceless` -- Books not in sequences
- `/opds/author/<sub1>/<sub2>/<author_id>/alphabet` -- Books sorted alphabetically
- `/opds/author/<sub1>/<sub2>/<author_id>/time` -- Books by date added
- `/opds/author/<sub1>/<sub2>/<author_id>/<seq_id>` -- Books in specific sequence

#### Sequences

- `/opds/sequencesindex/` -- List of first letters for sequences
- `/opds/sequencesindex/<cut>` -- Sequences by first 1 uppercase chars
- `/opds/sequencesindex/<cut1>/<cut2>` -- Sequences by 1 char + 3 char, uppercased
- `/opds/sequence/<sub1>/<sub2>/<seq_id>` -- Books in sequence

#### Genres

- `/opds/genresindex/` -- Genre groups (meta genres)
- `/opds/genresindex/<meta_id>` -- Genres in group
- `/opds/genre/<gen_id>` -- Books in genre
- `/opds/genre/<gen_id>/<page>` -- Paginated books in genre

#### Random Elements (no pagination, no "next" link)

- `/opds/random-books/` -- Random books (up to `page_size`)
- `/opds/random-sequences/` -- Random sequences (up to `page_size`)
- `/opds/rnd/genresindex/` -- Random genre groups
- `/opds/rnd/genresindex/<meta_id>` -- Random genres in group
- `/opds/rnd/genre/<gen_id>` -- Random books in genre

#### Search

- `/opds/search?searchTerm=<query>` -- Search root page
- `/opds/search/authors?searchTerm=<query>` -- Search in author names
- `/opds/search/sequences?searchTerm=<query>` -- Search in sequence names
- `/opds/search/books?searchTerm=<query>` -- Search in book titles
- `/opds/search/booksanno?searchTerm=<query>` -- Search in annotations
- `/opds/search/booksannovector?searchTerm=<query>` -- Vector search in annotations (requires `vector_search` config enabled)

Search Parameters:
- `searchTerm` -- string, max 128 characters, must be URL-encoded
- `{searchTerms}` -- placeholder in OPDS link definitions, replaced with URL-encoded value
- Empty query (`searchTerm=`) is valid and returns all entries
- Example: Search for "foo bar" -> `searchTerm=foo+bar` or `searchTerm=foo%20bar`

### Pagination

- Page numbers: `0, 1, 2, ...` (negative values return 404)
- `page=0` may be omitted (no trailing `/`)
- Last page: no `rel="next"` link (if backend can determine last page)
- Request for `page > last_page` returns 404 or empty feed with `rel="prev"` to last page

## OPDS Response Format

### Protocol

- Auth: HTTP Basic if `passwd` file exists
- Caching: OPDS 7 days, random 5 min
- Format: XML (Atom Feed with OPDS-CATALOG profile)
- Content-Type: 'text/xml; charset=utf-8'

### HTTP Headers

```
Content-Type: text/xml; charset=utf-8
Cache-Control: max-age=<seconds>, must-revalidate
```

### Common Feed Elements

```xml
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:os="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:opds="http://opds-spec.org/2010/catalog">

  <id>tag:$TAG</id>
  <title>$TITLE</title>
  <updated>%UPDATED%</updated>
  <icon>/favicon.ico</icon>
  
  <link href="/opds/search?searchTerm={searchTerms}" rel="search" type="application/atom+xml"/>
  <link href="/opds/" rel="start" type="application/atom+xml;profile=opds-catalog"/>
  <link href="/opds/..." rel="self" type="application/atom+xml;profile=opds-catalog"/>
  <link href="/opds/..." rel="up" type="application/atom+xml;profile=opds-catalog"/>
  <link href="/opds/..." rel="next" type="application/atom+xml;profile=opds-catalog"/>
  <link href="/opds/..." rel="prev" type="application/atom+xml;profile=opds-catalog"/>

  <entry>...</entry>
</feed>
```

Link Relation Meanings:
- `start` -- interface start (`/opds/`)
- `self` -- current page
- `up` -- parent or higher-level page
- `next` -- next page (mandatory for paginated lists)
- `prev` -- previous page (mandatory for non-default pages)
- `search` -- search with `{searchTerms}` placeholder

### Entry Types

#### Book Entry

```xml
<entry>
  <id>tag:book:{book_id}</id>
  <title>{book_title}</title>
  <updated>{date_time}</updated>
  
  <author>
    <uri>{author_url}</uri>
    <name>{author_name}</name>
  </author>
  
  <link rel="http://opds-spec.org/acquisition/open-access"
        href="{download_url}"
        type="application/fb2+zip"
        title="Download"/>
  <link rel="http://opds-spec.org/acquisition/open-access"
        href="{read_url}"
        type="text/html"
        title="Read online"/>
  
  <!-- Cover image links (4 variants for OPDS client compatibility) -->
  <link rel="http://opds-spec.org/image"
        href="{cover_url}"
        type="image/jpeg"></link>
  <link rel="x-stanza-cover-image"
        href="{cover_url}"
        type="image/jpeg"></link>
  <link rel="http://opds-spec.org/thumbnail"
        href="{cover_url}"
        type="image/jpeg"></link>
  <link rel="x-stanza-cover-image-thumbnail"
        href="{cover_url}"
        type="image/jpeg"></link>
  
  <link rel="related"
        href="{author_url}"
        type="application/atom+xml"
        title="{author_name}"></link>
  <link rel="related"
        href="{sequence_url}"
        type="application/atom+xml"
        title="{sequence_name}"></link>
  
  <category term="{genre_id}" label="{genre_name}"/>
  
  <dc:language>{lang_id}</dc:language>
  <dc:format>fb2</dc:format>
  
  <content type="text/html">
    {annotation}
  </content>
</entry>
```

#### Section Link Entry

```xml
<entry>
  <id>tag:{section}:{subtag}</id>
  <title>{title}</title>
  <updated>YYYY-MM-DDTHH:MM:SS+TZ</updated>
  <content type="text">{subtitle}</content>
  <link rel="alternate"
        href="{href}"
        type="application/atom+xml;profile=opds-catalog"/>
</entry>
```

#### Author View Entry

Author view includes biography entry and navigation links:

```xml
<!-- Biography entry -->
<entry>
  <updated>YYYY-MM-DDTHH:MM:SS+TZ</updated>
  <id>tag:author:bio:{author_id}</id>
  <title>About author</title>
  <link href="/opds/author/{prefix1}/{prefix2}/{author_id}/sequences"
        rel="http://www.feedbooks.com/opds/facet"
        title="By sequences"
        type="application/atom+xml;profile=opds-catalog"></link>
  <link href="/opds/author/{prefix1}/{prefix2}/{author_id}/sequenceless"
        rel="http://www.feedbooks.com/opds/facet"
        title="Not in sequences"
        type="application/atom+xml;profile=opds-catalog"></link>
  <content type="text/html">{biography_html}</content>
</entry>

<!-- Navigation link entry (alphabet, time, etc.) -->
<entry>
  <updated>YYYY-MM-DDTHH:MM:SS+TZ</updated>
  <id>tag:author:{author_id}:alphabet</id>
  <title>By alphabet</title>
  <link href="/opds/author/{prefix1}/{prefix2}/{author_id}/alphabet"
        type="application/atom+xml;profile=opds-catalog"></link>
</entry>
```

## Input Formats (Indexing)

### .zip Files
ZIP archives with FB2 files in `zips_path` (no subdirs).

### .inpx/.inp Files

Metadata container format (Librus/Library.ru/etc):

- Container (.inpx): ZIP archive with `.inp` files
- Internal (.inp): `\r\n` line separator, `\004` (EOT) field separator, `:` item separator, `,` part separator

| Field | Description |
|-------|-------------|
| 0 | AUTHOR (e.g., `Last,First,Middle`) |
| 1 | GENRE |
| 2 | TITLE |
| 3 | SERIES (optional) |
| 4 | SERNO (optional volume number) |
| 5 | FILE |
| 6 | SIZE |
| 7 | LIBID |
| 8 | DEL (`0`=active, `1`=deleted) |
| 9 | EXT |
| 10 | DATE |
| 11 | LANG |
| 12 | LIBRATE |
| 13 | KEYWORDS |

### .replace Files

JSON files for overriding metadata. Format: `<zipname>.replace` (same base name as ZIP file).

```json
{
  "book1.fb2": {
    "author": [{"last-name": "New", "first-name": "Author"}],
    "genre": ["new_genre"],
    "book-title": "New Title"
  },
  "book2.fb2": {
    "deleted": 0
  }
}
```

### .list Files

Intermediate JSONL format (`.zip.list` or `.zip.list.gz`). One `jsonl_book` per line.

## Database Schema

### books
Primary book information.

- `zipfile` -- String
- `filename` -- String
- `genres` -- ARRAY(String)
- `authors` -- ARRAY(String)
- `sequences` -- ARRAY(String)
- `book_id` -- String(32)
- `lang` -- String
- `date` -- Date
- `size` -- Integer
- `deleted` -- Boolean

### book_descr
Extended book description. Indexed: `books_descr_title` (GIN trgm), `books_descr_anno` (GIN trgm).

- `book_id` -- String(32)
- `book_title` -- String
- `pub_isbn` -- String
- `pub_year` -- String
- `publisher` -- String
- `publisher_id` -- String(32)
- `annotation` -- TEXT

### authors
Author information. Indexed: `authors_names` (GIN trgm).

- `id` -- String(32)
- `name` -- String
- `info` -- TEXT

### sequences
Sequence/series information. Indexed: `seq_names` (GIN trgm).

- `id` -- String(32)
- `name` -- String
- `info` -- TEXT

### genres_meta
Genre groups (meta genres). PK: meta_id.

- `meta_id` -- String(32)
- `name` -- String
- `description` -- TEXT

### genres
Individual genres. PK: id. FK: meta_id.

- `id` -- String(32)
- `meta_id` -- String(32)
- `name` -- String
- `description` -- TEXT

### vectors
Embedding vectors for semantic search. PK: id+type. Indexed: `sqlalchemy_orm_half_precision_index` (HNSW).

- `id` -- String(32)
- `type` -- Enum (0-3)
- `is_bad` -- Boolean
- `embedding` -- HALFVEC(256)

VectorType: BOOK_TITLE=0, BOOK_ANNO=1, SEQUENCE_NAME=2, AUTHOR_NAME=3.

## Processing Commands (datachew.py)

- `lists` -- Recreates all `.zip.list` files from `.zip` archives
- `new_lists` -- Creates `.zip.list` only for new/updated `.zip` files
- `tables` -- Creates DB tables and extensions
- `cleandb` -- Drops all DB tables
- `fillonly` -- Fills DB from `.zip.list` files
- `books` -- Creates static book data and resized covers
- `authors` -- Creates author index structure
- `sequences` -- Creates sequence index structure
- `genres` -- Creates genre index with pagination
- `all` -- Runs complete pipeline in order: new_lists -> tables -> fillonly -> books -> authors -> sequences -> genres
- `vectors` -- Creates semantic search embeddings (requires `vector_search` enabled)

## Static Data Structure

All paths are relative to `pages_path`. IDs use format: `<sub1>/<sub2>/<full_id>`.

### Book Data
- Info: `<pages_path>/books/<sub1>/<sub2>/<book_id>.json`
- Cover: `<pages_path>/books/<sub1>/<sub2>/<book_id>.jpg` (resized to `pic_width`)

### Author/Sequence/Genre Indexes
- Authors: `<pages_path>/author/` with `index.json`, `all.json`, `sequences.json`, `sequenceless.json` and letter subindexes in `<pages_path>/authorsindex/<cut>/`
- Sequences: `<pages_path>/sequence/` with `<seq_id>.json` files and letter subindexes in `<pages_path>/sequencesindex/<cut>/`
- Genres: `<pages_path>/genre/` with paginated `<n>.json` files and meta genre mapping in `<pages_path>/genresindex/<meta_id>.json`

## Vector Search

### Configuration

```ini
vector_search=yes
openai_url=http://localhost:18000/v1
openai_model=text-embedding-3-small
openai_key=-
```

### Vector Types

| Type | Value | Description |
|------|-------|-------------|
| BOOK_TITLE | 0 | Book title embedding |
| BOOK_ANNO | 1 | Book annotation embedding |
| SEQUENCE_NAME | 2 | Sequence name embedding |
| AUTHOR_NAME | 3 | Author name embedding |

### Vector Data

- Vector size: 256 dimensions
- Storage: HALFVEC(256) (half-precision)
- Distance metric: L2 (Euclidean)
- Index: HNSW
- Failed vectors marked with `is_bad=true`

## HTTP Status Codes and Error Handling

- `200` -- Successful response with OPDS XML
- `401` -- Authentication required (if `passwd` file exists)
- `404` -- Resource not found
- `500` -- Internal server error

Authentication (401):
```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Basic realm="Login Required"
```

Error Handling:
- Missing INPX: metadata extracted from FB2 headers
- Invalid FB2: files <500 bytes or non-FB2 format are skipped with logging
- Image errors: multiple extraction attempts made; if all fail, logged and skipped; successful covers converted to JPEG, resized to `pic_width`
- Deleted books: skipped if `hide_deleted=yes`, included with `deleted=1` otherwise


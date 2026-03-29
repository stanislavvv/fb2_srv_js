# Application Specification

## Common Considerations

### Overview

This service provides a web interface for accessing an FB2 (FictionBook) book library through OPDS (Open Publication Distribution System) protocol. The application supports multiple interfaces including OPDS for e-book readers and HTML for web browsers.

All URLs are relative to `APPLICATION_ROOT` configuration value. Examples in this document show both cases (`APPLICATION_ROOT = '/'` and `APPLICATION_ROOT = '/books'`).

### Basic Requirements

- **Filesystem**: Any Linux filesystem with:
  - Minimum 255 characters in single filename
  - Case-sensitive
  - Minimum 2047 characters in full filename (with path)

- **ID Length**: Calculated IDs must be at least 30 characters (current implementation uses MD5 with 32 character result)

- **Normalization**: For ID calculation:
  - Space stripping
  - Special characters removal
  - Uppercase conversion
  - Similar character replacement (e.g., 'Ё' -> 'Е')

### Configuration Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `APPLICATION_ROOT` | Base path for all URLs | `'/'`, `'/books'` |
| `pages_path` | Directory for static data files | `'/var/lib/fb2_data/pages'` |

### Limits and Constants

| Parameter | Value | Description |
|-----------|-------|-------------|
| Maximum search query length | 128 chars | URL encoding supported |
| Pagination page size | 50 items | Books per page |
| Random elements count | 50 items | Max entries in random lists |
| Default cache time | 604800 sec (7 days) | Normal responses |
| Random cache time | 300 sec (5 min) | Random element pages |

### Genre Identification

- `<meta_id>` -- string identifier for genre group, `[0-9a-z_]+`
- `<gen_id>` -- text genre identifier, `[0-9a-z_]+`
- The set of genres is broader than in the original FB2 format

### ID Calculations

| ID Type | Calculation | Example Format |
|---------|-------------|----------------|
| `author_id` | md5(normalized(author name)) | `05ef7b172bdd0a32fe7eda7df2a0e1c7` |
| `seq_id` | md5(normalized(sequence name)) | `e1f63f0997da77cfbcbaee19c2079661` |
| `book_id` | md5(zipfilename/bookfilename) | `a719e2d4695b93f1062834f5c76f0cbe` |
| `publisher_id` | md5(normalized(publisher)) | `...` |

All IDs are in hex format `[0-9a-f]+` with length >= 30 characters.

## Data Structures

### book_info (Index Data)

```json
{
  "zipfile": "filename.zip",      // required
  "filename": "filename.fb2",     // required
  "genres": ["string", ...],      // required, non-empty array
  "authors": [ ... ],             // required, non-empty array
  "sequences": null || [ ... ],   // optional
  "book_title": "string",         // required
  "book_id": "string",            // required
  "lang": "string[2]",            // required (ISO 639-1)
  "date_time": "YYYY-MM-DDTHH:MM:SS+TZ",  // required (ISO 8601), old records may use YYYY-MM-DD
  "size": "string(int(filename size in bytes))",  // required
  "annotation": "text/stripped html string",      // optional (may be null)
  "pub_info": {                   // optional (may be null)
    "isbn": null || "string",
    "year": null || "string[4]",  // str(year)
    "publisher": null || "string",
    "publisher_id": "string"      // md5(normalized(publisher))
  },
  "deleted": 0 || 1               // optional, default: 0
}
```

### author_info

```json
{
  "name": "string",
  "id": "string"
}
```

### sequence_info

```json
{
  "name": "string",
  "id": "string"
}
```

### sequence_info_cnt (with count)

```json
{
  "name": "string",
  "id": "string",
  "cnt": int
}
```

### silly_dict

Used for quick key existence check:

```json
{"key": 1, ...}
```

Value is `1` for simple existence check, or may be an object count.

### jsonl_book (Pre-index Data)

Used as intermediate data during indexing. One structure per file line:

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
  "date_time": "YYYY-MM-DDTHH:MM:SS+TZ",  // required (ISO 8601), old records may use YYYY-MM-DD
  "size": "string(int(filename size in bytes))",  // required
  "annotation": "text/stripped html string",      // optional (may be null)
  "pub_info": {                   // optional (may be null)
    "isbn": null || "string",
    "year": null || "string[4]",  // str(year)
    "publisher": null || "string",
    "publisher_id": "string"      // md5(normalized(publisher))
  },
  "deleted": 0 || 1               // optional, default: 0
}
```

## URL Specification

### Interface-Independent URLs

All URLs are relative to `APPLICATION_ROOT`:

| URL | Description |
|-----|-------------|
| `/` | Library entry point |
| `/fb2/<zip_file>/<filename>` | Download FB2 zip |
| `/plain/<zip_file>/<filename>` | Download plain `.fb2` file. `<filename>` may be `file.fb2` or `file.fb2.html` |
| `/read/<zip_file>/<filename>` | Read in browser (XSL->HTML) |
| `/books/<sub1>/<sub2>/<book_id>.jpg` | Book cover image (JPEG or PNG). `<sub1>` - first 2 chars, `<sub2>` - next 2 chars of hex-encoded book_id. All URLs must exist (may point to same image) for different book readers. |
| `/interface.js` | JavaScript interface file |
| `/favicon.ico` | Favicon file |

**URL Parameter Notation:**
- `<id>` -- string, alphanumeric (MD5 result)
- `<sub1>` -- first 2 chars of hex-encoded id (positions 1-2)
- `<sub2>` -- next 2 chars of hex-encoded id (positions 3-4)
- `<sub>` -- other string parameter
- `<page>` -- page number, int >= 0. If == 0, may be omitted with trailing `/` (omit trailing `/` entirely)

### Interface-Dependent URLs (OPDS)

All OPDS URLs are relative to `APPLICATION_ROOT` and begin from `/opds`:

#### Root and Navigation

| URL | Description |
|-----|-------------|
| `/opds/` | Main menu with primary sections |

#### Books Lists

| URL | Description | Pagination |
|-----|-------------|------------|
| `/opds/time` | All books by date (newest first) | Yes |
| `/opds/time/<page>` | Paginated books by date | Yes |

#### Authors

| URL | Description |
|-----|-------------|
| `/opds/authorsindex/` | List of first letters for authors |
| `/opds/authorsindex/<cut>` | Authors by first 1-3 uppercase chars |
| `/opds/authorsindex/<cut1>/<cut2>` | Authors by letter+letter |
| `/opds/author/<sub1>/<sub2>/<author_id>` | Author page |
| `/opds/author/<sub1>/<sub2>/<author_id>/sequences` | Author's sequences |
| `/opds/author/<sub1>/<sub2>/<author_id>/sequenceless` | Books not in sequences |
| `/opds/author/<sub1>/<sub2>/<author_id>/alphabet` | Books sorted alphabetically |
| `/opds/author/<sub1>/<sub2>/<author_id>/time` | Books by date added |
| `/opds/author/<sub1>/<sub2>/<author_id>/<seq_id>` | Books in specific sequence |

**Author ID Format:** hex-encoded author_id (e.g., `05ef7b17...`)

#### Sequences

| URL | Description |
|-----|-------------|
| `/opds/sequencesindex/` | List of first letters for sequences |
| `/opds/sequencesindex/<cut>` | Sequences by first 1-3 uppercase chars |
| `/opds/sequencesindex/<cut1>/<cut2>` | Sequences by letter+letter |
| `/opds/sequence/<sub1>/<sub2>/<seq_id>` | Books in sequence |

**Sequence ID Format:** hex-encoded seq_id (e.g., `e1f63f09...`)

#### Genres

| URL | Description |
|-----|-------------|
| `/opds/genresindex/` | Genre groups (meta genres) |
| `/opds/genresindex/<meta_id>` | Genres in group |
| `/opds/genre/<gen_id>` | Books in genre |
| `/opds/genre/<gen_id>/<page>` | Paginated books in genre |

#### Random Elements (no pagination, no "next" link)

| URL | Description |
|-----|-------------|
| `/opds/random-books/` | Random books (up to 50) |
| `/opds/random-sequences/` | Random sequences (up to 50) |
| `/opds/rnd/genresindex/` | Random genre groups |
| `/opds/rnd/genresindex/<meta_id>` | Random genres in group |
| `/opds/rnd/genre/<gen_id>` | Random books in genre |

#### Search

| URL | Description |
|-----|-------------|
| `/opds/search?searchTerm=<query>` | Search root page |
| `/opds/search/authors?searchTerm=<query>` | Search in author names |
| `/opds/search/sequences?searchTerm=<query>` | Search in sequence names |
| `/opds/search/books?searchTerm=<query>` | Search in book titles |
| `/opds/search/booksanno?searchTerm=<query>` | Search in annotations |
| `/opds/search/booksannovector?searchTerm=<query>` | Vector search in annotations (requires `vector_search` config enabled) |

**Search Parameters:**
- `searchTerm` -- string, max 128 characters, must be URL-encoded
- `{searchTerms}` -- placeholder in OPDS link definitions, replaced with URL-encoded value
- Empty query (`searchTerm=`) is valid and returns all entries
- Example: Search for "foo bar" → `searchTerm=foo+bar` or `searchTerm=foo%20bar`

### Pagination

- Page numbers: `0, 1, 2, ...`
- Negative page numbers are invalid (returns 404)
- `page=0` may be omitted (no trailing `/`)

**Last Page Handling:**
- No `rel="next"` link on last page
- Request for `page = last_page + 1` returns empty feed with `rel="prev"` link pointing to the last page

## OPDS Response Format

### Protocol

- **HTTP Basic Authentication**: Required if `passwd` file exists in data directory
- **Caching**: Default 7 days (604800 sec), random elements 5 min (300 sec)
- **Response Format**: XML (Atom Feed with OPDS-CATALOG profile)
- **Content-Type**: `text/xml; charset=utf-8`

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

**Link Relation Meanings:**
- `start` -- link to the start of the interface (`/opds/`)
- `self` -- link to the current page
- `up` -- link to parent page or higher-level page
- `next` -- link to next page (mandatory for paginated lists)
- `prev` -- link to previous page (mandatory for non-default pages)
- `search` -- link to search with `{searchTerms}` placeholder

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
  
  <link rel="http://opds-spec.org/image"
        href="{cover_url}"
        type="image/jpeg"/>
  <link rel="x-stanza-cover-image"
        href="{cover_url}"
        type="image/jpeg"/>
  <link rel="http://opds-spec.org/thumbnail"
        href="{cover_url}"
        type="image/jpeg"/>
  <link rel="x-stanza-cover-image-thumbnail"
        href="{cover_url}"
        type="image/jpeg"/>
  
  <link rel="related"
        href="{author_url}"
        type="application/atom+xml"
        title="{author_name}"/>
  <link rel="related"
        href="{sequence_url}"
        type="application/atom+xml"
        title="{sequence_name}"/>
  
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
  <!-- Identifier -->
  <id>tag:{section}:{subtag}</id>

  <!-- Title -->
  <title>{title}</title>

  <!-- Update time -->
  <updated>YYYY-MM-DDTHH:MM:SS+TZ</updated>

  <!-- Text description -->
  <content type="text">{subtitle}</content>

  <!-- Link to section -->
  <link rel="alternate"
        href="{href}"
        type="application/atom+xml;profile=opds-catalog"/>
</entry>
```

#### Author View Entry

Author view contains a special entry with author biography/links:

**Biography entry:**

```xml
<entry>
  <updated>YYYY-MM-DDTHH:MM:SS+TZ</updated>
  <!-- Author identifier -->
  <id>tag:author:bio:{author_id}</id>

  <!-- Author title -->
  <title>About author</title>

  <link href="/opds/author/{prefix1}/{prefix2}/{author_id}/sequences" rel="http://www.feedbooks.com/opds/facet" title="By sequences" type="application/atom+xml;profile=opds-catalog"></link>
  <link href="/opds/author/{prefix1}/{prefix2}/{author_id}/sequenceless" rel="http://www.feedbooks.com/opds/facet" title="Not in sequences" type="application/atom+xml;profile=opds-catalog"></link>

  <!-- Author biography content (HTML) -->
  <content type="text/html"><p><span style="font-weight:bold">Author Name</span></p></content>
</entry>
```

**Link entry example:**
```xml
<entry>
  <updated>YYYY-MM-DDTHH:MM:SS+TZ</updated>
  <id>tag:author:{author_id}:alphabet</id>
  <title>By alphabet</title>
  <link href="/opds/author/{prefix1}/{prefix2}/{author_id}/alphabet" type="application/atom+xml;profile=opds-catalog"></link>
</entry>
```

**Note:** Cover images may be in JPEG or PNG format. Content-Type header should reflect actual format.

#### Book Cover Links

Book entries should include cover image links for different book readers. All URLs must exist (may be point to same image). Content-Type should reflect actual image format:

```xml
<link rel="http://opds-spec.org/image"
      href="..."
      type="image/jpeg"/>

<link rel="x-stanza-cover-image"
      href="..."
      type="image/jpeg"/>

<link rel="http://opds-spec.org/thumbnail"
      href="..."
      type="image/jpeg"/>

<link rel="x-stanza-cover-image-thumbnail"
      href="..."
      type="image/jpeg"/>
```

For PNG covers, use `type="image/png"` instead of `type="image/jpeg"`.

**Note:** All cover URLs must exist (may point to same image) for different book readers. The Content-Type header should reflect the actual format of the cover image.

# OPDS Interface Specification

## Overview

OPDS (Open Publication Distribution System) is a specification for distributing electronic books via RSS/Atom feeds. This service provides an OPDS interface for accessing an FB2 book library.

The root URL `/` provides the HTML interface that converts OPDS feeds into a browser-friendly HTML representation. This is the main entry point for users accessing the library through a web browser.

All OPDS interface URLs are relative to the interface base URL (typically `/opds/`), where `/` is equivalent to `/opds/`.

## Protocol

- **HTTP Basic Authentication**: All requests to `/opds/` require authentication if a `passwd` file exists in the data directory.
- **Caching**: Responses are cached by default for 7 days (604800 seconds). For random elements: 5 minutes (300 seconds).
- **Response Format**: XML (Atom Feed with OPDS-CATALOG profile)
- **Content-Type**: `text/xml; charset=utf-8`

## URL Structure

### Root Element

```
GET /opds/
```
**Response**: Main menu with primary sections.

---

### Books

#### By Date

```
GET /opds/time[/<page>]
```
**Description**: All books sorted by date (newest to oldest).
**Pagination**: `page=0, 1, 2, ...` (default: 0)

---

### Authors

```
GET /opds/authorsindex/                    # List of first letters for authors
GET /opds/authorsindex/<prefix>            # List of authors starting with letter (A, Б, В, ...)
GET /opds/authorsindex/<prefix1>/<prefix2> # List of authors by "letter+letter" (ABC, DEF, ...)
GET /opds/author/<prefix1>/<prefix2>/<id>  # Author page
GET /opds/author/<prefix1>/<prefix2>/<id>/sequences              # List of author's sequences
GET /opds/author/<prefix1>/<prefix2>/<id>/sequenceless           # Author's books not in any sequence
GET /opds/author/<prefix1>/<prefix2>/<id>/alphabet               # Author's books sorted by title alphabetically
GET /opds/author/<prefix1>/<prefix2>/<id>/time                   # Author's books sorted by date added
GET /opds/author/<prefix1>/<prefix2>/<id>/<seq_id>               # Author's books in a specific sequence
```

**Validation**:
- `<prefix>`: 2 characters (letters)
- `<prefix1>`, `<prefix2>`: 2 characters (letters)
- `<id>`, `<seq_id>`: id of author or sequence in hex format `[0-9a-f]+`

**Note**: The `<prefix1>/<prefix2>` path segments use the first 2 and next 2 characters of the ID respectively (e.g., `1a/2b` for ID `1a2b3c...`).

---

### Sequences

```
GET /opds/sequencesindex/                  # List of first letters for sequences
GET /opds/sequencesindex/<prefix>          # List of sequences starting with letter
GET /opds/sequencesindex/<prefix1>/<prefix2> # List of sequences by "letter+letter"
GET /opds/sequence/<prefix1>/<prefix2>/<id>  # Books in a sequence
```

**Note**: The `<prefix1>/<prefix2>` path segments use the first 2 and next 2 characters of the ID respectively.

---

### Genres

```
GET /opds/genresindex/                     # Genre groups
GET /opds/genresindex/<meta_id>            # List of genres in a group
GET /opds/genre/<gen_id>[/<page>]          # Books in a genre (paginated)
```

**Validation**:
- `<meta_id>`: MD5 hash in hex format
- `<gen_id>`: `[0-9a-z_]+` — text genre id, mostly from fb2 format spec

---

### Random Elements

```
GET /opds/random-books/                    # Random books
GET /opds/random-sequences/                # Random sequences
GET /opds/rnd/genresindex/                 # Random genre groups
GET /opds/rnd/genresindex/<meta_id>        # Random genres in a group
GET /opds/rnd/genre/<gen_id>               # Random books in a genre
```

---

### Search

```
GET /opds/search?searchTerm=<query>        # Search root page

GET /opds/search/authors?searchTerm=<query>        # Search in author names
GET /opds/search/sequences?searchTerm=<query>      # Search in sequence names
GET /opds/search/books?searchTerm=<query>          # Search in book titles
GET /opds/search/booksanno?searchTerm=<query>      # Search in book annotations
GET /opds/search/booksannovector?searchTerm=<query> # Vector search in annotations
```

**Validation**:
- `<query>`: max 128 characters, URL encoding supported

**Note**: Vector search is available only if enabled in configuration.

---

## Response Structure

### HTTP Headers

```
Content-Type: text/xml; charset=utf-8
Cache-Control: max-age=<seconds>, must-revalidate
```

### Atom Feed Structure

```xml
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:os="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:opds="http://opds-spec.org/2010/catalog">

  <!-- Section identifier -->
  <id>tag:...</id>

  <!-- Section title -->
  <title>...</title>

  <!-- Last update time -->
  <updated>2026-03-10T...</updated>

  <!-- Application icon -->
  <icon>/favicon.ico</icon>

  <!-- Required links -->
  <link rel="start" href="/opds/" type="application/atom+xml;profile=opds-catalog"/>
  <link rel="self" href="..."/>
  <link rel="search" href="/opds/search?searchTerm={searchTerms}" type="application/atom+xml"/>

  <!-- Optional links -->
  <link rel="up" href="..."/>
  <link rel="prev" href="..."/>
  <link rel="next" href="..."/>

  <!-- Navigation link meanings -->
  <!--
    rel="start"   - link to the start of the interface (/opds/)
    rel="self"    - link to the current page
    rel="up"      - link to the parent page
    rel="next"    - link to the next page of current list (mandatory for paginated lists)
    rel="prev"    - link to the previous page of current list (mandatory for non-default pages)
    rel="search"  - link to search with {searchTerms} placeholder
  -->

  <!-- Entries (books or links to other sections) -->
  <entry>...</entry>
</feed>
```

**Note**: search url param is exactly 'searchTerm={searchTerms}' in opds link definition

### Entry (Book)

```xml
<entry>
  <!-- Book identifier -->
  <id>tag:book:{book_id}</id>

  <!-- Book title -->
  <title>{book_title}</title>

  <!-- Date added -->
  <updated>{date_time}</updated>

  <!-- Authors -->
  <author>
    <uri>{author_uri}</uri>
    <name>{author_name}</name>
  </author>

  <!-- Action links -->
  <link rel="http://opds-spec.org/acquisition/open-access"
        href="..."
        type="application/fb2+zip"
        title="Download"/>
  <link rel="http://opds-spec.org/acquisition/open-access"
        href="..."
        type="text/html"
        title="Read online"/>

  <!-- Book cover -->
  <link rel="http://opds-spec.org/image"
        href="..."
        type="image/jpeg"/>
  <link rel="x-stanza-cover-image"
        href="..."
        type="image/jpeg"/>

  <!-- Related elements links -->
  <link rel="related"
        href="..."
        type="application/atom+xml"
        title="{author_name}"/>
  <link rel="related"
        href="..."
        type="application/atom+xml"
        title="{seq_name}"/>

  <!-- Genres -->
  <category term="{genre_id}" label="{genre_name}"/>

  <!-- Language and format -->
  <dc:language>{lang_id}</dc:language>
  <dc:format>fb2</dc:format>

  <!-- Book description -->
  <content type="text/html">
    {annotation}
  </content>
</entry>
```

**Note**: The `<dc:language>` field contains a two-letter ISO 639-1 language code (e.g., `en`, `ru`, `de`).

### Entry (Section Link)

```xml
<entry>
  <!-- Identifier -->
  <id>tag:...</id>

  <!-- Title -->
  <title>{title}</title>

  <!-- Update time -->
  <updated>{timestamp}</updated>

  <!-- Text description -->
  <content type="text">{subtitle}</content>

  <!-- Link to section -->
  <link rel="alternate"
        href="{href}"
        type="application/atom+xml;profile=opds-catalog"/>
</entry>
```

### Entry (Author View)

Author view contains a special entry with author biography/links:

Biografy entry:

```xml
<entry>
  <updated>{timestamp}</updated>
  <!-- Author identifier -->
  <id>tag:author:bio:{author_id}</id>

  <!-- Author title -->
  <title>About author</title>

  <link href="/opds/author/{prefix1}/{prefix2}/{author_id}/sequences" rel="http://www.feedbooks.com/opds/facet" title="By sequences" type="application/atom+xml;profile=opds-catalog"></link>
  <link "/opds/author/{prefix1}/{prefix2}/{author_id}/sequences" rel="http://www.feedbooks.com/opds/facet" title="Not in sequences" type="application/atom+xml;profile=opds-catalog"></link>

  <!-- Author biography content (HTML) -->
  <content type="text/html"><p><span style="font-weight:bold">Author Name</span></p></content>
</entry>
```

Link entry example:
```xml
<entry>
  <updated>{timestamp}</updated>
  <id>tag:author:{author_id}:alphabet</id>
  <title>By alphabet</title>
  <link href="/opds/author/{prefix1}/{prefix2}/{author_id}/alphabet" type="application/atom+xml;profile=opds-catalog"></link>
</entry>
```

---

### Book Cover Links

Book entries should include cover image links for different book readers. All URLs must exist:

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

Cover images are available at `/cover/<prefix1>/<prefix2>/<book_id>.jpg`

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200  | Successful response with OPDS XML |
| 401  | Authentication required (if passwd file exists) |
| 404  | Resource not found |
| 500  | Internal server error |

---

## Authentication Errors

If the `passwd` file exists in the data directory, the server returns:

```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Basic realm="Login Required"
```

---

## Pagination

Book lists are paginated:

- **URL**: `/<endpoint>/<page>` where `page = 0, 1, 2, ...`
- **Navigation**: `rel="prev"`, `rel="next"` links for page navigation

---

## Notes

1. All OPDS URLs are relative to `APPLICATION_ROOT`
2. Dates are in ISO 8601 format. For older records, the format `YYYY-MM-DD` may be used instead of `YYYY-MM-DDTHH:MM:SS+TZ`
3. Cover images are available at `/cover/<prefix1>/<prefix2>/<book_id>.jpg`
4. Direct book access (outside OPDS interface):
   - `/read/<zipfile>/<filename>.html` — HTML reading interface
   - `/fb2/<zipfile>/<filename>.zip` — Download FB2 zip
   - `/plain/<zipfile>/<filename>` — XSL-based reading

## URL Parameters

  * `<id>` -- string, alphanumeric (MD5 result in this implementation)
  * `<prefix1>` -- first two characters of `<id>`
  * `<prefix2>` -- next two characters of `<id>`
  * `<prefix>` -- other string parameter
  * `<page>` -- page number, integer >= 0. If 0, may be omitted with the trailing `/`

## XML Examples

### Example: Root Page (`/opds/`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">
	<id>tag:root</id>
	<title>Home opds directory</title>
	<updated>2025-06-20T19:07:03+00:00</updated>
	<icon>/favicon.ico</icon>
	<link href="/books/opds/search?searchTerm={searchTerms}" rel="search" type="application/atom+xml"></link>
	<link href="/books/opds/" rel="start" type="application/atom+xml;profile=opds-catalog"></link>
	<link href="/books/opds/" rel="self" type="application/atom+xml;profile=opds-catalog"></link>
	<entry>
		<updated>2025-06-20T19:07:03+00:00</updated>
		<id>tag:root:time</id>
		<title>По дате поступления</title>
		<content type="text">По дате поступления</content>
		<link href="/books/opds/time" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:07:03+00:00</updated>
		<id>tag:root:authors</id>
		<title>По авторам</title>
		<content type="text">По авторам</content>
		<link href="/books/opds/authorsindex/" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:07:03+00:00</updated>
		<id>tag:root:sequences</id>
		<title>По сериям</title>
		<content type="text">По сериям</content>
		<link href="/books/opds/sequencesindex/" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:07:03+00:00</updated>
		<id>tag:root:genre</id>
		<title>По жанрам</title>
		<content type="text">По жанрам</content>
		<link href="/books/opds/genresindex/" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:07:03+00:00</updated>
		<id>tag:root:random:books</id>
		<title>Случайные книги</title>
		<content type="text">Случайные книги</content>
		<link href="/books/opds/random-books/" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:07:03+00:00</updated>
		<id>tag:root:random:sequences</id>
		<title>Случайные серии</title>
		<content type="text">Случайные серии</content>
		<link href="/books/opds/random-sequences/" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:07:03+00:00</updated>
		<id>tag:root:random:genres</id>
		<title>Случайные книги в жанре</title>
		<content type="text">Случайные книги в жанре</content>
		<link href="/books/opds/rnd/genresindex/" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
</feed>
```

### Example: Author View

```xml
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">
	<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7</id>
	<title>Автор 'Стругацкий Аркадий Натанович'</title>
	<updated>2026-03-10T15:46:52+05:00</updated>
	<icon>/favicon.ico</icon>
	<link href="/opds/search?searchTerm={searchTerms}" rel="search" type="application/atom+xml"></link>
	<link href="/opds/" rel="start" type="application/atom+xml;profile=opds-catalog"></link>
	<link href="/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7" rel="self" type="application/atom+xml;profile=opds-catalog"></link>
	<link href="/opds/authorsindex/" rel="up" type="application/atom+xml;profile=opds-catalog"></link>
	<entry>
		<updated>2026-03-10T15:46:52+05:00</updated>
		<id>tag:author:bio:05ef7b172bdd0a32fe7eda7df2a0e1c7</id>
		<title>Об авторе</title>
		<link href="/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequences" rel="http://www.feedbooks.com/opds/facet" title="По сериям" type="application/atom+xml;profile=opds-catalog"></link>
		<link href="/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequenceless" rel="http://www.feedbooks.com/opds/facet" title="Вне серий" type="application/atom+xml;profile=opds-catalog"></link>
		<content type="text/html">&lt;p&gt;&lt;span style="font-weight:bold"&gt;Стругацкий Аркадий Натанович&lt;/span&gt;&lt;/p&gt;</content>
	</entry>
	<entry>
		<updated>2026-03-10T15:46:52+05:00</updated>
		<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7:sequences</id>
		<title>По сериям</title>
		<link href="/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequences" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2026-03-10T15:46:52+05:00</updated>
		<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7:sequenceless</id>
		<title>Вне серий</title>
		<link href="/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequenceless" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2026-03-10T15:46:52+05:00</updated>
		<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7:alphabet</id>
		<title>По алфавиту</title>
		<link href="/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/alphabet" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2026-03-10T15:46:52+05:00</updated>
		<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7:time</id>
		<title>По дате добавления</title>
		<link href="/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/time" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
</feed>
```

### Example: Book Entry

```xml
<entry>
  <updated>2025-06-20T19:19:45+00:00</updated>
  <id>tag:book:a719e2d4695b93f1062834f5c76f0cbe</id>
  <title>Сталин И.В. Цитаты</title>
  <author>
    <uri>/opds/author/b4/c3/b4c32760971eb1ed25a4f4c9eb53c33c</uri>
    <name>Кувшинов В</name>
  </author>
  <link href="/opds/author/b4/c3/b4c32760971eb1ed25a4f4c9eb53c33c" 
        rel="related" 
        title="Кувшинов В" 
        type="application/atom+xml"/>
  <link href="/fb2/f.fb2-183654-185837/185743.fb2.zip" 
        rel="http://opds-spec.org/acquisition/open-access" 
        title="Скачать" 
        type="application/fb2+zip"/>
  <link href="/read/f.fb2-183654-185837/185743.fb2" 
        rel="alternate" 
        title="Читать онлайн" 
        type="text/html"/>
  <link href="/cover/a719e2d4695b93f1062834f5c76f0cbe/jpg" 
        rel="http://opds-spec.org/image" 
        type="image/jpeg"/>
  <link href="/cover/a719e2d4695b93f1062834f5c76f0cbe/jpg" 
        rel="x-stanza-cover-image" 
        type="image/jpeg"/>
  <link href="/cover/a719e2d4695b93f1062834f5c76f0cbe/jpg" 
        rel="http://opds-spec.org/thumbnail" 
        type="image/jpeg"/>
  <link href="/cover/a719e2d4695b93f1062834f5c76f0cbe/jpg" 
        rel="x-stanza-cover-image-thumbnail" 
        type="image/jpeg"/>
  <category label="Публицистика" term="nonf_publicism"/>
  <dc:language>ru</dc:language>
  <dc:format>fb2</dc:format>
  <content type="text/html">
    <p class="book">
      <p>Annotation text...</p>
      <br/>формат: fb2<br/>
      размер: 986.0KiB<br/>
    </p>
  </content>
</entry>
```

### Example: Paginated Books List

```xml
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" 
      xmlns:dc="http://purl.org/dc/terms/" 
      xmlns:os="http://a9.com/-/spec/opensearch/1.1/" 
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>tag:genre:books:abc</id>
  <updated>2025-06-20T19:19:45+00:00</updated>
  <title>Books in genre</title>
  <icon>/favicon.ico</icon>
  <link href="/opds/search?searchTerm={searchTerms}" rel="search" type="application/atom+xml"/>
  <link href="/opds/" rel="start" type="application/atom+xml;profile=opds-catalog"/>
  <link href="/opds/genre/abc" rel="self" type="application/atom+xml;profile=opds-catalog"/>
  <link href="/opds/genre/abc" rel="up" type="application/atom+xml;profile=opds-catalog"/>
  <link href="/opds/genre/abc/2" rel="next" type="application/atom+xml;profile=opds-catalog"/>
  <entry>...</entry>
  <entry>...</entry>
</feed>
```

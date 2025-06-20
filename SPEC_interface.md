# URL tree spec

some commons in url params:

  * `<sub1>` -- `<id[:2]>` two chars part of id
  * `<sub2>` -- `<id[2:2]>` two chars part of id
  * `<sub>` -- other string param
  * `<page>` -- page number. If ==0 may be omitted with omitted `/` at end

## Interface-independed urls

all theese urls are from root of library

  * `/` -- library entry point (some info + links to interfaces)
  * `/fb2/<zip_file>/<filename>` -- download `file.fb2.zip`. `<filename>` may be `file.fb2` or `file.fb2.zip` (some bookreaders need this)
  * `/read/<zip_file>/<filename>` -- read `<filename>` in browser (process it via xslt and take html).
  * `/cover/<sub1>/<sub2>/<book_id>.jpg` -- simple static files with `/cover/default.jpg` content if file not exists

## Interface-depended urls

all urls are in interface base url (`/opds` for example and `/` is equal `/opds/`)

  * `/` -- simple list. Links to library root views
  * `/authorsindex/` -- simple list. First letters of authors names view. Links to `/authorsindex/<sub>`
  * `/authorsindex/<sub>` -- simple list
    * for current first letter `<sub>`: list of first three letters of authors names view. Links to `/authorsindex/<sub>`
    * for current first three letter `<sub>`: list of authors names view. Links to `/author/<sub1>/<sub2>/<auth_id>`
  * `/author/<sub1>/<sub2>/<auth_id>` -- author view. Links to subviews of author
  * `/author/<sub1>/<sub2>/<auth_id>/sequences` -- simple list. List of author's books sequences. Links to `/author/<sub1>/<sub2>/<auth_id>/<seq_id>`
  * `/author/<sub1>/<sub2>/<auth_id>/<seq_id>` -- books list. List of author's books in current sequence
  * `/author/<sub1>/<sub2>/<auth_id>/sequenceless` -- books list. List of author's books not in any sequence
  * `/author/<sub1>/<sub2>/<auth_id>/alphabet` -- books list. List of all author's books sorted by book title
  * `/author/<sub1>/<sub2>/<auth_id>/time` -- books list. List of all author's books sorted by time
  * `/sequencesindex/` -- simple list. First letters of sequences names view. Links to `/sequencesindex/<sub>`
  * `/sequencesindex/<sub>` -- simple list
    * for current first letter `<sub>`: list of first three letters of sequences names view. Links to`/sequencesindex/<sub>`
    * for current first three letter `<sub>`: list of sequences names view. Links to `/sequence/<sub1>/<sub2>/<seq_id>`
  * `/sequence/<sub1>/<sub2>/<seq_id>` -- books list. List of all books in sequence.
  * `/genresindex/` -- simple list. List of genres groups. Links to `/genresindex/<sub>`
  * `/genresindex/<sub>` -- simple list. List of genres. Links to `/genre/<gen_id>`
  * `/genre/<gen_id>` -- paginated books list. List of books in current genre. Next page links to `/genre/<gen_id>/<page>`
  * `/genre/<gen_id>/<page>` -- paginated books list. List of books in current genre, non-default page. Next page links to `/genre/<gen_id>/<page>`
  * `/random-books/` -- books list. List of random books from library.
  * `/random-sequences/` -- simple list. List of random sequences from library.
  * `/search` -- simple list. Links to `/search/` views with search param.
  * `/search/authors` -- simple list. List of found authors. Links to `/author/<sub1>/<sub2>/<auth_id>`
  * `/search/sequences` -- simple list. List of found sequences. Links to `/sequence/<sub1>/<sub2>/<seq_id>`
  * `/search/books` -- books list. List of found books.
  * `/search/booksanno` -- books list. List of found books.
  * `/rnd/genresindex/` -- simple list. List of genres groups. Links to `/rnd/genresindex/<sub>`
  * `/rnd/genresindex/<sub>` -- simple list. List of genres. Links to `/genre/<gen_id>`
  * `/rnd/genre/<gen_id>` -- books list. List of randob books in current genre from library.
  * `/time` -- paginated books list. List of all books in library sorted by time. Next page links to `/time/<page>`
  * `/time/<page>` -- paginated books list. List of all books in library sorted by time, non-default page. Next page links to `/time/<page>`

# OPDS views spec

## Common opds page params

mandatory wrapper:
```xml
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">
[...data...]
</feed>
```

parameters on every page before `<entry>`:

```xml
	<id>tag:$TAG</id>
```
$TAG == page tag, unique for url without `<page>` param

```xml
	<title>$TITLE</title>
```
$TITLE == title of page, text

```xml
	<updated>%UPDATED</updated>
```
$UPDATED == timestamp of page in "2025-06-20T19:07:03+00:00" form

```xml
	<icon>/favicon.ico</icon>
```
link to library icon

```xml
	<link href="/opds/search?searchTerm={searchTerms}" rel="search" type="application/atom+xml"></link>
```
link to main search page with url-param for search terms

```xml
	<link href="/opds/" rel="start" type="application/atom+xml;profile=opds-catalog"></link>
```
common navigation links. `rel` may contain:
  * `start` -- link to start of interface
  * `self` -- link to current page
  * `up` -- link to parent page
  * `next` -- link to next page of current list
  * `prev` -- link to previous page of current list

## Simple list

list of simple urls with url text and some required parameters

`<entry>` data:
  * updated -- timestamp of entry in "2025-06-20T19:07:03+00:00" form
  * tag -- tag of linked page
  * title -- link title
  * content -- link title (need for some book readers)
  * `<link href="/books/opds/time" type="application/atom+xml;profile=opds-catalog"></link>` -- link itself

opds example for `/opds/` url:
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
		<link href="/books/opds/rnd-genresindex/" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
</feed>
```

## Author's view

simple list to fixed author's urls with special entry:
```xml
	<entry>
		<updated>2025-06-20T19:12:45+00:00</updated>
		<id>tag:author:bio:05ef7b172bdd0a32fe7eda7df2a0e1c7</id>
		<title>Об авторе</title>
		<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequences" rel="http://www.feedbooks.com/opds/facet" title="Books of author by sequences" type="application/atom+xml;profile=opds-catalog"></link>
		<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequenceless" rel="http://www.feedbooks.com/opds/facet" title="Sequenceless books of author" type="application/atom+xml;profile=opds-catalog"></link>
		<content type="text/html">&lt;p&gt;&lt;span style="font-weight:bold"&gt;Стругацкий Аркадий Натанович&lt;/span&gt;&lt;/p&gt;</content>
	</entry>
```

other entries as in simple list

example in opds:
```xml
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">
	<id>tag:root:author:05ef7b172bdd0a32fe7eda7df2a0e1c7</id>
	<updated>2025-06-20T19:12:45+00:00</updated>
	<title>Автор 'Стругацкий Аркадий Натанович'</title>
	<icon>/favicon.ico</icon>
	<link href="/books/opds/search?searchTerm={searchTerms}" rel="search" type="application/atom+xml"></link>
	<link href="/books/opds/" rel="start" type="application/atom+xml;profile=opds-catalog"></link>
	<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7" rel="self" type="application/atom+xml;profile=opds-catalog"></link>
	<link href="/books/opds/authorsindex/" rel="up" type="application/atom+xml;profile=opds-catalog"></link>
	<entry>
		<updated>2025-06-20T19:12:45+00:00</updated>
		<id>tag:author:bio:05ef7b172bdd0a32fe7eda7df2a0e1c7</id>
		<title>Об авторе</title>
		<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequences" rel="http://www.feedbooks.com/opds/facet" title="Books of author by sequences" type="application/atom+xml;profile=opds-catalog"></link>
		<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequenceless" rel="http://www.feedbooks.com/opds/facet" title="Sequenceless books of author" type="application/atom+xml;profile=opds-catalog"></link>
		<content type="text/html">&lt;p&gt;&lt;span style="font-weight:bold"&gt;Стругацкий Аркадий Натанович&lt;/span&gt;&lt;/p&gt;</content>
	</entry>
	<entry>
		<updated>2025-06-20T19:12:45+00:00</updated>
		<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7:sequences</id>
		<title>По сериям</title>
		<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequences" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:12:45+00:00</updated>
		<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7:sequenceless</id>
		<title>Вне серий</title>
		<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/sequenceless" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:12:45+00:00</updated>
		<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7:alphabet</id>
		<title>По алфавиту</title>
		<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/alphabet" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
	<entry>
		<updated>2025-06-20T19:12:45+00:00</updated>
		<id>tag:author:05ef7b172bdd0a32fe7eda7df2a0e1c7:time</id>
		<title>По дате добавления</title>
		<link href="/books/opds/author/05/ef/05ef7b172bdd0a32fe7eda7df2a0e1c7/time" type="application/atom+xml;profile=opds-catalog"></link>
	</entry>
</feed>
```

## Books lists

book entry fields:
  * `updated` -- timestamp
  * `id` -- `tag:book:<book_id>`
  * `title` -- book title
  * `author` -- for every author, contain subtags:
    * `uri` -- url to author's library page
    * `name` -- author name
  * `link` -- links to:
    * rel="related" -- author's library page
    * rel="http://opds-spec.org/acquisition/open-access" -- download
    * rel="alternate" -- read online
    * rel contain "http://opds-spec.org/image" or "x-stanza-cover-image" or "http://opds-spec.org/thumbnail" or "x-stanza-cover-image-thumbnail" -- cover image, all urls must exists (for different book readers)
  * `category` -- for every genre name/id
  * `dc:language` -- 2-letter language code. 'en' for example
  * `dc:format` -- book format. Only 'fb2' now
  * `content` -- description of book

### book list

list of books with some data for every book.

example of `/opds/random-book`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/terms/" xmlns:os="http://a9.com/-/spec/opensearch/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">
	<id>tag:search:books:random:</id>
	<updated>2025-06-20T19:19:45+00:00</updated>
	<title>Случайные книги</title>
	<icon>/favicon.ico</icon>
	<link href="/books/opds/search?searchTerm={searchTerms}" rel="search" type="application/atom+xml"></link>
	<link href="/books/opds/" rel="start" type="application/atom+xml;profile=opds-catalog"></link>
	<link href="/books/opds/random-books/" rel="self" type="application/atom+xml;profile=opds-catalog"></link>
	<link href="/books/opds/" rel="up" type="application/atom+xml;profile=opds-catalog"></link>
	<entry>
		<updated>2010-03-31</updated>
		<id>tag:book:a719e2d4695b93f1062834f5c76f0cbe</id>
		<title>Сталин И.В. Цитаты</title>
		<author>
			<uri>/books/opds/author/b4/c3/b4c32760971eb1ed25a4f4c9eb53c33c</uri>
			<name>Кувшинов В</name>
		</author>
		<link href="/books/opds/author/b4/c3/b4c32760971eb1ed25a4f4c9eb53c33c" rel="related" title="Кувшинов В" type="application/atom+xml"></link>
		<link href="/books/fb2/f.fb2-183654-185837/185743.fb2.zip" rel="http://opds-spec.org/acquisition/open-access" title="Скачать" type="application/fb2+zip"></link>
		<link href="/books/read/f.fb2-183654-185837/185743.fb2" rel="alternate" title="Читать онлайн" type="text/html"></link>
		<link href="/books/cover/a719e2d4695b93f1062834f5c76f0cbe/jpg" rel="http://opds-spec.org/image" type="image/jpeg"></link>
		<link href="/books/cover/a719e2d4695b93f1062834f5c76f0cbe/jpg" rel="x-stanza-cover-image" type="image/jpeg"></link>
		<link href="/books/cover/a719e2d4695b93f1062834f5c76f0cbe/jpg" rel="http://opds-spec.org/thumbnail" type="image/jpeg"></link>
		<link href="/books/cover/a719e2d4695b93f1062834f5c76f0cbe/jpg" rel="x-stanza-cover-image-thumbnail" type="image/jpeg"></link>
		<category label="Публицистика" term="nonf_publicism"></category>
		<dc:language>ru</dc:language>
		<dc:format>fb2</dc:format>
		<content type="text/html">
        &lt;p class="book"&gt; &lt;p&gt;
 Слава Богу, сейчас литературы о Сталине много. Литературы различной как по уровню, так и по направлению. Закончилось время возвеличивания, прошло время наспровержения, время забвения тоже пронеслось. Много книг о Сталине. О нем пишут, про него рассказывают, на него ссылаются… Да вот беда: самому Сталину слово не дают. Если цитаты и включаются в текст, то очень кратко и подчас эти самые цитаты вырываются из контекста. Так хлеще получается. А ведь фраза, вырванная из общего смысла, может приобрести направленность противоположную.
&lt;/p&gt;
 &lt;/p&gt;
&lt;br/&gt;формат: fb2&lt;br/&gt;
        размер: 986.0KiB&lt;br/&gt;
        &lt;p&gt;Год публикации: 2008&lt;/p&gt;&lt;p&gt;Издательство: Кувшинов&lt;/p&gt;</content>
	</entry>
	<entry>
		<updated>2010-11-15</updated>
		<id>tag:book:171526116ab92c3f68f9c7d0ca1da933</id>
		<title>Магьоснически гамбит</title>
		<author>
			<uri>/books/opds/author/19/cf/19cfacbc7dd5976c0495857f3a3536ed</uri>
			<name>Эддингс Дэвид</name>
		</author>
		<link href="/books/opds/author/19/cf/19cfacbc7dd5976c0495857f3a3536ed" rel="related" title="Эддингс Дэвид" type="application/atom+xml"></link>
		<link href="/books/opds/sequence/e1/f6/e1f63f0997da77cfbcbaee19c2079661" rel="related" title="Серия 'Белгариада'" type="application/atom+xml"></link>
		<link href="/books/fb2/f.fb2-203581-214697/207059.fb2.zip" rel="http://opds-spec.org/acquisition/open-access" title="Скачать" type="application/fb2+zip"></link>
		<link href="/books/read/f.fb2-203581-214697/207059.fb2" rel="alternate" title="Читать онлайн" type="text/html"></link>
		<link href="/books/cover/171526116ab92c3f68f9c7d0ca1da933/jpg" rel="http://opds-spec.org/image" type="image/jpeg"></link>
		<link href="/books/cover/171526116ab92c3f68f9c7d0ca1da933/jpg" rel="x-stanza-cover-image" type="image/jpeg"></link>
		<link href="/books/cover/171526116ab92c3f68f9c7d0ca1da933/jpg" rel="http://opds-spec.org/thumbnail" type="image/jpeg"></link>
		<link href="/books/cover/171526116ab92c3f68f9c7d0ca1da933/jpg" rel="x-stanza-cover-image-thumbnail" type="image/jpeg"></link>
		<category label="Фэнтези" term="sf_fantasy"></category>
		<dc:language>bg</dc:language>
		<dc:format>fb2</dc:format>
		<content type="text/html">
        &lt;p class="book"&gt; &lt;p&gt;
 Сенедра, престолонаследницата на империята Толнедра, беше объркана. Всички знаеха, че приказките за Кълбото, което уж закриляло Западните кралства от злия бог Торак, са просто глупави легенди. Ала ето че тя се оказа принудена да се присъедини към сериозна и много опасна експедиция, целяща възвръщането на откраднатото Кълбо. Никой не вярваше във вълшебства.
&lt;/p&gt;
&lt;p&gt;
 И все пак лелята и дядото на Гарион, изглежда, бяха прословутите вълшебници Поулгара и Белгарат, които би трябвало да са на възраст няколко хиляди години. Дори младият Гарион се научаваше да извършва разни неща, които биха могли да се наричат единствено вълшебства.
&lt;/p&gt;
 &lt;/p&gt;
&lt;br/&gt;формат: fb2&lt;br/&gt;
        размер: 1.6MiB&lt;br/&gt;
        </content>
	</entry>
</feed>
```

### Paginated books list

as book list, but with additional links:
  * to next page -- mandatory on every page
  * to previous page -- mandatory only for non-default page

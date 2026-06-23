# План реализации OPDS-сервера на Go

## Цель
Создать Go-версию OPDS-сервера (`opds_go`), полностью совместимую с существующим `opds.py`:
- Тот же файл конфигурации `config.ini`
- Те же HTTP-маршруты и тексты ответов
- Те же шаблоны (через конвертер Jinja2 → Go templates)
- Та же схема БД PostgreSQL
- Те же файлы данных в `pages_path`

**Контекст:** Приложение `fb2_srv` состоит из двух частей:
- `datachew.py` — подготовка данных (останется на Python)
- `opds.py` → `opds_go` — обслуживание OPDS-клиентов (перевод на Go)

## Технология

| Python (существующее) | Go (новая версия) |
|------------------------|-------------------|
| Flask routing | `chi` router |
| SQLAlchemy ORM | `database/sql` + raw SQL |
| xmltodict.unparse | Ручная XML-сборка |
| configparser | `gopkg.in/ini.v1` |
| lxml.etree XSLT | `sxml` (xslt1) |
| openai SDK | REST HTTP-клиент |
| BeautifulSoup | Ручная обработка |

## Структура проекта
```
app_go/
  go.mod                    # модуль
  main.go                   # точка входа
  config/
    config.go               # парсинг config.ini, Config struct, URL, LANG константы
  model/
    book.go                 # Book, Author, Sequence, Genre JSON-структуры
    opds.go                 # OPDS Feed, Entry, Link XML-структуры  
    pubinfo.go              # PublicationInfo
  util/
    strings.go              # normalize, make_id (MD5), id2path, unicode_upper
    validate.go             # validate_id, validate_zip, validate_fb2, validate_genre, validate_search, validate_prefix
    auth.go                 # is_auth (проверка passwd файла)
    xml.go                  # XMLEscape, html_refine
    sort.go                 # custom_alphabet_cmp (русская сортировка)
    filesize.go             # sizeof_fmt
    http.go                 # createOPDSResponse (XML + заголовки)
  db/
    db.go                   # инициализация, подключение, DB struct
    books.go                # запросы для книг (list, search, random)
    authors.go              # запросы для авторов
    sequences.go            # запросы для серий
    genres.go               # запросы для жанров
    vector.go               # векторный поиск
  handler/
    opds.go                 # все OPDS-маршруты
    static.go               # статические маршруты (cover, dl, read, plain, webroot, js)
    response.go             # сборка OPDS-ответов (header, main, simple_list, author_page, book_list, search_main)
    book_entry.go           # makeBookEntry, getSeqLink, getBookLink, pubinfoAnno
  templates/                # конвертированные из app/templates/ (Jinja2 → Go templates)
    index.html
    interface.js
  static -> ../../app/static # СИМЛИНК на оригинальные статические файлы
```

**Примечание:** `app_go/static` — симлинк на `app/static/` чтобы не дублировать файлы (favicon.ico, moon.svg, sun.svg, default-cover.jpg).

---

## Фаза 1: Базовая инфраструктура

### 1.1 Инициализация проекта
- [x] 1.1.1 `go mod init fb2srv_go`
- [x] 1.1.2 Добавить зависимости: chi, lib/pq, gopkg.in/ini.v1, sxml, openai
- [x] 1.1.3 Создать структуру директорий

### 1.2 Конфигурация
- [x] 1.2.1 `config/config.go` — Config struct со всеми полями из Python CONFIG
- [x] 1.2.2 Парсинг config.ini (секции common + app_env)
- [x] 1.2.3 Mapping vars из config.ini в Go-поля (как VARS в Python)
- [x] 1.2.4 Значения по умолчанию (как CONFIG default в Python)
- [x] 1.2.5 URL константы (URL map → struct)
- [x] 1.2.6 LANG константы (все строки из Python LANG)

### 1.3 Утилиты строк
- [x] 1.3.1 `util/strings.go` — unicode_upper (NFKD normalize + REPLACEMENT_MAP)
- [x] 1.3.2 `util/strings.go` — str_normalize (strip, spaces, quotes, punctuation)
- [x] 1.3.3 `util/strings.go` — make_id (MD5 hex)
- [x] 1.3.4 `util/strings.go` — id2path, id2pathonly
- [x] 1.3.5 `util/strings.go` — url_str (URL encode)
- [x] 1.3.6 `util/strings.go` — strip_quotes

### 1.4 Валидация
- [x] 1.4.1 `util/validate.go` — validate_id (regex: [0-9a-f]+)
- [x] 1.4.2 `util/validate.go` — validate_zip (regex)
- [x] 1.4.3 `util/validate.go` — validate_fb2 (regex)
- [x] 1.4.4 `util/validate.go` — validate_genre (regex)
- [x] 1.4.5 `util/validate.go` — validate_search (unurl, replace ;, max 128)
- [x] 1.4.6 `util/validate.go` — validate_prefix (safe_path, 1-10 chars)
- [x] 1.4.7 `util/validate.go` — safe_path (os.RelPath)

### 1.5 Сортировка
- [x] 1.5.1 `util/sort.go` — alphabet_1, alphabet_2 (русский + латинский)
- [x] 1.5.2 `util/sort.go` — customCharCmp
- [x] 1.5.3 `util/sort.go` — customAlphabetCmp (string compare)
- [x] 1.5.4 `util/sort.go` — customAlphabetBookTitleCmp
- [x] 1.5.5 `util/sort.go` — customAlphabetNameCmp

### 1.6 Мелкие утилиты
- [x] 1.6.1 `util/filesize.go` — sizeof_fmt (123456 -> 123KiB)
- [x] 1.6.2 `util/auth.go` — is_auth (parse passwd file)
- [x] 1.6.3 `util/xml.go` — XMLEscape
- [x] 1.6.4 `util/xml.go` — html_refine (упрощённый вариант)

---

## Фаза 2: Модели и БД

### 2.1 Модели данных
- [x] 2.1.1 `model/book.go` — Book struct (zipfile, filename, genres[], authors[], sequences[], book_id, lang, date, size, annotation, pub_info, date_time, deleted)
- [x] 2.1.2 `model/book.go` — Author struct (name, id, info)
- [x] 2.1.3 `model/book.go` — SequenceRef struct (name, id, num)
- [x] 2.1.4 `model/book.go` — PubInfo struct (isbn, year, publisher, publisher_id)
- [x] 2.1.5 `model/opds.go` — OPDSFeed struct (xml namespaces, id, title, updated, icon, links[], entries[])
- [x] 2.1.6 `model/opds.go` — OPDSEntry struct (id, title, updated, author[], link[], category[], content, dc:language, dc:format)
- [x] 2.1.7 `model/opds.go` — OPDSLink struct (href, rel, type, title)
- [x] 2.1.8 `model/opds.go` — OPDSAuthor struct (uri, name)
- [x] 2.1.9 `model/opds.go` — OPDSCategory struct (term, label)

### 2.2 Подключение к БД
- [x] 2.2.1 `db/db.go` — DB struct (sql.DB)
- [x] 2.2.2 `db/db.go` — NewDB (подключение postgres, connection pool)
- [x] 2.2.3 `db/db.go` — CloseDB

### 2.3 Запросы для книг
- [x] 2.3.1 `db/books.go` — GetBooksByDate (ORDER BY date DESC, LIMIT/OFFSET)
- [x] 2.3.2 `db/books.go` — GetBooksCount (COUNT для пагинации time)
- [x] 2.3.3 `db/books.go` — GetRandomBooks (ORDER BY random())
- [x] 2.3.4 `db/books.go` — GetRandomBooksByGenre (WHERE genres ARRAY OVERLAP)
- [x] 2.3.5 `db/books.go` — SearchBooksByTitle (ILIKE с trgm)
- [x] 2.3.6 `db/books.go` — SearchBooksByAnnotation (ILIKE с trgm)
- [x] 2.3.7 `db/books.go` — GetBooksWithDetails (JOIN book_descr, gather authors/sequences)

### 2.4 Запросы для авторов
- [x] 2.4.1 `db/authors.go` — GetAuthorsByID (batch)
- [x] 2.4.2 `db/authors.go` — SearchAuthors (ILIKE)
- [x] 2.4.3 `db/authors.go` — GetRandomAuthors (ORDER BY random())

### 2.5 Запросы для серий
- [x] 2.5.1 `db/sequences.go` — GetSequencesByID (batch)
- [x] 2.5.2 `db/sequences.go` — SearchSequences (ILIKE)

### 2.6 Запросы для жанров
- [x] 2.6.1 `db/genres.go` — GetGenresMeta (all meta genres)
- [x] 2.6.2 `db/genres.go` — GetGenresByMetaID

### 2.7 Векторный поиск
- [x] 2.7.1 `db/vector.go` — GetNearestIDs (l2_distance ORDER BY)
- [x] 2.7.2 `util/embedding.go` — GetVector (OpenAI-compatible REST call)

---

## Фаза 3: Генерация OPDS-ответов

### 3.1 Базовые функции
- [ ] 3.1.1 `handler/response.go` — getDTISO (current time ISO format)
- [ ] 3.1.2 `handler/response.go` — opdsHeader (feed с links: search, start, self, up, prev, next)
- [ ] 3.1.3 `handler/http.go` — createOPDSResponse (XML marshal + Cache-Control header)

### 3.2 Сборка записей
- [ ] 3.2.1 `handler/book_entry.go` — makeBookEntry (полная запись книги с links, categories, content)
- [ ] 3.2.2 `handler/book_entry.go` — getBookLink (dl/read/plain links)
- [ ] 3.2.3 `handler/book_entry.go` — getSeqLink (sequence related link)
- [ ] 3.2.4 `handler/book_entry.go` — pubinfoAnno (ISBN/год/издательство HTML)
- [ ] 3.2.5 `handler/book_entry.go` — coverLinks (4 OPDS variants)

### 3.3 Главные страницы
- [ ] 3.3.1 `handler/response.go` — opdsMain (root page: time, authors, sequences, genres, random)
- [ ] 3.3.2 `handler/response.go` — opdsSearchMain (search root with links to sub-searches)

### 3.4 Простые списки (из JSON-файлов)
- [ ] 3.4.1 `handler/response.go` — opdsSimpleList (читает index.json, создаёт entries)
- [ ] 3.4.2 `handler/response.go` — поддержка layout: subs, key_value, name_id_list

### 3.5 Страница автора
- [ ] 3.5.1 `handler/response.go` — opdsAuthorPage (bio entry, navigation links)

### 3.6 Списки книг (из JSON-файлов)
- [ ] 3.6.1 `handler/response.go` — opdsBookList (layout: author_seq, author_alpha, author_time, author_nonseq, sequence, paginated)
- [ ] 3.6.2 Сортировка по layout-у

### 3.7 Списки из БД
- [ ] 3.7.1 `handler/response.go` — opdsBooksDB (запросы к БД для time, random, search)
- [ ] 3.7.2 `handler/response.go` — opdsSimpleListDB (авторы/серии из БД)

### 3.8 XML-сериализация
- [ ] 3.8.1 Настроить XML-теги во всех model structs
- [ ] 3.8.2 Рекурсивная XML-сериализация с pretty-print
- [ ] 3.8.3 Правильные namespace в output

---

## Фаза 4: OPDS-маршруты (HTTP Handler)

### 4.1 Роутер и middleware
- [ ] 4.1.1 Инициализация chi router
- [ ] 4.1.2 Middleware: auth (проверка passwd)
- [ ] 4.1.3 Middleware: logging
- [ ] 4.1.4 ApplicationRoot prefix (strip/mount)

### 4.2 Root и навигация
- [ ] 4.2.1 GET `/opds/` → opdsMain
- [ ] 4.2.2 GET `/opds/time` → opdsTimeBooks (page=0)
- [ ] 4.2.3 GET `/opds/time/{page}` → opdsTimeBooks

### 4.3 Авторы
- [ ] 4.3.1 GET `/opds/authorsindex/` → authRoot
- [ ] 4.3.2 GET `/opds/authorsindex/{sub}` → authSub
- [ ] 4.3.3 GET `/opds/authorsindex/{sub1}/{sub2}` → authSub2
- [ ] 4.3.4 GET `/opds/author/{sub1}/{sub2}/{id}` → authorMain
- [ ] 4.3.5 GET `/opds/author/{sub1}/{sub2}/{id}/sequences` → authorSeqs
- [ ] 4.3.6 GET `/opds/author/{sub1}/{sub2}/{id}/sequenceless` → authorNonSeq
- [ ] 4.3.7 GET `/opds/author/{sub1}/{sub2}/{id}/alphabet` → authorAlphabet
- [ ] 4.3.8 GET `/opds/author/{sub1}/{sub2}/{id}/time` → authorTime
- [ ] 4.3.9 GET `/opds/author/{sub1}/{sub2}/{id}/{seq_id}` → authorSeqBooks

### 4.4 Серии
- [ ] 4.4.1 GET `/opds/sequencesindex/` → seqRoot
- [ ] 4.4.2 GET `/opds/sequencesindex/{sub}` → seqSub
- [ ] 4.4.3 GET `/opds/sequencesindex/{sub1}/{sub2}` → seqSub2
- [ ] 4.4.4 GET `/opds/sequence/{sub1}/{sub2}/{id}` → sequenceBooks

### 4.5 Жанры
- [ ] 4.5.1 GET `/opds/genresindex/` → genresRoot
- [ ] 4.5.2 GET `/opds/genresindex/{meta_id}` → genresList
- [ ] 4.5.3 GET `/opds/genre/{gen_id}` → genreBooks (page=0)
- [ ] 4.5.4 GET `/opds/genre/{gen_id}/{page}` → genreBooks

### 4.6 Случайные элементы
- [ ] 4.6.1 GET `/opds/random-books/` → rndBooks
- [ ] 4.6.2 GET `/opds/random-sequences/` → rndSeqs
- [ ] 4.6.3 GET `/opds/rnd/genresindex/` → rndGenresRoot
- [ ] 4.6.4 GET `/opds/rnd/genresindex/{meta_id}` → rndGenresList
- [ ] 4.6.5 GET `/opds/rnd/genre/{gen_id}` → rndBooksByGenre

### 4.7 Поиск
- [ ] 4.7.1 GET `/opds/search?searchTerm=` → searchMain
- [ ] 4.7.2 GET `/opds/search/authors?searchTerm=` → searchAuthors
- [ ] 4.7.3 GET `/opds/search/sequences?searchTerm=` → searchSequences
- [ ] 4.7.4 GET `/opds/search/books?searchTerm=` → searchBooks
- [ ] 4.7.5 GET `/opds/search/booksanno?searchTerm=` → searchBooksAnno
- [ ] 4.7.6 GET `/opds/search/booksannovector?searchTerm=` → searchBooksAnnoVector

---

## Фаза 5: Статические маршруты

### 5.1 Обложки
- [ ] 5.1.1 GET `/books/{sub1}/{sub2}/{book_id}.jpg` → coverHandler
- [ ] 5.1.2 Fallback на default cover

### 5.2 Загрузка книг
- [ ] 5.2.1 GET `/fb2/{zip_file}/{filename}` → downloadHandler (ZIP с FB2)
- [ ] 5.2.2 Формирование ZIP on-the-fly

### 5.3 Чтение
- [ ] 5.3.1 GET `/read/{zip_file}/{filename}` → readHandler (XSLT→HTML)
- [ ] 5.3.2 GET `/read/{zip_file}/{filename}.html` → readHandler
- [ ] 5.3.3 XSLT-трансформация FB2→HTML

### 5.4 Plain FB2
- [ ] 5.4.1 GET `/plain/{zip_file}/{filename}` → plainHandler (FB2 с XSL-line)

### 5.5 Web-интерфейс
- [ ] 5.5.1 GET `/` → webroot (render index.html template)
- [ ] 5.5.2 GET `/interface.js` → interfaceJS (render interface.js template)
- [ ] 5.5.3 GET `/favicon.ico` → faviconHandler
- [ ] 5.5.4 GET `/moon.svg` → moonIconHandler
- [ ] 5.5.5 GET `/sun.svg` → sunIconHandler
- [ ] 5.5.6 GET `/fb2.xsl` → xslHandler (сервер xslt файла)

---

## Фаза 6: Запуск и деплой

### 6.1 Main
- [ ] 6.1.1 `main.go` — загрузка конфига
- [ ] 6.1.2 `main.go` — загрузка жанров (genres.list, genres_meta.list)
- [ ] 6.1.3 `main.go` — инициализация БД
- [ ] 6.1.4 `main.go` — регистрация всех роутов
- [ ] 6.1.5 `main.go` — запуск HTTP-сервера (listen_host:listen_port)
- [ ] 6.1.6 Graceful shutdown (signal handling)

### 6.2 Сборка и инфраструктура
- [x] 6.2.1 Создание симлинка `app_go/static -> ../../app/static`
- [x] 6.2.2 Скрипт-конвертер `convert_templates.py` (Jinja2 → Go templates)
- [x] 6.2.3 `Makefile` — команды: `setup` (симлинки), `tplgo` (конвертация), `appgo` (сборка, зависит от tplgo), `clean` (очистка)
- [x] 6.2.4 Бинарник: `opds_go` (аналог `opds.py`)
- [ ] 6.2.5 Скрипт тестирования `test_opds.sh` (ручной запуск)

### 6.3 Тестирование
- [ ] 6.3.1 Запустить `opds.py` и `opds_go` параллельно
- [ ] 6.3.2 Прогнать все OPDS-маршруты, сравнить XML-ответы
- [ ] 6.3.3 Проверить пагинацию
- [ ] 6.3.4 Проверить поиск
- [ ] 6.3.5 Проверить авторизацию
- [ ] 6.3.6 Проверить загрузку/чтение книг
- [ ] 6.3.7 Проверить обложки
- [ ] 6.3.8 Нагрузочное тестирование

---

## Порядок выполнения

Рекомендуемый порядок реализации фаз:
1. **Фаза 1** — полностью (без утилит не обойтись)
2. **Фаза 2** — полностью (нужна БД для тестирования)
3. **Фаза 3** — полностью (сборка ответов)
4. **Фаза 4** — по группам маршрутов (root → авторы → серии → жанры → random → поиск)
5. **Фаза 5** — полностью
6. **Фаза 6** — завершение

## Заметки

- JSON-файлы в `pages_path` читаются как есть (те же пути, тот же формат)
- Для XSLT используем библиотеку `github.com/xmlverv/xslt` или `sxml`
- Для vector search — прямой HTTP-запрос к OpenAI-compatible API
- Авторизация: проверка файла `{zips_path}/passwd` на каждый запрос (как в Python)
- Кэширование: заголовки Cache-Control (никакого server-side кэша)
- **Бинарник:** `opds_go` (не `fb2srv_go`) — прямая замена `opds.py`
- **Шаблоны:** конвертер `convert_templates.py` преобразует Jinja2 из `app/templates/` в Go templates в `app_go/templates/`
- **Статические файлы:** симлинк `app_go/static -> ../../app/static` (не дублируем файлы)
- **Makefile:** `make setup` (симлинки), `make tplgo` (конвертация), `make appgo` (сборка, зависит от tplgo), `make clean` (очистка)
- **Совместимость с БД:** Go обращается к тем же таблицам PostgreSQL через raw SQL (database/sql + lib/pq), таблицы создаются Python-скриптом datachew.py

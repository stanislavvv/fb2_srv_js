// Package config provides configuration loading and constants.
package config

import (
	"os"
	"strings"

	"gopkg.in/ini.v1"
)

// VARS maps config.ini keys to internal Go field names.
var VARS = map[string]string{
	"debug":                "DEBUG",
	"app_root":             "APPLICATION_ROOT",
	"hide_deleted":         "HIDE_DELETED",
	"page_size":            "PAGE_SIZE",
	"pages_path":           "PAGES",
	"pg_base":              "PG_BASE",
	"pg_host":              "PG_HOST",
	"pg_pass":              "PG_PASS",
	"pg_user":              "PG_USER",
	"listen_port":          "LISTEN_PORT",
	"listen_host":          "LISTEN_HOST",
	"pic_width":            "PIC_WIDTH",
	"search_result_limit":  "MAX_SEARCH_RES",
	"web_title":            "TITLE",
	"inpx_file":            "INPX",
	"zips_path":            "ZIPS",
	"max_pass_length":      "MAX_PASS_LENGTH",
	"max_pass_length_gen":  "MAX_PASS_LENGTH_GEN",
	"books_pass_size_hint": "PASS_SIZE_HINT",
	"default_cover_image":  "DEFAULT_COVER",
	"default_cover_source": "DEFAULT_COVER_SRC",
	"default_cache_seconds": "CACHE_TIME",
	"static_file_cache_seconds": "CACHE_TIME_ST",
	"random_cache_seconds": "CACHE_TIME_RND",
	"xslt_file":            "FB2_XSLT",
	"app_ico":              "APP_ICO",
	"vector_search":        "VECTOR_SEARCH",
	"openai_url":           "OPENAI_URL",
	"openai_model":         "OPENAI_MODEL",
	"openai_key":           "OPENAI_KEY",
}

// Default values for configuration fields.
var defaults = map[string]string{
	"LISTEN_HOST":          "0.0.0.0",
	"LISTEN_PORT":          "8000",
	"APPLICATION_ROOT":     "",
	"AUTHOR_PLACEHOLDER":   "Автор Неизвестен",
	"MAX_PASS_LENGTH":      "4000",
	"MAX_PASS_LENGTH_GEN":  "5",
	"PASS_SIZE_HINT":       "10485760",
	"DEFAULT_COVER":        "/books/default.jpg",
	"DEFAULT_COVER_SRC":    "./app/static/default-cover.jpg",
	"CACHE_TIME":           "604800",
	"CACHE_TIME_ST":        "2592000",
	"CACHE_TIME_RND":       "300",
	"FB2_XSLT":             "fb2_to_html.xsl",
	"APP_ICO":              "/favicon.ico",
	"TITLE":                "Home OPDS directory",
	"HIDE_DELETED":         "no",
	"VECTOR_SEARCH":        "no",
	"OPENAI_URL":           "http://localhost:18000/v1",
	"OPENAI_MODEL":         "text-embedding-3-small",
	"OPENAI_KEY":           "-",
	"DEBUG":                "no",
	"PG_HOST":              "127.0.0.1",
	"PG_BASE":              "books",
	"PG_USER":              "books",
	"PG_PASS":              "",
	"PAGES":                "",
	"ZIPS":                 "",
	"PAGE_SIZE":            "50",
	"MAX_SEARCH_RES":       "500",
	"PIC_WIDTH":            "200",
	"INPX":                 "flibusta_fb2_local.inpx",
}

// Config holds all application configuration values.
type Config struct {
	DEBUG              string
	PG_HOST            string
	PG_BASE            string
	PG_USER            string
	PG_PASS            string
	PAGES              string
	ZIPS               string
	LISTEN_HOST        string
	LISTEN_PORT        string
	PIC_WIDTH          string
	PAGE_SIZE          string
	MAX_SEARCH_RES     string
	TITLE              string
	APPLICATION_ROOT   string
	HIDE_DELETED       string
	VECTOR_SEARCH      string
	OPENAI_URL         string
	OPENAI_MODEL       string
	OPENAI_KEY         string
	MAX_PASS_LENGTH    string
	MAX_PASS_LENGTH_GEN string
	PASS_SIZE_HINT     string
	DEFAULT_COVER      string
	DEFAULT_COVER_SRC  string
	CACHE_TIME         string
	CACHE_TIME_ST      string
	CACHE_TIME_RND     string
	FB2_XSLT           string
	APP_ICO            string
	INPX               string
	AUTHOR_PLACEHOLDER string
}

// Get returns the config value for the given key.
func (c *Config) Get(key string) string {
	switch key {
	case "DEBUG":
		return c.DEBUG
	case "PG_HOST":
		return c.PG_HOST
	case "PG_BASE":
		return c.PG_BASE
	case "PG_USER":
		return c.PG_USER
	case "PG_PASS":
		return c.PG_PASS
	case "PAGES":
		return c.PAGES
	case "ZIPS":
		return c.ZIPS
	case "LISTEN_HOST":
		return c.LISTEN_HOST
	case "LISTEN_PORT":
		return c.LISTEN_PORT
	case "PIC_WIDTH":
		return c.PIC_WIDTH
	case "PAGE_SIZE":
		return c.PAGE_SIZE
	case "MAX_SEARCH_RES":
		return c.MAX_SEARCH_RES
	case "TITLE":
		return c.TITLE
	case "APPLICATION_ROOT":
		return c.APPLICATION_ROOT
	case "HIDE_DELETED":
		return c.HIDE_DELETED
	case "VECTOR_SEARCH":
		return c.VECTOR_SEARCH
	case "OPENAI_URL":
		return c.OPENAI_URL
	case "OPENAI_MODEL":
		return c.OPENAI_MODEL
	case "OPENAI_KEY":
		return c.OPENAI_KEY
	case "MAX_PASS_LENGTH":
		return c.MAX_PASS_LENGTH
	case "MAX_PASS_LENGTH_GEN":
		return c.MAX_PASS_LENGTH_GEN
	case "PASS_SIZE_HINT":
		return c.PASS_SIZE_HINT
	case "DEFAULT_COVER":
		return c.DEFAULT_COVER
	case "DEFAULT_COVER_SRC":
		return c.DEFAULT_COVER_SRC
	case "CACHE_TIME":
		return c.CACHE_TIME
	case "CACHE_TIME_ST":
		return c.CACHE_TIME_ST
	case "CACHE_TIME_RND":
		return c.CACHE_TIME_RND
	case "FB2_XSLT":
		return c.FB2_XSLT
	case "APP_ICO":
		return c.APP_ICO
	case "INPX":
		return c.INPX
	case "AUTHOR_PLACEHOLDER":
		return c.AUTHOR_PLACEHOLDER
	}
	return ""
}

// Set sets a config value for the given key.
func (c *Config) Set(key, value string) {
	switch key {
	case "DEBUG":
		c.DEBUG = value
	case "PG_HOST":
		c.PG_HOST = value
	case "PG_BASE":
		c.PG_BASE = value
	case "PG_USER":
		c.PG_USER = value
	case "PG_PASS":
		c.PG_PASS = value
	case "PAGES":
		c.PAGES = value
	case "ZIPS":
		c.ZIPS = value
	case "LISTEN_HOST":
		c.LISTEN_HOST = value
	case "LISTEN_PORT":
		c.LISTEN_PORT = value
	case "PIC_WIDTH":
		c.PIC_WIDTH = value
	case "PAGE_SIZE":
		c.PAGE_SIZE = value
	case "MAX_SEARCH_RES":
		c.MAX_SEARCH_RES = value
	case "TITLE":
		c.TITLE = value
	case "APPLICATION_ROOT":
		c.APPLICATION_ROOT = value
	case "HIDE_DELETED":
		c.HIDE_DELETED = value
	case "VECTOR_SEARCH":
		c.VECTOR_SEARCH = value
	case "OPENAI_URL":
		c.OPENAI_URL = value
	case "OPENAI_MODEL":
		c.OPENAI_MODEL = value
	case "OPENAI_KEY":
		c.OPENAI_KEY = value
	case "MAX_PASS_LENGTH":
		c.MAX_PASS_LENGTH = value
	case "MAX_PASS_LENGTH_GEN":
		c.MAX_PASS_LENGTH_GEN = value
	case "PASS_SIZE_HINT":
		c.PASS_SIZE_HINT = value
	case "DEFAULT_COVER":
		c.DEFAULT_COVER = value
	case "DEFAULT_COVER_SRC":
		c.DEFAULT_COVER_SRC = value
	case "CACHE_TIME":
		c.CACHE_TIME = value
	case "CACHE_TIME_ST":
		c.CACHE_TIME_ST = value
	case "CACHE_TIME_RND":
		c.CACHE_TIME_RND = value
	case "FB2_XSLT":
		c.FB2_XSLT = value
	case "APP_ICO":
		c.APP_ICO = value
	case "INPX":
		c.INPX = value
	case "AUTHOR_PLACEHOLDER":
		c.AUTHOR_PLACEHOLDER = value
	}
}

// Keys returns all available config keys.
func (c *Config) Keys() []string {
	return []string{
		"DEBUG", "PG_HOST", "PG_BASE", "PG_USER", "PG_PASS",
		"PAGES", "ZIPS", "LISTEN_HOST", "LISTEN_PORT", "PIC_WIDTH",
		"PAGE_SIZE", "MAX_SEARCH_RES", "TITLE", "APPLICATION_ROOT", "HIDE_DELETED",
		"VECTOR_SEARCH", "OPENAI_URL", "OPENAI_MODEL", "OPENAI_KEY",
		"MAX_PASS_LENGTH", "MAX_PASS_LENGTH_GEN", "PASS_SIZE_HINT",
		"DEFAULT_COVER", "DEFAULT_COVER_SRC", "CACHE_TIME", "CACHE_TIME_ST",
		"CACHE_TIME_RND", "FB2_XSLT", "APP_ICO", "INPX", "AUTHOR_PLACEHOLDER",
	}
}

// LoadConfig reads config.ini and populates the Config struct.
func LoadConfig(path string) *Config {
	c := &Config{}

	// Apply defaults first
	for k, v := range defaults {
		c.Set(k, v)
	}

	f, err := ini.Load(path)
	if err != nil {
		// If file doesn't exist, use defaults only
		return c
	}

	// Process [common] section
	if common, err := f.GetSection("common"); err == nil {
		for _, key := range common.Keys() {
			internalKey := VARS[key.Name()]
			if internalKey != "" {
				c.Set(internalKey, key.Value())
			}
		}
	}

	// Process environment-specific section
	appEnv := os.Getenv("APP_ENV")
	if appEnv == "" {
		appEnv = "development"
	}
	if section, err := f.GetSection(appEnv); err == nil {
		for _, key := range section.Keys() {
			internalKey := VARS[key.Name()]
			if internalKey != "" {
				c.Set(internalKey, key.Value())
			}
		}
	}

	return c
}

// URL holds URL path constants for OPDS routes.
type URL struct {
	Start              string
	Author             string
	AuthIdx            string
	Seq                string
	SeqIdx             string
	Genre              string
	GenIdx             string
	Search             string
	SrchAuth           string
	SrchSeq            string
	SrchBook           string
	SrchBookAnno       string
	SrchBookAnnoVector string
	RndBook            string
	RndSeq             string
	RndGen             string
	RndGenIdx          string
	Time               string
	Read               string
	Dl                 string
	Plain              string
	Cover              string
	XslRead            string
}

// GetURLs returns the URL constants map.
func GetURLs() *URL {
	return &URL{
		Start:              "/opds/",
		Author:             "/opds/author/",
		AuthIdx:            "/opds/authorsindex/",
		Seq:                "/opds/sequence/",
		SeqIdx:             "/opds/sequencesindex/",
		Genre:              "/opds/genre/",
		GenIdx:             "/opds/genresindex/",
		Search:             "/opds/search",
		SrchAuth:           "/opds/search/authors",
		SrchSeq:            "/opds/search/sequences",
		SrchBook:           "/opds/search/books",
		SrchBookAnno:       "/opds/search/booksanno",
		SrchBookAnnoVector: "/opds/search/booksannovector",
		RndBook:            "/opds/random-books/",
		RndSeq:             "/opds/random-sequences/",
		RndGen:             "/opds/rnd/genre/",
		RndGenIdx:          "/opds/rnd/genresindex/",
		Time:               "/opds/time",
		Read:               "/read/",
		Dl:                 "/fb2/",
		Plain:              "/plain/",
		Cover:              "/books/",
		XslRead:            "/fb2.xsl",
	}
}

// LANG holds all interface strings.
type LANG struct {
	TitleTime          string
	TitleAuthors       string
	TitleSequences     string
	TitleGenres        string
	TitleRndBooks      string
	TitleRndSeqs       string
	TitleRndGenre      string
	BookDl             string
	BookFB2            string
	BookRead           string
	BooksNum           string
	BooksAuthorAlpha   string
	BooksAuthorTime    string
	BooksAuthorNonSeq  string
	BooksAuthorSeq     string
	BooksAlphabet      string
	BooksTime          string
	BooksNonSeq        string
	BooksSeq           string
	BookInfo           string
	BookInfoSeq        string
	Authors            string
	AuthRootSubtitle   string
	Author             string
	AuthorTpl          string
	AuthorsNum         string
	Sequences          string
	SeqRootSubtitle    string
	Sequence           string
	SeqTpl             string
	SeqsNum            string
	SeqsAuthor         string
	PubInfoISBN        string
	PubInfoYear        string
	PubInfoPublisher   string
	GenresMeta         string
	Genres             string
	Genre              string
	GenresRootSubtitle string
	GenreTpl           string
	SearchMain         string
	SchMainAuthor      string
	SchMainSeq         string
	SchMainBook        string
	SchMainAnno        string
	SchMainAnnoVector  string
	SearchAuthor       string
	SearchSeq          string
	SearchBook         string
	SearchAnno         string
	SearchAnnoVector   string
	RndBooks           string
	RndSeqs            string
	RndGenreBooks      string
	AllBooksByTime     string
	JSAuthors          string
	JSLinks            string
	JSGenres           string
	JSLang             string
}

// GetLANGs returns the LANG constants struct.
func GetLANGs() *LANG {
	return &LANG{
		TitleTime:      "По дате поступления",
		TitleAuthors:   "По авторам",
		TitleSequences: "По сериям",
		TitleGenres:    "По жанрам",
		TitleRndBooks:  "Случайные книги",
		TitleRndSeqs:   "Случайные серии",
		TitleRndGenre:  "Случайные книги в жанре",

		BookDl:   "Скачать",
		BookFB2:  "Читать fb2",
		BookRead: "Читать онлайн",

		BooksNum:         "%s книг(и)",
		BooksAuthorAlpha: "Книги автора '%s' по алфавиту",
		BooksAuthorTime:  "Книги автора '%s' по времени поступления",
		BooksAuthorNonSeq: "Книги автора '%s' вне серий",
		BooksAuthorSeq:   "Серия '%s', автор '%s'",

		BooksAlphabet: "По алфавиту",
		BooksTime:     "По дате добавления",
		BooksNonSeq:   "Вне серий",
		BooksSeq:      "По сериям",

		BookInfo: strings.Join([]string{
			"<p class=\"book\"> %s </p>\n<br/>формат: fb2<br/>",
			"размер: %s<br/>",
		}, ""),
		BookInfoSeq: strings.Join([]string{
			"<p class=\"book\"> %s </p>\n<br/>формат: fb2<br/>",
			"размер: %s<br/>Серия: %s, номер: %s<br/>",
		}, ""),

		Authors:          "Авторы",
		AuthRootSubtitle: "Авторы на ",
		Author:           "Автор %s",
		AuthorTpl:        "Автор '%s'",
		AuthorsNum:       "%s авт.",

		Sequences:       "Серии",
		SeqRootSubtitle: "Серии на ",
		Sequence:        "Серия ",
		SeqTpl:          "Серия '%s'",
		SeqsNum:         "%s сер.",
		SeqsAuthor:      "Серии автора '%s'",

		PubInfoISBN:      "<p>ISBN: %s</p>",
		PubInfoYear:      "<p>Год публикации: %s</p>",
		PubInfoPublisher: "<p>Издательство: %s</p>",

		GenresMeta:         "Группы жанров",
		Genres:             "Жанры",
		Genre:              "Жанр ",
		GenresRootSubtitle: "Жанры в группе ",
		GenreTpl:           "Жанр '%s'",

		SearchMain:        "Поиск по '%s'",
		SchMainAuthor:     "Поиск в именах авторов",
		SchMainSeq:        "Поиск в сериях",
		SchMainBook:       "Поиск в названиях книг",
		SchMainAnno:       "Поиск в аннотациях книг",
		SchMainAnnoVector: "Векторный поиск книг",

		SearchAuthor:       "Поиск среди авторов по '%s'",
		SearchSeq:          "Поиск среди серий по '%s'",
		SearchBook:         "Поиск в заголовках книг по '%s'",
		SearchAnno:         "Поиск в описаниях книг по '%s'",
		SearchAnnoVector:   "Векторный поиск по '%s'",

		RndBooks:      "Случайные книги",
		RndSeqs:       "Случайные серии",
		RndGenreBooks: "Случайные книги в жанре '%s'",

		AllBooksByTime: "Все книги по дате поступления",

		JSAuthors: "Авторы:",
		JSLinks:   "Ссылки:",
		JSGenres:  "Жанры:",
		JSLang:    "Язык:",
	}
}

// VECTOR_SIZE is the embedding vector dimension.
const VECTOR_SIZE = 256

// XSLReadTemplate is the XML-stylesheet line template.
const XSLReadTemplate = `<?xml-stylesheet type="text/xsl" href="%s"?>`
package main

import (
	"encoding/json"
	"encoding/xml"
	"fmt"
	"os"

	"fb2srv_go/config"
	"fb2srv_go/db"
	"fb2srv_go/model"
	"fb2srv_go/util"
)

func main() {
	fmt.Println("=== Phase 2: Models & Database ===")
	fmt.Println()

	// Load config
	cfgPath := "config.ini"
	if len(os.Args) > 1 {
		cfgPath = os.Args[1]
	}

	cfg := config.LoadConfig(cfgPath)

	// Print DB config values
	fmt.Println("--- Database Config ---")
	fmt.Printf("  PG_HOST:  %s\n", cfg.Get("PG_HOST"))
	fmt.Printf("  PG_BASE:  %s\n", cfg.Get("PG_BASE"))
	fmt.Printf("  PG_USER:  %s\n", cfg.Get("PG_USER"))
	fmt.Printf("  PG_PASS:  %s\n", cfg.Get("PG_PASS"))
	fmt.Printf("  PAGE_SIZE: %s\n", cfg.Get("PAGE_SIZE"))
	fmt.Printf("  OPENAI_URL: %s\n", cfg.Get("OPENAI_URL"))
	fmt.Printf("  OPENAI_MODEL: %s\n", cfg.Get("OPENAI_MODEL"))
	fmt.Printf("  VECTOR_SIZE: %d\n", config.VECTOR_SIZE)
	fmt.Println()

	// === Test DB Connection ===
	fmt.Println("=== Test: DB Connection ===")
	database, err := db.NewDB(cfg)
	if err != nil {
		fmt.Printf("  SKIP: Cannot connect to database: %v\n", err)
		fmt.Println("  (Set up PostgreSQL with config.ini to run DB tests)")
		fmt.Println()
		fmt.Println("=== Phase 2: Models Test (no DB) ===")
		testModels()
		testEmbedding(cfg)
		fmt.Println()
		fmt.Println("=== Phase 2 Complete (partial) ===")
		return
	}
	err = database.Close()
	if err != nil {
		fmt.Printf("  WARN: Close error: %v\n", err)
	} else {
		fmt.Println("  PASS: Database connection established and closed")
	}
	fmt.Println()

	// Re-open for tests
	database, err = db.NewDB(cfg)
	if err != nil {
		fmt.Printf("  FATAL: Cannot reconnect: %v\n", err)
		return
	}
	defer database.Close()

	// Run all DB tests
	testBooksCount(database, cfg)
	testBooksByDate(database, cfg)
	testRandomBooks(database, cfg)
	testSearchBooksByTitle(database, cfg)
	testSearchBooksByAnnotation(database, cfg)
	testAuthors(database, cfg)
	testSequences(database, cfg)
	testGenres(database, cfg)
	testOPDSXML()
	testEmbedding(cfg)

	fmt.Println()
	fmt.Println("=== Phase 2 Complete ===")
}

// --- Model tests (no DB required) ---

func testModels() {
	fmt.Println("--- Model: Book Structure ---")
	book := model.Book{
		Zipfile:   "1234/1234",
		Filename:  "book.fb2",
		Genres:    []string{"fantastic_scifi", "fantastic_heroic_fantasy"},
		BookID:    "1234",
		BookTitle: "Тестовая книга",
		Lang:      "rus",
		Size:      123456,
		DateTime:  "2024-01-15_00:00",
		Authors: []model.Author{
			{ID: "aaa111", Name: "Толстой Л."},
		},
		Sequences: []model.SequenceRef{
			{ID: "bbb222", Name: "Война и мир", Num: intPtr(1)},
		},
		PubInfo: &model.PubInfo{
			ISBN:      "978-5-00000-000-0",
			Year:      "2024",
			Publisher: "Издательство",
		},
	}
	b, _ := json.MarshalIndent(book, "  ", "  ")
	fmt.Printf("  Book JSON:\n  %s\n", string(b))
	fmt.Println()

	fmt.Println("--- Model: OPDSFeed Structure ---")
	feed := model.OPDSFeed{
		XMLName:   "feed",
		XMLNS:     "http://www.w3.org/2005/Atom",
		XMLNSdc:   "http://purl.org/dc/terms/",
		XMLNSos:   "http://a9.com/-/spec/opensearch/1.1/",
		XMLNSopds: "http://opds-spec.org/2010/catalog",
		ID:        "tag:root",
		Title:     "Test Library",
		Updated:   "2024-01-15T12:00:00",
		Icon:      "/favicon.ico",
		Links: []model.OPDSLink{
			{HRef: "/opds/", Rel: "start", Type: "application/atom+xml;profile=opds-catalog"},
			{HRef: "/opds/", Rel: "self", Type: "application/atom+xml;profile=opds-catalog"},
		},
		Entries: []model.OPDSEntry{
			{
				Updated: "2024-01-15T12:00:00",
				ID:      "tag:root:time",
				Title:   "По дате поступления",
				Links: []model.OPDSLink{
					{HRef: "/opds/time", Type: "application/atom+xml;profile=opds-catalog"},
				},
				Content: &model.OPDSContent{
					Type:  "text",
					Value: "По дате поступления",
				},
			},
		},
	}
	x, _ := xml.MarshalIndent(feed, "  ", "  ")
	fmt.Printf("  OPDS XML:\n  %s\n", string(x))
}

// --- DB test functions ---

func testBooksCount(database *db.DB, cfg *config.Config) {
	fmt.Println("--- Test: GetBooksCount ---")
	count, err := database.GetBooksCount()
	if err != nil {
		fmt.Printf("  ERROR: %v\n", err)
		return
	}
	fmt.Printf("  PASS: Total books = %d\n", count)
	fmt.Println()
}

func testBooksByDate(database *db.DB, cfg *config.Config) {
	fmt.Println("--- Test: GetBooksByDate ---")
	limit := 3
	books, err := database.GetBooksByDate(0, limit)
	if err != nil {
		fmt.Printf("  ERROR: %v\n", err)
		return
	}
	fmt.Printf("  PASS: Got %d books (latest)\n", len(books))
	for i, b := range books {
		fmt.Printf("    [%d] %s - %s (%s)\n", i+1, b.BookTitle, b.BookID, b.DateTime)
		if len(b.Authors) > 0 {
			fmt.Printf("        Authors: %s\n", b.Authors[0].Name)
		}
	}
	fmt.Println()
}

func testRandomBooks(database *db.DB, cfg *config.Config) {
	fmt.Println("--- Test: GetRandomBooks ---")
	limit := 2
	books, err := database.GetRandomBooks(limit)
	if err != nil {
		fmt.Printf("  ERROR: %v\n", err)
		return
	}
	fmt.Printf("  PASS: Got %d random books\n", len(books))
	for i, b := range books {
		fmt.Printf("    [%d] %s - %s\n", i+1, b.BookTitle, b.BookID)
	}
	fmt.Println()
}

func testSearchBooksByTitle(database *db.DB, cfg *config.Config) {
	fmt.Println("--- Test: SearchBooksByTitle ---")
	query := "война"
	books, err := database.SearchBooksByTitle(query, 5)
	if err != nil {
		fmt.Printf("  ERROR: %v\n", err)
		return
	}
	fmt.Printf("  PASS: Search(%q) => %d books\n", query, len(books))
	for i, b := range books {
		if i >= 3 {
			break
		}
		fmt.Printf("    [%d] %s (%s)\n", i+1, b.BookTitle, b.BookID)
	}
	fmt.Println()
}

func testSearchBooksByAnnotation(database *db.DB, cfg *config.Config) {
	fmt.Println("--- Test: SearchBooksByAnnotation ---")
	query := "приключение"
	books, err := database.SearchBooksByAnnotation(query, 5)
	if err != nil {
		fmt.Printf("  ERROR: %v\n", err)
		return
	}
	fmt.Printf("  PASS: SearchAnno(%q) => %d books\n", query, len(books))
	for i, b := range books {
		if i >= 3 {
			break
		}
		fmt.Printf("    [%d] %s (%s)\n", i+1, b.BookTitle, b.BookID)
	}
	fmt.Println()
}

func testAuthors(database *db.DB, cfg *config.Config) {
	fmt.Println("--- Test: Authors ---")

	count, err := database.AuthorCount()
	if err != nil {
		fmt.Printf("  AuthorCount ERROR: %v\n", err)
	} else {
		fmt.Printf("  AuthorCount: %d\n", count)
	}

	authors, err := database.SearchAuthors("толстой", 3)
	if err != nil {
		fmt.Printf("  SearchAuthors ERROR: %v\n", err)
	} else {
		fmt.Printf("  SearchAuthors(%q): %d\n", "толстой", len(authors))
		for i, a := range authors {
			fmt.Printf("    [%d] %s (%s)\n", i+1, a.Name, a.ID)
		}
	}

	rnd, err := database.GetRandomAuthors(2)
	if err != nil {
		fmt.Printf("  GetRandomAuthors ERROR: %v\n", err)
	} else {
		fmt.Printf("  GetRandomAuthors(2): %d\n", len(rnd))
		for i, a := range rnd {
			fmt.Printf("    [%d] %s (%s)\n", i+1, a.Name, a.ID)
		}
	}
	fmt.Println()
}

func testSequences(database *db.DB, cfg *config.Config) {
	fmt.Println("--- Test: Sequences ---")

	count, err := database.SequenceCount()
	if err != nil {
		fmt.Printf("  SequenceCount ERROR: %v\n", err)
	} else {
		fmt.Printf("  SequenceCount: %d\n", count)
	}

	seqs, err := database.SearchSequences("героическая", 3)
	if err != nil {
		fmt.Printf("  SearchSequences ERROR: %v\n", err)
	} else {
		fmt.Printf("  SearchSequences(%q): %d\n", "героическая", len(seqs))
		for i, s := range seqs {
			fmt.Printf("    [%d] %s (%s)\n", i+1, s.Name, s.ID)
		}
	}

	rnd, err := database.GetRandomSequences(2)
	if err != nil {
		fmt.Printf("  GetRandomSequences ERROR: %v\n", err)
	} else {
		fmt.Printf("  GetRandomSequences(2): %d\n", len(rnd))
		for i, s := range rnd {
			fmt.Printf("    [%d] %s (%s)\n", i+1, s.Name, s.ID)
		}
	}
	fmt.Println()
}

func testGenres(database *db.DB, cfg *config.Config) {
	fmt.Println("--- Test: Genres ---")

	count, err := database.GenreCount()
	if err != nil {
		fmt.Printf("  GenreCount ERROR: %v\n", err)
	} else {
		fmt.Printf("  GenreCount: %d\n", count)
	}

	metas, err := database.GetGenresMeta()
	if err != nil {
		fmt.Printf("  GetGenresMeta ERROR: %v\n", err)
	} else {
		fmt.Printf("  GetGenresMeta: %d groups\n", len(metas))
		for i, m := range metas {
			fmt.Printf("    [%d] %s (%s)\n", i+1, m.Name, m.MetaID)
		}
	}

	if len(metas) > 0 {
		genres, err := database.GetGenresByMetaID(metas[0].MetaID)
		if err != nil {
			fmt.Printf("  GetGenresByMetaID(%q) ERROR: %v\n", metas[0].MetaID, err)
		} else {
			fmt.Printf("  GetGenresByMetaID(%q): %d genres\n", metas[0].MetaID, len(genres))
			for i, g := range genres {
				if i >= 5 {
					break
				}
				fmt.Printf("    [%d] %s (%s)\n", i+1, g.Name, g.ID)
			}
		}
	}
	fmt.Println()
}

func testOPDSXML() {
	fmt.Println("--- Test: OPDS XML Serialization ---")

	feed := model.OPDSFeed{
		XMLName:   "feed",
		XMLNS:     "http://www.w3.org/2005/Atom",
		XMLNSdc:   "http://purl.org/dc/terms/",
		XMLNSos:   "http://a9.com/-/spec/opensearch/1.1/",
		XMLNSopds: "http://opds-spec.org/2010/catalog",
		ID:        "tag:root",
		Title:     "Test Library",
		Updated:   "2024-01-15T12:00:00+05:00",
		Icon:      "/favicon.ico",
		Links: []model.OPDSLink{
			{HRef: "/opds/?searchTerm={searchTerms}", Rel: "search", Type: "application/atom+xml"},
			{HRef: "/opds/", Rel: "start", Type: "application/atom+xml;profile=opds-catalog"},
			{HRef: "/opds/", Rel: "self", Type: "application/atom+xml;profile=opds-catalog"},
		},
		Entries: []model.OPDSEntry{
			{
				Updated: "2024-01-15T12:00:00+05:00",
				ID:      "tag:book:1234",
				Title:   "Война и мир",
				Authors: []model.OPDSAuthor{
					{URI: "/opds/author/t/tol/tolстой", Name: "Толстой Л.Н."},
				},
				Links: []model.OPDSLink{
					{HRef: "/fb2/1234/book.fb2.zip", Rel: "http://opds-spec.org/acquisition/open-access", Title: "Скачать", Type: "application/fb2+zip"},
					{HRef: "/read/1234/book.fb2.html", Title: "Читать онлайн", Type: "text/html"},
					{HRef: "/books/1/t/1234.jpg", Rel: "http://opds-spec.org/image", Type: "image/jpeg"},
				},
				Categories: []model.OPDSCategory{
					{Term: "fantastic_heroic_fantasy", Label: "Фантастика Героическая"},
				},
				DCLanguage: "rus",
				DCFormat:   "fb2",
				Content: &model.OPDSContent{
					Type:  "text/html",
					Value: "<p>Эпический роман о войне и мире.</p>",
				},
			},
		},
	}

	output, err := xml.MarshalIndent(feed, "", "  ")
	if err != nil {
		fmt.Printf("  ERROR: %v\n", err)
		return
	}
	xmlStr := "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + string(output)
	fmt.Printf("  PASS: OPDS Feed serialized (%d bytes)\n", len(xmlStr))
	fmt.Printf("  Preview:\n")
	preview := xmlStr
	if len(preview) > 500 {
		preview = preview[:500] + "... (truncated)"
	}
	for _, line := range splitLines(preview) {
		fmt.Printf("  %s\n", line)
	}
	fmt.Println()
}

func testEmbedding(cfg *config.Config) {
	fmt.Println("--- Test: GetVector (Embedding) ---")

	text := "Война и мир роман Толстой"
	fmt.Printf("  Text: %q\n", text)
	fmt.Printf("  URL: %s\n", cfg.Get("OPENAI_URL"))
	fmt.Printf("  Model: %s\n", cfg.Get("OPENAI_MODEL"))
	fmt.Printf("  Dimensions: %d\n", config.VECTOR_SIZE)

	vec := util.GetVector(cfg, text)
	if vec == nil {
		fmt.Printf("  SKIP: No vector returned (API unavailable or error)\n")
		fmt.Printf("  (Set OPENAI_URL to a running OpenAI-compatible API to test)\n")
	} else {
		fmt.Printf("  PASS: Got vector with %d dimensions\n", len(vec))
		// Print first 8 values
		show := len(vec)
		if show > 8 {
			show = 8
		}
		fmt.Printf("  First %d values: ", show)
		for i := 0; i < show; i++ {
			if i > 0 {
				fmt.Printf(", ")
			}
			fmt.Printf("%.6f", vec[i])
		}
		fmt.Printf("...\n")
	}
	fmt.Println()
}

// Helper functions

func intPtr(i int) *int {
	return &i
}

func splitLines(s string) []string {
	var lines []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			lines = append(lines, s[start:i])
			start = i + 1
		}
	}
	if start < len(s) {
		lines = append(lines, s[start:])
	}
	return lines
}
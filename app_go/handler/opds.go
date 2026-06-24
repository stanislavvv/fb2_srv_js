// Package handler provides OPDS HTTP handlers and route registration.
package handler

import (
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"

	"fb2srv_go/config"
	"fb2srv_go/db"
	"fb2srv_go/model"
	"fb2srv_go/util"

	"github.com/go-chi/chi"
)

// Server holds the application state for HTTP handlers.
type Server struct {
	CFG      *config.Config
	URLs     *config.URL
	LANG     *config.LANG
	Database *db.DB
	Router   *chi.Mux
	XSLT     *util.XSLTTransform
}

// NewServer creates a new Server with chi router and all routes registered.
func NewServer(cfg *config.Config, database *db.DB, xslt *util.XSLTTransform) *Server {
	s := &Server{
		CFG:      cfg,
		URLs:     config.GetURLs(),
		LANG:     config.GetLANGs(),
		Database: database,
		Router:   chi.NewRouter(),
		XSLT:     xslt,
	}

	// Middleware
	s.Router.Use(s.loggingMiddleware)
	s.Router.Use(s.authMiddleware)

	// Register all routes
	s.registerRoutes()

	return s
}

// authMiddleware checks HTTP Basic Authentication against passwd file.
func (s *Server) authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Check if passwd file exists
		passwdPath := s.CFG.Get("ZIPS") + "/passwd"
		if _, err := os.Stat(passwdPath); os.IsNotExist(err) {
			// No passwd file, no auth required
			next.ServeHTTP(w, r)
			return
		}

		// Require authentication
		auth := r.Header.Get("Authorization")
		if auth == "" {
			w.Header().Set("WWW-Authenticate", `Basic realm="OPDS Library"`)
			http.Error(w, "401 Authorization Required", http.StatusUnauthorized)
			return
		}

		// Parse Basic auth
		if !strings.HasPrefix(auth, "Basic ") {
			w.Header().Set("WWW-Authenticate", `Basic realm="OPDS Library"`)
			http.Error(w, "401 Authorization Required", http.StatusUnauthorized)
			return
		}

		// Decode base64 - simple implementation
		cred := strings.TrimPrefix(auth, "Basic ")
		decoded, err := decodeBase64Basic(cred)
		if err != nil {
			w.Header().Set("WWW-Authenticate", `Basic realm="OPDS Library"`)
			http.Error(w, "401 Authorization Required", http.StatusUnauthorized)
			return
		}

		parts := strings.SplitN(decoded, ":", 2)
		if len(parts) != 2 {
			w.Header().Set("WWW-Authenticate", `Basic realm="OPDS Library"`)
			http.Error(w, "401 Authorization Required", http.StatusUnauthorized)
			return
		}

		if !util.IsAuth(parts[0], parts[1], s.CFG.Get("ZIPS")) {
			w.Header().Set("WWW-Authenticate", `Basic realm="OPDS Library"`)
			http.Error(w, "401 Authorization Required", http.StatusUnauthorized)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// decodeBase64Basic decodes a base64 string without importing encoding/base64
// to keep the implementation simple. Uses standard library encoding/base64.
func decodeBase64Basic(encoded string) (string, error) {
	// Use Go standard library for base64 decoding
	imported, err := base64StdDecode(encoded)
	return imported, err
}

// base64StdDecode uses encoding/base64 for decoding
func base64StdDecode(s string) (string, error) {
	// We need a simple base64 decoder for "user:password"
	decodeMap := make([]byte, 128)
	for i := 0; i < 64; i++ {
		c := byte(0)
		switch {
		case i < 26:
			c = byte('A' + i)
		case i < 52:
			c = byte('a' + (i - 26))
		case i < 62:
			c = byte('0' + (i - 52))
		case i == 62:
			c = '+'
		case i == 63:
			c = '/'
		}
		decodeMap[c] = byte(i)
	}

	in := []byte(s)
	out := make([]byte, 0, len(in))
	var val uint64
	valLen := 0

	for _, c := range in {
		if c == '=' {
			break
		}
		if c < 128 {
			val = val<<6 | uint64(decodeMap[c])
			valLen += 6
		} else {
			continue
		}
		if valLen >= 8 {
			valLen -= 8
			out = append(out, byte(val>>uint(valLen)))
			val &= (1<<uint(valLen)) - 1
		}
	}

	return string(out), nil
}

func (sc *statusCapture) WriteHeader(status int) {
	sc.status = status
	sc.w.WriteHeader(status)
}

// loggingMiddleware logs each request method, path and status.
func (s *Server) loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := r.Context()
		_ = start
		log.Printf("START %s %s from %s", r.Method, r.RequestURI, r.RemoteAddr)

		// Wrap ResponseWriter to capture status code
		wr := &statusCapture{w: w, status: http.StatusOK}
		next.ServeHTTP(wr, r)

		log.Printf("FINISH %s %s => %d", r.Method, r.RequestURI, wr.status)
	})
}

// statusCapture wraps http.ResponseWriter to capture status code.
type statusCapture struct {
	w      http.ResponseWriter
	status int
}

func (sc *statusCapture) Header() http.Header { return sc.w.Header() }
func (sc *statusCapture) Write(header []byte) (int, error) {
	return sc.w.Write(header)
}
func (sc *statusCapture) WriteStatus(status int) {
	sc.status = status
	sc.w.WriteHeader(status)
}

// registerRoutes registers all OPDS and static routes.
func (s *Server) registerRoutes() {
	r := s.Router
	appRoot := s.CFG.Get("APPLICATION_ROOT")

	// Determine if we need a prefix strip middleware
	if appRoot != "" {
		// Strip APPLICATION_ROOT prefix from requests
		oldRouter := r
		r = chi.NewRouter()
		r.Mount(appRoot, oldRouter)
		s.Router = r
	}

	// === OPDS Routes (Phase 4.2: Root and navigation) ===

	// GET /opds/ -> opdsMain
	r.Get(s.URLs.Start, s.opdsMainHandler)

	// GET /opds/time -> opdsTimeBooks (page=0)
	r.Get(s.URLs.Time, s.opdsTimeHandler)

	// GET /opds/time/{page} -> opdsTimeBooks
	r.Get(s.URLs.Time+"/{page}", s.opdsTimePageHandler)

	// === Authors routes ===
	r.Get(s.URLs.AuthIdx, s.authRootHandler)
	r.Get(s.URLs.AuthIdx+"{sub}", s.authSubHandler)
	r.Get(s.URLs.AuthIdx+"{sub1}/{sub2}", s.authSub2Handler)
	r.Get(s.URLs.Author+"{sub1}/{sub2}/{id}", s.authorMainHandler)
	r.Get(s.URLs.Author+"{sub1}/{sub2}/{id}/sequences", s.authorSeqsHandler)
	r.Get(s.URLs.Author+"{sub1}/{sub2}/{id}/sequenceless", s.authorNonSeqHandler)
	r.Get(s.URLs.Author+"{sub1}/{sub2}/{id}/alphabet", s.authorAlphabetHandler)
	r.Get(s.URLs.Author+"{sub1}/{sub2}/{id}/time", s.authorTimeHandler)
	r.Get(s.URLs.Author+"{sub1}/{sub2}/{id}/{seq_id}", s.authorSeqBooksHandler)

	// === Sequences routes ===
	seqIdxBase := strings.TrimRight(s.URLs.SeqIdx, "/")
	r.Get(seqIdxBase, s.seqRootHandler)
	r.Get(seqIdxBase+"/", s.seqRootHandler)
	r.Get(seqIdxBase+"/{sub}", s.seqSubHandler)
	r.Get(seqIdxBase+"/{sub}/", s.seqSubHandler)
	r.Get(seqIdxBase+"/{sub1}/{sub2}", s.seqSub2Handler)
	r.Get(seqIdxBase+"/{sub1}/{sub2}/", s.seqSub2Handler)
	seqBase := strings.TrimRight(s.URLs.Seq, "/")
	r.Get(seqBase+"/{sub1}/{sub2}/{id}", s.sequenceBooksHandler)
	r.Get(seqBase+"/{sub1}/{sub2}/{id}/", s.sequenceBooksHandler)

	// === Genres routes ===
	genIdxBase := strings.TrimRight(s.URLs.GenIdx, "/")
	r.Get(genIdxBase, s.genresRootHandler)
	r.Get(genIdxBase+"/", s.genresRootHandler)
	r.Get(genIdxBase+"/{meta_id}", s.genresListHandler)
	r.Get(genIdxBase+"/{meta_id}/", s.genresListHandler)
	genreBase := strings.TrimRight(s.URLs.Genre, "/")
	r.Get(genreBase+"/{gen_id}", s.genreBooksHandler)
	r.Get(genreBase+"/{gen_id}/", s.genreBooksHandler)
	r.Get(genreBase+"/{gen_id}/{page}", s.genreBooksPageHandler)
	r.Get(genreBase+"/{gen_id}/{page}/", s.genreBooksPageHandler)

	// === Random routes ===
	r.Get(s.URLs.RndBook, s.rndBooksHandler)
	r.Get(s.URLs.RndSeq, s.rndSeqsHandler)
	rndGenIdxBase := strings.TrimRight(s.URLs.RndGenIdx, "/")
	r.Get(rndGenIdxBase, s.rndGenresRootHandler)
	r.Get(rndGenIdxBase+"/", s.rndGenresRootHandler)
	r.Get(rndGenIdxBase+"/{meta_id}", s.rndGenresListHandler)
	r.Get(rndGenIdxBase+"/{meta_id}/", s.rndGenresListHandler)
	rndGenBase := strings.TrimRight(s.URLs.RndGen, "/")
	r.Get(rndGenBase+"/{gen_id}", s.rndBooksByGenreHandler)
	r.Get(rndGenBase+"/{gen_id}/", s.rndBooksByGenreHandler)

	// === Search routes ===
	r.Get(s.URLs.Search, s.searchMainHandler)
	r.Get(s.URLs.SrchAuth, s.searchAuthorsHandler)
	r.Get(s.URLs.SrchSeq, s.searchSequencesHandler)
	r.Get(s.URLs.SrchBook, s.searchBooksHandler)
	r.Get(s.URLs.SrchBookAnno, s.searchBooksAnnoHandler)
	r.Get(s.URLs.SrchBookAnnoVector, s.searchBooksAnnoVectorHandler)

	// === Static routes: Covers ===
	coverBase := strings.TrimRight(s.URLs.Cover, "/")
	r.Get(coverBase+"/{sub1}/{sub2}/{book_id}.jpg", s.coverHandler)

	// === Static routes: Web Interface ===
	r.Get("/", s.webrootHandler)
	r.Get("/interface.js", s.interfaceJSHandler)
	r.Get("/favicon.ico", s.faviconHandler)
	r.Get("/moon.svg", s.moonIconHandler)
	r.Get("/sun.svg", s.sunIconHandler)
	r.Get(s.URLs.XslRead, s.xslHandler)

	// === Static routes: Download ===
	dlBase := strings.TrimRight(s.URLs.Dl, "/")
	r.Get(dlBase+"/{zip_file}/{filename}", s.downloadHandler)

	// === Static routes: Read ===
	readBase := strings.TrimRight(s.URLs.Read, "/")
	r.Get(readBase+"/{zip_file}/{filename}", s.readHandler)
	r.Get(readBase+"/{zip_file}/{filename}.html", s.readHandler)

	// === Static routes: Plain FB2 ===
	plainBase := strings.TrimRight(s.URLs.Plain, "/")
	r.Get(plainBase+"/{zip_file}/{filename}", s.plainHandler)
}

// --- Helper to get path params ---

// Param is a helper to extract URL path parameters from chi context.
func Param(r *http.Request, key string) string {
	return chi.URLParam(r, key)
}

// --- OPDS Root Handlers (4.2) ---

// opdsMainHandler handles GET /opds/
func (s *Server) opdsMainHandler(w http.ResponseWriter, r *http.Request) {
	feed := OpdsMain(s.CFG, s.URLs, s.LANG)
	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// opdsTimeHandler handles GET /opds/time (page=0)
func (s *Server) opdsTimeHandler(w http.ResponseWriter, r *http.Request) {
	s.opdsTimePageHandler(w, r)
}

// opdsTimePageHandler handles GET /opds/time/{page}
func (s *Server) opdsTimePageHandler(w http.ResponseWriter, r *http.Request) {
	pageStr := Param(r, "page")
	page := 0
	if pageStr != "" {
		var err error
		page, err = strconv.Atoi(pageStr)
		if err != nil || page < 0 {
			page = 0
		}
	}

	pageSize := 50
	fmt.Sscanf(s.CFG.Get("PAGE_SIZE"), "%d", &pageSize)

	offset := page * pageSize
	limit := pageSize

	// Calculate next page
	nextPage := page + 1
	nextStr := fmt.Sprintf("%s/%d", s.URLs.Time, nextPage)

	// Calculate prev page
	var prevStr *string
	if page > 0 {
		p := page - 1
		val := fmt.Sprintf("%s/%d", s.URLs.Time, p)
		prevStr = &val
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	// Check DB availability
	if s.Database == nil {
		// Build empty feed with navigation
		feed := OpdsHeader(OpdsHeaderParams{
			Title:   s.LANG.AllBooksByTime,
			Ts:      ts,
			Start:   s.URLs.Start,
			Self:    s.URLs.Time,
			Tag:     fmt.Sprintf("tag:time:%d", page),
			Up:      &s.URLs.Start,
			Prev:    prevStr,
			AppRoot: appRoot,
			URLs:    s.URLs,
		})
		CreateOPDSResponseWithConfig(w, feed, s.CFG)
		return
	}

	// Determine if more books exist for next page
	books, err := s.Database.GetBooksByDate(offset, limit+1)
	if err != nil {
		log.Printf("ERROR: GetBooksByDate: %v", err)
		http.Error(w, fmt.Sprintf("DB error: %v", err), http.StatusInternalServerError)
		return
	}

	// If we got limit+1 books, there's a next page
	hasNext := len(books) > limit
	if hasNext {
		books = books[:limit]
	} else {
		nextStr = ""
	}

	// Remove next link if no more pages
	var nextPtr *string
	if hasNext {
		nextPtr = &nextStr
	}

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   s.LANG.AllBooksByTime,
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.Time + "/" + strconv.Itoa(page),
		Tag:     fmt.Sprintf("tag:time:%d", page),
		Up:      &s.URLs.Start,
		Prev:    prevStr,
		Next:    nextPtr,
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	for _, book := range books {
		entry := MakeBookEntry(book, ts, appRoot, s.URLs, s.LANG, s.URLs.Author, s.URLs.Seq, nil)
		feed.Entries = append(feed.Entries, entry)
	}

	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// --- Author Handlers (4.3) ---

// authRootHandler handles GET /opds/authorsindex/
func (s *Server) authRootHandler(w http.ResponseWriter, r *http.Request) {
	appRoot := s.CFG.Get("APPLICATION_ROOT")

	// index: "authorsindex/" -> reads {pages_path}/authorsindex/index.json
	// Python: index=URL["authidx"].replace("/opds/", "", 1) => "authidx" without leading /opds/
	// URL["authidx"] = "/opds/authorsindex/" -> index = "authorsindex/"
	// up: URL["start"] = "/opds/"
	up := s.URLs.Start

	params := SimpleListParams{
		Index:         "authorsindex/",
		Self:          s.URLs.AuthIdx,
		SimpleBaseRef: s.URLs.AuthIdx,
		StrongBaseRef: s.URLs.Author,
		SubTag:        "tag:authors:",
		Subtitle:      s.LANG.AuthRootSubtitle,
		Title:         s.LANG.Authors,
		Up:            &up,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: authRootHandler: %v", err)
		http.Error(w, "Error loading authors", http.StatusInternalServerError)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// authSubHandler handles GET /opds/authorsindex/{sub}
func (s *Server) authSubHandler(w http.ResponseWriter, r *http.Request) {
	sub := Param(r, "sub")
	if sub == "" {
		s.authRootHandler(w, r)
		return
	}

	subValid := util.ValidatePrefix(sub)
	if subValid == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	subEnc := url.QueryEscape(subValid)
	self := s.URLs.AuthIdx + subEnc
	up := s.URLs.AuthIdx

	params := SimpleListParams{
		Index:         "authorsindex/" + subValid,
		Self:          self,
		SimpleBaseRef: s.URLs.AuthIdx + subEnc + "/",
		StrongBaseRef: s.URLs.Author,
		SubTag:        "tag:authors:",
		Subtitle:      s.LANG.AuthorsNum,
		Layout:        "subs",
		UseNums:       boolPtr(true),
		Title:         s.LANG.AuthRootSubtitle + subValid,
		Up:            &up,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: authSubHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// authSub2Handler handles GET /opds/authorsindex/{sub1}/{sub2}
func (s *Server) authSub2Handler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")

	if sub1 == "" || sub2 == "" {
		s.authSubHandler(w, r)
		return
	}

	sub1Valid := util.ValidatePrefix(sub1)
	sub2Valid := util.ValidatePrefix(sub2)
	if sub1Valid == "" || sub2Valid == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	sub1Enc := url.QueryEscape(sub1Valid)
	sub2Enc := url.QueryEscape(sub2Valid)
	self := s.URLs.AuthIdx + sub1Enc + "/" + sub2Enc
	up := s.URLs.AuthIdx + sub1Enc

	params := SimpleListParams{
		Index:         "authorsindex/" + sub1Valid + "/" + sub2Valid,
		Self:          self,
		SimpleBaseRef: s.URLs.AuthIdx + sub1Enc + "/" + sub2Enc + "/",
		StrongBaseRef: s.URLs.Author,
		SubTag:        "tag:author:",
		Subtitle:      "'%s'",
		Title:         s.LANG.AuthRootSubtitle + sub2Valid,
		Up:            &up,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: authSub2Handler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// authorMainHandler handles GET /opds/author/{sub1}/{sub2}/{id}
func (s *Server) authorMainHandler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")
	id := Param(r, "id")

	if sub1 == "" || sub2 == "" || id == "" {
		http.NotFound(w, r)
		return
	}

	// Validate each part
	if util.ValidateID(sub1) == "" || util.ValidateID(sub2) == "" || util.ValidateID(id) == "" {
		http.NotFound(w, r)
		return
	}

	// Python: auth_id = sub1 + sub2 + id (direct concatenation, NOT MakeID)
	authID := sub1 + sub2 + id

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	authPath := util.ID2Path(authID)
	up := s.URLs.AuthIdx + sub1 + "/" + sub2

	// index: "author/{sub1}/{sub2}/{id}" -> reads {pages_path}/author/{sub1}/{sub2}/{id}/index.json
	// Python: index=URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}"
	// URL["author"] = "/opds/author/" -> index = "author/" + sub1 + "/" + sub2 + "/" + id
	indexPath := "author/" + sub1 + "/" + sub2 + "/" + id

	params := AuthorPageParams{
		Sub1:    sub1,
		Sub2:    sub2,
		AuthID:  authID,
		Index:   indexPath,
		SubTag:  "tag:author:" + authID,
		Title:   s.LANG.AuthorTpl,
		Self:    s.URLs.Author + authPath,
		Start:   s.URLs.Start,
		Up:      &up,
		AppRoot: appRoot,
		URLs:    s.URLs,
		LANG:    s.LANG,
		CFG:     s.CFG,
	}

	feed, err := OpdsAuthorPage(params)
	if err != nil {
		log.Printf("ERROR: authorMainHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// authorSeqsHandler handles GET /opds/author/{sub1}/{sub2}/{id}/sequences
func (s *Server) authorSeqsHandler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")
	id := Param(r, "id")

	if sub1 == "" || sub2 == "" || id == "" {
		http.NotFound(w, r)
		return
	}

	if util.ValidateID(sub1) == "" || util.ValidateID(sub2) == "" || util.ValidateID(id) == "" {
		http.NotFound(w, r)
		return
	}

	authID := sub1 + sub2 + id

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	authPath := util.ID2Path(authID)
	self := s.URLs.Author + authPath + "/sequences"
	up := s.URLs.Author + authPath

	// nameindex: "author/{sub1}/{sub2}/{id}" -> reads index.json for author name
	nameIndex := "author/" + sub1 + "/" + sub2 + "/" + id
	nameIdxPtr := &nameIndex

	// index: "author/{sub1}/{sub2}/{id}/sequences" -> reads sequences.json
	// Python: index=URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/sequences"
	// => "author/" + sub1 + "/" + sub2 + "/" + id + "/sequences"
	// This reads {pages}/author/{sub1}/{sub2}/{id}/sequences.json
	idx := "author/" + sub1 + "/" + sub2 + "/" + id + "/sequences"

	params := SimpleListParams{
		Index:         idx,
		Self:          self,
		SimpleBaseRef: s.URLs.AuthIdx + sub1 + "/" + sub2,
		StrongBaseRef: s.URLs.Author + sub1 + "/" + sub2 + "/" + id + "/",
		SubTag:        "tag:author:" + authID,
		Subtitle:      s.LANG.BooksNum,
		Layout:        "name_id_list",
		UseNums:       boolPtr(true),
		Title:         s.LANG.SeqsAuthor,
		NameIndex:     nameIdxPtr,
		Up:            &up,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: authorSeqsHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// authorNonSeqHandler handles GET /opds/author/{sub1}/{sub2}/{id}/sequenceless
func (s *Server) authorNonSeqHandler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")
	id := Param(r, "id")

	if sub1 == "" || sub2 == "" || id == "" {
		http.NotFound(w, r)
		return
	}

	if util.ValidateID(sub1) == "" || util.ValidateID(sub2) == "" || util.ValidateID(id) == "" {
		http.NotFound(w, r)
		return
	}

	authID := sub1 + sub2 + id

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	authPath := util.ID2Path(authID)
	self := s.URLs.Author + authPath + "/sequenceless"
	up := s.URLs.Author + authPath

	// Python: index=URL["author"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}/"
	// => "author/" + sub1 + "/" + sub2 + "/" + id + "/"
	// opds_book_list with layout=author_nonseq reads: booksidx = index + "/all.json"
	// => {pages}/author/{sub1}/{sub2}/{id}/all.json
	idx := "author/" + sub1 + "/" + sub2 + "/" + id + "/"

	params := BookListParams{
		Index:   idx,
		Title:   s.LANG.BooksAuthorNonSeq,
		AuthRef: s.URLs.Author,
		SeqRef:  s.URLs.Seq,
		Layout:  "author_nonseq",
		Self:    self,
		Start:   s.URLs.Start,
		Up:      &up,
		SubTag:  "tag:author:" + authID,
		AppRoot: appRoot,
		URLs:    s.URLs,
		LANG:    s.LANG,
		CFG:     s.CFG,
	}

	feed, err := OpdsBookList(params)
	if err != nil {
		log.Printf("ERROR: authorNonSeqHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// authorAlphabetHandler handles GET /opds/author/{sub1}/{sub2}/{id}/alphabet
func (s *Server) authorAlphabetHandler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")
	id := Param(r, "id")

	if sub1 == "" || sub2 == "" || id == "" {
		http.NotFound(w, r)
		return
	}

	if util.ValidateID(sub1) == "" || util.ValidateID(sub2) == "" || util.ValidateID(id) == "" {
		http.NotFound(w, r)
		return
	}

	authID := sub1 + sub2 + id

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	authPath := util.ID2Path(authID)
	self := s.URLs.Author + authPath + "/alphabet"
	up := s.URLs.Author + authPath

	idx := "author/" + sub1 + "/" + sub2 + "/" + id + "/"

	params := BookListParams{
		Index:   idx,
		Title:   s.LANG.BooksAuthorAlpha,
		AuthRef: s.URLs.Author,
		SeqRef:  s.URLs.Seq,
		Layout:  "author_alpha",
		Self:    self,
		Start:   s.URLs.Start,
		Up:      &up,
		SubTag:  "tag:author:" + authID,
		AppRoot: appRoot,
		URLs:    s.URLs,
		LANG:    s.LANG,
		CFG:     s.CFG,
	}

	feed, err := OpdsBookList(params)
	if err != nil {
		log.Printf("ERROR: authorAlphabetHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// authorTimeHandler handles GET /opds/author/{sub1}/{sub2}/{id}/time
func (s *Server) authorTimeHandler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")
	id := Param(r, "id")

	if sub1 == "" || sub2 == "" || id == "" {
		http.NotFound(w, r)
		return
	}

	if util.ValidateID(sub1) == "" || util.ValidateID(sub2) == "" || util.ValidateID(id) == "" {
		http.NotFound(w, r)
		return
	}

	authID := sub1 + sub2 + id

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	authPath := util.ID2Path(authID)
	self := s.URLs.Author + authPath + "/time"
	up := s.URLs.Author + authPath

	idx := "author/" + sub1 + "/" + sub2 + "/" + id + "/"

	params := BookListParams{
		Index:   idx,
		Title:   s.LANG.BooksAuthorTime,
		AuthRef: s.URLs.Author,
		SeqRef:  s.URLs.Seq,
		Layout:  "author_time",
		Self:    self,
		Start:   s.URLs.Start,
		Up:      &up,
		SubTag:  "tag:author:" + authID,
		AppRoot: appRoot,
		URLs:    s.URLs,
		LANG:    s.LANG,
		CFG:     s.CFG,
	}

	feed, err := OpdsBookList(params)
	if err != nil {
		log.Printf("ERROR: authorTimeHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// authorSeqBooksHandler handles GET /opds/author/{sub1}/{sub2}/{id}/{seq_id}
func (s *Server) authorSeqBooksHandler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")
	id := Param(r, "id")
	seqID := Param(r, "seq_id")

	if sub1 == "" || sub2 == "" || id == "" || seqID == "" {
		http.NotFound(w, r)
		return
	}

	if util.ValidateID(sub1) == "" || util.ValidateID(sub2) == "" || util.ValidateID(id) == "" || util.ValidateID(seqID) == "" {
		http.NotFound(w, r)
		return
	}

	authID := sub1 + sub2 + id

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	authPath := util.ID2Path(authID)
	seqPath := util.ID2Path(seqID)
	self := s.URLs.Author + authPath + "/" + seqPath
	up := s.URLs.Author + authPath + "/sequences"

	idx := "author/" + sub1 + "/" + sub2 + "/" + id + "/"

	params := BookListParams{
		Index:   idx,
		Title:   s.LANG.BooksAuthorSeq,
		AuthRef: s.URLs.Author,
		SeqRef:  s.URLs.Seq,
		Layout:  "author_seq",
		SeqID:   &seqID,
		Self:    self,
		Start:   s.URLs.Start,
		Up:      &up,
		SubTag:  "tag:author:" + authID,
		AppRoot: appRoot,
		URLs:    s.URLs,
		LANG:    s.LANG,
		CFG:     s.CFG,
	}

	feed, err := OpdsBookList(params)
	if err != nil {
		log.Printf("ERROR: authorSeqBooksHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// --- Sequence Handlers (4.4) ---

// seqRootHandler handles GET /opds/sequencesindex/
func (s *Server) seqRootHandler(w http.ResponseWriter, r *http.Request) {
	appRoot := s.CFG.Get("APPLICATION_ROOT")

	// Python: index=URL["seqidx"].replace("/opds/", "", 1) => "sequencesindex/"
	// title=LANG["sequences"], subtitle=LANG["seq_root_subtitle"]
	// simple_baseref=URL["seqidx"], strong_baseref=URL["seq"]
	// up=URL["start"]
	up := s.URLs.Start

	params := SimpleListParams{
		Index:         "sequencesindex/",
		Self:          s.URLs.SeqIdx,
		SimpleBaseRef: s.URLs.SeqIdx,
		StrongBaseRef: s.URLs.Seq,
		SubTag:        "tag:sequences:",
		Subtitle:      s.LANG.SeqRootSubtitle,
		Title:         s.LANG.Sequences,
		Up:            &up,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: seqRootHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// seqSubHandler handles GET /opds/sequencesindex/{sub}
func (s *Server) seqSubHandler(w http.ResponseWriter, r *http.Request) {
	sub := Param(r, "sub")
	if sub == "" {
		s.seqRootHandler(w, r)
		return
	}

	subValid := util.ValidatePrefix(sub)
	if subValid == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	subEnc := url.QueryEscape(subValid)
	self := s.URLs.SeqIdx + subEnc
	up := s.URLs.SeqIdx

	useNums := true

	params := SimpleListParams{
		Index:         "sequencesindex/" + subValid,
		Self:          self,
		SimpleBaseRef: s.URLs.SeqIdx + subEnc + "/",
		StrongBaseRef: s.URLs.Seq,
		SubTag:        "tag:sequences:" + subValid + ":",
		Subtitle:      s.LANG.SeqsNum,
		Title:         s.LANG.SeqRootSubtitle + subValid,
		Layout:        "subs",
		UseNums:       &useNums,
		Up:            &up,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: seqSubHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// seqSub2Handler handles GET /opds/sequencesindex/{sub1}/{sub2}
func (s *Server) seqSub2Handler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")

	if sub1 == "" || sub2 == "" {
		s.seqSubHandler(w, r)
		return
	}

	sub1Valid := util.ValidatePrefix(sub1)
	sub2Valid := util.ValidatePrefix(sub2)
	if sub1Valid == "" || sub2Valid == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	sub1Enc := url.QueryEscape(sub1Valid)
	sub2Enc := url.QueryEscape(sub2Valid)
	self := s.URLs.SeqIdx + sub1Enc + "/" + sub2Enc
	up := s.URLs.SeqIdx + sub1Enc

	useID2Path := true
	params := SimpleListParams{
		Index:         "sequencesindex/" + sub1Valid + "/" + sub2Valid,
		Self:          self,
		SimpleBaseRef: s.URLs.SeqIdx + sub1Enc + "/" + sub2Enc + "/",
		StrongBaseRef: s.URLs.Seq,
		SubTag:        "tag:sequence:",
		Subtitle:      "'%s'",
		Title:         s.LANG.SeqRootSubtitle + sub2Valid,
		Layout:        "subs",
		UseID2Path:    &useID2Path,
		Up:            &up,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: seqSub2Handler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// sequenceBooksHandler handles GET /opds/sequence/{sub1}/{sub2}/{id}
func (s *Server) sequenceBooksHandler(w http.ResponseWriter, r *http.Request) {
	sub1 := Param(r, "sub1")
	sub2 := Param(r, "sub2")
	id := Param(r, "id")

	if sub1 == "" || sub2 == "" || id == "" {
		http.NotFound(w, r)
		return
	}

	// Python: validate_id on each part, then uses them directly
	// The ID in URL is already the full 32-char hash (not composed from sub1+sub2+id)
	if util.ValidateID(sub1) == "" || util.ValidateID(sub2) == "" || util.ValidateID(id) == "" {
		http.NotFound(w, r)
		return
	}

	// Python: index=URL["seq"].replace("/opds/", "", 1) + f"{sub1}/{sub2}/{id}"
	// => "sequence/" + sub1 + "/" + sub2 + "/" + id
	// title=LANG["seq_tpl"], layout="sequence"
	// simple_baseref=URL["seqidx"] + sub1 + "/" + sub2
	// strong_baseref=URL["seq"]
	// up=URL["seqidx"]
	appRoot := s.CFG.Get("APPLICATION_ROOT")
	seqPath := util.ID2Path(id)
	self := s.URLs.Seq + seqPath
	up := s.URLs.SeqIdx

	params := BookListParams{
		Index:   "sequence/" + sub1 + "/" + sub2 + "/" + id,
		Title:   s.LANG.SeqTpl,
		AuthRef: s.URLs.Author,
		SeqRef:  s.URLs.Seq,
		Layout:  "sequence",
		Self:    self,
		Start:   s.URLs.Start,
		Up:      &up,
		SubTag:  "tag:sequence:" + id,
		AppRoot: appRoot,
		URLs:    s.URLs,
		LANG:    s.LANG,
		CFG:     s.CFG,
	}

	feed, err := OpdsBookList(params)
	if err != nil {
		log.Printf("ERROR: sequenceBooksHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// --- Genre Handlers (4.5) ---

// genresRootHandler handles GET /opds/genresindex/
func (s *Server) genresRootHandler(w http.ResponseWriter, r *http.Request) {
	appRoot := s.CFG.Get("APPLICATION_ROOT")

	// Python: index=URL["genidx"].replace("/opds/", "", 1) => "genresindex/"
	// layout="key_value", title=LANG["genres_meta"], subtitle="%s"
	// simple_baseref=URL["genidx"], strong_baseref=URL["genidx"]
	// up=URL["start"]
	up := s.URLs.Start

	params := SimpleListParams{
		Index:         "genresindex/",
		Self:          s.URLs.GenIdx,
		SimpleBaseRef: s.URLs.GenIdx,
		StrongBaseRef: s.URLs.GenIdx,
		SubTag:        "tag:genresindex:",
		Subtitle:      "%s",
		Title:         s.LANG.GenresMeta,
		Layout:        "key_value",
		Up:            &up,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: genresRootHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// genresListHandler handles GET /opds/genresindex/{meta_id}
func (s *Server) genresListHandler(w http.ResponseWriter, r *http.Request) {
	metaID := Param(r, "meta_id")
	if metaID == "" {
		s.genresRootHandler(w, r)
		return
	}

	metaIDValid := util.ValidateGenre(metaID)
	if metaIDValid == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")

	metaName := getMetaName(metaIDValid)
	if metaName == "" {
		http.NotFound(w, r)
		return
	}

	self := s.URLs.GenIdx + metaIDValid
	startURL := s.URLs.Start

	params := SimpleListParams{
		Index:         "genresindex/" + metaIDValid,
		Self:          self,
		SimpleBaseRef: s.URLs.GenIdx,
		StrongBaseRef: s.URLs.Genre,
		SubTag:        "tag:genres:",
		Subtitle:      "%s",
		Title:         s.LANG.GenresRootSubtitle + metaName,
		Layout:        "key_value",
		Up:            &startURL,
		AppRoot:       appRoot,
		URLs:          s.URLs,
		LANG:          s.LANG,
		CFG:           s.CFG,
	}

	feed, err := OpdsSimpleList(params)
	if err != nil {
		log.Printf("ERROR: genresListHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// genreBooksHandler handles GET /opds/genre/{gen_id} (page=0)
func (s *Server) genreBooksHandler(w http.ResponseWriter, r *http.Request) {
	genID := Param(r, "gen_id")
	if genID == "" {
		http.NotFound(w, r)
		return
	}

	genIDValid := util.ValidateGenre(genID)
	if genIDValid == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	genreName := GetGenreName(genIDValid)

	self := s.URLs.Genre + genIDValid
	up := s.URLs.GenIdx

	params := BookListParams{
		Index:   "genre/" + genIDValid + "/",
		Title:   fmt.Sprintf(s.LANG.GenreTpl, genreName),
		AuthRef: s.URLs.Author,
		SeqRef:  s.URLs.Seq,
		Layout:  "paginated",
		Page:    0,
		Self:    self,
		Start:   s.URLs.Start,
		Up:      &up,
		SubTag:  "tag:genre:" + genIDValid,
		AppRoot: appRoot,
		URLs:    s.URLs,
		LANG:    s.LANG,
		CFG:     s.CFG,
	}

	feed, err := OpdsBookList(params)
	if err != nil {
		log.Printf("ERROR: genreBooksHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// genreBooksPageHandler handles GET /opds/genre/{gen_id}/{page}
func (s *Server) genreBooksPageHandler(w http.ResponseWriter, r *http.Request) {
	genID := Param(r, "gen_id")
	pageStr := Param(r, "page")

	if genID == "" {
		http.NotFound(w, r)
		return
	}

	genIDValid := util.ValidateGenre(genID)
	if genIDValid == "" {
		http.NotFound(w, r)
		return
	}

	page := 0
	if pageStr != "" {
		var err error
		page, err = strconv.Atoi(pageStr)
		if err != nil || page < 0 {
			page = 0
		}
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	genreName := GetGenreName(genIDValid)

	self := s.URLs.Genre + genIDValid + "/" + strconv.Itoa(page)
	up := s.URLs.GenIdx

	params := BookListParams{
		Index:   "genre/" + genIDValid + "/",
		Title:   fmt.Sprintf(s.LANG.GenreTpl, genreName),
		AuthRef: s.URLs.Author,
		SeqRef:  s.URLs.Seq,
		Layout:  "paginated",
		Page:    page,
		Self:    self,
		Start:   s.URLs.Start,
		Up:      &up,
		SubTag:  "tag:genre:" + genIDValid,
		AppRoot: appRoot,
		URLs:    s.URLs,
		LANG:    s.LANG,
		CFG:     s.CFG,
	}

	feed, err := OpdsBookList(params)
	if err != nil {
		log.Printf("ERROR: genreBooksPageHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	CreateOPDSResponseWithConfig(w, *feed, s.CFG)
}

// --- Meta genre names (local to opds.go) ---

// metaNamesMap maps meta_id -> meta_name
var metaNamesMap map[string]string = make(map[string]string)

// getMetaName returns the display name for a meta genre ID.
func getMetaName(metaID string) string {
	return metaNamesMap[metaID]
}

// LoadMetaNames loads meta genre names from genres_meta.list file.
// This must be called during initialization (separate from InitGenres in book_entry.go).
func LoadMetaNames(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	mm := make(map[string]string)
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "|", 2)
		if len(parts) >= 2 {
			// meta_id|meta_name
			mm[parts[0]] = parts[1]
		}
	}
	metaNamesMap = mm
	return nil
}

// --- Random Handlers (4.6) ---

// rndBooksHandler handles GET /opds/random-books/
func (s *Server) rndBooksHandler(w http.ResponseWriter, r *http.Request) {
	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   s.LANG.RndBooks,
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.RndBook,
		Tag:     "tag:random:books",
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	if s.Database == nil {
		CreateOPDSResponseWithConfig(w, feed, s.CFG)
		return
	}

	books, err := s.Database.GetRandomBooks(50)
	if err != nil {
		log.Printf("ERROR: rndBooksHandler DB: %v", err)
	} else {
		for _, book := range books {
			entry := MakeBookEntry(book, ts, appRoot, s.URLs, s.LANG, s.URLs.Author, s.URLs.Seq, nil)
			feed.Entries = append(feed.Entries, entry)
		}
	}

	cacheSeconds := 5
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_RND"), "%d", &cacheSeconds)
	CreateOPDSResponse(w, feed, cacheSeconds)
}

// rndSeqsHandler handles GET /opds/random-sequences/
func (s *Server) rndSeqsHandler(w http.ResponseWriter, r *http.Request) {
	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   s.LANG.RndSeqs,
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.RndSeq,
		Tag:     "tag:random:sequences",
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	if s.Database != nil {
		sequences, err := s.Database.GetRandomSequences(50)
		if err != nil {
			log.Printf("ERROR: rndSeqsHandler DB: %v", err)
		} else {
			for _, seq := range sequences {
				href := appRoot + s.URLs.Seq + util.ID2Path(seq.ID)
				feed.Entries = append(feed.Entries, model.OPDSEntry{
					Updated: ts,
					ID:      "tag:sequence:" + seq.ID,
					Title:   seq.Name,
					Links: []model.OPDSLink{
						{HRef: href, Type: "application/atom+xml;profile=opds-catalog"},
					},
					Content: &model.OPDSContent{Type: "text", Value: seq.Name},
				})
			}
		}
	}

	cacheSeconds := 5
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_RND"), "%d", &cacheSeconds)
	CreateOPDSResponse(w, feed, cacheSeconds)
}

// rndGenresRootHandler handles GET /opds/rnd/genresindex/
func (s *Server) rndGenresRootHandler(w http.ResponseWriter, r *http.Request) {
	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   s.LANG.GenresMeta,
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.RndGenIdx,
		Tag:     "tag:rnd:genres_meta",
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	if s.Database != nil {
		metaGenres, err := s.Database.GetGenresMeta()
		if err != nil {
			log.Printf("ERROR: rndGenresRootHandler DB: %v", err)
		} else {
			for _, mg := range metaGenres {
				href := appRoot + s.URLs.RndGenIdx + url.QueryEscape(mg.MetaID)
				feed.Entries = append(feed.Entries, model.OPDSEntry{
					Updated: ts,
					ID:      "tag:rnd:genres:meta:" + mg.MetaID,
					Title:   mg.Name,
					Links: []model.OPDSLink{
						{HRef: href, Type: "application/atom+xml;profile=opds-catalog"},
					},
					Content: &model.OPDSContent{Type: "text", Value: mg.Name},
				})
			}
		}
	}

	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// rndGenresListHandler handles GET /opds/rnd/genresindex/{meta_id}
func (s *Server) rndGenresListHandler(w http.ResponseWriter, r *http.Request) {
	metaID := Param(r, "meta_id")
	if metaID == "" {
		s.rndGenresRootHandler(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()
	self := s.URLs.RndGenIdx + url.QueryEscape(metaID)
	up := s.URLs.RndGenIdx

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   s.LANG.Genres,
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    self,
		Tag:     "tag:rnd:genres:meta:" + metaID,
		Up:      &up,
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	if s.Database != nil {
		genres, err := s.Database.GetGenresByMetaID(metaID)
		if err != nil {
			log.Printf("ERROR: rndGenresListHandler DB: %v", err)
		} else {
			for _, g := range genres {
				href := appRoot + s.URLs.RndGen + url.QueryEscape(g.ID)
				feed.Entries = append(feed.Entries, model.OPDSEntry{
					Updated: ts,
					ID:      "tag:rnd:genre:" + g.ID,
					Title:   g.Name,
					Links: []model.OPDSLink{
						{HRef: href, Type: "application/atom+xml;profile=opds-catalog"},
					},
					Content: &model.OPDSContent{Type: "text", Value: g.Name},
				})
			}
		}
	}

	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// rndBooksByGenreHandler handles GET /opds/rnd/genre/{gen_id}
func (s *Server) rndBooksByGenreHandler(w http.ResponseWriter, r *http.Request) {
	genID := Param(r, "gen_id")
	if genID == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	genreName := GetGenreName(genID)

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   fmt.Sprintf(s.LANG.RndGenreBooks, genreName),
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.RndGen + url.QueryEscape(genID),
		Tag:     "tag:rnd:genre:" + genID,
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	if s.Database != nil {
		books, err := s.Database.GetRandomBooksByGenre(genID, 50)
		if err != nil {
			log.Printf("ERROR: rndBooksByGenreHandler DB: %v", err)
		} else {
			for _, book := range books {
				entry := MakeBookEntry(book, ts, appRoot, s.URLs, s.LANG, s.URLs.Author, s.URLs.Seq, nil)
				feed.Entries = append(feed.Entries, entry)
			}
		}
	}

	cacheSeconds := 5
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_RND"), "%d", &cacheSeconds)
	CreateOPDSResponse(w, feed, cacheSeconds)
}

// --- Search Handlers (4.7) ---

// searchMainHandler handles GET /opds/search?searchTerm=
func (s *Server) searchMainHandler(w http.ResponseWriter, r *http.Request) {
	searchTerm := r.URL.Query().Get("searchTerm")
	feed := OpdsSearchMain(s.CFG, s.URLs, s.LANG, searchTerm)
	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// searchAuthorsHandler handles GET /opds/search/authors?searchTerm=
func (s *Server) searchAuthorsHandler(w http.ResponseWriter, r *http.Request) {
	searchTerm := r.URL.Query().Get("searchTerm")
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	searchTerm = util.ValidateSearch(searchTerm)
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   fmt.Sprintf(s.LANG.SearchAuthor, searchTerm),
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.SrchAuth,
		Tag:     "tag:search:authors:" + searchTerm,
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	maxRes := 500
	fmt.Sscanf(s.CFG.Get("MAX_SEARCH_RES"), "%d", &maxRes)

	if s.Database != nil {
		authors, err := s.Database.SearchAuthors(searchTerm, maxRes)
		if err != nil {
			log.Printf("ERROR: searchAuthorsHandler DB: %v", err)
		} else {
			for _, author := range authors {
				href := appRoot + s.URLs.Author + util.ID2Path(author.ID)
				feed.Entries = append(feed.Entries, model.OPDSEntry{
					Updated: ts,
					ID:      "tag:author:" + author.ID,
					Title:   author.Name,
					Links: []model.OPDSLink{
						{HRef: href, Type: "application/atom+xml;profile=opds-catalog"},
					},
					Content: &model.OPDSContent{Type: "text", Value: author.Name},
				})
			}
		}
	}

	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// searchSequencesHandler handles GET /opds/search/sequences?searchTerm=
func (s *Server) searchSequencesHandler(w http.ResponseWriter, r *http.Request) {
	searchTerm := r.URL.Query().Get("searchTerm")
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	searchTerm = util.ValidateSearch(searchTerm)
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   fmt.Sprintf(s.LANG.SearchSeq, searchTerm),
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.SrchSeq,
		Tag:     "tag:search:sequences:" + searchTerm,
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	maxRes := 500
	fmt.Sscanf(s.CFG.Get("MAX_SEARCH_RES"), "%d", &maxRes)

	if s.Database != nil {
		sequences, err := s.Database.SearchSequences(searchTerm, maxRes)
		if err != nil {
			log.Printf("ERROR: searchSequencesHandler DB: %v", err)
		} else {
			for _, seq := range sequences {
				href := appRoot + s.URLs.Seq + util.ID2Path(seq.ID)
				feed.Entries = append(feed.Entries, model.OPDSEntry{
					Updated: ts,
					ID:      "tag:sequence:" + seq.ID,
					Title:   seq.Name,
					Links: []model.OPDSLink{
						{HRef: href, Type: "application/atom+xml;profile=opds-catalog"},
					},
					Content: &model.OPDSContent{Type: "text", Value: seq.Name},
				})
			}
		}
	}

	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// searchBooksHandler handles GET /opds/search/books?searchTerm=
func (s *Server) searchBooksHandler(w http.ResponseWriter, r *http.Request) {
	searchTerm := r.URL.Query().Get("searchTerm")
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	searchTerm = util.ValidateSearch(searchTerm)
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	maxRes := 500
	fmt.Sscanf(s.CFG.Get("MAX_SEARCH_RES"), "%d", &maxRes)

	if s.Database == nil {
		feed := OpdsHeader(OpdsHeaderParams{
			Title:   fmt.Sprintf(s.LANG.SearchBook, searchTerm),
			Ts:      ts,
			Start:   s.URLs.Start,
			Self:    s.URLs.SrchBook,
			Tag:     "tag:search:books:" + searchTerm,
			AppRoot: appRoot,
			URLs:    s.URLs,
		})
		CreateOPDSResponseWithConfig(w, feed, s.CFG)
		return
	}

	books, err := s.Database.SearchBooksByTitle(searchTerm, maxRes)
	if err != nil {
		log.Printf("ERROR: searchBooksHandler DB: %v", err)
	}

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   fmt.Sprintf(s.LANG.SearchBook, searchTerm),
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.SrchBook,
		Tag:     "tag:search:books:" + searchTerm,
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	for _, book := range books {
		entry := MakeBookEntry(book, ts, appRoot, s.URLs, s.LANG, s.URLs.Author, s.URLs.Seq, nil)
		feed.Entries = append(feed.Entries, entry)
	}

	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// searchBooksAnnoHandler handles GET /opds/search/booksanno?searchTerm=
func (s *Server) searchBooksAnnoHandler(w http.ResponseWriter, r *http.Request) {
	searchTerm := r.URL.Query().Get("searchTerm")
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	searchTerm = util.ValidateSearch(searchTerm)
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	maxRes := 500
	fmt.Sscanf(s.CFG.Get("MAX_SEARCH_RES"), "%d", &maxRes)

	if s.Database == nil {
		feed := OpdsHeader(OpdsHeaderParams{
			Title:   fmt.Sprintf(s.LANG.SearchAnno, searchTerm),
			Ts:      ts,
			Start:   s.URLs.Start,
			Self:    s.URLs.SrchBookAnno,
			Tag:     "tag:search:booksanno:" + searchTerm,
			AppRoot: appRoot,
			URLs:    s.URLs,
		})
		CreateOPDSResponseWithConfig(w, feed, s.CFG)
		return
	}

	books, err := s.Database.SearchBooksByAnnotation(searchTerm, maxRes)
	if err != nil {
		log.Printf("ERROR: searchBooksAnnoHandler DB: %v", err)
	}

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   fmt.Sprintf(s.LANG.SearchAnno, searchTerm),
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.SrchBookAnno,
		Tag:     "tag:search:booksanno:" + searchTerm,
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	for _, book := range books {
		entry := MakeBookEntry(book, ts, appRoot, s.URLs, s.LANG, s.URLs.Author, s.URLs.Seq, nil)
		feed.Entries = append(feed.Entries, entry)
	}

	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// searchBooksAnnoVectorHandler handles GET /opds/search/booksannovector?searchTerm=
func (s *Server) searchBooksAnnoVectorHandler(w http.ResponseWriter, r *http.Request) {
	searchTerm := r.URL.Query().Get("searchTerm")
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	searchTerm = util.ValidateSearch(searchTerm)
	if searchTerm == "" {
		http.NotFound(w, r)
		return
	}

	if s.CFG.Get("VECTOR_SEARCH") != "true" && s.CFG.Get("VECTOR_SEARCH") != "yes" {
		http.NotFound(w, r)
		return
	}

	appRoot := s.CFG.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	if s.Database == nil {
		feed := OpdsHeader(OpdsHeaderParams{
			Title:   fmt.Sprintf(s.LANG.SearchAnnoVector, searchTerm),
			Ts:      ts,
			Start:   s.URLs.Start,
			Self:    s.URLs.SrchBookAnnoVector,
			Tag:     "tag:search:booksannovector:" + searchTerm,
			AppRoot: appRoot,
			URLs:    s.URLs,
		})
		CreateOPDSResponseWithConfig(w, feed, s.CFG)
		return
	}

	// Get embedding vector
	vector := util.GetVector(s.CFG, searchTerm)
	if vector == nil {
		log.Printf("ERROR: GetVector returned nil for: %s", searchTerm)
		http.Error(w, "Vector error", http.StatusInternalServerError)
		return
	}

	// Get nearest book IDs
	bookIDs, err := s.Database.GetNearestIDs(vector, 500)
	if err != nil {
		log.Printf("ERROR: GetNearestIDs: %v", err)
		http.Error(w, "DB error", http.StatusInternalServerError)
		return
	}

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   fmt.Sprintf(s.LANG.SearchAnnoVector, searchTerm),
		Ts:      ts,
		Start:   s.URLs.Start,
		Self:    s.URLs.SrchBookAnnoVector,
		Tag:     "tag:search:booksannovector:" + searchTerm,
		AppRoot: appRoot,
		URLs:    s.URLs,
	})

	// Fetch book details by IDs
	books, err := s.Database.GetBooksByIDs(bookIDs)
	if err != nil {
		log.Printf("ERROR: GetBooksByIDs: %v", err)
	}

	for _, book := range books {
		entry := MakeBookEntry(book, ts, appRoot, s.URLs, s.LANG, s.URLs.Author, s.URLs.Seq, nil)
		feed.Entries = append(feed.Entries, entry)
	}

	CreateOPDSResponseWithConfig(w, feed, s.CFG)
}

// --- Helper functions ---

func strPtr(s string) *string {
	return &s
}

func boolPtr(b bool) *bool {
	return &b
}
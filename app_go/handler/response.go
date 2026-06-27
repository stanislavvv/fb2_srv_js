// Package handler provides OPDS response generation functions.
package handler

import (
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"sort"

	"fb2srv_go/config"
	"fb2srv_go/db"
	"fb2srv_go/model"
	"fb2srv_go/util"
)

// --- Parameter structs ---

// OpdsHeaderParams holds parameters for building an OPDS feed header.
type OpdsHeaderParams struct {
	Title    string
	Ts       string
	Start    string
	Self     string
	Tag      string
	Up       *string // optional
	Prev     *string // optional
	Next     *string // optional
	AppRoot  string
	URLs     *config.URL
	AppICO   string // icon path from CONFIG["APP_ICO"]
}

// SimpleListParams holds parameters for opdsSimpleList.
type SimpleListParams struct {
	Index         string
	Self          string
	SimpleBaseRef string
	StrongBaseRef string
	SubTag        string
	Subtitle      string
	Title         string
	NameIndex     *string // optional
	UseNums       *bool   // optional
	UseID2Path    *bool   // optional: if true, apply ID2Path to keys in SimpleBaseRef entries
	Layout        string  // "name_id_list", "key_value", "subs", or "" for default
	Up            *string // optional up link
	AppRoot       string
	URLs          *config.URL
	LANG          *config.LANG
	CFG           *config.Config
}

// AuthorPageParams holds parameters for opdsAuthorPage.
type AuthorPageParams struct {
	Sub1    string
	Sub2    string
	AuthID  string
	Index   string
	SubTag  string
	Title   string
	Self    string
	Start   string
	Up      *string // optional up link
	AppRoot string
	URLs    *config.URL
	LANG    *config.LANG
	CFG     *config.Config
}

// BookListParams holds parameters for opdsBookList.
type BookListParams struct {
	Index      string
	Title      string
	AuthRef    string
	SeqRef     string
	Layout     string // "author_seq", "author_alpha", "author_time", "author_nonseq", "sequence", "paginated"
	Page       int    // for paginated layout
	SeqID      *string // for author_seq layout
	Self       string
	Start      string
	Up         *string // optional
	Prev       *string // optional
	Next       *string // optional
	SubTag     string
	AppRoot    string
	URLs       *config.URL
	LANG       *config.LANG
	CFG        *config.Config
}

// BooksDBParams holds parameters for opdsBooksDB (DB-based book lists).
type BooksDBParams struct {
	Title   string
	Self    string
	Start   string
	Up      *string // optional
	Prev    *string // optional
	Next    *string // optional
	Tag     string
	Offset  int
	Limit   int
	AuthRef string
	SeqRef  string
	AppRoot string
	URLs    *config.URL
	LANG    *config.LANG
	CFG     *config.Config
}

// SimpleListDBParams holds parameters for opdsSimpleListDB (DB-based author/sequence lists).
type SimpleListDBParams struct {
	Title     string
	Self      string
	Start     string
	Tag       string
	Search    string // if set, perform search instead of list
	Limit     int
	AppRoot   string
	URLs      *config.URL
	LANG      *config.LANG
	CFG       *config.Config
	ListType  string // "authors" or "sequences"
}

// --- OpdsHeader ---

// OpdsHeader builds the base OPDS feed structure with standard links.
func OpdsHeader(params OpdsHeaderParams) model.OPDSFeed {
	feed := model.OPDSFeed{
		XMLName:     "feed",
		XMLNS:       "http://www.w3.org/2005/Atom",
		XMLNSdc:     "http://purl.org/dc/terms/",
		XMLNSos:     "http://a9.com/-/spec/opensearch/1.1/",
		XMLNSopds:   "http://opds-spec.org/2010/catalog",
		ID:          params.Tag,
		Title:       params.Title,
		Updated:     params.Ts,
		Icon:        params.AppRoot + params.AppICO,
		Links: []model.OPDSLink{
			{
				HRef: params.AppRoot + params.URLs.Search + "?searchTerm={searchTerms}",
				Rel:  "search",
				Type: "application/atom+xml",
			},
			{
				HRef: params.AppRoot + params.Start,
				Rel:  "start",
				Type: "application/atom+xml;profile=opds-catalog",
			},
			{
				HRef: params.AppRoot + params.Self,
				Rel:  "self",
				Type: "application/atom+xml;profile=opds-catalog",
			},
		},
		Entries: []model.OPDSEntry{},
	}

	if params.Up != nil && *params.Up != "" {
		feed.Links = append(feed.Links, model.OPDSLink{
			HRef: params.AppRoot + *params.Up,
			Rel:  "up",
			Type: "application/atom+xml;profile=opds-catalog",
		})
	}
	if params.Prev != nil && *params.Prev != "" {
		feed.Links = append(feed.Links, model.OPDSLink{
			HRef: params.AppRoot + *params.Prev,
			Rel:  "prev",
			Type: "application/atom+xml;profile=opds-catalog",
		})
	}
	if params.Next != nil && *params.Next != "" {
		feed.Links = append(feed.Links, model.OPDSLink{
			HRef: params.AppRoot + *params.Next,
			Rel:  "next",
			Type: "application/atom+xml;profile=opds-catalog",
		})
	}

	return feed
}

// --- OpdsMain ---

// OpdsMain builds the library root OPDS page with navigation entries.
func OpdsMain(cfg *config.Config, urls *config.URL, lang *config.LANG) model.OPDSFeed {
	appRoot := cfg.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   cfg.Get("TITLE"),
		Ts:      ts,
		Start:   urls.Start,
		Self:    urls.Start,
		Tag:     "tag:root",
		AppRoot: appRoot,
		AppICO:  cfg.Get("APP_ICO"),
		URLs:    urls,
	})

	feed.Entries = []model.OPDSEntry{
		navEntry(ts, "tag:root:time", lang.TitleTime, appRoot+urls.Time),
		navEntry(ts, "tag:root:authors", lang.TitleAuthors, appRoot+urls.AuthIdx),
		navEntry(ts, "tag:root:sequences", lang.TitleSequences, appRoot+urls.SeqIdx),
		navEntry(ts, "tag:root:genre", lang.TitleGenres, appRoot+urls.GenIdx),
		navEntry(ts, "tag:root:random:books", lang.TitleRndBooks, appRoot+urls.RndBook),
		navEntry(ts, "tag:root:random:sequences", lang.TitleRndSeqs, appRoot+urls.RndSeq),
		navEntry(ts, "tag:root:random:genres", lang.TitleRndGenre, appRoot+urls.RndGenIdx),
	}

	return feed
}

// navEntry creates a simple navigation entry.
func navEntry(ts, id, title, href string) model.OPDSEntry {
	return model.OPDSEntry{
		Updated: ts,
		ID:      id,
		Title:   title,
		Links: []model.OPDSLink{
			{
				HRef: href,
				Type: "application/atom+xml;profile=opds-catalog",
			},
		},
		Content: &model.OPDSContent{
			Type:  "text",
			Value: title,
		},
	}
}

// --- OpdsSearchMain ---

// OpdsSearchMain builds the search root page with links to sub-searches.
func OpdsSearchMain(cfg *config.Config, urls *config.URL, lang *config.LANG, searchTerm string) model.OPDSFeed {
	appRoot := cfg.Get("APPLICATION_ROOT")
	ts := GetDTISO()

	tag := "tag:search"
	if searchTerm != "" {
		tag = tag + url.QueryEscape(searchTerm)
	}

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   fmt.Sprintf(lang.SearchMain, searchTerm),
		Ts:      ts,
		Start:   urls.Start,
		Self:    urls.Start,
		Tag:     tag,
		AppRoot: appRoot,
		AppICO:  cfg.Get("APP_ICO"),
		URLs:    urls,
	})

	if searchTerm == "" {
		return feed
	}

	encodedTerm := util.URLStr(searchTerm)

	feed.Entries = []model.OPDSEntry{
		navEntry(ts, "tag:search:authors:", lang.SchMainAuthor,
			appRoot+urls.SrchAuth+"?searchTerm="+encodedTerm),
		navEntry(ts, "tag:search:sequences:", lang.SchMainSeq,
			appRoot+urls.SrchSeq+"?searchTerm="+encodedTerm),
		navEntry(ts, "tag:search:booktitles:", lang.SchMainBook,
			appRoot+urls.SrchBook+"?searchTerm="+encodedTerm),
		navEntry(ts, "tag:search:bookanno:", lang.SchMainAnno,
			appRoot+urls.SrchBookAnno+"?searchTerm="+encodedTerm),
	}

	// Add vector search if enabled
	if cfg.Get("VECTOR_SEARCH") == "true" || cfg.Get("VECTOR_SEARCH") == "yes" || cfg.Get("VECTOR_SEARCH") == "YES" {
		feed.Entries = append(feed.Entries,
			navEntry(ts, "tag:search:bookannovector:", lang.SchMainAnnoVector,
				appRoot+urls.SrchBookAnnoVector+"?searchTerm="+encodedTerm))
	}

	return feed
}

// --- OpdsSimpleList ---

// OpdsSimpleList builds an OPDS feed from a JSON index file.
func OpdsSimpleList(params SimpleListParams) (*model.OPDSFeed, error) {
	pagesDir := params.CFG.Get("PAGES")
	ts := GetDTISO()

	// Determine index file path
	indexFile := ""
	simpleLinks := true

	path1 := pagesDir + "/" + params.Index + "/index.json"
	if _, err := os.Stat(path1); err == nil {
		indexFile = path1
		simpleLinks = true
	} else {
		path2 := pagesDir + "/" + params.Index + ".json"
		if _, err := os.Stat(path2); err == nil {
			indexFile = path2
			simpleLinks = false
		} else {
			return nil, fmt.Errorf("index file not found for %s", params.Index)
		}
	}

	// Load nameindex if provided
	var nameData map[string]interface{}
	if params.NameIndex != nil && *params.NameIndex != "" {
		nameIndexFile := pagesDir + "/" + *params.NameIndex + "/index.json"
		data, err := os.ReadFile(nameIndexFile)
		if err != nil {
			return nil, fmt.Errorf("nameindex file not found: %v", err)
		}
		if err := json.Unmarshal(data, &nameData); err != nil {
			return nil, fmt.Errorf("nameindex parse error: %v", err)
		}
	}

	// Load index data
	data, err := os.ReadFile(indexFile)
	if err != nil {
		return nil, fmt.Errorf("index read error: %v", err)
	}

	// Determine layout type
	var indexMap map[string]interface{}
	var indexList []map[string]interface{}
	isListFormat := false

	if params.Layout == "name_id_list" {
		if err := json.Unmarshal(data, &indexList); err != nil {
			return nil, fmt.Errorf("index parse error (name_id_list): %v", err)
		}
		isListFormat = true
	} else if params.Layout == "key_value" {
		if err := json.Unmarshal(data, &indexMap); err != nil {
			return nil, fmt.Errorf("index parse error (key_value): %v", err)
		}
	} else {
		// Default: try to detect format
		// First try as list (array of objects with name/id fields)
		if err := json.Unmarshal(data, &indexList); err == nil && len(indexList) > 0 {
			// Check if first element has "name" field (indicates name_id_list format)
			if _, hasName := indexList[0]["name"]; hasName {
				isListFormat = true
			} else {
				// Not a name_id_list, try as map
				if err := json.Unmarshal(data, &indexMap); err != nil {
					return nil, fmt.Errorf("index parse error: %v", err)
				}
			}
		} else {
			// Not a list, try as map
			if err := json.Unmarshal(data, &indexMap); err != nil {
				return nil, fmt.Errorf("index parse error: %v", err)
			}
		}
	}

	// Build title with nameindex
	title := params.Title
	if params.NameIndex != nil && nameData != nil {
		if name, ok := nameData["name"]; ok {
			title = fmt.Sprintf(title, name)
		}
	}

	// Build feed
	up := params.Up
	if up == nil {
		val := params.Self
		up = &val
	}
	feed := OpdsHeader(OpdsHeaderParams{
		Title:   title,
		Ts:      ts,
		Start:   params.URLs.Start,
		Self:    params.Self,
		Tag:     params.SubTag,
		Up:      up,
		AppRoot: params.AppRoot,
		AppICO:  params.CFG.Get("APP_ICO"),
		URLs:    params.URLs,
	})

	// Build entries based on layout
	if params.Layout == "name_id_list" || isListFormat {
		feed.Entries = buildNameIDListEntries(ts, params, indexList)
	} else if params.Layout == "key_value" {
		feed.Entries = buildKeyValueEntries(ts, params, indexMap)
	} else if simpleLinks {
		feed.Entries = buildSimpleMapEntries(ts, params, indexMap)
	} else {
		feed.Entries = buildKeyValueEntries(ts, params, indexMap)
	}

	return &feed, nil
}

// buildNameIDListEntries builds entries from a list of {name, id, ...} objects.
func buildNameIDListEntries(ts string, params SimpleListParams, indexList []map[string]interface{}) []model.OPDSEntry {
	// Collect items and sort by name
	type nameItem struct {
		key  string
		name string
		cnt  int
	}
	var items []nameItem
	for _, item := range indexList {
		name, _ := item["name"].(string)
		id, _ := item["id"].(string)
		cnt := 0
		if c, ok := item["cnt"]; ok {
			cnt = int(c.(float64))
		}
		items = append(items, nameItem{key: id, name: name, cnt: cnt})
	}

	// Sort by name using custom alphabet
	sort.Slice(items, func(i, j int) bool {
		cmp := util.CustomAlphabetCmp(items[i].name, items[j].name)
		return cmp < 0
	})

	useNums := params.UseNums != nil && *params.UseNums
	entries := make([]model.OPDSEntry, 0, len(items))
	for _, item := range items {
		var title, text string
		if useNums {
			title = item.name
			text = fmt.Sprintf(params.Subtitle, item.cnt)
		} else {
			title = item.name
			text = item.name
		}
		// Python: url_str(item['id']) then ID2Path for the directory structure
		idPath := util.ID2Path(item.key)
		encKey := util.URLStr(idPath)
		href := params.AppRoot + params.StrongBaseRef + encKey
		entries = append(entries, model.OPDSEntry{
			Updated: ts,
			ID:      params.SubTag + encKey,
			Title:   title,
			Links: []model.OPDSLink{
				{HRef: href, Type: "application/atom+xml;profile=opds-catalog"},
			},
			Content: &model.OPDSContent{Type: "text", Value: text},
		})
	}
	return entries
}

// buildKeyValueEntries builds entries from a {key: value} map, sorted by value.
func buildKeyValueEntries(ts string, params SimpleListParams, indexMap map[string]interface{}) []model.OPDSEntry {
	type kvItem struct {
		key   string
		value string
	}
	var items []kvItem
	for k, v := range indexMap {
		items = append(items, kvItem{key: k, value: fmt.Sprintf("%v", v)})
	}

	sort.Slice(items, func(i, j int) bool {
		cmp := util.CustomAlphabetCmp(items[i].value, items[j].value)
		return cmp < 0
	})

	useID2Path := params.UseID2Path != nil && *params.UseID2Path
	entries := make([]model.OPDSEntry, 0, len(items))
	for _, item := range items {
		var keyForLink string
		if useID2Path {
			// ID is hex+slash from ID2Path, no escaping needed
			keyForLink = util.ID2Path(item.key)
		} else {
			// Non-ID key may need escaping
			keyForLink = util.URLPathEncode(item.key)
		}
		href := params.AppRoot + params.StrongBaseRef + keyForLink
		entries = append(entries, model.OPDSEntry{
			Updated: ts,
			ID:      params.SubTag + keyForLink,
			Title:   item.value,
			Links: []model.OPDSLink{
				{HRef: href, Type: "application/atom+xml;profile=opds-catalog"},
			},
			Content: &model.OPDSContent{Type: "text", Value: item.value},
		})
	}
	return entries
}

// buildSimpleMapEntries builds entries from a {key: value} map, sorted by key.
// Note: SimpleBaseRef passed from handlers already contains URL-encoded path segments,
// so the key (sub letters) is appended directly without additional encoding.
func buildSimpleMapEntries(ts string, params SimpleListParams, indexMap map[string]interface{}) []model.OPDSEntry {
	type kvItem struct {
		key   string
		value string
	}
	var items []kvItem
	for k, v := range indexMap {
		items = append(items, kvItem{key: k, value: fmt.Sprintf("%v", v)})
	}

	sort.Slice(items, func(i, j int) bool {
		cmp := util.CustomAlphabetCmp(items[i].key, items[j].key)
		return cmp < 0
	})

	useNums := params.UseNums != nil && *params.UseNums
	useID2Path := params.UseID2Path != nil && *params.UseID2Path
	entries := make([]model.OPDSEntry, 0, len(items))
	for _, item := range items {
		var title, text string
		if useNums {
			title = item.key
			text = fmt.Sprintf(params.Subtitle, item.value)
		} else {
			title = item.key
			text = item.key
		}
		// SimpleBaseRef already has URL-encoded path; append key
		var keyForLink string
		if useID2Path {
			// ID is hex+slash from ID2Path, no escaping needed
			keyForLink = util.ID2Path(item.key)
		} else {
			// Non-ID key may need escaping
			keyForLink = util.URLPathEncode(item.key)
		}
		href := params.AppRoot + params.SimpleBaseRef + keyForLink
		entries = append(entries, model.OPDSEntry{
			Updated: ts,
			ID:      params.SubTag + keyForLink,
			Title:   title,
			Links: []model.OPDSLink{
				{HRef: href, Type: "application/atom+xml;profile=opds-catalog"},
			},
			Content: &model.OPDSContent{Type: "text", Value: text},
		})
	}
	return entries
}

// --- OpdsAuthorPage ---

// OpdsAuthorPage builds the main author page with bio entry and navigation links.
func OpdsAuthorPage(params AuthorPageParams) (*model.OPDSFeed, error) {
	pagesDir := params.CFG.Get("PAGES")
	ts := GetDTISO()

	indexFile := pagesDir + "/" + params.Index + "/index.json"
	data, err := os.ReadFile(indexFile)
	if err != nil {
		return nil, fmt.Errorf("author index file not found: %v", err)
	}

	var authData map[string]interface{}
	if err := json.Unmarshal(data, &authData); err != nil {
		return nil, fmt.Errorf("author index parse error: %v", err)
	}

	authName, _ := authData["name"].(string)
	title := fmt.Sprintf(params.Title, authName)

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   title,
		Ts:      ts,
		Start:   params.Start,
		Self:    params.Self,
		Tag:     params.SubTag,
		Up:      params.Up,
		AppRoot: params.AppRoot,
		AppICO:  params.CFG.Get("APP_ICO"),
		URLs:    params.URLs,
	})

	authPath := util.ID2Path(params.AuthID)
	seqFacetRel := "http://www.feedbooks.com/opds/facet"

	feed.Entries = []model.OPDSEntry{
		{
			Updated: ts,
			ID:      "tag:author:bio:" + params.AuthID,
			Title:   "Об авторе",
			Links: []model.OPDSLink{
				{
					HRef:  params.AppRoot + params.URLs.Author + authPath + "/sequences",
					Rel:   seqFacetRel,
					Title: params.LANG.BooksSeq,
					Type:  "application/atom+xml;profile=opds-catalog",
				},
				{
					HRef:  params.AppRoot + params.URLs.Author + authPath + "/sequenceless",
					Rel:   seqFacetRel,
					Title: params.LANG.BooksNonSeq,
					Type:  "application/atom+xml;profile=opds-catalog",
				},
			},
			Content: &model.OPDSContent{
				Type:  "text/html",
				Value: "<p><span style=\"font-weight:bold\">" + authName + "</span></p>",
			},
		},
		navEntry(ts, params.SubTag+":sequences", params.LANG.BooksSeq,
			params.AppRoot+params.URLs.Author+authPath+"/sequences"),
		navEntry(ts, params.SubTag+":sequenceless", params.LANG.BooksNonSeq,
			params.AppRoot+params.URLs.Author+authPath+"/sequenceless"),
		navEntry(ts, params.SubTag+":alphabet", params.LANG.BooksAlphabet,
			params.AppRoot+params.URLs.Author+authPath+"/alphabet"),
		navEntry(ts, params.SubTag+":time", params.LANG.BooksTime,
			params.AppRoot+params.URLs.Author+authPath+"/time"),
	}

	return &feed, nil
}

// --- OpdsBookList ---

// OpdsBookList builds an OPDS feed of books from a JSON file.
func OpdsBookList(params BookListParams) (*model.OPDSFeed, error) {
	pagesDir := params.CFG.Get("PAGES")
	ts := GetDTISO()

	var booksFile string
	var booksData []model.Book
	var title string = params.Title

	switch params.Layout {
	case "author_seq", "author_alpha", "author_time", "author_nonseq":
		booksFile = pagesDir + "/" + params.Index + "all.json"
		// Read author name
		authFile := pagesDir + "/" + params.Index + "index.json"
		if authData, err := os.ReadFile(authFile); err == nil {
			var authInfo map[string]interface{}
			if json.Unmarshal(authData, &authInfo) == nil {
				if name, ok := authInfo["name"].(string); ok {
					switch params.Layout {
					case "author_seq":
						// Need seq name too
						seqFile := pagesDir + "/" + params.Index + "sequences.json"
						if seqData, err := os.ReadFile(seqFile); err == nil && params.SeqID != nil {
							var seqList []map[string]interface{}
							if json.Unmarshal(seqData, &seqList) == nil {
								for _, s := range seqList {
									if sid, ok := s["id"].(string); ok && sid == *params.SeqID {
										if sname, ok := s["name"].(string); ok {
											title = fmt.Sprintf(params.LANG.BooksAuthorSeq, sname, name)
										}
										break
									}
								}
							}
						}
					case "author_alpha", "author_nonseq", "author_time":
						title = fmt.Sprintf(title, name)
					}
				}
			}
		}
	case "sequence":
		booksFile = pagesDir + "/" + params.Index + ".json"
	case "paginated":
		booksFile = pagesDir + "/" + params.Index + fmt.Sprintf("%d.json", params.Page)
	default:
		booksFile = pagesDir + "/" + params.Index + ".json"
	}

	// Check file existence
	if _, err := os.Stat(booksFile); os.IsNotExist(err) {
		// For paginated: if page doesn't exist but page > 0, return empty with prev
		if params.Layout == "paginated" && params.Page > 0 {
			baseID := ""
			// Extract base ID from index
			for _, ch := range params.Index {
				if ch == '/' {
					break
				}
				baseID += string(ch)
			}
			prev := params.AppRoot + params.Self[:len(params.Self)-len(fmt.Sprintf("%d", params.Page))] + fmt.Sprintf("%d", params.Page-1)
			// Simplified prev link
			params.Prev = &prev
			feed := OpdsHeader(OpdsHeaderParams{
				Title:   title,
				Ts:      ts,
				Start:   params.Start,
				Self:    params.Self,
				Tag:     params.SubTag,
				Prev:    params.Prev,
				AppRoot: params.AppRoot,
				AppICO:  params.CFG.Get("APP_ICO"),
				URLs:    params.URLs,
			})
			return &feed, nil
		}
		return nil, fmt.Errorf("books file not found: %s", booksFile)
	}

	data, err := os.ReadFile(booksFile)
	if err != nil {
		return nil, fmt.Errorf("books file read error: %v", err)
	}

	// Determine seq_id based on layout
	// For "author_seq": seq_id from params.SeqID (passed from handler)
	// For "sequence": seq_id from JSON file (extracted below)
	seqIDStr := ""
	if params.Layout == "author_seq" && params.SeqID != nil {
		seqIDStr = *params.SeqID
	}

	// Parse books
	if params.Layout == "sequence" {
		// Sequence format: {name: ..., id: ..., books: [...]}
		var seqInfo struct {
			Name  string       `json:"name"`
			ID    string       `json:"id"`
			Books []model.Book `json:"books"`
		}
		if err := json.Unmarshal(data, &seqInfo); err != nil {
			return nil, fmt.Errorf("sequence books parse error: %v", err)
		}
		title = fmt.Sprintf(params.Title, seqInfo.Name)
		booksData = seqInfo.Books
		// Extract seq_id from JSON (same as Python: seq_id = data["id"])
		seqIDStr = seqInfo.ID
	} else {
		if err := json.Unmarshal(data, &booksData); err != nil {
			return nil, fmt.Errorf("books parse error: %v", err)
		}
	}

	sortedBooks := sortBooksByLayout(booksData, params.Layout, seqIDStr)

	// Build feed
	self := params.Self
	feed := OpdsHeader(OpdsHeaderParams{
		Title:   title,
		Ts:      ts,
		Start:   params.Start,
		Self:    self,
		Tag:     params.SubTag,
		Prev:    params.Prev,
		Next:    params.Next,
		AppRoot: params.AppRoot,
		AppICO:  params.CFG.Get("APP_ICO"),
		URLs:    params.URLs,
	})

	// Build book entries
	for _, book := range sortedBooks {
		seqIDPtr := &seqIDStr
		if params.Layout != "sequence" && params.Layout != "author_seq" {
			seqIDPtr = nil
		}
		entry := MakeBookEntry(book, ts, params.AppRoot, params.URLs, params.LANG, params.AuthRef, params.SeqRef, seqIDPtr)
		feed.Entries = append(feed.Entries, entry)
	}

	return &feed, nil
}

// sortBooksByLayout sorts books according to the specified layout.
func sortBooksByLayout(books []model.Book, layout string, seqID string) []model.Book {
	switch layout {
	case "author_seq":
		// Presort by title, then filter by seq and sort by seq_num
		sorted := make([]model.Book, 0, len(books))
		for _, book := range books {
			if book.Sequences != nil {
				for _, s := range book.Sequences {
					if s.ID == seqID {
						// Add seq_num as a temporary field
						num := -1
						if s.Num != nil {
							num = *s.Num
						}
						book.Sequences[0].Num = &num
						sorted = append(sorted, book)
						break
					}
				}
			}
		}
		sort.Slice(sorted, func(i, j int) bool {
			numI := -1
			numJ := -1
			if len(sorted[i].Sequences) > 0 && sorted[i].Sequences[0].Num != nil {
				numI = *sorted[i].Sequences[0].Num
			}
			if len(sorted[j].Sequences) > 0 && sorted[j].Sequences[0].Num != nil {
				numJ = *sorted[j].Sequences[0].Num
			}
			return numI < numJ
		})
		return sorted

	case "author_nonseq":
		// Sort by title
		sort.Slice(books, func(i, j int) bool {
			return util.BookTitleCmp(books[i].BookTitle, books[j].BookTitle) < 0
		})
		return books

	case "author_time":
		// Sort by date_time descending (newest first)
		sort.Slice(books, func(i, j int) bool {
			return util.UnicodeUpper(books[i].DateTime) > util.UnicodeUpper(books[j].DateTime)
		})
		return books

	case "author_alpha":
		// Sort by title
		sort.Slice(books, func(i, j int) bool {
			return util.BookTitleCmp(books[i].BookTitle, books[j].BookTitle) < 0
		})
		return books

	case "sequence":
		// Same logic as Python: presort by title, filter by seq_id, sort by seq_num
		if seqID == "" {
			return books
		}
		// Presort by title
		sort.Slice(books, func(i, j int) bool {
			return util.BookTitleCmp(books[i].BookTitle, books[j].BookTitle) < 0
		})
		dataSeq := make([]model.Book, 0)
		for i := range books {
			if books[i].Sequences != nil {
				for _, s := range books[i].Sequences {
					if s.ID == seqID {
						num := 0
						if s.Num != nil {
							num = *s.Num
						}
						books[i].Sequences[0].Num = &num
						dataSeq = append(dataSeq, books[i])
						break
					}
				}
			}
		}
		// Sort by seq_num (numbered first, unnumbered after)
		sort.Slice(dataSeq, func(i, j int) bool {
			numI := -1
			numJ := -1
			if len(dataSeq[i].Sequences) > 0 && dataSeq[i].Sequences[0].Num != nil {
				numI = *dataSeq[i].Sequences[0].Num
			}
			if len(dataSeq[j].Sequences) > 0 && dataSeq[j].Sequences[0].Num != nil {
				numJ = *dataSeq[j].Sequences[0].Num
			}
			return numI < numJ
		})
		return dataSeq

	default:
		return books
	}
}

// --- OpdsBooksDB ---

// OpdsBooksDB builds an OPDS feed of books from the database.
func OpdsBooksDB(database *db.DB, params BooksDBParams) (*model.OPDSFeed, error) {
	ts := GetDTISO()

	books, err := database.GetBooksByDate(params.Offset, params.Limit)
	if err != nil {
		return nil, fmt.Errorf("DB query error: %v", err)
	}

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   params.Title,
		Ts:      ts,
		Start:   params.Start,
		Self:    params.Self,
		Tag:     params.Tag,
		Up:      params.Up,
		Prev:    params.Prev,
		Next:    params.Next,
		AppRoot: params.AppRoot,
		AppICO:  params.CFG.Get("APP_ICO"),
		URLs:    params.URLs,
	})

	for _, book := range books {
		entry := MakeBookEntry(book, ts, params.AppRoot, params.URLs, params.LANG, params.AuthRef, params.SeqRef, nil)
		feed.Entries = append(feed.Entries, entry)
	}

	return &feed, nil
}

// OpdsBooksDBSearch builds an OPDS feed from a DB search query.
func OpdsBooksDBSearch(database *db.DB, params BooksDBParams, searchType, searchTerm string) (*model.OPDSFeed, error) {
	ts := GetDTISO()

	var books []model.Book
	var err error

	switch searchType {
	case "title":
		books, err = database.SearchBooksByTitle(searchTerm, params.Limit)
	case "annotation":
		books, err = database.SearchBooksByAnnotation(searchTerm, params.Limit)
	default:
		books, err = database.SearchBooksByTitle(searchTerm, params.Limit)
	}

	if err != nil {
		return nil, fmt.Errorf("DB search error: %v", err)
	}

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   params.Title,
		Ts:      ts,
		Start:   params.Start,
		Self:    params.Self,
		Tag:     params.Tag,
		Up:      params.Up,
		AppRoot: params.AppRoot,
		AppICO:  params.CFG.Get("APP_ICO"),
		URLs:    params.URLs,
	})

	for _, book := range books {
		entry := MakeBookEntry(book, ts, params.AppRoot, params.URLs, params.LANG, params.AuthRef, params.SeqRef, nil)
		feed.Entries = append(feed.Entries, entry)
	}

	return &feed, nil
}

// --- OpdsSimpleListDB ---

// OpdsSimpleListDB builds an OPDS feed of authors or sequences from the database.
func OpdsSimpleListDB(database *db.DB, params SimpleListDBParams) (*model.OPDSFeed, error) {
	ts := GetDTISO()

	feed := OpdsHeader(OpdsHeaderParams{
		Title:   params.Title,
		Ts:      ts,
		Start:   params.Start,
		Self:    params.Self,
		Tag:     params.Tag,
		AppRoot: params.AppRoot,
		AppICO:  params.CFG.Get("APP_ICO"),
		URLs:    params.URLs,
	})

	if params.ListType == "authors" {
		var authors []model.Author
		var err error
		if params.Search != "" {
			authors, err = database.SearchAuthors(params.Search, params.Limit)
		} else {
			authors, err = database.GetRandomAuthors(params.Limit)
		}
		if err != nil {
			return nil, fmt.Errorf("DB authors error: %v", err)
		}

		for _, author := range authors {
			href := params.AppRoot + params.URLs.Author + util.ID2Path(author.ID)
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
	} else if params.ListType == "sequences" {
		var sequences []model.Sequence
		var err error
		if params.Search != "" {
			sequences, err = database.SearchSequences(params.Search, params.Limit)
		} else {
			sequences, err = database.GetRandomSequences(params.Limit)
		}
		if err != nil {
			return nil, fmt.Errorf("DB sequences error: %v", err)
		}

		for _, seq := range sequences {
			href := params.AppRoot + params.URLs.Seq + util.ID2Path(seq.ID)
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

	return &feed, nil
}

// NOTE: Chi route helpers (Param) will be added in Phase 4 when routes are implemented.

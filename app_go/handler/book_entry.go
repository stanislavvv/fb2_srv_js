// Package handler provides OPDS response generation functions.
package handler

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"fb2srv_go/config"
	"fb2srv_go/model"
	"fb2srv_go/util"
)

// getBookLink creates a download/read/plain link for OPDS.
func getBookLink(appRoot, zipfile, filename, ctype string, urls *config.URL) model.OPDSLink {
	title := ""
	bookCtype := "text/html"
	rel := "alternate"
	href := ""

	if ctype == "dl" {
		title = "Скачать"
		bookCtype = "application/fb2+zip"
		rel = "http://opds-spec.org/acquisition/open-access"
		zf := zipfile
		if strings.HasSuffix(zipfile, ".zip") {
			zf = zipfile[:len(zipfile)-4]
		}
		href = appRoot + urls.Dl + zf + "/" + util.URLStr(filename) + ".zip"
	} else if ctype == "plain" {
		title = "Читать fb2"
		bookCtype = "application/x-fb2+xml"
		rel = "http://opds-spec.org/acquisition/open-access"
		zf := zipfile
		if strings.HasSuffix(zipfile, ".zip") {
			zf = zipfile[:len(zipfile)-4]
		}
		href = appRoot + urls.Plain + zf + "/" + util.URLStr(filename)
	} else if ctype == "read_iface" {
		title = "Читать онлайн"
		bookCtype = "text/html"
		rel = "http://opds-spec.org/acquisition/open-access"
		zf := zipfile
		if strings.HasSuffix(zipfile, ".zip") {
			zf = zipfile[:len(zipfile)-4]
		}
		href = appRoot + urls.Read + zf + "/" + util.URLStr(filename) + ".html"
	} else {
		// Default: read
		title = "Читать онлайн"
		bookCtype = "text/html"
		rel = "alternate"
		zf := zipfile
		if strings.HasSuffix(zipfile, ".zip") {
			zf = zipfile[:len(zipfile)-4]
		}
		href = appRoot + urls.Read + zf + "/" + util.URLStr(filename)
	}

	return model.OPDSLink{
		HRef:  href,
		Rel:   rel,
		Title: title,
		Type:  bookCtype,
	}
}

// getSeqLink creates a sequence-related link for OPDS.
func getSeqLink(appRoot, seqRef, seqID, seqName string, lang *config.LANG) model.OPDSLink {
	return model.OPDSLink{
		HRef:  appRoot + seqRef + util.ID2Path(seqID),
		Rel:   "related",
		Title: fmt.Sprintf(lang.SeqTpl, seqName),
		Type:  "application/atom+xml",
	}
}

// pubinfoAnno creates publication info HTML (ISBN/year/publisher).
func pubinfoAnno(pubInfo *model.PubInfo, lang *config.LANG) string {
	if pubInfo == nil {
		return ""
	}
	var ret strings.Builder
	if pubInfo.ISBN != "" && pubInfo.ISBN != "None" {
		ret.WriteString(fmt.Sprintf(lang.PubInfoISBN, pubInfo.ISBN))
	}
	if pubInfo.Year != "" && pubInfo.Year != "None" {
		ret.WriteString(fmt.Sprintf(lang.PubInfoYear, pubInfo.Year))
	}
	if pubInfo.Publisher != "" && pubInfo.Publisher != "None" {
		ret.WriteString(fmt.Sprintf(lang.PubInfoPublisher, pubInfo.Publisher))
	}
	return ret.String()
}

// coverLinks returns 4 OPDS cover image link variants.
func coverLinks(appRoot, bookID string, urls *config.URL) []model.OPDSLink {
	relTypes := []string{
		"http://opds-spec.org/image",
		"x-stanza-cover-image",
		"http://opds-spec.org/thumbnail",
		"x-stanza-cover-image-thumbnail",
	}
	links := make([]model.OPDSLink, 0, len(relTypes))
	href := appRoot + urls.Cover + util.ID2Path(bookID) + ".jpg"
	for _, rel := range relTypes {
		links = append(links, model.OPDSLink{
			HRef: href,
			Rel:  rel,
			Type: "image/jpeg",
		})
	}
	return links
}

// getGenreName returns the human-readable genre name from the global genres map.
// This function uses the genres loaded from genres.list file.
var genresMap map[string]string = make(map[string]string)

// InitGenres populates the genre name map from a file.
func InitGenres(path string) error {
	// Read from genres.list format: meta_id|genre_id|descr
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, "|", 3)
		if len(parts) >= 3 {
			genresMap[parts[1]] = parts[2]
		}
	}
	return nil
}

// GetGenreName returns genre description by ID, or the ID itself if not found.
func GetGenreName(genID string) string {
	if name, ok := genresMap[genID]; ok {
		return name
	}
	return genID
}

// MakeBookEntry creates a complete OPDS entry for a book.
//
// Parameters:
//   - book: full book structure
//   - ts: timestamp in ISO format (from GetDTISO)
//   - appRoot: application root URL prefix
//   - urls: URL constants
//   - lang: language strings
//   - authRef: URL path for author references (e.g., URL.Author)
//   - seqRef: URL path for sequence references (e.g., URL.Seq)
//   - seqID: if not nil, this entry is for a specific sequence book list
func MakeBookEntry(book model.Book, ts string, appRoot string, urls *config.URL, lang *config.LANG, authRef string, seqRef string, seqID *string) model.OPDSEntry {
	bookTitle := book.BookTitle
	bookID := book.BookID
	langCode := book.Lang
	annotation := util.HTMLRefine(book.Annotation)
	size := 0
	if book.Size != "" {
		size, _ = strconv.Atoi(book.Size)
	}
	dateTime := book.DateTime
	zipfile := book.Zipfile
	filename := book.Filename
	genres := book.Genres

	// Authors
	authors := make([]model.OPDSAuthor, 0, len(book.Authors))
	links := make([]model.OPDSLink, 0)

	for _, author := range book.Authors {
		authors = append(authors, model.OPDSAuthor{
			URI:  appRoot + authRef + util.ID2Path(author.ID),
			Name: author.Name,
		})
		links = append(links, model.OPDSLink{
			HRef:  appRoot + authRef + util.ID2Path(author.ID),
			Rel:   "related",
			Title: author.Name,
			Type:  "application/atom+xml",
		})
	}

	// Genre categories
	categories := make([]model.OPDSCategory, 0, len(genres))
	for _, gen := range genres {
		categories = append(categories, model.OPDSCategory{
			Term:  gen,
			Label: GetGenreName(gen),
		})
	}

	// Sequences
	var seqName string
	var seqNum string
	if book.Sequences != nil && len(book.Sequences) > 0 {
		for _, seq := range book.Sequences {
			if seq.ID != "" {
				links = append(links, getSeqLink(appRoot, seqRef, seq.ID, seq.Name, lang))
				if seqID != nil && *seqID == seq.ID {
					seqName = seq.Name
					if seq.Num != nil {
						seqNum = fmt.Sprintf("%d", *seq.Num)
					} else {
						seqNum = "0"
					}
				}
			}
		}
	}

	// Book acquisition links
	links = append(links, getBookLink(appRoot, zipfile, filename, "dl", urls))
	links = append(links, getBookLink(appRoot, zipfile, filename, "read_iface", urls))

	// Cover links
	links = append(links, coverLinks(appRoot, bookID, urls)...)

	// Annotation text
	var annotext string
	if seqID != nil && *seqID != "" {
		annotext = fmt.Sprintf(lang.BookInfoSeq, annotation, util.SizeofFmt(size, ""), seqName, seqNum)
	} else {
		annotext = fmt.Sprintf(lang.BookInfo, annotation, util.SizeofFmt(size, ""))
	}

	// Append publication info
	pubinfo := pubinfoAnno(book.PubInfo, lang)
	annotext = annotext + pubinfo

	return model.OPDSEntry{
		Updated: dateTime,
		ID:      "tag:book:" + bookID,
		Title:   bookTitle,
		Authors: authors,
		Links:   links,
		Categories: categories,
		DCLanguage: langCode,
		DCFormat: "fb2",
		Content: &model.OPDSContent{
			Type:  "text/html",
			Value: annotext,
		},
	}
}
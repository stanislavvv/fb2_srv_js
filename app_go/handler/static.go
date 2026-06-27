// Package handler provides static file HTTP handlers.
package handler

import (
	"archive/zip"
	"bytes"
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"fb2srv_go/config"
	"fb2srv_go/util"

	"github.com/go-chi/chi"
)

// coverHandler handles GET /books/{sub1}/{sub2}/{book_id}.jpg
func (s *Server) coverHandler(w http.ResponseWriter, r *http.Request) {
	sub1 := chi.URLParam(r, "sub1")
	sub2 := chi.URLParam(r, "sub2")
	bookID := chi.URLParam(r, "book_id")

	sub1 = util.ValidateID(sub1)
	sub2 = util.ValidateID(sub2)
	bookID = util.ValidateID(bookID)

	if bookID == "" {
		// Fallback to default cover
		s.serveDefaultCover(w, r)
		return
	}

	pagesDir := s.CFG.Get("PAGES")

	// Build cover path: /books/{sub1}/{sub2}/{book_id}.jpg
	coverFile := fmt.Sprintf("/books/%s/%s/%s.jpg", sub1, sub2, bookID)

	// safe_path equivalent: ensure path is safe
	coverFile = strings.ReplaceAll(coverFile, "..", "")
	coverFile = strings.TrimPrefix(coverFile, "/")

	fullPath := filepath.Join(pagesDir, coverFile)

	// Check if file exists
	if _, err := os.Stat(fullPath); os.IsNotExist(err) {
		// Fallback to default cover
		s.serveDefaultCover(w, r)
		return
	}

	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	http.ServeFile(w, r, fullPath)
}

// serveDefaultCover serves the default cover image.
func (s *Server) serveDefaultCover(w http.ResponseWriter, r *http.Request) {
	pagesDir := s.CFG.Get("PAGES")
	defaultCover := s.CFG.Get("DEFAULT_COVER")

	// Remove leading "/" from default_cover path (e.g., "/books/default.jpg")
	defaultCover = strings.TrimPrefix(defaultCover, "/")

	fullPath := filepath.Join(pagesDir, defaultCover)

	if _, err := os.Stat(fullPath); os.IsNotExist(err) {
		// If even default cover from pages doesn't exist, try DEFAULT_COVER_SRC
		// which is the source file in app/static/
		defaultCoverSrc := s.CFG.Get("DEFAULT_COVER_SRC")
		// defaultCoverSrc is like "./app/static/default-cover.jpg"
		// Use it relative to working directory
		fullPath = strings.TrimPrefix(defaultCoverSrc, "./")

		if _, err2 := os.Stat(fullPath); os.IsNotExist(err2) {
			http.NotFound(w, r)
			return
		}
	}

	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	http.ServeFile(w, r, fullPath)
}

// webrootHandler handles GET / → renders index.html template
func (s *Server) webrootHandler(w http.ResponseWriter, r *http.Request) {
	// Template uses {{index .Data "key"}} format from Jinja2 conversion
	data := map[string]interface{}{
		"Title": s.CFG.Get("TITLE"),
		"Data": map[string]interface{}{
			"approot": s.CFG.Get("APPLICATION_ROOT"),
			"path":    "/",
			"title":   s.CFG.Get("TITLE"),
		},
	}

	cacheSeconds := 604800
	fmt.Sscanf(s.CFG.Get("CACHE_TIME"), "%d", &cacheSeconds)

	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", cacheSeconds))

	tmpl, err := template.ParseFiles("app_go/templates/index.html")
	if err != nil {
		log.Printf("ERROR: webrootHandler template parse: %v", err)
		http.Error(w, "Template error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := tmpl.Execute(w, data); err != nil {
		log.Printf("ERROR: webrootHandler template execute: %v", err)
	}
}

// interfaceJSHandler handles GET /interface.js → renders interface.js template
func (s *Server) interfaceJSHandler(w http.ResponseWriter, r *http.Request) {
	appRoot := s.CFG.Get("APPLICATION_ROOT")
	start := s.URLs.Start

	// Build opds_prefix: f"{approot}{start}".strip('/') — Python strips BOTH ends
	// For appRoot="/" + start="/opds" = "//opds" → strip('/') → "opds"
	opdsPrefix := strings.Trim(appRoot+start, "/")

	// Build genre_prefix: replicate Python URL["genre"].strip('/').replace('opds/', '')
	// For "/opds/genre/" → strip('/') → "opds/genre" → replace → "genre"
	genrePrefix := strings.ReplaceAll(strings.Trim(s.URLs.Genre, "/"), "opds/", "")

	// Template uses {{index .Data "key"}} format from Jinja2 conversion
	data := map[string]interface{}{
		"Title": s.CFG.Get("TITLE"),
		"Data": map[string]interface{}{
			"approot":      appRoot,
			"path":         "/interface.js",
			"opds_prefix":  opdsPrefix,
			"genre_prefix": genrePrefix,
			"lang_authors": s.LANG.JSAuthors,
			"lang_links":   s.LANG.JSLinks,
			"lang_genres":  s.LANG.JSGenres,
			"lang_lang":    s.LANG.JSLang,
		},
	}

	cacheSeconds := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &cacheSeconds)

	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", cacheSeconds))

	tmpl, err := template.ParseFiles("app_go/templates/interface.js")
	if err != nil {
		log.Printf("ERROR: interfaceJSHandler template parse: %v", err)
		http.Error(w, "Template error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/javascript; charset=utf-8")
	if err := tmpl.Execute(w, data); err != nil {
		log.Printf("ERROR: interfaceJSHandler template execute: %v", err)
	}
}

// faviconHandler handles GET /favicon.ico
func (s *Server) faviconHandler(w http.ResponseWriter, r *http.Request) {
	staticDir := "app_go/static"
	filePath := filepath.Join(staticDir, "favicon.ico")

	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		http.NotFound(w, r)
		return
	}

	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	http.ServeFile(w, r, filePath)
}

// moonIconHandler handles GET /moon.svg
func (s *Server) moonIconHandler(w http.ResponseWriter, r *http.Request) {
	staticDir := "app_go/static"
	filePath := filepath.Join(staticDir, "moon.svg")

	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		http.NotFound(w, r)
		return
	}

	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	http.ServeFile(w, r, filePath)
}

// sunIconHandler handles GET /sun.svg
func (s *Server) sunIconHandler(w http.ResponseWriter, r *http.Request) {
	staticDir := "app_go/static"
	filePath := filepath.Join(staticDir, "sun.svg")

	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		http.NotFound(w, r)
		return
	}

	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	http.ServeFile(w, r, filePath)
}

// xslHandler handles GET /fb2.xsl → serves the XSL stylesheet file
func (s *Server) xslHandler(w http.ResponseWriter, r *http.Request) {
	xslFile := s.CFG.Get("FB2_XSLT")
	// FB2_XSLT defaults to "fb2_to_html.xsl"
	if xslFile == "" {
		xslFile = "fb2_to_html.xsl"
	}

	// Try relative path first
	data, err := os.ReadFile(xslFile)
	if err != nil {
		log.Printf("ERROR: xslHandler: could not read %s: %v", xslFile, err)
		http.NotFound(w, r)
		return
	}

	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	w.Header().Set("Content-Type", "application/xml")
	w.Write(data)
}

// fb2Out extracts raw FB2 data from a ZIP archive.
// zipFileName: name of the ZIP file in zips_path (with .zip extension)
// fileName: name of the FB2 file inside the archive (without .zip)
func (s *Server) fb2Out(zipFileName string, fileName string) ([]byte, error) {
	zipsDir := s.CFG.Get("ZIPS")
	zipPath := filepath.Join(zipsDir, zipFileName)

	// Open the ZIP file
	zr, err := zip.OpenReader(zipPath)
	if err != nil {
		return nil, fmt.Errorf("open zip %s: %w", zipPath, err)
	}
	defer zr.Close()

	// Find the FB2 file inside the archive
	for _, f := range zr.File {
		if f.Name == fileName {
			rc, err := f.Open()
			if err != nil {
				return nil, fmt.Errorf("open file in zip %s/%s: %w", zipFileName, fileName, err)
			}
			data, err := io.ReadAll(rc)
			rc.Close()
			if err != nil {
				return nil, fmt.Errorf("read file from zip %s/%s: %w", zipFileName, fileName, err)
			}
			return data, nil
		}
	}

	return nil, fmt.Errorf("file %s not found in archive %s", fileName, zipFileName)
}

// downloadHandler handles GET /fb2/{zip_file}/{filename}
// Creates a ZIP archive containing the FB2 file and serves it for download.
func (s *Server) downloadHandler(w http.ResponseWriter, r *http.Request) {
	zipFile := chi.URLParam(r, "zip_file")
	filename := chi.URLParam(r, "filename")

	// Handle .zip extension: strip it from filename if present
	if strings.HasSuffix(filename, ".zip") {
		filename = filename[:len(filename)-4]
	}
	// Ensure zip_file ends with .zip
	if !strings.HasSuffix(zipFile, ".zip") {
		zipFile = zipFile + ".zip"
	}

	zipFile = util.ValidateZip(zipFile)
	filename = util.ValidateFB2(filename)
	if zipFile == "" || filename == "" {
		// Redirect to root on invalid params
		http.Redirect(w, r, s.URLs.Start, http.StatusFound)
		return
	}

	// Extract FB2 data from the source ZIP
	fb2Data, err := s.fb2Out(zipFile, filename)
	if err != nil {
		log.Printf("ERROR: downloadHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	// Create a new ZIP in memory with the FB2 file
	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)

	data := &zip.FileHeader{
		Name:   filename,
		Method: zip.Deflate,
	}
	set, err := zw.CreateHeader(data)
	if err != nil {
		log.Printf("ERROR: downloadHandler zip create: %v", err)
		http.Error(w, "Internal error", http.StatusInternalServerError)
		return
	}
	_, err = set.Write(fb2Data)
	if err != nil {
		log.Printf("ERROR: downloadHandler zip write: %v", err)
		http.Error(w, "Internal error", http.StatusInternalServerError)
		return
	}

	zw.Close()
	buf.Bytes()

	zipName := filename + ".zip"
	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", fmt.Sprintf(`attachment; filename="%s"`, zipName))
	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	w.Header().Set("Content-Length", fmt.Sprintf("%d", buf.Len()))
	w.Write(buf.Bytes())
}

// readHandler handles GET /read/{zip_file}/{filename} and /read/{zip_file}/{filename}.html
// Transforms FB2 to HTML using XSLT and serves it for online reading.
func (s *Server) readHandler(w http.ResponseWriter, r *http.Request) {
	zipFile := chi.URLParam(r, "zip_file")
	filename := chi.URLParam(r, "filename")

	// Handle .zip extension: strip from filename if present
	if strings.HasSuffix(filename, ".zip") {
		filename = filename[:len(filename)-4]
	}
	// Handle .html extension: strip from filename if present
	if strings.HasSuffix(filename, ".html") {
		filename = filename[:len(filename)-5]
	}
	// Ensure zip_file ends with .zip
	if !strings.HasSuffix(zipFile, ".zip") {
		zipFile = zipFile + ".zip"
	}

	zipFile = util.ValidateZip(zipFile)
	filename = util.ValidateFB2(filename)
	if zipFile == "" || filename == "" {
		http.Redirect(w, r, s.URLs.Start, http.StatusFound)
		return
	}

	// Extract FB2 data from the source ZIP
	fb2Data, err := s.fb2Out(zipFile, filename)
	if err != nil {
		log.Printf("ERROR: readHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	// Transform FB2 -> HTML using XSLT
	if s.XSLT == nil {
		log.Printf("ERROR: readHandler: XSLT not initialized")
		http.Error(w, "XSLT not configured", http.StatusInternalServerError)
		return
	}

	htmlData, err := s.XSLT.Transform(fb2Data)
	if err != nil {
		log.Printf("ERROR: readHandler XSLT transform: %s/%s: %v", zipFile, filename, err)
		http.NotFound(w, r)
		return
	}

	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	w.Write(htmlData)
}

// plainHandler handles GET /plain/{zip_file}/{filename}
// Serves raw FB2 with optional XSL processing instruction for browser XSLT.
func (s *Server) plainHandler(w http.ResponseWriter, r *http.Request) {
	zipFile := chi.URLParam(r, "zip_file")
	filename := chi.URLParam(r, "filename")

	// Handle .zip extension: strip from filename if present
	if strings.HasSuffix(filename, ".zip") {
		filename = filename[:len(filename)-4]
	}
	// Ensure zip_file ends with .zip
	if !strings.HasSuffix(zipFile, ".zip") {
		zipFile = zipFile + ".zip"
	}

	zipFile = util.ValidateZip(zipFile)
	filename = util.ValidateFB2(filename)
	if zipFile == "" || filename == "" {
		http.Redirect(w, r, s.URLs.Start, http.StatusFound)
		return
	}

	// Extract FB2 data from the source ZIP
	fb2Data, err := s.fb2Out(zipFile, filename)
	if err != nil {
		log.Printf("ERROR: plainHandler: %v", err)
		http.NotFound(w, r)
		return
	}

	maxAge := 2592000
	fmt.Sscanf(s.CFG.Get("CACHE_TIME_ST"), "%d", &maxAge)

	// Build XSL processing instruction
	xslLine := config.XSLReadTemplate
	// Replace the format placeholder with the actual XSL read URL
	xslHref := s.URLs.XslRead
	xslLine = fmt.Sprintf(xslLine, xslHref)

	// Add XSL line after XML declaration
	fb2Prepared := util.AddXSLLine(fb2Data, xslHref)

	// Send raw FB2 (with XSL line for browser processing)
	w.Header().Set("Content-Type", "application/x-fb2+xml")
	w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", maxAge))
	w.Write(fb2Prepared)
}

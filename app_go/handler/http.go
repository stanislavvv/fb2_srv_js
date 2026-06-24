// Package handler provides OPDS response generation functions.
package handler

import (
	"encoding/xml"
	"fmt"
	"net/http"
	"time"

	"fb2srv_go/config"
	"fb2srv_go/model"
)

// GetDTISO returns the current time in ISO 8601 format (timezone-aware, no microseconds).
func GetDTISO() string {
	return time.Now().In(time.Local).Format(time.RFC3339)
}

// CreateOPDSResponse marshals an OPDS feed to XML and writes it to the HTTP response
// with proper headers (Content-Type, Cache-Control).
func CreateOPDSResponse(w http.ResponseWriter, feed model.OPDSFeed, cacheSeconds int) {
	data, err := xml.MarshalIndent(feed, "", "  ")
	if err != nil {
		http.Error(w, fmt.Sprintf("XML marshal error: %v", err), http.StatusInternalServerError)
		return
	}

	// Build final XML with declaration
	xmlStr := fmt.Sprintf("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n%s", string(data))

	// Write headers
	w.Header().Set("Content-Type", "text/xml; charset=UTF-8")
	if cacheSeconds > 0 {
		w.Header().Set("Cache-Control", fmt.Sprintf("max-age=%d, must-revalidate", cacheSeconds))
	} else {
		w.Header().Set("Cache-Control", "no-cache, must-revalidate")
	}
	w.Header().Set("Content-Length", fmt.Sprintf("%d", len(xmlStr)))
	w.WriteHeader(http.StatusOK)
	_, err = w.Write([]byte(xmlStr))
	if err != nil {
		// Log error but response already sent
		_ = err
	}
}

// CreateOPDSResponseWithConfig is a convenience wrapper using config cache time.
func CreateOPDSResponseWithConfig(w http.ResponseWriter, feed model.OPDSFeed, cfg *config.Config) {
	cacheSeconds := 0
	// Parse CACHE_TIME as int
	fmt.Sscanf(cfg.Get("CACHE_TIME"), "%d", &cacheSeconds)
	CreateOPDSResponse(w, feed, cacheSeconds)
}
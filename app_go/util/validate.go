// Package util provides input validation utilities.
package util

import (
	"path/filepath"
	"regexp"
	"strings"
)

// Regex patterns for validation.
var (
	idCheck    = regexp.MustCompile(`^[0-9a-f]+$`)
	zipCheck   = regexp.MustCompile(`^[0-9a-zA-Z_.\-]+\.zip$`)
	fb2Check   = regexp.MustCompile(`^[ 0-9a-zA-ZА-Яа-я_,.:!\-]+\.fb2$`)
	genreCheck = regexp.MustCompile(`^[0-9a-z_]+$`)
)

// ValidateID validates an author/book/sequence ID (hex string).
func ValidateID(s string) string {
	if idCheck.MatchString(s) {
		return s
	}
	return ""
}

// ValidateZip validates a zip filename.
func ValidateZip(s string) string {
	if zipCheck.MatchString(s) {
		return s
	}
	return ""
}

// ValidateFB2 validates an fb2 filename.
func ValidateFB2(s string) string {
	if fb2Check.MatchString(s) {
		return s
	}
	return ""
}

// ValidateGenre validates a genre ID.
func ValidateGenre(s string) string {
	if genreCheck.MatchString(s) {
		return s
	}
	return ""
}

// unurl performs simple URL decoding for specific encoded characters.
func unurl(s string) string {
	if s == "" {
		return ""
	}
	translate := map[string]string{
		"%22": "\"",
		"%27": "'",
		"%2E": ".",
		"%2F": "/",
	}
	ret := s
	for k, v := range translate {
		ret = strings.ReplaceAll(ret, k, v)
	}
	return ret
}

// ValidateSearch normalizes a search pattern.
func ValidateSearch(s string) string {
	if s == "" {
		return ""
	}
	ret := unurl(s)
	ret = strings.ReplaceAll(ret, ";", "")
	if len(ret) > 128 {
		ret = ret[:128]
	}
	return ret
}

// SafePath creates a safe relative path from input (prevents path traversal).
func SafePath(fspath string) string {
	if fspath == "" {
		return ""
	}
	// Join with root and make relative - this prevents ../ traversal
	cleaned := filepath.Clean("/" + fspath)
	// Remove leading "/"
	return cleaned[1:]
}

// ValidatePrefix validates a prefix for authorsindex/sequencesindex URLs.
func ValidatePrefix(s string) string {
	if s == "" {
		return ""
	}
	// Reject path traversal attempts
	ret := SafePath(s)
	if ret != s {
		return ""
	}
	if len(ret) < 1 || len(ret) > 10 {
		return ""
	}
	return ret
}

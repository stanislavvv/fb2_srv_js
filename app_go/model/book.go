// Package model contains data structures for books, authors, sequences and OPDS.
package model

import (
	"encoding/json"
	"time"
)

// IntOrBool is a custom type that can unmarshal from either an integer (0/1) or a boolean.
type IntOrBool bool

// UnmarshalJSON implements json.Unmarshaler for IntOrBool.
func (ib *IntOrBool) UnmarshalJSON(data []byte) error {
	var f float64
	if err := json.Unmarshal(data, &f); err == nil {
		*ib = IntOrBool(f != 0)
		return nil
	}
	var b bool
	if err := json.Unmarshal(data, &b); err != nil {
		return err
	}
	*ib = IntOrBool(b)
	return nil
}

// Author represents a book author from the authors table.
type Author struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Info string `json:"info,omitempty"`
}

// SequenceRef is a reference to a sequence within a book record.
type SequenceRef struct {
	Name string `json:"name"`
	ID   string `json:"id"`
	Num  *int   `json:"num,omitempty"` // pointer to distinguish nil from 0
}

// PubInfo holds publication metadata (ISBN, year, publisher).
type PubInfo struct {
	ISBN         string `json:"isbn,omitempty"`
	Year         string `json:"year,omitempty"`
	Publisher    string `json:"publisher,omitempty"`
	PublisherID  string `json:"publisher_id,omitempty"`
}

// Book is the full book structure with joined description, authors and sequences.
type Book struct {
	Zipfile    string        `json:"zipfile"`
	Filename   string        `json:"filename"`
	Genres     []string      `json:"genres"`
	Authors    []Author      `json:"authors"`
	Sequences  []SequenceRef `json:"sequences"`
	BookID     string        `json:"book_id"`
	BookTitle  string        `json:"book_title"`
	Lang       string        `json:"lang"`
	Date       *time.Time    `json:"date,omitempty"`
	Size       string        `json:"size"`
	Annotation string        `json:"annotation"`
	PubInfo    *PubInfo      `json:"pub_info,omitempty"`
	DateTime   string        `json:"date_time"`
	Deleted    *IntOrBool    `json:"deleted,omitempty"`
}

// Sequence represents a sequence/series from the sequences table.
type Sequence struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Info string `json:"info,omitempty"`
}

// GenresMeta represents a meta genre (group) from genres_meta table.
type GenresMeta struct {
	MetaID      string `json:"meta_id"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
}

// Genre represents a genre from the genres table.
type Genre struct {
	ID          string `json:"id"`
	MetaID      string `json:"meta_id"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
}

// VectorRecord is a row from the vectors table.
type VectorRecord struct {
	ID        string    `json:"id"`
	Embedding []float32 `json:"embedding"`
	IsBad     bool      `json:"is_bad"`
}
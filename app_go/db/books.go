// Package db provides database access for books.
package db

import (
	"database/sql"
	"fmt"
	"strings"
	"time"

	"fb2srv_go/model"
	"github.com/lib/pq"
)

// GetBooksByDate returns books ordered by date descending with pagination.
func (db *DB) GetBooksByDate(offset, limit int) ([]model.Book, error) {
	var raw []BookRaw
	var err error
	raw, err = db.fetchBooks("ORDER BY date DESC", limit, offset)
	if err != nil {
		return nil, err
	}
	return assembleBooks(db, raw)
}

// GetBooksCount returns the total number of books.
func (db *DB) GetBooksCount() (int, error) {
	var count int
	err := db.conn.QueryRow("SELECT count(*) FROM books").Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("GetBooksCount: %w", err)
	}
	return count, nil
}

// GetRandomBooks returns random books from the database (NO pagination).
func (db *DB) GetRandomBooks(limit int) ([]model.Book, error) {
	var raw []BookRaw
	var err error
	raw, err = db.fetchBooks("ORDER BY random()", limit, 0)
	if err != nil {
		return nil, err
	}
	return assembleBooks(db, raw)
}

// GetRandomBooksByGenre returns random books filtered by genre (NO pagination).
func (db *DB) GetRandomBooksByGenre(genre string, limit int) ([]model.Book, error) {
	query := `
		SELECT zipfile, filename, genres, authors, sequences, book_id, lang, date, size, deleted
		FROM books
		WHERE genres && $1
		ORDER BY random()
		LIMIT $2
	`
	rows, err := db.conn.Query(query, pq.StringArray{genre}, limit)
	if err != nil {
		return nil, fmt.Errorf("GetRandomBooksByGenre: %w", err)
	}
	defer rows.Close()

	raw, err := scanBookRows(rows)
	if err != nil {
		return nil, err
	}
	return assembleBooks(db, raw)
}

// SearchBooksByTitle searches books by title using ILIKE.
func (db *DB) SearchBooksByTitle(query string, limit int) ([]model.Book, error) {
	bookIDs, err := db.searchByID("book_title", query, limit)
	if err != nil {
		return nil, err
	}
	if len(bookIDs) == 0 {
		return []model.Book{}, nil
	}
	return db.GetBooksWithDetails(bookIDs)
}

// SearchBooksByAnnotation searches books by annotation using ILIKE.
func (db *DB) SearchBooksByAnnotation(query string, limit int) ([]model.Book, error) {
	bookIDs, err := db.searchByID("annotation", query, limit)
	if err != nil {
		return nil, err
	}
	if len(bookIDs) == 0 {
		return []model.Book{}, nil
	}
	return db.GetBooksWithDetails(bookIDs)
}

// GetBooksWithDetails fetches full book data by IDs.
func (db *DB) GetBooksWithDetails(ids []string) ([]model.Book, error) {
	if len(ids) == 0 {
		return []model.Book{}, nil
	}

	query := `
		SELECT zipfile, filename, genres, authors, sequences, book_id, lang, date, size, deleted
		FROM books
		WHERE book_id = ANY($1)
	`
	rows, err := db.conn.Query(query, pq.Array(ids))
	if err != nil {
		return nil, fmt.Errorf("GetBooksWithDetails: %w", err)
	}
	defer rows.Close()

	raw, err := scanBookRows(rows)
	if err != nil {
		return nil, err
	}
	return assembleBooks(db, raw)
}

// GetBooksByIDs returns full book data for given IDs (used by vector search).
func (db *DB) GetBooksByIDs(ids []string) ([]model.Book, error) {
	return db.GetBooksWithDetails(ids)
}

// fetchBooks is a generic book fetcher with ordering and pagination.
func (db *DB) fetchBooks(orderBy string, limit, offset int) ([]BookRaw, error) {
	query := fmt.Sprintf(`
		SELECT zipfile, filename, genres, authors, sequences, book_id, lang, date, size, deleted
		FROM books
		%s LIMIT $1 OFFSET $2
	`, orderBy)

	rows, err := db.conn.Query(query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("fetchBooks: %w", err)
	}
	defer rows.Close()

	return scanBookRows(rows)
}

// searchByID searches book_descr by a column and returns matching book IDs.
func (db *DB) searchByID(column, query string, limit int) ([]string, error) {
	terms := strings.Fields(query)
	if len(terms) == 0 {
		return []string{}, nil
	}

	conditions := make([]string, len(terms))
	args := make([]interface{}, len(terms)+1)
	args[len(terms)] = limit
	for i, term := range terms {
		conditions[i] = fmt.Sprintf("%s ILIKE $%d", column, i+1)
		args[i] = "%" + term + "%"
	}

	sql := fmt.Sprintf(
		"SELECT book_id FROM book_descr WHERE %s LIMIT $%d",
		strings.Join(conditions, " AND "),
		len(terms)+1,
	)

	rows, err := db.conn.Query(sql, args...)
	if err != nil {
		return nil, fmt.Errorf("searchByID (%s): %w", column, err)
	}
	defer rows.Close()

	var ids []string
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			return nil, fmt.Errorf("scan id: %w", err)
		}
		ids = append(ids, id)
	}
	return ids, nil
}

// assembleBooks enriches raw book data with descriptions, authors and sequences.
func assembleBooks(db *DB, raw []BookRaw) ([]model.Book, error) {
	if len(raw) == 0 {
		return []model.Book{}, nil
	}

	// Collect all unique book IDs, author IDs, sequence IDs
	bookIDSet := make(map[string]bool, len(raw))
	var authorIDs []string
	var seqIDs []string
	authorIDSet := make(map[string]bool)
	seqIDSet := make(map[string]bool)

	for _, r := range raw {
		bookIDSet[r.BookID] = true

		// Parse author IDs from authors array
		if len(r.AuthorsRaw) > 0 {
			for _, aRaw := range r.AuthorsRaw {
				for _, part := range strings.Split(aRaw, "|") {
					aid := strings.TrimSpace(part)
					if aid != "" && !authorIDSet[aid] {
						authorIDSet[aid] = true
						authorIDs = append(authorIDs, aid)
					}
				}
			}
		}

		// Parse sequence IDs from sequences array
		if len(r.SequencesRaw) > 0 {
			for _, sRaw := range r.SequencesRaw {
				for _, part := range strings.Split(sRaw, "|") {
					sid := strings.TrimSpace(part)
					if sid != "" && !seqIDSet[sid] {
						seqIDSet[sid] = true
						seqIDs = append(seqIDs, sid)
					}
				}
			}
		}
	}

	// Fetch descriptions, authors, sequences in batch
	var bookIDs []string
	for id := range bookIDSet {
		bookIDs = append(bookIDs, id)
	}

	descrMap, err := db.getBooksDescr(bookIDs)
	if err != nil {
		return nil, fmt.Errorf("assembleBooks: getBooksDescr: %w", err)
	}

	authorMap, err := db.getAuthors(authorIDs)
	if err != nil {
		return nil, fmt.Errorf("assembleBooks: getAuthors: %w", err)
	}

	seqMap, err := db.getSequences(seqIDs)
	if err != nil {
		return nil, fmt.Errorf("assembleBooks: getSequences: %w", err)
	}

	// Assemble final result
	result := make([]model.Book, len(raw))
	for i, r := range raw {
		var datePtr *time.Time
		dateStr := ""
		if r.Date.Valid {
			datePtr = &r.Date.Time
			dateStr = r.Date.Time.Format("2006-01-02") + "_00:00"
		}
		var deletedPtr *model.IntOrBool
		if r.Deleted.Valid {
			val := model.IntOrBool(r.Deleted.Bool)
			deletedPtr = &val
		}

		// Description
		d, _ := descrMap[r.BookID]

		// Authors
		authors := make([]model.Author, 0, len(r.AuthorsRaw))
		for _, aRaw := range r.AuthorsRaw {
			for _, part := range strings.Split(aRaw, "|") {
				aid := strings.TrimSpace(part)
				if aid != "" {
					if a, ok := authorMap[aid]; ok {
						authors = append(authors, a)
					} else {
						authors = append(authors, model.Author{ID: aid, Name: aid})
					}
				}
			}
		}

		// Sequences
		sequences := make([]model.SequenceRef, 0, len(r.SequencesRaw))
		for _, sRaw := range r.SequencesRaw {
			for _, part := range strings.Split(sRaw, "|") {
				sid := strings.TrimSpace(part)
				if sid != "" {
					if s, ok := seqMap[sid]; ok {
						sequences = append(sequences, s)
					} else {
						sequences = append(sequences, model.SequenceRef{ID: sid, Name: sid})
					}
				}
			}
		}

		// Publication info
		var pubInfo *model.PubInfo
		if d.PubISBN != "" || d.PubYear != "" || d.Publisher != "" {
			pubInfo = &model.PubInfo{
				ISBN:        d.PubISBN,
				Year:        d.PubYear,
				Publisher:   d.Publisher,
				PublisherID: d.PublisherID,
			}
		}

		book := model.Book{
			Zipfile:    r.Zipfile,
			Filename:   r.Filename,
			Genres:     r.Genres,
			Authors:    authors,
			Sequences:  sequences,
			BookID:     r.BookID,
			BookTitle:  d.BookTitle,
			Lang:       r.Lang,
			Date:       datePtr,
			Size:       fmt.Sprintf("%d", r.Size),
			Annotation: d.Annotation,
			PubInfo:    pubInfo,
			DateTime:   dateStr,
			Deleted:    deletedPtr,
		}

		result[i] = book
	}

	return result, nil
}

// BookRaw is intermediate book data from the books table.
type BookRaw struct {
	Zipfile      string
	Filename     string
	Genres       pq.StringArray
	AuthorsRaw   pq.StringArray
	SequencesRaw pq.StringArray
	BookID       string
	Lang         string
	Date         sql.NullTime
	Size         int
	Deleted      sql.NullBool
}

// scanBookRows scans rows from books table into BookRaw structs.
func scanBookRows(rows *sql.Rows) ([]BookRaw, error) {
	var books []BookRaw
	for rows.Next() {
		var b BookRaw
		var dt sql.NullTime
		var dl sql.NullBool
		err := rows.Scan(
			&b.Zipfile, &b.Filename, &b.Genres,
			&b.AuthorsRaw, &b.SequencesRaw,
			&b.BookID, &b.Lang, &dt, &b.Size, &dl,
		)
		b.Date = dt
		b.Deleted = dl
		if err != nil {
			return nil, fmt.Errorf("scanBookRows: %w", err)
		}
		books = append(books, b)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("scanBookRows iteration: %w", err)
	}
	return books, nil
}

// BookDescr holds book description data.
type BookDescr struct {
	BookID      string
	BookTitle   string
	PubISBN     string
	PubYear     string
	Publisher   string
	PublisherID string
	Annotation  string
}

// getBooksDescr fetches book descriptions for given book IDs.
func (db *DB) getBooksDescr(bookIDs []string) (map[string]BookDescr, error) {
	ret := make(map[string]BookDescr)
	if len(bookIDs) == 0 {
		return ret, nil
	}

	rows, err := db.conn.Query(
		"SELECT book_id, book_title, pub_isbn, pub_year, publisher, publisher_id, annotation FROM book_descr WHERE book_id = ANY($1)",
		pq.Array(bookIDs),
	)
	if err != nil {
		return nil, fmt.Errorf("getBooksDescr: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var d BookDescr
		var pubISBN, pubYear, publisher, pubID, anno sql.NullString
		err := rows.Scan(&d.BookID, &d.BookTitle, &pubISBN, &pubYear, &publisher, &pubID, &anno)
		if err != nil {
			return nil, fmt.Errorf("scan descr: %w", err)
		}
		if pubISBN.Valid {
			d.PubISBN = pubISBN.String
		}
		if pubYear.Valid {
			d.PubYear = pubYear.String
		}
		if publisher.Valid {
			d.Publisher = publisher.String
		}
		if pubID.Valid {
			d.PublisherID = pubID.String
		}
		if anno.Valid {
			d.Annotation = anno.String
		}
		ret[d.BookID] = d
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("getBooksDescr iteration: %w", err)
	}
	return ret, nil
}

// getAuthors fetches authors for given IDs, returns map by ID.
func (db *DB) getAuthors(authorIDs []string) (map[string]model.Author, error) {
	ret := make(map[string]model.Author)
	if len(authorIDs) == 0 {
		return ret, nil
	}

	rows, err := db.conn.Query(
		"SELECT id, name, info FROM authors WHERE id = ANY($1)",
		pq.Array(authorIDs),
	)
	if err != nil {
		return nil, fmt.Errorf("getAuthors: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var a model.Author
		var info sql.NullString
		err := rows.Scan(&a.ID, &a.Name, &info)
		if err != nil {
			return nil, fmt.Errorf("scan author: %w", err)
		}
		if info.Valid {
			a.Info = info.String
		}
		ret[a.ID] = a
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("getAuthors iteration: %w", err)
	}
	return ret, nil
}

// getSequences fetches sequences for given IDs, returns map by ID.
func (db *DB) getSequences(seqIDs []string) (map[string]model.SequenceRef, error) {
	ret := make(map[string]model.SequenceRef)
	if len(seqIDs) == 0 {
		return ret, nil
	}

	rows, err := db.conn.Query(
		"SELECT id, name, info FROM sequences WHERE id = ANY($1)",
		pq.Array(seqIDs),
	)
	if err != nil {
		return nil, fmt.Errorf("getSequences: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var s model.SequenceRef
		var info sql.NullString
		err := rows.Scan(&s.ID, &s.Name, &info)
		if err != nil {
			return nil, fmt.Errorf("scan sequence: %w", err)
		}
		ret[s.ID] = s
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("getSequences iteration: %w", err)
	}
	return ret, nil
}
// Package db provides database access for books.
package db

import (
	"database/sql"
	"fmt"
	"strconv"
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

// GetRandomBooks returns random books from the database.
func (db *DB) GetRandomBooks(limit int) ([]model.Book, error) {
	var raw []BookRaw
	var err error
	raw, err = db.fetchBooks("ORDER BY random()", limit, 0)
	if err != nil {
		return nil, err
	}
	return assembleBooks(db, raw)
}

// GetRandomBooksByGenre returns random books filtered by genre.
func (db *DB) GetRandomBooksByGenre(genre string, limit int) ([]model.Book, error) {
	query := `
		SELECT zipfile, filename, genres, authors, sequences, book_id, lang, date, size, deleted
		FROM books
		WHERE genres && ARRAY[$1]::text[]
		ORDER BY random()
		LIMIT $2
	`
	rows, err := db.conn.Query(query, genre, limit)
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
func assembleBooks(_ *DB, raw []BookRaw) ([]model.Book, error) {
	if len(raw) == 0 {
		return []model.Book{}, nil
	}

	// TODO: This will be refactored to accept db pointer for lookups
	// For now, return basic book data

	result := make([]model.Book, len(raw))
	for i, r := range raw {
		var datePtr *time.Time
		if r.Date.Valid {
			datePtr = &r.Date.Time
		}
		var deletedPtr *bool
		if r.Deleted.Valid {
			deletedPtr = &r.Deleted.Bool
		}
		book := model.Book{
			Zipfile:    r.Zipfile,
			Filename:   r.Filename,
			Genres:     r.Genres,
			BookID:     r.BookID,
			Lang:       r.Lang,
			Date:       datePtr,
			Size:       r.Size,
			Deleted:    deletedPtr,
			BookTitle:  r.BookID,
			Annotation: "",
		}

		if book.Date != nil {
			book.DateTime = book.Date.Format("2006-01-02") + "_00:00"
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
	Date         *sql.NullTime
	Size         int
	Deleted      *sql.NullBool
}

// scanBookRows scans rows from books table into BookRaw structs.
func scanBookRows(rows *sql.Rows) ([]BookRaw, error) {
	var books []BookRaw
	for rows.Next() {
		var b BookRaw
		err := rows.Scan(
			&b.Zipfile, &b.Filename, &b.Genres,
			&b.AuthorsRaw, &b.SequencesRaw,
			&b.BookID, &b.Lang, &b.Date, &b.Size, &b.Deleted,
		)
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

// ignore unused import warning
var _ = strconv.Itoa
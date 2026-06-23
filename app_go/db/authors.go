package db

import (
	"database/sql"
	"fmt"
	"strings"

	"fb2srv_go/model"
	"github.com/lib/pq"
)

// GetAuthorsByID fetches authors for given IDs, returns map by ID.
func (db *DB) GetAuthorsByID(authorIDs []string) (map[string]model.Author, error) {
	return db.getAuthors(authorIDs)
}

// SearchAuthors searches authors by name using ILIKE with multiple terms.
func (db *DB) SearchAuthors(query string, limit int) ([]model.Author, error) {
	terms := strings.Fields(query)
	if len(terms) == 0 {
		return []model.Author{}, nil
	}

	conditions := make([]string, len(terms))
	args := make([]interface{}, len(terms)+1)
	args[len(terms)] = limit
	for i, term := range terms {
		conditions[i] = fmt.Sprintf("name ILIKE $%d", i+1)
		args[i] = "%" + term + "%"
	}

	sql := fmt.Sprintf(
		"SELECT id, name, info FROM authors WHERE %s LIMIT $%d",
		strings.Join(conditions, " AND "),
		len(terms)+1,
	)

	rows, err := db.conn.Query(sql, args...)
	if err != nil {
		return nil, fmt.Errorf("SearchAuthors: %w", err)
	}
	defer rows.Close()

	return scanAuthorRows(rows)
}

// GetRandomAuthors returns random authors from the database.
func (db *DB) GetRandomAuthors(limit int) ([]model.Author, error) {
	rows, err := db.conn.Query(
		"SELECT id, name, info FROM authors ORDER BY random() LIMIT $1",
		limit,
	)
	if err != nil {
		return nil, fmt.Errorf("GetRandomAuthors: %w", err)
	}
	defer rows.Close()

	return scanAuthorRows(rows)
}

// GetAuthorsByName searches for authors whose name contains the given prefix.
func (db *DB) GetAuthorsByName(prefix string, limit int) ([]model.Author, error) {
	rows, err := db.conn.Query(
		"SELECT id, name, info FROM authors WHERE name ILIKE $1 LIMIT $2",
		"%"+prefix+"%",
		limit,
	)
	if err != nil {
		return nil, fmt.Errorf("GetAuthorsByName: %w", err)
	}
	defer rows.Close()

	return scanAuthorRows(rows)
}

// scanAuthorRows scans rows from authors table into Author structs.
func scanAuthorRows(rows *sql.Rows) ([]model.Author, error) {
	var authors []model.Author
	for rows.Next() {
		var a model.Author
		var info sql.NullString
		err := rows.Scan(&a.ID, &a.Name, &info)
		if err != nil {
			return nil, fmt.Errorf("scanAuthorRows: %w", err)
		}
		if info.Valid {
			a.Info = info.String
		}
		authors = append(authors, a)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("scanAuthorRows iteration: %w", err)
	}
	return authors, nil
}

// AuthorCount returns the total number of authors.
func (db *DB) AuthorCount() (int, error) {
	var count int
	err := db.conn.QueryRow("SELECT count(*) FROM authors").Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("AuthorCount: %w", err)
	}
	return count, nil
}

// getAuthorsByIDsForSearch is a batch lookup used internally.
func (db *DB) getAuthorsByIDsForSearch(ids []string) ([]model.Author, error) {
	if len(ids) == 0 {
		return []model.Author{}, nil
	}
	rows, err := db.conn.Query(
		"SELECT id, name, info FROM authors WHERE id = ANY($1)",
		pq.Array(ids),
	)
	if err != nil {
		return nil, fmt.Errorf("getAuthorsByIDsForSearch: %w", err)
	}
	defer rows.Close()
	return scanAuthorRows(rows)
}
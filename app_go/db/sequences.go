package db

import (
	"database/sql"
	"fmt"
	"strings"

	"fb2srv_go/model"
	"github.com/lib/pq"
)

// GetSequencesByID fetches sequences for given IDs, returns map by ID.
func (db *DB) GetSequencesByID(seqIDs []string) (map[string]model.Sequence, error) {
	ret := make(map[string]model.Sequence)
	if len(seqIDs) == 0 {
		return ret, nil
	}

	rows, err := db.conn.Query(
		"SELECT id, name, info FROM sequences WHERE id = ANY($1)",
		pq.Array(seqIDs),
	)
	if err != nil {
		return nil, fmt.Errorf("GetSequencesByID: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var s model.Sequence
		var info sql.NullString
		err := rows.Scan(&s.ID, &s.Name, &info)
		if err != nil {
			return nil, fmt.Errorf("scan sequence: %w", err)
		}
		if info.Valid {
			s.Info = info.String
		}
		ret[s.ID] = s
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("GetSequencesByID iteration: %w", err)
	}
	return ret, nil
}

// SearchSequences searches sequences by name using ILIKE with multiple terms.
func (db *DB) SearchSequences(query string, limit int) ([]model.Sequence, error) {
	terms := strings.Fields(query)
	if len(terms) == 0 {
		return []model.Sequence{}, nil
	}

	conditions := make([]string, len(terms))
	args := make([]interface{}, len(terms)+1)
	args[len(terms)] = limit
	for i, term := range terms {
		conditions[i] = fmt.Sprintf("name ILIKE $%d", i+1)
		args[i] = "%" + term + "%"
	}

	sql := fmt.Sprintf(
		"SELECT id, name, info FROM sequences WHERE %s LIMIT $%d",
		strings.Join(conditions, " AND "),
		len(terms)+1,
	)

	rows, err := db.conn.Query(sql, args...)
	if err != nil {
		return nil, fmt.Errorf("SearchSequences: %w", err)
	}
	defer rows.Close()

	return scanSequenceRows(rows)
}

// GetRandomSequences returns random sequences from the database.
func (db *DB) GetRandomSequences(limit int) ([]model.Sequence, error) {
	rows, err := db.conn.Query(
		"SELECT id, name, info FROM sequences ORDER BY random() LIMIT $1",
		limit,
	)
	if err != nil {
		return nil, fmt.Errorf("GetRandomSequences: %w", err)
	}
	defer rows.Close()

	return scanSequenceRows(rows)
}

// SequenceCount returns the total number of sequences.
func (db *DB) SequenceCount() (int, error) {
	var count int
	err := db.conn.QueryRow("SELECT count(*) FROM sequences").Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("SequenceCount: %w", err)
	}
	return count, nil
}

// scanSequenceRows scans rows from sequences table into Sequence structs.
func scanSequenceRows(rows *sql.Rows) ([]model.Sequence, error) {
	var seqs []model.Sequence
	for rows.Next() {
		var s model.Sequence
		var info sql.NullString
		err := rows.Scan(&s.ID, &s.Name, &info)
		if err != nil {
			return nil, fmt.Errorf("scanSequenceRows: %w", err)
		}
		if info.Valid {
			s.Info = info.String
		}
		seqs = append(seqs, s)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("scanSequenceRows iteration: %w", err)
	}
	return seqs, nil
}
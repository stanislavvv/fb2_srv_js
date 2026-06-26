package db

import (
	"database/sql"
	"fmt"
	"strings"

	"fb2srv_go/config"
)

// float32SliceToVectorStr converts a []float32 to a pgvector-compatible string format "[v1,v2,...]".
// The vector text input accepts bracket format. This is more reliable than halfvec text input
// which may fail when passed through lib/pq's text parameter encoding.
func float32SliceToVectorStr(vector []float32) string {
	parts := make([]string, len(vector))
	for i, v := range vector {
		parts[i] = fmt.Sprintf("%g", v)
	}
	return "[" + strings.Join(parts, ",") + "]"
}

// GetNearestIDs finds the nearest vector embeddings by L2 distance.
// vector is the query embedding, limit is the max number of results.
// We cast the halfvec column to vector for comparison, which works reliably with text parameters.
func (db *DB) GetNearestIDs(vector []float32, limit int) ([]string, error) {
	query := `
		SELECT id FROM vectors
		WHERE is_bad = false
		ORDER BY embedding::vector <-> $1::vector
		LIMIT $2
	`

	rows, err := db.conn.Query(query, float32SliceToVectorStr(vector), limit)
	if err != nil {
		return nil, fmt.Errorf("GetNearestIDs (vector extension may not be installed): %w", err)
	}
	defer rows.Close()

	var ids []string
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			return nil, fmt.Errorf("scan vector id: %w", err)
		}
		ids = append(ids, id)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("GetNearestIDs iteration: %w", err)
	}
	return ids, nil
}

// GetNearestIDsWithType finds nearest vectors filtered by type.
// typeStr: "book_title", "book_anno", "sequence_name", "author_name"
func (db *DB) GetNearestIDsWithType(vector []float32, typeStr string, limit int) ([]string, error) {
	query := `
		SELECT id FROM vectors
		WHERE is_bad = false AND type = $1::vector_type
		ORDER BY embedding::vector <-> $2::vector
		LIMIT $3
	`

	rows, err := db.conn.Query(query, typeStr, float32SliceToVectorStr(vector), limit)
	if err != nil {
		return nil, fmt.Errorf("GetNearestIDsWithType (%s): %w", typeStr, err)
	}
	defer rows.Close()

	var ids []string
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			return nil, fmt.Errorf("scan vector id: %w", err)
		}
		ids = append(ids, id)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("GetNearestIDsWithType iteration: %w", err)
	}
	return ids, nil
}

// VectorCount returns the total number of vector records.
func (db *DB) VectorCount() (int, error) {
	var count int
	err := db.conn.QueryRow("SELECT count(*) FROM vectors").Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("VectorCount: %w", err)
	}
	return count, nil
}

// VectorSize returns the configured vector dimension size.
func VectorSize() int {
	_ = sql.ErrNoRows
	return config.VECTOR_SIZE
}
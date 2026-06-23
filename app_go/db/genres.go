package db

import (
	"database/sql"
	"fmt"

	"fb2srv_go/model"
)

// GetGenresMeta returns all meta genres (genre groups).
func (db *DB) GetGenresMeta() ([]model.GenresMeta, error) {
	rows, err := db.conn.Query(
		"SELECT meta_id, name, description FROM genres_meta ORDER BY name",
	)
	if err != nil {
		return nil, fmt.Errorf("GetGenresMeta: %w", err)
	}
	defer rows.Close()

	var result []model.GenresMeta
	for rows.Next() {
		var g model.GenresMeta
		var desc sql.NullString
		err := rows.Scan(&g.MetaID, &g.Name, &desc)
		if err != nil {
			return nil, fmt.Errorf("scan genres_meta: %w", err)
		}
		if desc.Valid {
			g.Description = desc.String
		}
		result = append(result, g)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("GetGenresMeta iteration: %w", err)
	}
	return result, nil
}

// GetGenresByMetaID returns all genres belonging to a meta genre group.
func (db *DB) GetGenresByMetaID(metaID string) ([]model.Genre, error) {
	rows, err := db.conn.Query(
		"SELECT id, meta_id, name, description FROM genres WHERE meta_id = $1 ORDER BY name",
		metaID,
	)
	if err != nil {
		return nil, fmt.Errorf("GetGenresByMetaID: %w", err)
	}
	defer rows.Close()

	var result []model.Genre
	for rows.Next() {
		var g model.Genre
		var desc sql.NullString
		err := rows.Scan(&g.ID, &g.MetaID, &g.Name, &desc)
		if err != nil {
			return nil, fmt.Errorf("scan genre: %w", err)
		}
		if desc.Valid {
			g.Description = desc.String
		}
		result = append(result, g)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("GetGenresByMetaID iteration: %w", err)
	}
	return result, nil
}

// GetAllGenres returns all genres from the genres table.
func (db *DB) GetAllGenres() ([]model.Genre, error) {
	rows, err := db.conn.Query(
		"SELECT id, meta_id, name, description FROM genres ORDER BY name",
	)
	if err != nil {
		return nil, fmt.Errorf("GetAllGenres: %w", err)
	}
	defer rows.Close()

	var result []model.Genre
	for rows.Next() {
		var g model.Genre
		var desc sql.NullString
		err := rows.Scan(&g.ID, &g.MetaID, &g.Name, &desc)
		if err != nil {
			return nil, fmt.Errorf("scan genre: %w", err)
		}
		if desc.Valid {
			g.Description = desc.String
		}
		result = append(result, g)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("GetAllGenres iteration: %w", err)
	}
	return result, nil
}

// GetGenreByID returns a single genre by its ID.
func (db *DB) GetGenreByID(id string) (*model.Genre, error) {
	var g model.Genre
	var desc sql.NullString
	err := db.conn.QueryRow(
		"SELECT id, meta_id, name, description FROM genres WHERE id = $1",
		id,
	).Scan(&g.ID, &g.MetaID, &g.Name, &desc)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("GetGenreByID: %w", err)
	}
	if desc.Valid {
		g.Description = desc.String
	}
	return &g, nil
}

// GenreCount returns the total number of genres.
func (db *DB) GenreCount() (int, error) {
	var count int
	err := db.conn.QueryRow("SELECT count(*) FROM genres").Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("GenreCount: %w", err)
	}
	return count, nil
}
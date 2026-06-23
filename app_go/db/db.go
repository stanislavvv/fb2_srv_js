// Package db provides database access layer with raw SQL queries.
package db

import (
	"database/sql"
	"fmt"

	"fb2srv_go/config"
	_ "github.com/lib/pq"
)

// DB wraps a sql.DB connection pool.
type DB struct {
	conn *sql.DB
}

// NewDB creates a new database connection pool from the application config.
func NewDB(cfg *config.Config) (*DB, error) {
	dsn := fmt.Sprintf(
		"host=%s port=5432 user=%s password=%s dbname=%s sslmode=disable",
		cfg.Get("PG_HOST"),
		cfg.Get("PG_USER"),
		cfg.Get("PG_PASS"),
		cfg.Get("PG_BASE"),
	)

	conn, err := sql.Open("postgres", dsn)
	if err != nil {
		return nil, fmt.Errorf("sql.Open: %w", err)
	}

	// Verify the connection is actually working
	err = conn.Ping()
	if err != nil {
		return nil, fmt.Errorf("db ping: %w", err)
	}

	return &DB{conn: conn}, nil
}

// Close closes the database connection pool.
func (db *DB) Close() error {
	return db.conn.Close()
}

// Conn returns the underlying *sql.DB for direct access.
func (db *DB) Conn() *sql.DB {
	return db.conn
}
package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"fb2srv_go/config"
	"fb2srv_go/db"
	"fb2srv_go/handler"
)

func main() {
	// Load config
	cfgPath := "config.ini"
	if len(os.Args) > 1 {
		cfgPath = os.Args[1]
	}

	cfg := config.LoadConfig(cfgPath)

	// Load genres from file
	if err := handler.InitGenres("genres.list"); err != nil {
		fmt.Printf("WARN: Could not load genres.list: %v\n", err)
	}
	// Load meta genre names
	if err := handler.LoadMetaNames("genres_meta.list"); err != nil {
		fmt.Printf("WARN: Could not load genres_meta.list: %v\n", err)
	}

	// Init database
	var database *db.DB
	var err error
	database, err = db.NewDB(cfg)
	if err != nil {
		fmt.Printf("WARN: Could not connect to database: %v\n", err)
		fmt.Println("Running without database (file-based mode only)")
	} else {
		fmt.Printf("DB connected: %s@%s/%s\n",
			cfg.Get("PG_USER"), cfg.Get("PG_HOST"), cfg.Get("PG_BASE"))
		defer database.Close()
	}

	// Create server with all routes
	srv := handler.NewServer(cfg, database)

	// Setup HTTP server
	addr := fmt.Sprintf("%s:%s", cfg.Get("LISTEN_HOST"), cfg.Get("LISTEN_PORT"))
	httpSrv := &http.Server{
		Addr:    addr,
		Handler: srv.Router,
	}

	// Graceful shutdown
	go func() {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
		<-sigChan
		fmt.Println("\nShutting down server...")
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := httpSrv.Shutdown(ctx); err != nil {
			log.Printf("Server shutdown error: %v", err)
		}
	}()

	fmt.Printf("OPDS server starting on http://%s\n", addr)
	if root := cfg.Get("APPLICATION_ROOT"); root != "" {
		fmt.Printf("Application root: %s\n", root)
	}

	if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}

	fmt.Println("Server stopped")
}

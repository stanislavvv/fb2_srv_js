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
	"fb2srv_go/util"
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

	// Init XSLT for FB2->HTML transformation
	xsltFile := cfg.Get("FB2_XSLT")
	if xsltFile == "" {
		xsltFile = "fb2_to_html.xsl"
	}
	var xslt *util.XSLTTransform
	xslt, err = util.NewXSLTTransform(xsltFile)
	if err != nil {
		fmt.Printf("WARN: Could not load XSLT stylesheet: %v\n", err)
		fmt.Println("XSLT-based reading will be disabled")
	}

	// Create server with all routes
	srv := handler.NewServer(cfg, database, xslt)

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

	// Debug output for configuration
	if cfg.DEBUG == "yes" || cfg.DEBUG == "true" || cfg.DEBUG == "YES" {
		fmt.Println("\n=== CONFIG DEBUG ===")
		fmt.Printf("  DEBUG:                %s\n", cfg.DEBUG)
		fmt.Printf("  APPLICATION_ROOT:     '%s'\n", cfg.Get("APPLICATION_ROOT"))
		fmt.Printf("  LISTEN_HOST:          %s\n", cfg.LISTEN_HOST)
		fmt.Printf("  LISTEN_PORT:          %s\n", cfg.LISTEN_PORT)
		fmt.Printf("  PAGES:                '%s'\n", cfg.PAGES)
		fmt.Printf("  ZIPS:                 '%s'\n", cfg.ZIPS)
		fmt.Printf("  VECTOR_SEARCH:        %s\n", cfg.VECTOR_SEARCH)
		fmt.Printf("  CACHE_TIME:           %s\n", cfg.CACHE_TIME)
		fmt.Printf("  CACHE_TIME_RND:       %s\n", cfg.CACHE_TIME_RND)
		fmt.Printf("  PAGE_SIZE:            %s\n", cfg.PAGE_SIZE)
		fmt.Println("")

		// Print all URLs
		urls := config.GetURLs()
		fmt.Println("  URLs:")
		fmt.Printf("    Start:              '%s'\n", urls.Start)
		fmt.Printf("    Author:             '%s'\n", urls.Author)
		fmt.Printf("    AuthIdx:            '%s'\n", urls.AuthIdx)
		fmt.Printf("    Seq:                '%s'\n", urls.Seq)
		fmt.Printf("    SeqIdx:             '%s'\n", urls.SeqIdx)
		fmt.Printf("    Genre:              '%s'\n", urls.Genre)
		fmt.Printf("    GenIdx:             '%s'\n", urls.GenIdx)
		fmt.Printf("    Search:             '%s'\n", urls.Search)
		fmt.Printf("    SrchAuth:           '%s'\n", urls.SrchAuth)
		fmt.Printf("    SrchSeq:            '%s'\n", urls.SrchSeq)
		fmt.Printf("    SrchBook:           '%s'\n", urls.SrchBook)
		fmt.Printf("    SrchBookAnno:       '%s'\n", urls.SrchBookAnno)
		fmt.Printf("    SrchBookAnnoVector: '%s'\n", urls.SrchBookAnnoVector)
		fmt.Printf("    RndBook:            '%s'\n", urls.RndBook)
		fmt.Printf("    RndSeq:             '%s'\n", urls.RndSeq)
		fmt.Printf("    RndGen:             '%s'\n", urls.RndGen)
		fmt.Printf("    RndGenIdx:          '%s'\n", urls.RndGenIdx)
		fmt.Printf("    Time:               '%s'\n", urls.Time)
		fmt.Printf("    Read:               '%s'\n", urls.Read)
		fmt.Printf("    Dl:                 '%s'\n", urls.Dl)
		fmt.Printf("    Plain:              '%s'\n", urls.Plain)
		fmt.Printf("    Cover:              '%s'\n", urls.Cover)
		fmt.Printf("    XslRead:            '%s'\n", urls.XslRead)
		fmt.Println("")

		// URLs with APPLICATION_ROOT prefix
		appRoot := cfg.APPLICATION_ROOT
		if appRoot != "" {
			fmt.Println("  URLs WITH APPLICATION_ROOT PREFIX:")
			fmt.Printf("    Start:              '%s%s'\n", appRoot, urls.Start)
			fmt.Printf("    Author:             '%s%s'\n", appRoot, urls.Author)
			fmt.Printf("    AuthIdx:            '%s%s'\n", appRoot, urls.AuthIdx)
			fmt.Printf("    Seq:                '%s%s'\n", appRoot, urls.Seq)
			fmt.Printf("    SeqIdx:             '%s%s'\n", appRoot, urls.SeqIdx)
			fmt.Printf("    Genre:              '%s%s'\n", appRoot, urls.Genre)
			fmt.Printf("    GenIdx:             '%s%s'\n", appRoot, urls.GenIdx)
			fmt.Printf("    Search:             '%s%s'\n", appRoot, urls.Search)
			fmt.Printf("    Time:               '%s%s'\n", appRoot, urls.Time)
			fmt.Printf("    Read:               '%s%s'\n", appRoot, urls.Read)
			fmt.Printf("    Dl:                 '%s%s'\n", appRoot, urls.Dl)
			fmt.Printf("    Cover:              '%s%s'\n", appRoot, urls.Cover)
		}
		fmt.Println("=== END CONFIG DEBUG ===\n")
	}

	if err := httpSrv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}

	fmt.Println("Server stopped")
}

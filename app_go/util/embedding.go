// Package util provides utility functions for fb2srv.
package util

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"

	"fb2srv_go/config"
)

// EmbeddingRequest is the JSON body for OpenAI-compatible embeddings API.
type embeddingRequest struct {
	Model      string `json:"model"`
	Input      string `json:"input"`
	Dimensions int    `json:"dimensions,omitempty"`
}

// EmbeddingData holds a single embedding result.
type embeddingData struct {
	Embedding []float64 `json:"embedding"`
}

// EmbeddingResponse is the JSON response from OpenAI-compatible embeddings API.
type embeddingResponse struct {
	Data []embeddingData `json:"data"`
}

// GetVector returns a float32 embedding vector for the given text.
// It uses the OpenAI-compatible REST API configured in Config.
// Returns nil if the text is empty or the API call fails.
func GetVector(cfg *config.Config, text string) []float32 {
	if text == "" || strings.TrimSpace(text) == "" {
		return nil
	}

	// Build request
	url := cfg.Get("OPENAI_URL")
	if !strings.HasSuffix(url, "/v1") {
		// Ensure base_url ends with /v1, then append /embeddings
		if !strings.HasSuffix(url, "/") {
			url += "/v1"
		} else {
			url += "v1"
		}
	}
	url += "/embeddings"

	reqBody := embeddingRequest{
		Model:      cfg.Get("OPENAI_MODEL"),
		Input:      text,
		Dimensions: config.VECTOR_SIZE,
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		fmt.Printf("GetVector marshal error: %v\n", err)
		return nil
	}

	// HTTP request
	req, err := http.NewRequest("POST", url, bytes.NewReader(jsonData))
	if err != nil {
		fmt.Printf("GetVector new request error: %v\n", err)
		return nil
	}

	req.Header.Set("Content-Type", "application/json")
	apiKey := cfg.Get("OPENAI_KEY")
	if apiKey != "" && apiKey != "-" {
		req.Header.Set("Authorization", "Bearer "+apiKey)
	}

	// Execute
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("GetVector HTTP error: %v\n", err)
		return nil
	}
	defer resp.Body.Close()

	// Read body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("GetVector read body error: %v\n", err)
		return nil
	}

	if resp.StatusCode != http.StatusOK {
		fmt.Printf("GetVector API error: status=%d body=%s\n", resp.StatusCode, string(body))
		return nil
	}

	// Parse response
	var embResp embeddingResponse
	err = json.Unmarshal(body, &embResp)
	if err != nil {
		fmt.Printf("GetVector unmarshal error: %v body=%s\n", err, string(body))
		return nil
	}

	if len(embResp.Data) == 0 {
		return nil
	}

	// Convert float64[] to float32[]
	embedding := embResp.Data[0].Embedding
	result := make([]float32, len(embedding))
	for i, v := range embedding {
		result[i] = float32(v)
	}

	return result
}
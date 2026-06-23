package util

import (
	"html"
)

// XMLEscape escapes special XML characters.
func XMLEscape(s string) string {
	return html.EscapeString(s)
}

// HTMLRefine refines HTML text (simplified version).
// This is a basic implementation - a full version would use an HTML parser.
func HTMLRefine(txt string) string {
	// For now, just return as-is
	// A full implementation would use goquery or similar
	if txt == "" {
		return ""
	}
	return txt
}
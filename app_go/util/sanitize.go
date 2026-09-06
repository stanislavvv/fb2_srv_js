// Package util provides shared helper functions.
//
// This file contains XSS-sanitizing helpers mirroring the Python
// implementation in app/sanitize.py. They are applied to backend-rendered
// HTML content (FB2 book body and OPDS entry annotation/pubinfo/bio) before
// it is sent to the client.
package util

import (
	"bytes"
	"html"
	"strings"
	"unicode"

	xhtml "golang.org/x/net/html"
)

// dangerousTags is the set of element names that are removed together with
// their content because they can execute or load arbitrary resources.
var dangerousTags = map[string]bool{
	"script":   true,
	"iframe":   true,
	"frame":    true,
	"frameset": true,
	"object":   true,
	"embed":    true,
	"applet":   true,
	"form":     true,
	"input":    true,
	"button":   true,
	"textarea": true,
	"select":   true,
	"option":   true,
	"noscript": true,
	"base":     true,
	"link":     true,
	"svg":      true,
	"math":     true,
}

// urlAttrs are attributes that hold URLs and may therefore carry
// javascript: and similar schemes.
var urlAttrs = map[string]bool{
	"href":     true,
	"src":      true,
	"action":   true,
	"formaction": true,
	"data":     true,
}

// safeURLPrefixes are the URL schemes allowed in urlAttrs.
// Note: data: is allowed only for image content types (covers).
var safeURLPrefixes = []string{
	"http://", "https://", "mailto:", "ftp://", "ftps://",
	"tel:", "sms:", "irc:", "ircs:", "data:image/",
}

// sanitizeRootID is a temporary wrapper used so that a fragment can be
// parsed and then re-emitted without the implicit <html>/<head>/<body> that
// the html5 parser always builds.
const sanitizeRootID = "__sanitize_root__"

// isDangerousTag reports whether an element name must be removed.
func isDangerousTag(tagName string) bool {
	return dangerousTags[strings.ToLower(tagName)]
}

// isURLAttr reports whether an attribute key holds a URL value.
func isURLAttr(key string) bool {
	return urlAttrs[strings.ToLower(key)]
}

// isSafeURL reports whether a URL value is safe to keep in an attribute.
func isSafeURL(value string) bool {
	if value == "" {
		return true
	}
	v := strings.ToLower(value)
	v = strings.ReplaceAll(v, "\x00", "")
	v = strings.ReplaceAll(v, "\t", " ")
	v = strings.ReplaceAll(v, "\n", " ")
	v = strings.ReplaceAll(v, "\r", " ")
	v = strings.Join(strings.Fields(v), " ")
	v = strings.TrimSpace(v)
	if v == "" {
		return true
	}
	if strings.HasPrefix(v, "#") {
		return true
	}
	for _, p := range safeURLPrefixes {
		if strings.HasPrefix(v, p) {
			return true
		}
	}
	// No explicit scheme -> treat as a relative path.
	beforeSlash := v
	if i := strings.IndexByte(v, '/'); i >= 0 {
		beforeSlash = v[:i]
	}
	if !strings.Contains(beforeSlash, ":") {
		return true
	}
	return false
}

// cleanAttrs drops on* handlers and neutralizes unsafe URL/style values.
func cleanAttrs(n *xhtml.Node) {
	if n.Type != xhtml.ElementNode {
		return
	}
	kept := make([]xhtml.Attribute, 0, len(n.Attr))
	for _, a := range n.Attr {
		key := strings.ToLower(a.Key)
		if strings.HasPrefix(key, "on") {
			continue
		}
		if isURLAttr(key) && !isSafeURL(a.Val) {
			a.Val = "#"
		}
		if key == "style" {
			low := strings.ToLower(a.Val)
			if strings.Contains(low, "javascript:") ||
				strings.Contains(low, "vbscript:") ||
				strings.Contains(low, "expression(") {
				continue
			}
		}
		kept = append(kept, a)
	}
	n.Attr = kept
}

// sanitizeNode removes comments and dangerous elements, and cleans the
// attributes of everything that remains (recursively).
func sanitizeNode(n *xhtml.Node) {
	for c := n.FirstChild; c != nil; {
		next := c.NextSibling
		if c.Type == xhtml.CommentNode {
			n.RemoveChild(c)
		} else if c.Type == xhtml.ElementNode && isDangerousTag(c.Data) {
			n.RemoveChild(c)
		} else {
			cleanAttrs(c)
			sanitizeNode(c)
		}
		c = next
	}
}

// findSanitizeRoot returns the temporary wrapper div node.
func findSanitizeRoot(doc *xhtml.Node) *xhtml.Node {
	var found *xhtml.Node
	var walk func(n *xhtml.Node)
	walk = func(n *xhtml.Node) {
		if found != nil {
			return
		}
		if n.Type == xhtml.ElementNode && n.Data == "div" {
			for _, a := range n.Attr {
				if a.Key == "id" && a.Val == sanitizeRootID {
					found = n
					return
				}
			}
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(doc)
	return found
}

// SanitizeHTML strips dangerous elements/attributes from an HTML string
// produced from FB2 (book body) or composed for OPDS entries (annotation +
// pubinfo + sequence name). It preserves regular formatting markup so the
// reader interface keeps working.
func SanitizeHTML(s string) string {
	if s == "" {
		return ""
	}
	trimmed := strings.TrimLeftFunc(s, unicode.IsSpace)
	lower := strings.ToLower(trimmed)
	isFullDoc := strings.HasPrefix(lower, "<html") || strings.HasPrefix(lower, "<!doctype")

	var doc *xhtml.Node
	var err error
	if isFullDoc {
		doc, err = xhtml.Parse(strings.NewReader(s))
	} else {
		wrapped := `<div id="` + sanitizeRootID + `">` + s + `</div>`
		doc, err = xhtml.Parse(strings.NewReader(wrapped))
	}
	if err != nil {
		return html.EscapeString(s)
	}

	sanitizeNode(doc)

	var b bytes.Buffer
	if isFullDoc {
		if err := xhtml.Render(&b, doc); err != nil {
			return html.EscapeString(s)
		}
		return b.String()
	}

	root := findSanitizeRoot(doc)
	if root == nil {
		if err := xhtml.Render(&b, doc); err != nil {
			return html.EscapeString(s)
		}
		return b.String()
	}
	for c := root.FirstChild; c != nil; c = c.NextSibling {
		if err := xhtml.Render(&b, c); err != nil {
			break
		}
	}
	return b.String()
}

// EscapeHTML escapes plain text so it can be embedded into HTML safely.
func EscapeHTML(text string) string {
	return html.EscapeString(text)
}

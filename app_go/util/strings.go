// Package util provides string manipulation utilities.
package util

import (
	"crypto/md5"
	"fmt"
	"strings"
	"unicode"

	"golang.org/x/text/unicode/norm"
)

// REPLACEMENT_MAP maps special characters to their normalized string equivalents.
var REPLACEMENT_MAP = map[rune]string{
	// Cyrillic
	'Ё': "Е",
	'Й': "И",
	'Ъ': "Ь",
	// German umlauts (uppercase)
	'Ä': "AE",
	'Ö': "OE",
	'Ü': "UE",
	'ß': "SS",
	// Other common replacements (uppercase)
	'À': "A", 'Á': "A", 'Â': "A", 'Ã': "A", 'Å': "A",
	'È': "E", 'É': "E", 'Ê': "E", 'Ë': "E",
	'Ì': "I", 'Í': "I", 'Î': "I", 'Ï': "I",
	'Ñ': "N",
	'Ò': "O", 'Ó': "O", 'Ô': "O", 'Õ': "O",
	'Ù': "U", 'Ú': "U", 'Û': "U",
	'Ý': "Y",
	'Ç': "C",
	'Þ': "TH",
	'Đ': "D",
	'Ł': "L",
	'Ń': "N",
	'Ǿ': "O",
	'Ŕ': "R",
	'Ś': "S",
	'Ź': "Z",
	'Ż': "Z",
}

// UnicodeUpper performs uppercase conversion with NFKD normalization.
func UnicodeUpper(s string) string {
	// NFKD normalize
	transformed := norm.NFKD.String(s)

	// Remove combining characters (category Mn = Nonspacing_Mark)
	var buf strings.Builder
	for _, r := range transformed {
		if unicode.Is(unicode.Mn, r) {
			continue
		}
		buf.WriteRune(r)
	}
	ret := buf.String()

	// Upper case
	ret = strings.ToUpper(ret)

	// Apply replacements (handle multi-char replacements like Ä->AE)
	var result strings.Builder
	for _, r := range ret {
		if repl, ok := REPLACEMENT_MAP[r]; ok {
			result.WriteString(repl)
		} else {
			result.WriteRune(r)
		}
	}
	return result.String()
}

// StrNormalize normalizes a string for ID generation and comparison.
func StrNormalize(s string) string {
	if s == "" {
		return ""
	}

	// Strip leading/trailing whitespace
	ret := strings.TrimSpace(s)

	// Replace multiple spaces with single space
	for strings.Contains(ret, "  ") {
		ret = strings.ReplaceAll(ret, "  ", " ")
	}

	// Normalize all quote types to double quotes
	ret = strings.ReplaceAll(ret, "«", "\"")
	ret = strings.ReplaceAll(ret, "»", "\"")
	ret = strings.ReplaceAll(ret, "'", "\"")

	// Upper case with unicode normalization
	ret = UnicodeUpper(ret)

	// Normalize quotes again after uppercasing
	ret = strings.ReplaceAll(ret, "«", "\"")
	ret = strings.ReplaceAll(ret, "»", "\"")
	ret = strings.ReplaceAll(ret, "'", "\"")

	// Collect trailing ? and ! (1-4 chars)
	trailingPunct := ""
	i := len(ret) - 1
	for i >= 0 && len(trailingPunct) < 4 {
		ch := ret[i]
		if ch == '?' || ch == '!' {
			trailingPunct = string(ch) + trailingPunct
			i--
		} else {
			break
		}
	}

	// Remove punctuation except parentheses and double quotes
	var result strings.Builder
	for _, ch := range ret {
		switch ch {
		case '(', ')', '"':
			result.WriteRune(ch)
		default:
			if isPunctuation(ch) {
				continue
			}
			result.WriteRune(ch)
		}
	}
	ret = result.String()

	// Strip multiple spaces after punctuation removal
	for strings.Contains(ret, "  ") {
		ret = strings.ReplaceAll(ret, "  ", " ")
	}

	// Strip again
	ret = strings.TrimSpace(ret)

	// Add back trailing punctuation
	if trailingPunct != "" {
		ret = ret + trailingPunct
	}

	return ret
}

// isPunctuation checks if a rune is a punctuation character.
func isPunctuation(r rune) bool {
	punctuation := "`-~=!@#$%^&*_+[]{}\\|;:',.<>/"
	for _, p := range punctuation {
		if r == p {
			return true
		}
	}
	return false
}

// MakeID generates an MD5 hex ID from a normalized string.
func MakeID(name string, nameAsIs bool) string {
	nameStr := "--- unknown ---"
	if name != "" {
		nameStr = name
	}
	normName := nameStr
	if !nameAsIs {
		normName = StrNormalize(nameStr)
	}
	hash := md5.Sum([]byte(normName))
	return fmt.Sprintf("%x", hash[:])
}

// ID2Path converts an ID to a directory path: "1a2b3c..." -> "1a/2b/1a2b3c..."
func ID2Path(id string) string {
	if len(id) < 4 {
		return id
	}
	first := id[:2]
	second := id[2:4]
	return first + "/" + second + "/" + id
}

// ID2PathOnly returns the directory part of ID2Path: "1a2b3c..." -> "1a/2b"
func ID2PathOnly(id string) string {
	if len(id) < 4 {
		return id
	}
	first := id[:2]
	second := id[2:4]
	return first + "/" + second
}

// URLStr URL-encodes a string with custom character replacements.
func URLStr(s string) string {
	if s == "" {
		return ""
	}
	transl := map[byte]string{
		'"':  "%22",
		'\'': "%27",
	}
	var result strings.Builder
	for i := 0; i < len(s); i++ {
		ch := s[i]
		if replacement, ok := transl[ch]; ok {
			result.WriteString(replacement)
		} else {
			result.WriteByte(ch)
		}
	}
	// Now percent-encode the result
	return strings.ReplaceAll(result.String(), " ", "%20")
}

// StripQuotes safely removes symmetric quotes from a string.
func StripQuotes(s string) string {
	if s == "" {
		return ""
	}
	s = strings.TrimSpace(s)
	if len(s) >= 2 {
		if (s[0] == '"' && s[len(s)-1] == '"') || (s[0] == '\'' && s[len(s)-1] == '\'') {
			return s[1 : len(s)-1]
		}
	}
	return s
}
// Package util provides custom sorting utilities.
package util

// Alphabet1 is the primary alphabet (Russian + some extra).
var Alphabet1 = []rune{
	'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й',
	'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф',
	'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я',
}

// Alphabet2 is the secondary alphabet (Latin).
var Alphabet2 = []rune{
	'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
	'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
	'U', 'V', 'W', 'X', 'Y', 'Z',
}

// cmpInArr compares two runes by their position in the given array.
func cmpInArr(arr []rune, c1 rune, c2 rune) int {
	idx1 := -1
	idx2 := -1
	for i, r := range arr {
		if r == c1 {
			idx1 = i
		}
		if r == c2 {
			idx2 = i
		}
	}
	if idx1 >= 0 && idx2 >= 0 {
		if idx1 == idx2 {
			return 0
		} else if idx1 < idx2 {
			return -1
		} else {
			return 1
		}
	}
	return -2 // not found
}

// containsRune checks if a rune is in the array.
func containsRune(arr []rune, c rune) bool {
	for _, r := range arr {
		if r == c {
			return true
		}
	}
	return false
}

// CustomCharCmp compares two characters using custom alphabet order.
func CustomCharCmp(c1 rune, c2 rune) int {
	if c1 == c2 {
		return 0
	}

	in1 := containsRune(Alphabet1, c1)
	in2 := containsRune(Alphabet1, c2)
	inL1 := containsRune(Alphabet2, c1)
	inL2 := containsRune(Alphabet2, c2)

	if in1 && !in2 {
		return -1
	}
	if inL1 && !inL2 && !in2 {
		return -1
	}
	if in2 && !in1 {
		return 1
	}
	if inL2 && !inL1 && !in1 {
		return 1
	}

	// Sort by array order
	if in1 && in2 {
		result := cmpInArr(Alphabet1, c1, c2)
		if result != -2 {
			return result
		}
	}
	if inL1 && inL2 {
		result := cmpInArr(Alphabet2, c1, c2)
		if result != -2 {
			return result
		}
	}

	// Fallback to natural order
	if c1 < c2 {
		return -1
	}
	return 1
}

// CustomAlphabetCmp compares two strings using custom alphabet order.
func CustomAlphabetCmp(str1 string, str2 string) int {
	s1 := []rune(str1)
	s2 := []rune(str2)
	s1len := len(s1)
	s2len := len(s2)
	i := 0

	// Zero-length strings case
	if s1len == 0 {
		if s2len == 0 {
			return 0
		}
		return -1
	}
	if s2len == 0 {
		return 1
	}

	for CustomCharCmp(s1[i], s2[i]) == 0 {
		i++
		if i == s1len {
			if i == s2len {
				return 0
			}
			return -1
		}
		if i == s2len {
			return 1
		}
	}
	return CustomCharCmp(s1[i], s2[i])
}

// BookEntry is used for book title comparison.
type BookEntry struct {
	BookTitle string `json:"book_title"`
}

// CustomAlphabetBookTitleCmp compares two book entries by title.
func CustomAlphabetBookTitleCmp(b1 BookEntry, b2 BookEntry) int {
	return CustomAlphabetCmp(b1.BookTitle, b2.BookTitle)
}

// NameEntry is used for name comparison.
type NameEntry struct {
	Name string `json:"name"`
}

// CustomAlphabetNameCmp compares two name entries by name.
func CustomAlphabetNameCmp(n1 NameEntry, n2 NameEntry) int {
	return CustomAlphabetCmp(n1.Name, n2.Name)
}
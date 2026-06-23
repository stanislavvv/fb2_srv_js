package util

import "fmt"

// SizeofFmt formats a byte count into human-readable format.
// 123456 -> "123.0KiB", 1234567 -> "1.2MiB"
func SizeofFmt(num int, suffix string) string {
	if suffix == "" {
		suffix = "B"
	}
	units := []string{"", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"}
	val := float64(num)
	for i := 0; i < len(units); i++ {
		if val < 1024.0 {
			return fmt.Sprintf("%.1f%s%s", val, units[i], suffix)
		}
		val /= 1024.0
	}
	return fmt.Sprintf("%.1fYi%s", val, suffix)
}
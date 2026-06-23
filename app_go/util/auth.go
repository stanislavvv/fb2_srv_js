package util

import (
	"os"
	"strings"
)

// IsAuth checks if the provided user:password pair is valid.
// It reads the passwd file from {zips_path}/passwd.
// If the file doesn't exist, authentication is disabled (returns true).
func IsAuth(user, password, zipsPath string) bool {
	passwdPath := zipsPath + "/passwd"
	data, err := os.ReadFile(passwdPath)
	if err != nil {
		// File not found or unreadable - no auth mode
		return true
	}
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			continue
		}
		if parts[0] == user && parts[1] == password {
			return true
		}
	}
	return false
}
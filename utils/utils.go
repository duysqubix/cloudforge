/*
Copyright 2022 Vorys <dhuys@vorys.com>

Useful utilities that doesn't fit in a particular group

*/
package utils

import (
	"bufio"
	"os"
)

// Reads a file and returns file contents newline seperated
func ReadFileN(fpath string) []string {
	file, err := os.Open(fpath)
	if err != nil {
		logger.Fatal(err)
	}

	defer file.Close()
	scanner := bufio.NewScanner(file)

	var lines []string
	for scanner.Scan() {
		lines = append(lines, scanner.Text())
	}
	return lines
}

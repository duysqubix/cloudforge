/*
Copyright 2022 Vorys <dhuys@vorys.com>

Useful utilities that doesn't fit in a particular group

*/
package utils

import (
	"bufio"
	"io/ioutil"
	"log"
	"os"
)

// Write to a file
func WriteFile(fpath, content string) {
	f, err := os.Create(fpath)

	if err != nil {
		logger.Fatal(err)
	}

	defer f.Close()

	b := []byte(content)
	if _, err := f.Write(b); err != nil {
		logger.Fatal(err)
	}

}

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

func GenTempFile() *os.File {
	f, err := ioutil.TempFile("/tmp", "tmpfile.*.txt")
	if err != nil {
		log.Fatal(err)
	}
	return f
}

/*
Copyright 2022 Vorys <dhuys@vorys.com>

Useful utilities that doesn't fit in a particular group

*/
package utils

import (
	"bufio"
	"fmt"
	"io/ioutil"
	"log"
	"os"

	"github.com/chigopher/pathlib"
	"github.com/google/uuid"
	"github.com/spf13/afero"
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

// removes duplicates strings in a string slice
func removeDuplicateStr(strSlice []string) []string {
	allKeys := make(map[string]bool)
	list := []string{}

	for _, item := range strSlice {
		if _, value := allKeys[item]; !value {
			allKeys[item] = true
			list = append(list, item)
		}
	}

	return list
}

// returns a unique dirname by appending a UUID string value
// to supplied dirname
func MakeDirUnique(dir *pathlib.Path) *pathlib.Path {
	newName := fmt.Sprintf("%s-%s", dir.Name(), uuid.New().String())

	return pathlib.NewPathAfero(newName, afero.NewOsFs())
}

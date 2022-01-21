/*
Copyright 2022 Duan Uys <dhuys@vorys.com>

Utilities and objects related to replacing tokens within files
with externally defined values.

*/
package utils

import (
	"log"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/chigopher/pathlib"
	"github.com/spf13/afero"
)

// global regexp that finds all values
// encapsulated with `__`
// ex: __MYTOKEN__
const TOKEN_EXPRESSION string = "__(.*?)__"

// Object that holds an entire directory
// in memory and performs token replacement.
// And dumps final result to a default TMPDIR_PATH
type Tokenizer struct {
	tree     *map[string]string
	tokens   *map[string]string
	rootDir  *pathlib.Path
	destPath *pathlib.Path
}

// create new tokenizer object
func TokenizerNew(tokens *map[string]string) *Tokenizer {

	rootDir := GetCwd()

	return &Tokenizer{
		tree:     &map[string]string{},
		tokens:   tokens,
		rootDir:  rootDir,
		destPath: pathlib.NewPathAfero("/", afero.NewMemMapFs()),
	}
}

// recursivly traverses a directory and reads the objects
// encountered. A directory will cause the method to be
// invoked again. Any file encountered that passes the conditions
// will be read and file contents stored within internal `Tokenizer.tree`
func (t *Tokenizer) traverseDirectory(path *pathlib.Path) {
	matches, _ := path.Glob("*")

	for _, match := range matches {
		is_dir, _ := match.IsDir()
		if is_dir && match.Name() != "sandbox" {
			t.traverseDirectory(match)
		}

		is_file, _ := match.IsFile()
		if is_file && strings.Contains(filepath.Ext(match.Name()), ".tf") {
			absolute_path := match.String()
			f_content, err := match.ReadFile()

			if err != nil {
				log.Fatal(err)
			}
			(*t.tree)[absolute_path] = string(f_content)
		}
	}
}

// Maps and reads directory starting from path as
// defined in Tokenizer.RootDir()
func (t *Tokenizer) ReadRoot() {
	root := t.RootDir()
	t.traverseDirectory(root)
}

// combines both validation and replacement of tokens
// will panic if unused tokens have not been replaced
func (t *Tokenizer) ReplaceAndValidateTokens(tokens *map[string]string) {
	t.ReplaceTokens(tokens)
	results := t.ValidateTokens(tokens)
	if len(*results) != 0 {
		logger.Fatalf("The following tokens have not been parsed: %v", *results)
	}
}

// validation process that identified unused tokens
func (t *Tokenizer) ValidateTokens(tokens *map[string]string) *[]string {
	r := regexp.MustCompile(TOKEN_EXPRESSION)
	validationErrors := []string{}

	for _, fcontent := range *t.tree {

		results := r.FindAllString(fcontent, -1)
		if results != nil {
			validationErrors = append(validationErrors, results...)
		}
	}

	validationErrors = removeDuplicateStr(validationErrors)
	return &validationErrors
}

// handles physical replacement of tokens within Tokenizer.tree
// with values defined by supplied parameter
func (t *Tokenizer) ReplaceTokens(tokens *map[string]string) {
	var toLog bool = true
	for fpath, fcontent := range *t.tree {
		for token, value := range *tokens {
			if toLog {
				logger.Infof("Setting token: __%v__", token)
			}
			fcontent = strings.ReplaceAll(fcontent, "__"+token+"__", value)
		}
		toLog = false
		(*t.tree)[fpath] = fcontent
	}
}

// Writes entire Tokenizer.tree to supplied dirpath.
//
// TODO: Build logic to prevent dirpath from being the
// same as RootDir()
func (t *Tokenizer) DumpTo(dirpath *pathlib.Path) {
	// check if dirpath exists

	dirExists, err := dirpath.DirExists()
	if err != nil {
		logger.Fatal(err)
	}

	if !dirExists {
		logger.Infof("Creating directory: [%v]", dirpath.String())
		// create it
		if err := dirpath.MkdirAll(); err != nil {
			logger.Fatal(err)
		}
	} else {
		if err := dirpath.RemoveAll(); err != nil {
			logger.Fatal(err)
		}

	}

	for fpath, fcontent := range *t.tree {
		new_path := strings.ReplaceAll(fpath, t.RootDir().String(), dirpath.String())
		newPathObj := pathlib.NewPathAfero(new_path, afero.NewOsFs())

		logger.Infof("[%v]-->[%v]", fpath, new_path)
		fileExists, err := newPathObj.Exists()
		if err != nil {
			logger.Fatal(err)
		}

		if !fileExists {
			newPathObj.Parent().MkdirAll()
			_, err := newPathObj.Create()
			if err != nil {
				logger.Fatal(err)
			}
		}

		// write data to newly created file
		newPathObj.WriteFile([]byte(fcontent))
		logger.Infof("Writing contents to %v", new_path)
	}
}

func (t *Tokenizer) RootDir() *pathlib.Path {
	return t.rootDir
}

package utils

import (
	"io/ioutil"
	"os"
	"reflect"
	"testing"

	"github.com/chigopher/pathlib"
	"github.com/spf13/afero"
)

func TestTokenizer(t *testing.T) {
	dummyTokens := map[string]string{"FOO": "baz", "BAR": "bazzer"}

	// create dummy directory
	tmpRoot, err := ioutil.TempDir("/tmp", "ec-*")
	defer os.RemoveAll(tmpRoot)

	// create dummy dump path
	dumpPath, err := ioutil.TempDir("/tmp", "ec-dump-*")
	if err != nil {
		logger.Fatal(err)
	}

	defer os.RemoveAll(dumpPath)
	if err != nil {
		logger.Fatal(err)
	}
	// create dummy subdirectory
	subdirname, err := ioutil.TempDir(tmpRoot, "sub-*")

	if err != nil {
		logger.Fatal(err)
	}

	// fill with some dummy files
	WriteFile(tmpRoot+"/main.tf", "__FOO__")
	WriteFile(tmpRoot+"/variables.tf", "__BAR__")
	WriteFile(subdirname+"/main.tf", "module data")
	WriteFile(subdirname+"/variables.tf", "module var data")

	t.Run("populate dummy tree and validate", func(t *testing.T) {
		token := &Tokenizer{
			tree:     &map[string]string{},
			rootDir:  pathlib.NewPathAfero(tmpRoot, afero.NewOsFs()),
			destPath: pathlib.NewPathAfero(dumpPath, afero.NewOsFs()),
		}

		token.ReadRoot()

		got := token.GetTree()
		want := &map[string]string{
			tmpRoot + "/main.tf":         "__FOO__",
			tmpRoot + "/variables.tf":    "__BAR__",
			subdirname + "/main.tf":      "module data",
			subdirname + "/variables.tf": "module var data",
		}

		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("replace tokens", func(t *testing.T) {
		token := &Tokenizer{
			tree:     &map[string]string{},
			rootDir:  pathlib.NewPathAfero(tmpRoot, afero.NewOsFs()),
			destPath: pathlib.NewPathAfero(dumpPath, afero.NewOsFs()),
		}
		token.ReadRoot()
		token.ReplaceTokens(&dummyTokens)

		want := []string{"baz", "bazzer", "module data", "module var data"}
		got := []string{}

		tree := token.GetTree()
		for _, content := range *tree {
			got = append(got, content)
		}

		if !(len(got) == len(want)) {
			t.Errorf("got %v, want %v, tokens %v", got, want, dummyTokens)
		}

		t.Run("validate tokens", func(t *testing.T) {
			token := &Tokenizer{
				tree:     &map[string]string{},
				rootDir:  pathlib.NewPathAfero(tmpRoot, afero.NewOsFs()),
				destPath: pathlib.NewPathAfero(dumpPath, afero.NewOsFs()),
			}

			token.ReadRoot()
			token.ReplaceTokens(&dummyTokens)

			validErrors := token.ValidateTokens()
			want := 0
			got := len(*validErrors)

			if want != got {
				t.Errorf("want length %v, got length %v, with tokens %v", want, got, validErrors)
			}
		})

		t.Run("unused token check", func(t *testing.T) {
			token := &Tokenizer{
				tree:     &map[string]string{},
				rootDir:  pathlib.NewPathAfero(tmpRoot, afero.NewOsFs()),
				destPath: pathlib.NewPathAfero(dumpPath, afero.NewOsFs()),
			}

			altTokens := map[string]string{"FOO": "bar"} // missing "BAR key"

			token.ReadRoot()
			token.ReplaceTokens(&altTokens)

			validErrors := token.ValidateTokens() // should have one unused token
			want := 1
			got := len(*validErrors)

			if want != got {
				t.Errorf("want length %v, got length %v, with tokens %v", want, got, altTokens)
			}
		})
	})

}

package utils

import (
	"os"
	"reflect"
	"testing"

	"github.com/chigopher/pathlib"
	"github.com/spf13/afero"
)

func TestReadFileN(t *testing.T) {

	t.Run("Read file with 3 lines", func(t *testing.T) {
		tmpFile := GenTempFile()
		defer os.Remove(tmpFile.Name())

		fcontents := "line1\nline2\nline3"
		tmpFile.Write([]byte(fcontents))

		got := len(ReadFileN(tmpFile.Name()))
		want := 3
		if got != want {
			t.Errorf("got %d want %d given, %v", got, want, fcontents)
		}
	})

	t.Run("Read file with 0 lines", func(t *testing.T) {
		tmpFile := GenTempFile()
		defer os.Remove(tmpFile.Name())

		tmpFile.Write([]byte{})

		got := len(ReadFileN(tmpFile.Name()))
		want := 0
		if got != want {
			t.Errorf("got %d, want %d, given empty string", got, want)
		}
	})
}

func TestWriteFileN(t *testing.T) {
	t.Run("Write to file", func(t *testing.T) {
		fpath := "/tmp/my-231221312.txt"
		fcontents := "This is my new file"

		defer os.Remove(fpath)

		WriteFile(fpath, fcontents)

		pObj := pathlib.NewPathAfero(fpath, afero.NewOsFs())
		if exist, _ := pObj.IsFile(); !exist {
			t.Errorf("file, %s, failed to be created", fpath)
		}
	})
}

func TestRemoveDuplicateStrings(t *testing.T) {
	supplied := []string{"no", "no", "duplicates", "duplicates"}
	want := []string{"no", "duplicates"}

	got := removeDuplicateStr(supplied)

	if !reflect.DeepEqual(got, want) {
		t.Errorf("got %v, want %v, given %v", got, want, supplied)
	}
}

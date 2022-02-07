package internal

import (
	"os"
	"reflect"
	"testing"
)

func TestConfig(t *testing.T) {
	t.Run("config init w/ empty fpath", func(t *testing.T) {
		got := NewConfigFile("")
		want := &ConfigFile{
			fpath:    "",
			keyPairs: map[string]string{},
		}

		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("config init w/ fpath", func(t *testing.T) {
		fname := "myinitfile"

		got := NewConfigFile(fname)
		want := &ConfigFile{
			fpath:    fname,
			keyPairs: map[string]string{},
		}

		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("config get all options", func(t *testing.T) {
		opts := map[string]string{"a": "1", "b": "2", "c": "3"}

		config := &ConfigFile{
			fpath:    "",
			keyPairs: opts,
		}

		got := config.GetAllOpts()
		want := opts

		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("config read from file", func(t *testing.T) {
		f := GenTempFile()
		fcontent := "foo=1\nbar=2\nbaz=3"
		defer os.Remove(f.Name())

		opts := map[string]string{"foo": "1", "bar": "2", "baz": "3"}

		WriteFile(f.Name(), fcontent)

		config := NewConfigFile(f.Name())
		config.ReadAndParse()

		got := config.GetAllOpts()
		want := opts

		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v, given %s", got, want, f.Name())
		}
	})

	t.Run("config read from environment variables", func(t *testing.T) {

		config := NewConfigFile("")
		config.ReadAndParse()

		got := len(config.GetAllOpts())
		want := len(os.Environ())

		if got != want {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("config get ARM variables", func(t *testing.T) {

		config := &ConfigFile{
			fpath:    "",
			keyPairs: map[string]string{"ARM_X": "1", "ARM_Y": "2", "OTHER": "3"},
		}
		opts := config.GetArms()
		want := 2
		got := len(opts)

		if got != want {
			t.Errorf("got %v, want %v, given %v with opts %v", got, want, config, opts)
		}

	})

	t.Run("set arm variables", func(t *testing.T) {
		vars := map[string]string{"ARM_X": "1"}
		config := &ConfigFile{
			fpath:    "",
			keyPairs: vars,
		}
		config.SetArmEnvs()

		exist := false
		for _, elem := range os.Environ() {
			if elem == "ARM_X=1" {
				exist = true
			}
		}

		if !exist {
			t.Errorf("Setting ARM variables failed")
		}
	})

	t.Run("get element from config", func(t *testing.T) {
		config := &ConfigFile{
			fpath:    "",
			keyPairs: map[string]string{"a": "1"},
		}

		want := "1"
		got := config.Get("a")

		if want != got {
			t.Errorf("got %v, want %v", got, want)
		}
	})
}

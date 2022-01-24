package utils

import (
	"fmt"
	"reflect"
	"testing"

	"github.com/hashicorp/terraform-exec/tfexec"
)

func TestTerraform(t *testing.T) {
	t.Run("generate backend option no quotes", func(t *testing.T) {
		key := "mykey"
		value := "myvalue"

		wantStr := fmt.Sprintf("%s=%s", key, value)
		want := tfexec.BackendConfig(wantStr)

		got := makeBackendOpt(key, value)

		if !reflect.DeepEqual(got, want) {
			t.Errorf("want %v, got %v", got, want)
		}
	})

	t.Run("generate backend option with quotes", func(t *testing.T) {
		key := "mykey"
		value := "\"myvalue\"" // enclose value with quotes

		want := tfexec.BackendConfig("mykey=myvalue")
		got := makeBackendOpt(key, value)

		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})
}

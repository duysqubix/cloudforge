package utils

import (
	"os"

	"github.com/chigopher/pathlib"
	"github.com/op/go-logging"
	"github.com/spf13/afero"
)

var logger = logging.MustGetLogger("utils")

const TMPDIR_PATH string = "/tmp/.terraform-go"

func GetExecutablePath() *pathlib.Path {
	exec, err := os.Executable()

	if err != nil {
		logger.Fatal("Can not find")
	}
	rootDir := pathlib.NewPathAfero(exec, afero.NewOsFs()).Parent()
	return rootDir
}

func init() {
	var format = logging.MustStringFormatter(
		`%{color}%{time:15:04:05.000} %{shortfunc} ▶ %{level:.4s} %{id:03x}%{color:reset} %{message}`,
	)
	backend1 := logging.NewLogBackend(os.Stderr, "", 0)

	backend1Formatter := logging.NewBackendFormatter(backend1, format)

	// Only errors and more severe messages should be sent to backend1
	backend1Leveled := logging.AddModuleLevel(backend1)
	backend1Leveled.SetLevel(logging.ERROR, "")

	// Set the backends to be used.
	logging.SetBackend(backend1Leveled, backend1Formatter)

}

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

type AzureServicePrincipal struct {
	clientId     string
	clientSecret string
	tenantId     string
}

func NewServicePrincipal(clientId, clientSecret, tenantId *string) *AzureServicePrincipal {
	return &AzureServicePrincipal{
		clientId:     *clientId,
		clientSecret: *clientSecret,
		tenantId:     *tenantId,
	}
}

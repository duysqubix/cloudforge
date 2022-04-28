// Utils package holds structures and logic related to managing terraform
// connecting to Azure services, and parsing raw terraform files
package internal

import (
	"os"

	"github.com/chigopher/pathlib"
	"github.com/op/go-logging"
	"github.com/spf13/afero"
)

var logger = logging.MustGetLogger("utils")

// Directory where formatted terraform files will be dumped to
const TMPDIR_ROOT string = "/tmp"
const TMPDIR_PATH string = TMPDIR_ROOT + "/.terraform-go"

// Returns executable path and returns a pathlib object
func GetExecutablePath() *pathlib.Path {
	exec, err := os.Executable()

	if err != nil {
		logger.Fatal("Can not find")
	}
	rootDir := pathlib.NewPathAfero(exec, afero.NewOsFs()).Parent()
	return rootDir
}

// Get current working directory
func GetCwd() *pathlib.Path {
	cwd, err := os.Getwd()
	if err != nil {
		logger.Fatal(err)
	}

	cwdObj := pathlib.NewPathAfero(cwd, afero.NewOsFs())
	return cwdObj
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

// Represents the service principal used to authenticate against Azure
type AzureServicePrincipal struct {
	clientId     string
	clientSecret string
	tenantId     string
}

// Generates a new service principal object
func NewServicePrincipal(clientId, clientSecret, tenantId *string) *AzureServicePrincipal {
	return &AzureServicePrincipal{
		clientId:     *clientId,
		clientSecret: *clientSecret,
		tenantId:     *tenantId,
	}
}

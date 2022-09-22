package version

import (
	"fmt"

	version "github.com/hashicorp/go-version"
)

// Main version number that is being run at the moment
var Version string

// A pre-release marker for this version. If this is empty ("")
// then it means that it is a final release. Otherwise, this is a pre-release
// such as 'dev', 'beta', 'rc1', etc..
var PreRelease string

var SemVer *version.Version

func init() {
	SemVer = version.Must(version.NewVersion(Version))
}

func String() string {
	if PreRelease != "" {
		return fmt.Sprintf("%s-%s", Version, PreRelease)
	}
	return Version
}

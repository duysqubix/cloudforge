/*
Copyright © 2022 Duan Uys <dhuys@vorys.com>

eControl Infrastructure Manager

A set of useful tools that manages eControl Digital environment.

** Executable must be located in root of project.

Installation w/ Make:
	make all

Usage:
	Global Flags: --no-plan // do not generate a plan
	ec validate [dev, int, uat, prod] // validates tf files and generates plan
	ec deploy    [dev, int, uat, prod] // deploys tf files to appropriate env



*/
package main

import (
	"github.com/op/go-logging"

	"github.com/vorys-econtrol/ec/cmd"
)

var logger = logging.MustGetLogger("main")

var VERSION string = ""

func main() {

	// VERSION is set during the build stage
	if VERSION == "" {
		logger.Warning("VERSION IS NOT SET")
	}
	cmd.VERSION = VERSION
	cmd.Execute()
}

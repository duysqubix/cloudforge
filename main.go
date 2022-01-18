/*
Copyright © 2022 Duan Uys <dhuys@vorys.com>

eControl Infrastructure Manager

Software that allows to validate and deploy to eControl Digitals' multiple environments.


** Executable must be located in root of project.


Installation w/ Make:
	make all

Usage:
	ec [validate/deploy] [dev, int, uat, prod]



*/
package main

import (
	"github.com/vorys-econtrol/ec/cmd"
)

var VERSION string = "0.2.0"

func main() {
	cmd.VERSION = VERSION
	cmd.Execute()
}

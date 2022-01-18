/*
Copyright © 2022 Duan Uys <dhuys@vorys.com>

eControl Infrastructure Manager

Software that allows to validate and deploy to eControl Digitals' multiple environments.


** Executable must be located in root of project.


Installation w/ Make:
	make all

Usage:
	./einfra [validate/deploy] [dev, int, uat, prod]



*/
package main

import (
	"github.com/terraform/ec/cmd"
)

const VERSION string = "0.1.10"

func main() {
	cmd.VERSION = VERSION
	cmd.Execute()

}

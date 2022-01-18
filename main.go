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
	"log"

	"github.com/vorys-econtrol/ec/cmd"
)

var VERSION string

func main() {
	if VERSION == "" {
		log.Fatal("VERSION IS NOT SET")
	}
	cmd.VERSION = VERSION
	cmd.Execute()
}

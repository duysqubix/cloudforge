/*
Copyright © 2022 Duan Uys <dhuys@vorys.com>

eControl Infrastructure Manager

A set of useful tools that manages eControl Digital environment.


*/
package main

import (
	"github.com/op/go-logging"

	"github.com/vorys-econtrol/ec/cmd"
)

var logger = logging.MustGetLogger("main")

func main() {

	cmd.Execute()
}

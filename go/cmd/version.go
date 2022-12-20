/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"github.com/spf13/cobra"
	"github.com/vorys-econtrol/ec/version"
)

// versionCmd represents the version command
var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "",
	Long:  ``,
	Run:   ShowVersion,
}

func init() {
	rootCmd.AddCommand(versionCmd)
}

func ShowVersion(cmd *cobra.Command, args []string) {

	cmd.Println(version.String())

}

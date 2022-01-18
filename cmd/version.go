/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
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

	fmt.Println("Version: ", VERSION)

}

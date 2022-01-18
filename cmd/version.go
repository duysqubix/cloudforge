/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/terraform/ec/utils"
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
	execPath := utils.GetExecutablePath()
	versionPath := execPath.Join("VERSION")

	isFile, _ := versionPath.IsFile()
	if !isFile {
		logger.Fatal("Version file for Einfra not found")
	}
	contents, _ := versionPath.ReadFile()

	fmt.Println("Version: ", string(contents))

}

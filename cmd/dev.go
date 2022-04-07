/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"github.com/spf13/cobra"
)

// devCmd represents the dev command
var devCmd = &cobra.Command{
	Use:   "dev",
	Short: "Validates dev environment",
	Long:  ``,
	Run:   ValidateDev,
}

var devDeployCmd = &cobra.Command{
	Use:   "dev",
	Short: "Deploys dev environment",
	Long:  ``,
	Run:   DeployDev,
}

func init() {
	validateCmd.AddCommand(devCmd)
	deployCmd.AddCommand(devDeployCmd)
}

func ValidateDev(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("dev")
	validateTerraform(tf, cmd)

}

func DeployDev(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("dev")
	validateTerraform(tf, cmd)
	deployTerraform(tf)

}

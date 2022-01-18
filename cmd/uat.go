/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"github.com/spf13/cobra"
)

// uatCmd represents the uat command
var uatCmd = &cobra.Command{
	Use:   "uat",
	Short: "Validates User Acceptance Envrionment",
	Long:  ``,
	Run:   ValidateUat,
}

var uatDeployCmd = &cobra.Command{
	Use:   "uat",
	Short: "Deploys in User Acceptance Environment",
	Long:  ``,
	Run:   DeployUat,
}

func init() {
	validateCmd.AddCommand(uatCmd)
	deployCmd.AddCommand(uatDeployCmd)

}

func ValidateUat(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("uat")
	validateTerraform(tf, cmd)

}

func DeployUat(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("uat")
	validateTerraform(tf, cmd)
	deployTerraform(tf)

}

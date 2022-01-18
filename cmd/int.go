/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"github.com/spf13/cobra"
)

// devCmd represents the dev command
var intCmd = &cobra.Command{
	Use:   "int",
	Short: "Validates integration environment",
	Long:  ``,
	Run:   ValidateInt,
}

var intDeployCmd = &cobra.Command{
	Use:   "int",
	Short: "Deploys integration environment",
	Long:  ``,
	Run:   DeployInt,
}

func init() {
	validateCmd.AddCommand(intCmd)
	deployCmd.AddCommand(intDeployCmd)
}

func ValidateInt(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("int")
	validateTerraform(tf, cmd)

}

func DeployInt(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("int")
	validateTerraform(tf, cmd)
	deployTerraform(tf)

}

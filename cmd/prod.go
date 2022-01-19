/*

 */

package cmd

import "github.com/spf13/cobra"

var prodCmd = &cobra.Command{
	Use:   "prod",
	Short: "Validates Production environment",
	Long:  ``,
	Run:   ValidateProd,
}

var prodDeployCmd = &cobra.Command{
	Use:   "prod",
	Short: "Deploys in Production Environment",
	Long:  ``,
	Run:   DeployProd,
}

func init() {
	validateCmd.AddCommand(prodCmd)
	deployCmd.AddCommand(prodDeployCmd)
}

func ValidateProd(cmd *cobra.Command, args []string)  {
	tf := baseTerraformSetup("prod")
	validateTerraform(tf, cmd)
}

func DeployProd(cmd *cobra.Command, args []string)  {
	tf := baseTerraformSetup("prod")
	validateTerraform(tf, cmd)
	deployTerraform(tf)
}

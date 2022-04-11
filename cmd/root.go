package cmd

import (
	"os"

	"github.com/op/go-logging"
	"github.com/spf13/cobra"
	"github.com/vorys-econtrol/ec/version"
)

var logger = logging.MustGetLogger("cmd")

// VERSION variable is set within Main function
var VERSION string

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "ec",
	Short: "Easily validates and deploys terraform files to appropriate environment",
	Long: `Used to validate and potentially deploy terraform files into Azure and the respective 
	environment.
	
	Usage:
		ec validate [dev, int, uat, prod]
		ec deploy [dev, int, uat, prod]
	`,
}

var cfgFile string

func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {

	rootCmd.AddCommand(terraformCmd)
	rootCmd.AddCommand(datafactoryCmd)
	rootCmd.AddCommand(synapseCmd)

	rootCmd.Printf("Running EC Version: %s\n", version.String())
}

func appendNoPlanFlag(cmd *cobra.Command) {
	cmd.Flags().Bool("no-plan", false, "Skips plang action during validation")
}

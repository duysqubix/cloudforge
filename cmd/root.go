/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"os"

	"github.com/chigopher/pathlib"
	"github.com/op/go-logging"
	"github.com/spf13/afero"
	"github.com/spf13/cobra"
	"github.com/vorys-econtrol/ec/utils"
)

var logger = logging.MustGetLogger("cmd")
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
	// Uncomment the following line if your bare application
	// has an action associated with it:
	// Run: func(cmd *cobra.Command, args []string) { },
}

var cfgFile string

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	err := rootCmd.Execute()
	if err != nil {
		os.Exit(1)
	}
}

func init() {
	// Here you will define your flags and configuration settings.
	// Cobra supports persistent flags, which, if defined here,
	// will be global for your application.
	// rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.terraform_script.yaml)")

	// Cobra also supports local flags, which will only run
	// when this action is called directly.
	// rootCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
	rootCmd.PersistentFlags().BoolP("no-plan", "n", false, "Performs a plan action during validation")
}

func baseTerraformSetup(env string) *utils.AzureTerraform {

	switch env {
	case "dev":
		cfgFile = ".env.dev"
	case "int":
		cfgFile = ".env.int"
	case "uat":
		cfgFile = ".env.uat"
	case "prod":
		cfgFile = ".env.prod"
	default:
		logger.Fatal("Incorrect environment supplied")
	}

	_, useArmEnv := os.LookupEnv("ARM_VARS_USE_EXISTING")
	var config *utils.ConfigFile
	if !useArmEnv {
		if cfgFile == "" {
			logger.Fatal("cfgFile not set")
		}
		config = utils.NewConfigFile(cfgFile)

	} else {
		config = utils.NewConfigFile("") // we are using existing environment variables already set
	}

	config.ReadAndParse() // read either from file or os.Env
	tokenizer := utils.TokenizerNew(config.GetAllOpts())
	tokenizer.ReadRoot()

	clientId := config.Get("ARM_CLIENT_ID")
	clientSecret := config.Get("ARM_CLIENT_SECRET")
	tenantId := config.Get("ARM_TENANT_ID")
	vaultName := config.Get("KEY_VAULT_NAME")

	sp := utils.NewServicePrincipal(&clientId, &clientSecret, &tenantId)
	tokens := utils.GetKeyVaultSecrets(&vaultName, sp)

	tokenizer.ReplaceAndValidateTokens(tokens)
	tmp_dir := pathlib.NewPathAfero(utils.TMPDIR_PATH, afero.NewOsFs())

	tokenizer.DumpTo(tmp_dir)
	tf := utils.NewTerraformHandler(config)
	return tf
}

func validateTerraform(tf *utils.AzureTerraform, cmd *cobra.Command) {
	resp, errors := tf.Validate()
	if !resp {
		logger.Fatalf("Terraform did not validate properly:\n%v", errors)
	}

	if cmd.Flag("no-plan").Value.String() == "false" {
		logger.Warning("Performing plan action")
		if err := tf.Plan(); err != nil {
			logger.Fatal(err)
		}
	} else {
		logger.Warning("Skipping plan action")
	}
}

func deployTerraform(tf *utils.AzureTerraform) {
	if err := tf.Deploy(); err != nil {
		logger.Fatal(err)
	}
}

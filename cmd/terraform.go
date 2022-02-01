package cmd

import (
	"fmt"
	"os"

	"github.com/chigopher/pathlib"
	"github.com/spf13/afero"
	"github.com/spf13/cobra"
	"github.com/vorys-econtrol/ec/utils"
)

const (
	defaultDevEnvFile  = ".env.dev"
	defaultIntEnvFile  = ".env.int"
	defaultUatEnvFile  = ".env.uat"
	defaultProdEnvFile = ".env.prod"
)

var (
	projDir string
)

func init() {
	cwd, err := os.Getwd()
	if err != nil {
		logger.Fatalf("Unable to get current working directory, reason %v", err)
	}

	terraformCmd.AddCommand(validateCmd)
	terraformCmd.AddCommand(deployCmd)

	// add globally persistent flags to terraform cmd
	terraformCmd.PersistentFlags().StringVarP(&projDir, "proj-dir", "p", cwd, "Path to project directory that contains terraform files ")

	validateCmd.AddCommand(prodCmd)
	validateCmd.AddCommand(uatCmd)
	validateCmd.AddCommand(intCmd)
	validateCmd.AddCommand(devCmd)

	deployCmd.AddCommand(prodDeployCmd)
	deployCmd.AddCommand(uatDeployCmd)
	deployCmd.AddCommand(devDeployCmd)
	deployCmd.AddCommand(intDeployCmd)

	appendNoPlanFlag(devCmd)
	appendNoPlanFlag(intCmd)
	appendNoPlanFlag(uatCmd)
	appendNoPlanFlag(prodCmd)
}

//################ COMMANDS ##########################

var terraformCmd = &cobra.Command{
	Use:   "terraform",
	Short: "Manages eControl 360 infrastructure",
	Long:  `Used to validate and deploy eControl 360 infrastructure using Terraform.`,
	Example: `
	ec terraform [validate/deploy] [dev/int/uat/prod]
	`,
}

var validateCmd = &cobra.Command{
	Use:   "validate",
	Short: "Validate different environments",
}

var deployCmd = &cobra.Command{
	Use:   "deploy",
	Short: "Deploy to different environments",
}

var devCmd = &cobra.Command{
	Use:   "dev",
	Short: "Validates dev environment",
	Run:   validateDev,
}

var devDeployCmd = &cobra.Command{
	Use:   "dev",
	Short: "Deploys dev environment",
	Run:   deployDev,
}

func validateDev(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("dev")
	validateTerraform(tf, cmd)

}

func deployDev(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("dev")
	validateTerraform(tf, cmd)
	deployTerraform(tf)

}

var intCmd = &cobra.Command{
	Use:   "int",
	Short: "Validates integration environment",
	Run:   validateInt,
}

var intDeployCmd = &cobra.Command{
	Use:   "int",
	Short: "Deploys integration environment",
	Run:   deployInt,
}

func validateInt(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("int")
	validateTerraform(tf, cmd)

}

func deployInt(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("int")
	validateTerraform(tf, cmd)
	deployTerraform(tf)

}

var uatCmd = &cobra.Command{
	Use:   "uat",
	Short: "Validates User Acceptance Envrionment",
	Run:   validateUat,
}

var uatDeployCmd = &cobra.Command{
	Use:   "uat",
	Short: "Deploys in User Acceptance Environment",
	Run:   deployUat,
}

func validateUat(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("uat")
	validateTerraform(tf, cmd)

}

func deployUat(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("uat")
	validateTerraform(tf, cmd)
	deployTerraform(tf)

}

var prodCmd = &cobra.Command{
	Use:   "prod",
	Short: "Validates Production environment",
	Run:   validateProd,
}

var prodDeployCmd = &cobra.Command{
	Use:   "prod",
	Short: "Deploys in Production Environment",
	Run:   deployProd,
}

func validateProd(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("prod")
	validateTerraform(tf, cmd)
}

func deployProd(cmd *cobra.Command, args []string) {
	tf := baseTerraformSetup("prod")
	validateTerraform(tf, cmd)
	deployTerraform(tf)
}

//############################################################

func baseTerraformSetup(env string) *utils.AzureTerraform {
	fmt.Println(projDir)
	switch env {
	case "dev":
		cfgFile = projDir + "/.env.dev"
	case "int":
		cfgFile = projDir + "/.env.int"
	case "uat":
		cfgFile = projDir + "/.env.uat"
	case "prod":
		cfgFile = projDir + "/.env.prod"
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
	tokenizer := utils.TokenizerNew()
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
	tf := utils.NewAzureTerraformHandler(config)
	return tf
}

// Performs validation of terraform with either a plan or no-plan
// depending on supplied flag
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

// Performs an Apply action with -auto-apply
func deployTerraform(tf *utils.AzureTerraform) {
	if err := tf.Deploy(); err != nil {
		logger.Fatal(err)
	}
}

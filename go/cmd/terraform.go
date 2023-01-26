package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/chigopher/pathlib"
	"github.com/spf13/afero"
	"github.com/spf13/cobra"
	"github.com/vorys-econtrol/ec/internal"
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

// cleans up the temporary directory that terraform creates
func cleanUpTmpDir() {
	if tfTmpDir != nil {
		internal.CleanUpDir(tfTmpDir)
	} else {
		logger.Warningf("tfTmpDir pointer is set to nil")
	}
}

func init() {
	cwd, err := os.Getwd()
	if err != nil {
		logger.Fatalf("Unable to get current working directory, reason %v", err)
	}

	terraformCmd.AddCommand(validateCmd)
	terraformCmd.AddCommand(deployCmd)
	terraformCmd.AddCommand(debugCmd)
	// add globally persistent flags to terraform cmd
	terraformCmd.PersistentFlags().StringVarP(&projDir, "proj-dir", "p", cwd, "Path to project directory that contains terraform files ")

	debugCmd.AddCommand(devDebug)
	debugCmd.AddCommand(intDebug)
	debugCmd.AddCommand(uatDebug)
	debugCmd.AddCommand(prodDebug)

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

var debugCmd = &cobra.Command{
	Use:   "debug",
	Short: "Create a debugging environment",
	Long:  "Creates a temporary directory with a script that can be used to initialize terraform",
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

var devDebug = &cobra.Command{
	Use:   "dev",
	Short: "Debugs dev environment",
	Run:   func(cmd *cobra.Command, args []string) { createDebugEnvironment("dev") },
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

var intDebug = &cobra.Command{
	Use:   "int",
	Short: "Debugs int environment",
	Run:   func(cmd *cobra.Command, args []string) { createDebugEnvironment("int") },
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

var uatDebug = &cobra.Command{
	Use:   "uat",
	Short: "Debugs uat environment",
	Run:   func(cmd *cobra.Command, args []string) { createDebugEnvironment("uat") },
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

var prodDebug = &cobra.Command{
	Use:   "prod",
	Short: "Debugs prod environment",
	Run:   func(cmd *cobra.Command, args []string) { createDebugEnvironment("prod") },
}

//############################################################

func createDebugEnvironment(env string) {
	var tfWrapper strings.Builder
	var script strings.Builder

	initFname := "init.sh"
	wrapperFname := "terraform.sh"

	config := initTerraformSetup(env)

	clientId := "ARM_CLIENT_ID"
	clientSecret := "ARM_CLIENT_SECRET"
	tenantId := "ARM_TENANT_ID"
	subId := "ARM_SUBSCRIPTION_ID"

	prefix := fmt.Sprintf("%s=%s %s=%s %s=%s %s=%s terraform ", clientId, config.Get(clientId), clientSecret, config.Get(clientSecret), tenantId, config.Get(tenantId), subId, config.Get(subId))

	backendConfigs := map[string]string{
		"storage_account_name": config.Get("STORAGE_ACCOUNT_NAME"),
		"sas_token":            config.Get("SAS_TOKEN"),
		"key":                  config.Get("TF_KEY"),
		"container_name":       config.Get("CONTAINER_NAME"),
	}

	script.WriteString(prefix + "init ")
	for key, ele := range backendConfigs {
		script.WriteString(fmt.Sprintf("-backend-config=%s=%s ", key, ele))
	}

	fmt.Println("debug environment: ", tfTmpDir.String())
	initFilePath := tfTmpDir.Join(initFname)
	internal.WriteFile(initFilePath.String(), script.String())
	os.Chmod(initFilePath.String(), 0700)

	tfWrapper.WriteString("#!/usr/bin/env bash\n\n")

	tfWrapper.WriteString(fmt.Sprintf("%s $@", prefix))

	wrapperFilePath := tfTmpDir.Join(wrapperFname)
	internal.WriteFile(wrapperFilePath.String(), tfWrapper.String())
	os.Chmod(wrapperFilePath.String(), 0700)
}

func GetConfigSettingsForEnv(env string) *internal.ConfigFile {
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
	var config *internal.ConfigFile
	if !useArmEnv {
		if cfgFile == "" {
			logger.Fatal("cfgFile not set")
		}
		config = internal.NewConfigFile(cfgFile)

	} else {
		config = internal.NewConfigFile("") // we are using existing environment variables already set
	}

	config.ReadAndParse() // read either from file or os.Env

	return config
}

func baseTerraformSetup(env string) *internal.AzureTerraform {
	config := initTerraformSetup(env)
	tf := internal.NewAzureTerraformHandler(config, tfTmpDir)

	return tf
}

func initTerraformSetup(env string) *internal.ConfigFile {
	tokenizer := internal.TokenizerNew(pathlib.NewPathAfero(projDir, afero.NewOsFs()), ".tf")
	tokenizer.ReadRoot()

	config := GetConfigSettingsForEnv(env)
	clientId := config.Get("ARM_CLIENT_ID")
	clientSecret := config.Get("ARM_CLIENT_SECRET")
	tenantId := config.Get("ARM_TENANT_ID")
	vaultName := config.Get("KEY_VAULT_NAME")

	sp := internal.NewServicePrincipal(&clientId, &clientSecret, &tenantId)
	tokens := internal.GetKeyVaultSecrets(&vaultName, sp)

	tokenizer.ReplaceAndValidateTokens(tokens)
	tmp_dir := pathlib.NewPathAfero(internal.TMPDIR_PATH, afero.NewOsFs())

	tmp_dir = tokenizer.DumpTo(tmp_dir, true)
	tfTmpDir = tmp_dir

	return config
}

// Performs validation of terraform with either a plan or no-plan
// depending on supplied flag
func validateTerraform(tf *internal.AzureTerraform, cmd *cobra.Command) {
	resp, errors := tf.Validate()
	if !resp {
		logger.Fatalf("Terraform did not validate properly:\n%v", errors)
	}

	ptrFlag := cmd.Flag("no-plan")

	if ptrFlag != nil {

		if cmd.Flag("no-plan").Value.String() == "false" {
			logger.Warning("Performing plan action")
			if err := tf.Plan(); err != nil {
				cleanUpTmpDir()
				logger.Fatal(err)
			}
		}
	} else {
		logger.Warning("Skipping plan action")
	}

}

// Performs an Apply action with -auto-apply
func deployTerraform(tf *internal.AzureTerraform) {
	if err := tf.Deploy(); err != nil {
		cleanUpTmpDir()
		logger.Fatal(err)
	}
	cleanUpTmpDir()
}
/*
	Synapse management tool

*/

package cmd

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/chigopher/pathlib"
	"github.com/spf13/afero"
	"github.com/spf13/cobra"
	"github.com/vorys-econtrol/ec/internal"
)

var (
	workspacePath string
	workspaceName string
	configPath    string
	destPath      string
	debug         bool
	dryRun        bool
	env           string
	fileName      string
	fileType      string
	formatType    string
	targetDir     string
	// sqlDbName     string
	// sqlUsername   string
	// sqlPassword   string
)

var synapseCmd = &cobra.Command{
	Use:   "syn",
	Short: "Manages Synapse",
}

func init() {
	synapseCmd.AddCommand(synPrettyifyCmd)
	synapseCmd.AddCommand(synCreateArmCmd)
	synapseCmd.AddCommand(synSqlCmd)

	synSqlCmd.AddCommand(synSqlDeployCmd)

	synSqlDeployCmd.AddCommand(devSynSqlDeployCmd)

	synCreateArmCmd.Flags().StringVarP(&workspacePath, "workspace-dir", "d", "", "Path to workspace JSON files")
	synCreateArmCmd.Flags().StringVarP(&workspaceName, "workspace-name", "n", "", "Name of the workspace")
	synCreateArmCmd.Flags().StringVarP(&destPath, "output", "o", "", "Path to write ARM template")
	synCreateArmCmd.Flags().StringVarP(&configPath, "config", "c", "", "Path to configuration deployment file")
	synCreateArmCmd.Flags().BoolVar(&debug, "debug", false, "Output debug information")
	synCreateArmCmd.Flags().BoolVar(&dryRun, "dry-run", false, "Performs a dry run")
	synCreateArmCmd.Flags().StringVarP(&env, "env", "e", "", "Targeted Environment")

	synCreateArmCmd.MarkFlagRequired("workspace-dir")
	synCreateArmCmd.MarkFlagRequired("workspace-name")
	synCreateArmCmd.MarkFlagRequired("config")
	synCreateArmCmd.MarkFlagRequired("output")
	/*******************************************/

	synPrettyifyCmd.Flags().StringVarP(&fileName, "name", "n", "", "Name of file")
	synPrettyifyCmd.Flags().StringVarP(&fileType, "type", "t", "", "Type of file")
	synPrettyifyCmd.Flags().StringVarP(&formatType, "format", "f", "", "formatter to be used")

	synPrettyifyCmd.MarkFlagRequired("name")
	synPrettyifyCmd.MarkFlagRequired("type")

	/*******************************************/
	devSynSqlDeployCmd.Flags().StringVarP(&targetDir, "target-dir", "t", "", "Location of Synapse Stored SQL Scripts")

	devSynSqlDeployCmd.MarkFlagRequired("target-dir")
}

var synCreateArmCmd = &cobra.Command{
	Use:   "arm",
	Short: "Managed synapse workspace",
	Run:   invokeSynModuleArm,
}
var synPrettyifyCmd = &cobra.Command{
	Use:   "prettify",
	Short: "Prettifies notebooks and sqlscripts",
	Run:   invokeSynModulePrettify,
}

var synSqlCmd = &cobra.Command{
	Use:   "sql",
	Short: "Manage Synapse SQL",
}

var synSqlDeployCmd = &cobra.Command{
	Use:   "deploy",
	Short: "Deploy SQL to Env",
}

var devSynSqlDeployCmd = &cobra.Command{
	Use:   "dev",
	Short: "Deploy SQL to Env",
	Run:   deploySynSQLDev,
}

func getExecutablePath() string {
	ex, err := os.Executable()

	if err != nil {
		panic(err)
	}

	exPath := filepath.Dir(ex)
	return exPath
}

func getExecutablename() string {
	ex, err := os.Executable()

	if err != nil {
		panic(err)
	}

	exPath := pathlib.NewPathAfero(ex, afero.NewOsFs())
	return exPath.Name()
}

func deploySynSQLDev(cmd *cobra.Command, args []string) {
	deploySynSql("dev", cmd.Flag("target-dir").Value.String())
}

func deploySynSql(env string, target_dir string) {
	config := GetConfigSettingsForEnv(env)
	clientId := config.Get("ARM_CLIENT_ID")
	clientSecret := config.Get("ARM_CLIENT_SECRET")
	tenantId := config.Get("ARM_TENANT_ID")
	vaultName := config.Get("KEY_VAULT_NAME")

	sp := internal.NewServicePrincipal(&clientId, &clientSecret, &tenantId)
	tokens := internal.GetKeyVaultSecrets(&vaultName, sp)

	workspaceName := (*tokens)["SynapseWorkspaceName"]
	databaseName := (*tokens)["SynapseWorkspaceSQLName"]
	username := (*tokens)["SynapseWorkspaceSQLAdminUsername"]
	password := (*tokens)["SynapseWorkspaceSQLAdminPassword"]

	// create SQL files first
	bin := fmt.Sprintf("%s/%s_synapse_prettify", getExecutablePath(), getExecutablename())

	destPath := internal.MakeDirUnique(pathlib.NewPathAfero("/tmp/_synapse_sqlscripts", afero.NewOsFs()))

	sub_args := []string{
		"generate-sql-scripts",
		"--wks-folder-name=migrations", // explicilty looks for SQL files stored in a migrations folder
		"--target-dir=" + target_dir,
		"--dest=" + destPath.String(),
	}

	mod := exec.Command(bin, sub_args...)

	stdout, err := mod.CombinedOutput()

	if err != nil {
		fmt.Println(err.Error(), string(stdout))
		return
	}
	fmt.Println("Saving SQL Scripts to" + destPath.String())

	fmt.Println(string(stdout))

	// now read these current files and deploy
	bin = fmt.Sprintf("%s/%s_synapse_sql", getExecutablePath(), getExecutablename())

	sub_args = []string{
		"deploy",
		"--workspace_name=" + workspaceName,
		"--database=" + databaseName,
		"--username=" + username,
		"--password=" + password,
		"--target-dir=" + destPath.String(),
	}

	mod = exec.Command(bin, sub_args...)

	stdout, err = mod.CombinedOutput()

	if err != nil {
		fmt.Println(err.Error(), string(stdout))
		return
	}

	fmt.Println(string(stdout))

}

func invokeSynModulePrettify(cmd *cobra.Command, args []string) {
	bin := fmt.Sprintf("%s/%s_synapse_prettify", getExecutablePath(), getExecutablename())

	sub_args := []string{
		"--name=" + cmd.Flag("name").Value.String(),
		"--type=" + cmd.Flag("type").Value.String(),
		"--format=" + cmd.Flag("format").Value.String(),
	}

	mod := exec.Command(bin, sub_args...)

	stdout, err := mod.CombinedOutput()

	if err != nil {
		fmt.Println(err.Error(), string(stdout))
		return
	}

	fmt.Println(string(stdout))
}

func invokeSynModuleArm(cmd *cobra.Command, args []string) {

	bin := fmt.Sprintf("%s/%s_synapse_arm", getExecutablePath(), getExecutablename())

	sub_args := []string{
		"--dir=" + cmd.Flag("workspace-dir").Value.String(),
		"--config=" + cmd.Flag("config").Value.String(),
		"--workspace-name=" + cmd.Flag("workspace-name").Value.String(),
		"--output=" + cmd.Flag("output").Value.String(),
	}

	if debug == true {
		sub_args = append(sub_args, "--debug")
	}

	if dryRun == true {
		sub_args = append(sub_args, "--dry-run")
	}
	mod := exec.Command(bin, sub_args...)
	stdout, err := mod.CombinedOutput()

	if err != nil {
		fmt.Println(err.Error(), string(stdout))
		return

	}

	config := GetConfigSettingsForEnv(cmd.Flag("env").Value.String())
	tokenizer := internal.TokenizerNew(pathlib.NewPathAfero(workspacePath, afero.NewOsFs()), ".json")

	outputArmTempate := pathlib.NewPathAfero(cmd.Flag("output").Value.String(), afero.NewOsFs())
	tokenizer.ReadFile(outputArmTempate)

	clientId := config.Get("ARM_CLIENT_ID")
	clientSecret := config.Get("ARM_CLIENT_SECRET")
	tenantId := config.Get("ARM_TENANT_ID")
	vaultName := config.Get("KEY_VAULT_NAME")

	sp := internal.NewServicePrincipal(&clientId, &clientSecret, &tenantId)
	tokens := internal.GetKeyVaultSecrets(&vaultName, sp)

	tokenizer.ReplaceAndValidateTokens(tokens)

	tmp_dir := pathlib.NewPathAfero(internal.TMPDIR_ROOT+"/synapseArm", afero.NewOsFs())
	tokenizer.DumpTo(tmp_dir, false)

	fmt.Print(string(stdout))

}

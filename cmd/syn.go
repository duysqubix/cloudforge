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
)

func init() {

	synapseCmd.Flags().StringVarP(&workspacePath, "workspace-dir", "d", "", "Path to workspace JSON files")
	synapseCmd.Flags().StringVarP(&workspaceName, "workspace-name", "n", "", "Name of the workspace")
	synapseCmd.Flags().StringVarP(&destPath, "output", "o", "", "Path to write ARM template")
	synapseCmd.Flags().StringVarP(&configPath, "config", "c", "", "Path to configuration deployment file")
	synapseCmd.Flags().BoolVar(&debug, "debug", false, "Output debug information")
	synapseCmd.Flags().BoolVar(&dryRun, "dry-run", false, "Performs a dry run")
	synapseCmd.Flags().StringVarP(&env, "env", "e", "", "Targeted Environment")

	synapseCmd.MarkFlagRequired("workspace-dir")
	synapseCmd.MarkFlagRequired("workspace-name")
	synapseCmd.MarkFlagRequired("config")
	synapseCmd.MarkFlagRequired("output")
	synapseCmd.MarkFlagRequired("env")
}

var synapseCmd = &cobra.Command{
	Use:   "syn",
	Short: "Manages Synapse Workspace",
	Long:  `Used to validate and deploy a synapse workspace`,
	Run:   invokeSynModule,
}

func invokeSynModule(cmd *cobra.Command, args []string) {
	ex, err := os.Executable()

	if err != nil {
		panic(err)
	}

	exPath := filepath.Dir(ex)
	bin := exPath + "/synapse"
	fmt.Println(bin)

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
	stdout, err := mod.Output()

	if err != nil {
		fmt.Println(err.Error())
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

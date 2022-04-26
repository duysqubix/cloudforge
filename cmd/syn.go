/*
	Synapse management tool

*/

package cmd

import (
	"fmt"
	"os/exec"

	"github.com/spf13/cobra"
)

var (
	workspacePath string
	configPath    string
	debug         bool
	dryRun        bool
)

func init() {

	synapseCmd.Flags().StringVarP(&workspacePath, "workspace-dir", "d", "", "Path to workspace JSON files")
	synapseCmd.Flags().StringVarP(&configPath, "config", "c", "", "Path to configuration deployment file")
	synapseCmd.Flags().BoolVar(&debug, "debug", false, "Output debug information")
	synapseCmd.Flags().BoolVar(&dryRun, "dry-run", false, "Performs a dry run")

	synapseCmd.MarkFlagRequired("workspace-dir")
	synapseCmd.MarkFlagRequired("config")

}

var synapseCmd = &cobra.Command{
	Use:   "syn",
	Short: "Manages Synapse Workspace",
	Long:  `Used to validate and deploy a synapse workspace`,
	Run:   invokeSynModule,
}

func invokeSynModule(cmd *cobra.Command, args []string) {
	bin := "bin/synapse"

	sub_args := []string{
		"--dir=" + cmd.Flag("workspace-dir").Value.String(),
		"--config=" + cmd.Flag("config").Value.String(),
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
		fmt.Errorf(err.Error())
		return
	}

	fmt.Print(string(stdout))

}

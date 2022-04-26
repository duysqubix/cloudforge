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
)

func init() {

	synapseCmd.Flags().StringVarP(&workspacePath, "workspace-dir", "d", "", "Path to workspace JSON files")
	synapseCmd.Flags().StringVarP(&configPath, "config", "c", "", "Path to configuration deployment file")

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

	dirpath := "--dir=" + cmd.Flag("workspace-dir").Value.String()
	configPath := "--config=" + cmd.Flag("config").Value.String()

	mod := exec.Command(bin, dirpath, configPath)
	stdout, err := mod.Output()

	if err != nil {
		fmt.Errorf(err.Error())
		return
	}

	fmt.Print(string(stdout))

}

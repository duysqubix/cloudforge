/*
	Synapse management tool

*/

package cmd

import "github.com/spf13/cobra"

func init() {

}

var synapseCmd = &cobra.Command{
	Use:   "syn",
	Short: "Manages Synapse Workspace",
	Long:  `Used to validate and deploy a synapse workspace`,
}

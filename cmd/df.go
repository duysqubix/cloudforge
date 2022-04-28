/*
	Datafactory management tool

*/

package cmd

import "github.com/spf13/cobra"

func init() {

}

var datafactoryCmd = &cobra.Command{
	Use:   "df",
	Short: "Manages datafactory infrastructure",
	Long:  `Used to validate and deploy datafactory`,
}

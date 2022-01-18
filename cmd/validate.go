/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"github.com/spf13/cobra"
)

// validateCmd represents the validate command
var validateCmd = &cobra.Command{
	Use:   "validate",
	Short: "Validate different environments",
	Long: `
	Usage:
		einfra validate [dev, int, uat, prod]
	`,
}

func init() {
	rootCmd.AddCommand(validateCmd)
}

/*
Copyright © 2022 NAME HERE <EMAIL ADDRESS>

*/
package cmd

import (
	"github.com/spf13/cobra"
)

// deployCmd represents the deploy command
var deployCmd = &cobra.Command{
	Use:   "deploy",
	Short: "Deploy to different environments",
	Long: `
		Usage:
			ec deploy [dev, int, uat, prod]
	.`,
}

func init() {
	rootCmd.AddCommand(deployCmd)
}

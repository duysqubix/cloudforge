package utils

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/hashicorp/go-version"
	"github.com/hashicorp/hc-install/product"
	"github.com/hashicorp/hc-install/releases"
	"github.com/hashicorp/terraform-exec/tfexec"
	tfjson "github.com/hashicorp/terraform-json"
)

func makeBackendOpt(k, v string) *tfexec.BackendConfigOption {
	fmtStr := fmt.Sprintf("%s=%s", k, v)
	fmtStr = strings.Replace(fmtStr, "\"", "", -1)
	return tfexec.BackendConfig(fmtStr)
}

type AzureTerraform struct {
	tf *tfexec.Terraform
}

func (t *AzureTerraform) Validate() (bool, []tfjson.Diagnostic) {
	resp, err := t.tf.Validate(context.Background())

	if err != nil {
		logger.Fatal(err)
	}

	if resp.Valid {
		return true, []tfjson.Diagnostic{}
	} else {
		return false, resp.Diagnostics
	}
}

func (t *AzureTerraform) Plan() error {
	_, err := t.tf.Plan(context.Background())
	return err
}

func (t *AzureTerraform) Deploy() error {
	return t.tf.Apply(context.Background())
}

func NewTerraformHandler(c *ConfigFile) *AzureTerraform {
	c.SetArmEnvs()
	installer := &releases.ExactVersion{
		Product: product.Terraform,
		Version: version.Must(version.NewVersion("1.0.11")),
	}

	execPath, err := installer.Install(context.Background())
	if err != nil {
		log.Fatalf("error installing Terraform: %s", err)
	}

	workingDir := TMPDIR_PATH
	tf, err := tfexec.NewTerraform(workingDir, execPath)
	if err != nil {
		log.Fatalf("error running NewTerraform: %s", err)
	}

	tf.SetStdout(os.Stdout)
	tf.SetStderr(os.Stderr)
	tf.SetLogPath("tflog.log")

	storageName := c.Get("STORAGE_ACCOUNT_NAME")
	containerName := c.Get("CONTAINER_NAME")
	tfKey := c.Get("TF_KEY")
	sasToken := c.Get("SAS_TOKEN")

	storageAccountBackend := makeBackendOpt("storage_account_name", storageName)
	containerNameBackend := makeBackendOpt("container_name", containerName)
	tfKeyBackend := makeBackendOpt("key", tfKey)
	sasTokenBackend := makeBackendOpt("sas_token", sasToken)

	err = tf.Init(context.Background(), tfexec.Upgrade(true), storageAccountBackend, containerNameBackend, tfKeyBackend, sasTokenBackend)

	if err != nil {
		log.Fatalf("error running Init: %s", err)
	}

	return &AzureTerraform{
		tf: tf,
	}
}

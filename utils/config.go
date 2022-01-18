package utils

import (
	"os"
	"strings"
)

type ConfigFile struct {
	fpath    string
	keyPairs map[string]string
}

func NewConfigFile(fpath string) *ConfigFile {
	c := ConfigFile{
		fpath:    fpath,
		keyPairs: make(map[string]string),
	}

	return &c
}

func (c *ConfigFile) GetAllOpts() *map[string]string {
	newMap := map[string]string{}

	for k, v := range newMap {
		newMap[k] = v
	}
	return &newMap
}

func (c *ConfigFile) ReadAndParse() {

	if c.fpath == "" {
		// read from os.Env -- and store entire env as dict
		for _, elem := range os.Environ() {
			pair := strings.SplitN(elem, "=", 2)
			key, value := pair[0], pair[1]
			c.keyPairs[key] = value
		}
	} else {

		lines := ReadFileN(c.fpath)
		for _, line := range lines {
			split := strings.SplitN(line, "=", 2)
			key, value := split[0], split[1]
			c.keyPairs[key] = value
		}
	}
}

func (c *ConfigFile) GetArms() map[string]string {
	results := make(map[string]string)
	for k, v := range c.keyPairs {
		if strings.Contains(k, "ARM_") {
			results[k] = v
		}
	}
	return results
}

func (c *ConfigFile) SetArmEnvs() {
	for k, v := range c.GetArms() {
		os.Setenv(k, v)
	}
}

func (c *ConfigFile) Get(keyName string) string {
	value := c.keyPairs[keyName]

	if value == "" {
		logger.Fatalf("Unable to retrieve: %s", keyName)
	}
	return value
}

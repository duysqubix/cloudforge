package internal

import (
	"os"
	"strings"
)

// Object that stores configuration elements
type ConfigFile struct {
	fpath    string
	keyPairs map[string]string
}

// Initializes an empty config object
func NewConfigFile(fpath string) *ConfigFile {
	c := ConfigFile{
		fpath:    fpath,
		keyPairs: make(map[string]string),
	}

	return &c
}

// Retrieve all options fron config as a seperate entity
func (c *ConfigFile) GetAllOpts() map[string]string {
	newMap := map[string]string{}

	for k, v := range c.keyPairs {
		newMap[k] = v
	}
	return newMap
}

// Reads and parses from internal `ConfigFile.fpath`
// if supplied fpath is empty, it will populate internal
// map with environment variables
func (c *ConfigFile) ReadAndParse() {

	if c.fpath == "" {
		// read from os.Env -- and store entire env as dict
		// this will more than likely include variables not of interest
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

// Returns a map of internal elements that have the
// Substring of `ARM_` located within them.
func (c *ConfigFile) GetArms() map[string]string {
	results := make(map[string]string)
	for k, v := range c.keyPairs {
		if strings.Contains(k, "ARM_") {
			results[k] = v
		}
	}
	return results
}

// Sets all ARM variables as environment variables
func (c *ConfigFile) SetArmEnvs() {
	for k, v := range c.GetArms() {
		os.Setenv(k, v)
	}
}

// Helper method to retrieve elment within internal map
// Unlike, built-in map, this will panic if key is not found
func (c *ConfigFile) Get(keyName string) string {
	value := c.keyPairs[keyName]

	if value == "" {
		logger.Fatalf("Unable to retrieve: %s", keyName)
	}
	return value
}

# Modules

### Purpose

Modules intended purpose are meant to be seperate applications that extend the
abilities and functionality of the origin deployment engine.

### Architecture

Each module must abide by certain rules in order for the framework to be fully
functional. Below are requirements for each app.

1. Must be designed as a CLI app

#### Language

It is preferred to write modules in Python, for uniformity, however any language
can theoritically be chosen to write modules. It is the developers
responsibility to properly integrate modules into the base program via Golang.

#### Supported Languages

- Python 3.8+

#### Notes

- You must run bash script as user to ensure that you are using the system
  python installation instead of any potential virtualenv variables that are
  preloaded.

  `bash -l compile_modules.sh`

### Synapse Module

Synapse Module is responsible for dynamically creating valid synapse ARM
templates from synapse json files. In order to run the module independently of
the main program, you will need to have `python 3.8+` environment activated.
Install all requirements via `pip install -r requirements.txt`

Command: `ec syn`

Args:

- `--dir`: Current directory where Synapse Workspace is saved
- `--config` : Deployment configuration file
- `--workspace-name`: Name of the workspace targeted
- `--output`: name given to the ARM file generated

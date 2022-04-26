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

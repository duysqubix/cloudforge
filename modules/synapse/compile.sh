#!/bin/bash 

PY_INSTALLER=$(which pyinstaller)
${PY_INSTALLER} -F --clean -y -n syn main.py

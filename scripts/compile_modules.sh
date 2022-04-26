#!/bin/bash 

#
#  Compiles all modules
#

PY_INSTALLER=$(which pyinstaller)
MODULES=("synapse")

for module in ${MODULES[@]}; do
    module_dir=${PWD}/modules/${module} 
    
    echo "Processing Module: ${module^^}"
    ${PY_INSTALLER} -F --clean -y -n ${module} ${module_dir}/main.py

    
done

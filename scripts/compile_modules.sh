#!/bin/bash 

#
#  Compiles all modules
#

PY_INSTALLER=$(which pyinstaller)
PY_TEST=$(which pytest)

echo "PY_INSTALLER=${PY_INSTALLER}"

if  [ ! -n ${PY_INSTALLER} ]; then
    echo "PyInstaller not found."
    exit 1
fi

if [ ! -n ${PY_TEST} ]; then
    echo "Pytest not found"
    exit 1
fi

MODULES=("synapse")

for module in ${MODULES[@]}; do
    module_dir=${PWD}/modules/${module} 
    
    echo "Processing Module: ${module^^}"
    
    # perform unit tests
    ${PY_TEST} ${module_dir}
    for file in ${module_dir}/*.py;
    do
        fname=`basename $file .py`
        ${PY_INSTALLER} -F --clean --workpath=/tmp/.build-$RANDOM/ --distpath=${PWD}/bin -y -n ${module}_${fname} ${module_dir}/${fname}.py&
    done;

    
done

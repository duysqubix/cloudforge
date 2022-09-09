#!/bin/bash 

#
#  Compiles all modules
#
PY=$(which python3)
PY_INSTALLER=$(which pyinstaller)
PY_TEST=$(which pytest)

if [ ! -n $1 ]; then
    echo "Supply argument for binary name"
    exit 1
fi

echo "PY_INSTALLER=${PY_INSTALLER}"

if  [ ! -n ${PY_INSTALLER} ]; then
    echo "PyInstaller not found."
    exit 1
fi

if [ ! -n ${PY_TEST} ]; then
    echo "Pytest not found"
    exit 1
fi

if [ ! -n ${PY} ]; then
    echo "Python3 not found"
    exit 1 
fi 

# generate spec build files for all available modules
echo "Generating spec files"
${PY} ${PWD}/scripts/build_spec.py # path -> /tmp/MODULE_NAME.spec



MODULES=("synapse")

for module in ${MODULES[@]}; do
    module_dir=${PWD}/modules/${module} 
    uid=$(uuidgen -t)

    echo "Processing Module: ${module^^}"    

    # perform unit tests
    ${PY_TEST} ${module_dir}
    
    uid_workdir="/tmp/.build-${uid}_$1-${module}"
    spec_dir=${uid_workdir}/spec 

    mkdir -p -v ${spec_dir}
    mv -v /tmp/${module}.spec ${spec_dir}/${module}.spec
    ${PY_INSTALLER} --clean --workpath=$uid_workdir --distpath=${PWD}/bin -y ${spec_dir}/${module}.spec

    
done

#!/usr/bin/env bash

BIN=ec

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ] ; do SOURCE="$(readlink "$SOURCE")"; done
DIR="$( cd "$(dirname "$SOURCE" )/.." && pwd )"
# Go project

echo "Working Directory: [${DIR}]"

GOPROJ="github.com/vorys-econtrol/ec"

# Change into that directory
cd "${DIR}"

# In release mode we don't want debug information in the binary
if ! [[ -n "${EC_RELEASE}" ]]; then
    echo "==> Building for Development"
    LD_FLAGS="-w -X ${GOPROJ}/version.PreRelease=dev"
else
    echo "==> Building for Release"
    LD_FLAGS="-w -s"
fi 

if [ ! -d ${DIR}/bin ]; then
    mkdir -p ${DIR}/bin
fi
# Ensure all remote modules are downlaoded and cached
go mod download 

# Test 
echo "==> Testing..."
go test -v ./...

#Build 
echo "==> Building..."

go build \
    -ldflags "${LD_FLAGS}" \
    -o "${DIR}/bin/${BIN}"



# Build Modules
echo "==> Compiling Modules"

bash -l ${DIR}/scripts/compile_modules.sh ${BIN}

#Done 
echo 
echo "==> Done"

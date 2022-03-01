#!/bin/bash 

CWD=${PWD}
ec=${CWD}/_ECDeployTool/core/ec

chmod +x ${ec}

echo "CWD: ${CWD}" && \
${CWD}/scripts/tree ${CWD} && \

cd terraform_files/core && \
${ec} version && \
${ec} validate dev --no-plan

#!/usr/bin/env bash

# Run Quicksilver and record the trace data and output it to ./data
QS_DIR=~/git/Quicksilver # You'll probably need to change this
UF_DIR=~/git/uftrace-2-python # This as well

cd ${QS_DIR}

uftrace record -t 500us -- ./src/qs --nx 10 --ny 10 --nz 10 --nSteps 5 --inputFile ${QS_DIR}/Examples/NoFission/noFission.inp
uftrace dump --chrome >> ${UF_DIR}/data/trace.json
cd -
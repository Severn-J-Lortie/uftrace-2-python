#!/usr/bin/env bash

# Run Quicksilver and record the trace data and output it to ./data
QS_DIR=~/git/Quicksilver # You'll probably need to change this
UF_DIR=~/git/uftrace-2-python # This as well


sudo echo # doing a no-op to force sudo before the turbostat script
uftrace record -t 5ms -- ${QS_DIR}/src/qs --nx 10 --ny 10 --nz 10 --nSteps 5 --inputFile ${QS_DIR}/Examples/NoFission/noFission.inp &
qs_pid=$!
python ${UF_DIR}/turbostat.py &
turbo_pid=$!
wait $qs_pid
sleep 1
kill $turbo_pid
uftrace dump --chrome > ${UF_DIR}/data/trace.json
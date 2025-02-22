#!/usr/bin/env bash

# Run Quicksilver and record the trace data and output it to ./data
QS_DIR=~/git/Quicksilver # You'll probably need to change this
UF_DIR=~/git/uftrace-2-python # This as well

sudo echo # doing a no-op to force sudo before the turbostat script

echo "Beginning test. This will run for 3 iterations so it may take a while."
echo "------------------------"
TIMESTAMP=$(TZ="America/New_York" date +"%Y-%m-%d_%H-%M-%S")
OUTPUT_PATH=${UF_DIR}/data/$TIMESTAMP
echo "Writing output to directory: ${OUTPUT_PATH}"
mkdir -p ${OUTPUT_PATH}

# Function to clean up all processes on exit or CTRL+C
cleanup() {
    echo "Cleaning up..."
    pkill -P $$
    wait 
    echo "Cleanup complete."
}
trap cleanup EXIT

for i in {1..3}; do
  echo "Run $i"
  RUN_OUTPUT_PATH=${OUTPUT_PATH}/run_$i
  mkdir ${RUN_OUTPUT_PATH}

  uftrace record -t 5ms -- ${QS_DIR}/src/qs --inputFile ${UF_DIR}/qs-test-local-cfg.inp &
  qs_pid=$!

  python ${UF_DIR}/turbostat.py --output-file ${RUN_OUTPUT_PATH}/stats.csv &
  turbo_pid=$!
  wait $qs_pid

  sleep 1
  kill $turbo_pid
  uftrace dump --chrome > ${RUN_OUTPUT_PATH}/trace.json
done

# Compress
for dir in ${UF_DIR}/data/*; do
    tar -czf "${dir}.tar.gz" -C "${UF_DIR}/data" "$(basename "$dir")"
    rm -rf ${dir}
done
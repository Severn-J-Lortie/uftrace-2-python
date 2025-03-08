#!/usr/bin/env bash
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 output_file"
  exit 1
fi

output_file="${1}.stats"
log_file="${1}.log"
total_time=0
total_energy=0

>"$output_file"

QS_DIR=/home/severn/git/Quicksilver-fork
UF_DIR=/home/severn/git/uftrace-2-python

source ${QS_DIR}/xml_profile

for i in {1..3}; do
  echo "Run $i:" >> "$log_file"
  initial_energy=$(cat /sys/class/powercap/intel-rapl:0/energy_uj)
  start=$(date +%s%N)
  ${QS_DIR}/src/qs --inputFile ${UF_DIR}/qs-test-local-cfg.inp 2>&1 | tee ${log_file}
  end=$(date +%s%N)
  final_energy=$(cat /sys/class/powercap/intel-rapl:0/energy_uj)
  elapsed_ns=$((end - start))
  elapsed_s=$(echo "scale=3; $elapsed_ns/1000000000" | bc)
  energy_diff=$((final_energy - initial_energy))
  echo "Energy diff run $i: $energy_diff" | tee -a "$output_file"
  total_time=$(echo "$total_time + $elapsed_s" | bc)
  total_energy=$((total_energy + energy_diff))
done

avg_time=$(echo "scale=3; $total_time / 3" | bc)
avg_energy=$(echo "scale=0; $total_energy / 3" | bc)
echo "Average Time: $avg_time seconds" | tee -a "$output_file"
echo "Average Energy: $avg_energy microjoules" | tee -a "$output_file"

#!/usr/bin/env bash
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 folder_name"
  exit 1
fi

mkdir -p ./data/"$1"
output_file="./data/${1}/run.csv"
log_file="./data/${1}/run.log"
total_time=0
total_energy=0

# Clear log and output files.
> "$log_file"
> "$output_file"

echo "run,elapsed_time_ns,energy_uj" > "$output_file"

QS_DIR=/global/home/hpc5581/git/Quicksilver-fork
UF_DIR=/global/home/hpc5581/git/uftrace-2-python
RAPL_DIR=/global/home/hpc5581/git/rapl-read-ryzen

source ${QS_DIR}/xml_profile

for i in {1..1}; do
  echo "Run $i:" >> "$log_file"

  # Start the QS run and record start time.
  start=$(date +%s%N)
  ${QS_DIR}/src/qs --inputFile ${UF_DIR}/qs-test-local-cfg.inp 2>&1 | tee -a "$log_file" &
  qs_pid=$!

  trap "kill $qs_pid 2>/dev/null; exit 1" SIGINT

  energy=0
  # While QS is running, sample power readings every 0.1 seconds.
  while kill -0 $qs_pid 2>/dev/null; do
      output=$(${RAPL_DIR}/ryzen_highres)
      if [[ $output =~ Core\ sum:\ ([0-9.]+)W ]]; then
          watt=${BASH_REMATCH[1]}
          energy=$(echo "$energy + $watt * 0.01 * 1000000" | bc -l)
      fi
  done

  end=$(date +%s%N)
  wait $qs_pid

  elapsed_ns=$((end - start))
  # Round the energy to an integer (microjoules)
  energy_int=$(printf "%.0f" "$energy")

  echo "$i,$elapsed_ns,$energy_int" >> "$output_file"
  total_time=$((total_time + elapsed_ns))
  total_energy=$(echo "$total_energy + $energy" | bc -l)
done

avg_time=$(echo "scale=3; $total_time / 3" | bc)
avg_energy=$(echo "scale=0; $total_energy / 3" | bc)
echo "avg,$avg_time,$avg_energy" >> "$output_file"
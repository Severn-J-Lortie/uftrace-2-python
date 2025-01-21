import subprocess
import csv
import time
import math

def run_turbostat(interval=0.5, output_csv="./data/stats.csv"):
  """
  Runs turbostat with the specified interval (in seconds),
  and parses its output line by line. It writes data to the
  output_csv file.
  """
  cmd = ["sudo", "turbostat", "--interval", str(interval), "--quiet"]
  process = subprocess.Popen(
      cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

  try:
    header_line = next(process.stdout).strip()
  except StopIteration:
    print("No output from turbostat.")
    return
  headers = header_line.split()
  headers.insert(0, "TIME_STAMP");

  with open(output_csv, "w") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(headers)
    timestamp = time.time_ns()
    for line in process.stdout:
      line = line.strip()
      if not line or line.startswith("turbostat:"):
        continue
      if line.split() == headers[1:]:
        timestamp = time.time_ns()
        continue
      cols = line.split()
      cols.insert(0, timestamp / 1000)
      writer.writerow(cols)
  process.wait()


if __name__ == "__main__":
  run_turbostat(interval=0.1)

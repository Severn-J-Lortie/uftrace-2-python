import subprocess
import atexit
import csv
import time
import psutil
import argparse

def run_turbostat(interval=0.5, output_csv="./data/stats.csv"):
  """
  Runs turbostat with the specified interval (in seconds),
  and parses its output line by line. It writes data to the
  output_csv file.
  """
  cmd = ["sudo", "turbostat", "--interval", str(interval), "--quiet"]
  process = subprocess.Popen(
      cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

  def cleanup():
    if process.poll() is None:
      print("Killing turbostat process...")
      process.terminate()

  atexit.register(cleanup)

  try:
    header_line = next(process.stdout).strip()
  except StopIteration:
    print("No output from turbostat.")
    return
  headers = header_line.split()
  headers.insert(0, "TIME_STAMP")
  headers.append("used_memory")

  with open(output_csv, "w") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(headers)
    timestamp = time.time_ns()
    for line in process.stdout:
      line = line.strip()
      if not line or line.startswith("turbostat:"):
        continue
      if line.split() == headers[1:-1]:
        timestamp = time.time_ns()
        continue
      cols = line.split()
      mem = psutil.virtual_memory().percent
      cols.insert(0, timestamp / 1000)
      cols.append(mem)
      writer.writerow(cols)
  process.wait()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-o", "--output-dir", help="Output data directory to write stats.csv file", type=str)
  args = parser.parse_args()
  run_turbostat(interval=0.08, output_csv=args.output_dir)

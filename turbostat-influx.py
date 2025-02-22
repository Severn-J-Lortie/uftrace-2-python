import subprocess
import atexit
import time
import psutil
import os
import argparse

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = os.environ['INFLUX_GENERAL_API_TOKEN']
INFLUXDB_ORG = "main"
INFLUXDB_BUCKET = "powerstats"

def run_turbostat(run_id, interval=0.5, ):
  """
  Runs turbostat with the specified interval (in seconds),
  and parses its output line by line. This writes data to InfluxDB.
  """

  client = InfluxDBClient(
    url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
  write_api = client.write_api(write_options=SYNCHRONOUS)

  point = Point("run_info")
  point = point.tag("run_id", run_id)
  point = point.field("start_ts", time.time_ns())
  point = point.time(time.time_ns(), write_precision=WritePrecision.NS)
  write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

  cmd = ["sudo", "turbostat", "--interval", str(interval), "--quiet"]
  process = subprocess.Popen(
    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
  )

  def cleanup():
    process.terminate()
    point = Point("run_info")
    point = point.tag("run_id", run_id)
    point = point.field("end_ts", time.time_ns())
    point = point.time(time.time_ns(), write_precision=WritePrecision.NS)
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
    client.close()

  atexit.register(cleanup)

  try:
    header_line = next(process.stdout).strip()
  except StopIteration:
    print("No output from turbostat.")
    return

  headers = header_line.split()
  headers.append("used_memory")

  while True:
    line = process.stdout.readline()
    if not line:
      if process.poll() is not None:
        break
      time.sleep(0.01)
      continue

    line = line.strip()
    if not line or line.startswith("#") or line.startswith("turbostat:"):
      continue

    if line == header_line:
      continue
    mem = psutil.virtual_memory().percent

    cols = line.split()
    cols.append(str(mem))

    data = dict(zip(headers, cols))
    if data.get("Core", "") == "-":
      data["Core"] = "all"
    if data.get("CPU", "") == "-":
      data["CPU"] = "all"

    point = Point("cpu_stats")
    point = point.tag("Core", data["Core"])
    point = point.tag("CPU", data["CPU"])
    point = point.tag("RunID", run_id)
    point = point.time(time.time_ns(), write_precision=WritePrecision.NS)

    numeric_fields = list(data.keys())[1:]

    for field in numeric_fields:
      if field in data:
        try:
          value = float(data[field])
          point = point.field(field.replace("%", "_pct"), value)
        except ValueError:
          pass
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

  process.wait()


if __name__ == "__main__":
  parser = argparse.ArgumentParser("Turbostat Influx Writer")
  parser.add_argument("run_id")
  args = parser.parse_args()
  run_turbostat(args.run_id, interval=0.08)

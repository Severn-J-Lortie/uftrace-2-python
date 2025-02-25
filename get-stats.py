import pandas as pd
import argparse
import tarfile
from os.path import basename
from io import BytesIO

def get_total_energy(stats_csv):
  start_time = int(stats_csv["TIME_STAMP"].iloc[0])
  end_time = int(
    stats_csv["TIME_STAMP"].iloc[stats_csv.loc[stats_csv["CPU"] == "-"].index[1]])
  delta = (end_time - start_time)/1e6
  energy = 0  # Joules
  for watt in stats_csv["PkgWatt"][stats_csv["PkgWatt"].notnull()].iloc[:-2]:
    energy += float(watt) * delta
  return energy

def get_total_exec_time(stats_csv):
  start_time = int(stats_csv["TIME_STAMP"].iloc[0])
  end_time = int(stats_csv["TIME_STAMP"].iloc[-1])
  return (end_time-start_time)/1e3

def analyze_csv(file):
  stats_csv = pd.read_csv(args.file)
  total_energy = get_total_energy(stats_csv)
  total_exec_time = get_total_exec_time(stats_csv)
  print(f"Energy {total_energy:.0f} J")
  print(f"Total runtime {total_exec_time:.0f} ms")

def analyze_dir(dir):
  times = []
  energies = []
  with tarfile.open(dir, "r:gz") as tar:
    for member in tar.getmembers():
      file_obj = tar.extractfile(member)
      if file_obj:
        if basename(member.name) == "stats.csv":
          file_data = BytesIO(file_obj.read())
          stats_csv = pd.read_csv(file_data)
          times.append(get_total_exec_time(stats_csv))
          energies.append(get_total_energy(stats_csv))
  avg_time = sum(times)/len(times)
  avg_energy = sum(energies)/len(energies)
  print(f"Average energy {avg_energy:.0f} J")
  print(f"Average time {avg_time:.0f} ms")


if __name__ == "__main__":
  parser = argparse.ArgumentParser("Turbostat output stat calculator")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-f", "--file", help="The input file to analyze", type=str)
  group.add_argument("-d", "--dir", help="A compressed directory containing multiple runs (.tar.gz) to analyze", type=str)
  # TODO: -c argument to allow comparing two runs
  args = parser.parse_args()
  if args.file:
    analyze_csv(args.file)
  elif args.dir:
    analyze_dir(args.dir)

import pandas as pd
import argparse
import tarfile
import matplotlib.pyplot as plt
import numpy as np
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

def get_multi_run_stats(dir):
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
  return avg_time, avg_energy

def analyze_csv(file):
  stats_csv = pd.read_csv(args.file)
  total_energy = get_total_energy(stats_csv)
  total_exec_time = get_total_exec_time(stats_csv)
  print(f"Energy {total_energy:.0f} J")
  print(f"Total runtime {total_exec_time:.0f} ms")

def analyze_dir(dir):
  avg_energy, avg_time = get_multi_run_stats(dir)
  print(f"Average energy {avg_energy:.0f} J")
  print(f"Average time {avg_time:.0f} ms")

def analyze_comparison(dir1, dir2):
  run_1_avg_time, run_1_avg_energy = get_multi_run_stats(dir1);
  run_2_avg_time, run_2_avg_energy = get_multi_run_stats(dir2);

  categories = ["Baseline", "Test"]
  time_values = [run_1_avg_time, run_2_avg_time]
  energy_values = [run_1_avg_energy, run_2_avg_energy]
  time_change = ((time_values[1] - time_values[0]) / time_values[0]) * 100
  energy_change = ((energy_values[1] - energy_values[0]) / energy_values[0]) * 100
  fig, ax1 = plt.subplots(figsize=(8, 5))
  x = np.arange(len(categories))
  width = 0.4
  ax1.bar(x - width/2, time_values, width, label="Time (ms)", color="tab:blue")
  ax1.bar(x + width/2, energy_values, width, label="Energy (J)", color="tab:orange")
  ax1.set_ylabel("Raw Values")
  ax1.set_title("Comparison of Runtime and Energy Usage")
  ax1.set_xticks(x)
  ax1.set_xticklabels(categories)
  ax1.legend(loc="upper left")
  ax2 = ax1.twinx()
  ax2.set_ylabel("Percentage Change (%)")
  ax2.plot(x, [0, time_change], "bo-", label="Time Change (%)")
  ax2.plot(x, [0, energy_change], "ro-", label="Energy Change (%)")
  ax2.axhline(0, color="gray", linestyle="--", linewidth=0.8)
  ax2.legend(loc="upper right")
  plt.savefig("run-comparison.png");



if __name__ == "__main__":
  parser = argparse.ArgumentParser("Turbostat output stat calculator")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument("-f", "--file", help="The input file to analyze", type=str)
  group.add_argument("-d", "--dir", help="A compressed directory containing multiple runs (.tar.gz) to analyze", type=str)
  group.add_argument("-c", "--compare", help="Compare two runs (give the two directory paths)", nargs=2, type=str)
  args = parser.parse_args()
  if args.file:
    analyze_csv(args.file)
  elif args.dir:
    analyze_dir(args.dir)
  elif args.compare:
    analyze_comparison(args.compare[0], args.compare[1])

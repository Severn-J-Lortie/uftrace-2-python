import pandas as pd

stats_csv = pd.read_csv('./data/stats.csv')


def get_total_energy():
  start_time = int(stats_csv["TIME_STAMP"].iloc[0])
  end_time = int(
    stats_csv["TIME_STAMP"].iloc[stats_csv.loc[stats_csv["CPU"] == "-"].index[1]])
  delta = (end_time - start_time)/1e6
  energy = 0  # Joules
  for watt in stats_csv["PkgWatt"][stats_csv["PkgWatt"].notnull()].iloc[:-2]:
    energy += float(watt) * delta
  return energy

def get_total_exec_time():
  start_time = int(stats_csv["TIME_STAMP"].iloc[0])
  end_time = int(stats_csv["TIME_STAMP"].iloc[-1])
  return (end_time-start_time)/1e3

print(f"Energy {get_total_energy():.0f} J")
print(f"Total runtime {get_total_exec_time():.0f} ms")
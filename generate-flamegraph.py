import json
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import colormaps
from matplotlib.widgets import Button
import pandas as pd
import argparse
from os import path

matplotlib.use("TkAgg")

units = {"Avg_MHz": "Avg MHz (Hz)", "FREQ": "Frequency (Hz)"}

prev_annotation = None

def generate_stack_timeline(trace_file):
  with open(trace_file, "r") as file:
    data = json.load(file)

  event_timeline = []
  event_stack = []
  measurement_start = 0
  for event in data["traceEvents"]:
    # Ignore metadata for now
    event["ts"] = event["ts"]/1e6
    if event["ph"] == "M":
      continue

    if not measurement_start:
      measurement_start = event["ts"]

    if event["ph"] == "B":  # B means begin
      event_stack.append({
          "name": event["name"],
          "start": event["ts"] - measurement_start,
          "depth": len(event_stack)
      })

    if event["ph"] == "E":  # E means end
      prev_event = event_stack.pop()
      prev_event["end"] = event["ts"] - measurement_start
      prev_event["duration"] = event["ts"] - \
          measurement_start - prev_event["start"]
      event_timeline.append(prev_event)
  return event_timeline


def plot_event_timeline(event_timeline, power_measurements, columns, cpus, title):
  # update the trace file and data file to be in elapsed seconds
  power_data = pd.read_csv(power_measurements)
  power_data["TIME_STAMP"] = power_data["TIME_STAMP"] - \
      int(power_data["TIME_STAMP"][0])
  power_data["TIME_STAMP"] = power_data["TIME_STAMP"]/1e6

  for event in event_timeline:
    event["start"] = event["start"]
    event["end"] = event["end"]
    event["duration"] = event["duration"]

  fig, ax = plt.subplots(figsize=(10, 6))
  # have to set this, bounding box would change each time, causing incorrect text width
  ax.set_xlim(0, max([event["end"] for event in event_timeline]))

  # plot the power_metrics
  colormap = colormaps.get_cmap("tab20c")
  ax2 = ax.twinx()
  ax2.set_zorder(3)
  labels = []
  for i, column in enumerate(columns):
    if not column in power_data.columns:
      raise Exception(f"Column {column} does not exist in the CSV.")
    for cpu in cpus:
      if isinstance(cpu, (int)):
        stat_color = colormap(cpu / (max(cpus) + 1))
      else:
        stat_color = "blue"
      # arbritrary 5% buffer on top of max point.
      ax2.set_ylim(0, power_data[column].max() +
                  (power_data[column].max()) * .05)
      ax2.yaxis.tick_left()
      ax2.yaxis.set_label_position("left")
      ax2.plot(power_data.loc[power_data["CPU"] == f"{cpu}", "TIME_STAMP"],
              power_data.loc[power_data["CPU"] == f"{cpu}", column], picker=False, color=stat_color)
      labels.append(f"{column if not column in units.keys() else units[column] } (cpu {cpu})" or f"{column} ({cpu})")
  ax2.legend(labels)

  # plot the traces
  bar_height = 0.3
  bar_vertical_space = 0.05

  renderer = fig.canvas.get_renderer()
  ax4 = ax.twinx()

  for i, event in enumerate(event_timeline):
    y_start = event["depth"] * (bar_vertical_space + bar_height)
    x_start = event["start"]
    bar_width = event["duration"]
    text = ax4.text(x_start + bar_width / 2, y_start + bar_height / 2,
                    event["name"], ha="center", va="center", color="white")
    bounding_box = text.get_window_extent(renderer=renderer)
    text_width = ax4.transData.inverted().transform((bounding_box.width, 0))[
        0] - ax4.transData.inverted().transform((0, 0))[0]
    if bar_width < text_width:  # if bar is too small
      max_bar_text_width = int(
          (bar_width/text_width) * len(event["name"]))
      if max_bar_text_width > 4:  # event for at least 1 character and ...
        text.set_text(event["name"][:max_bar_text_width - 3] + "...")
      else:
        text.remove()
    legend_label = event["name"].lstrip("_")

    bar_colour = "black"
    ax4.broken_barh([(x_start, bar_width)], (y_start, bar_height),
                    facecolors=bar_colour, picker=True, label=legend_label)

  # have bars only take up bottom half of plot
  ax4.set_ylim(0, max([event["depth"] for event in event_timeline]) * 1.5)
  ax4.set_yticklabels([])
  ax4.set_yticks([])

  ax.set_yticklabels([])
  ax.set_yticks([])
  ax.set_xlabel("Execution Time (s)")
  plt.savefig("./event_timeline.png")

  def hover(event):
    global prev_annotation
    label = event.artist.get_label()
    if prev_annotation is not None:  # need to clear previous annotation or else they will stack
      prev_annotation.remove()

    prev_annotation = ax4.annotate(label, xy=(event.mouseevent.xdata, event.mouseevent.ydata), xytext=(
        (ax4.get_xlim()[1] / 3), ax4.get_ylim()[1] - 0.5), arrowprops=dict(arrowstyle="->", color="black", lw=1))
    fig.canvas.draw()
    print(label)

  fig.canvas.mpl_connect("pick_event", hover)

  #change the z-order of the axis to make top one clickable
  axes = [ax2, ax4]
  ax2.set_zorder(2)
  ax4.set_zorder(1)
  
  def change_zorder(event):
    start = axes.pop(0)
    axes.append(start)

    for i, axis in enumerate(axes):
      axis.set_zorder(len(axes) - i)
    
    fig.canvas.draw()

  #add room for button
  fig.subplots_adjust(right=0.9)
  # x,y,width,height
  button_ax = plt.axes([0.95, 0.05, 0.04, 0.04])  
  button = Button(button_ax, "Cycle")
  button.on_clicked(change_zorder)

  fig.suptitle(title)

  plt.show()  # Not gonna work over SSH (without X11 forwarding) --> save the plot as well
  plt.savefig("./stack-trace.png")

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-d", "--data-dir", help="Path to data directory for the run. It must contain a stats.csv and trace.json file", type=str, required=True)
  parser.add_argument("-c", "--cpu", help="A list of CPUs for which to view the data", type=list, required=True)
  parser.add_argument("-f", "--fields", help="One or more fields to view. They must match a header in the stats.csv file", nargs="+", type=str, required=True)
  parser.add_argument("-p", "--plot-title", help="Optional title of the plot", type=str)
  args = parser.parse_args()
  trace_file_path = path.join(args.data_dir, "trace.json")
  stats_file_path = path.join(args.data_dir, "stats.csv")
  timeline = generate_stack_timeline(trace_file_path)
  plot_event_timeline(timeline, stats_file_path,
                      args.fields, args.cpu, args.plot_title if args.plot_title else "Plot")



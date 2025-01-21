import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import colormaps
import pandas as pd

units = {'Avg_MHz': 'Power (W)', 'FREQ': 'Frequency (Hz)'}

prev_annotation = None


def generate_stack_timeline(trace_file):
  with open(trace_file, 'r') as file:
    data = json.load(file)

  event_timeline = []
  event_stack = []
  measurement_start = 0
  for event in data['traceEvents']:
    # Ignore metadata for now
    event['ts'] = event['ts']/1e6
    if event['ph'] == 'M':
      continue

    if not measurement_start:
      measurement_start = event['ts']

    if event['ph'] == 'B':  # B means begin
      event_stack.append({
          'name': event['name'],
          'start': event['ts'] - measurement_start,
          'depth': len(event_stack)
      })

    if event['ph'] == 'E':  # E means end
      prev_event = event_stack.pop()
      prev_event['end'] = event['ts'] - measurement_start
      prev_event['duration'] = event['ts'] - \
          measurement_start - prev_event['start']
      event_timeline.append(prev_event)
  return event_timeline


def plot_event_timeline(event_timeline, power_measurements, columns, title):
  # update the trace file and data file to be in elapsed seconds
  power_data = pd.read_csv(power_measurements)
  power_data['TIME_STAMP'] = power_data['TIME_STAMP'] - \
      power_data['TIME_STAMP'][0]
  power_data['TIME_STAMP'] = power_data['TIME_STAMP']/1e6
  for event in event_timeline:
    event['start'] = event['start']
    event['end'] = event['end']
    event['duration'] = event['duration']

  fig, ax = plt.subplots(figsize=(10, 6))
  # have to set this, bounding box would change each time, causing incorrect text width
  ax.set_xlim(0, max([event['end'] for event in event_timeline]))

  # plot the power_metrics, first one and second
  if columns[0] in power_data.columns:
    column = columns[0]
    ax2 = ax.twinx()
    # arbritrary 5% buffer on top of max point.
    ax2.set_ylim(0, power_data[column].max() +
                 (power_data[column].max()) * .05)
    ax2.yaxis.tick_left()
    ax2.yaxis.set_label_position("left")
    ax2.plot(power_data['TIME_STAMP'],
             power_data[column], picker=False, color="red")
    ax2.set_ylabel(units[column], color="red")

  if len(columns) > 1:
    if columns[1] in power_data.columns:
      column = columns[1]
      ax3 = ax.twinx()
      # arbritrary 5% buffer on top of max point.
      ax3.set_ylim(0, power_data[column].max() +
                   (power_data[column].max()) * .05)
      ax3.yaxis.tick_right()
      ax3.yaxis.set_label_position("right")
      ax3.plot(power_data['TIME_STAMP'],
               power_data[column], picker=False, color="blue")
      ax3.set_ylabel(units[column], color="blue")

  # plot the traces
  bar_height = 0.3
  bar_vertical_space = 0.05

  colormap = colormaps.get_cmap('tab20c')
  renderer = fig.canvas.get_renderer()
  ax4 = ax.twinx()

  for i, event in enumerate(event_timeline):
    y_start = event['depth'] * (bar_vertical_space + bar_height)
    x_start = event['start']
    bar_width = event['duration']
    text = ax4.text(x_start + bar_width / 2, y_start + bar_height / 2,
                    event['name'], ha='center', va='center', color='white')
    bounding_box = text.get_window_extent(renderer=renderer)
    text_width = ax4.transData.inverted().transform((bounding_box.width, 0))[
        0] - ax4.transData.inverted().transform((0, 0))[0]
    if bar_width < text_width:  # if bar is too small
      max_bar_text_width = int(
          (bar_width/text_width) * len(event['name']))
      if max_bar_text_width > 4:  # event for at least 1 character and ...
        text.set_text(event['name'][:max_bar_text_width - 3] + '...')
      else:
        text.remove()
    legend_label = event['name'].lstrip('_')

    bar_colour = "black"  # bar_colour = colormap(i / len(event_timeline))
    ax4.broken_barh([(x_start, bar_width)], (y_start, bar_height),
                    facecolors=bar_colour, picker=True, label=legend_label)

  # have bars only take up bottom half of plot
  ax4.set_ylim(0, max([event['depth'] for event in event_timeline]) * 1.5)
  ax4.set_yticklabels([])
  ax4.set_yticks([])

  ax.set_yticklabels([])
  ax.set_yticks([])
  ax.set_xlabel('Execution Time (s)')
  plt.savefig('./event_timeline.png')

  def hover(event):
    global prev_annotation
    label = event.artist.get_label()
    if prev_annotation is not None:  # need to clear previous annotation or else they will stack
      prev_annotation.remove()

    prev_annotation = ax4.annotate(label, xy=(event.mouseevent.xdata, event.mouseevent.ydata), xytext=(
        (ax4.get_xlim()[1] / 3), ax4.get_ylim()[1] - 0.5), arrowprops=dict(arrowstyle="->", color="black", lw=1))
    fig.canvas.draw()

  fig.canvas.mpl_connect('pick_event', hover)
  plt.title(title)

  # cosmetic changes to chart

  plt.show()  # Not gonna work over SSH (without X11 forwarding) --> save the plot as well
  plt.savefig('./stack-trace.png')


timeline = generate_stack_timeline('./data/trace.json')

# SOME USAGE:
# pass in timeline, name of data file, the columns to plot, and then plot title.
# plot_event_timeline(timeline, 'main_test1731268056.txt',["POWER", "FREQ"], "CPUx Power and Frequency Against Trace Timeline")
plot_event_timeline(timeline, 'data/stats.csv',
                    ["Avg_MHz"], "CPUx Power Against Trace Timeline")

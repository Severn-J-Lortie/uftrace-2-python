import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import colormaps

prev_annotation = None

def generate_stack_timeline(trace_file):
  with open(trace_file, 'r') as file:
    data = json.load(file)

  event_timeline = []
  event_stack = []
  measurement_start = 0
  for event in data['traceEvents']:
    # Ignore metadata for now
    if event['ph'] == 'M':
      continue

    if not measurement_start:
      measurement_start = event['ts']

    if event['ph'] == 'B': # B means begin
      event_stack.append({
        'name': event['name'],
        'start': event['ts'] - measurement_start,
        'depth': len(event_stack)
      })

    if event['ph'] == 'E': # E means end
      prev_event = event_stack.pop()
      prev_event['end'] = event['ts'] - measurement_start
      prev_event['duration'] = event['ts'] - measurement_start - prev_event['start']
      event_timeline.append(prev_event)
  return event_timeline

def plot_event_timeline(event_timeline):
  fig, ax = plt.subplots(figsize=(10, 6))
  ax.set_xlim(0, max([event['end'] for event in event_timeline])) #have to set this, bounding box would change each time, causing incorrect text width

  bar_height = 1
  bar_vertical_space = 0.25

  colormap = colormaps.get_cmap('tab20c')
  renderer = fig.canvas.get_renderer()

  for i, event in enumerate(event_timeline):
    y_start = event['depth'] * (bar_vertical_space + bar_height)
    x_start = event['start']
    bar_width =  event['duration']
    text = ax.text(x_start + bar_width / 2, y_start + bar_height / 2, event['name'], ha='center', va='center', color='white')
    bounding_box = text.get_window_extent(renderer=renderer)
    text_width = ax.transData.inverted().transform((bounding_box.width, 0))[0] - ax.transData.inverted().transform((0, 0))[0]
    if bar_width < text_width: #if bar is too small
      max_bar_text_width = int((bar_width/text_width) * len(event['name']))
      if max_bar_text_width > 4: #event for at least 1 character and ...
        text.set_text(event['name'][:max_bar_text_width - 3] + '...')
      else:
        text.remove()
    legend_label = event['name'].lstrip('_')

    bar_colour = colormap(i / len(event_timeline))
    ax.broken_barh([(x_start, bar_width)], (y_start, bar_height), facecolors=bar_colour, picker=True, label=legend_label)

  ax.set_xlabel('time (ns)')
  plt.savefig('./event_timeline.png')

  def hover(event):
    global prev_annotation
    label = event.artist.get_label()
    if prev_annotation is not None: # need to clear previous annotation or else they will stack
      prev_annotation.remove()

    prev_annotation = ax.annotate(label, xy=(event.mouseevent.xdata,event.mouseevent.ydata),xytext=((ax.get_xlim()[1] / 3) , ax.get_ylim()[1] - 0.5), arrowprops=dict(arrowstyle="->",color="black",lw=1))
    fig.canvas.draw()
  
  fig.canvas.mpl_connect('pick_event', hover)
  plt.show()


timeline = generate_stack_timeline('./trace.json')
plot_event_timeline(timeline)
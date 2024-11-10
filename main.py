import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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
  fig, ax = plt.subplots()

  bar_height = 1
  bar_vertical_space = 0.25

  renderer = fig.canvas.get_renderer()
  for event in event_timeline:
    y_start = event['depth'] * (bar_vertical_space + bar_height)
    x_start = event['start']
    bar_width =  event['duration']
    ax.broken_barh([(x_start, bar_width)], (y_start, bar_height), facecolors='tab:blue')
    text = ax.text(x_start + bar_width / 2, y_start + bar_height / 2, event['name'], ha='center', va='center', color='white')
    bounding_box = text.get_window_extent(renderer=renderer)
    text_width = ax.transData.inverted().transform((bounding_box.width, 0))[0] - ax.transData.inverted().transform((0, 0))[0]
    if bar_width < text_width:
      text.remove()

  ax.set_xlabel('time (ns)')
  plt.savefig('./event_timeline.png')

timeline = generate_stack_timeline('./trace.json')
plot_event_timeline(timeline)
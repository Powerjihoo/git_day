import random
import time

import matplotlib.pyplot as plt

plt.ion()  # Interactive mode on
fig, ax = plt.subplots()
x, y = [], []

# Initial plot
line, = ax.plot(x, y, 'bo-')
ax.set_xlim(0, 20)
ax.set_ylim(0, 1)

# Function to update plot
def update_plot():
    global x, y
    if len(x) < 20:
        x.append(len(x))
    else:
        x = [i for i in range(20)]
    
    y.append(random.random())
    
    # Keep only the last 20 items
    if len(y) > 20:
        y = y[-20:]
    
    line.set_xdata(x)
    line.set_ydata(y)
    ax.relim()  # Recompute limits
    ax.autoscale_view()  # Autoscale
    plt.draw()
    plt.pause(1)  # Pause for 1 second

# Main loop
while True:
    update_plot()

# Uncomment the next two lines if you want to save the animation
#import matplotlib
#matplotlib.use("Agg")

import numpy
from matplotlib.pylab import *
from mpl_toolkits.axes_grid1 import host_subplot
import matplotlib.animation as animation


# Sent for figure
font = {'size': 9}
matplotlib.rc('font', **font)

# Setup figure and subplots
f0 = figure(num = 0, figsize = (12, 8))#, dpi = 100)
f0.suptitle("Sensor plot", fontsize=12)
ax01 = subplot2grid((3, 1), (0, 0))
ax02 = subplot2grid((3, 1), (1, 0))
ax03 = subplot2grid((3, 1), (2, 0))
#tight_layout()

# Set titles of subplots
ax01.set_title('imu vs Time')
#ax02.set_title('imu_ay vs Time')
#ax03.set_title('imu_az vs Time')

# set y-limits
ax01.set_ylim(-10,10)
ax02.set_ylim(-10,10)
ax03.set_ylim(-10,10)

# sex x-limits
ax01.set_xlim(0,5.0)
ax02.set_xlim(0,5.0)
ax03.set_xlim(0,5.0)

# Turn on grids
ax01.grid(True)
ax02.grid(True)
ax03.grid(True)

# set label names
ax01.set_xlabel("time")
ax01.set_ylabel("ax")
ax02.set_xlabel("time")
ax02.set_ylabel("ay")
ax03.set_xlabel("time")
ax03.set_ylabel("az")

# Data Placeholders
ax=zeros(0)
ay=zeros(0)
az=zeros(0)
t=zeros(0)

# set plots
p011, = ax01.plot(t,ax,'b-', label="ax")
p021, = ax02.plot(t,ay,'b-', label="ay")
p031, = ax03.plot(t,az,'b-', label="az")

# set lagends
ax01.legend([p011], [p011.get_label()])
ax02.legend([p021], [p021.get_label()])
ax03.legend([p031], [p031.get_label()])

# Data Update
xmin = 0.0
xmax = 5.0
x = 0.0

def updateData(self):
    global x
    global ax
    global ay
    global az
    global t


    tmpp1 = 1 + exp(-x) *sin(2 * pi * x)
    tmpv1 = - exp(-x) * sin(2 * pi * x) + exp(-x) * cos(2 * pi * x) * 2 * pi
    ax=append(ax,tmpp1)
    ay=append(ay,tmpv1)
    az=append(az,0.5*tmpp1+tmpv1)
    #yv2=append(yv2,0.5*tmpv1)
    t=append(t,x)

    x += 0.05
    p011.set_data(t,ax)
    p021.set_data(t,ay)
    p031.set_data(t,az)

    if x >= xmax-1.00:
        p011.axes.set_xlim(x-xmax+1.0,x+1.0)
        p021.axes.set_xlim(x-xmax+1.0,x+1.0)
        p031.axes.set_xlim(x-xmax+1.0,x+1.0)
        #p032.axes.set_xlim(x-xmax+1.0,x+1.0)

    return p011, p021, p031

# interval: draw new frame every 'interval' ms
# frames: number of frames to draw
simulation = animation.FuncAnimation(f0, updateData, blit=False, frames=200, interval=20, repeat=False)

# Uncomment the next line if you want to save the animation
#simulation.save(filename='sim.mp4',fps=30,dpi=300)

plt.show()

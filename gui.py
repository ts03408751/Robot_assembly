from tkinter import *
from PIL import Image, ImageTk
import time
import matplotlib
matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import numpy as np


class StopWatch(Frame):
    """ Implements a stop watch frame widget. """

    def __init__(self, parent=None, **kw):
        Frame.__init__(self, parent, kw)
        self._start = 0.0
        self._elapsedtime = 0.0
        self._running = 0
        self.timestr = StringVar()
        self.makeWidgets()

    def makeWidgets(self):
        """ Make the time label. """
        l = Label(self, textvariable=self.timestr,bg='blue', font=('Arial',20))
        self._setTime(self._elapsedtime)
        l.pack(fill=X, expand=NO, pady=2, padx=2)

    def _update(self):
        """ Update the label with elapsed time. """
        self._elapsedtime = time.time() - self._start
        self._setTime(self._elapsedtime)
        self._timer = self.after(50, self._update)

    def _setTime(self, elap):
        """ Set the time string to Minutes:Seconds:Hundreths """
        minutes = int(elap / 60)
        seconds = int(elap - minutes * 60.0)
        hseconds = int((elap - minutes * 60.0 - seconds) * 100)
        self.timestr.set('%02d:%02d:%02d' % (minutes, seconds, hseconds))

    def Start(self):
        """ Start the stopwatch, ignore if running. """
        if not self._running:
            self._start = time.time() - self._elapsedtime
            self._update()
            self._running = 1

    def Stop(self):
        """ Stop the stopwatch, ignore if stopped. """
        if self._running:
            self.after_cancel(self._timer)
            self._elapsedtime = time.time() - self._start
            self._setTime(self._elapsedtime)
            self._running = 0

    def Reset(self):
        """ Reset the stopwatch. """
        self._start = time.time()
        self._elapsedtime = 0.0
        self._setTime(self._elapsedtime)

if __name__ == '__main__':
    window = Tk()
    sw = StopWatch(window)
    sw.pack(side='left')

    window.title('Robot Assembly Task')
    window.geometry('1024x768')
    window.resizable(False,False)
    bt1=Button(text="Start",command=sw.Start)
    bt2=Button(text="Stop", command=sw.Stop)
    bt3=Button(text="Reset", command=sw.Reset)
    bt1.pack(side='bottom')
    bt2.pack(side='bottom')
    bt3.pack(side='bottom')

    label=Label(text='Robot Assembly Task', font=('Arial', 30))
    label.pack(side='top')

    im=Image.open("images.jpeg")
    img=ImageTk.PhotoImage(im)
    imLabel=Label(window, image=img).place(x=500,y=100)

    f = Figure(figsize=(10,10))
    a = f.add_subplot(111)
    t = np.arange(0.0, 3, 0.01)
    s = np.sin(2 * np.pi * t)
    a.plot(t, s)

    canvas = FigureCanvasTkAgg(f, master=window)
    #canvas.show()
    canvas.get_tk_widget().pack(side='top', fill=X, expand=1)
    # 把matplotlib绘制图形的导航工具栏显示到tkinter窗口上
    #toolbar = NavigationToolbar2TkAgg(canvas, window)
    #toolbar.update()
    canvas._tkcanvas.pack(side='top', fill=X, expand=1)

    window.mainloop()


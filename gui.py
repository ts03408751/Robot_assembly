import matplotlib
matplotlib.use('TkAgg')
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from timer import StopWatch
import os
from client import *
from Tkinter import *
import pandas as pd
import platform
from PIL import Image, ImageTk
import sys
import matplotlib.pyplot as plt
from sklearn.externals import joblib
from sklearn import preprocessing
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import timedelta
from glob import glob
import paramiko

def predict_data(data, window_size):
    n_label = 7
    # model = joblib.load('svm_classification.model')
    model = joblib.load('decisionTree.model')

    data_roll = data_roll = data.iloc[:, data.columns.get_loc('video_aboutTime') + 1:].rolling(
        window=window_size).mean()
    data_roll = data_roll[window_size - 1:]
    data.loc[window_size - 1:, 'label'] = model.predict(data_roll.values)
    print ('data_size:', len(data_roll))

    return data.iloc[window_size-1:]

def pre_processing_sig(data):
    for i in range(data.columns.get_loc('imu_temp'),len(data.columns)):
        data.iloc[:,i] = preprocessing.scale(data.iloc[:,i].values)

    from datetime import timedelta

    data.timestamp = pd.to_datetime(data.timestamp, unit='s')
    data.timestamp = data.timestamp.dt.tz_localize('UTC').dt.tz_convert('Asia/Taipei')

    #data.wall_time= pd.to_datetime(data.wall_time, format='%Y-%m-%d %H:%M:%S')
    data.wall_time= pd.to_datetime(data.wall_time, format='%Y-%m-%d_%f')

    data.loc[:, 'time_difference'] = data.wall_time-data.wall_time[0]

    data.loc[:, 'video_aboutTime'] = data.time_difference + timedelta(minutes=0, seconds=0)
    data.video_aboutTime = pd.to_datetime(data.video_aboutTime).dt.strftime('%M:%S')
    data = data[['key', 'timestamp', 'wall_time', 'time_difference',
       'video_aboutTime', 'imu_temp', 'imu_ax', 'imu_ay',
       'imu_az', 'imu_gx', 'imu_gy', 'imu_gz', 'msu_ax', 'msu_ay',
       'msu_az', 'baro_temp', 'baro']]
    return data


def plot_sig_by_videoTime_label(LorR, start_time, end_time, data=None):
    if LorR == 'L':
        data = pd.read_csv('20180926_basic_movement_Chi-Lan_IMU_labeled_left.csv')
    elif LorR == 'R':
        data = pd.read_csv('20180926_basic_movement_Chi-Lan_IMU_labeled_right.csv')
    elif LorR == 'All':
        data = data[:]
        data.rename(columns={'predict': 'label'}, inplace=True)
    data_part = data[(data.video_aboutTime >= start_time) & (data.video_aboutTime <= end_time)]
    data_setIndex = data_part.set_index('key')
    colors = ['gray', 'b', 'g', 'r', 'c', 'm', 'y', 'orange', 'fuchsia']
    labels = ['0. No nabel',
              '1.Spin by hand',
              '2. Remove with screws',
              '3. Screw with screws',
              '4. Rotate the object with both hands',
              '5. Pick up the object with one hand',
              '6. Put the screws up',
              '7. Put the screws sideways',
              '8. Weird!']
    for i in range(data_setIndex.columns.get_loc('video_aboutTime') + 2, data_setIndex.columns.get_loc('baro') + 1):
        fig = plt.figure(figsize=(7.5, 1.5))
        ax1 = plt.subplot(1, 1, 1)
        plt.title(data_setIndex.columns[i])
        ax1.locator_params(nbins=20, axis='x')

        for j in range(0, 8 + 1):
            if j == 0:
                ax1.plot(data_setIndex.iloc[:, i], marker='.', color=colors[j], label=labels[j])
            else:
                data_setIndex_L = data_setIndex[data_setIndex.label == j]  # <-
                labeled_data_L_G = data_setIndex_L.groupby(
                    data_setIndex_L.index.to_series().diff().ne(1).cumsum()).groups  # <-
                if len(labeled_data_L_G) == 0:
                    ax1.plot(data_setIndex_L.iloc[:, i], marker='.', color=colors[j], label=labels[j])
                else:
                    for k, group in labeled_data_L_G.iteritems():  # <-
                        if k == 1:
                            ax1.plot(data_setIndex_L.loc[group].iloc[:, i], marker='.', color=colors[j],
                                     label=labels[j])  # data_setIndex[data_setIndex['label']==j].iloc[:,i],
                        else:
                            ax1.plot(data_setIndex_L.loc[group].iloc[:, i], marker='.', color=colors[j], label='')
                            # data_setIndex[data_setIndex['label']==j].iloc[:,i],

        # Set scond x-axis
        ax2 = ax1.twiny()
        x_stick_data = data_part.groupby('video_aboutTime').first()['key']
        D_x_stick = [(len(x_stick_data) / 19) if (len(x_stick_data) / 19) != 0 else 1][0]
        ax2_values = x_stick_data[::D_x_stick]

        ### set same xlim(x_board), ax2 xlim not from 0 to len(data)
        ax2.set_xlim(ax1.get_xlim())
        ax2.set_xticks(ax2_values)
        ax2.set_xticklabels(ax2_values.index)

        ax2.xaxis.set_ticks_position('bottom')  # set the position of the second x-axis to bottom
        ax2.xaxis.set_label_position('bottom')  # set the position of the second x-axis to bottom
        ax2.spines['bottom'].set_position(('outward', 36))
        # ax2.locator_params(nbins=30, axis='x')

        ax1.legend()
        return fig
        #plt.savefig('result2.png')
        #plt.show()

        # canvas = FigureCanvasTkAgg(fig, master=root)
        # canvas.show()
def judge_LorR(data_lef, data_rig):
    data_lef.loc[:, 'LorR'] = 'L'
    data_rig.loc[:, 'LorR'] = 'R'
    data_all = pd.concat([data_lef, data_rig])

    count_L = 0
    count_R = 0

    for i in range(6,len(data_all.columns[:-2])):
        tmp_data_L = data_all[data_all.LorR=='L'].groupby('video_aboutTime').apply(
                        lambda x: abs(x.iloc[:, i]-x.iloc[:, i].mean())).mean()
        tmp_data_R = data_all[(data_all.LorR=='R')].groupby('video_aboutTime').apply(
                        lambda x: abs(x.iloc[:, i]-x.iloc[:, i].mean())).mean()

        if np.abs(tmp_data_L) > np.abs(tmp_data_R):
            count_L = count_L + 1
            #print data_all.columns[i],'L'
        else:
            count_R = count_R + 1
            #print data_all.columns[i],'R'

    if count_L > count_R:
        return 'L'
    else:
        return 'R'


def averageTime_eachActions(data):
    time_motions = {i: timedelta(0) for i in range(1, 7 + 1)}
    for label_i in range(1, 7 + 1):
        tmp = timedelta(0)
        labeled_data = data[data.label == label_i]
        labeled_data.video_aboutTime = pd.to_datetime(labeled_data.video_aboutTime, format='%M:%S')
        labeled_data_G = labeled_data.groupby(labeled_data.index.to_series().diff().ne(1).cumsum()).groups
        for group in labeled_data_G.itervalues():
            time_motions[label_i] = time_motions[label_i] + abs(
                labeled_data.loc[group[0], 'video_aboutTime'] - labeled_data.loc[group[-1], 'video_aboutTime'])
        if time_motions[label_i]==timedelta(0):
            time_motions[label_i] = time_motions[label_i]
        else:
            time_motions[label_i] = time_motions[label_i] / float(len(labeled_data_G))
        # print 'label:',label_i, time_motions[label_i]

    return time_motions


def print_user_averageTime(time_motions):
    labels=['0. No nabel',
        '1. Spin by hand',
        '2. Remove with screws',
        '3. Screw with screws',
        '4. Rotate the object with both hands',
        '5. Pick up the object with one hand',
        '6. Put the screws up',
        '7. Put the screws sideways',
        '8. Weird!']

    for label_i in range(1,7+1):
        print ' %s: %.2f s' %(labels[label_i],time_motions[label_i].total_seconds())


def bar_eachActions(user_time):
    n_groups = 7
    fig, ax = plt.subplots()
    mastr_time = [5.133333333,
                  3.0,
                  4.9,
                  3.555555555,
                  1.186046511,
                  3.736842105,
                  4.6000000000000005]

    index = np.arange(n_groups)
    bar_width = 0.35

    opacity = 0.4
    error_config = {'ecolor': '0.3'}

    rects1 = ax.bar(index, user_time, bar_width,
                    alpha=opacity,
                    color='b',
                    # yerr=std_men,
                    #error_kw=error_config,
                    label='User')

    rects2 = ax.bar(index + bar_width, mastr_time, bar_width,
                    alpha=opacity,
                    color='r',
                    # yerr=std_women,
                    error_kw=error_config,
                    label='Master')
    ax.set_xlabel('Actions')
    ax.set_ylabel('Seconds')
    ax.set_title('Avarage time each actins')
    # ax.set_xticks(index + bar_width / 2, index+1)
    ax.legend()

    # ax.tight_layout()




    return fig


class GUI(Tk):
    def __init__(self, master=None):
        Tk.__init__(self, master)
        self.title('Robot Assembly Tutorial')
        self.geometry('800x600')
        self.resizable(width=False, height=False)
        self._time = ''
        self._client=RobotClient()
        self.__init_window()
        self.switch_screen('_StartScreen')

    def __init_window(self):
        container = Frame(self)
        container.pack(side='top', fill='both', expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._screens = {}
        for scr in [_StartScreen, _RunScreen, _LoadScreen]:
            scr_name = scr.__name__
            screen = scr(parent=container, controller=self)
            screen.grid(row=0, column=0, sticky="nsew")
            self._screens[scr_name] = screen

    def switch_screen(self, scr_name):
        screen = self._screens[scr_name]
        screen.tkraise()
    @property
    def client(self):
        return self._client
class _StartScreen(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self._controller = controller
        self._buttons = {}
        self._images = {}
        self._labels = {}
        self.__init_screen()

    def __init_screen(self):
        self.__create_title()
        self.__create_image()
        self.__create_buttons()

    def __create_title(self):
        self._labels['title'] = Label(self, text='Robot Assembly Task', font=('Arial', 30))
        self._labels['title'].pack(side='top')

    def __create_buttons(self):
        global start_img
        img = Image.open('pic/start.png')
        img = img.resize((100, 100), Image.ANTIALIAS)
        start_img = ImageTk.PhotoImage(img)

        self._buttons['start'] = Button(self, image=start_img, text='start')
        self._buttons['start'].bind('<Button-1>', self.__click_start_button)
        self._buttons['start'].pack(side='top')

    def __click_start_button(self, e):
        self._controller.switch_screen('_RunScreen')

    def __create_image(self):
        img_open = Image.open('pic/robot.jpg')
        global img_png
        img_png = ImageTk.PhotoImage(img_open)
        self._images['robot'] = Label(self, image=img_png)
        self._images['robot'].pack(side='top')

class _RunScreen(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self._controller = controller
        self._buttons = {}
        self._labels = {}
        self._images = {}
        self.elap = 0
        self.__init_screen()

    def __init_screen(self):
        self.__create_image()
        self.__create_buttons()
        self.sw=StopWatch(self)
        self.sw.pack(side='bottom')

    def __create_image(self):
        global img_png1, img_pract
        img1 = Image.open('pic/word1.png')
        img_png1 = ImageTk.PhotoImage(img1)
        img_pract = Image.open('pic/pract1.png')
        img_pract = img_pract.resize((800, 300), Image.ANTIALIAS)
        img_pract = ImageTk.PhotoImage(img_pract)
        self._images['wd'] = Label(self, image=img_png1)
        self._images['wd'].place(x=0,y=0)
        self._images['pract'] = Label(self, image=img_pract)
        self._images['pract'].place(x=0,y=120)

    def __create_buttons(self):
        global start_btn, done_btn
        img = Image.open('pic/start_btn.png')
        start_btn = ImageTk.PhotoImage(img)
        img2 = Image.open('pic/done.png')
        done_btn = ImageTk.PhotoImage(img2)
        self._buttons['start'] = Button(self, image=start_btn, text='start')
        self._buttons['start'].bind('<Button-1>', self.__click_start_button)
        self._buttons['start'].place(x=20,y=450)

        self._buttons['done'] = Button(self, image=done_btn, text='done')
        self._buttons['done'].bind('<Button-1>', self.__click_done_button)
        self._buttons['done'].place(x=420,y=450)

    def  __click_start_button(self, e):
        self.sw.Start()

    def __click_done_button(self, e):
        self.elap = self.sw.Stop()

        self._controller.switch_screen('_LoadScreen')
        time = self.sw._getTime(self.elap)
        print time


    def _getelap(self):
        return self.elap
class _LoadScreen(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)
        self._controller = controller
        self._buttons = {}
        self._labels = {}
        self._images = {}
        self._canvas = {}
        self._filename = self._controller._client._local_sensor_filename
        self.__init_screen()
        self._pred_data_r = None

    def __init_screen(self):
        self.__create_buttons()
        self._labels['down']=Label(self, text='Downloading...& \nShow Result', font=('Arial', 20))
        self._labels['down'].place(x=500,y=300)
        #self.__show_result()


    def __create_buttons(self):
        global show_btn
        img = Image.open('pic/download.png')
        show_btn = ImageTk.PhotoImage(img)
        self._buttons['start'] = Button(self, image=show_btn, text='download')
        self._buttons['start'].bind('<Button-1>', self.__download)
        self._buttons['start'].place(x=500,y=350)

    def __show_result(self):
        items = os.listdir('sensor_data')
        csv_items = list(filter(lambda name: name[-4:] == '.csv', items))
        filename = max(csv_items)
        print filename
        sensor_df = pd.read_csv('sensor_data/' + filename)
        #print sensor_df
        data_r = pre_processing_sig(sensor_df)
        self._pred_data_r = predict_data(data_r,15)
        filename_list = filename.split('.')
        self._pred_data_r.to_csv('sensor_data/'+filename_list[0]+'_pred.'+filename_list[-1])

    def  __download(self, e):

        # ssh = paramiko.SSHClient()
        # ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # ssh.connect('192.168.1.4', username='', password='')
        # sftp = ssh.open_sftp()
        # remote_items = sftp.listdir('robot/data_collection')
        # csv_items = list(filter(lambda name: name[-4:] == '.csv', remote_items))
        # remote_filename = max(csv_items)
        #
        # sftp.get(remote_filename, 'sensor_data/'+remote_filename)

        self.__show_result()

        fig = plot_sig_by_videoTime_label('All', '00:00', '50:00', data=self._pred_data_r)
        self._canvas['line'] = FigureCanvasTkAgg(fig, master=self)
        self._canvas['line'].show()
        self._canvas['line'].get_tk_widget().place(x=0,y=0, width=800, height=300)
        #self._canvas['line'].get_tk_widget().place(x=0,y=0)

        #img = Image.open('pic/download.png')
        #show_btn = ImageTk.PhotoImage(img)

        # user_time = averageTime_eachActions(self._pred_data_r)
        # print_user_averageTime(user_time)
        # fig2 = bar_eachActions(user_time)
        # self._canvas['bar'] = FigureCanvasTkAgg(fig2, master=self)
        # self._canvas['bar'].show()
        # self._canvas['bar'].get_tk_widget().place(x=400, y=0)


if __name__ == '__main__':
    window = GUI()
    window.mainloop()

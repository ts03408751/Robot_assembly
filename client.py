import pandas as pd
import platform
import paramiko
import threading
import subprocess
import sys
import os
import posixpath
import logging
import re
from glob import glob


# execute command
REMOTE_BASE_PATH = 'robot/'
BASE_PATH = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')
LOCAL_SENSOR_PATH = posixpath.join(BASE_PATH, 'sensor_data/')
LINUX_BB_COMMAND = "cd %s; python bbblue_acq -v -c;" % REMOTE_BASE_PATH
LINUX_KILL_COMMAND = "pkill -f python;"
SSH_CONFIG_PATH = posixpath.join(BASE_PATH, 'connect_host/')


class _Client(object):

    def __init__(self):
        self._local_sensor_filename = ''
        self._taiko_ssh = {}
        self._ip_addr = '127.0.0.1'
        self._port = {}


    def _record_sensor(self, host_ip_, username_, pwd_, command_, label_):
        print('_Client _record_sensor() =>', threading.current_thread())
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host_ip_, username=username_, password=pwd_)
            ssh.exec_command(command_)

            sys.stdout.write('connect %s ok\n' % host_ip_)
            sys.stdout.flush()

        except Exception as ee:
            sys.stderr.write("SSH connection error: {0}\n".format(ee))
            sys.stderr.flush()

    def _stop_sensor(self, host_ip_, username_, pwd_, command_, label_):
        logging.debug('_Client _stop_sensor() => %s' % threading.current_thread())
        try:
            taiko_ssh = self._taiko_ssh.pop(label_, None)
            if taiko_ssh is not None:
                taiko_ssh.close()
                sys.stdout.write('stop %s ok\n' % taiko_ssh.ip_addr)
                sys.stdout.flush()

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host_ip_, username=username_, password=pwd_)
            ssh.exec_command(command_)
            ssh.close()

            sys.stdout.write('kill %s ok\n' % host_ip_)
            sys.stdout.flush()

        except Exception as e:
            sys.stderr.write('SSH connection error: %s\n' % str(e))
            sys.stderr.flush()

    def _download_sensor(self, host_ip_, username_, pwd_, prefix_):
        logging.debug('_Client _download_sensor() => %s' % threading.current_thread())
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host_ip_, username=username_, password=pwd_)
            sftp = ssh.open_sftp()

            remote_items = sftp.listdir(REMOTE_BASE_PATH + 'data_collection')
            csv_items = list(filter(lambda name: name[-4:] == '.csv', remote_items))
            remote_filename = max(csv_items)

            remote_file = posixpath.join(REMOTE_BASE_PATH + 'data_collection', remote_filename)
            local_file = posixpath.join(LOCAL_SENSOR_PATH, remote_filename)

            sys.stdout.write('Reading from %s ...\n' % host_ip_)
            sys.stdout.flush()

            sftp.get(remote_file, local_file)
            self._local_sensor_filename = remote_filename

            sys.stdout.write('Reading %s done.\n' % host_ip_)
            sys.stdout.flush()

            sftp.close()
            ssh.close()

        except Exception as ee:
            sys.stderr.write("SSH connection error: {0}\n".format(ee))
            sys.stderr.flush()


class RobotClient(_Client):

    def __init__(self):
        super(RobotClient, self).__init__()
        self._capture_thread = None
        self._taiko_ssh_thread = []
        self._song_id = None
        self._drummer_name = None

    def clear(self):
        self.stop_sensor()
        self.stop_screenshot()
        self.clear_tmp_dir_png()
        self._progress = {
            'maximum': 100,
            'value': 0,
        }
        self._progress_tips = ''

    def record_sensor(self):
        logging.debug('TaikoClient record_sensor() => %s' % threading.current_thread())
        sensor_settings = glob(posixpath.join(SSH_CONFIG_PATH, '*.bb'))

        threads = []
        for file_path in sensor_settings:
            res = re.search('(\d){,3}.(\d){,3}.(\d){,3}.(\d){,3}.bb', file_path)
            filename = res.group(0)

            host_ip = filename[:-3]
            try:
                with open(file_path, 'r') as f:
                    username = f.readline()[:-1]
                    pwd = f.readline()[:-1]
                    label = f.readline()[:-1]
                    command = LINUX_BB_COMMAND
                    thread = threading.Thread(target=self._record_sensor,
                                              args=(host_ip, username, pwd, command, label))
                    thread.start()
                    threads.append(thread)

                    f.close()

            except Exception as e:
                sys.stderr.write('error: %s\n' % str(e))
                sys.stderr.flush()

        for thread in threads:
            thread.join()

        for _, taiko_ssh in self._taiko_ssh.items():
            thread = threading.Thread(target=taiko_ssh.start)
            thread.start()
            self._taiko_ssh_thread.append(thread)

    def query_sensor(self, label):
        try:
            taiko_ssh = self._taiko_ssh[label]
            window_df = taiko_ssh.get_window_df()
            return window_df

        except KeyError:
            return None

    def stop_sensor(self):
        logging.debug('TaikoClient stop_sensor() => %s' % threading.current_thread())
        sensor_settings = glob(posixpath.join(SSH_CONFIG_PATH, '*.bb'))

        threads = []
        for file_path in sensor_settings:
            res = re.search('(\d){,3}.(\d){,3}.(\d){,3}.(\d){,3}.bb', file_path)
            filename = res.group(0)

            host_ip = filename[:-3]
            try:
                with open(file_path, 'r') as f:
                    username = f.readline()[:-1]
                    pwd = f.readline()[:-1]
                    label = f.readline()[:-1]
                    command = LINUX_KILL_COMMAND
                    thread = threading.Thread(target=self._stop_sensor,
                                              args=(host_ip, username, pwd, command, label))
                    thread.start()
                    threads.append(thread)
                    f.close()

            except Exception as e:
                sys.stderr.write('error: %s\n' % str(e))
                sys.stderr.flush()

        for thread in threads:
            thread.join()
            logging.debug('TaikoClient join() stop_sensor() => %s' % thread)

    def download_sensor(self):
        logging.debug('TaikoClient download_sensor() => %s' % threading.current_thread())
        sensor_settings = glob(posixpath.join(SSH_CONFIG_PATH, '*.bb'))

        #self._progress_tips = 'Downloading raw data from sensors ...'
        # threads = []
        for file_path in sensor_settings:
            res = re.search('(\d){,3}.(\d){,3}.(\d){,3}.(\d){,3}.bb', file_path)
            filename = res.group(0)

            host_ip = filename[:-3]
            try:
                threads = []
                with open(file_path, 'r') as f:
                    username = f.readline()[:-1]
                    pwd = f.readline()[:-1]
                    _prefix = f.readline()[:-1]

                    self._download_sensor(host_ip, username, pwd, _prefix)


            except Exception as e:
                sys.stderr.write('error: %s\n' % str(e))
                sys.stderr.flush()


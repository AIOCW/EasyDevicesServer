import threading
from datetime import time

from tools.file_tools import composite_file
from tools.md5 import getmd5


class file_deal_thread(threading.Thread):
    def __init__(self, threadname, send_task, json_data):
        self.send_task = send_task
        self.json_data = json_data
        threading.Thread.__init__(self, name='线程' + threadname)

    def run(self):
        filename = self.json_data['filename']
        filesize = self.json_data['filesize']
        filepath = self.json_data['filepath']
        aim_device = self.json_data['aim_device']
        md5 = self.json_data['md5']
        composite_file("file/temp_lite/", "file/JustSave/" + filename)
        if md5 == getmd5("file/JustSave/" + filename):
            print("大文件接收成功")
            self.send_task.append([9110040, True])
        else:
            self.send_task.append([9110040, False])
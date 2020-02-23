import os
import struct
import json

from tools.net_tools import unpackage_data_2_security, package_data_2_security, byte2data, data2byte
from tools.md5 import getmd5

buffsize = 1024

def operafile(filename):
    '''对报头进行打包'''
    filesize_bytes = os.path.getsize(filename)
    head_dir = {
        'filename': filename,
        'filesize_bytes': filesize_bytes
    }
    head_info = json.dumps(head_dir)
    head_info_len = struct.pack('i', len(head_info))
    print(len(head_info))
    return head_info_len, head_info

def file_save_option(json_data, tcp_link):
    filename = json_data['filename']
    filesize = json_data['filesize']
    filepath = json_data['filepath']
    aim_device = json_data['aim_device']
    md5 = json_data['md5']

    print(filesize)
    recv_len = 0
    if aim_device == 'just-save':
        with open(filepath + filename, 'wb') as f:
            while recv_len < filesize:
                if filesize - recv_len > buffsize:
                    recv_mesg = tcp_link.recv(buffsize)
                    recv_mesg = unpackage_data_2_security(recv_mesg)
                    recv_len += len(recv_mesg)
                    f.write(recv_mesg)
                else:
                    recv_mesg = tcp_link.recv(filesize - recv_len)
                    recv_mesg = unpackage_data_2_security(recv_mesg)
                    recv_len += len(recv_mesg)
                    f.write(recv_mesg)
            print(recv_len)

        getmd5(filepath + filename)

        print('文件存储传输完成')


def file_send_option(one_task, save_device_link):
    # [1100, "start", json_data_len_buffer, json_data_buffer]
    json_data_len_buffer = one_task[2]
    json_data_buffer = one_task[3]

    # 接受客户端介绍信息的长度。
    confirm_code_buffer = save_device_link.recv(4)
    confirm_code_buffer_unpackage = unpackage_data_2_security(confirm_code_buffer)
    confirm_code = byte2data(confirm_code_buffer_unpackage)
    if confirm_code == 91100:
        save_device_link.send(json_data_len_buffer)
        save_device_link.send(json_data_buffer)
    else:
        print("error")


def composite_file(temp_file_path, file_path):
    with open(file_path, 'wb') as save_file:
        for root, dir, files in os.walk(temp_file_path):
            for file in files:
                with open(root + file, 'rb') as file_read:
                    save_file.write(file_read.read())
                os.remove(root + file)
    pass



if __name__ == "__main__":
    composite_file("../file/temp_lite/", "../file/test.zip")
    getmd5("../file/test.zip")
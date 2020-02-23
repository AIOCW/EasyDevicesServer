#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 18-5-21 下午8:04
# @Author  : Yaque
# @File    : server_socket_文件_服务端.py
# @Software: PyCharm

import socketserver
import time
import json
from socket import socket
import traceback

from entity.client import Client

from tools.net_tools import unpackage_data_2_security, package_data_2_security, byte2data, data2byte

from tools.file_tools import file_send_option, file_save_option

from tools.md5 import getmd5

from static_data import INT_DATA_RECV_LEN

from file_deal_thread import file_deal_thread


client_list = []
split_file_counter = []
buffsize = 1024


class MyServer(socketserver.BaseRequestHandler):

    def handle(self):
        print('连接人的信息: conn是{}, addr是{}, port是{}'.format(self.request,  self.client_address[0], self.client_address[1]))
        try:
            while True:
                receive_order_buffer = self.request.recv(4)
                receive_order_buffer_unpackage = unpackage_data_2_security(receive_order_buffer)
                order = -1
                try:
                    order = byte2data(receive_order_buffer_unpackage)
                except :
                    pass
                    # print("可能是这个错误unpack requires a buffer of 4 bytes")

                if order == 1000:

                    # 接受客户端介绍信息的长度
                    json_data_len_buffer = self.request.recv(4)
                    json_data_len_buffer = unpackage_data_2_security(json_data_len_buffer)
                    json_data_len = byte2data(json_data_len_buffer)

                    # 接受介绍信息的内容
                    json_data_buffer = self.request.recv(json_data_len)
                    json_data_buffer = unpackage_data_2_security(json_data_buffer)
                    # 将介绍信息的内容反序列化
                    json_data = json.loads(json_data_buffer.decode('utf-8'))
                    print("本次介绍信息的内容为：{}".format(json_data))
                    client = Client()
                    client.ip = self.client_address[0]
                    client.port = self.client_address[1]
                    client.is_online = True
                    client.server_thread = self

                    self.client_name = json_data["client_name"]
                    client.name = self.client_name

                    client_flag = True
                    for i, one_client in enumerate(client_list):
                            if one_client.ip == client.ip:
                                client_flag = False
                                client_list.remove(one_client)
                                print("error port {} error name {}".format(one_client.port, one_client.name))
                                one_client.server_thread.request.close()
                                print("close old client")
                                client_list.append(client)
                    if client_flag:
                        client_list.append(client)
                    print("当前客户链接数量为：{} ".format(len(client_list)))

                    send_data = data2byte(1000)
                    send_data = package_data_2_security(send_data)

                    self.request.send(send_data)

                elif order == 1010:
                    # 心跳包
                    print("port {} ===接收心跳包 {} now device {}".format(self.client_address[1], self.client_name, [device.name for device in client_list]))
                    if len(self.send_task) > 0 :
                        one_task = self.send_task[0]
                        if one_task[0] == 1011:
                            self.send_task.remove(one_task)
                            send_data = data2byte(91011)
                            send_data = package_data_2_security(send_data)

                            self.request.send(send_data)
                            self.request.send(one_task[1])
                            self.request.send(one_task[2])
                            self.request.send(one_task[3])
                        elif one_task[0] == 1100:
                            self.send_task.remove(one_task)
                            if one_task[1] == 'start':
                                send_data = data2byte(91100)
                                send_data = package_data_2_security(send_data)
                                self.request.send(send_data)
                                file_send_option(one_task, self.request)
                                while True:
                                    if len(self.send_task) > 0:
                                        data_task = self.send_task.pop(0)
                                        if data_task[1] == 'data':
                                            self.request.send(data_task[2])
                                            if byte2data(unpackage_data_2_security(self.request.recv(4))) == 91100:
                                                continue
                                            else:
                                                time.sleep(0.005)
                                                self.request.send(data_task[2])
                                        elif data_task[1] == 'end':
                                            print('文件传输完成')
                                            break;
                        elif one_task[0] == 110040:
                            if len(split_file_counter) == 5:
                                self.send_task.remove(one_task)
                                file_deal_thread(str("file_deal"), self.send_task, one_task[1]).start()
                                split_file_counter.clear()
                            send_data = data2byte(1010)
                            send_data = package_data_2_security(send_data)
                            self.request.send(send_data)
                        elif one_task[0] == 9110040:
                            self.send_task.remove(one_task)
                            if one_task[1]:
                                self.request.send(package_data_2_security(data2byte(9110040)))
                                print("大文件接收成功")
                            else:
                                self.request.send(package_data_2_security(data2byte(7110040)))
                                print("大文件接收失败")
                        elif one_task[0] == 110041:
                            self.send_task.remove(one_task)
                            send_data = data2byte(110041)
                            send_data = package_data_2_security(send_data)

                            self.request.send(send_data)
                            self.request.send(one_task[1])
                            self.request.send(one_task[2])
                            self.request.send(one_task[3])
                    else:

                        send_data = data2byte(1010)
                        send_data = package_data_2_security(send_data)

                        self.request.send(send_data)

                elif order == 1001:
                    # 客户端要求返回服务器目前所有连接
                    send_data = data2byte(1001)
                    send_data = package_data_2_security(send_data)

                    self.request.send(send_data)
                    print("客户端要求返回服务器目前所有连接的客户机名称".format(self.client_name, self.client_address[0]))

                    send_message = '{"name":"just-save", "ip":"192.168.100.14", "port":8080}'
                    message_list = []
                    message_list.append(send_message)
                    for one_client in client_list:
                        print(one_client.name)
                        if one_client.name == self.client_name:
                            continue
                        elif one_client.is_online:
                            send_message = '{'+'"name":"{}", "ip":"{}", "port":{}'.format(one_client.name, one_client.ip, one_client.port)+'}'
                            message_list.append(send_message)

                    send_message_buffer = str(message_list).encode('utf-8')
                    send_message_buffer = package_data_2_security(send_message_buffer)

                    send_message_len_buffer = data2byte(len(send_message_buffer))
                    send_message_len_buffer = package_data_2_security(send_message_len_buffer)
                    self.request.send(send_message_len_buffer)

                    self.request.send(send_message_buffer)

                    # ok
                    flag_code_buffer = self.request.recv(INT_DATA_RECV_LEN)
                    flag_code_buffer = unpackage_data_2_security(flag_code_buffer)
                    flag_code = byte2data(flag_code_buffer)

                # text
                if order == 1011:

                    # 接受客户端介绍信息的长度
                    json_data_len_buffer = self.request.recv(4)
                    json_data_len_buffer_unpackage = unpackage_data_2_security(json_data_len_buffer)
                    json_data_len = byte2data(json_data_len_buffer_unpackage)

                    # 接受介绍信息的内容
                    json_data_buffer = self.request.recv(json_data_len)
                    json_data_buffer_unpackage = unpackage_data_2_security(json_data_buffer)
                    # 将介绍信息的内容反序列化
                    json_data = json.loads(json_data_buffer_unpackage.decode('utf-8'))
                    print("本次介绍信息的内容为：{}".format(json_data))

                    if json_data['client_name'] == 'all':
                        for one_client in client_list:
                            print("send object {}".format(one_client.name))
                            one_client.server_thread.send_task.append(
                                [1011, receive_order_buffer, json_data_len_buffer, json_data_buffer])
                            # client_dict[key].request.send(receive_order_buffer)
                            # client_dict[key].request.send(json_data_len_buffer)
                            # client_dict[key].request.send(json_data_buffer)
                    else:
                        for one_client in client_list:
                            if one_client.name == json_data['client_name']:
                                print("send object {}".format(one_client.name))
                                one_client.server_thread.send_task.append(
                                    [1011, receive_order_buffer, json_data_len_buffer, json_data_buffer])
                                # client_dict[key].request.send(receive_order_buffer)
                                # client_dict[key].request.send(json_data_len_buffer)
                                # client_dict[key].request.send(json_data_buffer)

                    self.request.send(receive_order_buffer)

                # 小于2M的文件接收入口
                elif order == 1100:
                    print("进入文件操作")
                    confirm_code = package_data_2_security(data2byte(91100))
                    self.request.send(confirm_code)

                    # 接受客户端介绍信息的长度
                    json_data_len_buffer = self.request.recv(4)
                    json_data_len_buffer_unpackage = unpackage_data_2_security(json_data_len_buffer)
                    json_data_len = byte2data(json_data_len_buffer_unpackage)

                    # 接受介绍信息的内容
                    json_data_buffer = self.request.recv(json_data_len)
                    json_data_buffer_unpackage = unpackage_data_2_security(json_data_buffer)
                    # 将介绍信息的内容反序列化
                    json_data = json.loads(json_data_buffer_unpackage.decode('utf-8'))
                    print("本次介绍信息的内容为：{}".format(json_data))
                    print("本次file长度为：{}".format(json_data["filesize"]))

                    if json_data['aim_device'] == 'just-save':
                        recv_len = 0
                        filename = json_data['filename']
                        filesize = json_data['filesize']
                        filepath = json_data['filepath']
                        aim_device = json_data['aim_device']
                        md5 = json_data['md5']
                        with open("file/JustSave/" + filename, 'wb') as f:
                            now_data_number = 0;
                            while recv_len < filesize:
                                package_data_buffer = self.request.recv(1028)
                                package_data_buffer_un = unpackage_data_2_security(package_data_buffer)
                                # print("Data Length {}".format(len(package_data_buffer_un)))
                                if len(package_data_buffer_un) == 1028:
                                    file_buffer = package_data_buffer_un[0:1024]
                                    data_number = byte2data(package_data_buffer_un[1024:1028])
                                    # print("Now Data Number {}, Data Number {}, ".format(now_data_number, data_number))
                                    if now_data_number == data_number:
                                        if filesize - recv_len > buffsize:
                                            recv_len += len(file_buffer)
                                            f.write(file_buffer)
                                        else:
                                            end_size = filesize - recv_len
                                            recv_len += end_size
                                            f.write(file_buffer[0:end_size])
                                        self.request.send(package_data_2_security(data2byte(91100)))
                                        now_data_number += 1
                                    else:
                                        continue
                                else:
                                    continue
                        new_file_md5 = getmd5("file/JustSave/" + filename)
                        if new_file_md5 == md5:
                            print("new_file_md5 {}, md5 {}".format(new_file_md5, md5))
                            print("文件接收成功")
                    else:
                        for one_client in client_list:
                            if one_client.name == json_data['aim_device']:
                                print("send object {}".format(one_client.name))
                                one_client.server_thread.send_task.append(
                                    [1100, "start", json_data_len_buffer, json_data_buffer])
                                recv_len = 0
                                filename = json_data['filename']
                                filesize = json_data['filesize']
                                filepath = json_data['filepath']
                                aim_device = json_data['aim_device']
                                md5 = json_data['md5']
                                with open("file/Temp/" + filename, 'wb') as f:
                                    now_data_number = 0;
                                    while recv_len < filesize:
                                        package_data_buffer = self.request.recv(1028)
                                        package_data_buffer_un = unpackage_data_2_security(package_data_buffer)
                                        file_buffer = package_data_buffer_un[0:1024]
                                        data_number = byte2data(package_data_buffer_un[1024:1028])

                                        if now_data_number == data_number:
                                            if filesize - recv_len > buffsize:
                                                recv_len += len(file_buffer)
                                                one_client.server_thread.send_task.append(
                                                    [1100, "data", package_data_buffer])
                                                f.write(file_buffer)
                                            else:
                                                end_size = filesize - recv_len
                                                recv_len += end_size
                                                one_client.server_thread.send_task.append(
                                                    [1100, "data", package_data_buffer])
                                                f.write(file_buffer[0:end_size])
                                            self.request.send(package_data_2_security(data2byte(91100)))
                                            now_data_number += 1
                                        else:
                                            continue

                                one_client.server_thread.send_task.append(
                                        [1100, "end"])


                    confirm_code = package_data_2_security(data2byte(91100))
                    self.request.send(confirm_code)

                # 分片文件的接收入口
                elif order == 11000:
                    print("进入文件操作")
                    confirm_code = package_data_2_security(data2byte(911000))
                    self.request.send(confirm_code)

                    # 接受客户端介绍信息的长度
                    json_data_len_buffer = self.request.recv(4)
                    json_data_len_buffer_unpackage = unpackage_data_2_security(json_data_len_buffer)
                    json_data_len = byte2data(json_data_len_buffer_unpackage)

                    # 接受介绍信息的内容
                    json_data_buffer = self.request.recv(json_data_len)
                    json_data_buffer_unpackage = unpackage_data_2_security(json_data_buffer)
                    # 将介绍信息的内容反序列化
                    json_data = json.loads(json_data_buffer_unpackage.decode('utf-8'))
                    print("{}本次介绍信息的内容为：{}".format(self.client_address[1], json_data))
                    print("{}本次file长度为：{}".format(self.client_address[1], json_data["filesize"]))

                    if json_data['aim_device'] == 'just-save':
                        recv_len = 0
                        filename = json_data['filename']
                        filesize = json_data['filesize']
                        filepath = json_data['filepath']
                        aim_device = json_data['aim_device']
                        md5 = json_data['md5']
                        with open("file/temp_lite/" + filename, 'wb') as f:
                            now_data_number = 0;
                            while recv_len < filesize:
                                package_data_buffer = self.request.recv(1028)
                                package_data_buffer_un = unpackage_data_2_security(package_data_buffer)
                                # print("Data Length {}".format(len(package_data_buffer_un)))
                                if len(package_data_buffer_un) == 1028:
                                    file_buffer = package_data_buffer_un[0:1024]
                                    data_number = byte2data(package_data_buffer_un[1024:1028])
                                    # print("Now Data Number {}, Data Number {}, ".format(now_data_number, data_number))
                                    if now_data_number == data_number:
                                        if filesize - recv_len > buffsize:
                                            recv_len += len(file_buffer)
                                            f.write(file_buffer)
                                        else:
                                            end_size = filesize - recv_len
                                            recv_len += end_size
                                            f.write(file_buffer[0:end_size])
                                        self.request.send(package_data_2_security(data2byte(911000)))
                                        now_data_number += 1
                                else:
                                    self.request.send(package_data_2_security(data2byte(911001)))
                        new_file_md5 = getmd5("file/temp_lite/" + filename)
                        if new_file_md5 == md5:
                            print("new_file_md5 {}, md5 {}".format(new_file_md5, md5))
                            print("{}文件接收成功".format(self.client_address[1]))
                            confirm_code = package_data_2_security(data2byte(911000))
                            self.request.send(confirm_code)
                            print("{} 使用break".format(self.client_address[1]))
                            split_file_counter.append(0)
                        else:
                            print("{}文件接收失败".format(self.client_address[1]))
                            confirm_code = package_data_2_security(data2byte(911002))
                            self.request.send(confirm_code)
                    else:
                        for one_client in client_list:
                            if one_client.name == json_data['aim_device']:
                                print("send object {}".format(one_client.name))
                                one_client.server_thread.send_task.append(
                                    [11000, "start", json_data_len_buffer, json_data_buffer])
                                recv_len = 0
                                filename = json_data['filename']
                                filesize = json_data['filesize']
                                filepath = json_data['filepath']
                                aim_device = json_data['aim_device']
                                md5 = json_data['md5']
                                with open("file/temp_lite/" + filename, 'wb') as f:
                                    now_data_number = 0;
                                    while recv_len < filesize:
                                        package_data_buffer = self.request.recv(1028)
                                        package_data_buffer_un = unpackage_data_2_security(package_data_buffer)
                                        file_buffer = package_data_buffer_un[0:1024]
                                        data_number = byte2data(package_data_buffer_un[1024:1028])

                                        if now_data_number == data_number:
                                            if filesize - recv_len > buffsize:
                                                recv_len += len(file_buffer)
                                                one_client.server_thread.send_task.append(
                                                    [11000, "data", package_data_buffer])
                                                f.write(file_buffer)
                                            else:
                                                end_size = filesize - recv_len
                                                recv_len += end_size
                                                one_client.server_thread.send_task.append(
                                                    [11000, "data", package_data_buffer])
                                                f.write(file_buffer[0:end_size])
                                            self.request.send(package_data_2_security(data2byte(911000)))
                                            now_data_number += 1
                                        else:
                                            continue

                                one_client.server_thread.send_task.append(
                                        [11000, "end"])


                        confirm_code = package_data_2_security(data2byte(911000))
                        self.request.send(confirm_code)
                    print("{} 使用break".format(self.client_address[1]))
                    break

                # 分片文件的整体文件汇总信息
                elif order == 11004:
                    print("进入文件操作")
                    confirm_code = package_data_2_security(data2byte(911004))
                    self.request.send(confirm_code)

                    # 接受客户端介绍信息的长度
                    json_data_len_buffer = self.request.recv(4)
                    json_data_len_buffer_unpackage = unpackage_data_2_security(json_data_len_buffer)
                    json_data_len = byte2data(json_data_len_buffer_unpackage)

                    # 接受介绍信息的内容
                    json_data_buffer = self.request.recv(json_data_len)
                    json_data_buffer_unpackage = unpackage_data_2_security(json_data_buffer)
                    # 将介绍信息的内容反序列化
                    json_data = json.loads(json_data_buffer_unpackage.decode('utf-8'))
                    print("本次介绍信息的内容为：{}".format(json_data))
                    print("本次file长度为：{}".format(json_data["filesize"]))
                    if json_data['aim_device'] == 'just-save':
                        one_client.server_thread.send_task.append(
                            [110040, json_data])
                    else:
                        for one_client in client_list:
                            if one_client.name == json_data['aim_device']:
                                print("send object {}".format(one_client.name))
                                one_client.server_thread.send_task.append([110041, self.request,
                                                 json_data_len_buffer, json_data_buffer])

                # elif order == 1100:
                #     print("进入文件操作")
                #     confirm_code = package_data_2_security(data2byte(91100))
                #     self.request.send(confirm_code)
                #
                #     # 接受客户端介绍信息的长度
                #     json_data_len_buffer = self.request.recv(4)
                #     json_data_len_buffer_unpackage = unpackage_data_2_security(json_data_len_buffer)
                #     json_data_len = byte2data(json_data_len_buffer_unpackage)
                #
                #     # 接受介绍信息的内容
                #     json_data_buffer = self.request.recv(json_data_len)
                #     json_data_buffer_unpackage = unpackage_data_2_security(json_data_buffer)
                #     # 将介绍信息的内容反序列化
                #     json_data = json.loads(json_data_buffer_unpackage.decode('utf-8'))
                #     print("本次介绍信息的内容为：{}".format(json_data))
                #     print("本次file长度为：{}".format(json_data["filesize"]))
                #
                #     if json_data['aim_device'] == 'all':
                #         for one_client in client_list:
                #             print("send object {}".format(one_client.name))
                #             one_client.server_thread.send_task.append(
                #                 [1100, json_data, self.request, json_data_len_buffer, json_data_buffer])
                #
                #     elif json_data['aim_device'] == 'just-save':
                #         file_save_option(json_data, self.request)
                #
                #     else:
                #         for one_client in client_list:
                #             if one_client.name == json_data['aim_device']:
                #                 print("send object {}".format(one_client.name))
                #                 recv_len = 0
                #                 filename = json_data['filename']
                #                 filesize = json_data['filesize']
                #                 filepath = json_data['filepath']
                #                 aim_device = json_data['aim_device']
                #                 md5 = json_data['md5']
                #                 with open("file/Temp/" + filename, 'wb') as f:
                #                     while recv_len < filesize:
                #                         # 接受客户端介绍信息的长度
                #                         file_buffer = unpackage_data_2_security(self.request.recv(1024))
                #                         if filesize - recv_len > buffsize:
                #                             recv_len += len(file_buffer)
                #                             f.write(file_buffer)
                #                         else:
                #                             end_size = filesize - recv_len
                #                             recv_len += end_size
                #                             f.write(file_buffer[0:end_size])
                #
                #                 # one_client.server_thread.send_task.append(
                #                 #         [1100, "end"])
                #
                #
                #     confirm_code = package_data_2_security(data2byte(91100))
                #     self.request.send(confirm_code)

                #

        except Exception as e:
            print(e.args)
            print("===========")
            print(traceback.format_exc())
            print("don't know error")
            for one_client in client_list:
                if one_client.port == self.client_address[1]:
                    client_list.remove(one_client)
                    self.request.close()

                    print(self.client_address, "{} 连接断开".format(self.client_name))
            print("当前客户链接数量为：{}".format(len(client_list)))
        except socket.timeout:  # 如果接收超时会抛出socket.timeout异常
            print(self.ip + ":" + str(self.port) + "接收超时！即将断开连接！")
            for one_client in client_list:
                if one_client.port == self.client_address[1]:

                    self.request.close()
                    client_list.remove(one_client)
                    print(self.client_address, "{} 连接断开".format(self.client_name))
            print("当前客户链接数量为：{}".format(len(client_list)))
        finally:
            self.request.close()

    def setup(self):
        self.client_name = ""
        self.timeOut = 50
        self.send_task = []
        self.request.settimeout(self.timeOut)
        print("before handle,连接建立：",self.client_address)

    def finish(self):
        self.request.close()
        print("finish run after handle")


if __name__ == '__main__':
    print('还没有人连接')
    s = socketserver.ThreadingTCPServer(('192.168.100.4', 8080), MyServer)  # 多线程
    # s = socketserver.ThreadingTCPServer(('localhost', 8080), MyServer)  # 多线程
    #   服务器一直开着
    s.serve_forever()

import os
import json
import struct

def operafile(filename):
    '''对报头进行打包'''
    filesize_bytes = os.path.getsize(filename)
    head_dir = {
        'filename': 'new' + filename,
        'filesize_bytes': filesize_bytes,
    }
    head_info = json.dumps(head_dir)
    head_info_len = struct.pack('i', 11)
    print(head_dir)
    print(len(head_info))
    print(head_info_len)
    return head_info_len, head_info


def testRange():
    print("start")
    for i in range(1, 10):
        print(i)

def test_pack():
    # operafile("client.py")
    print(len('s'.encode('utf-8')))
    print(struct.pack('i', 11))

if __name__ == "__main__":
    # testRange()
    S = "{}".format(0)
    send_message = "'name':'{}', 'ip':'{}', 'port':{}".format(1, " one_client.ip", 808)
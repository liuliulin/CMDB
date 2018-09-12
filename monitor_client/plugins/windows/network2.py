#!/usr/bin/env python
# coding: utf-8

try:
    import psutil
except ImportError:
    print('Error: psutil module not found!')
    exit()


# 函数获取各网卡发送、接收字节数
def get_key():
    key_info = psutil.net_io_counters(pernic=True).keys()  # 获取网卡名称

    recv = {}
    sent = {}

    for key in key_info:
        recv.setdefault(key, psutil.net_io_counters(pernic=True).get(key).bytes_recv)  # 各网卡接收的字节数
        sent.setdefault(key, psutil.net_io_counters(pernic=True).get(key).bytes_sent)  # 各网卡发送的字节数

    return key_info, recv, sent

# key_info, recv, sent = get_key()
# print(key_info)
# print(recv)
# print(sent)
# print(get_key())


# 函数计算每秒速率
def get_rate(func):
    import time
    key_info, old_recv, old_sent = func()  # 上一秒收集的数据
    time.sleep(1)
    key_info, now_recv, now_sent = func()  # 当前所收集的数据
    net_in = {}
    net_out = {}

    for key in key_info:
        net_in.setdefault(key, (now_recv.get(key) - old_recv.get(key)) / 1024)  # 每秒接收速率
        net_out.setdefault(key, (now_sent.get(key) - old_sent.get(key)) / 1024)  # 每秒发送速率

    return key_info, net_in, net_out

# key_info, net_in, net_out = get_rate(get_key)
# print(net_in)
# print(net_out)

# while 1:
#     try:
#         key_info, net_in, net_out = get_rate(get_key)
#
#         for key in key_info:
#             print('%s\nInput:\t %-5sKB/s\nOutput:\t %-5sKB/s\n' % (key, net_in.get(key), net_out.get(key)))
#     except KeyboardInterrupt:
#         exit()
